import time
from typing import List
import classes.spotify as spotify
import classes.filters as filters
import helpers
from classes.spotify.resource import Resource
"""
Any collection of Spotify resources
"""
# TODO: Reimplement following: 'release_year', 'artists_number'
SUMMABLE_FEATURES = {'signature', 'tempo', 'popularity', 'duration', 'valence', 'dance',
                             'speech', 'acoustic', 'instrumental', 'live', 'track_number', 'energy', 'explicit',
                             'mode'}

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
        self.features = {}  # Average values of child features

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
            if isinstance(sub, Collection):
                sub.get_children()
                tracks.update(sub.gather_tracks())
            elif isinstance(sub, spotify.Track):
                tracks.add(sub)
        return list(tracks)


    def get_features(self):
        # TODO: Add quantitive features; most popular artists, languages
        """
        Downloads and updates features for all children tracks and their average values.

        This will cause all subcollections to load.
        """
        if not self.features:
            # TODO: Add options for loading new tracks and forcing a refresh on all tracks
            # TODO: There is a difference between artist's tracks' average features and albums' average features
            all_tracks = self.gather_tracks()
            # Getting track features and details is much faster in bulk, it has to be done by the parent
            incomplete_tracks = list(filter(lambda track: not track.details_complete, all_tracks))
            self.sp.fetch_track_details(incomplete_tracks)
            tracks_without_features = list(filter(lambda track: not track.features, all_tracks))
            self.sp.fetch_track_features(tracks_without_features)

            # TODO: Temporary check, test if there's any way to break this

            all_tracks = self.gather_tracks()
            incomplete_tracks = list(filter(lambda track: not track.details_complete, all_tracks))
            tracks_without_features = list(filter(lambda track: not track.features, all_tracks))
            if incomplete_tracks or tracks_without_features:
                raise Exception("Tracks without features or attributes")

            artists = {}
            languages = {}

            # Calculate averages
            feature_sums = dict().fromkeys(SUMMABLE_FEATURES, 0)
            for child in all_tracks:
                child_details = {**child.features, **child.attributes}
                for feature in feature_sums:
                    feature_sums[feature] += child_details[feature]
            for feature_sum in feature_sums:
                self.features[feature_sum] = feature_sums[feature_sum]/len(all_tracks)

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
        
    
    def search_uri(self, uri):
        "Recursively search for a spotify resource within this object's children."
        for child in self.children:
            if child.uri == uri:
                return child
            elif match := child.search_uri(uri):
                return match
        return None
    
    
"""
