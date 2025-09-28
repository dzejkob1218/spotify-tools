from typing import List
import spotifytools.spotify as spotify

# TODO: Add recommendation methods.
class Track(spotify.Resource):

    # TODO: Bring back language estimation since not all tracks have genius pages

    available_markets: List[str]  # A list of market tags where the content is available.
    disc_number: int  # The disk of the album on which the track was released (starting with 1).
    duration_ms: int  # Duration of track in milliseconds.
    explicit: bool  # True if the track contains explicit lyrics.
    popularity: int  # Relative recent popularity (0 - 100).
    preview_url: str  # Url at which a free 30 second mp3 clip of the track is available.
    track_number: int  # Number of the track on the album (starting with 1).

    def __init__(self, sp, raw_data, artists, album):
        self.artists: List[spotify.Artist] = artists  # Artists who released and featured on the track.
        self.album: spotify.Album = album  # Album on which the track was released.
        super().__init__(sp, raw_data)
        self.sp = sp
        self.audio_features: spotify.audio_features = None  # False means features unavailable
        self.genius_features: spotify.genius_features = None

    def load(self, recursive=False):
        """Downloads all available data about the track."""
        # TODO: Should this also include details?
        if not recursive:
            self.get_features()
        self.get_confidence_scores()
        self.get_lyrics()
        # self.get_language()

    # TODO: Add method for completing own details

    def get_features(self):
        """Add audio features to track attributes."""
        if not self.audio_features:
            self.sp.load_features(self)
        return self.audio_features

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
        self.audio_features = bool(features)
        if features:
            self.details.update(features)
            self.__dict__.update(features)
