import classes.spotify as spotify


"""
Represents a Spotify resource that has a uri and can be retrieved from Spotify API
"""


class Resource(spotify.Object):
    def __init__(self, sp, raw_data=None):
        self.attributes = (
            {}
        )  # Static attributes reflecting an existing spotify resource, added to __dict__
        self.load_details(raw_data)
        self.__dict__.update(self.attributes)

    def get_name(self):
        return self.attributes["name"] if "name" in self.attributes else "Unnamed"

    def load_details(self, raw_data) -> bool:
        """
        Parse all attributes available in the raw data.
        Returns False if the data missed some attributes.
        """
        pass

    def get_img_urls(self, raw_data):
        """
        Extract urls to images for this object from its raw data.
        Every type of object stores image urls under a different path.
        """
        pass
