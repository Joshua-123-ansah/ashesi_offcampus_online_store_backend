from rest_framework.permissions import BasePermission

from .models import UserProfile


def _get_user_role(user):
    if not user or not user.is_authenticated:
        return None
    profile = getattr(user, 'userprofile', None)
    return profile.role if profile else None


class IsSuperAdmin(BasePermission):
    """
    Allows access only to users with the super admin role.
    """

    def has_permission(self, request, view):
        return _get_user_role(request.user) == UserProfile.ROLE_SUPER_ADMIN


class IsStaffMember(BasePermission):
    """
    Allows access to super admins, employees, cooks, and shop managers.
    """

    STAFF_ROLES = {
        UserProfile.ROLE_SUPER_ADMIN,
        UserProfile.ROLE_SHOP_MANAGER,
        UserProfile.ROLE_EMPLOYEE,
        UserProfile.ROLE_COOK,
    }

    def has_permission(self, request, view):
        return _get_user_role(request.user) in self.STAFF_ROLES


class IsShopManager(BasePermission):
    """
    Allows access to super admins and shop managers.
    """

    def has_permission(self, request, view):
        role = _get_user_role(request.user)
        return role in {UserProfile.ROLE_SUPER_ADMIN, UserProfile.ROLE_SHOP_MANAGER}


class IsStudent(BasePermission):
    """
    Allows access only to students.
    """

    def has_permission(self, request, view):
        return _get_user_role(request.user) == UserProfile.ROLE_STUDENT

