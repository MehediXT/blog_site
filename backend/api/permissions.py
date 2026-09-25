"""Reusable role and object access rules for the public API."""

from rest_framework.permissions import BasePermission


def is_verified_scholar(user):
    """Only approved, active scholar profiles can author or review answers."""
    if not user or not user.is_authenticated:
        return False
    try:
        return user.scholarprofile.can_author
    except AttributeError:
        return False


def is_moderator(user):
    """Staff and members of the moderator or administrator groups can moderate."""
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.groups.filter(name__in=('moderator', 'administrator')).exists()
        )
    )


def question_for_object(obj):
    """Resolve a question from a question, clarification, or answer revision."""
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
    """Allow answer authoring and review only for approved, unsuspended scholars."""

    message = 'An approved, active scholar profile is required.'

    def has_permission(self, request, view):
        return is_verified_scholar(request.user)


class IsModerator(BasePermission):
    """Allow moderation endpoints to staff and moderator/administrator groups."""

    message = 'Moderator permission is required.'

    def has_permission(self, request, view):
        return is_moderator(request.user)


class IsQuestionParticipant(BasePermission):
    """Allow the asker, assigned scholar/reviewer, or moderator to access a question."""

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
    """Restrict question editing, submission, withdrawal, and consent to its asker."""

    message = 'Only the asker can perform this action.'

    def has_object_permission(self, request, view, obj):
        question = question_for_object(obj)
        return bool(
            question
            and request.user.is_authenticated
            and question.owner_id == request.user.id
        )


class IsClarificationParticipant(IsQuestionParticipant):
    """Clarifications are limited to the asker, assigned team, and moderators."""

    message = 'Only the asker, assigned team, or a moderator can add clarifications.'


class IsAssignedScholar(BasePermission):
    """Allow only the assigned scholar to create or update an answer draft."""

    message = 'This question is not assigned to you as the answering scholar.'

    def has_object_permission(self, request, view, obj):
        question = question_for_object(obj)
        return bool(
            question
            and request.user.is_authenticated
            and question.assigned_scholar_id == request.user.id
        )


class IsAssignedReviewer(BasePermission):
    """Allow only the assigned reviewer to decide an answer revision."""

    message = 'This answer is not assigned to you for review.'

    def has_object_permission(self, request, view, obj):
        question = question_for_object(obj)
        return bool(
            question
            and request.user.is_authenticated
            and question.assigned_reviewer_id == request.user.id
        )
