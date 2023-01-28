import classes.spotify as spotify
import helper
from classes.spotify.track import Track as Track
from helpers.parser import filter_false_tracks, sort_image_urls

SUMMABLE_FEATURES = {'signature', 'release_year', 'tempo', 'popularity', 'duration', 'valence', 'dance',
                             'speech', 'acoustic', 'instrumental', 'live', 'number', 'energy', 'explicit',
                             'mode', 'artists_number'}

# TODO: Data about when a track was added to a playlist is being lost right now
class Playlist(spotify.Resource, spotify.Collection):
    child_type = Track

    # Viable children types: Track
    def __init__(self, sp, raw_data, children=None):
        # Resource init
        spotify.Resource.__init__(self, sp, raw_data)
        # Collection init
        spotify.Collection.__init__(self, sp, children)

        self.children_loaded = len(self.children) == self.total
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
            self.load_children()
        if recursive:
            for child in self.children:
                child.load(recursive=recursive)
        self.get_features()

    def load_children(self):
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

    def get_features(self):
        # TODO: Add quantitive features; most popular artists, languages
        """Downloads and updates features for all children tracks and their average values."""
        if not self.features:
            # TODO: Add an options for loading new tracks and forcing a refresh on all tracks
            print(f"PLAYLIST {self.name} LOADING FEATURES")
            track_features = self.sp.fetch_track_features([item.uri for item in self.children])
            # TODO: This should be redundant
            if not len(self.children) == len(track_features):
                raise Exception("Not all features were loaded")

            # Saves all tracks and their audio features into a list of children objects
            for i in range(len(self.children)):
                self.children[i].parse_features(track_features[i])

        feature_sums = dict().fromkeys(SUMMABLE_FEATURES, 0)
        featured_tracks = 0
        attribute_tracks = 0
        nones = 0
        for child in self.children:
            if child.attributes:
                attribute_tracks += 1
            if child.features:
                featured_tracks += 1
            if child.features == None:
                nones += 1
            child_details = {**child.features, **child.attributes}
            for feature in feature_sums:
                feature_sums[feature] += child_details[feature]
        print(f"Attributed:{attribute_tracks}, Featured:{featured_tracks}, Nones:{nones}")
        if attribute_tracks == featured_tracks:
            for sum in feature_sums:
                self.features[sum] = feature_sums[sum]/attribute_tracks
        else:
            exit()
        helper.show_dict(self.features)


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
