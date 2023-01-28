import classes.spotify as spotify


class User(spotify.Resource, spotify.Collection):
    child_type = spotify.Playlist

    """
    Note: Saved tracks, albums and artists are only available for an authorized user, so they are a part of the session rather than of the user object.
    """

    def __init__(self, sp, raw_data, children=None):
        # Resource init
        spotify.Resource.__init__(self, sp, raw_data)

        # Collection init
        # TODO: The old function for loading attributes assumes 'tracks' are always there, is this true?
        spotify.Collection.__init__(self, sp, name=None, children=children)

    def load_children(self):
        self.children = self.sp.fetch_user_playlists(self)
        self.children_loaded = True
        return self.children

    # Details
    def parse_details(self, raw_data):
        self.attributes = {
            # TODO: Images?
            "uri": raw_data["uri"],
            "id": raw_data["id"],
            "name": raw_data["display_name"],
            "followers": raw_data["followers"]["total"],
        }
