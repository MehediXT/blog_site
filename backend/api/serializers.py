from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from accounts.models import ScholarProfile, UserProfile
from fatwas.models import Bookmark, Category, Methodology, Publication, Report
from notifications.models import Notification
from questions.models import ClarificationMessage, Question
from .permissions import is_moderator


User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('That username is already in use.')
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        # Django's create_user() calls set_password() before writing the user.
        return User.objects.create_user(password=password, **validated_data)


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)
    preferred_language = serializers.ChoiceField(choices=('bn', 'en'), required=False)
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    scholar = serializers.BooleanField(read_only=True)
    moderator = serializers.BooleanField(read_only=True)

    def to_representation(self, user):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        scholar = getattr(user, 'scholarprofile', None)
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'email_verified': profile.email_verified,
            'preferred_language': profile.preferred_language,
            'display_name': profile.display_name,
            'scholar': bool(scholar and scholar.can_author),
            'moderator': is_moderator(user),
        }

    def update(self, user, validated_data):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        for field in ('preferred_language', 'display_name'):
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save(update_fields=('preferred_language', 'display_name', 'updated_at'))
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('slug', 'name_en', 'name_bn')


class MethodologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Methodology
        fields = ('id', 'slug', 'name_en', 'name_bn', 'description')
        read_only_fields = ('id',)


class ClarificationSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source='author_id', read_only=True)

    class Meta:
        model = ClarificationMessage
        fields = ('id', 'author_id', 'body', 'created_at')
        read_only_fields = ('id', 'author_id', 'created_at')


class QuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='original_title', write_only=True, max_length=240)
    body = serializers.CharField(source='original_body', write_only=True)
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )
    clarifications = ClarificationSerializer(many=True, read_only=True)
    assigned_scholar_id = serializers.IntegerField(read_only=True)
    assigned_reviewer_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Question
        fields = (
            'id', 'status', 'language', 'category', 'is_public',
            'created_at', 'updated_at', 'title', 'body',
            'original_title', 'original_body', 'public_title', 'public_body',
            'madhhab_preference', 'assigned_scholar_id', 'assigned_reviewer_id',
            'clarifications',
        )
        read_only_fields = (
            'id', 'status', 'created_at', 'updated_at', 'original_title',
            'original_body', 'public_title', 'public_body',
            'assigned_scholar_id', 'assigned_reviewer_id',
        )

    def create(self, validated_data):
        return Question.objects.create(owner=self.context['request'].user, **validated_data)


class PublicFatwaSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    public_id = serializers.UUIDField(read_only=True, allow_null=True)
    slug = serializers.CharField(read_only=True)
    title = serializers.SerializerMethodField()
    question = serializers.SerializerMethodField()
    answer = serializers.CharField(source='approved_revision.body', read_only=True)
    language = serializers.CharField(source='approved_revision.language', read_only=True)
    references = serializers.JSONField(source='approved_revision.references', read_only=True)
    methodology = serializers.SerializerMethodField()
    scholar = serializers.SerializerMethodField()
    published_at = serializers.DateTimeField(read_only=True, allow_null=True)

    def get_title(self, publication):
        revision = publication.approved_revision
        return revision.public_question_title or revision.answer.question.public_title

    def get_question(self, publication):
        revision = publication.approved_revision
        return revision.public_question_body or revision.answer.question.public_body

    def get_methodology(self, publication):
        methodology = publication.approved_revision.methodology
        return methodology.slug if methodology else None

    def get_scholar(self, publication):
        user = publication.approved_revision.created_by
        profile = getattr(user, 'userprofile', None)
        return {
            'id': user.id,
            'name': (profile.display_name if profile else '') or user.get_username(),
        }


class ScholarSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user_id', read_only=True)
    name = serializers.SerializerMethodField()
    languages = serializers.JSONField(source='supported_languages', read_only=True)

    class Meta:
        model = ScholarProfile
        fields = ('id', 'name', 'institution', 'specialties', 'languages')

    def get_name(self, profile):
        user_profile = getattr(profile.user, 'userprofile', None)
        return (user_profile.display_name if user_profile else '') or profile.user.username


class ScholarDetailSerializer(ScholarSerializer):
    biography = serializers.CharField(source='public_bio', read_only=True)

    class Meta(ScholarSerializer.Meta):
        fields = ScholarSerializer.Meta.fields + ('biography', 'qualifications')


class ScholarApplicationSerializer(serializers.ModelSerializer):
    languages = serializers.ListField(
        source='supported_languages',
        child=serializers.ChoiceField(choices=('bn', 'en')),
        min_length=1,
    )
    specialties = serializers.ListField(
        child=serializers.CharField(max_length=120, trim_whitespace=True),
        min_length=1,
    )
    can_author = serializers.BooleanField(read_only=True)

    class Meta:
        model = ScholarProfile
        fields = (
            'institution', 'biography', 'public_bio', 'qualifications',
            'specialties', 'languages', 'verification_status',
            'is_suspended', 'can_author', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'verification_status', 'is_suspended', 'can_author',
            'created_at', 'updated_at',
        )
        extra_kwargs = {
            'institution': {'required': True, 'allow_blank': False},
            'biography': {'required': True, 'allow_blank': False},
            'public_bio': {'required': True, 'allow_blank': False},
            'qualifications': {'required': True, 'allow_blank': False},
        }

    def validate_specialties(self, value):
        cleaned = list(dict.fromkeys(item.strip() for item in value if item.strip()))
        if not cleaned:
            raise serializers.ValidationError('Add at least one specialty.')
        return cleaned

    def validate_languages(self, value):
        return list(dict.fromkeys(value))


class ScholarModerationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    display_name = serializers.SerializerMethodField()
    languages = serializers.ListField(source='supported_languages', read_only=True)

    class Meta:
        model = ScholarProfile
        fields = (
            'user_id', 'username', 'email', 'display_name', 'institution',
            'qualifications', 'specialties', 'languages', 'biography',
            'public_bio', 'verification_status', 'verification_note',
            'verified_at', 'is_suspended', 'created_at', 'updated_at',
        )

    def get_display_name(self, scholar):
        profile = getattr(scholar.user, 'userprofile', None)
        return (profile.display_name if profile else '') or scholar.user.username


class ScholarModerationActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=('approve', 'reject', 'suspend', 'unsuspend'))
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        if attrs['action'] in ('reject', 'suspend') and not attrs.get('note', '').strip():
            raise serializers.ValidationError({'note': 'Add a note for this decision.'})
        return attrs


class ModerationQuestionSerializer(serializers.ModelSerializer):
    asker_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            'id', 'status', 'language', 'original_title', 'original_body',
            'category_name', 'madhhab_preference', 'created_at', 'submitted_at',
            'asker_name', 'assigned_scholar_id', 'assigned_reviewer_id',
        )

    def get_asker_name(self, question):
        profile = getattr(question.owner, 'userprofile', None)
        return (profile.display_name if profile else '') or question.owner.username

    def get_category_name(self, question):
        return question.category.name_en if question.category_id else ''


class ReportSerializer(serializers.ModelSerializer):
    publication_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Report
        fields = ('id', 'publication_id', 'reason', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')

    def validate_publication_id(self, value):
        if not Publication.objects.filter(pk=value, visibility='public').exists():
            raise serializers.ValidationError('Fatwa not found.')
        return value

    def create(self, validated_data):
        return Report.objects.create(
            reporter=self.context['request'].user,
            publication_id=validated_data.pop('publication_id'),
            **validated_data,
        )


class BookmarkSerializer(serializers.ModelSerializer):
    publication_id = serializers.IntegerField(write_only=True)
    fatwa = PublicFatwaSerializer(source='publication', read_only=True)

    class Meta:
        model = Bookmark
        fields = ('id', 'publication_id', 'fatwa', 'created_at')
        read_only_fields = ('id', 'fatwa', 'created_at')

    def validate_publication_id(self, value):
        if not Publication.objects.filter(pk=value, visibility='public').exists():
            raise serializers.ValidationError('Fatwa not found.')
        return value

    def create(self, validated_data):
        bookmark, created = Bookmark.objects.get_or_create(
            user=self.context['request'].user,
            publication_id=validated_data['publication_id'],
        )
        self.context['created'] = created
        return bookmark


class AnswerActionSerializer(serializers.Serializer):
    body = serializers.CharField()
    language = serializers.ChoiceField(choices=('bn', 'en'), required=False)
    references = serializers.JSONField(required=False, default=list)
    methodology_id = serializers.IntegerField(required=False, allow_null=True)
    action = serializers.ChoiceField(choices=('save', 'submit_for_review'), default='save')


class ReviewActionSerializer(serializers.Serializer):
    feedback = serializers.CharField(required=False, allow_blank=True)


class AssignmentSerializer(serializers.Serializer):
    scholar_id = serializers.IntegerField()
    reviewer_id = serializers.IntegerField()


class QuestionActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=('submit', 'withdraw', 'clarify', 'change_consent')
    )
    is_public = serializers.BooleanField(required=False)
    public_title = serializers.CharField(required=False, allow_blank=True, max_length=240)
    public_body = serializers.CharField(required=False, allow_blank=True)
    body = serializers.CharField(required=False, allow_blank=True)


class NotificationSerializer(serializers.ModelSerializer):
    read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('id', 'kind', 'title', 'body', 'target_url', 'read', 'created_at')

    def get_read(self, notification):
        return bool(notification.read_at)
