import classes.spotify as spotify
import helper
from helpers.parser import parse_artists, sort_image_urls
from classes.genius_session import GeniusSession

class Track(spotify.Resource):
    """
    Additional methods:
    - Recommended (track)
    """

    def __init__(self, sp, raw_data, audio_features=None):
        super().__init__(sp, raw_data)
        self.lyrics = None
        self.language = None
        self.confidence_scores = None

        self.sp = sp

    def load(self, recursive=False):
        """
        Downloads all available data about the track.

        """
        if not recursive:
            self.get_features()
        self.get_confidence_scores()
        self.get_lyrics()
        self.get_language()

    def get_features(self):
        """Add audio features to track attributes."""
        if not self.features:
            print(f"TRACK {self.name} LOADING FEATURES")
            self.parse_features(self.sp.fetch_track_features([self.uri])[0])
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
            self.language = helper.detect_language(self.lyrics)
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

    def parse_details(self, raw_data):
        # Load attributes from Spotify.track
        # TODO: Are the images ever missing?
        # TODO: Wouldn't it be better to just create the parent object?
        image_urls = (
            sort_image_urls(raw_data["album"]["images"])
            if "images" in raw_data["album"]
            else None
        )

        self.attributes = {
            "uri": raw_data["uri"],
            "name": raw_data["name"],
            "miniature": image_urls[0] if image_urls else None,
            "image": image_urls[-1] if image_urls else None,
            "artists_number": len(raw_data["artists"]),
            # TODO: perhaps parse artists can be elsewhere?
            "artists": parse_artists(raw_data["artists"]),
            "popularity": raw_data["popularity"],
            "explicit": raw_data["explicit"],
            "duration": raw_data["duration_ms"],
            "number": raw_data["track_number"],
            "release": raw_data["album"]["release_date"],
            "release_precision": raw_data["album"]["release_date_precision"],
            "release_year": int(raw_data["album"]["release_date"][:4]),
        }

    def parse_features(self, raw_data):
        self.features = {
            'valence': raw_data['valence'],
            'energy': raw_data['energy'],
            'dance': raw_data['danceability'],
            'speech': raw_data['speechiness'],
            'acoustic': raw_data['acousticness'],
            'instrumental': raw_data['instrumentalness'],
            'live': raw_data['liveness'],
            'tempo': raw_data['tempo'],
            'key': raw_data['key'],  # this is the root note of the song's key (used for filtering)
            'mode': raw_data['mode'],
            # this is the mode itself for sorting songs into major and minor keys (used for filtering)
            # TODO: key_name probably doesn't need to be here
            # 'key_name': track_key(self.raw_data['key'], self.raw_data['mode']),
            # this is a string representation of the song's key including it's mode (used for display)
            'signature': raw_data['time_signature'],
        }

