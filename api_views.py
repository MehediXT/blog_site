import json
import secrets
import uuid
from functools import wraps

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from accounts.models import EmailVerificationToken, ScholarProfile, UserProfile
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

User = get_user_model()


def _body(request):
    if request.body:
        try:
            return json.loads(request.body.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
    return request.POST.dict()


def _error(message, status=400, *, code='invalid', fields=None):
    payload = {'error': {'code': code, 'message': message}}
    if fields:
        payload['error']['fields'] = fields
    return JsonResponse(payload, status=status)


def _ok(data=None, status=200):
    return JsonResponse(data or {'ok': True}, status=status)


def _auth(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _error('Authentication is required.', 401, code='authentication_required')
        return view(request, *args, **kwargs)

    return wrapped


def _profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _can_moderate(user):
    return user.is_staff or user.groups.filter(name__in=('moderator', 'administrator')).exists()


def _scholar(user):
    try:
        return user.scholarprofile
    except ScholarProfile.DoesNotExist:
        return None


def _can_author(user):
    profile = _scholar(user)
    return bool(profile and profile.can_author)


def _private_access(user, question):
    if not user.is_authenticated:
        return False
    return (
        question.owner_id == user.id
        or question.assigned_scholar_id == user.id
        or question.assigned_reviewer_id == user.id
        or _can_moderate(user)
    )


def _question_data(question, *, private=False):
    data = {
        'id': question.id,
        'status': question.status,
        'language': question.language,
        'category': question.category.slug if question.category else None,
        'is_public': question.is_public,
        'created_at': question.created_at.isoformat(),
        'updated_at': question.updated_at.isoformat(),
    }
    if private:
        data.update({
            'original_title': question.original_title,
            'original_body': question.original_body,
            'public_title': question.public_title,
            'public_body': question.public_body,
            'madhhab_preference': question.madhhab_preference,
            'assigned_scholar_id': question.assigned_scholar_id,
            'assigned_reviewer_id': question.assigned_reviewer_id,
            'clarifications': [
                {'id': item.id, 'author_id': item.author_id, 'body': item.body, 'created_at': item.created_at.isoformat()}
                for item in question.clarifications.select_related('author').all()
            ],
        })
    return data


def _publication_data(publication):
    revision = publication.approved_revision
    question = revision.answer.question
    return {
        'id': publication.id,
        'public_id': str(publication.public_id) if publication.public_id else None,
        'slug': publication.slug,
        'title': revision.public_question_title or question.public_title,
        'question': revision.public_question_body or question.public_body,
        'answer': revision.body,
        'language': revision.language,
        'references': revision.references,
        'methodology': revision.methodology.slug if revision.methodology else None,
        'scholar': {
            'id': revision.created_by_id,
            'name': _profile(revision.created_by).display_name or revision.created_by.get_username(),
        },
        'published_at': publication.published_at.isoformat() if publication.published_at else None,
    }


def _notify(user, kind, title, target_url=''):
    notification = Notification.objects.create(
        user=user,
        kind=kind,
        title=title,
        body='Sign in to Universe of Ilm to view the latest update.',
        target_url=target_url,
    )
    if user.email and _profile(user).email_updates:
        DeliveryOutbox.objects.create(
            notification=notification,
            recipient_email=user.email,
            idempotency_key=f'notification:{notification.pk}',
        )
    return notification


@ensure_csrf_cookie
@require_http_methods(['GET'])
def api_csrf(request):
    return _ok({'csrfToken': get_token(request)})


@csrf_protect
@require_http_methods(['POST'])
def api_register(request):
    data = _body(request) or {}
    username = str(data.get('username', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    password = data.get('password') or data.get('password1')
    if not username or not email or not password:
        return _error('Username, email, and password are required.', fields={'required': ['username', 'email', 'password']})
    if User.objects.filter(username=username).exists():
        return _error('That username is already in use.', fields={'username': ['Choose another username.']})
    if User.objects.filter(email__iexact=email).exists():
        return _error('An account with this email already exists.', fields={'email': ['Use another email address.']})
    try:
        validate_password(password)
    except ValidationError as exc:
        return _error('Choose a stronger password.', fields={'password': list(exc.messages)})
    user = User.objects.create_user(username=username, email=email, password=password)
    token = EmailVerificationToken.objects.create(user=user, token=secrets.token_urlsafe(32))
    send_mail(
        'Verify your Universe of Ilm email',
        f'Open the verification link to activate submissions: {request.build_absolute_uri("/api/v1/auth/verify-email/" + token.token + "/")}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=True,
    )
    login(request, user)
    return _ok({'user': {'id': user.id, 'username': user.username, 'email_verified': False}}, 201)


@csrf_protect
@require_http_methods(['POST'])
def api_login(request):
    data = _body(request) or {}
    username = data.get('username') or data.get('email')
    user = authenticate(request, username=username, password=data.get('password'))
    if user is None:
        return _error('Invalid login details.', 400, code='invalid_credentials')
    login(request, user)
    return _ok({'user': {'id': user.id, 'username': user.username, 'email_verified': _profile(user).email_verified}})


@csrf_protect
@_auth
@require_http_methods(['POST'])
def api_logout(request):
    logout(request)
    return _ok()


@require_http_methods(['GET'])
def api_verify_email(request, token):
    verification = EmailVerificationToken.objects.filter(token=token, used_at__isnull=True).select_related('user').first()
    if not verification:
        return _error('This verification link is invalid or already used.', 400, code='invalid_token')
    verification.used_at = timezone.now()
    verification.save(update_fields=['used_at'])
    profile = _profile(verification.user)
    profile.email_verified = True
    profile.save(update_fields=['email_verified', 'updated_at'])
    return _ok({'verified': True})


@_auth
@require_http_methods(['GET', 'PATCH'])
def api_me(request):
    profile = _profile(request.user)
    if request.method == 'PATCH':
        data = _body(request) or {}
        if 'preferred_language' in data and data['preferred_language'] in ('bn', 'en'):
            profile.preferred_language = data['preferred_language']
        if 'display_name' in data:
            profile.display_name = str(data['display_name']).strip()[:150]
        profile.save()
    scholar = _scholar(request.user)
    return _ok({'id': request.user.id, 'username': request.user.username, 'email': request.user.email, 'email_verified': profile.email_verified, 'preferred_language': profile.preferred_language, 'display_name': profile.display_name, 'scholar': bool(scholar and scholar.can_author)})


@_auth
@require_http_methods(['GET', 'POST'])
def api_questions(request):
    if request.method == 'GET':
        return _ok({'results': [_question_data(q, private=True) for q in Question.objects.filter(owner=request.user).select_related('category').prefetch_related('clarifications')]})
    data = _body(request) or {}
    title = str(data.get('title', '')).strip()
    body = str(data.get('body', '')).strip()
    language = data.get('language', 'bn')
    if not title or not body or language not in ('bn', 'en', 'ar'):
        return _error('Title, question, and a supported language are required.', fields={'title': ['Required.'], 'body': ['Required.'], 'language': ['Use bn, en, or ar.']})
    category = Category.objects.filter(slug=data.get('category')).first() if data.get('category') else None
    question = Question.objects.create(owner=request.user, original_title=title, original_body=body, language=language, category=category, madhhab_preference=str(data.get('madhhab_preference', '')).strip(), is_public=False)
    return _ok({'question': _question_data(question, private=True)}, 201)


@_auth
@require_http_methods(['GET', 'POST'])
def api_question_detail(request, question_id):
    question = Question.objects.filter(pk=question_id).select_related('category').prefetch_related('clarifications').first()
    if not question or not _private_access(request.user, question):
        return _error('Question not found.', 404, code='not_found')
    if request.method == 'GET':
        return _ok({'question': _question_data(question, private=True)})
    data = _body(request) or {}
    action = data.get('action')
    if action == 'submit':
        if question.owner_id != request.user.id:
            return _error('Only the asker can submit this question.', 403, code='permission_denied')
        if not _profile(request.user).email_verified:
            return _error('Verify your email before submitting a question.', 403, code='email_unverified')
        if question.status not in ('draft', 'rejected'):
            return _error('This question cannot be submitted in its current state.', 409, code='workflow_conflict')
        is_public = data.get('is_public') is True
        question.is_public = is_public
        question.public_title = str(data.get('public_title', question.original_title)).strip() if is_public else ''
        question.public_body = str(data.get('public_body', question.original_body)).strip() if is_public else ''
        if is_public and (not question.public_title or not question.public_body):
            return _error('Public questions require redacted title and wording.', fields={'public_title': ['Required.'], 'public_body': ['Required.']})
        question.status = 'submitted'
        question.submitted_at = timezone.now()
        question.save()
        return _ok({'question': _question_data(question, private=True)})
    if action == 'withdraw':
        if question.owner_id != request.user.id or question.status == 'withdrawn':
            return _error('Only the asker can withdraw this question.', 403, code='permission_denied')
        question.status = 'withdrawn'
        question.withdrawn_at = timezone.now()
        question.save(update_fields=['status', 'withdrawn_at', 'updated_at'])
        Publication.objects.filter(answer__question=question, visibility='public').update(visibility='withdrawn', withdrawn_at=timezone.now())
        return _ok({'question': _question_data(question, private=True)})
    if action == 'change_consent':
        if question.owner_id != request.user.id or question.status in ('answered', 'withdrawn'):
            return _error('Consent can only be changed by the asker before release.', 403, code='permission_denied')
        question.is_public = data.get('is_public') is True
        if question.is_public:
            question.public_title = str(data.get('public_title', question.public_title or question.original_title)).strip()
            question.public_body = str(data.get('public_body', question.public_body or question.original_body)).strip()
            if not question.public_title or not question.public_body:
                return _error('Public consent requires redacted title and wording.', fields={'public_title': ['Required.'], 'public_body': ['Required.']})
        else:
            question.public_title = ''
            question.public_body = ''
        question.save(update_fields=['is_public', 'public_title', 'public_body', 'updated_at'])
        return _ok({'question': _question_data(question, private=True)})
    if action == 'clarify':
        message = str(data.get('body', '')).strip()
        if not message:
            return _error('A clarification message is required.')
        ClarificationMessage.objects.create(question=question, author=request.user, body=message)
        question.status = 'needs_clarification'
        question.save(update_fields=['status', 'updated_at'])
        return _ok({'created': True}, 201)
    return _error('Use an explicit submit, withdraw, clarify, or change_consent action.')


@require_http_methods(['GET'])
def api_fatwas(request):
    publications = Publication.objects.filter(visibility='public', approved_revision__status='approved').select_related('approved_revision__answer__question', 'approved_revision__methodology', 'approved_revision__created_by')
    query = request.GET.get('q', '').strip()
    if query:
        from django.db.models import Q
        publications = publications.filter(Q(approved_revision__public_question_title__icontains=query) | Q(approved_revision__public_question_body__icontains=query) | Q(approved_revision__body__icontains=query))
    language = request.GET.get('language')
    if language:
        publications = publications.filter(approved_revision__language=language)
    category = request.GET.get('category')
    if category:
        publications = publications.filter(approved_revision__answer__question__category__slug=category)
    methodology = request.GET.get('methodology')
    if methodology:
        publications = publications.filter(approved_revision__methodology__slug=methodology)
    scholar_id = request.GET.get('scholar')
    if scholar_id and scholar_id.isdigit():
        publications = publications.filter(approved_revision__created_by_id=scholar_id)
    madhhab = request.GET.get('madhhab')
    if madhhab:
        publications = publications.filter(approved_revision__answer__question__madhhab_preference=madhhab)
    total = publications.count()
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(100, max(1, int(request.GET.get('page_size', 20))))
    except (TypeError, ValueError):
        page_size = 20
    start = (page - 1) * page_size
    return _ok({'results': [_publication_data(publication) for publication in publications[start:start + page_size]], 'count': total, 'page': page, 'page_size': page_size})


@require_http_methods(['GET'])
def api_fatwa_detail(request, publication_id):
    publication = Publication.objects.filter(pk=publication_id, visibility='public', approved_revision__status='approved').select_related('approved_revision__answer__question', 'approved_revision__methodology', 'approved_revision__created_by').first()
    if not publication:
        return _error('Fatwa not found.', 404, code='not_found')
    return _ok({'fatwa': _publication_data(publication)})


@_auth
@require_http_methods(['POST'])
def api_report_fatwa(request, publication_id):
    publication = Publication.objects.filter(pk=publication_id, visibility='public').first()
    if not publication:
        return _error('Fatwa not found.', 404, code='not_found')
    data = _body(request) or {}
    reason = str(data.get('reason', '')).strip()
    if not reason:
        return _error('A report reason is required.', fields={'reason': ['Required.']})
    report = Report.objects.create(publication=publication, reporter=request.user, reason=reason)
    return _ok({'report_id': report.id}, 201)


@require_http_methods(['GET'])
def api_categories(request):
    return _ok({'results': list(Category.objects.filter(is_active=True).values('slug', 'name_en', 'name_bn'))})


@require_http_methods(['GET'])
def api_methodologies(request):
    return _ok({'results': list(Methodology.objects.filter(is_active=True).values('slug', 'name_en', 'name_bn', 'description'))})


@require_http_methods(['GET'])
def api_scholars(request):
    profiles = ScholarProfile.objects.filter(verification_status='approved', is_suspended=False).select_related('user')
    return _ok({'results': [{'id': p.user_id, 'name': _profile(p.user).display_name or p.user.username, 'institution': p.institution, 'specialties': p.specialties, 'languages': p.supported_languages} for p in profiles]})


@require_http_methods(['GET'])
def api_scholar_detail(request, user_id):
    profile = ScholarProfile.objects.filter(user_id=user_id, verification_status='approved', is_suspended=False).select_related('user').first()
    if not profile:
        return _error('Scholar not found.', 404, code='not_found')
    return _ok({'scholar': {'id': user_id, 'name': _profile(profile.user).display_name or profile.user.username, 'biography': profile.public_bio, 'qualifications': profile.qualifications, 'institution': profile.institution, 'specialties': profile.specialties, 'languages': profile.supported_languages}})


@_auth
@require_http_methods(['GET', 'POST', 'DELETE'])
def api_bookmarks(request):
    if request.method == 'GET':
        publications = Publication.objects.filter(bookmarks__user=request.user, visibility='public').select_related('approved_revision__answer__question', 'approved_revision__methodology', 'approved_revision__created_by')
        return _ok({'results': [_publication_data(p) for p in publications]})
    data = _body(request) or {}
    publication = Publication.objects.filter(pk=data.get('publication_id'), visibility='public').first()
    if not publication:
        return _error('Fatwa not found.', 404, code='not_found')
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, publication=publication)
    if request.method == 'DELETE':
        bookmark.delete()
        return _ok()
    return _ok({'bookmarked': True, 'created': created}, 201 if created else 200)


@_auth
@require_http_methods(['GET'])
def api_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:100]
    return _ok({'results': [{'id': n.id, 'kind': n.kind, 'title': n.title, 'body': n.body, 'target_url': n.target_url, 'read': bool(n.read_at), 'created_at': n.created_at.isoformat()} for n in notifications]})


@_auth
@require_http_methods(['GET'])
def api_scholar_assignments(request):
    if not _can_author(request.user):
        return _error('An approved, active scholar profile is required.', 403, code='permission_denied')
    questions = Question.objects.filter(assigned_scholar=request.user, status__in=('assigned', 'in_progress', 'needs_clarification')).select_related('category')
    return _ok({'results': [_question_data(q, private=True) for q in questions]})


@_auth
@require_http_methods(['POST'])
def api_answer(request, question_id):
    if not _can_author(request.user):
        return _error('An approved, active scholar profile is required.', 403, code='permission_denied')
    question = Question.objects.filter(pk=question_id, assigned_scholar=request.user).first()
    if not question:
        return _error('Assignment not found.', 404, code='not_found')
    data = _body(request) or {}
    body = str(data.get('body', '')).strip()
    if not body:
        return _error('Answer body is required.', fields={'body': ['Required.']})
    with transaction.atomic():
        answer, _ = Answer.objects.get_or_create(question=question, defaults={'author': request.user})
        if answer.author_id != request.user.id:
            return _error('This answer belongs to another scholar.', 403, code='permission_denied')
        draft = answer.revisions.filter(status__in=('draft', 'changes_requested'), created_by=request.user).first()
        if draft is None:
            next_number = (answer.revisions.order_by('-revision_number').values_list('revision_number', flat=True).first() or 0) + 1
            draft = AnswerRevision.objects.create(answer=answer, revision_number=next_number, language=data.get('language', question.language), body=body, public_question_title=question.public_title, public_question_body=question.public_body, references=data.get('references', []), methodology_id=data.get('methodology_id'), created_by=request.user)
        else:
            draft.body = body
            draft.references = data.get('references', draft.references)
            draft.save(update_fields=['body', 'references'])
        if data.get('action') == 'submit_for_review':
            if question.assigned_reviewer_id == request.user.id:
                return _error('A scholar cannot review their own answer.', 403, code='permission_denied')
            draft.status = 'in_review'
            draft.submitted_at = timezone.now()
            draft.save(update_fields=['status', 'submitted_at'])
            question.status = 'in_progress'
            question.save(update_fields=['status', 'updated_at'])
        else:
            question.status = 'in_progress'
            question.save(update_fields=['status', 'updated_at'])
    return _ok({'revision_id': draft.id, 'status': draft.status}, 201)


@_auth
@require_http_methods(['GET'])
def api_review_queue(request):
    if not _can_author(request.user):
        return _error('An approved, active scholar profile is required.', 403, code='permission_denied')
    revisions = AnswerRevision.objects.filter(answer__question__assigned_reviewer=request.user, status='in_review').select_related('answer__question', 'created_by')
    return _ok({'results': [{'id': r.id, 'question': _question_data(r.answer.question, private=True), 'body': r.body, 'author_id': r.created_by_id, 'revision_number': r.revision_number, 'submitted_at': r.submitted_at.isoformat() if r.submitted_at else None} for r in revisions]})


@_auth
@require_http_methods(['POST'])
def api_review_action(request, revision_id, action):
    if action not in ('approve', 'request-changes', 'reject'):
        return _error('Unknown review action.')
    if not _can_author(request.user):
        return _error('An approved, active scholar profile is required.', 403, code='permission_denied')
    with transaction.atomic():
        revision = AnswerRevision.objects.select_for_update().select_related('answer__question').filter(pk=revision_id).first()
        if not revision or revision.answer.question.assigned_reviewer_id != request.user.id:
            return _error('Review assignment not found.', 404, code='not_found')
        if revision.created_by_id == request.user.id:
            return _error('A reviewer cannot approve their own answer.', 403, code='permission_denied')
        if revision.status != 'in_review':
            return _error('This revision is no longer awaiting review.', 409, code='workflow_conflict')
        data = _body(request) or {}
        decision = {'approve': 'approved', 'request-changes': 'changes_requested', 'reject': 'rejected'}[action]
        if decision != 'approved' and not str(data.get('feedback', '')).strip():
            return _error('Feedback is required for this decision.', fields={'feedback': ['Required.']})
        ReviewDecision.objects.create(revision=revision, reviewer=request.user, decision=decision, feedback=str(data.get('feedback', '')).strip())
        revision.status = decision
        revision.save(update_fields=['status'])
        question = revision.answer.question
        if decision == 'approved':
            revision.answer.approved_revision = revision
            revision.answer.save(update_fields=['approved_revision', 'updated_at'])
            visibility = 'public' if question.is_public else 'private'
            title = revision.public_question_title or question.public_title or question.original_title
            base_slug = slugify(title)[:220] or 'fatwa'
            slug = f'{base_slug}-{revision.id}'
            publication = Publication.objects.filter(answer=revision.answer).first()
            if publication:
                publication.approved_revision = revision
                publication.slug = slug
                publication.visibility = visibility
                publication.published_at = timezone.now()
                publication.withdrawn_at = None
                publication.save(update_fields=['approved_revision', 'slug', 'visibility', 'published_at', 'withdrawn_at'])
            else:
                publication = Publication.objects.create(answer=revision.answer, approved_revision=revision, public_id=uuid.uuid4(), slug=slug, visibility=visibility, published_at=timezone.now())
            question.status = 'answered'
            question.save(update_fields=['status', 'updated_at'])
            _notify(question.owner, 'answer_released', 'Your answer is ready', f'/questions/{question.id}/')
        elif decision == 'changes_requested':
            question.status = 'in_progress'
            question.save(update_fields=['status', 'updated_at'])
            _notify(revision.created_by, 'answer_changes_requested', 'Your answer needs changes', f'/scholar/questions/{question.id}/')
        else:
            question.status = 'rejected'
            question.save(update_fields=['status', 'updated_at'])
            _notify(question.owner, 'question_rejected', 'Your question has an update', f'/questions/{question.id}/')
    return _ok({'decision': decision, 'revision_id': revision.id})


@_auth
@require_http_methods(['POST'])
def api_assign_question(request, question_id):
    if not _can_moderate(request.user):
        return _error('Moderator permission is required.', 403, code='permission_denied')
    data = _body(request) or {}
    scholar = User.objects.filter(pk=data.get('scholar_id')).first()
    reviewer = User.objects.filter(pk=data.get('reviewer_id')).first()
    if not scholar or not reviewer or scholar == reviewer or not _can_author(scholar) or not _can_author(reviewer):
        return _error('Select two different approved, active scholars.', fields={'scholar_id': ['Must be an approved scholar.'], 'reviewer_id': ['Must be a different approved scholar.']})
    with transaction.atomic():
        question = Question.objects.select_for_update().filter(pk=question_id, status__in=('submitted', 'rejected')).first()
        if not question:
            return _error('Question is not available for assignment.', 409, code='workflow_conflict')
        question.assigned_scholar = scholar
        question.assigned_reviewer = reviewer
        question.assigned_at = timezone.now()
        question.status = 'assigned'
        question.save(update_fields=['assigned_scholar', 'assigned_reviewer', 'assigned_at', 'status', 'updated_at'])
        AuditEvent.objects.create(actor=request.user, event_type='question_assigned', object_type='question', object_id=str(question.id), metadata={'scholar_id': scholar.id, 'reviewer_id': reviewer.id})
        _notify(scholar, 'question_assigned', 'A question has been assigned to you', f'/scholar/questions/{question.id}/')
        _notify(reviewer, 'review_assigned', 'A review has been assigned to you', '/reviews/')
    return _ok({'question': _question_data(question, private=True)})
