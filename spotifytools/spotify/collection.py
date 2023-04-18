from typing import List
from spotifytools.filters import Filter
import spotifytools.spotify as spotify
from spotifytools.spotify.resource import Resource


class Collection(spotify.Object):
    """Represents any collection of Spotify."""
    child_type = Resource

    def __init__(self, sp, children=None, children_loaded=False, name=None):
        self.sp = sp  # TODO: Look into making resource ignorant of the session.
        self.name = name or self.name  # Replace name only if specified.
        self.children: List[spotify.Object] = children or []
        self.filters: List[Filter] = []
        self.children_loaded = children_loaded
        # TODO: Make features work as they do in Track, where None is unloaded and False means unavailable.
        self.features = {}  # Average values of child details.

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
        if 'total_tracks' in self.details:
            return self.details['total_tracks']
        else:
            return sum(child.count_tracks() for child in self.get_children())

    # TODO: Merge details and features
    def get_features(self, reload=False):
        # TODO: Add quantitive features; most popular artists, languages
        """
        Downloads and updates features for all children tracks and their average values.

        This will cause all subcollections to load.
        """
        # TODO: Reimplement following: 'release_year', 'artists_number'
        # Details that can be summed up and averaged.
        summable = ['popularity', 'energy', 'dance', 'valence', 'duration', 'explicit', 'tempo', 'live', 'speech', 'acoustic', 'instrumental', 'mode', 'signature', 'track_number']

        if not self.features:
            # TODO: Add options for loading new tracks and forcing a refresh on all tracks
            # TODO: There is a difference between artist's tracks' average features and albums' average features
            # Load complete tracks.
            tracks = self.get_tracks()
            self.sp.load(tracks, details=True, features=True)
            # Initialize the dictionary to hold the sums of values and resources.
            sums = {detail: {'sum': 0, 'count': 0} for detail in summable}
            for child in tracks:
                for detail in summable:
                    if detail in child.details:
                        sums[detail]['sum'] += child.details[detail]
                        sums[detail]['count'] += 1
            for detail in sums:
                if sums[detail]['count']:
                    self.features[detail] = sums[detail]['sum']/sums[detail]['count']
        return self.features

