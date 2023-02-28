import spotifytools.spotify as spotify


class Resource(spotify.Object):
    """Represents any Spotify resource that has a uri and can be retrieved from Spotify API."""

    # Details that need to be extracted from the Spotify data for the item to be considered completely loaded.
    detail_names = ['uri']

    # TODO: Replace this with an adapter on data returned from spotify
    # Procedures for extracting specific details. Specified as a tuple of the detail's alias and a lambda function.
    detail_procedures = {}

    def __init__(self, sp, raw_data=None):
        self.attributes = {}  # Static attributes reflecting an existing spotify resource, added to __dict__
        # TODO: Request complete details only if the required data is missing.
        self.missing_details = None
        self.parse_details(raw_data)

    def get_name(self):
        return self.name

    def missing_detail_keys(self):
        """
        Returns missing attribute keys.

        This returns the keys that are used in Spotify API responses, not the local aliases.
        """
        missing = [detail for detail in self.detail_names if detail not in self.attributes]
        return [self.detail_procedures[detail][0] if detail in self.detail_procedures else detail for detail in missing]

    def parse_details(self, raw_data):
        """
        Updates resource with details from a Spotify API response.

        The track data in Spotify responses arbitrarily misses important values depending on the initial request.
        It must be assumed any value can be missing and will need to be updated later.
        """
        for detail in self.detail_names:
            try:
                if detail in self.detail_procedures:
                    # Parse details requiring a more complex procedure.
                    alias, procedure = self.detail_procedures[detail]
                    value = procedure(raw_data[alias]) if procedure else raw_data[alias]
                else:
                    # If no procedure is stated, assume the value is available by key.
                    value = raw_data[detail]
                self.attributes[detail] = value
            except KeyError:
                pass
        # Update the object with new attributes and check if the details are complete.
        self.__dict__.update(self.attributes)
        # Check which keys are missing.
        self.missing_details = self.missing_detail_keys()
        if 'uri' in self.missing_details:
            raise Exception("URI not provided to resource.")

