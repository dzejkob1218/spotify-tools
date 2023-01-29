"""
Additional methods:
- Recommended (artist)
- Recommended (genre)
- Related

"""

SUMMABLE_FEATURES = {'signature', 'release_year', 'tempo', 'popularity', 'duration', 'valence', 'dance',
                     'speech', 'acoustic', 'instrumental', 'live', 'number', 'energy', 'explicit',
                     'mode', 'artists_number'}

import classes.spotify as spotify
from classes.spotify.album import Album
from helpers import sort_image_urls


class Artist(spotify.Resource, spotify.Collection):
    child_type = Album

    # Viable children types: Track
    def __init__(self, sp, raw_data, children=None):
        # Resource init
        spotify.Resource.__init__(self, sp, raw_data)
        # Collection init
        spotify.Collection.__init__(self, sp, children)

        self.details_complete = False

        print(f"CREATING ARTIST {self.name}")

    def parse_details(self, raw_data):
        # Write object attributes
        self.attributes = {
            "uri": raw_data["uri"],
            "name": raw_data["name"],
            "url": raw_data['external_urls']['spotify'],
        }

        if len(raw_data) > 6:
            self.details_complete = True
            image_urls = (sort_image_urls(raw_data["images"]))  # Get a list of image urls sorted by size
            self.attributes.update({
                    "miniature": image_urls[0] if image_urls else None,
                    "image": image_urls[-1] if image_urls else None,
                    "followers": raw_data["followers"]["total"],
                    "popularity": raw_data["popularity"],
                    "genres": raw_data["genres"],
                })

    def get_children(self):
        if not self.children:
            print(f"ARTIST {self.name} LOADING CHILDREN")
            # Request all remaining tracks
            self.children = self.sp.fetch_artist_albums(self.uri)
        return self.children