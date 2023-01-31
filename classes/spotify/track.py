import classes.spotify as spotify
import helpers
from helpers import parse_artists, sort_image_urls
from classes.genius_session import GeniusSession


class Track(spotify.Resource):
    """
    Additional methods:
    - Recommended (track)
    """
    # Parent features that should be considered when averaging lists:
    # Album - album, album_type, release_date, release_date_precision, genres (?), copyrights
    # Artist - artist, genres,

    # TODO: This could later be merged into details
    feature_names = ['valence', 'energy', 'dance', 'speech', 'acoustic', 'instrumental', 'live', 'tempo', 'key', 'mode',
                     'signature']
    feature_aliases = {
            'dance': 'danceability',
            'speech': 'speechiness',
            'acoustic': 'acousticness',
            'instrumental': 'instrumentalness',
            'live': 'liveness',
            'signature': 'time_signature',
        }
    detail_names = ['uri', 'url', 'name', 'popularity', 'explicit', 'duration', 'track_number']
    detail_procedures = {
        'url': ('external_urls', lambda data: data['spotify']),
        'duration': ('duration_ms', None),
    }

    def __init__(self, sp, raw_data, artists, album):

        self.artists = artists
        self.album = album

        super().__init__(sp, raw_data)
        self.lyrics = None
        self.language = None
        self.confidence_scores = None
        self.sp = sp
        self.features = None

    def load(self, recursive=False):
        """
        Downloads all available data about the track.

        """
        if not recursive:
            self.get_features()
        self.get_confidence_scores()
        self.get_lyrics()
        self.get_language()

    # TODO: Add method for completing own details

    def get_features(self):
        # TODO: Measure performance cost of loading features with track by default
        """Add audio features to track attributes."""
        if not self.features:
            self.sp.fetch_track_features([self])
        return self.features

    def get_lyrics(self):
        if not self.lyrics:
            self.lyrics = GeniusSession().get_lyrics(self)
        return self.lyrics

    def get_language(self):
        # TODO: export no lyrics text to a single variable
        self.get_lyrics()
        if self.lyrics == 'No lyrics available.':
            return None
        if not self.language:
            self.language = helpers.detect_language(self.lyrics)
        return self.language

    def get_confidence_scores(self):
        """
        Add confidence ratings from audio analysis to track attributes.

        Spotify isn't perfect at guessing some features of a song and only commonly used keys and time signatures are recognized, so some attributes comes with a confidence rating.
        The analysis endpoint is slow and accepts only one track per request.
        """
        if not self.confidence_scores:
            raw_data = self.sp.connection.audio_analysis(self.uri)['track']
            self.confidence_scores = {
                'tempo': raw_data['tempo_confidence'],
                'key': raw_data['key_confidence'],
                'mode': raw_data['mode_confidence'],
                'signature': raw_data['time_signature_confidence'],
            }
        return self.confidence_scores

    def parse_features(self, raw_data):
        """
        Updates features from a Spotify API response.

        Spotify doesn't have features on very short and unusual tracks, in that case the features remain an empty dict.
        It is assumed the rest of the features responses are always complete.
        The default Spotify names for the features are unnecessarily long, so this function aliases them before copying.
        """


        self.features = {}

        if raw_data:
            for feature in self.feature_names:
                key = self.feature_aliases[feature] if feature in self.feature_aliases else feature
                self.features[feature] = raw_data[key]

