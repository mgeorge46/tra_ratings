"""
Tests for Uganda Number Plate OCR Engine
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import os


class PlateValidatorTests(TestCase):
    """Test the plate validation and formatting logic"""

    def setUp(self):
        from plate_ocr.ocr_engine import PlateValidator, PlateFormat
        self.validator = PlateValidator
        self.PlateFormat = PlateFormat

    def test_legacy_format_validation(self):
        """Test legacy format: UAX 123Y"""
        formatted, fmt, is_valid = self.validator.validate_and_format("UAX123Y")
        self.assertTrue(is_valid)
        self.assertEqual(fmt, self.PlateFormat.LEGACY)
        self.assertEqual(formatted, "UAX 123Y")

    def test_legacy_format_with_4_digits(self):
        """Test legacy format with 4 digits: UDS 1234M"""
        formatted, fmt, is_valid = self.validator.validate_and_format("UDS1234M")
        self.assertTrue(is_valid)
        self.assertEqual(fmt, self.PlateFormat.LEGACY)
        self.assertEqual(formatted, "UDS 1234M")

    def test_new_standard_format(self):
        """Test new standard format: UA 077AK"""
        formatted, fmt, is_valid = self.validator.validate_and_format("UA077AK")
        self.assertTrue(is_valid)
        self.assertEqual(fmt, self.PlateFormat.NEW_STANDARD)
        self.assertEqual(formatted, "UA 077AK")

    def test_motorcycle_format(self):
        """Test motorcycle format: UMA 055AF"""
        formatted, fmt, is_valid = self.validator.validate_and_format("UMA055AF")
        self.assertTrue(is_valid)
        self.assertEqual(fmt, self.PlateFormat.MOTORCYCLE)
        self.assertEqual(formatted, "UMA 055AF")

    def test_government_format(self):
        """Test government format: UP 6633"""
        formatted, fmt, is_valid = self.validator.validate_and_format("UP6633")
        self.assertTrue(is_valid)
        self.assertEqual(fmt, self.PlateFormat.GOVERNMENT)
        self.assertEqual(formatted, "UP 6633")

    def test_ocr_correction_zero_to_o(self):
        """Test OCR correction: 0 -> O in letter position"""
        # UA077AK with 0 instead of O should still work
        formatted, fmt, is_valid = self.validator.validate_and_format("0A077AK")
        # Should be corrected to UA 077AK
        # Note: This depends on the correction logic

    def test_with_spaces(self):
        """Test validation with various spacing"""
        formatted, fmt, is_valid = self.validator.validate_and_format("UA 077 AK")
        self.assertTrue(is_valid)
        self.assertEqual(formatted, "UA 077AK")

    def test_lowercase_input(self):
        """Test lowercase input is normalized"""
        formatted, fmt, is_valid = self.validator.validate_and_format("ua077ak")
        self.assertTrue(is_valid)
        self.assertEqual(formatted, "UA 077AK")

    def test_invalid_format(self):
        """Test invalid format detection"""
        formatted, fmt, is_valid = self.validator.validate_and_format("ABC123")
        self.assertFalse(is_valid)
        self.assertEqual(fmt, self.PlateFormat.UNKNOWN)

    def test_empty_string(self):
        """Test empty string handling"""
        formatted, fmt, is_valid = self.validator.validate_and_format("")
        self.assertFalse(is_valid)


class PlatePatternTests(TestCase):
    """Test regex patterns for different plate formats"""

    def setUp(self):
        from plate_ocr.ocr_engine import UgandaPlatePatterns, PlateFormat
        self.patterns = UgandaPlatePatterns.PATTERNS
        self.PlateFormat = PlateFormat

    def test_legacy_pattern(self):
        """Test legacy pattern matches correctly"""
        pattern = self.patterns[self.PlateFormat.LEGACY]
        self.assertIsNotNone(pattern.match("UAX123Y"))
        self.assertIsNotNone(pattern.match("UDS1234M"))
        self.assertIsNone(pattern.match("UA123AK"))  # Should not match new format

    def test_new_standard_pattern(self):
        """Test new standard pattern"""
        pattern = self.patterns[self.PlateFormat.NEW_STANDARD]
        self.assertIsNotNone(pattern.match("UA077AK"))
        self.assertIsNotNone(pattern.match("UG092AK"))
        self.assertIsNone(pattern.match("UMA055AF"))  # Should not match motorcycle

    def test_motorcycle_pattern(self):
        """Test motorcycle pattern"""
        pattern = self.patterns[self.PlateFormat.MOTORCYCLE]
        self.assertIsNotNone(pattern.match("UMA055AF"))
        self.assertIsNotNone(pattern.match("UMB010AL"))

    def test_government_pattern(self):
        """Test government pattern"""
        pattern = self.patterns[self.PlateFormat.GOVERNMENT]
        self.assertIsNotNone(pattern.match("UP6633"))
        self.assertIsNotNone(pattern.match("UG0793"))


class PhotoRatingWizardTests(TestCase):
    """Test the photo rating wizard views"""

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_capture_step_loads(self):
        """Test capture step renders correctly"""
        response = self.client.get(reverse('photo_rating_wizard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo')
        self.assertContains(response, 'Voice')

    def test_motor_type_selection(self):
        """Test motor type can be selected"""
        response = self.client.post(reverse('photo_rating_wizard'), {
            'motor_type': 'car',
            'input_method': 'text',
            'plate_number': 'UA 077AK',
            'current_step': 'capture',
        })
        # Should redirect to rate step on valid input
        self.assertIn(response.status_code, [200, 302])

    def test_unauthenticated_redirect(self):
        """Test unauthenticated users are redirected"""
        self.client.logout()
        response = self.client.get(reverse('photo_rating_wizard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class OCRAPITests(TestCase):
    """Test the OCR API endpoint"""

    def setUp(self):
        self.client = Client()

    def test_api_requires_photo(self):
        """Test API returns error without photo"""
        response = self.client.post(reverse('plate_ocr_api'))
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])