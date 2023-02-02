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
SUMMABLE_DETAILS = {'popularity', 'duration', 'track_number', 'explicit', 'mode'}
SUMMABLE_FEATURES = {'signature', 'tempo', 'valence', 'dance', 'speech', 'acoustic', 'instrumental', 'live', 'energy',
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
        """Loads, caches and returns all available children."""
        pass

    def count_tracks(self):
        if 'total_tracks' in self.attributes:
            return self.attributes['total_tracks']
        else:
            tracks = 0
            for child in self.get_complete_children():
                tracks += child.count_tracks()
            return tracks

    def gather_tracks(self):
        """Recursively return all tracks in this collection and all subcollections."""
        # TODO: Use a set to remove duplicates
        # TODO: Different people may have different preferences on which version to keep (f.e. older vs newer release).
        # TODO: Add options for what's considered a duplicate e.g. live versions, remixes
        tracks = set()
        for sub in self.get_children():
            if isinstance(sub, Collection):
                sub.get_children()
                tracks.update(sub.gather_tracks())
            elif isinstance(sub, spotify.Track):
                tracks.add(sub)
        return list(tracks)

    def get_complete_children(self):
        # TODO: Right now this is handled by inheriting classes, make the session recognise the correct type itself.
        pass

    def get_complete_tracks(self, features=False, remove_duplicates=False):
        """Makes sure all tracks under this collection are fully loaded and returns them."""
        all_tracks = self.gather_tracks()
        # Getting track features and details is much faster in bulk, it has to be done by the parent
        incomplete_tracks = list(filter(lambda track: not track.details_complete, all_tracks))
        # TODO: Does it makes sense to merge features and details fetch methods? (one has a limit of 50, the other 100)
        if incomplete_tracks:
            self.sp.fetch_track_details(incomplete_tracks)

        if features:
            tracks_without_features = list(filter(lambda track: track.features is None, all_tracks))
            if tracks_without_features:
                self.sp.fetch_track_features(tracks_without_features)

        # TODO: Temporary check, test if there's any way to break this
        all_tracks = self.gather_tracks()
        incomplete_tracks = list(filter(lambda track: not track.details_complete, all_tracks))
        if features:
            tracks_without_features = list(filter(lambda track: track.features is None, all_tracks))
        if incomplete_tracks or (features and tracks_without_features):
            raise Exception("Tracks without features or attributes")

        # TODO: Temporary simplified code for removing duplicates, later add more options
        if remove_duplicates:
            all_tracks = sorted(all_tracks, key=lambda track: track.popularity, reverse=True)
            all_tracks = helpers.remove_duplicates(all_tracks)

        return all_tracks

    def get_features(self):
        # TODO: Add quantitive features; most popular artists, languages
        """
        Downloads and updates features for all children tracks and their average values.

        This will cause all subcollections to load.
        """
        if not self.features:
            # TODO: Add options for loading new tracks and forcing a refresh on all tracks
            # TODO: There is a difference between artist's tracks' average features and albums' average features
            all_tracks = self.get_complete_tracks()
            detail_sums = dict().fromkeys(SUMMABLE_DETAILS, 0)
            feature_sums = dict().fromkeys(SUMMABLE_FEATURES, 0)
            tracks_with_features = 0
            for child in all_tracks:
                # Every complete track has details.
                for detail in detail_sums:
                    detail_sums[detail] += child.attributes[detail]
                # Not every track has features, but if it does they're always complete.
                if child.features:
                    tracks_with_features += 1
                    for feature in feature_sums:
                        feature_sums[feature] += child.features[feature]
            for detail_sum in detail_sums:
                self.features[detail_sum] = detail_sums[detail_sum] / len(all_tracks)
            for feature_sum in feature_sums:
                self.features[feature_sum] = feature_sums[feature_sum] / tracks_with_features
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
