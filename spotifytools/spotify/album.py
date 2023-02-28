import spotifytools.spotify as spotify
from spotifytools.helpers import sort_image_urls
from spotifytools.spotify.track import Track


class Album(spotify.Resource, spotify.Collection):
    child_type = Track
    # TODO: 'genre' is often found in album responses, but it seems to never have a value - test this
    detail_names = ['uri', 'url', 'images', 'album_type', 'name', 'release_date', 'release_date_precision',
                    'total_tracks', 'popularity', 'label', 'genres', 'copyrights']
    detail_procedures = {
        'url': ('external_urls', lambda data: data['spotify']),
        'images': ('images', lambda data: sort_image_urls(data)),
    }

    def __init__(self, sp, raw_data, artists, children=None, children_loaded=False):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children, children_loaded)
        self.artists = artists
