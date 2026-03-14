"""Credentials parser for reading credentials from config file."""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class CredentialsError(Exception):
    """Exception raised when credentials cannot be parsed."""
    pass


def parse_credentials(credentials_path: str = "credentials.json") -> Dict[str, str]:
    """
    Parse credentials from JSON config file.
    
    Args:
        credentials_path: Path to the credentials file (default: credentials.json)
    
    Returns:
        Dictionary containing credentials with keys:
        - source_account_1_token: First source account token
        - source_account_2_token: Second source account token  
        - target_account_token: Target account token
    
    Raises:
        CredentialsError: If file not found or required credentials are missing
    """
    creds_file = Path(credentials_path)
    
    if not creds_file.exists():
        raise CredentialsError(f"Credentials file not found: {credentials_path}")
    
    try:
        with open(creds_file, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
    except json.JSONDecodeError as e:
        raise CredentialsError(f"Invalid JSON in credentials file: {e}")
    
    # Define required credentials
    required_keys = ['source_account_1_token', 'source_account_2_token', 'target_account_token']
    
    # Check all required credentials are present
    missing_keys = [key for key in required_keys if key not in credentials]
    if missing_keys:
        raise CredentialsError(
            f"Missing required credentials: {', '.join(missing_keys)}"
        )
    
    # Validate tokens are not empty
    empty_keys = [key for key in required_keys if not credentials[key].strip()]
    if empty_keys:
        raise CredentialsError(
            f"Empty credentials found: {', '.join(empty_keys)}"
        )
    
    return credentials


def load_credentials_from_env() -> Optional[Dict[str, str]]:
    """
    Load credentials from environment variables.
    
    Returns:
        Dictionary with credentials or None if not all are set
    """
    source_1_token = os.getenv('QOBUZ_SOURCE_ACCOUNT_1_TOKEN')
    source_2_token = os.getenv('QOBUZ_SOURCE_ACCOUNT_2_TOKEN')
    target_token = os.getenv('QOBUZ_TARGET_ACCOUNT_TOKEN')
    
    if source_1_token and source_2_token and target_token:
        return {
            'source_account_1_token': source_1_token,
            'source_account_2_token': source_2_token,
            'target_account_token': target_token
        }
    
    return None
