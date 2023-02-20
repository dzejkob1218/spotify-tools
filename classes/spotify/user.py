import classes.spotify as spotify


class User(spotify.Resource, spotify.Collection):
    # TODO: Urls? Images?
    child_type = spotify.Playlist
    detail_names = ['uri', 'id', 'followers', 'name']
    detail_procedures = {
        'followers': ("followers", lambda data: data["total"]),
        'name': ("display_name", None),
    }
    """
    Note: Saved tracks, albums and artists are only available for an authorized user, so they belong to the session rather than to the user object.
    """

    def __init__(self, sp, raw_data, children=None):
        # Resource init
        spotify.Resource.__init__(self, sp, raw_data)

        # Collection init
        # TODO: The old function for loading attributes assumes 'tracks' are always there, is this true?
        spotify.Collection.__init__(self, sp, name=None, children=children)

    def get_children(self):
        self.children = self.sp.fetch_user_playlists(self)
        self.children_loaded = True
        return self.children
