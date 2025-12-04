"""
Uganda Number Plate OCR Engine
Supports multiple OCR backends with preprocessing optimized for Ugandan plates.
Formats supported:
- Legacy: UAX 123Y, UDS 164M (3-letter prefix, 3-4 digits, 1 letter suffix)
- New: UA 077AK, UG 092AK (2-letter prefix, 3 digits, 2-letter suffix)
- Motorcycle: UMA 055AF (3-letter prefix, 3 digits, 2-letter suffix)
- Government/Police: UP 6633, UG 1234 (2-letter prefix, 4 digits)
"""

import re
import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PlateFormat(Enum):
    LEGACY = "legacy"  # UAX 123Y - 3 letters, 3-4 digits, 1 letter
    NEW_STANDARD = "new"  # UA 077AK - 2 letters, 3 digits, 2 letters
    MOTORCYCLE = "motorcycle"  # UMA 055AF - 3 letters, 3 digits, 2 letters
    GOVERNMENT = "government"  # UP 6633 - 2 letters, 4 digits
    UNKNOWN = "unknown"


@dataclass
class PlateResult:
    """Result from plate detection and OCR"""
    plate_text: str
    formatted_plate: str
    confidence: float
    plate_format: PlateFormat
    bounding_box: Optional[Tuple[int, int, int, int]] = None
    raw_detections: Optional[List[str]] = None
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.error is None and self.confidence > 0.5


class UgandaPlatePatterns:
    """Regex patterns for Uganda number plate formats"""

    # All patterns must start with U
    PATTERNS = {
        # Legacy format: UAX 123Y or UAX 1234Y (3 letters, 3-4 digits, 1 letter)
        PlateFormat.LEGACY: re.compile(r'^U[A-Z]{2}\s?[0-9]{3,4}[A-Z]$'),

        # New standard: UA 077AK (2 letters, 3 digits, 2 letters)
        PlateFormat.NEW_STANDARD: re.compile(r'^U[A-Z]\s?[0-9]{3}[A-Z]{2}$'),

        # Motorcycle format: UMA 055AF (3 letters, 3 digits, 2 letters)
        PlateFormat.MOTORCYCLE: re.compile(r'^U[A-Z]{2}\s?[0-9]{3}[A-Z]{2}$'),

        # Government/Police: UP 6633 (2 letters, 4 digits)
        PlateFormat.GOVERNMENT: re.compile(r'^U[A-Z]\s?[0-9]{4}$'),
    }

    # Common OCR misreads to correct
    OCR_CORRECTIONS = {
        'O': '0', 'Q': '0', 'D': '0',  # Often confused with zero
        'I': '1', 'L': '1', '|': '1',  # Often confused with one
        'Z': '2',
        'S': '5', '$': '5',
        'B': '8',
        'G': '6',
        ' ': '',  # Remove extra spaces initially
    }

    # Position-aware corrections (letters vs digits)
    DIGIT_CORRECTIONS = {'O': '0', 'I': '1', 'L': '1', 'S': '5', 'B': '8', 'G': '6', 'Z': '2'}
    LETTER_CORRECTIONS = {'0': 'O', '1': 'I', '5': 'S', '8': 'B', '6': 'G', '2': 'Z'}


class ImagePreprocessor:
    """Image preprocessing for number plate detection"""

    @staticmethod
    def preprocess_for_ocr(image: np.ndarray) -> List[np.ndarray]:
        """
        Generate multiple preprocessed versions of the image for OCR.
        Returns list of processed images to try.
        """
        results = []

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 1. Basic grayscale with contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        results.append(enhanced)

        # 2. Adaptive thresholding (good for varying lighting)
        adaptive = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        results.append(adaptive)

        # 3. Otsu's thresholding (good for bimodal images)
        _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results.append(otsu)

        # 4. Inverted (for dark text on light background)
        inverted = cv2.bitwise_not(adaptive)
        results.append(inverted)

        # 5. Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        morphed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
        results.append(morphed)

        # 6. Sharpened image
        kernel_sharp = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel_sharp)
        results.append(sharpened)

        return results

    @staticmethod
    def detect_plate_region(image: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Detect potential number plate regions in the image.
        Returns list of (cropped_region, bounding_box) tuples.
        """
        regions = []

        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply bilateral filter to reduce noise while keeping edges sharp
        filtered = cv2.bilateralFilter(gray, 11, 17, 17)

        # Edge detection
        edges = cv2.Canny(filtered, 30, 200)

        # Find contours
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Sort by area and take top candidates
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

        for contour in contours:
            # Approximate the contour
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.018 * peri, True)

            # Look for rectangular shapes (4 corners)
            if len(approx) >= 4 and len(approx) <= 6:
                x, y, w, h = cv2.boundingRect(approx)

                # Check aspect ratio (plates are typically 2:1 to 5:1)
                aspect_ratio = w / float(h) if h > 0 else 0

                if 1.5 <= aspect_ratio <= 6.0:
                    # Check minimum size
                    if w > 60 and h > 20:
                        # Add padding
                        padding = 10
                        x1 = max(0, x - padding)
                        y1 = max(0, y - padding)
                        x2 = min(image.shape[1], x + w + padding)
                        y2 = min(image.shape[0], y + h + padding)

                        cropped = image[y1:y2, x1:x2]
                        if cropped.size > 0:
                            regions.append((cropped, (x1, y1, x2, y2)))

        # Also try color-based detection for yellow plates
        if len(image.shape) == 3:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Yellow plate detection
            lower_yellow = np.array([15, 80, 80])
            upper_yellow = np.array([35, 255, 255])
            yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

            # White plate detection
            lower_white = np.array([0, 0, 180])
            upper_white = np.array([180, 30, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)

            for mask in [yellow_mask, white_mask]:
                # Find contours in the mask
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / float(h) if h > 0 else 0

                    if 1.5 <= aspect_ratio <= 6.0 and w > 60 and h > 20:
                        padding = 10
                        x1 = max(0, x - padding)
                        y1 = max(0, y - padding)
                        x2 = min(image.shape[1], x + w + padding)
                        y2 = min(image.shape[0], y + h + padding)

                        cropped = image[y1:y2, x1:x2]
                        if cropped.size > 0:
                            regions.append((cropped, (x1, y1, x2, y2)))

        # Remove duplicates based on overlap
        regions = ImagePreprocessor._remove_overlapping_regions(regions)

        # If no regions found, return the whole image
        if not regions:
            regions.append((image, (0, 0, image.shape[1], image.shape[0])))

        return regions

    @staticmethod
    def _remove_overlapping_regions(regions: List[Tuple[np.ndarray, Tuple[int, int, int, int]]]) -> List:
        """Remove overlapping regions, keeping the larger ones"""
        if len(regions) <= 1:
            return regions

        # Sort by area (descending)
        regions = sorted(regions, key=lambda r: (r[1][2] - r[1][0]) * (r[1][3] - r[1][1]), reverse=True)

        filtered = []
        for region, bbox in regions:
            x1, y1, x2, y2 = bbox
            is_overlap = False

            for _, existing_bbox in filtered:
                ex1, ey1, ex2, ey2 = existing_bbox

                # Check if bboxes overlap significantly
                overlap_x = max(0, min(x2, ex2) - max(x1, ex1))
                overlap_y = max(0, min(y2, ey2) - max(y1, ey1))
                overlap_area = overlap_x * overlap_y

                current_area = (x2 - x1) * (y2 - y1)
                if current_area > 0 and overlap_area / current_area > 0.5:
                    is_overlap = True
                    break

            if not is_overlap:
                filtered.append((region, bbox))

        return filtered[:5]  # Return top 5 candidates


class PlateValidator:
    """Validates and formats extracted plate text"""

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove unwanted characters and normalize"""
        # Remove common noise characters
        text = text.upper().strip()
        text = re.sub(r'[^A-Z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def apply_corrections(text: str, format_type: PlateFormat = None) -> str:
        """Apply OCR correction mappings based on expected format"""
        # Remove all spaces first for analysis
        clean = text.replace(' ', '')

        if not clean.startswith('U'):
            # Try to fix if it starts with 0 (might be O misread as 0)
            if clean.startswith('0'):
                clean = 'U' + clean[1:]

        # Apply position-aware corrections
        result = []
        for i, char in enumerate(clean):
            if format_type == PlateFormat.GOVERNMENT:
                # UP 6633 format: first 2 are letters, rest are digits
                if i < 2:
                    result.append(UgandaPlatePatterns.LETTER_CORRECTIONS.get(char, char))
                else:
                    result.append(UgandaPlatePatterns.DIGIT_CORRECTIONS.get(char, char))
            elif format_type == PlateFormat.NEW_STANDARD:
                # UA 077AK: 2 letters, 3 digits, 2 letters
                if i < 2 or i >= 5:
                    result.append(UgandaPlatePatterns.LETTER_CORRECTIONS.get(char, char))
                else:
                    result.append(UgandaPlatePatterns.DIGIT_CORRECTIONS.get(char, char))
            elif format_type == PlateFormat.MOTORCYCLE:
                # UMA 055AF: 3 letters, 3 digits, 2 letters
                if i < 3 or i >= 6:
                    result.append(UgandaPlatePatterns.LETTER_CORRECTIONS.get(char, char))
                else:
                    result.append(UgandaPlatePatterns.DIGIT_CORRECTIONS.get(char, char))
            elif format_type == PlateFormat.LEGACY:
                # UAX 123Y: 3 letters, 3-4 digits, 1 letter
                if i < 3 or i == len(clean) - 1:
                    result.append(UgandaPlatePatterns.LETTER_CORRECTIONS.get(char, char))
                else:
                    result.append(UgandaPlatePatterns.DIGIT_CORRECTIONS.get(char, char))
            else:
                result.append(char)

        return ''.join(result)

    @staticmethod
    def detect_format(text: str) -> PlateFormat:
        """Detect the plate format from cleaned text"""
        clean = text.replace(' ', '').upper()

        for fmt, pattern in UgandaPlatePatterns.PATTERNS.items():
            if pattern.match(clean):
                return fmt

        return PlateFormat.UNKNOWN

    @staticmethod
    def format_plate(text: str, format_type: PlateFormat) -> str:
        """Format the plate text with proper spacing"""
        clean = text.replace(' ', '').upper()

        if format_type == PlateFormat.LEGACY:
            # UAX 123Y -> UAX 123Y (space after 3 letters)
            if len(clean) >= 4:
                return f"{clean[:3]} {clean[3:]}"

        elif format_type == PlateFormat.NEW_STANDARD:
            # UA077AK -> UA 077AK (space after 2 letters)
            if len(clean) >= 3:
                return f"{clean[:2]} {clean[2:]}"

        elif format_type == PlateFormat.MOTORCYCLE:
            # UMA055AF -> UMA 055AF (space after 3 letters)
            if len(clean) >= 4:
                return f"{clean[:3]} {clean[3:]}"

        elif format_type == PlateFormat.GOVERNMENT:
            # UP6633 -> UP 6633 (space after 2 letters)
            if len(clean) >= 3:
                return f"{clean[:2]} {clean[2:]}"

        return clean

    @staticmethod
    def validate_and_format(text: str) -> Tuple[str, PlateFormat, bool]:
        """
        Validate and format plate text.
        Returns (formatted_text, format_type, is_valid)
        """
        clean = PlateValidator.clean_text(text)

        # Try each format with corrections
        for fmt in PlateFormat:
            if fmt == PlateFormat.UNKNOWN:
                continue

            corrected = PlateValidator.apply_corrections(clean, fmt)
            detected_fmt = PlateValidator.detect_format(corrected)

            if detected_fmt != PlateFormat.UNKNOWN:
                formatted = PlateValidator.format_plate(corrected, detected_fmt)
                return formatted, detected_fmt, True

        # If no valid format found, return cleaned text
        return clean, PlateFormat.UNKNOWN, False


class OCREngine:
    """Main OCR engine with multiple backend support"""

    def __init__(self, use_easyocr: bool = True, use_tesseract: bool = True):
        self.use_easyocr = use_easyocr
        self.use_tesseract = use_tesseract
        self._easyocr_reader = None
        self._tesseract_available = None
        self.preprocessor = ImagePreprocessor()
        self.validator = PlateValidator()

    @property
    def easyocr_reader(self):
        """Lazy load EasyOCR reader"""
        if self._easyocr_reader is None and self.use_easyocr:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR initialized successfully")
            except ImportError:
                logger.warning("EasyOCR not available")
                self.use_easyocr = False
            except Exception as e:
                logger.error(f"Error initializing EasyOCR: {e}")
                self.use_easyocr = False
        return self._easyocr_reader

    @property
    def tesseract_available(self):
        """Check if Tesseract is available"""
        if self._tesseract_available is None:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
                logger.info("Tesseract available")
            except Exception:
                self._tesseract_available = False
                logger.warning("Tesseract not available")
        return self._tesseract_available

    def extract_plate(self, image: np.ndarray) -> PlateResult:
        """
        Extract number plate from image.
        Tries multiple methods and returns best result.
        """
        all_detections = []

        # Step 1: Detect plate regions
        regions = self.preprocessor.detect_plate_region(image)
        logger.info(f"Found {len(regions)} potential plate regions")

        for region_img, bbox in regions:
            # Step 2: Preprocess each region
            preprocessed = self.preprocessor.preprocess_for_ocr(region_img)

            for processed_img in preprocessed:
                # Step 3: Run OCR with available engines

                # Try EasyOCR
                if self.use_easyocr and self.easyocr_reader:
                    try:
                        results = self.easyocr_reader.readtext(processed_img)
                        for detection in results:
                            text = detection[1]
                            confidence = detection[2]
                            all_detections.append((text, confidence, bbox, 'easyocr'))
                    except Exception as e:
                        logger.error(f"EasyOCR error: {e}")

                # Try Tesseract
                if self.use_tesseract and self.tesseract_available:
                    try:
                        import pytesseract
                        # Use specific config for license plates
                        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                        text = pytesseract.image_to_string(processed_img, config=custom_config)
                        text = text.strip()
                        if text:
                            # Tesseract doesn't provide confidence for simple mode
                            all_detections.append((text, 0.7, bbox, 'tesseract'))
                    except Exception as e:
                        logger.error(f"Tesseract error: {e}")

        # Step 4: Find best valid plate from all detections
        best_result = self._find_best_plate(all_detections)

        if best_result:
            return best_result

        # No valid plate found
        return PlateResult(
            plate_text="",
            formatted_plate="",
            confidence=0.0,
            plate_format=PlateFormat.UNKNOWN,
            raw_detections=[d[0] for d in all_detections],
            error="No valid Uganda plate detected"
        )

    def _find_best_plate(self, detections: List[Tuple[str, float, Tuple, str]]) -> Optional[PlateResult]:
        """Find the best valid plate from detections"""
        candidates = []

        for text, confidence, bbox, engine in detections:
            formatted, fmt, is_valid = self.validator.validate_and_format(text)

            if is_valid:
                # Boost confidence for EasyOCR results
                if engine == 'easyocr':
                    confidence *= 1.1

                candidates.append(PlateResult(
                    plate_text=text,
                    formatted_plate=formatted,
                    confidence=min(confidence, 1.0),
                    plate_format=fmt,
                    bounding_box=bbox,
                    raw_detections=[text]
                ))

        if not candidates:
            return None

        # Sort by confidence and return best
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        return candidates[0]

    def extract_from_file(self, file_path: str) -> PlateResult:
        """Extract plate from image file"""
        try:
            image = cv2.imread(file_path)
            if image is None:
                return PlateResult(
                    plate_text="",
                    formatted_plate="",
                    confidence=0.0,
                    plate_format=PlateFormat.UNKNOWN,
                    error="Could not read image file"
                )
            return self.extract_plate(image)
        except Exception as e:
            return PlateResult(
                plate_text="",
                formatted_plate="",
                confidence=0.0,
                plate_format=PlateFormat.UNKNOWN,
                error=str(e)
            )

    def extract_from_bytes(self, image_bytes: bytes) -> PlateResult:
        """Extract plate from image bytes"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                return PlateResult(
                    plate_text="",
                    formatted_plate="",
                    confidence=0.0,
                    plate_format=PlateFormat.UNKNOWN,
                    error="Could not decode image"
                )
            return self.extract_plate(image)
        except Exception as e:
            return PlateResult(
                plate_text="",
                formatted_plate="",
                confidence=0.0,
                plate_format=PlateFormat.UNKNOWN,
                error=str(e)
            )


# Singleton instance for reuse
_engine_instance = None


def get_ocr_engine() -> OCREngine:
    """Get or create OCR engine singleton"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = OCREngine()
    return _engine_instance