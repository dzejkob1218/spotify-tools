class SpotifyToolsException(Exception):
    pass


class SpotifyToolsUnauthorizedException(SpotifyToolsException):
    pass


class SpotifyToolsNotFoundException(SpotifyToolsException):
    pass
