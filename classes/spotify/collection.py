from typing import List
import classes.spotify as spotify
import classes.filters as filters

"""
Any collection of Spotify resources
"""


class Collection(spotify.Object):
    # Viable children types: All
    # child_type = spotify.Resource

    def __init__(self, sp, children=None, name=None):
        self.sp = sp
        self.name = name or self.name  # Replace name only if specified
        self.children: List[spotify.Object] = children or []
        self.filters: List[filters.Filter] = []
        self.statistics = {}  # All average values calculated for this collection so far
        self.children_loaded = False
        self.length = 0  # TODO: Before the collection loads fully, get its length from attribute, on load change this value to actual number of children

        # TODO : check if this has any effect on performance
        # self.__delattr__('raw_object')

    def __iter__(self):
        return iter(self.children)

    def get_name(self):
        return self.name or "Unnamed Collection"

    def load_children(self):
        """Loads all available children by sending requests to Spotify."""
        pass

    def gather_tracks(self, keep_duplicates=False):
        """Recursively return all tracks in this collection and all subcollections."""
        # TODO: Use a set to remove duplicates
        tracks = []
        for sub in self.children:
            if isinstance(sub, type(self)):
                tracks.extend(sub.gather_tracks())
            elif isinstance(sub, spotify.Track):
                tracks.append(sub)
        return tracks

    def search_uri(self, uri):
        """Recursively search for a spotify resource within this object's children."""
        for child in self.children:
            if child.uri == uri:
                return child
            elif match := child.search_uri(uri):
                return match
        return None


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
