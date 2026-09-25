import secrets
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import EmailVerificationToken, ScholarProfile, UserProfile
from .serializers import (
    AnswerActionSerializer,
    AssignmentSerializer,
    BookmarkSerializer,
    CategorySerializer,
    MethodologySerializer,
    MeSerializer,
    ModerationQuestionSerializer,
    NotificationSerializer,
    PublicFatwaSerializer,
    QuestionActionSerializer,
    QuestionSerializer,
    RegisterSerializer,
    ReportSerializer,
    ReviewActionSerializer,
    ScholarApplicationSerializer,
    ScholarDetailSerializer,
    ScholarModerationActionSerializer,
    ScholarModerationSerializer,
    ScholarSerializer,
    UserSummarySerializer,
)
from fatwas.models import (
    Answer,
    AnswerRevision,
    AuditEvent,
    Bookmark,
    Category,
    Methodology,
    Publication,
    Report,
    ReviewDecision,
)
from notifications.models import DeliveryOutbox, Notification
from questions.models import ClarificationMessage, Question
from .permissions import (
    IsAssignedReviewer,
    IsAssignedScholar,
    IsClarificationParticipant,
    IsModerator,
    IsQuestionOwner,
    IsQuestionParticipant,
    IsVerifiedScholar,
    is_moderator,
    is_verified_scholar,
)


User = get_user_model()


class PublicPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def public_publications_queryset():
    return Publication.objects.filter(
        visibility='public',
        approved_revision__status='approved',
    ).select_related(
        'approved_revision__answer__question__category',
        'approved_revision__methodology',
        'approved_revision__created_by__userprofile',
    )


def profile_for(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def scholar_for(user):
    try:
        return user.scholarprofile
    except ScholarProfile.DoesNotExist:
        return None


def notify(user, kind, title, target_url=''):
    notification = Notification.objects.create(
        user=user,
        kind=kind,
        title=title,
        body='Sign in to Universe of Ilm to view the latest update.',
        target_url=target_url,
    )
    if user.email and profile_for(user).email_updates:
        DeliveryOutbox.objects.create(
            notification=notification,
            recipient_email=user.email,
            idempotency_key=f'notification:{notification.pk}',
        )
    return notification


class EmailOrUsernameTokenSerializer(TokenObtainPairSerializer):
    username = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(self.context['request'], username=identifier, password=password)
        if user is None:
            candidate = User.objects.filter(email__iexact=identifier).first()
            if candidate:
                user = authenticate(
                    self.context['request'],
                    username=candidate.username,
                    password=password,
                )
        if user is None or not user.is_active:
            raise AuthenticationFailed('Invalid login details.')
        refresh = self.get_token(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSummarySerializer(user).data,
        }


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request, *args, **kwargs):
        serializer = EmailOrUsernameTokenSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class RegisterAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = EmailVerificationToken.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
        )
        send_mail(
            'Verify your Universe of Ilm email',
            (
                'Open the verification link to activate submissions: '
                f'{request.build_absolute_uri("/api/v1/auth/verify-email/" + token.token + "/")}'
            ),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': UserSummarySerializer(user).data,
                'email_verified': False,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                return Response(
                    {'detail': 'Invalid refresh token.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyEmailAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, token):
        verification = EmailVerificationToken.objects.filter(
            token=token,
            used_at__isnull=True,
        ).select_related('user').first()
        if verification is None:
            return Response(
                {'detail': 'This verification link is invalid or already used.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        verification.used_at = timezone.now()
        verification.save(update_fields=('used_at',))
        profile = profile_for(verification.user)
        profile.email_verified = True
        profile.save(update_fields=('email_verified', 'updated_at'))
        return Response({'verified': True})


class HealthAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({'status': 'ok', 'service': 'backend'})


class MeAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response(MeSerializer(request.user).data)

    def put(self, request, *args, **kwargs):
        return self._update(request)

    def patch(self, request, *args, **kwargs):
        return self._update(request)

    def _update(self, request):
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MeSerializer(request.user).data)


class ScholarApplicationAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        scholar = scholar_for(request.user)
        return Response({
            'scholar_profile': (
                ScholarApplicationSerializer(scholar).data if scholar else None
            )
        })

    def post(self, request, *args, **kwargs):
        if not profile_for(request.user).email_verified:
            return Response(
                {
                    'detail': 'Verify your email before applying as a scholar.',
                    'code': 'email_unverified',
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        scholar = scholar_for(request.user)
        if scholar and scholar.is_suspended:
            return Response(
                {'detail': 'A suspended scholar profile cannot be edited.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ScholarApplicationSerializer(
            scholar,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            if scholar is None:
                scholar = serializer.save(user=request.user)
                created = True
            else:
                scholar = serializer.save()
                created = False

            # Profile details are never self-approved. Editing an approved
            # profile sends the complete profile back through verification.
            scholar.verification_status = 'pending'
            scholar.verification_note = ''
            scholar.verified_by = None
            scholar.verified_at = None
            scholar.save(update_fields=(
                'verification_status', 'verification_note', 'verified_by',
                'verified_at', 'updated_at',
            ))
            AuditEvent.objects.create(
                actor=request.user,
                event_type='scholar_application_submitted',
                object_type='scholar_profile',
                object_id=str(scholar.pk),
                metadata={'created': created},
            )

        return Response(
            {'scholar_profile': ScholarApplicationSerializer(scholar).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class QuestionListCreateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Question.objects.filter(owner=self.request.user).select_related(
            'category', 'assigned_scholar', 'assigned_reviewer'
        ).prefetch_related('clarifications')

    def get(self, request, *args, **kwargs):
        questions = self.get_queryset()
        paginator = PublicPageNumberPagination()
        page = paginator.paginate_queryset(questions, request, view=self)
        return paginator.get_paginated_response(
            QuestionSerializer(page, many=True, context={'request': request}).data
        )

    def post(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        return Response(
            {'question': QuestionSerializer(question, context={'request': request}).data},
            status=status.HTTP_201_CREATED,
        )


class QuestionDetailAPIView(APIView):
    permission_classes = (IsAuthenticated, IsQuestionParticipant)

    def get_queryset(self):
        queryset = Question.objects.select_related('category').prefetch_related(
            'clarifications'
        )
        return queryset.filter(
            Q(owner=self.request.user)
            | Q(assigned_scholar=self.request.user)
            | Q(assigned_reviewer=self.request.user)
        ) if not is_moderator(self.request.user) else queryset

    def get_object(self, request, pk):
        question = self.get_queryset().filter(pk=pk).first()
        if question is not None:
            self.check_object_permissions(request, question)
        return question

    def require_object_permission(self, request, question, permission_class):
        permission = permission_class()
        if not permission.has_object_permission(request, self, question):
            raise PermissionDenied(permission.message)

    def get(self, request, pk, *args, **kwargs):
        question = self.get_object(request, pk)
        if question is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'question': QuestionSerializer(question, context={'request': request}).data})

    def put(self, request, pk, *args, **kwargs):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk, *args, **kwargs):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        question = self.get_object(request, pk)
        if question is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.require_object_permission(request, question, IsQuestionOwner)
        if question.status not in ('draft', 'rejected'):
            raise ValidationError(
                {'detail': 'Only draft or rejected questions can be edited.'}
            )
        serializer = QuestionSerializer(
            question, data=request.data, partial=partial, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        return Response({'question': QuestionSerializer(question, context={'request': request}).data})

    def delete(self, request, pk, *args, **kwargs):
        question = self.get_object(request, pk)
        if question is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.require_object_permission(request, question, IsQuestionOwner)
        if question.status == 'answered':
            raise ValidationError(
                {'detail': 'Answered questions cannot be deleted.'}
            )
        question.status = 'withdrawn'
        question.withdrawn_at = timezone.now()
        question.save(update_fields=('status', 'withdrawn_at', 'updated_at'))
        Publication.objects.filter(answer__question=question, visibility='public').update(
            visibility='withdrawn', withdrawn_at=timezone.now()
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, pk, *args, **kwargs):
        question = self.get_object(request, pk)
        if question is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        action_serializer = QuestionActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        data = action_serializer.validated_data
        action = data['action']

        if action == 'submit':
            self.require_object_permission(request, question, IsQuestionOwner)
            if not profile_for(request.user).email_verified:
                return Response({'detail': 'Verify your email before submitting a question.', 'code': 'email_unverified'}, status=403)
            if question.status not in ('draft', 'rejected'):
                return Response({'detail': 'This question cannot be submitted in its current state.', 'code': 'workflow_conflict'}, status=409)
            question.is_public = data.get('is_public', False)
            if question.is_public:
                question.public_title = data.get('public_title', question.original_title).strip()
                question.public_body = data.get('public_body', question.original_body).strip()
                if not question.public_title or not question.public_body:
                    return Response({'detail': 'Public questions require redacted title and wording.'}, status=400)
            else:
                question.public_title = ''
                question.public_body = ''
            question.status = 'submitted'
            question.submitted_at = timezone.now()
            question.save()
        elif action == 'withdraw':
            self.require_object_permission(request, question, IsQuestionOwner)
            if question.status == 'withdrawn':
                return Response({'detail': 'This question is already withdrawn.', 'code': 'workflow_conflict'}, status=409)
            question.status = 'withdrawn'
            question.withdrawn_at = timezone.now()
            question.save(update_fields=('status', 'withdrawn_at', 'updated_at'))
            Publication.objects.filter(answer__question=question, visibility='public').update(
                visibility='withdrawn', withdrawn_at=timezone.now()
            )
        elif action == 'change_consent':
            if question.status in ('answered', 'withdrawn'):
                return Response({'detail': 'Consent cannot be changed at this stage.'}, status=403)
            self.require_object_permission(request, question, IsQuestionOwner)
            question.is_public = data.get('is_public', False)
            if question.is_public:
                question.public_title = data.get('public_title', question.public_title or question.original_title).strip()
                question.public_body = data.get('public_body', question.public_body or question.original_body).strip()
                if not question.public_title or not question.public_body:
                    return Response({'detail': 'Public consent requires redacted title and wording.'}, status=400)
            else:
                question.public_title = ''
                question.public_body = ''
            question.save(update_fields=('is_public', 'public_title', 'public_body', 'updated_at'))
        elif action == 'clarify':
            self.require_object_permission(request, question, IsClarificationParticipant)
            body = data.get('body', '').strip()
            if not body:
                return Response({'detail': 'A clarification message is required.'}, status=400)
            ClarificationMessage.objects.create(
                question=question,
                author=request.user,
                body=body,
            )
            question.status = 'needs_clarification'
            question.save(update_fields=('status', 'updated_at'))

        return Response({'question': QuestionSerializer(question, context={'request': request}).data})


class PublicFatwaListAPIView(APIView):
    permission_classes = (AllowAny,)

    def get_queryset(self, request):
        publications = public_publications_queryset()
        params = request.query_params
        query = params.get('q', '').strip()
        if query:
            publications = publications.filter(
                Q(approved_revision__public_question_title__icontains=query)
                | Q(approved_revision__public_question_body__icontains=query)
                | Q(approved_revision__body__icontains=query)
            )
        for parameter, lookup in (
            ('language', 'approved_revision__language'),
            ('category', 'approved_revision__answer__question__category__slug'),
            ('methodology', 'approved_revision__methodology__slug'),
            ('madhhab', 'approved_revision__answer__question__madhhab_preference'),
        ):
            value = params.get(parameter)
            if value:
                publications = publications.filter(**{lookup: value})
        scholar_id = params.get('scholar')
        if scholar_id and scholar_id.isdigit():
            publications = publications.filter(approved_revision__created_by_id=scholar_id)
        return publications

    def get(self, request, *args, **kwargs):
        paginator = PublicPageNumberPagination()
        page = paginator.paginate_queryset(self.get_queryset(request), request, view=self)
        data = PublicFatwaSerializer(page, many=True).data
        return paginator.get_paginated_response(data)


class PublicFatwaDetailAPIView(APIView):
    permission_classes = (AllowAny,)

    def get_queryset(self, request):
        queryset = public_publications_queryset()
        language = request.query_params.get('language')
        return queryset.filter(approved_revision__language=language) if language else queryset

    def get(self, request, publication_id, *args, **kwargs):
        publication = self.get_queryset(request).filter(pk=publication_id).first()
        if publication is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'fatwa': PublicFatwaSerializer(publication).data})


class CategoryListAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        categories = Category.objects.filter(is_active=True)
        return Response({'results': CategorySerializer(categories, many=True).data})


class MethodologyListAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        methodologies = Methodology.objects.filter(is_active=True)
        return Response({'results': MethodologySerializer(methodologies, many=True).data})


class ScholarListAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        scholars = ScholarProfile.objects.filter(
            verification_status='approved', is_suspended=False
        ).select_related('user__userprofile')
        return Response({'results': ScholarSerializer(scholars, many=True).data})


class ScholarDetailAPIView(APIView):
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return ScholarProfile.objects.filter(
            verification_status='approved', is_suspended=False
        ).select_related('user__userprofile')

    def get(self, request, user_id, *args, **kwargs):
        scholar = self.get_queryset().filter(user_id=user_id).first()
        if scholar is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'scholar': ScholarDetailSerializer(scholar).data})


class ReportCreateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['publication_id'] = kwargs['publication_id']
        serializer = ReportSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        return Response(
            {'report_id': report.id},
            status=status.HTTP_201_CREATED,
        )


class BookmarkListCreateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Bookmark.objects.filter(
            user=self.request.user,
            publication__visibility='public',
            publication__approved_revision__status='approved',
        ).select_related(
            'publication__approved_revision__answer__question',
            'publication__approved_revision__methodology',
            'publication__approved_revision__created_by__userprofile',
        )

    def get(self, request, *args, **kwargs):
        bookmarks = self.get_queryset()
        return Response({'results': BookmarkSerializer(bookmarks, many=True, context={'request': request}).data})

    def post(self, request, *args, **kwargs):
        serializer = BookmarkSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        created = serializer.context.get('created', False)
        return Response(
            {'bookmarked': True, 'created': created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        publication_id = request.data.get('publication_id')
        bookmark = self.get_queryset().filter(publication_id=publication_id).first()
        if bookmark:
            bookmark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:100]
        return Response({'results': NotificationSerializer(notifications, many=True).data})


class ScholarAssignmentListAPIView(APIView):
    permission_classes = (IsVerifiedScholar,)

    def get_queryset(self, user):
        return Question.objects.filter(
            assigned_scholar=user,
            status__in=('assigned', 'in_progress', 'needs_clarification'),
        ).select_related('category').prefetch_related('clarifications')

    def get(self, request, *args, **kwargs):
        questions = self.get_queryset(request.user)
        return Response({'results': QuestionSerializer(questions, many=True, context={'request': request}).data})


class AnswerCreateAPIView(APIView):
    permission_classes = (IsVerifiedScholar, IsAssignedScholar)

    def post(self, request, *args, **kwargs):
        serializer = AnswerActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        question = Question.objects.filter(
            pk=kwargs['question_id'], assigned_scholar=request.user
        ).first()
        if question is None:
            return Response({'detail': 'Assignment not found.'}, status=404)
        self.check_object_permissions(request, question)
        if data.get('methodology_id') and not Methodology.objects.filter(
            pk=data['methodology_id'], is_active=True
        ).exists():
            return Response({'detail': 'Methodology not found.'}, status=400)
        with transaction.atomic():
            answer, _ = Answer.objects.get_or_create(
                question=question,
                defaults={'author': request.user},
            )
            if answer.author_id != request.user.id:
                return Response({'detail': 'This answer belongs to another scholar.'}, status=403)
            draft = answer.revisions.filter(
                status__in=('draft', 'changes_requested'),
                created_by=request.user,
            ).first()
            if draft is None:
                next_number = (
                    answer.revisions.order_by('-revision_number')
                    .values_list('revision_number', flat=True)
                    .first() or 0
                ) + 1
                draft = AnswerRevision.objects.create(
                    answer=answer,
                    revision_number=next_number,
                    language=data.get('language', question.language),
                    body=data['body'],
                    public_question_title=question.public_title,
                    public_question_body=question.public_body,
                    references=data.get('references', []),
                    methodology_id=data.get('methodology_id'),
                    created_by=request.user,
                )
            else:
                draft.body = data['body']
                draft.references = data.get('references', draft.references)
                if data.get('language'):
                    draft.language = data['language']
                if data.get('methodology_id') is not None:
                    draft.methodology_id = data['methodology_id']
                draft.save(update_fields=('body', 'references', 'language', 'methodology_id'))
            if data['action'] == 'submit_for_review':
                if question.assigned_reviewer_id == request.user.id:
                    return Response({'detail': 'A scholar cannot review their own answer.'}, status=403)
                draft.status = 'in_review'
                draft.submitted_at = timezone.now()
                draft.save(update_fields=('status', 'submitted_at'))
            question.status = 'in_progress'
            question.save(update_fields=('status', 'updated_at'))
        return Response(
            {'revision_id': draft.id, 'status': draft.status},
            status=status.HTTP_201_CREATED,
        )


class ReviewQueueAPIView(APIView):
    permission_classes = (IsVerifiedScholar,)

    def get_queryset(self, user):
        return AnswerRevision.objects.filter(
            answer__question__assigned_reviewer=user,
            status='in_review',
        ).select_related('answer__question__category', 'created_by')

    def get(self, request, *args, **kwargs):
        results = []
        for revision in self.get_queryset(request.user):
            results.append({
                'id': revision.id,
                'question': QuestionSerializer(revision.answer.question, context={'request': request}).data,
                'body': revision.body,
                'author_id': revision.created_by_id,
                'revision_number': revision.revision_number,
                'submitted_at': revision.submitted_at,
            })
        return Response({'results': results})


class ReviewActionAPIView(APIView):
    permission_classes = (IsVerifiedScholar, IsAssignedReviewer)

    def post(self, request, revision_id, action):
        if action not in ('approve', 'request-changes', 'reject'):
            return Response({'detail': 'Unknown review action.'}, status=400)
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.validated_data.get('feedback', '').strip()
        decision = {
            'approve': 'approved',
            'request-changes': 'changes_requested',
            'reject': 'rejected',
        }[action]
        if decision != 'approved' and not feedback:
            return Response({'detail': 'Feedback is required for this decision.'}, status=400)
        with transaction.atomic():
            revision = AnswerRevision.objects.select_for_update().select_related(
                'answer__question', 'created_by'
            ).filter(
                pk=revision_id,
                answer__question__assigned_reviewer=request.user,
            ).first()
            if revision is None:
                return Response({'detail': 'Review assignment not found.'}, status=404)
            self.check_object_permissions(request, revision)
            if revision.created_by_id == request.user.id:
                return Response({'detail': 'A reviewer cannot approve their own answer.'}, status=403)
            if revision.status != 'in_review':
                return Response({'detail': 'This revision is no longer awaiting review.'}, status=409)
            ReviewDecision.objects.create(
                revision=revision,
                reviewer=request.user,
                decision=decision,
                feedback=feedback,
            )
            revision.status = decision
            revision.save(update_fields=('status',))
            question = revision.answer.question
            if decision == 'approved':
                revision.answer.approved_revision = revision
                revision.answer.save(update_fields=('approved_revision', 'updated_at'))
                visibility = 'public' if question.is_public else 'private'
                title = revision.public_question_title or question.public_title or question.original_title
                publication, _ = Publication.objects.get_or_create(
                    answer=revision.answer,
                    defaults={
                        'approved_revision': revision,
                        'public_id': uuid.uuid4(),
                        'slug': f'{slugify(title)[:220] or "fatwa"}-{revision.id}',
                        'visibility': visibility,
                        'published_at': timezone.now(),
                    },
                )
                publication.approved_revision = revision
                publication.slug = f'{slugify(title)[:220] or "fatwa"}-{revision.id}'
                publication.visibility = visibility
                publication.published_at = timezone.now()
                publication.withdrawn_at = None
                publication.save(update_fields=('approved_revision', 'slug', 'visibility', 'published_at', 'withdrawn_at'))
                question.status = 'answered'
                question.save(update_fields=('status', 'updated_at'))
                notify(question.owner, 'answer_released', 'Your answer is ready', f'/questions/{question.id}/')
            elif decision == 'changes_requested':
                question.status = 'in_progress'
                question.save(update_fields=('status', 'updated_at'))
                notify(revision.created_by, 'answer_changes_requested', 'Your answer needs changes', f'/scholar/questions/{question.id}/')
            else:
                question.status = 'rejected'
                question.save(update_fields=('status', 'updated_at'))
                notify(question.owner, 'question_rejected', 'Your question has an update', f'/questions/{question.id}/')
        return Response({'decision': decision, 'revision_id': revision.id})


class AssignQuestionAPIView(APIView):
    permission_classes = (IsModerator,)

    def post(self, request, *args, **kwargs):
        serializer = AssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        scholar = User.objects.filter(pk=data['scholar_id']).first()
        reviewer = User.objects.filter(pk=data['reviewer_id']).first()
        if not scholar or not reviewer or scholar == reviewer or not is_verified_scholar(scholar) or not is_verified_scholar(reviewer):
            return Response({'detail': 'Select two different approved, active scholars.'}, status=400)
        with transaction.atomic():
            question = Question.objects.select_for_update().filter(
                pk=kwargs['question_id'], status__in=('submitted', 'rejected')
            ).first()
            if question is None:
                return Response({'detail': 'Question is not available for assignment.', 'code': 'workflow_conflict'}, status=409)
            question.assigned_scholar = scholar
            question.assigned_reviewer = reviewer
            question.assigned_at = timezone.now()
            question.status = 'assigned'
            question.save(update_fields=('assigned_scholar', 'assigned_reviewer', 'assigned_at', 'status', 'updated_at'))
            AuditEvent.objects.create(
                actor=request.user,
                event_type='question_assigned',
                object_type='question',
                object_id=str(question.id),
                metadata={'scholar_id': scholar.id, 'reviewer_id': reviewer.id},
            )
            notify(scholar, 'question_assigned', 'A question has been assigned to you', f'/scholar/questions/{question.id}/')
            notify(reviewer, 'review_assigned', 'A review has been assigned to you', '/reviews/')
        return Response({'question': QuestionSerializer(question, context={'request': request}).data})


class ScholarModerationListAPIView(APIView):
    permission_classes = (IsModerator,)

    def get(self, request, *args, **kwargs):
        queryset = ScholarProfile.objects.select_related(
            'user', 'user__userprofile', 'verified_by'
        ).order_by('verification_status', 'user__username')
        status_filter = request.query_params.get('status')
        if status_filter:
            if status_filter not in {'pending', 'approved', 'rejected'}:
                return Response({'detail': 'Unknown scholar status.'}, status=400)
            queryset = queryset.filter(verification_status=status_filter)
        return Response({
            'results': ScholarModerationSerializer(queryset, many=True).data,
        })


class ScholarModerationActionAPIView(APIView):
    permission_classes = (IsModerator,)

    def patch(self, request, user_id, *args, **kwargs):
        serializer = ScholarModerationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data['action']
        note = serializer.validated_data.get('note', '').strip()

        with transaction.atomic():
            scholar = ScholarProfile.objects.select_for_update().select_related(
                'user', 'user__userprofile'
            ).filter(user_id=user_id).first()
            if scholar is None:
                return Response({'detail': 'Scholar profile not found.'}, status=404)

            if action == 'approve':
                scholar.verification_status = 'approved'
                scholar.verification_note = note
                scholar.verified_by = request.user
                scholar.verified_at = timezone.now()
                scholar.is_suspended = False
            elif action == 'reject':
                scholar.verification_status = 'rejected'
                scholar.verification_note = note
                scholar.verified_by = request.user
                scholar.verified_at = timezone.now()
            elif action == 'suspend':
                scholar.is_suspended = True
                scholar.verification_note = note
            else:
                scholar.is_suspended = False
                scholar.verification_note = ''

            scholar.save(update_fields=(
                'verification_status', 'verification_note', 'verified_by',
                'verified_at', 'is_suspended', 'updated_at',
            ))
            AuditEvent.objects.create(
                actor=request.user,
                event_type=f'scholar_profile_{action}',
                object_type='scholar_profile',
                object_id=str(scholar.pk),
                metadata={'user_id': scholar.user_id, 'note': note},
            )

        return Response({'scholar': ScholarModerationSerializer(scholar).data})


class ModerationQuestionListAPIView(APIView):
    permission_classes = (IsModerator,)

    def get(self, request, *args, **kwargs):
        questions = Question.objects.filter(
            status__in=('submitted', 'rejected'),
        ).select_related('owner__userprofile', 'category').order_by(
            'submitted_at', 'created_at'
        )
        return Response({
            'results': ModerationQuestionSerializer(questions, many=True).data,
        })
