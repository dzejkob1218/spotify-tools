import classes.spotify as spotify
from classes.spotify.track import Track
from helpers import sort_image_urls



# TODO: Data about when a track was added to a playlist is being lost right now
class Playlist(spotify.Resource, spotify.Collection):
    child_type = Track

    # Viable children types: Track
    def __init__(self, sp, raw_data, children=None):
        # Resource init
        spotify.Resource.__init__(self, sp, raw_data)
        # Collection init
        spotify.Collection.__init__(self, sp, children)
        # TODO: Does storing the initial 100 children (which increases code complexity), ever come in handy?
        self.children_loaded = len(self.children) == self.total  # Are all tracks loaded, not only the initial 100
        self.user_is_owner = self.owner == sp.fetch_user().uri

    def parse_details(self, raw_data):
        # Get a list of image urls sorted by size
        image_urls = (
            sort_image_urls(raw_data["images"]) if "images" in raw_data else None
        )

        # Write object attributes
        self.attributes = {
            "uri": raw_data["uri"],
            "name": raw_data["name"],
            "miniature": image_urls[0] if image_urls else None,
            "image": image_urls[-1] if image_urls else None,
            "followers": raw_data["followers"]["total"]
            if "followers" in raw_data
            else 0,
            "owner": raw_data["owner"]["uri"],
            "owner_name": raw_data["owner"]["display_name"],
            "public": raw_data["public"],
            "total": raw_data["tracks"]["total"],
            "description": raw_data["description"],
        }

    def load(self, recursive=False):
        # TODO: Research if something like 'playlist features' exists
        """
        Loads all tracks and their details.
        """
        if not self.children_loaded:
            self.get_children()
        if recursive:
            for child in self.children:
                child.load(recursive=recursive)
        self.get_features()

    def get_children(self):
        print(f"PLAYLIST {self.name} LOADING CHILDREN")
        total_tracks = self.attributes["total"]
        total_tracks_downloaded = len(self.children)
        # TODO: Generalize this check and move up to Collection class
        if total_tracks_downloaded >= total_tracks:
            raise Exception("Load children called on loaded collection")
        # TODO: Test this
        # Request all remaining tracks
        self.children.extend(
            self.sp.fetch_playlist_tracks(
                self.uri, total_tracks, start=total_tracks_downloaded
            )
        )
        self.children_loaded = True
        return self.children



    def get_averages(self):
        # Count up attributes of included songs which can be nicely averaged out and presented
        # TODO : Add a functionality for presenting attributes which can't be just averaged (date, key, signature, most popular artist etc.)
        pass


    def get_track_features(self):
        " Returns a list of track attributes that successfully loaded their features and can be filtered and sorted "
        loaded, unloaded = [], []
        for track in self.children:
            loaded.append(track.attributes) if track.features else unloaded.append(track.attributes)
        return loaded, unloaded
