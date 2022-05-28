from ..base.api.permissions import (AllowAny, ResourcePermission, UserPerm, AdminPerm)


class LocationPermissions(ResourcePermission):
    metadata_perms = AllowAny()
    enough_perms = None
    global_perms = None
    retrieve_perms = UserPerm()
    create_perms = AdminPerm()
    update_perms = AllowAny()
    create_with_base64_perms = AllowAny()
    multiple_perms = AllowAny()
    location_list_perms = AllowAny()
    get_location_count_perms = AllowAny()
    user_locations_perms=UserPerm()


class DevicePermissions(ResourcePermission):
    metadata_perms = AllowAny()
    enough_perms = None
    global_perms = None
    destroy_perms = AllowAny()
    retrieve_perms = AllowAny()
    create_perms = AllowAny()
    update_perms = AllowAny()
    list_perms = AllowAny()
    partial_update_perms = AllowAny()
    location_devices_perms = UserPerm()


class InverterDataPermissions(ResourcePermission):
    metadata_perms = AllowAny()
    enough_perms = None
    global_perms = None
    destroy_perms = AdminPerm()
    retrieve_perms = AdminPerm()
    create_perms = AllowAny()
    update_perms = AdminPerm()
    list_perms = AllowAny()
    partial_update_perms = AdminPerm()
    location_devices_perms = UserPerm()

