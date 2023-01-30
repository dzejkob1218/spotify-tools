"""
Additional methods:
- Recommended (artist)
- Recommended (genre)
- Related

"""
import classes.spotify as spotify
from classes.spotify.album import Album
from helpers import sort_image_urls


class Artist(spotify.Resource, spotify.Collection):
    child_type = Album
    detail_names = ['uri', 'url', 'name', 'popularity', 'genres', 'followers', 'images']
    detail_procedures = {
        'url': ('external_urls', lambda data: data['spotify']),
        'images': ('images', lambda data: sort_image_urls(data)),
        'followers': ("followers", lambda data: data["total"]),
    }

    # Viable children types: Track
    def __init__(self, sp, raw_data, children=None):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children)

    def gather_tracks(self, keep_duplicates=False):
        """
        Extends Collection's function to exclude songs by other artists.

        Not all tracks on an artist's child albums feature the artist, for example if it's a compilation album.
        """
        # TODO: Use a set to remove duplicates
        # TODO: Add options for what's considered a duplicate e.g. live versions, remixes
        tracks = super().gather_tracks()
        return [track for track in tracks if self in track.artists]

    def get_children(self):
        # TODO: album_group (appears on, single, album) is specific to the artist and is currently being missed
        if not self.children:
            #(f"ARTIST {self.name} LOADING CHILDREN")
            # Request all remaining tracks
            self.sp.fetch_artist_albums(self)
        return self.children