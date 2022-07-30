from ..base.api.permissions import (AllowAny, ResourcePermission, UserPerm, AdminPerm)


class LocationPermissions(ResourcePermission):
    metadata_perms = AllowAny()
    enough_perms = None
    global_perms = None
    retrieve_perms = UserPerm()
    create_perms = AdminPerm()
    update_perms = AdminPerm()
    create_with_base64_perms = AllowAny()
    multiple_perms = AllowAny()
    location_list_perms = AdminPerm() | UserPerm()
    get_location_count_perms = AdminPerm() |UserPerm()
    user_locations_perms = AdminPerm() | UserPerm()
    graph_data_perms = AdminPerm() | UserPerm()


class DevicePermissions(ResourcePermission):
    metadata_perms = AllowAny()
    enough_perms = None
    global_perms = None
    destroy_perms = AdminPerm() | UserPerm()
    retrieve_perms = AdminPerm() | UserPerm()
    create_perms = AdminPerm()
    update_perms = AdminPerm() | UserPerm()
    list_perms = AdminPerm() | UserPerm()
    partial_update_perms = AdminPerm() | UserPerm()
    location_devices_perms = AdminPerm() | UserPerm()


class InverterDataPermissions(ResourcePermission):
    metadata_perms = AllowAny()
    enough_perms = None
    global_perms = None
    destroy_perms = AdminPerm()
    retrieve_perms = AdminPerm()
    create_perms = AllowAny()
    update_perms = AdminPerm()
    list_perms = AdminPerm() | UserPerm()
    partial_update_perms = AdminPerm()
    location_devices_perms = AdminPerm() | UserPerm()
    inverter_data_perms = AllowAny()


class ZipReportPermissions(ResourcePermission):
    metadata_perms = AllowAny()
    enough_perms = None
    global_perms = None
    destroy_perms = AdminPerm() | UserPerm()
    retrieve_perms = AdminPerm() | UserPerm()
    create_perms = AdminPerm() | UserPerm()
    update_perms = AdminPerm() | UserPerm()
    list_perms = AdminPerm() | UserPerm()
    report_zip_perms = AdminPerm() | UserPerm()
