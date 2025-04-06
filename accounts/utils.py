import phonenumbers
from geoip2.database import Reader
from phonenumbers import parse, is_valid_number, format_number, PhoneNumberFormat
from phonenumbers.phonenumberutil import NumberParseException


# Load GeoIP database (download and place it in your project)
geoip_db_path = 'D:\\Dev\\Django\\tra_ratings\\external_db\\GeoLite2-Country.mmdb'

def normalize_phone_number(phone, ip_address=None):
    default_country_code = "+256"  # Default to Uganda

    try:
        # Load the GeoIP database
        reader = Reader(geoip_db_path)

        # Detect the user's location based on IP
        if ip_address:
            location = reader.country(ip_address)
            country_code = f"+{phonenumbers.country_code_for_region(location.country.iso_code)}"
        else:
            country_code = default_country_code
    except FileNotFoundError:
        # Fallback to default country code if database is missing
        country_code = default_country_code
    except Exception as e:
        # Log other exceptions for debugging
        print(f"Error detecting country code: {e}")
        country_code = default_country_code

    # Normalize the phone number
    if phone.startswith('+'):
        return phone  # Already in international format
    elif phone.startswith('0'):
        return country_code + phone[1:]  # Replace leading zero
    elif phone.startswith(country_code[1:]):  # Country code without '+'
        return f"+{phone}"
    else:
        return phone  # Assume it is already normalized


def normalize_phone_number_model(phone, default_country="UG"):
    """
    Normalize a phone number to international format.
    :param phone: The phone number to normalize.
    :param default_country: The default country code for normalization (e.g., 'UG' for Uganda).
    :return: The normalized phone number in international format (e.g., +256754605808).
    """
    try:
        # Parse the phone number
        parsed_number = parse(phone, default_country)

        # Check if the parsed number is valid
        if not is_valid_number(parsed_number):
            raise ValueError("Invalid phone number.")

        # Format the number in international format
        return format_number(parsed_number, PhoneNumberFormat.E164)  # Always starts with `+`
    except NumberParseException as e:
        raise ValueError(f"Error parsing phone number: {e}")

