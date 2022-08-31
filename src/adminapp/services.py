import zipfile


def zip_file(archive_list, zfilename):
    zout = zipfile.ZipFile(zfilename, "w", zipfile.ZIP_DEFLATED)
    for fname in archive_list:
        zout.write(fname)
    zout.close()


def alarm_status_check(value):
    if value == int("0x5500", 16) or value == int("0x9100", 16):
        return "On-Error"
    else:
        return "Online"


def operation_state_check(value):
    if value == int("0x0", 16):
        return "Run"
    elif value == int("0x8000", 16):
        return "Stop"
    elif value == int("0x1300", 16):
        return "Key stop"
    elif value == int("0x1500", 16):
        return "Emergency Stop"
    elif value == int("0x1400", 16):
        return "Standby"
    elif value == int("0x1200", 16):
        return "Initial standby"
    elif value == int("0x1600", 16):
        return "Starting"
    elif value == int("0x9100", 16):
        return "Alarm run"
    elif value == int("0x8100", 16):
        return "Derating run"
    elif value == int("0x8200", 16):
        return "Dispatch run"
    elif value == int("0x5500", 16):
        return "Fault"
    else:
        return "Undefined State"


def alarm_name_check(value):
    if value == int("0x0017", 16):
        return "PV conn fail"
    elif value == int("0x0046", 16):
        return "FAN Fail"
    elif value == int("0x0000", 16):
        return "OK"
    else:
        return "Device abnormal"
