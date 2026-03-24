"""Tests for QobuzClient."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from src.qobuz_client import QobuzClient


class TestQobuzClientInitialization:
    """Test QobuzClient initialization."""
    
    def test_init_with_token(self, mock_token):
        """Test client initialization with token."""
        client = QobuzClient(mock_token, "Test Account")
        
        assert client.user_auth_token == mock_token
        assert client.account_name == "Test Account"
        assert client.user_id is None
        assert client.user_name is None
    
    def test_session_headers_configured(self, mock_token):
        """Test that session headers are properly configured."""
        client = QobuzClient(mock_token, "Test Account")
        
        assert 'X-User-Auth-Token' in client._session.headers
        assert client._session.headers['X-User-Auth-Token'] == mock_token
        assert 'X-App-Id' in client._session.headers


class TestQobuzClientAuthentication:
    """Test QobuzClient authentication."""
    
    @patch('src.qobuz_client.requests.Session.get')
    def test_authenticate_success(self, mock_get, mock_token, mock_favorite_response):
        """Test successful authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_favorite_response
        mock_get.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        client.authenticate()
        
        assert client.user_id == 999
        assert client.user_name == "Test User"
        mock_get.assert_called_once()
    
    @patch('src.qobuz_client.requests.Session.get')
    def test_authenticate_invalid_token(self, mock_get, mock_token):
        """Test authentication with invalid token."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        
        with pytest.raises(Exception) as exc_info:
            client.authenticate()
        
        assert "Invalid or expired" in str(exc_info.value)
        assert "Test Account" in str(exc_info.value)
    
    @patch('src.qobuz_client.requests.Session.get')
    def test_authenticate_network_error(self, mock_get, mock_token):
        """Test authentication with network error."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        client = QobuzClient(mock_token, "Test Account")
        
        with pytest.raises(Exception) as exc_info:
            client.authenticate()
        
        assert "Authentication failed" in str(exc_info.value)


class TestQobuzClientFavorites:
    """Test favorite tracks operations."""
    
    @patch('src.qobuz_client.requests.Session.get')
    def test_get_favorite_tracks(self, mock_get, mock_token, mock_favorite_response):
        """Test retrieving favorite tracks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_favorite_response
        mock_get.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        tracks = client.get_favorite_tracks()
        
        assert len(tracks) == 2
        assert tracks[0]['id'] == 1
        assert tracks[0]['title'] == 'Track One'
        assert tracks[0]['artist'] == 'Artist One'
        assert tracks[0]['isrc'] == 'USTEST0000001'
    
    @patch('src.qobuz_client.requests.Session.post')
    def test_add_favorite_track(self, mock_post, mock_token):
        """Test adding track to favorites."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        result = client.add_favorite_track(12345)
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('src.qobuz_client.requests.Session.post')
    def test_add_favorite_already_exists(self, mock_post, mock_token):
        """Test adding already favorited track (400 response)."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        result = client.add_favorite_track(12345)
        
        assert result is True  # Should still return True for already favorited


class TestQobuzClientAlbumsAndArtists:
    """Test favorite album and artist operations."""

    @patch('src.qobuz_client.requests.Session.get')
    def test_get_favorite_albums(self, mock_get, mock_token):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'albums': {
                'items': [
                    {'id': 10, 'title': 'Album One', 'artist': {'name': 'Artist One'}, 'upc': 'UPC1'}
                ]
            }
        }
        mock_get.return_value = mock_response

        client = QobuzClient(mock_token, "Test Account")
        albums = client.get_favorite_albums()

        assert len(albums) == 1
        assert albums[0]['id'] == 10
        assert albums[0]['title'] == 'Album One'
        assert albums[0]['upc'] == 'UPC1'

    @patch('src.qobuz_client.requests.Session.post')
    def test_add_favorite_album(self, mock_post, mock_token):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = QobuzClient(mock_token, "Test Account")
        assert client.add_favorite_album(10) is True

    @patch('src.qobuz_client.requests.Session.get')
    def test_get_favorite_artists(self, mock_get, mock_token):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'artists': {
                'items': [
                    {'id': 77, 'name': 'Artist One'}
                ]
            }
        }
        mock_get.return_value = mock_response

        client = QobuzClient(mock_token, "Test Account")
        artists = client.get_favorite_artists()

        assert len(artists) == 1
        assert artists[0]['id'] == 77
        assert artists[0]['name'] == 'Artist One'

    @patch('src.qobuz_client.requests.Session.post')
    def test_add_favorite_artist(self, mock_post, mock_token):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = QobuzClient(mock_token, "Test Account")
        assert client.add_favorite_artist(77) is True


class TestQobuzClientPlaylists:
    """Test playlist operations."""
    
    @patch('src.qobuz_client.requests.Session.get')
    def test_list_user_playlists(self, mock_get, mock_token, mock_playlist_response):
        """Test listing user playlists."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_playlist_response
        mock_get.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        playlists = client.list_user_playlists()
        
        assert len(playlists) == 2
        assert playlists[0]['id'] == '100'
        assert playlists[0]['name'] == 'Playlist One'
        assert playlists[0]['tracks_count'] == 10
    
    @patch('src.qobuz_client.requests.Session.get')
    def test_get_playlist_tracks(self, mock_get, mock_token, mock_playlist_tracks_response):
        """Test getting tracks from a playlist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_playlist_tracks_response
        mock_get.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        tracks = client.get_playlist_tracks('100')
        
        assert len(tracks) == 2
        assert tracks[0]['id'] == 1
        assert tracks[0]['title'] == 'Track One'
    
    @patch('src.qobuz_client.requests.Session.post')
    def test_create_playlist(self, mock_post, mock_token):
        """Test creating a new playlist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 999}
        mock_post.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        playlist_id = client.create_playlist("New Playlist", "Description")
        
        assert playlist_id == '999'
        mock_post.assert_called_once()
    
    @patch('src.qobuz_client.requests.Session.post')
    def test_add_track_to_playlist(self, mock_post, mock_token):
        """Test adding track to playlist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = QobuzClient(mock_token, "Test Account")
        result = client.add_track_to_playlist('100', 12345)
        
        assert result is True
        mock_post.assert_called_once()
    
    def test_find_playlist_by_name(self, mock_token):
        """Test finding playlist by name."""
        client = QobuzClient(mock_token, "Test Account")
        
        # Mock the list_user_playlists method
        client.list_user_playlists = Mock(return_value=[
            {'id': '1', 'name': 'Playlist A', 'tracks_count': 5},
            {'id': '2', 'name': 'Playlist B', 'tracks_count': 10}
        ])
        
        result = client.find_playlist_by_name('Playlist B')
        
        assert result is not None
        assert result['id'] == '2'
        assert result['name'] == 'Playlist B'
    
    def test_find_playlist_by_name_not_found(self, mock_token):
        """Test finding non-existent playlist."""
        client = QobuzClient(mock_token, "Test Account")
        
        client.list_user_playlists = Mock(return_value=[
            {'id': '1', 'name': 'Playlist A', 'tracks_count': 5}
        ])
        
        result = client.find_playlist_by_name('Non-existent')
        
        assert result is None
