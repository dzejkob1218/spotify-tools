from typing import Dict

from classes import spotify
from exceptions import SpotifyToolsException
from helpers import uri_to_url, filter_false_tracks, uri_list


class ResourceFactory:

    def __init__(self, sp):
        self.sp = sp
        self._cache = {}

    def get_resource(self, raw_data: Dict):
        """Return an existing resource by uri or create a new one."""
        if 'uri' not in raw_data:
            raise SpotifyToolsException(f"No URI supplied for resource: {raw_data}.")
        uri = raw_data['uri']
        # Check if the resource exists and return it if does.
        if uri in self._cache:
            resource = self._cache[uri]
            # Parse the new data if it contains some missing information. # TODO: test performance on this
            # TODO isn't doing it this way more resource-intensive than just parsing the details each time?
            if resource.missing_details and any(missing in raw_data for missing in resource.missing_details):
                resource.parse_details(raw_data)
            return resource
        else:
            # Create a new resource if it didn't exist.
            resource = self._parse_resource(raw_data)
            return resource

    def _parse_resource(self, raw_data: Dict):
        """
        Recognizes the resource type from the raw data and calls the correct constructor or method.

        This should be the only way through which instances of Resource are initialized.
        """
        resource = None
        # TODO: Check for type in uri instead of keys in the data
        # Playlist
        if "type" in raw_data and raw_data["type"] == "playlist":
            resource = self._parse_playlist(raw_data)

        # Album
        if "type" in raw_data and raw_data["type"] == "album":
            resource = self._parse_album(raw_data)

        # Track
        if "type" in raw_data and raw_data["type"] == "track" or "track" in raw_data:
            resource = self._parse_track(raw_data)

        # User
        if "type" in raw_data and raw_data["type"] == "user":
            resource = spotify.User(self.sp, raw_data=raw_data)

        # Artist
        if "type" in raw_data and raw_data["type"] == "artist":
            resource = spotify.Artist(self.sp, raw_data=raw_data)

        if not resource:
            raise SpotifyToolsException(f"Parser didn't recognize object: {raw_data}")

        # Cache and return
        self._cache[resource.uri] = resource
        return resource

    def _parse_playlist(self, raw_data):
        # Create the user.
        owner = self.get_resource(raw_data["owner"])
        # Parse track data that may be included with the playlist data.
        if children_data := raw_data["tracks"].pop("items", None):
            children = [self.get_resource(track) for track in filter_false_tracks(children_data)]
            children_loaded = not raw_data["tracks"]["next"]
        else:
            children = None
            children_loaded = False
        # Create the playlist.
        return spotify.Playlist(self.sp, raw_data=raw_data, owner=owner, children=children,
                                children_loaded=children_loaded)

    def _parse_album(self, raw_data):
        # Parse artist data.
        artists = [self.get_resource(artist) for artist in raw_data['artists']]
        # Create the album.
        album = spotify.Album(self.sp, raw_data=raw_data, artists=artists)
        # Tracks in album data miss their 'album' key, so it has to be injected after the album is created.
        if children_data := raw_data["tracks"].pop("items", None) if "tracks" in raw_data else None:
            children = []
            for child in filter_false_tracks(children_data):
                # Restore the reference to the album if it's missing.
                if 'album' not in child:
                    child['album'] = {'uri': raw_data['uri']}
                children.append(self.get_resource(child))
            album.children = children
            album.children_loaded = not raw_data["tracks"]["next"]
        return album

    def _parse_track(self, raw_data):
        # Parse artist and album data.
        artists = [self.get_resource(artist) for artist in raw_data['artists']]
        album = self.get_resource(raw_data['album'])
        # Create the track.
        track = spotify.Track(self.sp, raw_data=raw_data, artists=artists, album=album)
        return track
