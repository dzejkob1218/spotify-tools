"""
Represents any Spotify resource or collection the program can operate on
"""

SUMMABLE_FEATURES = {'signature', 'release_year', 'tempo', 'popularity', 'duration', 'valence', 'dance',
                             'speech', 'acoustic', 'instrumental', 'live', 'number', 'energy', 'explicit',
                             'mode', 'artists_number'}

class Object:
    def get_name(self):
        return None

    def load(self, recursive=False):
        """
        Download all data about the object and its children.
        """
        pass