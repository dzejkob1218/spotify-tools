import classes.spotify as spotify
from classes.spotify.track import Track
from helpers import sort_image_urls


class Album(spotify.Resource, spotify.Collection):
    child_type = Track
    # TODO: When called for directly (like in a search) every album comes with first 50 tracks, which in most cases is all of them.
    # TODO: These tracks miss album (obv), popularity and external id. Measure how much saving that data would save.
    # Viable children types: Track
    def __init__(self, sp, raw_data, artists, children=None):
        # Resource init
        spotify.Resource.__init__(self, sp, raw_data)
        # Collection init
        spotify.Collection.__init__(self, sp, children)
        self.artists = artists
        self.details_complete = False
        # self.children_loaded = len(self.children) == self.total

        print(f"CREATING ALBUM {self.name}")

    def parse_details(self, raw_data):
        image_urls = (sort_image_urls(raw_data["images"]))  # Get a list of image urls sorted by size

        # Write object attributes
        self.attributes = {
            "type": raw_data["album_type"],
            "uri": raw_data["uri"],
            "name": raw_data["name"],
            "url": raw_data['external_urls']['spotify'],
            "image": image_urls[-1] if image_urls else None,
            "release": raw_data["release_date"],
            "release_precision": raw_data["release_date_precision"],
            "release_year": int(raw_data["release_date"][:4]),
            "total": raw_data["total_tracks"],
        }

        if len(raw_data) >= 19:  # Full album response has at least 19 entries
            self.details_complete = True
            self.attributes.update({
                    "copyrights": raw_data["copyrights"],
                    "label": raw_data["label"],
                    "popularity": raw_data["popularity"],
                    "genres": raw_data["genres"],
                })

    def get_children(self):
        if not self.children:
            print(f"ALBUM {self.name} LOADING CHILDREN")
            # Request all remaining tracks
            self.children = self.sp.fetch_album_tracks(self.uri)
        return self.children