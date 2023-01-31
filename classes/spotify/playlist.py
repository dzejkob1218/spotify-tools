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

    def __init__(self, sp, raw_data, children=None):
        spotify.Resource.__init__(self, sp, raw_data)
        spotify.Collection.__init__(self, sp, children)
        # TODO: Does storing the initial 100 children (which increases code complexity), ever come in handy?
        self.children_loaded = len(self.children) == self.total_tracks  # Are all tracks loaded, not only the initial 100
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

    def get_children(self):
        if not self.children_loaded:
            print(f"PLAYLIST {self.name} LOADING CHILDREN")
            total_tracks = self.attributes["total_tracks"]
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

    # Legacy function
    def get_track_features(self):
        """ Returns a list of track attributes that successfully loaded their features and can be filtered and sorted """
        loaded, unloaded = [], []
        for track in self.children:
            loaded.append(track.attributes) if track.features else unloaded.append(track.attributes)
        return loaded, unloaded
