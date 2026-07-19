import random


class PhraseManager:
    def __init__(self):
        self._phrases = [
            "Zeus, I need you to learn my voice now.",
            "This is how I sound when I speak clearly.",
            "My voice is my password and my identity.",
            "Authentication requires a consistent vocal tone.",
            "Please record this phrase for my speaker profile.",
            "The quick brown fox jumps over the lazy dog.",
            "I authorize this system to recognize me.",
            "Artificial intelligence simplifies complex tasks.",
            "Initialize the core protocols immediately.",
            "This sample helps build a secure embedding.",
            "I am speaking at a normal conversational volume.",
            "Security systems require continuous validation.",
            "Voice biometrics provide seamless authentication.",
            "Verify my identity using this audio sample.",
            "A clear microphone signal ensures high quality.",
            "I expect the system to respond only to me.",
            "Background noise can interfere with recognition.",
            "My vocal tract produces a unique signature.",
            "Every person has a distinct audio footprint.",
            "Let's calibrate the microphone sensitivity.",
            "Ensure the environment remains relatively quiet.",
            "This phrase is long enough to extract features.",
            "Deep neural networks process the audio stream.",
            "Speaker verification adds an extra security layer.",
            "I am ready to complete the enrollment process.",
            "The system is listening for the wake word.",
            "Analyze this recording for spectral characteristics.",
            "Protecting data is of utmost importance.",
            "Seamless interaction is the goal of this software.",
            "Thank you for setting up my voice profile.",
        ]
        self._available_phrases = self._phrases.copy()

    def get_next_phrase(self) -> str:
        if not self._available_phrases:
            self._available_phrases = self._phrases.copy()

        phrase = random.choice(self._available_phrases)
        self._available_phrases.remove(phrase)
        return phrase
