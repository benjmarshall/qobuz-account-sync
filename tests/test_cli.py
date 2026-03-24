"""Tests for CLI flag behavior in sync.py."""

from unittest.mock import Mock, patch

import sync


def _build_client(name):
    client = Mock()
    client.account_name = name
    client.authenticate.return_value = None
    return client


@patch('sync.setup_logger')
@patch('sync.QobuzSyncService')
@patch('sync.QobuzClient')
@patch('sync.parse_credentials')
def test_cli_default_runs_all_entities(mock_parse_credentials, mock_client_cls, mock_service_cls, mock_setup_logger):
    mock_parse_credentials.return_value = {
        'source_account_1_token': 's1',
        'source_account_2_token': 's2',
        'target_account_token': 't'
    }

    clients = [_build_client('s1'), _build_client('s2'), _build_client('target')]
    mock_client_cls.side_effect = clients

    service = Mock()
    service.sync_favorites.return_value = {'newly_favorited': 0, 'already_favorited': 0}
    service.sync_albums.return_value = {'newly_favorited': 0, 'already_favorited': 0}
    service.sync_artists.return_value = {'newly_favorited': 0, 'already_favorited': 0}
    service.sync_playlists.return_value = {'playlists_created': 0, 'playlists_updated': 0, 'tracks_added': 0}
    mock_service_cls.return_value = service

    mock_setup_logger.return_value = Mock()

    with patch('sys.argv', ['sync.py']):
        assert sync.main() == 0

    service.sync_favorites.assert_called_once()
    service.sync_albums.assert_called_once()
    service.sync_artists.assert_called_once()
    service.sync_playlists.assert_called_once()


@patch('sync.setup_logger')
@patch('sync.QobuzSyncService')
@patch('sync.QobuzClient')
@patch('sync.parse_credentials')
def test_cli_skip_flags_skip_albums_and_artists(mock_parse_credentials, mock_client_cls, mock_service_cls, mock_setup_logger):
    mock_parse_credentials.return_value = {
        'source_account_1_token': 's1',
        'source_account_2_token': 's2',
        'target_account_token': 't'
    }

    clients = [_build_client('s1'), _build_client('s2'), _build_client('target')]
    mock_client_cls.side_effect = clients

    service = Mock()
    service.sync_favorites.return_value = {'newly_favorited': 0, 'already_favorited': 0}
    service.sync_playlists.return_value = {'playlists_created': 0, 'playlists_updated': 0, 'tracks_added': 0}
    mock_service_cls.return_value = service

    mock_setup_logger.return_value = Mock()

    with patch('sys.argv', ['sync.py', '--skip-albums', '--skip-artists']):
        assert sync.main() == 0

    service.sync_favorites.assert_called_once()
    service.sync_playlists.assert_called_once()
    service.sync_albums.assert_not_called()
    service.sync_artists.assert_not_called()


@patch('sync.setup_logger')
@patch('sync.QobuzSyncService')
@patch('sync.QobuzClient')
@patch('sync.parse_credentials')
def test_cli_albums_only(mock_parse_credentials, mock_client_cls, mock_service_cls, mock_setup_logger):
    mock_parse_credentials.return_value = {
        'source_account_1_token': 's1',
        'source_account_2_token': 's2',
        'target_account_token': 't'
    }

    clients = [_build_client('s1'), _build_client('s2'), _build_client('target')]
    mock_client_cls.side_effect = clients

    service = Mock()
    service.sync_albums.return_value = {'newly_favorited': 0, 'already_favorited': 0}
    mock_service_cls.return_value = service

    mock_setup_logger.return_value = Mock()

    with patch('sys.argv', ['sync.py', '--albums-only']):
        assert sync.main() == 0

    service.sync_albums.assert_called_once()
    service.sync_favorites.assert_not_called()
    service.sync_artists.assert_not_called()
    service.sync_playlists.assert_not_called()


def test_cli_rejects_multiple_only_flags():
    with patch('sys.argv', ['sync.py', '--albums-only', '--artists-only']):
        try:
            sync.main()
            assert False, 'Expected SystemExit due to parser error'
        except SystemExit as exc:
            assert exc.code == 2
