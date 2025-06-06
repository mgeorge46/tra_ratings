from cryptography.fernet import Fernet
import base64
from django.conf import settings
import re
from django.core.exceptions import ValidationError

# Use a unique key for encryption (set this in your settings.py)
SECRET_KEY = settings.SECRET_KEY[:32]
CIPHER = Fernet(base64.urlsafe_b64encode(SECRET_KEY.encode()))

def encrypt_data(data):
    return CIPHER.encrypt(data.encode()).decode()

def decrypt_data(data):
    return CIPHER.decrypt(data.encode()).decode()

# Combined format regex: handles old and new formats
import re
from django.core.exceptions import ValidationError

# Legacy: UAR1234L
LEGACY_PLATE_REGEX = re.compile(r'^U[A-Z]{2}[0-9]{3,4}[A-Z]$')

# New: UA123MG
NEW_PLATE_REGEX = re.compile(r'^U[A-Z][0-9]{3}[A-Z]{2}$')

def validate_ug_plate_format(value):
    """
    Smart validator for Ugandan number plates:
    - Legacy format: UAR 1234L → 3-letter prefix, 3–4 digits, 1-letter suffix
    - New format: UA 123MG → 2-letter prefix, 3 digits, 2-letter suffix
    - Accepts input with inconsistent spacing, casing, or formatting
    """

    # Step 1: Normalize input
    cleaned = re.sub(r'\s+', '', value.upper())  # e.g., ' ua 07 5ak ' → 'UA075AK'

    # Step 2: Match correct pattern
    if LEGACY_PLATE_REGEX.match(cleaned):
        formatted = f"{cleaned[:3]} {cleaned[3:]}"  # E.g., UAR1234L → UAR 1234L
    elif NEW_PLATE_REGEX.match(cleaned):
        formatted = f"{cleaned[:2]} {cleaned[2:5]}{cleaned[5:]}"  # E.g., UA075AK → UA 075AK
    else:
        raise ValidationError("Invalid Ugandan number plate. Please double-check.")

    return formatted