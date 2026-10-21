from rest_framework.permissions import BasePermission


def is_verified_scholar(user):
    if not user or not user.is_authenticated:
        return False
    try:
        return user.scholarprofile.can_author
    except AttributeError:
        return False


def is_moderator(user):
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.groups.filter(name__in=('moderator', 'administrator')).exists()
        )
    )


def question_for_object(obj):
    if obj is None:
        return None
    if hasattr(obj, 'assigned_scholar_id') and hasattr(obj, 'assigned_reviewer_id'):
        return obj
    question = getattr(obj, 'question', None)
    if question is not None:
        return question
    answer = getattr(obj, 'answer', None)
    if answer is not None:
        return getattr(answer, 'question', None)
    return None


class IsVerifiedScholar(BasePermission):

    message = 'An approved, active scholar profile is required.'

    def has_permission(self, request, view):
        return is_verified_scholar(request.user)


class IsModerator(BasePermission):

    message = 'Moderator permission is required.'

    def has_permission(self, request, view):
        return is_moderator(request.user)


class IsQuestionParticipant(BasePermission):

    message = 'You are not allowed to access this question.'

    def has_object_permission(self, request, view, obj):
        question = question_for_object(obj)
        user = request.user
        return bool(
            question
            and user.is_authenticated
            and (
                question.owner_id == user.id
                or question.assigned_scholar_id == user.id
                or question.assigned_reviewer_id == user.id
                or is_moderator(user)
            )
        )


class IsQuestionOwner(BasePermission):

    message = 'Only the asker can perform this action.'

    def has_object_permission(self, request, view, obj):
        question = question_for_object(obj)
        return bool(
            question
            and request.user.is_authenticated
            and question.owner_id == request.user.id
        )


class IsClarificationParticipant(IsQuestionParticipant):
    message = 'Only the asker, assigned team, or a moderator can add clarifications.'


class IsAssignedScholar(BasePermission):

    message = 'This question is not assigned to you as the answering scholar.'

    def has_object_permission(self, request, view, obj):
        question = question_for_object(obj)
        return bool(
            question
            and request.user.is_authenticated
            and question.assigned_scholar_id == request.user.id
        )


class IsAssignedReviewer(BasePermission):

    message = 'This answer is not assigned to you for review.'

    def has_object_permission(self, request, view, obj):
        question = question_for_object(obj)
        return bool(
            question
            and request.user.is_authenticated
            and question.assigned_reviewer_id == request.user.id
        )
