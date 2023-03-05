from typing import Dict

import spotifytools.spotify as spotify
from spotifytools.exceptions import SpotifyToolsException
from spotifytools.helpers import filter_false_tracks, details_adapter


class ResourceFactory:

    def __init__(self, sp):
        self.sp = sp
        self.cache = {}

    def get_resource(self, raw_data: Dict, refresh=False):
        """
        Return an existing resource or create a new one from Spotify API data.

        This is the only way through which instances of Resource should be initialized or updated.
        """
        data = details_adapter(raw_data)

        if 'uri' not in data:
            raise SpotifyToolsException(f"No URI supplied for resource: {data}.")
        uri = data['uri']

        # Check if the resource exists and return it if it does.
        if uri in self.cache:
            resource = self.cache[uri]
            # Parse the new data if it contains some missing information.
            if new_details := {detail: data[detail] for detail in data if detail not in resource.details}:
                resource.parse_details(new_details)
            return resource
        else:
            # Create a new resource if it doesn't exist.
            resource = self._parse_resource(data)
            return resource

    def _parse_resource(self, raw_data: Dict):
        """Recognizes the resource type from the raw data and calls the correct constructor or method."""
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
        self.cache[resource.uri] = resource
        return resource

    def _parse_playlist(self, raw_data):
        # Create the user.
        owner = self.get_resource(raw_data["owner_data"])
        # Parse track data that may be included with the playlist data.
        if 'items' in raw_data['tracks_data']:
            children = [self.get_resource(track) for track in filter_false_tracks(raw_data['tracks_data']['items'])]
            children_loaded = not raw_data['tracks_data']["next"]
        else:
            children = None
            children_loaded = False
        # Create the playlist.
        return spotify.Playlist(self.sp, raw_data=raw_data, owner=owner, children=children,
                                children_loaded=children_loaded)

    def _parse_album(self, raw_data):
        # Parse artist data.
        artists = [self.get_resource(artist) for artist in raw_data["artists_data"]]
        # Create the album.
        album = spotify.Album(self.sp, raw_data=raw_data, artists=artists)
        # Tracks in album data miss their 'album' key, so it has to be injected after the album is created.
        if 'tracks_data' in raw_data and 'items' in raw_data['tracks_data']:
            children = []
            children_data = raw_data['tracks_data']['items']
            for child in filter_false_tracks(children_data):
                # Restore the reference to the album if it's missing.
                if 'album_data' not in child:
                    child['album_data'] = {'uri': raw_data['uri']}
                children.append(self.get_resource(child))
            album.children = children
            album.children_loaded = not raw_data["tracks_data"]["next"]
        return album

    def _parse_track(self, raw_data):
        # Parse artist and album data.
        artists = [self.get_resource(artist) for artist in raw_data["artists_data"]]
        album = self.get_resource(raw_data["album_data"])
        # Create the track.
        track = spotify.Track(self.sp, raw_data=raw_data, artists=artists, album=album)
        return track
