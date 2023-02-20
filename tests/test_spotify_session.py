import itertools
import os
import sys
# Workaround to import classes properly
import unittest.mock
from unittest.mock import call
import helpers
from helpers import filter_false_tracks

test_path = os.path.dirname(os.path.abspath(__file__))
new_path = test_path.rsplit("/", 1)[0]
sys.path.insert(0, new_path)

import pytest
from unittest.mock import Mock, MagicMock
from unittest.mock import patch
from dotenv import load_dotenv
from classes import spotify
from classes.spotify_session import SpotifySession
from exceptions import SpotifyToolsException, SpotifyToolsUnauthorizedException

# TODO: Once getting a random playlist is a feature, use it to test any possible input

# Dictionaries of collection and track id's used for testing
PLAYLISTS = {
    "basic_test": "spotify:playlist:0qaWhFRLG86FcXqw47FDtQ",  # small, basic playlist, owned by me (dzejkob1218)
    "edge_test": "411NWDp9tPPcPgt5afBf5x",
    # long playlist, no set image, no description, includes podcasts (also by me)
    "empty_test": "3kPfB9mIkckYOPNxDgie2Q",  # empty playlist
    "running": "37i9dQZF1DWZUTt0fNaCPB",  # spotify's 'running to rock' playlist
}


class TestSpotifySession:
    """
    Tests the central SpotifySession class in isolation and offline.

    To test for actual compatibility with Spotify API and spotipy library run tests in 'live' directory.
    """

    @pytest.fixture
    def sp(self):
        load_dotenv()
        sp = SpotifySession()
        sp.connection = Mock()
        sp.authorized = True
        yield sp
        # sp.remove_cache()

    # def test_fetch_item_failure(self, sp):
    #    """Assert exceptions are handled."""
    #    # TODO: Right now providing an invalid uri causes a retry loop

    # def test_authorize():
    #    assert False

    def test_unique_playlist_name(self, sp):
        """Assert a duplicate name is appended with the smallest available index."""
        # Setup
        mock_playlists = [Mock(), Mock()]
        mock_playlists[0].name = 'Mock Playlist'
        mock_playlists[1].name = 'Mock Playlist (2)'
        sp.fetch_user = Mock()
        sp.fetch_user_playlists = Mock(return_value=mock_playlists)
        # Call and Assert
        assert sp.unique_playlist_name('Mock Playlist') == 'Mock Playlist (3)'

    def test_create_playlist(self, sp):
        """Assert the method calls playlist creation and track adding methods with correct parameters."""
        # Setup
        mock_user = Mock()
        mock_user.id = "Mock User"
        sp.fetch_user = Mock(return_value=mock_user)
        sp.unique_playlist_name = Mock(return_value="Mock Playlist (2)")
        sp._add_to_playlist = Mock()
        sp.get_resource = Mock()
        # Call
        sp.create_playlist("Mock Playlist", [Mock() for i in range(201)])
        # Assertions
        assert sp.connection.method_calls == [call.user_playlist_create("Mock User", "Mock Playlist (2)")]
        assert sp._add_to_playlist.call_count == 3  # 3 requests limited to 100 for a list of 201 tracks.

    def test__add_to_playlist(self, sp):
        """Assert passing up to 100 tracks calls the correct method."""
        # Setup
        mock_tracks = [MagicMock(uri=i) for i in range(100)]
        mock_playlist = MagicMock(uri='Mock Playlist')
        # Call
        sp._add_to_playlist(mock_playlist, mock_tracks)
        # Assert
        expected_call = [unittest.mock.call.playlist_add_items("Mock Playlist", [t.uri for t in mock_tracks])]
        assert sp.connection.method_calls == expected_call

    def test__add_to_playlist_exception(self, sp):
        """Assert passing more than 100 tracks raises an exception."""
        with pytest.raises(SpotifyToolsException):
            sp._add_to_playlist('Mock URI', [None for i in range(101)])

    def test_fetch_user_playlists(self, sp):
        """Assert that the function makes requests until the downloaded resources are complete and parses them."""
        # Setup
        sp.connection.user_playlists = Mock(side_effect=[{'next': True, 'items': ['Mock Item']}, {'next': False}])
        sp.get_resource = Mock(return_value='Parsed Item')
        # Call and Assertions
        assert sp.fetch_user_playlists(Mock(id='1')) == ['Parsed Item']
        assert len(sp.connection.user_playlists.mock_calls) == 2
        sp.get_resource.assert_called_once_with('Mock Item')

    def test_fetch_user(self, sp):
        """Assert the function caches the result and only updates when specified."""
        # Setup
        sp.connection.current_user = Mock(side_effect='Current User')
        sp.get_resource = Mock(side_effect=['Parsed User', 'Parsed Updated User'])

        # Calls and Assertions
        assert sp.fetch_user() == 'Parsed User'
        assert sp.fetch_user() == 'Parsed User'  # call a second time to test caching
        assert sp.connected_user == 'Parsed User'
        assert len(sp.connection.current_user.mock_calls) == 1

        assert sp.fetch_user(update=True) == 'Parsed Updated User'
        assert sp.connected_user == 'Parsed Updated User'
        assert len(sp.connection.current_user.mock_calls) == 2

        # Cleanup
        # TODO: Test if this is needed
        sp.connected_user = None

    def test_fetch_user_unauthorized(self):
        """Test the @authorized decorator by attempting to get the user of an unauthorized session."""
        # TODO: Waiting for authorization functionality to be fully implemented
        sp = SpotifySession("")
        with pytest.raises(SpotifyToolsUnauthorizedException):
            sp.fetch_user()

    @pytest.fixture()
    def load_bulk_setup(self, sp):
        # Setup
        mock_tracks = [spotify.Track(sp, {'uri': f'Mock Track {i}'}, None, None) for i in range(51)]
        mock_albums = [spotify.Album(sp, {'uri': f"Mock Album {i}", 'name': f"Mock Album {i}"}, None) for i in range(2)]
        mock_artist = spotify.Artist(sp, {'uri': "Mock Artist", 'name': "Mock Artist"})
        mock_playlist = spotify.Playlist(sp, {'uri': f"Mock Playlist", 'name': f"Mock Playlist"})
        mock_items = mock_tracks + [mock_playlist, mock_artist] + mock_albums
        sp._fetch_bulk_details = Mock()
        sp._fetch_bulk_children = Mock()
        yield sp, mock_items

    def test_load_bulk(self, load_bulk_setup):
        sp, mock_items = load_bulk_setup
        parameters = (True, False)
        # Call the method with each possible combination of bool parameters.
        for p in list(itertools.product(*(parameters,) * 3)):
            sp.load_bulk(mock_items, *p)
            # Assert each method is called once for each type of resource if requested.
            assert sp._fetch_bulk_details.call_count == (2 if p[0] else 0) + (1 if p[1] else 0)
            assert sp._fetch_bulk_children.call_count == (3 if p[2] else 0)
            sp._fetch_bulk_details.reset_mock()
            sp._fetch_bulk_children.reset_mock()

    def test_load_bulk_empty(self, load_bulk_setup):
        """Test that load bulk doesn't have effect when called without parameters."""
        # Setup
        sp, mock_items = load_bulk_setup
        # Calls
        sp.load_bulk([], details=True, features=True, children=True)
        sp.load_bulk(mock_items)
        # Assertions
        assert sp._fetch_bulk_details.call_count == 0
        assert sp._fetch_bulk_children.call_count == 0

    def test_load_children(self, sp):
        # Setup
        mock_album = spotify.Album(sp, {'uri': "Mock Artist", 'name': "Mock Artist"}, artists=Mock())
        mock_artist = spotify.Artist(sp, {'uri': "Mock Artist", 'name': "Mock Artist"})
        mock_playlist = spotify.Playlist(sp, {'uri': "Mock Playlist", 'name': "Mock Playlist"})
        sp._fetch_bulk_children = Mock()
        # Call
        sp.load_children([mock_album, mock_artist, mock_playlist])
        # Assertions
        assert call([mock_artist], sp._artist_albums, sp._parse_children, 50) in sp._fetch_bulk_children.mock_calls
        assert call([mock_album], sp._album_tracks, sp._parse_children, 50) in sp._fetch_bulk_children.mock_calls
        assert call([mock_playlist], sp._playlist_tracks, sp._parse_children, 100) in sp._fetch_bulk_children.mock_calls

    def test_load_features(self, sp):
        # Setup
        mock_track = spotify.Track(sp, {'uri': "Mock Track"}, artists=Mock(), album=Mock())
        sp._fetch_bulk_details = Mock()
        # Call
        sp.load_features(mock_track)
        # Assertion
        sp._fetch_bulk_details.assert_called_once_with([mock_track], sp._track_features, sp._match_features, 100)

    def test_load_details(self, sp):
        # Setup
        mock_album = spotify.Album(sp, {'uri': "Mock Artist", 'name': "Mock Artist"}, artists=Mock())
        mock_track = spotify.Track(sp, {'uri': "Mock Track"}, artists=Mock(), album=Mock())
        sp._fetch_bulk_details = Mock()
        # Call
        sp.load_details([mock_album, mock_track])
        # Assertions
        assert call([mock_track], sp._track_details, sp._match_details, 50) in sp._fetch_bulk_details.mock_calls
        assert call([mock_album], sp._album_details, sp._match_details, 20) in sp._fetch_bulk_details.mock_calls

    def test__fetch_bulk_details(self, sp):
        # Setup
        mock_response = Mock()
        request_method = Mock(return_value=mock_response)
        parsing_method = Mock()
        items = [Mock() for i in range(11)]
        # Call
        sp._fetch_bulk_details(items, request_method, parsing_method, 10)
        # Assertions
        assert request_method.call_count == 2
        assert parsing_method.call_count == 2
        assert parsing_method.mock_calls == [call(items[:10], mock_response), call(items[10:], mock_response)]

    def test__fetch_bulk_children(self, sp):
        # Setup
        mock_children = Mock()
        mock_responses = [{'next': True, 'items': [mock_children]}, {'next': False, 'items': [mock_children]}]
        request_method = Mock(side_effect=mock_responses)
        parsing_method = Mock()
        mock_item = Mock()
        mock_item.children = [Mock() for i in range(3)]
        # Call
        sp._fetch_bulk_children([mock_item], request_method, parsing_method, 5)
        # Assertions
        assert request_method.mock_calls == [call(mock_item, offset=3), call(mock_item, offset=8)]
        parsing_method.assert_called_once_with(mock_item, [mock_children, ] * 2)

    def test_get_resource(self, sp):
        # Setup
        mock_data = {'uri': "Mock URI"}
        sp._parse_resource = Mock()
        # Call
        sp.get_resource(mock_data)
        # Assertion
        assert sp._parse_resource.mock_calls == [call(mock_data)]

    def test_get_resource_missing_data(self, sp):
        # Setup
        mock_data = {'uri': "Mock URI", 'missing': 'data', 'not missing': 'data'}
        mock_resource = spotify.Resource(sp, raw_data={'uri': "Mock URI"})
        mock_resource.missing_details = ['missing']
        mock_resource.parse_details = Mock()
        sp.resources = {"Mock URI": mock_resource}
        # Call
        sp.get_resource(mock_data)
        assert mock_resource.parse_details.mock_calls == [call(mock_data)]

    def test_get_resource_duplicate(self, sp):
        # Setup
        mock_data = {'uri': "Mock URI", 'not missing': 'data'}
        mock_resource = spotify.Resource(sp, raw_data={'uri': "Mock URI"})
        mock_resource.missing_details = ['missing']
        mock_resource.parse_details = Mock()
        sp._parse_resource = Mock()
        sp.resources = {"Mock URI": mock_resource}
        # Call
        sp.get_resource(mock_data)
        # Assertions
        assert not mock_resource.parse_details.mock_calls
        assert not sp._parse_resource.mock_calls

    def test_get_resource_invalid(self, sp):
        # Setup
        mock_data = {'data': 'data'}
        # Call and Exception
        with pytest.raises(SpotifyToolsException):
            sp.get_resource(mock_data)

    @patch('classes.spotify_session.filter_false_tracks')
    @patch('classes.spotify_session.spotify.Playlist')
    def test__parse_playlist(self, mock_playlist, mock_filter_false_tracks, sp):
        # Setup
        mock_child_data = Mock()
        mock_child = Mock()
        mock_data = {
            'type': 'playlist',
            'tracks': {
                'items': [Mock()],
                'next': True
            }
        }
        sp.get_resource = Mock(return_value=mock_child)
        mock_filter_false_tracks.return_value = [mock_child_data]
        # Call
        sp._parse_resource(mock_data)
        # Assertions
        sp.get_resource.assert_called_once_with(mock_child_data)
        assert mock_playlist.mock_calls[0] == call(sp, raw_data=mock_data, children=[mock_child], children_loaded=False)

    @patch('classes.spotify_session.filter_false_tracks')
    @patch('classes.spotify_session.spotify.Album')
    def test__parse_album(self, mock_album, mock_filter_false_tracks, sp):
        # Setup
        mock_album_uri = Mock()
        mock_artist_data = Mock()
        mock_child_data = {}
        mock_resource = Mock()
        mock_data = {
            'type': 'album',
            'uri': mock_album_uri,
            'artists': [mock_artist_data],
            'tracks': {
                'items': [Mock()],
                'next': False
            }
        }
        sp.get_resource = Mock(return_value=mock_resource)
        mock_filter_false_tracks.return_value = [mock_child_data]
        # Call
        album = sp._parse_resource(mock_data)
        # Assertions
        assert call(mock_child_data) in sp.get_resource.mock_calls
        assert call(mock_artist_data) in sp.get_resource.mock_calls
        assert mock_album.mock_calls[0] == call(sp, raw_data=mock_data, artists=[mock_resource])
        assert 'album' in mock_child_data and mock_child_data['album']['uri'] == mock_album_uri
        assert mock_resource in album.children
        assert album.children_loaded

    @patch('classes.spotify_session.spotify.Track')
    def test__parse_track(self, mock_track, sp):
        # Setup
        mock_artist_data = Mock()
        mock_album_data = Mock()
        mock_resource = Mock()
        mock_data = {
            'type': 'track',
            'album': mock_album_data,
            'artists': [mock_artist_data],
        }
        sp.get_resource = Mock(return_value=mock_resource)
        # Call
        sp._parse_resource(mock_data)
        # Assertions
        assert call(mock_artist_data) in sp.get_resource.mock_calls
        assert call(mock_album_data) in sp.get_resource.mock_calls
        assert mock_track.mock_calls[0] == call(sp, raw_data=mock_data, artists=[mock_resource], album=mock_resource)


def test_timeout_wait(self, sp):
    assert False
