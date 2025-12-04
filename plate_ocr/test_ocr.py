#!/usr/bin/env python
"""
Quick test script for the Uganda Plate OCR Engine
Run this to verify the OCR is working correctly.

Usage from command line:
    python test_ocr.py                          # Run pattern tests only
    python test_ocr.py path/to/plate_image.jpg  # Test with specific image
    python test_ocr.py --all                    # Test with sample images in project

Usage from Django shell:
    from plate_ocr.test_ocr import test_ocr
    test_ocr()  # or test_ocr("path/to/image.jpg")
"""

import sys
import os

# Setup Django environment if running standalone
def setup_django():
    """Setup Django settings for standalone script execution"""
    # Find the project root (where manage.py is)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # Go up one level from plate_ocr
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tra_ratings.settings')
    
    try:
        import django
        django.setup()
    except Exception as e:
        print(f"Note: Django setup skipped ({e})")


def test_patterns():
    """Test plate pattern validation without OCR"""
    from .ocr_engine import PlateValidator, PlateFormat
    
    print("\n[Test 1] Pattern Validation")
    print("-" * 40)
    
    test_plates = [
        ("UA077AK", "New Standard", True),
        ("UG092AK", "New Standard", True),
        ("UDS164M", "Legacy", True),
        ("UAX123Y", "Legacy", True),
        ("UMA055AF", "Motorcycle", True),
        ("UMB010AL", "Motorcycle", True),
        ("UP6633", "Government", True),
        ("UG0793", "Government", True),
        ("ABC123", "Invalid", False),
        ("UABC12", "Invalid", False),
    ]
    
    validator = PlateValidator()
    passed = 0
    failed = 0
    
    for plate, expected_type, should_be_valid in test_plates:
        formatted, fmt, is_valid = validator.validate_and_format(plate)
        
        if is_valid == should_be_valid:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1
        
        print(f"  {status} {plate:12} -> {formatted:12} ({fmt.value})")
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_corrections():
    """Test OCR correction logic"""
    from .ocr_engine import PlateValidator
    
    print("\n[Test 2] OCR Corrections")
    print("-" * 40)
    
    validator = PlateValidator()
    
    ocr_errors = [
        ("0A077AK", "UA 077AK"),    # 0 -> U at start
        ("uds164m", "UDS 164M"),    # lowercase
        ("UA 077 AK", "UA 077AK"),  # extra spaces
        ("UA0T7AK", "UA 077AK"),    # T -> 7 in digit position (might not work)
        ("UM A055AF", "UMA 055AF"), # space in wrong place
    ]
    
    passed = 0
    for raw, expected in ocr_errors:
        formatted, _, is_valid = validator.validate_and_format(raw)
        # Compare without spaces for flexibility
        matches = formatted.replace(" ", "") == expected.replace(" ", "")
        status = "✓" if matches else "~"
        if matches:
            passed += 1
        print(f"  {status} '{raw}' -> '{formatted}' (expected: '{expected}')")
    
    print(f"\n  Results: {passed}/{len(ocr_errors)} corrections working")
    return True


def test_ocr_engines():
    """Test OCR engine availability"""
    print("\n[Test 3] OCR Engine Status")
    print("-" * 40)
    
    # Test OpenCV
    try:
        import cv2
        print(f"  ✓ OpenCV: {cv2.__version__}")
    except ImportError:
        print("  ✗ OpenCV: NOT INSTALLED")
        print("    Run: pip install opencv-python-headless")
        return False
    
    # Test NumPy
    try:
        import numpy as np
        print(f"  ✓ NumPy: {np.__version__}")
    except ImportError:
        print("  ✗ NumPy: NOT INSTALLED")
        print("    Run: pip install numpy")
        return False
    
    # Test EasyOCR
    try:
        import easyocr
        print(f"  ✓ EasyOCR: Available")
    except ImportError:
        print("  ⚠ EasyOCR: NOT INSTALLED (optional)")
        print("    Run: pip install easyocr")
    
    # Test Tesseract
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"  ✓ Tesseract: {version}")
    except Exception as e:
        print(f"  ⚠ Tesseract: NOT AVAILABLE ({e})")
        print("    Install from: https://github.com/UB-Mannheim/tesseract/wiki")
    
    return True


def test_image(image_path: str):
    """Test OCR on a specific image"""
    print(f"\n[Test 4] Processing Image")
    print("-" * 40)
    print(f"  File: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"  ✗ File not found!")
        return False
    
    try:
        import cv2
        from .ocr_engine import get_ocr_engine, ImagePreprocessor
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"  ✗ Could not read image")
            return False
        
        print(f"  Image size: {image.shape[1]}x{image.shape[0]}")
        
        # Detect plate regions
        preprocessor = ImagePreprocessor()
        regions = preprocessor.detect_plate_region(image)
        print(f"  Detected regions: {len(regions)}")
        
        # Run OCR
        print("  Running OCR (this may take a moment)...")
        engine = get_ocr_engine()
        result = engine.extract_plate(image)
        
        if result.is_valid:
            print(f"\n  ✓ SUCCESS!")
            print(f"    Plate: {result.formatted_plate}")
            print(f"    Format: {result.plate_format.value}")
            print(f"    Confidence: {result.confidence:.1%}")
            return True
        else:
            print(f"\n  ✗ Extraction failed: {result.error}")
            if result.raw_detections:
                print(f"    Raw detections: {result.raw_detections[:5]}")
            return False
            
    except ImportError as e:
        print(f"  ✗ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_ocr(image_path=None):
    """Main test function"""
    print("=" * 50)
    print("Uganda Number Plate OCR Test Suite")
    print("=" * 50)
    
    # Test 1: Pattern validation
    test_patterns()
    
    # Test 2: OCR corrections
    test_corrections()
    
    # Test 3: Engine availability
    engines_ok = test_ocr_engines()
    
    # Test 4: Image processing (if path provided)
    if image_path and engines_ok:
        test_image(image_path)
    elif image_path and not engines_ok:
        print("\n[Test 4] Skipped - Install dependencies first")
    
    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)
    
    if not engines_ok:
        print("\n⚠️  Install required packages:")
        print("   pip install opencv-python-headless easyocr pytesseract numpy")


def find_sample_images():
    """Find sample images in the project"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Common locations for test images
    search_paths = [
        os.path.join(project_root, 'media'),
        os.path.join(project_root, 'static'),
        os.path.join(project_root, 'test_images'),
        os.path.join(current_dir, 'test_images'),
    ]
    
    images = []
    for path in search_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    images.append(os.path.join(path, file))
    
    return images


if __name__ == "__main__":
    setup_django()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--all":
            # Test all sample images
            images = find_sample_images()
            if images:
                print(f"Found {len(images)} sample images")
                for img in images[:5]:  # Test first 5
                    test_ocr(img)
            else:
                print("No sample images found. Run: python test_ocr.py path/to/image.jpg")
        else:
            # Test specific image
            test_ocr(arg)
    else:
        # Run basic tests only
        test_ocr()
