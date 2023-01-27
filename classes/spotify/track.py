import classes.spotify as spotify
import helper
from helpers.parser import parse_artists, sort_image_urls


class Track(spotify.Resource):
    """
    Additional methods:
    - Recommended (track)
    """

    def __init__(self, sp, raw_data, audio_features=None):
        super().__init__(sp, raw_data)
        self.lyrics = None
        self.features_loaded = False
        self.confidence_scores = None

        self.sp = sp

    def load_details(self, raw_data):
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

    def get_lyrics(self, genius_session):
        if not self.lyrics:
            self.lyrics = genius_session.get_lyrics(self)
        return self.lyrics

    def load_features(self):
        """Add audio features to track attributes."""
        if self.features_loaded:
            return
        audio_features = self.sp.fetch_track_features([self.uri])[0]
        self.features_loaded = True
        self.attributes.update({
            'valence': audio_features['valence'] * 100,
            'energy': audio_features['energy'] * 100,
            'dance': audio_features['danceability'] * 100,
            'speech': audio_features['speechiness'] * 100,
            'acoustic': audio_features['acousticness'] * 100,
            'instrumental': audio_features['instrumentalness'] * 100,
            'live': audio_features['liveness'] * 100,
            'tempo': audio_features['tempo'],
            'key': audio_features['key'],  # this is the root note of the song's key (used for filtering)
            'mode': audio_features['mode'],
            # this is the mode itself for sorting songs into major and minor keys (used for filtering)
            # TODO: key_name probably doesn't need to be here
            # 'key_name': track_key(self.audio_features['key'], self.audio_features['mode']),
            # this is a string representation of the song's key including it's mode (used for display)
            'signature': audio_features['time_signature'],
        })

    def load_analysis(self):
        """
        Add confidence ratings from audio analysis to track attributes.

        Spotify isn't perfect at guessing some features of a song and only commonly used keys and time signatures are recognized, so some attributes comes with a confidence rating.
        The analysis endpoint is slow and returns a single song at at time.
        """
        if self.confidence_scores:
            return
        audio_analysis = self.sp.connection.audio_analysis(self.uri)['track']
        self.confidence_scores = {
            'tempo': audio_analysis['tempo_confidence'],
            'key': audio_analysis['key_confidence'],
            'mode': audio_analysis['mode_confidence'],
            'signature': audio_analysis['time_signature_confidence'],
        }
