"""Tests for HAR token extraction."""

import pytest
import json
import sys
from pathlib import Path
from io import StringIO

# Import the extraction function
sys.path.insert(0, str(Path(__file__).parent.parent))
from extract_token_from_har import extract_token_from_har


class TestTokenExtraction:
    """Test HAR file token extraction."""
    
    def test_extract_from_request_header(self, temp_har_file):
        """Test extraction from request header."""
        token = extract_token_from_har(temp_har_file)
        
        assert token == "extracted_test_token_12345"
    
    def test_extract_from_request_cookie(self, tmp_path):
        """Test extraction from request cookie."""
        har_data = {
            "log": {
                "entries": [
                    {
                        "request": {
                            "headers": [],
                            "cookies": [
                                {
                                    "name": "user_auth_token",
                                    "value": "cookie_token_67890"
                                }
                            ]
                        },
                        "response": {"cookies": []}
                    }
                ]
            }
        }
        
        har_file = tmp_path / "test_cookie.har"
        with open(har_file, 'w') as f:
            json.dump(har_data, f)
        
        token = extract_token_from_har(str(har_file))
        
        assert token == "cookie_token_67890"
    
    def test_extract_from_response_cookie(self, tmp_path):
        """Test extraction from response cookie."""
        har_data = {
            "log": {
                "entries": [
                    {
                        "request": {
                            "headers": [],
                            "cookies": []
                        },
                        "response": {
                            "cookies": [
                                {
                                    "name": "user_auth_token",
                                    "value": "response_cookie_token_999"
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        har_file = tmp_path / "test_response.har"
        with open(har_file, 'w') as f:
            json.dump(har_data, f)
        
        token = extract_token_from_har(str(har_file))
        
        assert token == "response_cookie_token_999"
    
    def test_no_token_found(self, tmp_path):
        """Test when no token is found."""
        har_data = {
            "log": {
                "entries": [
                    {
                        "request": {
                            "headers": [],
                            "cookies": []
                        },
                        "response": {"cookies": []}
                    }
                ]
            }
        }
        
        har_file = tmp_path / "test_empty.har"
        with open(har_file, 'w') as f:
            json.dump(har_data, f)
        
        token = extract_token_from_har(str(har_file))
        
        assert token == ""
    
    def test_invalid_har_file(self):
        """Test handling of missing HAR file."""
        token = extract_token_from_har("nonexistent.har")
        
        assert token == ""
    
    def test_malformed_har_json(self, tmp_path):
        """Test handling of malformed HAR JSON."""
        har_file = tmp_path / "bad.har"
        with open(har_file, 'w') as f:
            f.write("{ invalid json }")
        
        token = extract_token_from_har(str(har_file))
        
        assert token == ""
    
    def test_prioritize_header_over_cookie(self, tmp_path):
        """Test that header takes priority over cookie."""
        har_data = {
            "log": {
                "entries": [
                    {
                        "request": {
                            "headers": [
                                {
                                    "name": "X-User-Auth-Token",
                                    "value": "header_token"
                                }
                            ],
                            "cookies": [
                                {
                                    "name": "user_auth_token",
                                    "value": "cookie_token"
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        har_file = tmp_path / "priority.har"
        with open(har_file, 'w') as f:
            json.dump(har_data, f)
        
        token = extract_token_from_har(str(har_file))
        
        # Should return header token (priority)
        assert token == "header_token"
    
    def test_skip_short_tokens(self, tmp_path):
        """Test that short cookie values are skipped."""
        har_data = {
            "log": {
                "entries": [
                    {
                        "request": {
                            "headers": [],
                            "cookies": [
                                {
                                    "name": "user_auth_token",
                                    "value": "short"  # Too short to be valid
                                },
                                {
                                    "name": "user_auth_token",
                                    "value": "this_is_a_long_enough_token_value_12345"
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        har_file = tmp_path / "short_token.har"
        with open(har_file, 'w') as f:
            json.dump(har_data, f)
        
        token = extract_token_from_har(str(har_file))
        
        assert token == "this_is_a_long_enough_token_value_12345"
