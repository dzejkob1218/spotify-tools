from typing import List

import spotifytools.spotify as spotify
from spotifytools.spotify.playlist import Playlist


class User(spotify.Resource, spotify.Collection):
    child_type = Playlist

    images: List[spotify.Image]  # List of images associated with the user.
    followers: int  # Number of followers of the user.     # TODO: extract the count same as in Artist (['followers']['total'])
    display_name: str  # Name used for display in the app (can be different from 'name' property).

    def __init__(self, sp, raw_data, children=None):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, name=None, children=children)

    # TODO: Method to get top items

    # TODO: Method to get playlists