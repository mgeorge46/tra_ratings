from cryptography.fernet import Fernet
import base64
import re
from django.conf import settings
from django.core.exceptions import ValidationError

# Derive a Fernet key from your Django SECRET_KEY (use a separate key in production!)
SECRET_KEY = settings.SECRET_KEY[:32]
CIPHER = Fernet(base64.urlsafe_b64encode(SECRET_KEY.encode()))

def encrypt_data(data: str) -> str:
    """Encrypt a string using Fernet encryption."""
    return CIPHER.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    """Decrypt a string previously encrypted with encrypt_data()."""
    return CIPHER.decrypt(data.encode()).decode()

# Regular expressions covering both old and new private-vehicle plate formats.
# Legacy format: UAR 1234L → starts with 'U', then two letters, 3–4 digits, and one letter.
LEGACY_PLATE_REGEX = re.compile(r'^U[A-Z]{2}[0-9]{3,4}[A-Z]$')

# New format: UA 123MG → starts with 'U', one letter, 3 digits, and two letters.
NEW_PLATE_REGEX = re.compile(r'^U[A-Z][0-9]{3}[A-Z]{2}$')

def validate_ug_plate_format(value: str) -> str:
    """
    Normalise and validate a Ugandan number plate.
    Accepts input with inconsistent spacing or casing, matches both legacy
    (e.g. 'UDS164M' or 'UDS 164M') and new (e.g. 'UA123MG' or 'UA 123MG')
    formats.  Returns a canonicalised plate (with a space inserted after
    the prefix) if valid, or raises ValidationError otherwise.
    """
    # Remove whitespace and convert to uppercase
    cleaned = re.sub(r'\s+', '', value).upper()

    if LEGACY_PLATE_REGEX.match(cleaned):
        # Insert a space after the three-letter prefix: UAA1234L -> UAA 1234L
        return f"{cleaned[:3]} {cleaned[3:]}"
    if NEW_PLATE_REGEX.match(cleaned):
        # Insert a space after the two-character prefix: UA123MG -> UA 123MG
        return f"{cleaned[:2]} {cleaned[2:5]}{cleaned[5:]}"

    # If neither pattern matches, raise a validation error
    raise ValidationError("Invalid Ugandan number plate. Please double-check.")
