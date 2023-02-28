from spotifytools.filters.filter import Filter


class Attribute(Filter):
    # TODO: A list of all possible attributes including descriptions should be available somewhere
    # TODO: Should these be classes?
    viable_attributes = {
        # Attributes that are either truly boolean or filtered based on resource present or missing.
        "boolean": [
            "explicit",
            "image",
            "miniature",
        ],
        # Attributes available as integers.
        "integer": [
            "multiple_artists",
            "tempo",
            "key",  # Coded 0-11 for each possible root note of a key.
            "duration",  # Duration in milliseconds.
            "number",  # Number of the track in order on its album.
            "signature",  # Describes the time signature of a track as 'signature'/4.
        ],
        # Attributes stored by Spotify as integer values from 0 to 100.
        "percentage": [
            "popularity",
            "valence",
            "energy",
            "dance",
            "speech",
            "acoustic",
            "instrumental",
            "live",
            "mode",
            # Together with 'key' attribute describes the musical key, True for major keys, False for minor keys.
        ],
    }
    # ???
    """
    'name': raw_data['name'],
    'release': raw_data['album']['release_date'],
    'release_precision': raw_data['album']['release_date_precision'],
    'release_year': int(raw_data['album']['release_date'][:4]),
    'key_name': track_key(self.audio_features['key'], self.audio_features['mode']),
    """

    """
    Filters out items based on attributes provided by spotify.
    """

    def __init__(self, attribute, _min=None, _max=None, _reverse=False):
        # Determine attribute type
        for attribute_type in self.viable_attributes:
            if attribute in self.viable_attributes[attribute_type]:
                self.attribute_type = attribute_type
                break
            raise Exception(f"Invalid attribute passed to filter ({attribute})")

        if self.attribute_type == "percentage" and any(
            100 < limit < 0 for limit in [_min, _max]
        ):
            raise Exception(
                f"Invalid limit for a percentage attribute ({attribute}, min: {_min}, max: {_max})"
            )

        self.attribute = attribute
        self.min = _min
        self.max = _max
        self.reverse = _reverse

    def filter(self, item):
        if self.attribute_type == "boolean":
            return bool(item.attributes[self.attribute]) != self.reverse
        if self.attribute_type in ["percentage", "integer"]:
            return self.min < item < self.max != self.reverse
