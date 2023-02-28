import os
import sys
import itertools

import pytest
from dotenv import load_dotenv

from spotifytools import spotify
from spotifytools.spotify_session import SpotifySession
from spotifytools.exceptions import SpotifyToolsException, SpotifyToolsUnauthorizedException


class TestSpotifySession:

    @pytest.fixture
    def sp(self):
        load_dotenv()
        sp = SpotifySession()
        yield sp

    @pytest.fixture
    def featured_content(self, sp):
        """
        Get content from the featured playlists endpoint to provide data for testing.

        This content will vary for different times, locations and users.
        """
        content = {}
        raw_content = sp.connection.featured_playlists()
        content['playlists'] = [sp.factory.get_resource(item) for item in raw_content['playlists']['items']]
        content['tracks'] = content['playlists'][0].get_tracks()
        content['artists'] = list(set(itertools.chain(*[item.artists for item in content['tracks']])))
        content['albums'] = list(set([item.album for item in content['tracks']]))
        yield content

    def test_search(self, sp):
        # Setup
        query = 'test'
        limit = 10
        correct_types = {'tracks': spotify.Track,
                         'playlists': spotify.Playlist,
                         'artists': spotify.Artist,
                         'albums': spotify.Album}
        # Call
        results = sp.search(query=query, limit=limit, tracks=True, artists=True, albums=True, playlists=True)
        # Assertion
        for resource in results:
            correct_type = correct_types[resource]
            assert all(isinstance(item, correct_type) for item in results[resource])
            assert len(results[resource]) == limit

    def test_fetch_item(self, sp, featured_content):
        item = featured_content['tracks'][0]
        sp.factory._cache.pop(item.uri)
        result = sp.fetch_item(item.uri)
        assert not result.missing_details

    def test_fetch_item_duplicate(self, sp, featured_content):
        item = featured_content['tracks'][0]
        result = sp.fetch_item(item.uri)
        assert result == item

    def test_fetch_artist_top_tracks(self, sp, featured_content):
        artist = featured_content['artists'][0]
        result = sp.fetch_artist_top_tracks(artist)
        assert len(result) == len(set(result)) and len(result)
        assert all(isinstance(track, spotify.Track) for track in result)

    def test_fetch_related_artists(self, sp, featured_content):
        artist = featured_content['artists'][0]
        result = sp.fetch_related_artists(artist)
        assert len(result) == len(set(result)) and len(result)
        assert all(isinstance(artist, spotify.Artist) for artist in result)

# TODO: Test all the methods and requests are called correct number of times with monkeypatching

    def test_load_children(self, sp, featured_content):
        # Setup
        artist = featured_content['artists'][0]
        album = featured_content['albums'][0]
        playlist = featured_content['playlists'][0]
        track = featured_content['tracks'][0]
        items = [artist, album, playlist, track]
        for item in items:
            # Remove children from items
            item.children = []
            item.children_loaded = False
        # Call
        sp.load_children(items)
        # Assertions
        for item in [album, playlist, artist]:
            assert item.children_loaded
        for item in [album, playlist]:  # Artists don't have an indicator for number of children.
            assert len(item.children) == item.total_tracks

    def test_load_features(self, sp, featured_content):
        # Setup
        album = featured_content['albums'][0]
        tracks = featured_content['tracks']
        items = tracks + [album]
        for track in tracks:
            # Remove features
            track.features = None
        # Call
        sp.load_features(items)
        # Assertions
        assert all(track.features is not None for track in tracks)  # Some tracks have empty dict for features.

    def test_load_details(self, sp, featured_content):
        # Setup
        items = []
        for resource in featured_content:
            items.extend(featured_content[resource])
        # Call
        sp.load_details(items)
        # Assertions
        for item in items:
            assert not item.missing_details

"""
    def test_get_resource(self, sp, featured_content):
        assert False


    def test__parse_resource(self, sp, featured_content):
        assert False


    def test__parse_playlist(self, sp, featured_content):
        assert False


    def test__parse_album(self, sp, featured_content):
        assert False


    def test__parse_track(self, sp, featured_content):
        assert False


"""

class TestSpotifySessionAuthorized:
    """
    Tests the SpotifySession class on a live Spotify connection.

    Requires a validated connection to a real Spotify account for tests in the authorized scope.
    Will create, modify and clean up playlists, as well as play back songs, during the testing.
    To avoid endorsing any specific artist, tests are run on the user's library and public playlists created by Spotify.
    """

    @pytest.fixture
    def sp(self):
        load_dotenv()
        sp = SpotifySession()
        sp.authorize()
        if sp.authorized:
            yield sp
        else:
            raise SpotifyToolsUnauthorizedException("Failed to authorize a session for testing.")

    def test_unique_playlist_name():
        assert False


    def test_create_playlist():
        assert False


    def test__add_to_playlist():
        assert False


    def test_fetch_user_playlists():
        assert False


    def test_fetch_user():
        assert False


    def test_queue():
        assert False


    def test_play():
        assert False


    def test_fetch_currently_playing():
        assert False

