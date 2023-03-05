import spotifytools.spotify as spotify
from spotifytools.spotify.playlist import Playlist


class User(spotify.Resource, spotify.Collection):
    child_type = Playlist

    def __init__(self, sp, raw_data, children=None):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, name=None, children=children)
