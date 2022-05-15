from ..base.api.permissions import (AllowAny, IsAuthenticated, HRPerm, EmployeePerm, ApprovalPerm, NoDuesPerm, IsSuperUser,
                                    PermissionComponent, ResourcePermission)


class IsTheSameUser(PermissionComponent):
    def has_permission(self, request, view):
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj=None):
        return request.user.is_authenticated() and request.user.pk == obj.pk


class UserPermissions(ResourcePermission):
    enough_perms = AllowAny()
    global_perms = None
    retrieve_perms = IsTheSameUser()
    update_perms = IsTheSameUser()
    partial_update_perms = IsTheSameUser()
    destroy_perms = IsTheSameUser()
    list_perms = AllowAny()
    login_perms = AllowAny()
    logout_perms = IsAuthenticated()
    password_change_perms = AllowAny()
    register_perms = AllowAny()
    registered_list_perms = AllowAny()
    approve_perms = AllowAny()
    permission_group_perms = AllowAny()
    reset_password_perms = AllowAny()
    send_otp_perms = AllowAny()
    resend_otp_perms = AllowAny()
    verify_otp_perms = AllowAny()
    user_reset_mail_perms = AllowAny()
    user_clone_perms = AllowAny()
    google_signup_perms = AllowAny()
    facebook_signup_perms = AllowAny()
    employee_list_perms = HRPerm()
    separated_list_perms = HRPerm()
    superadmin_password_reset_perms = HRPerm()
