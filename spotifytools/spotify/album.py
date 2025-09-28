from typing import List, Dict, Union

import spotifytools.spotify as spotify
from spotifytools.spotify.track import Track


class Album(spotify.Resource, spotify.Collection):
    child_type = Track

    album_type: str  # The type of the album (e.g., "album", "single", "compilation").
    available_markets: List[str]  # A list of market tags where the album is available.
    copyrights: List[Dict[str, str]]  # A list of copyright information for the album.
    genres: List[str]  # A list of genres associated with the album.
    images: List[spotify.Image]  # A list of images for the album.
    label: str  # The label that released the album.
    popularity: int  # The popularity of the album.
    release_date: str  # The release date of the album.
    release_date_precision: str  # The precision of the release date (e.g., "day", "year").
    total_tracks: int  # The total number of tracks on the album.

    def __init__(self, sp, raw_data, artists, children=None, children_loaded=False):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children, children_loaded)
        self.artists = artists
