import spotifytools.spotify as spotify
from spotifytools.helpers import details_adapter


class Resource(spotify.Object):
    """Represents any Spotify resource that has a uri and can be retrieved from Spotify API."""
    def __init__(self, sp, raw_data=None):
        self.details = {}  # Static attributes reflecting an existing spotify resource, added to __dict__
        self.uri: str
        self.name: str
        # TODO: Request complete details only if the required data is missing.
        self.parse_details(raw_data)
        # Require URI to be provided in the initial details.
        if 'uri' not in self.details:
            raise Exception("URI not provided to resource.")

    def get_name(self):
        return self.name

    def parse_details(self, details):
        """
        Updates resource with details from a Spotify API response.

        The track data in Spotify responses arbitrarily misses important values depending on the initial request.
        It must be assumed any value can be missing and will need to be updated later.
        """
        self.details.update(details)
        self.__dict__.update(details)



