import classes.spotify as spotify
from classes.spotify.track import Track
from helpers import sort_image_urls


# TODO: Data about when a track was added to a playlist is being lost right now
class Playlist(spotify.Resource, spotify.Collection):
    child_type = Track
    detail_names = ['uri', 'name', 'public', 'description', 'followers', 'total_tracks', 'images']
    detail_procedures = {
        'followers': ("followers", lambda data: data["total"]),
        'total_tracks': ("tracks", lambda data: data["total"]),
        'images': ('images', lambda data: sort_image_urls(data)),
    }

    def __init__(self, sp, raw_data, children=None, children_loaded=False):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children, children_loaded)
        #self.user_is_owner = self.owner == sp.fetch_user().uri

        # TODO: Introduce an attribute for the owner user object

    def load(self, recursive=False):
        # TODO: This should be pushed up
        """Loads all tracks and their details."""
        if not self.children_loaded:
            self.get_children()
        if recursive:
            for child in self.children:
                child.load(recursive=recursive)
        self.get_features()

    # Legacy function
    def get_track_features(self):
        """ Returns a list of track attributes that successfully loaded their features and can be filtered and sorted """
        loaded, unloaded = [], []
        for track in self.children:
            loaded.append(track.attributes) if track.features else unloaded.append(track.attributes)
        return loaded, unloaded
