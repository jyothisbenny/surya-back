import zipfile


def zip_file(archive_list, zfilename):
    zout = zipfile.ZipFile(zfilename, "w", zipfile.ZIP_DEFLATED)
    for fname in archive_list:
        zout.write(fname)
    zout.close()
