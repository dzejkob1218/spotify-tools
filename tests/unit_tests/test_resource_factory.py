import pytest
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch
from dotenv import load_dotenv

from spotifytools import spotify
from spotifytools.exceptions import SpotifyToolsException, SpotifyToolsUnauthorizedException
from spotifytools.resource_factory import ResourceFactory
from spotifytools.spotify_session import SpotifySession


class TestResourceFactory:

    @pytest.fixture
    def factory(self):
        load_dotenv()
        sp = SpotifySession()
        sp.connection = Mock()
        yield ResourceFactory(sp)

    def test_get_resource(self, factory):
        # Setup
        mock_data = {'uri': "Mock URI"}
        factory._parse_resource = Mock()
        # Call
        factory.get_resource(mock_data)
        # Assertion
        assert factory._parse_resource.mock_calls == [call(mock_data)]

    def test_get_resource_missing_data(self, factory):
        """Assert a cached resource is updated with new data when available."""
        # Setup
        mock_uri = Mock()
        mock_data = {'uri': mock_uri, 'missing': 'data', 'not missing': 'data'}
        mock_resource = spotify.Resource(factory, raw_data={'uri': mock_uri, 'not missing': 'data'})
        mock_resource.parse_details = Mock()
        factory._parse_resource = Mock()
        factory.cache = {mock_uri: mock_resource}
        # Call
        factory.get_resource(mock_data)
        assert mock_resource.parse_details.mock_calls == [call({'missing': 'data'})]
        assert not factory._parse_resource.mock_calls

    def test_get_resource_duplicate(self, factory):
        """Assert a new resource is not created when an resource of the same URI is available in the cache."""
        # Setup
        mock_uri = Mock()
        mock_data = {'uri': mock_uri, 'not missing': 'data'}
        mock_resource = spotify.Resource(factory, raw_data={'uri': mock_uri, 'not missing': 'data'})
        mock_resource.parse_details = Mock()
        factory._parse_resource = Mock()
        factory.cache = {mock_uri: mock_resource}
        # Call
        factory.get_resource(mock_data)
        # Assertions
        assert not mock_resource.parse_details.mock_calls
        assert not factory._parse_resource.mock_calls

    def test_get_resource_invalid(self, factory):
        # Setup
        mock_data = {'data': 'data'}
        # Call and Exception
        with pytest.raises(SpotifyToolsException):
            factory.get_resource(mock_data)


    @patch('spotifytools.resource_factory.filter_false_tracks')
    @patch('spotifytools.resource_factory.spotify.Playlist')
    def test__parse_playlist(self, mock_playlist, mock_filter_false_tracks, factory):
        # Setup
        mock_child_data = Mock()
        mock_owner_data = Mock()
        mock_resource = Mock()
        mock_data = {
            'type': 'playlist',
            'owner_data': mock_owner_data,
            'tracks_data': {
                'items': [Mock()],
                'next': True
            }
        }
        factory.get_resource = Mock(return_value=mock_resource)
        mock_filter_false_tracks.return_value = [mock_child_data]
        # Call
        factory._parse_resource(mock_data)
        # Assertions
        assert factory.get_resource.mock_calls == [call(mock_owner_data), call(mock_child_data)]
        assert mock_playlist.mock_calls[0] == call(factory.sp, raw_data=mock_data, owner=mock_resource, children=[mock_resource],
                                                   children_loaded=False)


    @patch('spotifytools.resource_factory.filter_false_tracks')
    @patch('spotifytools.resource_factory.spotify.Album')
    def test__parse_album(self, mock_album, mock_filter_false_tracks, factory):
        # Setup
        mock_album_uri = Mock()
        mock_artist_data = Mock()
        mock_child_data = {}
        mock_resource = Mock()
        mock_data = {
            'type': 'album',
            'uri': mock_album_uri,
            'artists_data': [mock_artist_data],
            'tracks_data': {
                'items': [Mock()],
                'next': False
            }
        }
        factory.get_resource = Mock(return_value=mock_resource)
        mock_filter_false_tracks.return_value = [mock_child_data]
        # Call
        album = factory._parse_resource(mock_data)
        # Assertions
        assert call(mock_child_data) in factory.get_resource.mock_calls
        assert call(mock_artist_data) in factory.get_resource.mock_calls
        assert mock_album.mock_calls[0] == call(factory.sp, raw_data=mock_data, artists=[mock_resource])
        assert 'album_data' in mock_child_data and mock_child_data['album_data']['uri'] == mock_album_uri
        assert mock_resource in album.children
        assert album.children_loaded

    @patch('spotifytools.resource_factory.spotify.Track')
    def test__parse_track(self, mock_track, factory):
        # Setup
        mock_artist_data = Mock()
        mock_album_data = Mock()
        mock_resource = Mock()
        mock_data = {
            'type': 'track',
            'album_data': mock_album_data,
            'artists_data': [mock_artist_data],
        }
        factory.get_resource = Mock(return_value=mock_resource)
        # Call
        factory._parse_resource(mock_data)
        # Assertions
        assert call(mock_artist_data) in factory.get_resource.mock_calls
        assert call(mock_album_data) in factory.get_resource.mock_calls
        assert mock_track.mock_calls[0] == call(factory.sp, raw_data=mock_data, artists=[mock_resource], album=mock_resource)