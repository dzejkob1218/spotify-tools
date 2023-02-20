"""
Represents any Spotify resource or collection the program can operate on
"""

class Object:
    def get_name(self):
        return None

    def load(self, recursive=False):
        """
        Download all data about the object and its children.
        """
        pass