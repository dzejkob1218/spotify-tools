from typing import List

import spotifytools.spotify as spotify
from spotifytools.spotify.track import Track

from spotifytools.helpers import sort_image_urls


# TODO: Data about when a track was added to a playlist is being lost right now
class Playlist(spotify.Resource, spotify.Collection):

    child_type = Track

    collaborative: bool  # True if the playlist is collaborative (i.e., created by multiple users).
    description: str  # Description of the playlist.
    followers: int  # Number of followers of the playlist.     # TODO: extract the count same as in Artist (['followers']['total'])
    images: List[spotify.Image]  # List of images associated with the playlist.
    primary_color: str  # Primary color of the playlist.
    public: bool  # True if the playlist is public.
    snapshot_id: str  # Snapshot ID of the playlist.

    def __init__(self, sp, raw_data, owner, children=None, children_loaded=False):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children, children_loaded)
        # TODO: What about collab playlists?
        self.owner = owner
        #self.user_is_owner = self.owner == sp.fetch_user().uri
