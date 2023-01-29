from typing import List
import classes.spotify as spotify
import classes.filters as filters
from classes.spotify.resource import Resource
"""
Any collection of Spotify resources
"""

SUMMABLE_FEATURES = {'signature', 'release_year', 'tempo', 'popularity', 'duration', 'valence', 'dance',
                             'speech', 'acoustic', 'instrumental', 'live', 'number', 'energy', 'explicit',
                             'mode', 'artists_number'}

class Collection(spotify.Object):
    # Viable children types: All
    child_type = Resource

    def __init__(self, sp, children=None, name=None):
        self.sp = sp
        self.name = name or self.name  # Replace name only if specified
        self.children: List[spotify.Object] = children or []
        self.filters: List[filters.Filter] = []
        self.statistics = {}  # All average values calculated for this collection so far
        self.children_loaded = False
        self.length = 0  # TODO: Before the collection loads fully, get its length from attribute, on load change this value to actual number of children
        self.features = {}  # Average values of track features

        # TODO : check if this has any effect on performance
        # self.__delattr__('raw_object')

    def __iter__(self):
        return iter(self.children)

    def get_name(self):
        return self.name or "Unnamed Collection"

    # TODO: Consider splitting into get and load functions
    def get_children(self):
        """Loads all available children by sending requests to Spotify."""
        pass

    def gather_tracks(self, keep_duplicates=False):
        """Recursively return all tracks in this collection and all subcollections."""
        # TODO: Use a set to remove duplicates
        # TODO: Add options for what's considered a duplicate e.g. live versions, remixes
        tracks = set()
        self.get_children()
        for sub in self.children:
            if isinstance(sub, type(self)):
                sub.get_children()
                tracks.update(sub.gather_tracks())
            elif isinstance(sub, spotify.Track):
                tracks.add(sub)
        return list(tracks)

    def search_uri(self, uri):
        """Recursively search for a spotify resource within this object's children."""
        for child in self.children:
            if child.uri == uri:
                return child
            elif match := child.search_uri(uri):
                return match
        return None

    def get_features(self):
        # TODO: Add quantitive features; most popular artists, languages
        """Downloads and updates features for all children tracks and their average values."""
        if not self.features:
            self.get_children()
            # TODO: Add an options for loading new tracks and forcing a refresh on all tracks
            print(f"{self.name} LOADING FEATURES")
            # Getting track features is much faster in bulk, it has to be done by the parent
            # TODO: Gather tracks first, load features on them
            # TODO: There is a difference between artist's tracks' average features and albums' average features
            track_features = self.sp.fetch_track_features([item.uri for item in self.children])
            # TODO: This should be redundant
            if not len(self.children) == len(track_features):
                raise Exception("Not all features were loaded")

            artists = {}
            languages = {}

            # Saves pass the audio features to the children to parse
            for i in range(len(self.children)):
                child = self.children[i]
                child.parse_features(track_features[i])
                # Sum up other attributes
                #for artist in child.artists:
                #    if artist not in

            # Calculate averages
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
                raise Exception()
        return self.features


"""
Legacy Code:
    # Takes a list of attribute names and returns average, minimum and maximum values for sub-collections
    def average_children_details(self, attributes, child_number):
        # Initialize the dictionary for child attributes where each value is an array of [average, min, max]
        base_dict = {'avg': 0, 'min': None, 'max': None}
        child_attributes = dict.fromkeys(attributes)
        for attr in child_attributes:
            child_attributes[attr] = base_dict.copy()

        # Iterate through each child and add up the values
        for sub in self.children:
            for attr in attributes:
                if attr in sub.attributes:
                    new_value = sub.attributes[attr]
                    total = child_attributes[attr]
                    total['avg'] += new_value
                    total['min'] = new_value if total['min'] is None or total['min'] > new_value else total['min']
                    total['max'] = new_value if total['max'] is None or total['max'] < new_value else total['max']

        # Divide the attributes by total tracks
        for attr in child_attributes:
            total = child_attributes[attr]
            total['avg'] /= child_number
            total['min'], total['max'] = round(total['min']), round(total['max'])

        self.averages.update(child_attributes)
"""
