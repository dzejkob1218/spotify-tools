import classes.spotify as spotify
from classes.spotify.track import Track
from helpers import sort_image_urls


class Album(spotify.Resource, spotify.Collection):
    child_type = Track
    # TODO: 'genre' is often found in album responses, but it seems to never have a value - test this
    detail_names = ['uri', 'url', 'images', 'album_type', 'name', 'release_date', 'release_date_precision', 'total_tracks', 'popularity', 'label', 'genres', 'copyrights']
    detail_procedures = {
        'url': ('external_urls', lambda data: data['spotify']),
        'images': ('images', lambda data: sort_image_urls(data)),
    }

    # TODO: When called for directly (like in a search) every album comes with first 50 tracks, which in most cases is all of them.
    # TODO: These tracks miss album (obv), popularity and external id. Measure how much saving that data would save.
    def __init__(self, sp, raw_data, artists, children=None):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children)
        self.artists = artists
        # self.children_loaded = len(self.children) == self.total

    def get_children(self):
        if not self.children:
            self.sp.fetch_album_tracks(self)
        return self.children
