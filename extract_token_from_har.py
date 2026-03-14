#!/usr/bin/env python3
"""
Extract Qobuz authentication token from HAR file.

Usage:
    python extract_token_from_har.py qobuz.har
    
This will extract the user_auth_token and print it for manual addition to credentials.json
"""

import json
import sys
from pathlib import Path


def extract_token_from_har(har_file_path: str) -> str:
    """
    Extract Qobuz authentication token from HAR file.
    
    Args:
        har_file_path: Path to HAR file
        
    Returns:
        Token string or empty string if not found
    """
    har_path = Path(har_file_path)
    
    if not har_path.exists():
        print(f"❌ HAR file not found: {har_file_path}")
        return ""
    
    try:
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid HAR file (not valid JSON): {e}")
        return ""
    except Exception as e:
        print(f"❌ Error reading HAR file: {e}")
        return ""
    
    print("=" * 60)
    print("Searching for Qobuz Authentication Token")
    print("=" * 60)
    print()
    
    token = None
    found_in = None
    
    # Search through all entries
    entries = har_data.get('log', {}).get('entries', [])
    
    for entry in entries:
        # Check request headers
        if 'request' in entry and 'headers' in entry['request']:
            for header in entry['request']['headers']:
                header_name = header.get('name', '').lower()
                if header_name in ['x-user-auth-token', 'authorization', 'x-auth-token']:
                    token = header.get('value', '')
                    if len(token) > 30:  # Valid tokens are long
                        found_in = f"Request header: {header['name']}"
                        break
        
        # Check request cookies
        if 'request' in entry and 'cookies' in entry['request']:
            for cookie in entry['request']['cookies']:
                cookie_name = cookie.get('name', '').lower()
                if 'user_auth_token' in cookie_name or 'auth' in cookie_name:
                    cookie_value = cookie.get('value', '')
                    if len(cookie_value) > 30:
                        token = cookie_value
                        found_in = f"Request cookie: {cookie['name']}"
                        break
        
        # Check response cookies
        if 'response' in entry and 'cookies' in entry['response']:
            for cookie in entry['response']['cookies']:
                cookie_name = cookie.get('name', '').lower()
                if 'user_auth_token' in cookie_name or 'auth' in cookie_name:
                    cookie_value = cookie.get('value', '')
                    if len(cookie_value) > 30:
                        token = cookie_value
                        found_in = f"Response cookie: {cookie['name']}"
                        break
        
        if token:
            break
    
    if token:
        print(f"✅ Found token in: {found_in}")
        print()
        print("Token:")
        print("-" * 60)
        print(token)
        print("-" * 60)
        print()
        print("Add this to your credentials.json file:")
        print()
        print(f'  "your_account_token": "{token}"')
        print()
        return token
    else:
        print("❌ Could not find authentication token in HAR file")
        print()
        print("This might mean:")
        print("  - You weren't fully logged in when you exported the HAR")
        print("  - The token is stored differently than expected")
        print()
        print("Please ensure you:")
        print("  1. Logged into https://play.qobuz.com")
        print("  2. Played a song or browsed your library")
        print("  3. Then exported the HAR file from DevTools → Network tab")
        print()
        return ""


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_token_from_har.py <har_file>")
        print()
        print("Example:")
        print("  python extract_token_from_har.py qobuz.har")
        print()
        print("How to get a HAR file:")
        print("  1. Open https://play.qobuz.com and login")
        print("  2. Open DevTools (F12) → Network tab")
        print("  3. Play a song or browse your playlists")
        print("  4. Right-click in Network tab → 'Save all as HAR with content'")
        print("  5. Save as qobuz.har")
        sys.exit(1)
    
    har_file = sys.argv[1]
    token = extract_token_from_har(har_file)
    
    if token:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
