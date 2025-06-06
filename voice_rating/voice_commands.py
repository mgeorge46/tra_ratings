import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from rating.models import MotorCar, Rating, MotorCarConflict, MOTOR_TYPES
from rating.utils import validate_ug_plate_format
from .models import VoiceCommand
import logging

logger = logging.getLogger('voice_rating')


class VoiceCommandProcessor:
    """Process voice commands for rating flow"""

    def __init__(self, voice_engine, session_manager):
        self.voice_engine = voice_engine
        self.session_manager = session_manager
        self.motor_types_voice_map = {
            'boda': 'motorcycle',
            'boda boda': 'motorcycle',
            'motorcycle': 'motorcycle',
            'bike': 'motorcycle',
            'car': 'car',
            'vehicle': 'car',
            'bus': 'bus',
            'truck': 'truck',
            'lorry': 'truck',
            'taxi': 'taxi',
            'tuku': 'tuku',
            'tuku tuku': 'tuku',
            'coaster': 'coaster'
        }

    def start_rating_flow(self, session_id):
        """Start the voice rating flow"""
        self.voice_engine.speak("Welcome to the voice rating system. Let's rate a motor vehicle.")
        return self.get_motor_type(session_id)

    def get_motor_type(self, session_id):
        """Get motor type via voice"""
        motor_types_text = ", ".join([name for _, name in MOTOR_TYPES])
        prompt = f"Please say the type of motor vehicle you want to rate. Options are: {motor_types_text}"

        max_attempts = settings.VOICE_RATING.get('MAX_ATTEMPTS', 3)

        for attempt in range(max_attempts):
            response = self.voice_engine.listen_for_command(prompt=prompt)

            if response:
                # Log the command
                session_data = self.session_manager.get_session(session_id)
                VoiceCommand.objects.create(
                    session=session_data['session'],
                    command_text=response,
                    command_type='motor_type'
                )

                # Process the response
                motor_type = self._extract_motor_type(response)

                if motor_type:
                    self.session_manager.update_session(
                        session_id,
                        data={'motor_type': motor_type},
                        step='plate_number'
                    )

                    motor_name = dict(MOTOR_TYPES).get(motor_type, motor_type)
                    self.voice_engine.speak(f"You selected {motor_name}. Now let's get the plate number.")
                    return self.get_plate_number(session_id)
                else:
                    if attempt < max_attempts - 1:
                        self.voice_engine.speak("I didn't recognize that motor type. Please try again.")
                    else:
                        self.voice_engine.speak("Sorry, I couldn't understand the motor type. Please try using the text interface.")
                        return False

        return False

    def _extract_motor_type(self, text):
        """Extract motor type from voice input"""
        text_lower = text.lower()

        for voice_term, motor_type in self.motor_types_voice_map.items():
            if voice_term in text_lower:
                return motor_type

        return None

    def get_plate_number(self, session_id):
        """Get plate number via voice"""
        prompt = "Please say the vehicle plate number. For example: U A R one two three four L"

        max_attempts = settings.VOICE_RATING.get('MAX_ATTEMPTS', 3)

        for attempt in range(max_attempts):
            response = self.voice_engine.listen_for_command(prompt=prompt)

            if response:
                # Log the command
                session_data = self.session_manager.get_session(session_id)
                VoiceCommand.objects.create(
                    session=session_data['session'],
                    command_text=response,
                    command_type='plate_number'
                )

                # Process plate number
                plate_number = self._process_plate_number(response)

                if plate_number:
                    try:
                        # Validate using existing utils
                        formatted_plate = validate_ug_plate_format(plate_number)

                        # Confirm with user
                        spelled_plate = ' '.join(formatted_plate.replace(' ', ''))
                        self.voice_engine.speak(f"I heard {spelled_plate}. Is this correct? Say yes or no.")

                        confirm = self.voice_engine.listen_for_command()

                        if confirm and 'yes' in confirm.lower():
                            self.session_manager.update_session(
                                session_id,
                                data={'plate_number': formatted_plate},
                                step='rating'
                            )

                            self.voice_engine.speak("Great! Now let's rate the vehicle.")
                            return self.get_rating(session_id)
                        else:
                            if attempt < max_attempts - 1:
                                self.voice_engine.speak("Let's try again.")

                    except ValidationError as e:
                        if attempt < max_attempts - 1:
                            self.voice_engine.speak("That doesn't seem to be a valid plate number. Please try again.")
                else:
                    if attempt < max_attempts - 1:
                        self.voice_engine.speak("I couldn't understand the plate number. Please speak clearly.")

        self.voice_engine.speak("Sorry, I couldn't get the plate number. Please use the text interface.")
        return False

    def _process_plate_number(self, text):
        """Convert voice input to plate number format"""
        # Replace spoken numbers with digits
        number_words = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
        }

        text_processed = text.upper()
        for word, digit in number_words.items():
            text_processed = text_processed.replace(word.upper(), digit)

        # Remove common filler words
        text_processed = re.sub(r'\b(THE|AND|SPACE|DASH)\b', ' ', text_processed)

        # Clean up spaces and special characters
        text_processed = re.sub(r'[^A-Z0-9]', '', text_processed)

        return text_processed

    def get_rating(self, session_id):
        """Get rating score via voice"""
        prompt = "Please rate the vehicle from 1 to 5. You can use half points like 2.5 or 3.5"

        max_attempts = settings.VOICE_RATING.get('MAX_ATTEMPTS', 3)

        for attempt in range(max_attempts):
            response = self.voice_engine.listen_for_command(prompt=prompt)

            if response:
                # Log the command
                session_data = self.session_manager.get_session(session_id)
                VoiceCommand.objects.create(
                    session=session_data['session'],
                    command_text=response,
                    command_type='rating'
                )

                # Extract rating
                rating = self._extract_rating(response)

                if rating:
                    self.session_manager.update_session(
                        session_id,
                        data={'rating': rating},
                        step='comments'
                    )

                    self.voice_engine.speak(f"You gave a rating of {rating}. Now let's add comments.")
                    return self.get_comments(session_id, rating)
                else:
                    if attempt < max_attempts - 1:
                        self.voice_engine.speak("Please provide a rating between 1 and 5.")

        return False

    def _extract_rating(self, text):
        """Extract rating from voice input"""
        # Look for numbers in the text
        text_lower = text.lower()

        # Replace word numbers
        number_map = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'half': '.5', 'point five': '.5', 'and a half': '.5'
        }

        for word, num in number_map.items():
            text_lower = text_lower.replace(word, num)

        # Extract decimal number
        import re
        match = re.search(r'(\d+\.?\d*)', text_lower)

        if match:
            rating = float(match.group(1))

            # Validate rating
            if 1 <= rating <= 5:
                # Round to nearest 0.5
                rating = round(rating * 2) / 2
                return rating

        return None

    def get_comments(self, session_id, rating):
        """Get comments based on rating"""
        # Generate appropriate comments based on rating
        if rating <= 2.5:
            comments = [
                "Drove too fast or recklessly",
                "Ignored traffic rules",
                "Sudden braking or jerky driving",
                "Car was unclean or uncomfortable",
                "Driver was late or caused delays",
                "Distracted while driving"
            ]
        elif rating <= 4:
            comments = [
                "Decent driving but could improve",
                "Followed most traffic rules",
                "Car cleanliness could be better",
                "Minor delays during the trip",
                "Driving was okay but not outstanding"
            ]
        else:
            comments = [
                "Polite and professional driver",
                "Smooth and safe driving",
                "Followed traffic rules",
                "Clean and comfortable car",
                "Punctual and timely",
                "Attentive to road conditions"
            ]

        # Read comments to user
        comments_text = ". ".join([f"{i + 1}. {comment}" for i, comment in enumerate(comments)])
        prompt = f"Based on your rating, here are some comment options: {comments_text}. Say the numbers of the comments you want to select, or say 'other' to add your own comment."

        response = self.voice_engine.listen_for_command(prompt=prompt, timeout=15)

        if response:
            # Log the command
            session_data = self.session_manager.get_session(session_id)
            VoiceCommand.objects.create(
                session=session_data['session'],
                command_text=response,
                command_type='comments'
            )

            selected_comments = []
            other_comment = None

            # Check for "other"
            if 'other' in response.lower():
                self.voice_engine.speak("Please say your custom comment.")
                other_response = self.voice_engine.listen_for_command(timeout=20)
                if other_response:
                    other_comment = other_response
                    VoiceCommand.objects.create(
                        session=session_data['session'],
                        command_text=other_response,
                        command_type='other_comment'
                    )

            # Extract selected comment numbers
            import re
            numbers = re.findall(r'\d+', response)
            for num in numbers:
                idx = int(num) - 1
                if 0 <= idx < len(comments):
                    selected_comments.append(comments[idx])

            if selected_comments or other_comment:
                self.session_manager.update_session(
                    session_id,
                    data={
                        'system_comments': ', '.join(selected_comments) if selected_comments else '',
                        'comment': other_comment or ''
                    },
                    step='confirm'
                )

                return self.confirm_rating(session_id)
            else:
                self.voice_engine.speak("I didn't catch any comments. Let's skip to confirmation.")
                return self.confirm_rating(session_id)

        return self.confirm_rating(session_id)

    def confirm_rating(self, session_id):
        """Confirm and save rating"""
        session_data = self.session_manager.get_session(session_id)
        data = session_data['data']

        # Read back the rating details
        motor_type_name = dict(MOTOR_TYPES).get(data.get('motor_type'), 'vehicle')
        confirmation = f"Here's your rating: {motor_type_name} with plate number {data.get('plate_number')}, "
        confirmation += f"rated {data.get('rating')} stars. "

        if data.get('system_comments'):
            confirmation += f"Comments: {data.get('system_comments')}. "
        if data.get('comment'):
            confirmation += f"Additional comment: {data.get('comment')}. "

        confirmation += "Say 'confirm' to submit or 'cancel' to discard."

        self.voice_engine.speak(confirmation)
        response = self.voice_engine.listen_for_command()

        if response and 'confirm' in response.lower():
            # Save the rating
            success = self.save_rating(session_id)
            if success:
                self.voice_engine.speak("Thank you! Your rating has been saved successfully.")
                self.session_manager.close_session(session_id)
                return True
            else:
                self.voice_engine.speak("Sorry, there was an error saving your rating.")
                return False
        else:
            self.voice_engine.speak("Rating cancelled.")
            self.session_manager.close_session(session_id)
            return False

    def save_rating(self, session_id):
        """Save the rating to database"""
        try:
            session_data = self.session_manager.get_session(session_id)
            data = session_data['data']
            session = session_data['session']

            # Get or create motor car
            motor_car, created = MotorCar.objects.get_or_create(
                motor_car_number=data['plate_number'],
                defaults={
                    'motor_type': data['motor_type'],
                    'user': session.user
                }
            )

            # Check for conflicts
            if not created and motor_car.motor_type != data['motor_type']:
                motor_car.is_conflicted = True
                motor_car.save()

                MotorCarConflict.objects.create(
                    motor_car=motor_car,
                    reported_type=data['motor_type'],
                    user=session.user
                )

            # Create rating
            rating = Rating.objects.create(
                motor_car=motor_car,
                user=session.user,
                score=Decimal(str(data['rating'])),
                motor_type=data['motor_type'],
                system_comments=data.get('system_comments', ''),
                comment=data.get('comment', ''),
                location='0,0',  # Default location for voice ratings
                rate_method='Voice',  # Mark as voice rating
                is_anonymous=not session.user
            )

            logger.info(f"Rating saved via voice: {rating}")
            return True

        except Exception as e:
            logger.error(f"Error saving voice rating: {e}")
            return False