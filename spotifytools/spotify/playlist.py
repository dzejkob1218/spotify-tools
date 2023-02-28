import spotifytools.spotify as spotify
from spotifytools.spotify.track import Track
from spotifytools.helpers import sort_image_urls


# TODO: Data about when a track was added to a playlist is being lost right now
class Playlist(spotify.Resource, spotify.Collection):
    child_type = Track
    detail_names = ['uri', 'name', 'public', 'description', 'followers', 'total_tracks', 'images']
    detail_procedures = {
        'followers': ("followers", lambda data: data["total"]),
        'total_tracks': ("tracks", lambda data: data["total"]),
        'images': ('images', lambda data: sort_image_urls(data)),
    }

    def __init__(self, sp, raw_data, owner, children=None, children_loaded=False):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children, children_loaded)
        self.owner = owner
        #self.user_is_owner = self.owner == sp.fetch_user().uri
