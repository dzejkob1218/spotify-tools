import itertools
# Workaround to import classes properly
import pytest
import unittest.mock
from unittest.mock import Mock, MagicMock, call
from dotenv import load_dotenv

from spotifytools import spotify
from spotifytools.spotify_session import SpotifySession
from spotifytools.exceptions import SpotifyToolsException, SpotifyToolsUnauthorizedException


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

    # def test_fetch_item_failure(self, sp):
    #    """Assert exceptions are handled."""
    #    # TODO: Right now providing an invalid uri causes a retry loop

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
        sp.factory.get_resource = Mock()
        # Call
        sp.create_playlist("Mock Playlist", [Mock() for i in range(201)])
        # Assertions
        assert sp.connection.method_calls == [call.user_playlist_create(mock_user.id, "Mock Playlist (2)")]
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
            sp._add_to_playlist(Mock(), [Mock() for i in range(101)])

    def test_fetch_user_playlists(self, sp):
        """Assert that the function makes requests until the downloaded resources are complete and parses them."""
        # Setup
        raw_item = Mock()
        parsed_item = Mock()
        sp.connection.user_playlists = Mock(side_effect=[{'next': True, 'items': [raw_item]}, {'next': False}])
        sp.factory.get_resource = Mock(return_value=parsed_item)
        # Call and Assertions
        assert sp.fetch_user_playlists(Mock(id='1')) == [parsed_item]
        assert len(sp.connection.user_playlists.mock_calls) == 2
        sp.factory.get_resource.assert_called_once_with(raw_item)

    def test_fetch_user(self, sp):
        """Assert the function caches the result and only updates when specified."""
        # Setup
        parsed_user = Mock()
        parsed_updated_user = Mock()
        sp.connection.current_user = Mock()
        sp.factory.get_resource = Mock(side_effect=[parsed_user, parsed_updated_user])

        # Calls and Assertions
        assert sp.fetch_user() == parsed_user
        assert sp.fetch_user() == parsed_user  # call a second time to test caching
        assert sp.connected_user == parsed_user
        assert len(sp.connection.current_user.mock_calls) == 1

        assert sp.fetch_user(update=True) == parsed_updated_user
        assert sp.connected_user == parsed_updated_user
        assert len(sp.connection.current_user.mock_calls) == 2

    def test_fetch_user_unauthorized(self):
        """Test the @authorized decorator by attempting to get the user of an unauthorized session."""
        load_dotenv()
        sp = SpotifySession("")
        with pytest.raises(SpotifyToolsUnauthorizedException):
            sp.fetch_user()

    def test_search(self, sp):
        parsed_resource = Mock()
        sp.connection.search = Mock(return_value={'resources': {'items': [Mock()]}})
        sp.factory.get_resource = Mock(return_value=parsed_resource)
        result = sp.search(query='test', search_type='track,artist,playlist', limit=10)
        assert call(q='test', limit=10, type='track,artist,playlist') in sp.connection.search.mock_calls
        assert parsed_resource in result['resource']

    @pytest.fixture()
    def load_bulk_setup(self, sp):
        # Setup
        mock_tracks = [spotify.Track(sp, {'uri': f'Mock Track {i}'}, None, None) for i in range(51)]
        mock_albums = [spotify.Album(sp, {'uri': f"Mock Album {i}", 'name': f"Mock Album {i}"}, None) for i in range(2)]
        mock_artist = spotify.Artist(sp, {'uri': "Mock Artist", 'name': "Mock Artist"})
        mock_playlist = spotify.Playlist(sp, {'uri': f"Mock Playlist", 'name': f"Mock Playlist"}, None)
        mock_items = mock_tracks + [mock_playlist, mock_artist] + mock_albums
        sp._fetch_bulk_details = Mock()
        sp._fetch_bulk_children = Mock()
        yield sp, mock_items

    def test_load_bulk(self, load_bulk_setup):
        sp, mock_items = load_bulk_setup
        parameters = (True, False)
        # Call the method with each possible combination of bool parameters.
        for p in list(itertools.product(*(parameters,) * 3)):
            sp.load(mock_items, *p)
            # Assert each method is called once for each type of resource if requested.
            assert sp._fetch_bulk_details.call_count == (4 if p[0] else 0) + (1 if p[1] else 0)
            assert sp._fetch_bulk_children.call_count == (3 if p[2] else 0)
            sp._fetch_bulk_details.reset_mock()
            sp._fetch_bulk_children.reset_mock()

    def test_load_bulk_empty(self, load_bulk_setup):
        """Test that load bulk doesn't have effect when called without parameters."""
        # Setup
        sp, mock_items = load_bulk_setup
        # Calls
        sp.load([], details=True, features=True, children=True)
        sp.load(mock_items)
        # Assertions
        assert sp._fetch_bulk_details.call_count == 0
        assert sp._fetch_bulk_children.call_count == 0

    def test_load_children(self, sp):
        # Setup
        mock_user = spotify.User(sp, {'uri': "Mock User", 'name': "Mock User"})
        mock_artist = spotify.Artist(sp, {'uri': "Mock Artist", 'name': "Mock Artist"})
        mock_album = spotify.Album(sp, {'uri': "Mock Artist", 'name': "Mock Artist"}, artists=[mock_artist])
        mock_playlist = spotify.Playlist(sp, {'uri': "Mock Playlist", 'name': "Mock Playlist"}, owner=mock_user)
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




def test_timeout_wait(self, sp):
    assert False
