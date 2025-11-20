from rest_framework.permissions import BasePermission

from .models import UserProfile


class IsSuperAdmin(BasePermission):
    """
    Allows access only to users with the super admin role.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, "userprofile", None)
        return bool(profile and profile.role == UserProfile.ROLE_SUPER_ADMIN)


class IsStaffMember(BasePermission):
    """
    Allows access to super admins, employees, and cooks.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, "userprofile", None)
        return bool(profile and profile.role in {
            UserProfile.ROLE_SUPER_ADMIN,
            UserProfile.ROLE_EMPLOYEE,
            UserProfile.ROLE_COOK,
        })
from rest_framework.permissions import BasePermission

from .models import UserProfile


def _get_user_role(user):
    if not user or not user.is_authenticated:
        return None
    try:
        return user.userprofile.role
    except UserProfile.DoesNotExist:
        return None


class IsSuperAdmin(BasePermission):
    """
    Allows access only to users with the super admin role.
    """

    def has_permission(self, request, view):
        return _get_user_role(request.user) == UserProfile.ROLE_SUPER_ADMIN


class IsStaffMember(BasePermission):
    """
    Allows access to super admins, employees, and cooks.
    """

    STAFF_ROLES = {
        UserProfile.ROLE_SUPER_ADMIN,
        UserProfile.ROLE_EMPLOYEE,
        UserProfile.ROLE_COOK,
    }

    def has_permission(self, request, view):
        return _get_user_role(request.user) in self.STAFF_ROLES


class IsStudent(BasePermission):
    """
    Allows access only to students.
    """

    def has_permission(self, request, view):
        return _get_user_role(request.user) == UserProfile.ROLE_STUDENT

