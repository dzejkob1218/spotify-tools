import time
from typing import List, Dict, Union

import requests.exceptions
import spotipy.exceptions
from spotipy import Spotify
import os
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import CacheFileHandler
import classes.spotify as spotify
import mock
import helpers
from helpers import uri_to_url, filter_false_tracks, uri_list
from exceptions import SpotifyToolsException, SpotifyToolsUnauthorizedException

"""
Responsible for connecting and exchanging data with spotify

TODO : Decide what part of the authorization flow is on the side of the library vs the app 
Caching and sessions should be part of the app
Make the cut at the narrow point of the credentials flow stream

What does the library do - all heavy lifting of processing information and interacting with big services
What does the app do - provides graphical interface, ease of public access and authentication for interaction with the library
Local client - for downloading everything into dbs

"""
TIMEOUT_SLEEP = 30

# The authorization scope for Spotify API needed to run this app
SCOPE = "user-top-read user-read-currently-playing user-modify-playback-state playlist-read-private playlist-read-collaborative playlist-modify-private"

# TODO: Consider creating an auhorized session class as a child of the general session
def timeout_wait(func):
    """If the decorated function returns a timeout exception, wait and try again."""

    def inner(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            # TODO: SpotifyException doesn't always mean timeout
            except (requests.exceptions.ReadTimeout, spotipy.exceptions.SpotifyException) as error:
                # Take a break
                print(f"GOT TIMEOUT, WAITING ({error})")
                time.sleep(TIMEOUT_SLEEP)

    return inner


def authorized(func):
    """Raises a dedicated exception if the session is unauthorized when decorated method is called."""

    def inner(self, *args, **kwargs):
        if not self.authorized:
            raise SpotifyToolsUnauthorizedException()
        return func(self, *args, **kwargs)

    return inner


class SpotifySession:
    # TODO: Check if web app needs separate sp instances
    def __init__(self, cache_path=None):
        self.authorized = False
        self.cache_handler = CacheFileHandler(cache_path=cache_path)
        # TODO: this auth manager is not used yet, it is waiting to react when user wants to authenticate, it should be initialized at a later time though
        self.auth_manager = SpotifyOAuth(
            scope=SCOPE, cache_handler=self.cache_handler, show_dialog=True
        )
        # This initializes an unauthorized connection - only endpoints not accessing user info will work.
        self.connection: Spotify = Spotify(auth_manager=SpotifyClientCredentials())
        self.connected_user = None  # cache for currently connected user's data # TODO: Replace this with a user class instance
        self.resources = {}  # Master dictionary of all instantiated unique resources indexed by URI
        self.time_spent_parsing_details = 0
        self.missing_details_found = 0
    def remove_cache(self):
        os.remove(self.cache_handler.cache_path)

    def authorize(self, code=None):
        self.auth_manager.get_access_token(code)
        self.connection = Spotify(auth_manager=self.auth_manager)
        # TODO: get a better way of checking if the authorization was successful
        self.authorized = True

    # AUTHORIZED SCOPE
    # TODO: Add some authorize checks and exceptions for these
    # Get current user's playlists

    @authorized
    def unique_playlist_name(self, name):
        """Modifies a playlist name to make it unique in the user's library."""
        all_names = [p.name for p in self.fetch_user_playlists(self.fetch_user())]
        if name in all_names:
            i = 2  # Try adding numbers till a unique name is found starting with 2.
            while name + f" ({i})" in all_names:
                i += 1
            name += f" ({i})"
        return name

    @authorized
    @timeout_wait
    def create_playlist(self, name, tracks: List[spotify.Track] = None):
        # TODO: Longest playlist name is 100 chars, add exception handling
        """Creates a playlist in the user's library and adds supplied tracks in chunks of 100."""
        user_id = self.fetch_user().id
        name = self.unique_playlist_name(name)
        raw_playlist = self.connection.user_playlist_create(user_id, name)
        new_playlist = self.get_resource(raw_playlist)
        if tracks:
            for i in range(-(-len(tracks) // 100)):
                self._add_to_playlist(new_playlist, tracks[i * 100: (i + 1) * 100])
        return new_playlist

    @authorized
    @timeout_wait
    def _add_to_playlist(self, playlist: spotify.Playlist, tracks: List[spotify.Track]):
        """
        Adds up to a hundred tracks to a playlist.

        This is a separate function because each state-modifying request needs a separate decorator to catch a timeout.
        """
        # TODO: Add handling for invalid playlist or track parameters
        if len(tracks) > 100:
            raise SpotifyToolsException("Adding tracks to playlist limited to 100 at a time.")
        self.connection.playlist_add_items(playlist.uri, [track.uri for track in tracks])

    @authorized
    @timeout_wait
    def fetch_user_playlists(self, user: spotify.User):
        """Return all publicly visible playlists from the library of user with given id."""
        # TODO: Add handling for invalid user parameter
        results = []
        has_next = True
        i = 0
        while has_next:
            response = self.connection.user_playlists(user.id, limit=50, offset=i * 50)
            i += 1
            has_next = bool(response['next'])
            if "items" in response:
                results.extend([self.get_resource(item) for item in response["items"]])
        return results

    @authorized
    @timeout_wait
    def fetch_user(self, update=False):
        """Download, cache and return metadata about the currently logged in user."""
        # TODO: Check possible ways in which the user data might change mid-session
        if not self.connected_user or update:
            user_data = self.connection.current_user()
            self.connected_user = self.get_resource(user_data)
        return self.connected_user

    @authorized
    @timeout_wait
    def queue(self, uris):
        """Queue one or more tracks."""
        # TODO: Handling of invalid parameters on this and play
        for uri in uri_list(uris):
            self.connection.add_to_queue(uri)

    @authorized
    # Time sensitive functions don't get a timeout decorator
    def play(self, uris):
        """Starts playback of one or more tracks."""
        self.connection.start_playback(uris=uri_list(uris))

    @authorized
    def fetch_currently_playing(self):
        """Returns the track which is currently playing in the authorized account, or None if there's no playback."""
        playback = self.connection.currently_playing()
        # Spotify API doesn't return anything if there's no playback.
        if not playback:
            return None
        current_track = playback["item"]
        # TODO: Make this not skip the context (i.e. the playlist) of playback
        return self.get_resource(current_track)

    # GENERAL SCOPE
    @timeout_wait
    def search(self, query, search_type="track", limit=50):
        results = self.connection.search(q=query, type=search_type, limit=limit)
        return results[search_type + "s"]

    @timeout_wait
    def fetch_item(self, uri, raw=False):
        # TODO: Make this check if the item is already present before requesting
        # TODO: Right now providing an invalid uri causes a retry loop
        url = uri_to_url(uri)
        response = self.connection._get(url)
        return response if raw else self.get_resource(response)

    @timeout_wait
    def fetch_artist_top_tracks(self, artist, remove_duplicates=True):
        """
        Returns artist's 10 top tracks.
        """
        response = self.connection.artist_top_tracks(artist.uri)
        tracks = [self.get_resource(track) for track in response['tracks']]
        # TODO: This shouldn't be here
        if remove_duplicates:
            # Remove duplicates (tracks are sorted by popularity by default)
            tracks = helpers.remove_duplicates(tracks)
        return tracks

    @timeout_wait
    def fetch_related_artists(self, artist):
        response = self.connection.artist_related_artists(artist.uri)
        return [self.get_resource(artist) for artist in response['artists']]

    # Shorthands
    def load_children(self, items):
        return self.load_bulk(items, children=True)

    def load_features(self, items):
        return self.load_bulk(items, features=True)

    def load_details(self, items):
        return self.load_bulk(items, details=True)

    # TODO: Add a decorator for making single item arguments into a list
    def load_bulk(self, items: List[spotify.Resource], details=False, features=False, children=False):
        """
        Downloads and updates details and features for a list of resources.

        The resources can be of mixed types, but at least one request to the API has to be made for each type of item.
        Features are only available for tracks.
        There are cases where some tracks in a collection are missing their details, while others are missing features.
        """

        # TODO: Make this more elegant
        if not isinstance(items, list):
            items = [items]


        # TODO: Add cases for all types
        # TODO: Add logic for recursive loading
        # Define request limit, methods for requesting and parsing respectively for each requested resource.
        cases = {
            'features': {
                spotify.Track: (self._track_features, self._match_features, 100)
            } if features else None,
            'details': {
                spotify.Track: (self._track_details, self._match_details, 50),
                spotify.Album: (self._album_details, self._match_details, 20),
            } if details else None,
            'children': {
                spotify.Playlist: (self._playlist_tracks, self._parse_children, 100),
                spotify.Album: (self._album_tracks, self._parse_children, 50),
                spotify.Artist: (self._artist_albums, self._parse_children, 50)
            } if children else None,
        }

        fetch_methods = {
            'details': self._fetch_bulk_details,
            'features': self._fetch_bulk_details,
            'children': self._fetch_bulk_children,
        }

        # Separate the items into lists by type.
        sorted_items = {}
        for item in items:
            if type(item) not in sorted_items:
                sorted_items[type(item)] = []
            sorted_items[type(item)].append(item)

        # For each sorted list that is left, download and parse details or features.
        for c in cases:
            case = cases[c]
            if not case:
                continue
            for resource in case:
                if resource in sorted_items:
                    fetch_methods[c](sorted_items[resource], *case[resource])
        # TODO: is this return value ever used?
        return items

    @staticmethod
    def _fetch_bulk_details(items, request_method, parsing_method, limit):
        """Passes items to request_method in chunks not exceeding the limit and passes the results to parsing_method."""
        for i in range(-(-len(items) // limit)):
            chunk = items[(i * limit): (i * limit) + limit]
            response = request_method(chunk)  # Get response for each chunk.
            parsing_method(chunk, response)

    @staticmethod
    def _fetch_bulk_children(items, request_method, parsing_method, limit):
        """Calls request_method for each item until the results are complete and passes them to parsing_method."""
        for item in items:
            children = []
            offset = len(item.children)  # Compensate for children already known.
            has_next = True
            while has_next:
                response = request_method(item, offset=offset)
                offset += limit
                children.extend(response['items'])
                has_next = bool(response['next'])
            parsing_method(item, children)

    def _parse_children(self, item, children):
        # TODO: removing duplicates should be implemented early on before any sort of recursion kicks in
        children = [self.get_resource(child) for child in children]
        item.children.extend(children)
        item.children_loaded = True

    @timeout_wait
    def _track_features(self, tracks: List[spotify.Track]):
        return self.connection.audio_features([track.uri for track in tracks])

    @timeout_wait
    def _track_details(self, tracks: List[spotify.Track]):
        return self.connection.tracks([track.uri for track in tracks])['tracks']

    @timeout_wait
    def _album_details(self, albums: List[spotify.Album]):
        return self.connection.albums([album.uri for album in albums])['albums']

    @staticmethod
    def _match_details(items: List[spotify.Resource], details):
        """"""
        for i in range(len(items)):
            if details[i]:
                items[i].parse_details(details[i])
            else:
                # TODO: Replace this with logging
                # Another edge case that has never happened so far
                raise SpotifyToolsException(f"Failed to fetch details for {items[i].uri}.")

    @staticmethod
    def _match_features(tracks: List[spotify.Track], features):
        """"""
        # Unlike details, features are sometimes intentionally left blank.
        for i in range(len(tracks)):
            tracks[i].parse_features(features[i])

    @timeout_wait
    def _playlist_tracks(self, playlist, offset):
        """Download all tracks from spotify for a playlist URI."""
        response = self.connection.playlist_items(playlist.uri, offset=offset, limit=100)
        response["items"] = filter_false_tracks(response["items"])  # Remove local tracks and podcasts from the result.
        return response

    @timeout_wait
    def _artist_albums(self, artist, offset=0):
        # TODO: For now only albums are considered to save time, make this configurable
        # TODO: In very rare cases (Ray Dalton) an artist will only have singles uploaded. Make it an option to load singles if there are no albums.
        return self.connection.artist_albums(artist.uri, album_type='album', offset=offset, limit=50)
        # Notes:
        # album groups  ['album', 'single', 'compilation', 'appears_on']
        # album types  ['album', 'single', 'compilation']
        # compilation means it's the only artist, appears_on means it's a compilation with more artists
        # TODO: album_type parameter in the request above appears to actually mean the album group - test this
        # For some reason, sometimes two albums exist which are exactly the same, except for their uri.

    @timeout_wait
    def _album_tracks(self, album, offset=0):
        response = self.connection.album_tracks(album.uri, offset=offset, limit=50)
        # Album data is missing from the tracks, the album's URI is appended to link the track back to the album.
        response["items"] = filter_false_tracks(response["items"])  # Remove podcasts from the result.
        for track in response['items']:
            track['album'] = {'uri': album.uri}
        return response

        # TODO: Replace this with logging a warning
        if len(album_tracks) != album.total_tracks:
            exit(f"ALBUM TRACKS: {len(album_tracks)}, ALBUM TOTAL: {album.total_tracks}")

    # PARSING
    def get_resource(self, raw_data: Dict):
        """Return an existing resource by uri or create a new one."""
        if 'uri' not in raw_data:
            raise SpotifyToolsException(f"No URI supplied for resource: {raw_data}.")
        uri = raw_data['uri']
        # Check if the resource exists and return it if yes.
        if uri in self.resources:
            resource = self.resources[uri]
            time0 = time.time()
            # Parse the new data if it contains some missing information. # TODO: test performance on this
            # TODO isn't doing it this way more resource-intensive than just parsing the details each time?
            if resource.missing_details and any(missing in raw_data for missing in resource.missing_details):
                self.missing_details_found += 1
                resource.parse_details(raw_data)
            self.time_spent_parsing_details += time.time() - time0
            return resource
        else:
            # Create a new resource otherwise.
            resource = self._parse_resource(raw_data)
            return resource

    def _parse_resource(self, raw_data: Dict):
        """
        Recognizes the resource type from the raw data and calls the correct constructor or method.

        This should be the only way through which instances of Resource are initialized.
        """

        # Playlist
        if "type" in raw_data and raw_data["type"] == "playlist":
            return self._parse_playlist(raw_data)

        # Album
        if "type" in raw_data and raw_data["type"] == "album":
            return self._parse_album(raw_data)

        # Track
        if "type" in raw_data and raw_data["type"] == "track" or "track" in raw_data:
            return self._parse_track(raw_data)

        # User
        if "type" in raw_data and raw_data["type"] == "user":
            return spotify.User(self, raw_data=raw_data)

        # Artist
        if "type" in raw_data and raw_data["type"] == "artist":
            return spotify.Artist(self, raw_data=raw_data)

        raise SpotifyToolsException(f"Parser didn't recognize object: {raw_data}")

    def _parse_playlist(self, raw_data):
        # Parse track data that may be included with the playlist data.
        if children_data := raw_data["tracks"].pop("items", None):
            children = [self.get_resource(track) for track in filter_false_tracks(children_data)]
            children_loaded = not raw_data["tracks"]["next"]
        else:
            children = None
            children_loaded = False
        # Create the playlist.
        return spotify.Playlist(self, raw_data=raw_data, children=children, children_loaded=children_loaded)

    def _parse_album(self, raw_data):
        # Parse artist data.
        artists = [self.get_resource(artist) for artist in raw_data['artists']]
        # Create the album.
        album = spotify.Album(self, raw_data=raw_data, artists=artists)
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
        track = spotify.Track(self, raw_data=raw_data, artists=artists, album=album)
        return track
