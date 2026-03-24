"""Tests for QobuzSyncService."""

import pytest
from unittest.mock import Mock, MagicMock

from src.sync_service import QobuzSyncService


class TestSyncServiceInitialization:
    """Test SyncService initialization."""
    
    def test_init_with_clients(self):
        """Test service initialization with clients."""
        source1 = Mock()
        source1.account_name = "Source 1"
        source2 = Mock()
        source2.account_name = "Source 2"
        target = Mock()
        target.account_name = "Target"
        
        service = QobuzSyncService([source1, source2], target)
        
        assert len(service.source_clients) == 2
        assert service.target_client == target


class TestFavoritesSync:
    """Test favorites synchronization."""
    
    def test_sync_favorites_basic(self):
        """Test basic favorites sync."""
        # Setup source clients
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.get_favorite_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180},
            {'id': 2, 'title': 'Track 2', 'artist': 'Artist 2', 'isrc': 'ISRC2', 'duration': 200}
        ]
        
        source2 = Mock()
        source2.account_name = "Source 2"
        source2.get_favorite_tracks.return_value = [
            {'id': 3, 'title': 'Track 3', 'artist': 'Artist 3', 'isrc': 'ISRC3', 'duration': 190}
        ]
        
        # Setup target client
        target = Mock()
        target.account_name = "Target"
        target.get_favorite_tracks.return_value = []
        target.add_favorite_track.return_value = True
        
        # Create service and sync
        service = QobuzSyncService([source1, source2], target)
        stats = service.sync_favorites(dry_run=False)
        
        assert stats['source_accounts'] == 2
        assert stats['unique_tracks'] == 3
        assert stats['newly_favorited'] == 3
        assert target.add_favorite_track.call_count == 3
    
    def test_sync_favorites_deduplication_by_id(self):
        """Test deduplication by track ID."""
        # Both sources have track with same ID
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.get_favorite_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        
        source2 = Mock()
        source2.account_name = "Source 2"
        source2.get_favorite_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.get_favorite_tracks.return_value = []
        target.add_favorite_track.return_value = True
        
        service = QobuzSyncService([source1, source2], target)
        stats = service.sync_favorites(dry_run=False)
        
        # Should only add once despite appearing in both sources
        assert stats['unique_tracks'] == 1
        assert target.add_favorite_track.call_count == 1
    
    def test_sync_favorites_deduplication_by_isrc(self):
        """Test deduplication by ISRC."""
        # Different IDs but same ISRC
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.get_favorite_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'SAME_ISRC', 'duration': 180}
        ]
        
        source2 = Mock()
        source2.account_name = "Source 2"
        source2.get_favorite_tracks.return_value = [
            {'id': 999, 'title': 'Track 1 Remix', 'artist': 'Artist 1', 'isrc': 'SAME_ISRC', 'duration': 200}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.get_favorite_tracks.return_value = []
        target.add_favorite_track.return_value = True
        
        service = QobuzSyncService([source1, source2], target)
        stats = service.sync_favorites(dry_run=False)
        
        # Should deduplicate by ISRC
        assert stats['unique_tracks'] == 1
        assert target.add_favorite_track.call_count == 1
    
    def test_sync_favorites_skip_existing(self):
        """Test skipping already favorited tracks."""
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.get_favorite_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180},
            {'id': 2, 'title': 'Track 2', 'artist': 'Artist 2', 'isrc': 'ISRC2', 'duration': 200}
        ]
        
        target = Mock()
        target.account_name = "Target"
        # Track 1 already in target
        target.get_favorite_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        target.add_favorite_track.return_value = True
        
        service = QobuzSyncService([source1], target)
        stats = service.sync_favorites(dry_run=False)
        
        assert stats['already_favorited'] == 1
        assert stats['newly_favorited'] == 1
        assert target.add_favorite_track.call_count == 1
    
    def test_sync_favorites_dry_run(self):
        """Test dry-run mode for favorites."""
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.get_favorite_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.get_favorite_tracks.return_value = []
        
        service = QobuzSyncService([source1], target)
        stats = service.sync_favorites(dry_run=True)
        
        # Should not call add_favorite_track in dry run
        target.add_favorite_track.assert_not_called()
        assert stats['newly_favorited'] == 1


class TestAlbumsAndArtistsSync:
    """Test albums/artists synchronization."""

    def test_sync_albums_dedup_and_skip_existing(self):
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.get_favorite_albums.return_value = [
            {'id': 10, 'title': 'Album 1', 'artist': 'Artist 1', 'upc': 'UPC1'},
            {'id': 11, 'title': 'Album 2', 'artist': 'Artist 2', 'upc': 'UPC2'}
        ]

        source2 = Mock()
        source2.account_name = "Source 2"
        source2.get_favorite_albums.return_value = [
            {'id': 999, 'title': 'Album 1 Duplicate', 'artist': 'Artist 1', 'upc': 'UPC1'}
        ]

        target = Mock()
        target.account_name = "Target"
        target.get_favorite_albums.return_value = [
            {'id': 11, 'title': 'Album 2', 'artist': 'Artist 2', 'upc': 'UPC2'}
        ]
        target.add_favorite_album.return_value = True

        service = QobuzSyncService([source1, source2], target)
        stats = service.sync_albums(dry_run=False)

        assert stats['unique_albums'] == 2
        assert stats['already_favorited'] == 1
        assert stats['newly_favorited'] == 1
        assert target.add_favorite_album.call_count == 1

    def test_sync_albums_dry_run(self):
        source = Mock()
        source.account_name = "Source"
        source.get_favorite_albums.return_value = [
            {'id': 10, 'title': 'Album 1', 'artist': 'Artist 1', 'upc': 'UPC1'}
        ]

        target = Mock()
        target.account_name = "Target"
        target.get_favorite_albums.return_value = []

        service = QobuzSyncService([source], target)
        stats = service.sync_albums(dry_run=True)

        target.add_favorite_album.assert_not_called()
        assert stats['newly_favorited'] == 1

    def test_sync_artists_dedup_and_skip_existing(self):
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.get_favorite_artists.return_value = [
            {'id': 1, 'name': 'Artist 1'},
            {'id': 2, 'name': 'Artist 2'}
        ]

        source2 = Mock()
        source2.account_name = "Source 2"
        source2.get_favorite_artists.return_value = [
            {'id': 2, 'name': 'Artist 2'}
        ]

        target = Mock()
        target.account_name = "Target"
        target.get_favorite_artists.return_value = [
            {'id': 1, 'name': 'Artist 1'}
        ]
        target.add_favorite_artist.return_value = True

        service = QobuzSyncService([source1, source2], target)
        stats = service.sync_artists(dry_run=False)

        assert stats['unique_artists'] == 2
        assert stats['already_favorited'] == 1
        assert stats['newly_favorited'] == 1
        assert target.add_favorite_artist.call_count == 1


class TestPlaylistsSync:
    """Test playlists synchronization."""
    
    def test_sync_playlists_basic(self):
        """Test basic playlist sync."""
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.list_user_playlists.return_value = [
            {'id': '1', 'name': 'Playlist A', 'tracks_count': 2}
        ]
        source1.get_playlist_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.list_user_playlists.return_value = []
        target.create_playlist.return_value = 'new_playlist_id'
        target.add_track_to_playlist.return_value = True
        target.get_playlist_tracks.return_value = []
        
        service = QobuzSyncService([source1], target)
        stats = service.sync_playlists(dry_run=False)
        
        assert stats['playlists_created'] == 1
        assert stats['tracks_added'] == 1
        target.create_playlist.assert_called_once()
    
    def test_sync_playlists_merge_by_name(self):
        """Test merging playlists with same name."""
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.list_user_playlists.return_value = [
            {'id': '1', 'name': 'Same Name', 'tracks_count': 1}
        ]
        source1.get_playlist_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        
        source2 = Mock()
        source2.account_name = "Source 2"
        source2.list_user_playlists.return_value = [
            {'id': '2', 'name': 'Same Name', 'tracks_count': 1}
        ]
        source2.get_playlist_tracks.return_value = [
            {'id': 2, 'title': 'Track 2', 'artist': 'Artist 2', 'isrc': 'ISRC2', 'duration': 200}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.list_user_playlists.return_value = []
        target.create_playlist.return_value = 'merged_playlist_id'
        target.add_track_to_playlist.return_value = True
        target.get_playlist_tracks.return_value = []
        
        service = QobuzSyncService([source1, source2], target)
        stats = service.sync_playlists(dry_run=False, merge_playlists=True)
        
        # Should create one playlist with tracks from both sources
        assert stats['playlists_created'] == 1
        assert stats['tracks_added'] == 2
        assert target.create_playlist.call_count == 1
    
    def test_sync_playlists_no_merge(self):
        """Test keeping playlists separate."""
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.list_user_playlists.return_value = [
            {'id': '1', 'name': 'Same Name', 'tracks_count': 1}
        ]
        source1.get_playlist_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        
        source2 = Mock()
        source2.account_name = "Source 2"
        source2.list_user_playlists.return_value = [
            {'id': '2', 'name': 'Same Name', 'tracks_count': 1}
        ]
        source2.get_playlist_tracks.return_value = [
            {'id': 2, 'title': 'Track 2', 'artist': 'Artist 2', 'isrc': 'ISRC2', 'duration': 200}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.list_user_playlists.return_value = []
        target.create_playlist.return_value = 'playlist_id'
        target.add_track_to_playlist.return_value = True
        target.get_playlist_tracks.return_value = []
        
        service = QobuzSyncService([source1, source2], target)
        stats = service.sync_playlists(dry_run=False, merge_playlists=False)
        
        # Should create two separate playlists
        assert stats['playlists_created'] == 2
        assert target.create_playlist.call_count == 2
    
    def test_sync_playlists_update_existing(self):
        """Test updating existing playlists."""
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.list_user_playlists.return_value = [
            {'id': '1', 'name': 'Existing', 'tracks_count': 2}
        ]
        source1.get_playlist_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180},
            {'id': 2, 'title': 'Track 2', 'artist': 'Artist 2', 'isrc': 'ISRC2', 'duration': 200}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.list_user_playlists.return_value = [
            {'id': 'existing_id', 'name': 'Existing', 'tracks_count': 1}
        ]
        # Playlist already has track 1
        target.get_playlist_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        target.add_track_to_playlist.return_value = True
        
        service = QobuzSyncService([source1], target)
        stats = service.sync_playlists(dry_run=False)
        
        assert stats['playlists_updated'] == 1
        assert stats['playlists_created'] == 0
        assert stats['tracks_added'] == 1  # Only track 2 added
        assert stats['tracks_skipped'] == 1  # Track 1 skipped
    
    def test_sync_playlists_dry_run(self):
        """Test dry-run mode for playlists."""
        source1 = Mock()
        source1.account_name = "Source 1"
        source1.list_user_playlists.return_value = [
            {'id': '1', 'name': 'Test', 'tracks_count': 1}
        ]
        source1.get_playlist_tracks.return_value = [
            {'id': 1, 'title': 'Track 1', 'artist': 'Artist 1', 'isrc': 'ISRC1', 'duration': 180}
        ]
        
        target = Mock()
        target.account_name = "Target"
        target.list_user_playlists.return_value = []
        
        service = QobuzSyncService([source1], target)
        stats = service.sync_playlists(dry_run=True)
        
        # Should not call create_playlist or add_track in dry run
        target.create_playlist.assert_not_called()
        target.add_track_to_playlist.assert_not_called()
        assert stats['playlists_created'] == 1
        assert stats['tracks_added'] == 1
