from spotifytools.filters.resource_filter import ResourceFilter
# TODO: Replace this with a general filter that checks for any genius feature

class LanguageFilter(ResourceFilter):
    def __init__(self, language):
        self.language = language

    def condition(self, item):
        return item.genius_features and item.genius_features.language == self.language