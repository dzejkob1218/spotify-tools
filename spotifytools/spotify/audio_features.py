# TODO: This class should be equally valid for storing features of a single class and averages of a collection
# TODO: Consider making a parent class for all 'feature' classes

class AudioFeatures:
    """
    Features resulting from Spotify's analysis of a track's audio.

    Some names are changed from the original API keys by removing endings like '-ness' and '-ability' for clarity.
    """
    dance: float  # A measure of how suitable a track is for dancing (0.0 - 1.0).
    energy: float  # Represents a perceptual measure of intensity and activity (0.0 - 1.0).
    key: int  # The estimated overall key of the track (0 - 11, where 0 is C). # TODO: Check which note is 0
    loudness: float  # The overall loudness of a track in decibels (dB).
    mode: int  # Represents the modality of a track (0 = minor, 1 = major).
    speech: float  # Detects the presence of spoken words in a track (0.0 - 1.0).
    acoustic: float  # Represents the acoustic quality of a track (0.0 - 1.0).
    instrumental: float  # Predicts whether a track contains no vocals (0.0 - 1.0).
    live: float  # Detects the presence of an audience in the recording (0.0 - 1.0).
    valence: float  # A measure of musical positiveness conveyed by a track (0.0 - 1.0).
    tempo: float  # The overall estimated tempo of a track in beats per minute (BPM).
    duration: int  # The duration of the track in milliseconds.
    signature: int  # An estimated overall time signature of a track (number of beats per measure).

    def __init__(self, data: dict):
        self.__dict__.update(data)
