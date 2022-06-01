from django.core.exceptions import ValidationError
from django.conf import settings


def file_extension_validator(value):
    valid_extensions_file = ('pdf', 'zip')
    try:
        if value:
            file_name = value.name
            file_extension = file_name.split('.')[-1].lower()
            if file_extension in valid_extensions_file:
                if value.size > int(settings.MAX_UPLOAD_SIZE):
                    raise ValidationError("Please keep the file size under 100 MB")
            else:
                raise ValidationError("Please upload file in PDF/ZIP/ formats.")
    except Exception:
        return True


def image_extension_validator(value):
    valid_extensions_image = ('png', 'jpeg', 'jpg', 'pdf')
    try:
        if value:
            image_name = value.name
            image_file_extension = image_name.split('.')[-1].lower()
            if image_file_extension in valid_extensions_image:
                if value.size > int(settings.MAX_UPLOAD_SIZE):
                    raise ValidationError({"detail": "Please keep the file size under 10 MB"})
            else:
                raise ValidationError({"detail": "Please upload image in PDF/PNG/JPG/JPEG formats."})
    except Exception:
        return True
