from typing import List, Dict
from spotipy import Spotify
import os
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import CacheFileHandler
import classes.spotify as spotify


import helpers
from helpers import uri_to_url, filter_false_tracks

"""
Responsible for connecting and exchanging data with spotify

TODO : Decide what part of the authorization flow is on the side of the library vs the app 
Caching and sessions should be part of the app
Make the cut at the narrow point of the credentials flow stream

What does the library do - all heavy lifting of processing information and interacting with big services
What does the app do - provides graphical interface, ease of public access and authentication for interaction with the library
Local client - for downloading everything into dbs

"""
# The authorization scope for Spotify API needed to run this app
SCOPE = "user-top-read user-read-currently-playing user-modify-playback-state playlist-read-private playlist-read-collaborative playlist-modify-private"


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

    def get_unique_name(self, name):
        all_names = [p["name"] for p in self.fetch_user_playlists()]
        if name in all_names:
            i = 2
            while name + f" ({i})" in all_names:
                i += 1
            name += f" ({i})"
        return name

    def create_playlist(self, name, tracks):
        user_id = self.fetch_user()["id"]
        name = self.get_unique_name(name)
        new_playlist = self.connection.user_playlist_create(user_id, name=name)
        self.connection.playlist_add_items(new_playlist["id"], tracks)

    def fetch_current_user_playlists(self):
        """Return all playlists from the library of currently logged in user."""
        if self.authorized:
            # TODO: Make this load all playlists instead of first 50
            result = self.connection.current_user_playlists(limit=50)
            if "items" in result:
                return [self.get_resource(item) for item in result["items"]]

    def fetch_user_playlists(self, user):
        """Return all publicly visible playlists from the library of user with given id."""
        if self.authorized:
            # TODO: Make this load all playlists instead of first 50
            result = self.connection.user_playlists(user.id, limit=50)
            if "items" in result:
                return [self.get_resource(item) for item in result["items"]]

    def fetch_user(self, force_update=False):
        if self.authorized:
            if not self.connected_user or force_update:
                user_data = self.connection.current_user()
                self.connected_user = self.get_resource(user_data)
            return self.connected_user

    def fetch_currently_playing(self):
        if self.authorized:
            playback = self.connection.currently_playing()
            if not playback:
                return None
            current_track = playback["item"]
            # TODO: Make this not skip the context (i.e. the playlist) of playback
            return self.get_resource(current_track)

    def play(self, uris, queue=False):
        if self.authorized:
            if queue:
                for uri in uris:
                    self.connection.add_to_queue(uri)
            else:
                self.connection.start_playback(uris=uris)

    # GENERAL SCOPE
    def fetch_track_details(self, tracks: List[spotify.Track]):
        """
        Downloads and updates details for a list of tracks.

        Each request can fetch up to 100 tracks, so this is more efficient to do in bulk.
        """
        result = []
        total_tracks = len(tracks)
        # Run a loop requesting a 100 tracks at a time
        for i in range(-(-total_tracks // 50)):
            chunk = tracks[(i * 50) : (i * 50) + 50]
            chunk_size = len(chunk)
            details = self.connection.tracks([track.uri for track in chunk])['tracks']
            # It's important that the input and output loaded_lists are the same length since they may be later combined entry for entry.
            if not len(details) == chunk_size:
                raise Exception("Failed to fetch track details for all tracks")
            # Pass details to each track to be parsed
            for i in range(chunk_size):
                chunk[i].parse_details(details[i])
        return tracks

    def fetch_album_details(self, albums: List[spotify.Album]):
        """
        Downloads and updates details for a list of albums.

        Each request can fetch up to 100 albums, so this is more efficient to do in bulk.
        """
        result = []
        total_albums = len(albums)
        # Run a loop requesting a 100 albums at a time
        for i in range(-(-total_albums // 20)):
            chunk = albums[(i * 20) : (i * 20) + 20]
            chunk_size = len(chunk)
            details = self.connection.albums([album.uri for album in chunk])['albums']
            # It's important that the input and output loaded_lists are the same length since they may be later combined entry for entry.
            if not len(details) == chunk_size:
                raise Exception("Failed to fetch album details for all albums")
            # Pass details to each album to be parsed
            for i in range(chunk_size):
                chunk[i].parse_details(details[i])
        return albums


    # TODO: Test that this works on a static playlist
    def fetch_track_features(self, tracks: List[spotify.Track]):
        """
        Downloads and updates audio features for a list of tracks.

        Each request can fetch up to 100 tracks, so this is more efficient to do in bulk.
        """
        result = []
        total_tracks = len(tracks)
        # Run a loop requesting a 100 tracks at a time
        for i in range(-(-total_tracks // 100)):
            chunk = tracks[(i * 100) : (i * 100) + 100]
            chunk_size = len(chunk)
            features = self.connection.audio_features([track.uri for track in chunk])
            # It's important that the input and output loaded_lists are the same length since they may be later combined entry for entry.
            if not len(features) == chunk_size:
                raise Exception("Failed to fetch track features for all tracks")
            # Pass features to each track to be parsed
            for i in range(chunk_size):
                chunk[i].parse_features(features[i])
        return tracks

    # TODO: Test that this works on a static playlist
    def fetch_playlist_tracks(self, playlist_uri, total_tracks, start=0):
        """Download all tracks from spotify for a playlist URI."""
        playlist_tracks = []
        # TODO: API reference quotes 50 as the limit for one request, but the old 100 seems to work fine - check other endpoints
        # Run a loop requesting a 100 tracks at a time
        for i in range(start // 100, -(-total_tracks // 100)):
            response = self.connection.playlist_items(
                playlist_uri, offset=(i * 100), limit=100
            )
            playlist_tracks += filter_false_tracks(
                response["items"]
            )  # remove local tracks and podcasts from the result
        return [self.get_resource(track) for track in playlist_tracks]

    # TODO: Fetch functions for different types are extremely similar
    def fetch_artist_albums(self, artist, remove_duplicates=True):
        """
        Updates artist with all albums.

        By default skips singles and compilations.
        By default removes duplicates and uses popularity to decide priority.
        """
        i = 0
        has_next = True
        albums = []
        while has_next:
            # Maximum albums for one request is 50
            response = self.connection.artist_albums(artist.uri, offset=i * 50, limit=50)
            i += 1
            for item in response['items']:
                   # album groups  ['album', 'single', 'compilation', 'appears_on']
                   # compilation means it's the only artist, appears_on means it's a compilation with more artists
                   # album types  ['album', 'single', 'compilation']
                if item['album_group'] != 'appears_on' and item['album_group'] != item['album_type']:
                    helpers.show_dict(item)
                    exit()
                if item['album_group'] not in ['album', 'single', 'compilation', 'appears_on']:
                    helpers.show_dict(item)
                    exit()
                if item['album_type'] not in ['album', 'single', 'compilation']:
                    helpers.show_dict(item)
                    exit()
                # TODO: For now only albums are considered save time, make this configurable
                if item['album_type'] in ['album'] and item['album_group'] == item['album_type']:
                    albums.append(self.get_resource(item))
            has_next = bool(response['next'])
        # TODO: For now do the sorting here, later add options to manipulate the sorting (appears to have little effect)
        # For some reason, sometimes two albums exist which are exactly the same, except for their uri.
        if remove_duplicates:
            # Get complete album details to apply a custom sorting
            self.fetch_album_details(albums)
            # Sort albums by popularity
            albums = sorted(albums, key=lambda album: album.popularity, reverse=True)
            # Remove duplicates
            albums = helpers.remove_duplicates(albums)
        artist.children = albums

    # TODO: This function proves it's better to use whole objects as arguments instead of just URIs
    def fetch_album_tracks(self, album):
        album_tracks = []
        # Maximum tracks for one request is 50
        for i in range(0, -(-album.total_tracks // 50)):
            response = self.connection.album_tracks(album.uri, offset=(i*50), limit=50)
            for item in response['items']:
                item['album'] = {'uri': album.uri}  # Album URI is appended to link the track back to the album.
                album_tracks.append(self.get_resource(item))
        if len(album_tracks) != album.total_tracks:
            exit(f"ALBUM TRACKS: {len(album_tracks)}, ALBUM TOTAL: {album.total_tracks}")
        album.children = album_tracks

    def search(self, query, search_type):
        results = self.connection.search(q=query, type=search_type, limit=50)
        return results[search_type + "s"]

    def fetch_raw_item(self, uri):
        url = uri_to_url(uri)
        return self.connection._get(url)

    def fetch_item(self, uri):
        url = uri_to_url(uri)
        return self.get_resource(self.connection._get(url))

    def get_resource(self, raw_data: Dict):
        """Return an existing resource by uri or create a new one."""
        uri = raw_data['uri']

        # TODO: In some cases the incoming raw_data can contain new information which currently would be ignored

        if uri in self.resources:
            resource = self.resources[uri]
            # Parse the new data if it contains some missing information. # TODO: test this
            if any(missing in raw_data for missing in resource.missing_detail_keys()):
                resource.parse_details(raw_data)
            return resource

        resource = self.parse_resource(raw_data)
        self.resources[uri] = resource
        return resource

    def parse_resource(self, raw_data: Dict):
        """This should be the only method through which instances of Resource are initialized."""
        if "type" in raw_data and raw_data["type"] == "playlist":
            # Parse track data that may be included with the playlist data
            # TODO: This assumes that 'items' is always present in response objects of type 'playlist', make sure this is true
            children_data = raw_data["tracks"].pop("items", None)
            children = (
                [self.get_resource(child) for child in filter_false_tracks(children_data)]
                if children_data
                else None
            )
            return spotify.Playlist(self, raw_data=raw_data, children=children)

        if "type" in raw_data and raw_data["type"] == "user":
            return spotify.User(self, raw_data=raw_data)

        if "type" in raw_data and raw_data["type"] == "album":
            artists = [self.get_resource(artist) for artist in raw_data['artists']]
            return spotify.Album(self, raw_data, artists)

        if "type" in raw_data and raw_data["type"] == "artist":
            return spotify.Artist(self, raw_data=raw_data)

        elif "type" in raw_data and raw_data["type"] == "track" or "track" in raw_data:
            # TODO: Album and artist data acquired through track is not complete. Making two more requests for each track tanks the performance.
            album = self.get_resource(raw_data['album'])
            artists = [self.get_resource(artist) for artist in raw_data['artists']]
            track = spotify.Track(self, raw_data, artists=artists, album=album)
            # TODO: Does adding incomplete tracks to an album help anything right now?
            album.children.append(track)
            return track

        else:
            raise Exception("Parser didn't recognize object")
