import spotifytools.spotify as spotify
from spotifytools.spotify.album import Album


class Artist(spotify.Resource, spotify.Collection):
    child_type = Album

    def __init__(self, sp, raw_data, children=None):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children)

    def get_tracks(self):
        """
        Recursively return all tracks in this collection and all subcollections belonging to this artist.

        Overrides the Collection implementation to only return tracks that belong to the artist (for compilation albums)
        """
        tracks = super().get_tracks()
        return [track for track in tracks if self in track.artists]

    def get_top_tracks(self, remove_duplicates=False):
        """Downloads and returns top 10 tracks for this artist."""
        return self.sp.fetch_artist_top_tracks(self, remove_duplicates)
