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
    # TODO : Downloading track features is not needed for basic discovery and it hugely tanks performance
    # Viable children types: Track
    def __init__(self, sp, raw_data, children=None):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children)

    def gather_tracks(self):
        """
        Extends Collection's function to exclude songs by other artists.

        Not all tracks on an artist's child albums feature the artist, for example if it's a compilation album.
        """
        # TODO: Use a set to remove duplicates
        # TODO: Add options for what's considered a duplicate e.g. live versions, remixes
        tracks = super().gather_tracks()
        return [track for track in tracks if self in track.artists]

    def get_complete_children(self):
        children = self.get_children()
        incomplete_albums = list(filter(lambda album: not album.details_complete, children))
        # TODO: Does it makes sense to merge features and details fetch methods? (one has a limit of 50, the other 100)
        if incomplete_albums:
            self.sp.fetch_album_details(incomplete_albums)
        return children

    def get_children(self):
        # TODO: album_group (appears on, single, album) is specific to the artist and is currently being missed
        if not self.children_loaded:
            #(f"ARTIST {self.name} LOADING CHILDREN")
            # Request all remaining tracks
            self.sp.fetch_artist_albums(self)
            self.children_loaded = True
        return self.children

    def get_top_tracks(self, remove_duplicates=False):
        return self.sp.fetch_artist_top_tracks(self, remove_duplicates)