import classes.spotify as spotify

"""
Represents a Spotify resource that has a uri and can be retrieved from Spotify API
"""


class Resource(spotify.Object):

    # Details that need to be extracted from the Spotify data for the item to be considered completely loaded.
    detail_names = []

    # Procedures for extracting specific details. Specified as a tuple of the detail's alias and a lambda function.
    detail_procedures = {}

    def __init__(self, sp, raw_data=None):
        self.attributes = {}  # Static attributes reflecting an existing spotify resource, added to __dict__
        self.details_complete = False
        self.parse_details(raw_data)

    def missing_detail_keys(self):
        """
        Returns missing attribute keys.

        Note this returns the names that the missing data is stored under in Spotify responses, not the attribute names.
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
                    # In no procedure is stated, assume the value is available by key.
                    value = raw_data[detail]
                self.attributes[detail] = value
            except KeyError:
                pass
        # Update the object with new attributes and check if the details are complete
        self.__dict__.update(self.attributes)
        self.details_complete = not self.missing_detail_keys()

