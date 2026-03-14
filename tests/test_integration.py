"""Integration tests for end-to-end sync workflows."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.qobuz_client import QobuzClient
from src.sync_service import QobuzSyncService


class TestEndToEndSync:
    """Integration tests for complete sync workflows."""
    
    @patch('src.qobuz_client.requests.Session')
    def test_complete_favorites_sync_workflow(self, mock_session_class):
        """Test complete end-to-end favorites sync."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock authentication
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            'tracks': {'items': []},
            'user': {'id': 1, 'display_name': 'Test'}
        }
        
        # Mock get_favorite_tracks for source 1
        source1_favorites = Mock()
        source1_favorites.status_code = 200
        source1_favorites.json.return_value = {
            'tracks': {
                'items': [
                    {
                        'id': 1,
                        'title': 'Source 1 Track',
                        'performer': {'name': 'Artist 1'},
                        'album': {'title': 'Album 1'},
                        'isrc': 'ISRC1',
                        'duration': 180
                    }
                ]
            }
        }
        
        # Mock get_favorite_tracks for source 2
        source2_favorites = Mock()
        source2_favorites.status_code = 200
        source2_favorites.json.return_value = {
            'tracks': {
                'items': [
                    {
                        'id': 2,
                        'title': 'Source 2 Track',
                        'performer': {'name': 'Artist 2'},
                        'album': {'title': 'Album 2'},
                        'isrc': 'ISRC2',
                        'duration': 200
                    }
                ]
            }
        }
        
        # Mock target favorites (empty)
        target_favorites = Mock()
        target_favorites.status_code = 200
        target_favorites.json.return_value = {'tracks': {'items': []}}
        
        # Mock add_favorite responses
        add_favorite_response = Mock()
        add_favorite_response.status_code = 200
        
        # Setup mock session behavior
        get_call_count = [0]
        def mock_get(*args, **kwargs):
            get_call_count[0] += 1
            if get_call_count[0] <= 3:  # Auth calls
                return auth_response
            elif get_call_count[0] == 4:  # Source 1 favorites
                return source1_favorites
            elif get_call_count[0] == 5:  # Source 2 favorites
                return source2_favorites
            else:  # Target favorites
                return target_favorites
        
        mock_session.get.side_effect = mock_get
        mock_session.post.return_value = add_favorite_response
        
        # Create clients
        source1 = QobuzClient('token1', 'Source 1')
        source2 = QobuzClient('token2', 'Source 2')
        target = QobuzClient('token3', 'Target')
        
        # Authenticate
        source1.authenticate()
        source2.authenticate()
        target.authenticate()
        
        # Perform sync
        service = QobuzSyncService([source1, source2], target)
        stats = service.sync_favorites(dry_run=False)
        
        # Verify results
        assert stats['source_accounts'] == 2
        assert stats['unique_tracks'] == 2
        assert stats['newly_favorited'] == 2
        assert mock_session.post.call_count == 2
    
    @patch('src.qobuz_client.requests.Session')
    def test_complete_playlists_sync_workflow(self, mock_session_class):
        """Test complete end-to-end playlists sync."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock authentication
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            'tracks': {'items': []},
            'user': {'id': 1, 'display_name': 'Test'}
        }
        
        # Mock list playlists
        source_playlists_response = Mock()
        source_playlists_response.status_code = 200
        source_playlists_response.json.return_value = {
            'playlists': {
                'items': [
                    {'id': 1, 'name': 'Test Playlist', 'tracks_count': 1}
                ]
            }
        }
        
        target_playlists_response = Mock()
        target_playlists_response.status_code = 200
        target_playlists_response.json.return_value = {'playlists': {'items': []}}
        
        # Mock playlist tracks
        playlist_tracks_response = Mock()
        playlist_tracks_response.status_code = 200
        playlist_tracks_response.json.return_value = {
            'tracks': {
                'items': [
                    {
                        'id': 1,
                        'title': 'Playlist Track',
                        'performer': {'name': 'Artist'},
                        'album': {'title': 'Album'},
                        'isrc': 'ISRC',
                        'duration': 180
                    }
                ]
            }
        }
        
        # Mock create playlist
        create_playlist_response = Mock()
        create_playlist_response.status_code = 200
        create_playlist_response.json.return_value = {'id': 999}
        
        # Mock add track to playlist
        add_track_response = Mock()
        add_track_response.status_code = 200
        
        # Setup mock behavior
        get_responses = [
            auth_response,  # Source auth
            auth_response,  # Target auth
            source_playlists_response,  # Source playlists
            playlist_tracks_response,  # Source playlist tracks
            target_playlists_response  # Target playlists
        ]
        
        mock_session.get.side_effect = get_responses
        post_responses = [
            create_playlist_response,  # Create playlist
            add_track_response  # Add track
        ]
        mock_session.post.side_effect = post_responses
        
        # Create clients
        source = QobuzClient('token1', 'Source')
        target = QobuzClient('token2', 'Target')
        
        # Authenticate
        source.authenticate()
        target.authenticate()
        
        # Perform sync
        service = QobuzSyncService([source], target)
        stats = service.sync_playlists(dry_run=False)
        
        # Verify results
        assert stats['playlists_created'] == 1
        assert stats['tracks_added'] == 1
    
    def test_sync_with_api_errors(self):
        """Test sync behavior with API errors."""
        # Create mock clients that fail
        source = Mock()
        source.account_name = "Failing Source"
        source.get_favorite_tracks.side_effect = Exception("API Error")
        
        target = Mock()
        target.account_name = "Target"
        
        service = QobuzSyncService([source], target)
        
        # Sync should handle the error gracefully
        with pytest.raises(Exception) as exc_info:
            service.sync_favorites(dry_run=False)
        
        assert "API Error" in str(exc_info.value)
    
    def test_dry_run_makes_no_changes(self):
        """Test that dry-run mode makes no actual changes."""
        source = Mock()
        source.account_name = "Source"
        source.get_favorite_tracks.return_value = [
            {'id': 1, 'title': 'Track', 'artist': 'Artist', 'isrc': 'ISRC', 'duration': 180}
        ]
        source.list_user_playlists.return_value = [
            {'id': '1', 'name': 'Playlist', 'tracks_count': 1}
        ]
        source.get_playlist_tracks.return_value = [
            {'id': 1, 'title': 'Track', 'artist': 'Artist', 'isrc': 'ISRC', 'duration': 180}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.get_favorite_tracks.return_value = []
        target.list_user_playlists.return_value = []
        
        service = QobuzSyncService([source], target)
        
        # Run syncs in dry-run mode
        service.sync_favorites(dry_run=True)
        service.sync_playlists(dry_run=True)
        
        # Verify no write operations were called
        target.add_favorite_track.assert_not_called()
        target.create_playlist.assert_not_called()
        target.add_track_to_playlist.assert_not_called()
