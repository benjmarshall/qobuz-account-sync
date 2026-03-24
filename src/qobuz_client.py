"""
Qobuz API client using token-based authentication.

Based on spotify2qobuz reference implementation.
"""

from typing import Dict, List, Optional
import requests
import time
from src.utils.logger import get_logger


logger = get_logger()


class QobuzClient:
    """
    Client for interacting with Qobuz API using session token authentication.
    
    Get your token from browser cookies after logging in to https://play.qobuz.com
    """
    
    BASE_URL = "https://www.qobuz.com/api.json/0.2"
    
    def __init__(self, user_auth_token: str, account_name: str = "Qobuz"):
        """
        Initialize Qobuz client with session token.
        
        Args:
            user_auth_token: Session token from browser cookies
            account_name: Friendly name for this account (for logging)
        """
        self.user_auth_token = user_auth_token
        self.account_name = account_name
        self.user_id: Optional[int] = None
        self.user_name: Optional[str] = None
        
        # Create session with required headers
        self._session = requests.Session()
        self._session.headers.update({
            "X-App-Id": "798273057",  # App ID used by web player
            "X-User-Auth-Token": self.user_auth_token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Origin": "https://play.qobuz.com",
            "Referer": "https://play.qobuz.com/",
        })
    
    def authenticate(self) -> None:
        """
        Validate the session token by fetching user info.
        
        Raises:
            Exception: If token is invalid or expired
        """
        try:
            url = f"{self.BASE_URL}/favorite/getUserFavorites"
            params = {"type": "albums", "limit": 1}
            
            response = self._session.get(url, params=params, timeout=10)
            
            if response.status_code in [401, 400]:
                logger.error(f"[{self.account_name}] Token validation failed with status {response.status_code}")
                raise Exception(f"Invalid or expired Qobuz token for {self.account_name}")
            
            response.raise_for_status()
            data = response.json()
            
            if 'user' in data and 'id' in data['user']:
                self.user_id = data['user']['id']
                self.user_name = data['user'].get('display_name', self.account_name)
            else:
                self.user_id = 1
                self.user_name = self.account_name
            
            logger.info(f"✅ [{self.account_name}] Authenticated successfully as {self.user_name}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.account_name}] Network error during authentication: {e}")
            raise Exception(f"Authentication failed for {self.account_name}: {e}")
    
    def _make_request(self, endpoint: str, params: Dict = None, method: str = "GET") -> Dict:
        """
        Make authenticated request to Qobuz API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters or request body
            method: HTTP method (GET or POST)
        
        Returns:
            Response JSON
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            if method == "GET":
                response = self._session.get(url, params=params, timeout=10)
            else:  # POST
                response = self._session.post(url, data=params, timeout=10)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.account_name}] API request failed for {endpoint}: {e}")
            raise Exception(f"API request failed: {e}")
    
    def get_favorite_tracks(self, limit: int = 5000) -> List[Dict]:
        """
        Get all favorite/liked tracks for the authenticated user.
        
        Args:
            limit: Maximum number of favorites to retrieve
        
        Returns:
            List of track dictionaries with id, title, artist, album, isrc
        """
        try:
            url = f"{self.BASE_URL}/favorite/getUserFavorites"
            params = {"type": "tracks", "limit": limit, "offset": 0}
            
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            tracks = []
            
            if 'tracks' in data and 'items' in data['tracks']:
                for item in data['tracks']['items']:
                    track = {
                        'id': item['id'],
                        'title': item.get('title', 'Unknown'),
                        'artist': item.get('performer', {}).get('name', 'Unknown'),
                        'album': item.get('album', {}).get('title', 'Unknown'),
                        'isrc': item.get('isrc', ''),
                        'duration': item.get('duration', 0)
                    }
                    tracks.append(track)
            
            logger.info(f"[{self.account_name}] Retrieved {len(tracks)} favorite tracks")
            return tracks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.account_name}] Failed to get favorite tracks: {e}")
            raise Exception(f"Failed to get favorite tracks: {e}")
    
    def add_favorite_track(self, track_id: int) -> bool:
        """
        Add a track to user's favorites.
        
        Args:
            track_id: Qobuz track ID to favorite
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/favorite/create"
            params = {"track_ids": str(track_id)}
            
            response = self._session.post(url, data=params, timeout=10)
            
            # 400 means already favorited, which is fine
            if response.status_code == 400:
                logger.debug(f"[{self.account_name}] Track {track_id} already favorited")
                return True
            
            response.raise_for_status()
            logger.debug(f"[{self.account_name}] Added track {track_id} to favorites")
            
            # Small delay to avoid rate limiting
            time.sleep(0.05)
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.account_name}] Failed to add track {track_id}: {e}")
            return False

    def get_favorite_albums(self, limit: int = 5000) -> List[Dict]:
        """Get all favorite albums for the authenticated user."""
        try:
            url = f"{self.BASE_URL}/favorite/getUserFavorites"
            params = {"type": "albums", "limit": limit, "offset": 0}

            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            albums = []

            if 'albums' in data and 'items' in data['albums']:
                for item in data['albums']['items']:
                    albums.append({
                        'id': item['id'],
                        'title': item.get('title', 'Unknown'),
                        'artist': item.get('artist', {}).get('name', 'Unknown'),
                        'upc': item.get('upc', ''),
                        'release_date': item.get('release_date_original', '')
                    })

            logger.info(f"[{self.account_name}] Retrieved {len(albums)} favorite albums")
            return albums

        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.account_name}] Failed to get favorite albums: {e}")
            raise Exception(f"Failed to get favorite albums: {e}")

    def add_favorite_album(self, album_id: int) -> bool:
        """Add an album to user's favorites."""
        try:
            url = f"{self.BASE_URL}/favorite/create"
            params = {"album_ids": str(album_id)}

            response = self._session.post(url, data=params, timeout=10)

            if response.status_code == 400:
                logger.debug(f"[{self.account_name}] Album {album_id} already favorited")
                return True

            response.raise_for_status()
            logger.debug(f"[{self.account_name}] Added album {album_id} to favorites")
            time.sleep(0.05)
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.account_name}] Failed to add album {album_id}: {e}")
            return False

    def get_favorite_artists(self, limit: int = 5000) -> List[Dict]:
        """Get all favorite artists for the authenticated user."""
        try:
            url = f"{self.BASE_URL}/favorite/getUserFavorites"
            params = {"type": "artists", "limit": limit, "offset": 0}

            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            artists = []

            if 'artists' in data and 'items' in data['artists']:
                for item in data['artists']['items']:
                    artists.append({
                        'id': item['id'],
                        'name': item.get('name', 'Unknown')
                    })

            logger.info(f"[{self.account_name}] Retrieved {len(artists)} favorite artists")
            return artists

        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.account_name}] Failed to get favorite artists: {e}")
            raise Exception(f"Failed to get favorite artists: {e}")

    def add_favorite_artist(self, artist_id: int) -> bool:
        """Add an artist to user's favorites."""
        try:
            url = f"{self.BASE_URL}/favorite/create"
            params = {"artist_ids": str(artist_id)}

            response = self._session.post(url, data=params, timeout=10)

            if response.status_code == 400:
                logger.debug(f"[{self.account_name}] Artist {artist_id} already favorited")
                return True

            response.raise_for_status()
            logger.debug(f"[{self.account_name}] Added artist {artist_id} to favorites")
            time.sleep(0.05)
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.account_name}] Failed to add artist {artist_id}: {e}")
            return False
    
    def list_user_playlists(self) -> List[Dict]:
        """
        Get all user playlists.
        
        Returns:
            List of playlist dictionaries with id, name, tracks_count
        """
        try:
            params = {'limit': 500}
            data = self._make_request('playlist/getUserPlaylists', params)
            
            playlists = []
            if data.get('playlists', {}).get('items'):
                for item in data['playlists']['items']:
                    playlists.append({
                        'id': str(item['id']),
                        'name': item['name'],
                        'tracks_count': item.get('tracks_count', 0),
                        'description': item.get('description', '')
                    })
                    
            logger.info(f"[{self.account_name}] Found {len(playlists)} playlists")
            return playlists
            
        except Exception as e:
            logger.error(f"[{self.account_name}] Error listing playlists: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """
        Get all tracks in a playlist with full metadata.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            List of track dictionaries with id, title, artist, album, isrc
        """
        try:
            params = {'playlist_id': playlist_id}
            data = self._make_request('playlist/get', params)
            
            tracks = []
            if data and 'tracks' in data and 'items' in data['tracks']:
                for item in data['tracks']['items']:
                    track = {
                        'id': item['id'],
                        'title': item.get('title', 'Unknown'),
                        'artist': item.get('performer', {}).get('name', 'Unknown'),
                        'album': item.get('album', {}).get('title', 'Unknown'),
                        'isrc': item.get('isrc', ''),
                        'duration': item.get('duration', 0)
                    }
                    tracks.append(track)
            
            logger.debug(f"[{self.account_name}] Retrieved {len(tracks)} tracks from playlist {playlist_id}")
            return tracks
            
        except Exception as e:
            logger.error(f"[{self.account_name}] Error getting playlist tracks: {e}")
            return []
    
    def create_playlist(self, name: str, description: str = "") -> Optional[str]:
        """
        Create a new playlist.
        
        Args:
            name: Playlist name
            description: Playlist description
        
        Returns:
            Playlist ID or None if creation fails
        """
        try:
            url = f"{self.BASE_URL}/playlist/create"
            
            data = {
                'name': name,
                'is_public': 'false',
                'is_collaborative': 'false'
            }
            
            if description:
                data['description'] = description
            
            response = self._session.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            playlist_id = str(result['id'])
            
            logger.info(f"[{self.account_name}] Created playlist: {name} (ID: {playlist_id})")
            return playlist_id
            
        except Exception as e:
            logger.error(f"[{self.account_name}] Error creating playlist {name}: {e}")
            return None
    
    def add_track_to_playlist(self, playlist_id: str, track_id: int) -> bool:
        """
        Add a track to a playlist.
        
        Args:
            playlist_id: Playlist ID
            track_id: Track ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/playlist/addTracks"
            data = {
                'playlist_id': playlist_id,
                'track_ids': str(track_id)
            }
            
            response = self._session.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.debug(f"[{self.account_name}] Added track {track_id} to playlist {playlist_id}")
            
            # Small delay to avoid rate limiting
            time.sleep(0.05)
            return True
            
        except Exception as e:
            logger.error(f"[{self.account_name}] Error adding track {track_id} to playlist: {e}")
            return False
    
    def find_playlist_by_name(self, name: str) -> Optional[Dict]:
        """
        Find a playlist by exact name match.
        
        Args:
            name: Playlist name to search for
            
        Returns:
            Playlist dict or None if not found
        """
        playlists = self.list_user_playlists()
        for playlist in playlists:
            if playlist['name'] == name:
                logger.debug(f"[{self.account_name}] Found playlist: {name} (ID: {playlist['id']})")
                return playlist
        return None
