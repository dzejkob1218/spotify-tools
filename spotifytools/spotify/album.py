import spotifytools.spotify as spotify
from spotifytools.spotify.track import Track


class Album(spotify.Resource, spotify.Collection):
    child_type = Track

    def __init__(self, sp, raw_data, artists, children=None, children_loaded=False):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children, children_loaded)
        self.artists = artists
