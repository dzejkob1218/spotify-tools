import time
from typing import List, Dict, Union

import requests.exceptions
from spotipy import Spotify
import os
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import CacheFileHandler

import spotifytools.spotify as spotify
from spotifytools.resource_factory import ResourceFactory
from spotifytools.helpers import uri_to_url, filter_false_tracks, uri_list, remove_duplicates
from spotifytools.exceptions import SpotifyToolsException, SpotifyToolsUnauthorizedException

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
            except (requests.exceptions.ReadTimeout) as error:
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
        """ Initializes an unauthorized connection - only endpoints not accessing user info will work."""
        self.authorized = False
        self.cache_handler = CacheFileHandler(cache_path=cache_path)
        self.connection: Spotify = Spotify(auth_manager=SpotifyClientCredentials())
        self.factory = ResourceFactory(self)  # TODO: Experiment with shared factories for sessions.
        self.connected_user = None  # Cache for currently connected user's data.
        self.resources = {}  # Master dictionary of all instantiated unique resources indexed by URI

    def remove_cache(self):
        os.remove(self.cache_handler.cache_path)

    def authorize(self, code=None):
        auth_manager = SpotifyOAuth(scope=SCOPE, cache_handler=self.cache_handler, show_dialog=True)
        auth_manager.get_access_token(code)
        self.connection = Spotify(auth_manager=auth_manager)
        # TODO: Check if timeouts can be handled by spotipy
        # self.connection.requests_timeout = 30
        self.authorized = True

    # AUTHORIZED SCOPE
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
        """Creates a playlist in the user's library and adds supplied tracks in batches of 100."""
        user_id = self.fetch_user().id
        name = self.unique_playlist_name(name)
        raw_playlist = self.connection.user_playlist_create(user_id, name)
        new_playlist = self.factory.get_resource(raw_playlist)
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
                results.extend([self.factory.get_resource(item) for item in response["items"]])
        return results

    @authorized
    @timeout_wait
    def fetch_user(self, update=False):
        """Download, cache and return metadata about the currently logged in user."""
        # TODO: Check possible ways in which the user data might change mid-session
        if not self.connected_user or update:
            user_data = self.connection.current_user()
            self.connected_user = self.factory.get_resource(user_data)
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
        return self.factory.get_resource(current_track)

    # GENERAL SCOPE
    @timeout_wait
    def search(self, query, limit=50, tracks=False, artists=False, playlists=False, albums=False):
        search_types = [('track', tracks), ('artist', artists), ('playlist', playlists), ('album', albums)]
        search_type = ",".join(k for k, v in search_types if v)
        results = self.connection.search(q=query, limit=limit, type=search_type)
        for resource in results:
            results[resource] = [self.factory.get_resource(data) for data in results[resource]['items']]
        return results

    @timeout_wait
    def fetch_item(self, uri, raw=False):
        # TODO: Make this check if the item is already present before requesting
        # TODO: Right now providing an invalid uri causes a retry loop
        url = uri_to_url(uri)
        response = self.connection._get(url)
        return response if raw else self.factory.get_resource(response)

    @timeout_wait
    def fetch_artist_top_tracks(self, artist, keep_duplicates=False):
        """
        Returns artist's 10 top tracks.
        """
        response = self.connection.artist_top_tracks(artist.uri)
        tracks = [self.factory.get_resource(track) for track in response['tracks']]
        # TODO: This shouldn't be here
        if not keep_duplicates:
            # Remove duplicates (tracks are sorted by popularity by default)
            tracks = remove_duplicates(tracks)
        return tracks

    @timeout_wait
    def fetch_related_artists(self, artist):
        response = self.connection.artist_related_artists(artist.uri)
        return [self.factory.get_resource(artist) for artist in response['artists']]

    # Shorthands
    def load_children(self, items):
        return self.load(items, children=True)

    def load_features(self, items):
        return self.load(items, features=True)

    def load_details(self, items):
        return self.load(items, details=True)

    # TODO: Add a decorator for making single item arguments into a list
    def load(self, items: List[spotify.Resource], details=False, features=False, children=False):
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
                spotify.Track: (self._track_features, self._match_features, 100),
            } if features else None,
            'details': {
                spotify.Track: (self._track_details, self._match_details, 50),
                spotify.Album: (self._album_details, self._match_details, 20),
                spotify.Artist: (self._artist_details, self._match_details, 50),
                spotify.Playlist: (self._playlist_details, self._match_details, 1),
            } if details else None,
            'children': {
                spotify.Playlist: (self._playlist_tracks, self._parse_children, 100),
                spotify.Album: (self._album_tracks, self._parse_children, 50),
                spotify.Artist: (self._artist_albums, self._parse_children, 50),
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

        # TODO: Add logic that separates items into lists based on their missing features (f.e. only load children if children are missing) so other parts of the program don't have to do checks

        # For each sorted list that is left, download and parse details or features.
        for c in cases:
            case = cases[c]
            if not case:  # Only proceed if the corresponding parameter is true.
                continue
            for resource in case:
                if resource in sorted_items:
                    fetch_methods[c](sorted_items[resource], *case[resource])
        # TODO: is this return value ever used?
        return items

    @staticmethod
    def _fetch_bulk_details(items, request_method, parsing_method, limit):
        """Passes items to request_method in batches not exceeding the limit and passes the results to parsing_method."""
        for i in range(-(-len(items) // limit)):
            batch = items[(i * limit): (i * limit) + limit]
            response = request_method(batch)  # Get response for each batch.
            parsing_method(batch, response)

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
        children = [self.factory.get_resource(child) for child in children]
        item.children.extend(children)
        item.children_loaded = True

    @timeout_wait
    def _track_features(self, tracks: List[spotify.Track]):
        return self.connection.audio_features([track.uri for track in tracks])

    @timeout_wait
    def _artist_details(self, artists: List[spotify.Artist]):
        return self.connection.artists([artist.uri for artist in artists])['artists']

    @timeout_wait
    def _track_details(self, tracks: List[spotify.Track]):
        return self.connection.tracks([track.uri for track in tracks])['tracks']

    @timeout_wait
    def _playlist_details(self, playlist: List[spotify.Playlist]):
        return [self.connection.playlist(playlist[0].uri)]

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
