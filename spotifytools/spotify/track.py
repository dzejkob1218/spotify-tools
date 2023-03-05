import spotifytools.spotify as spotify

from spotifytools.helpers import detect_language, features_adapter
from spotifytools.genius_session import GeniusSession


# TODO: Add recommendation methods.
class Track(spotify.Resource):
    def __init__(self, sp, raw_data, artists, album):
        self.artists = artists
        self.album = album
        super().__init__(sp, raw_data)
        self.lyrics = None
        # self.language = helpers.quick_language(self) # Takes approx. half a second
        self.confidence_scores = None
        self.sp = sp
        self.features = None  # False denotes features not available

    def load(self, recursive=False):
        """Downloads all available data about the track."""
        if not recursive:
            self.get_features()
        self.get_confidence_scores()
        self.get_lyrics()
        self.get_language()

    # TODO: Add method for completing own details

    def get_features(self):
        """Add audio features to track attributes."""
        if not self.features:
            self.sp.load_features(self)
        return self.features

    def get_lyrics(self):
        if not self.lyrics:
            self.lyrics = GeniusSession().get_lyrics(self)
        return self.lyrics

    def get_language(self):
        self.get_lyrics()
        if self.lyrics == GeniusSession.NO_LYRICS_PLACEHOLDER:
            return None
        if not self.language:
            self.language = detect_language(self.lyrics)
        return self.language

    def get_confidence_scores(self):
        """
        Add confidence ratings from audio analysis to track attributes.

        Spotify isn't perfect at guessing some features of a song and only commonly used keys and time signatures are recognized, so some attributes comes with a confidence rating.
        The analysis endpoint is slow and accepts only one track per request.
        """
        # TODO: This should be in SpotifySession
        if not self.confidence_scores:
            raw_data = self.sp.connection.audio_analysis(self.uri)['track']
            self.confidence_scores = {
                'tempo': raw_data['tempo_confidence'],
                'key': raw_data['key_confidence'],
                'mode': raw_data['mode_confidence'],
                'signature': raw_data['time_signature_confidence'],
            }
        return self.confidence_scores

    def parse_features(self, features):
        """
        Updates features from a Spotify API response.

        Spotify doesn't have features on very short and unusual tracks, in that case the features are set to False.
        It is assumed the rest of the features responses are always complete.
        Some default Spotify names for the features are aliased to be shorter.
        """
        # TODO: Look into loading features through Resource parse_details route
        self.features = bool(features)
        if features:
            self.details.update(features)
            self.__dict__.update(features)
