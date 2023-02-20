import os
import sys
# Workaround to import classes properly
import unittest.mock

import helpers

test_path = os.path.dirname(os.path.abspath(__file__))
new_path = test_path.rsplit("/", 1)[0]
sys.path.insert(0, new_path)

import pytest
from unittest.mock import Mock, MagicMock
import httpretty
from dotenv import load_dotenv

from classes.spotify_session import SpotifySession
from exceptions import SpotifyToolsException, SpotifyToolsUnauthorizedException


# TODO: Once getting a random playlist is a feature, use it to test any possible input

class TestSpotifySession:
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


    def test_remove_cache():
        assert False


    def test_authorize():
        assert False


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


    def test_search():
        assert False


    def test_fetch_item():
        assert False


    def test_fetch_artist_top_tracks():
        assert False


    def test_fetch_related_artists():
        assert False


    def test_load_children():
        assert False


    def test_load_features():
        assert False


    def test_load_details():
        assert False


    def test_load_bulk():
        assert False


    def test__fetch_bulk_details():
        assert False


    def test__fetch_bulk_children():
        assert False


    def test__parse_children():
        assert False


    def test__track_features():
        assert False


    def test__track_details():
        assert False


    def test__album_details():
        assert False


    def test__match_details():
        assert False


    def test__match_features():
        assert False


    def test__playlist_tracks():
        assert False


    def test__artist_albums():
        assert False


    def test__album_tracks():
        assert False


    def test_get_resource():
        assert False


    def test__parse_resource():
        assert False


    def test__parse_playlist():
        assert False


    def test__parse_album():
        assert False


    def test__parse_track():
        assert False
