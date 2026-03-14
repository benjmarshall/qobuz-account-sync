"""Tests for credentials parsing and validation."""

import pytest
import json
import tempfile
from pathlib import Path

from src.utils.credentials import (
    parse_credentials,
    load_credentials_from_env,
    CredentialsError
)


class TestCredentialsParsing:
    """Test credential file parsing."""
    
    def test_parse_valid_credentials(self, temp_credentials_file):
        """Test parsing valid credentials file."""
        creds = parse_credentials(temp_credentials_file)
        
        assert 'source_account_1_token' in creds
        assert 'source_account_2_token' in creds
        assert 'target_account_token' in creds
        assert creds['source_account_1_token'] == 'mock_source_1_token'
    
    def test_parse_missing_file(self):
        """Test handling of missing credentials file."""
        with pytest.raises(CredentialsError) as exc_info:
            parse_credentials('nonexistent_file.json')
        
        assert 'not found' in str(exc_info.value).lower()
    
    def test_parse_invalid_json(self):
        """Test handling of malformed JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_path = f.name
        
        try:
            with pytest.raises(CredentialsError) as exc_info:
                parse_credentials(temp_path)
            
            assert 'invalid json' in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_parse_missing_required_field(self):
        """Test detection of missing required fields."""
        incomplete_creds = {
            'source_account_1_token': 'token1',
            'source_account_2_token': 'token2'
            # missing target_account_token
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(incomplete_creds, f)
            temp_path = f.name
        
        try:
            with pytest.raises(CredentialsError) as exc_info:
                parse_credentials(temp_path)
            
            assert 'missing required credentials' in str(exc_info.value).lower()
            assert 'target_account_token' in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_parse_empty_token(self):
        """Test detection of empty token values."""
        empty_creds = {
            'source_account_1_token': '',
            'source_account_2_token': 'token2',
            'target_account_token': 'token3'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(empty_creds, f)
            temp_path = f.name
        
        try:
            with pytest.raises(CredentialsError) as exc_info:
                parse_credentials(temp_path)
            
            assert 'empty credentials' in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestEnvironmentVariables:
    """Test environment variable credential loading."""
    
    def test_load_from_env_complete(self, monkeypatch):
        """Test loading complete credentials from environment."""
        monkeypatch.setenv('QOBUZ_SOURCE_ACCOUNT_1_TOKEN', 'env_token_1')
        monkeypatch.setenv('QOBUZ_SOURCE_ACCOUNT_2_TOKEN', 'env_token_2')
        monkeypatch.setenv('QOBUZ_TARGET_ACCOUNT_TOKEN', 'env_token_target')
        
        creds = load_credentials_from_env()
        
        assert creds is not None
        assert creds['source_account_1_token'] == 'env_token_1'
        assert creds['source_account_2_token'] == 'env_token_2'
        assert creds['target_account_token'] == 'env_token_target'
    
    def test_load_from_env_incomplete(self, monkeypatch):
        """Test handling of incomplete environment variables."""
        monkeypatch.setenv('QOBUZ_SOURCE_ACCOUNT_1_TOKEN', 'env_token_1')
        # Missing other tokens
        
        creds = load_credentials_from_env()
        
        assert creds is None
    
    def test_load_from_env_none_set(self):
        """Test when no environment variables are set."""
        creds = load_credentials_from_env()
        
        assert creds is None
