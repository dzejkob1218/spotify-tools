import spotifytools.spotify as spotify
from spotifytools.spotify.playlist import Playlist


class User(spotify.Resource, spotify.Collection):
    child_type = Playlist
    # TODO: Urls? Images?
    detail_names = ['uri', 'id', 'followers', 'name']
    detail_procedures = {
        'followers': ("followers", lambda data: data["total"]),
        'name': ("display_name", None),
    }

    def __init__(self, sp, raw_data, children=None):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, name=None, children=children)
