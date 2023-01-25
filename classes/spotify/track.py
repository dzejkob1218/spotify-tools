import classes.spotify as spotify
from helpers.parser import parse_artists, sort_image_urls


class Track(spotify.Resource):
    """
    Additional methods:
    - Recommended (track)
    """

    def __init__(self, sp, raw_data, audio_features=None):
        super().__init__(sp, raw_data)
        self.lyrics = None

    def load_details(self, raw_data):
        # Load attributes from Spotify.track
        # TODO: Are the images ever missing?
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

    """
    Legacy code:
        # Load parent attributes from Spotify.track
        # In this case the parent is the album
        self.parent = {
            'uri': self.spotify_object['album']['uri'],
            'name': self.spotify_object['album']['name'],
            'miniature': self.attributes['miniature'],
            'artists': self.attributes['artists'],
        }

        # Load attributes from track features
        if not self.audio_features:
            self.audio_features = self.sp.fetch_track_features([self.uri])[0]

        if self.audio_features:
            self.attributes.update({
                'valence': self.audio_features['valence'] * 100,
                'energy': self.audio_features['energy'] * 100,
                'dance': self.audio_features['danceability'] * 100,
                'speech': self.audio_features['speechiness'] * 100,
                'acoustic': self.audio_features['acousticness'] * 100,
                'instrumental': self.audio_features['instrumentalness'] * 100,
                'live': self.audio_features['liveness'] * 100,
                'tempo': self.audio_features['tempo'],
                'key': self.audio_features['key'],  # this is the root note of the song's key (used for filtering)
                'mode': self.audio_features['mode'],
                # this is the mode itself for sorting songs into major and minor keys (used for filtering)
                # TODO: key_name probably doesn't need to be here
                'key_name': track_key(self.audio_features['key'], self.audio_features['mode']),
                # this is a string representation of the song's key including it's mode (used for display)
                'signature': self.audio_features['time_signature'],
            })


    def get_lyrics(self):
        # Load confidence ratings from audio analysis 
        # Spotify isn't perfect at guessing some features of a song and only commonly used keys and time signatures are recognized, so some attributes comes with a confidence rating
        # Making a request for each song takes too much time and there is no endpoint in spotify API for getting multiple songs analysed
        # Later make this data load only when the song's attributes show up
        audio_analysis = self.sp.connection.audio_analysis(self.uri)['track']
        self.attributes.update({
            'tempo_confidence': audio_analysis['tempo_confidence'],
            'key_confidence': audio_analysis['key_confidence'],
            'mode_confidence': audio_analysis['mode_confidence'],
            'signature_confidence': audio_analysis['time_signature_confidence'],
        })
    """
