import time
from typing import List
import spotifytools.spotify as spotify
import spotifytools.filters as filters
import spotifytools.helpers
from spotifytools.spotify.resource import Resource

"""
Any collection of Spotify resources
"""
# TODO: Reimplement following: 'release_year', 'artists_number'
SUMMABLE_DETAILS = {'popularity', 'duration', 'track_number', 'explicit', 'mode'}
SUMMABLE_FEATURES = {'signature', 'tempo', 'valence', 'dance', 'speech', 'acoustic', 'instrumental', 'live', 'energy',
                     'mode'}


class Collection(spotify.Object):
    child_type = Resource

    def __init__(self, sp, children=None, children_loaded=False, name=None):
        self.sp = sp  # TODO: Look into making resource ignorant of the session.
        self.name = name or self.name  # Replace name only if specified
        self.children: List[spotify.Object] = children or []
        self.filters: List[filters.Filter] = []
        self.statistics = {}  # All average values calculated for this collection so far
        self.children_loaded = children_loaded
        self.features = {}  # Average values of child features

    def __iter__(self):
        return iter(self.children)

    def get_name(self):
        return self.name or "Unnamed Collection"

    def get_children(self):
        """Loads, caches and returns all available children."""
        if not self.children_loaded:
            self.sp.load_children(self)
        return self.children

    def get_tracks(self):
        """Recursively return all tracks in this collection and all subcollections."""
        # TODO: Different people may have different preferences on which version to keep (f.e. older vs newer release).
        # TODO: Add options for what's considered a duplicate e.g. live versions, remixes
        tracks = set()
        for sub in self.get_children():
            if isinstance(sub, Collection):
                tracks.update(sub.get_tracks())
            elif isinstance(sub, spotify.Track):
                tracks.add(sub)
        return list(tracks)

    def count_tracks(self):
        """Estimates the total number of tracks under this collection by summing up 'total_tracks' attribute."""
        if 'total_tracks' in self.attributes:
            return self.attributes['total_tracks']
        else:
            return sum(child.count_tracks() for child in self.get_children())

    # TODO: Merge details and features
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

