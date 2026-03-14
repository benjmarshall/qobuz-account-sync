# Testing Guide

This document describes the comprehensive test suite for the Qobuz Account Sync service.

## Test Suite Overview

The test suite provides **professional-grade test coverage** with mocked Qobuz API responses, allowing full validation of all functionality without requiring real Qobuz credentials.

### Test Statistics

- **Total Test Files:** 5
- **Test Categories:** Unit tests, Integration tests
- **Coverage Areas:** 
  - Credentials parsing and validation
  - QobuzClient (all methods)
  - SyncService (deduplication, merging)
  - Token extraction from HAR files
  - End-to-end sync workflows
  - Error handling and edge cases

## Installation

Install test dependencies:

```bash
pip install pytest pytest-cov
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_qobuz_client.py
```

### Run Specific Test Class

```bash
pytest tests/test_qobuz_client.py::TestQobuzClientAuthentication
```

### Run Specific Test

```bash
pytest tests/test_qobuz_client.py::TestQobuzClientAuthentication::test_authenticate_success
```

### Run with Coverage Report

```bash
pytest --cov=src --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Only Integration Tests

```bash
pytest -m integration
```

## Test Structure

```
tests/
├── __init__.py                    # Test package marker
├── conftest.py                    # Shared fixtures and mocks
├── test_credentials.py            # Credentials parsing tests
├── test_qobuz_client.py           # QobuzClient unit tests
├── test_sync_service.py           # SyncService unit tests
├── test_token_extraction.py       # HAR token extraction tests
└── test_integration.py            # End-to-end integration tests
```

## Test Coverage

### 1. Credentials Parsing (`test_credentials.py`)

**Tests:**
- Valid JSON credentials file parsing
- Missing credentials file handling
- Invalid JSON format detection
- Missing required fields detection
- Empty/blank token validation
- Environment variable loading
- Complete vs incomplete environment variables

**What's Tested:**
- `parse_credentials()` function
- `load_credentials_from_env()` function
- `CredentialsError` exception handling

### 2. Qobuz Client (`test_qobuz_client.py`)

**Tests:**
- Client initialization with token
- Session header configuration
- Successful authentication
- Invalid token handling (401 response)
- Network error handling
- Get favorite tracks
- Add favorite track
- Already favorited track (400 response)
- List user playlists
- Get playlist tracks
- Create new playlist
- Add track to playlist
- Find playlist by name
- Playlist not found handling

**What's Tested:**
- `QobuzClient.__init__()`
- `QobuzClient.authenticate()`
- `QobuzClient.get_favorite_tracks()`
- `QobuzClient.add_favorite_track()`
- `QobuzClient.list_user_playlists()`
- `QobuzClient.get_playlist_tracks()`
- `QobuzClient.create_playlist()`
- `QobuzClient.add_track_to_playlist()`
- `QobuzClient.find_playlist_by_name()`

### 3. Sync Service (`test_sync_service.py`)

**Tests:**
- Service initialization with multiple clients
- Basic favorites sync
- Deduplication by track ID
- Deduplication by ISRC
- Skip already favorited tracks
- Dry-run mode for favorites
- Basic playlist sync
- Merge playlists by name
- Keep playlists separate (no merge)
- Update existing playlists
- Dry-run mode for playlists

**What's Tested:**
- `QobuzSyncService.__init__()`
- `QobuzSyncService.sync_favorites()`
- `QobuzSyncService.sync_playlists()`
- Deduplication logic
- Merge strategies

### 4. Token Extraction (`test_token_extraction.py`)

**Tests:**
- Extract from request header (X-User-Auth-Token)
- Extract from request cookie (user_auth_token)
- Extract from response cookie
- No token found handling
- Invalid/missing HAR file
- Malformed HAR JSON
- Priority: header over cookie
- Skip short/invalid token values

**What's Tested:**
- `extract_token_from_har()` function
- HAR file parsing
- Token priority logic

### 5. Integration Tests (`test_integration.py`)

**Tests:**
- Complete end-to-end favorites sync workflow
- Complete end-to-end playlists sync workflow
- API error handling during sync
- Dry-run makes no actual changes

**What's Tested:**
- Full sync pipeline
- Client → Service → API interaction
- Error propagation
- Dry-run safety

## Test Fixtures

Located in `conftest.py`, available to all tests:

- `mock_token` - Sample authentication token
- `mock_credentials` - Complete credentials dictionary
- `mock_track` - Sample track object
- `mock_playlist` - Sample playlist object
- `mock_favorite_response` - Mocked API response for favorites
- `mock_playlist_response` - Mocked API response for playlists
- `mock_playlist_tracks_response` - Mocked tracks in playlist
- `mock_response` - Generic HTTP response mock
- `temp_credentials_file` - Temporary credentials JSON file
- `temp_har_file` - Temporary HAR file with test data
- `mock_qobuz_client` - Mocked QobuzClient instance

## Mocking Strategy

The test suite uses **comprehensive mocking** to avoid real API calls:

### HTTP Mocking

```python
@patch('src.qobuz_client.requests.Session.get')
def test_something(self, mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {...}
    mock_get.return_value = mock_response
```

### Client Mocking

```python
source_client = Mock()
source_client.get_favorite_tracks.return_value = [...]
```

### File System Mocking

```python
@pytest.fixture
def temp_credentials_file(mock_credentials):
    with tempfile.NamedTemporaryFile(...) as f:
        json.dump(mock_credentials, f)
        yield f.name
```

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<what_is_being_tested>`

### Example Test

```python
class TestMyFeature:
    """Test my feature."""
    
    def test_basic_functionality(self):
        """Test that basic functionality works."""
        # Arrange
        input_data = {...}
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_output
```

### Using Fixtures

```python
def test_with_fixture(self, mock_credentials):
    """Test using a fixture."""
    # mock_credentials is automatically provided
    assert 'source_account_1_token' in mock_credentials
```

### Testing Exceptions

```python
def test_error_handling(self):
    """Test error is raised correctly."""
    with pytest.raises(CredentialsError) as exc_info:
        parse_credentials('nonexistent.json')
    
    assert 'not found' in str(exc_info.value)
```

## Continuous Integration

The test suite is designed to work in CI/CD environments:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-report=xml
```

## Test Maintenance

### Adding Tests for New Features

1. Create test file: `tests/test_<feature>.py`
2. Add test class: `class Test<Feature>`
3. Write test methods using fixtures
4. Update this documentation

### Updating Mocks

When the Qobuz API changes:

1. Update mock responses in `conftest.py`
2. Update affected tests
3. Verify all tests still pass

## Known Limitations

The test suite does **not** test:

- Actual Qobuz API responses (requires real tokens)
- Network latency and timeouts (would need real API)
- Rate limiting behavior (needs production usage)
- Real-world track deduplication accuracy

These require manual testing with real Qobuz credentials.

## Troubleshooting

### Import Errors

If you get import errors:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Fixture Not Found

Make sure `conftest.py` is in the tests directory and properly configured.

### Mock Not Working

Verify you're patching the correct path:
```python
# Patch where it's used, not where it's defined
@patch('src.qobuz_client.requests.Session.get')  # ✅ Correct
@patch('requests.Session.get')  # ❌ Wrong
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)

---

**Test Suite Status:** ✅ Complete and ready for use

All tests are designed to run without external dependencies and provide comprehensive validation of the sync service functionality.
