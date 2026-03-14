"""Pytest configuration and shared fixtures."""

import pytest
import json
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile


@pytest.fixture
def mock_token():
    """Provide a mock authentication token."""
    return "mock_token_12345_test"


@pytest.fixture
def mock_credentials():
    """Provide mock credentials for testing."""
    return {
        "source_account_1_token": "mock_source_1_token",
        "source_account_2_token": "mock_source_2_token",
        "target_account_token": "mock_target_token"
    }


@pytest.fixture
def mock_track():
    """Provide a mock track object."""
    return {
        'id': 12345,
        'title': 'Test Track',
        'artist': 'Test Artist',
        'album': 'Test Album',
        'isrc': 'USTEST1234567',
        'duration': 180
    }


@pytest.fixture
def mock_playlist():
    """Provide a mock playlist object."""
    return {
        'id': '67890',
        'name': 'Test Playlist',
        'tracks_count': 5,
        'description': 'Test Description'
    }


@pytest.fixture
def mock_favorite_response():
    """Provide mock API response for favorites."""
    return {
        'tracks': {
            'items': [
                {
                    'id': 1,
                    'title': 'Track One',
                    'performer': {'name': 'Artist One'},
                    'album': {'title': 'Album One'},
                    'isrc': 'USTEST0000001',
                    'duration': 180
                },
                {
                    'id': 2,
                    'title': 'Track Two',
                    'performer': {'name': 'Artist Two'},
                    'album': {'title': 'Album Two'},
                    'isrc': 'USTEST0000002',
                    'duration': 200
                }
            ]
        },
        'user': {
            'id': 999,
            'display_name': 'Test User'
        }
    }


@pytest.fixture
def mock_playlist_response():
    """Provide mock API response for playlists."""
    return {
        'playlists': {
            'items': [
                {
                    'id': 100,
                    'name': 'Playlist One',
                    'tracks_count': 10,
                    'description': 'First playlist'
                },
                {
                    'id': 200,
                    'name': 'Playlist Two',
                    'tracks_count': 5,
                    'description': 'Second playlist'
                }
            ]
        }
    }


@pytest.fixture
def mock_playlist_tracks_response():
    """Provide mock API response for playlist tracks."""
    return {
        'tracks': {
            'items': [
                {
                    'id': 1,
                    'title': 'Track One',
                    'performer': {'name': 'Artist One'},
                    'album': {'title': 'Album One'},
                    'isrc': 'USTEST0000001',
                    'duration': 180
                },
                {
                    'id': 2,
                    'title': 'Track Two',
                    'performer': {'name': 'Artist Two'},
                    'album': {'title': 'Album Two'},
                    'isrc': 'USTEST0000002',
                    'duration': 200
                }
            ]
        }
    }


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {}
    return mock


@pytest.fixture
def temp_credentials_file(mock_credentials):
    """Create a temporary credentials file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_credentials, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_har_file():
    """Create a temporary HAR file with mock data."""
    har_data = {
        "log": {
            "version": "1.2",
            "entries": [
                {
                    "request": {
                        "headers": [
                            {
                                "name": "X-User-Auth-Token",
                                "value": "extracted_test_token_12345"
                            }
                        ]
                    }
                }
            ]
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.har', delete=False) as f:
        json.dump(har_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_qobuz_client():
    """Create a mock QobuzClient."""
    from src.qobuz_client import QobuzClient
    
    client = Mock(spec=QobuzClient)
    client.account_name = "Mock Account"
    client.user_auth_token = "mock_token"
    client.authenticate.return_value = None
    
    return client
