"""Service for syncing favorites and playlists across Qobuz accounts."""

from typing import Dict, List, Set
from src.qobuz_client import QobuzClient
from src.utils.logger import get_logger


logger = get_logger()


class QobuzSyncService:
    """Service for syncing favorites and playlists from multiple Qobuz accounts to a target account."""

    def __init__(self, source_clients: List[QobuzClient], target_client: QobuzClient):
        self.source_clients = source_clients
        self.target_client = target_client

    def sync_favorites(self, dry_run: bool = False) -> Dict:
        """Sync favorite tracks from all source accounts to target account."""
        logger.info("=" * 60)
        logger.info("Starting favorites sync")
        logger.info("=" * 60)

        stats = {
            'source_accounts': len(self.source_clients),
            'total_source_favorites': 0,
            'unique_tracks': 0,
            'already_favorited': 0,
            'newly_favorited': 0,
            'failed': 0
        }

        unique_tracks: Dict[int, Dict] = {}
        seen_isrcs: Set[str] = set()

        for source_client in self.source_clients:
            logger.info(f"\nFetching favorites from {source_client.account_name}...")
            source_favorites = source_client.get_favorite_tracks()
            stats['total_source_favorites'] += len(source_favorites)

            for track in source_favorites:
                track_id = track['id']
                isrc = track['isrc'].upper() if track.get('isrc') else ''

                if track_id in unique_tracks:
                    continue
                if isrc and isrc in seen_isrcs:
                    logger.debug(f"Skipping duplicate ISRC: {track['title']} by {track['artist']}")
                    continue

                unique_tracks[track_id] = track
                if isrc:
                    seen_isrcs.add(isrc)

        logger.info(f"Fetching existing favorites from target account ({self.target_client.account_name})...")
        target_favorites = self.target_client.get_favorite_tracks()
        target_track_ids = {track['id'] for track in target_favorites}
        target_isrcs = {track['isrc'].upper() for track in target_favorites if track.get('isrc')}
        logger.info(f"Target account has {len(target_favorites)} existing favorites")

        stats['unique_tracks'] = len(unique_tracks)
        logger.info(f"\nFound {stats['unique_tracks']} unique tracks across {stats['source_accounts']} source accounts")
        logger.info(f"Total source favorites: {stats['total_source_favorites']}")

        logger.info(f"\nSyncing to target account ({self.target_client.account_name})...")
        for i, (track_id, track) in enumerate(unique_tracks.items(), 1):
            isrc = track['isrc'].upper() if track.get('isrc') else ''

            already_exists = track_id in target_track_ids
            if not already_exists and isrc:
                already_exists = isrc in target_isrcs

            if already_exists:
                stats['already_favorited'] += 1
                continue

            if dry_run:
                logger.info(f"[{i}/{stats['unique_tracks']}] [DRY RUN] Would favorite: {track['title']} by {track['artist']}")
                stats['newly_favorited'] += 1
            else:
                success = self.target_client.add_favorite_track(track_id)
                if success:
                    logger.info(f"[{i}/{stats['unique_tracks']}] ✅ Favorited: {track['title']} by {track['artist']}")
                    stats['newly_favorited'] += 1
                    target_track_ids.add(track_id)
                    if isrc:
                        target_isrcs.add(isrc)
                else:
                    stats['failed'] += 1

        logger.info("\n" + "=" * 60)
        logger.info("FAVORITES SYNC SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Source accounts: {stats['source_accounts']}")
        logger.info(f"Total source favorites: {stats['total_source_favorites']}")
        logger.info(f"Unique tracks (after dedup): {stats['unique_tracks']}")
        logger.info(f"Already in target account: {stats['already_favorited']}")
        logger.info(f"Newly favorited: {stats['newly_favorited']}")
        logger.info(f"Failed: {stats['failed']}")
        if stats['unique_tracks'] > 0:
            coverage = ((stats['already_favorited'] + stats['newly_favorited']) / stats['unique_tracks']) * 100
            logger.info(f"Coverage: {coverage:.1f}%")
        logger.info("=" * 60)

        return stats

    def sync_albums(self, dry_run: bool = False) -> Dict:
        """Sync favorite albums from all source accounts to target account."""
        logger.info("=" * 60)
        logger.info("Starting albums sync")
        logger.info("=" * 60)

        stats = {
            'source_accounts': len(self.source_clients),
            'total_source_albums': 0,
            'unique_albums': 0,
            'already_favorited': 0,
            'newly_favorited': 0,
            'failed': 0
        }

        unique_albums: Dict[int, Dict] = {}
        seen_upcs: Set[str] = set()

        for source_client in self.source_clients:
            logger.info(f"\nFetching favorite albums from {source_client.account_name}...")
            source_albums = source_client.get_favorite_albums()
            stats['total_source_albums'] += len(source_albums)
            for album in source_albums:
                album_id = album['id']
                upc = album.get('upc', '').upper()
                if album_id in unique_albums:
                    continue
                if upc and upc in seen_upcs:
                    continue
                unique_albums[album_id] = album
                if upc:
                    seen_upcs.add(upc)

        logger.info(f"Fetching existing albums from target account ({self.target_client.account_name})...")
        target_albums = self.target_client.get_favorite_albums()
        target_album_ids = {album['id'] for album in target_albums}
        target_upcs = {album['upc'].upper() for album in target_albums if album.get('upc')}
        logger.info(f"Target account has {len(target_albums)} existing favorite albums")

        stats['unique_albums'] = len(unique_albums)
        logger.info(f"\nFound {stats['unique_albums']} unique albums across {stats['source_accounts']} source accounts")
        logger.info(f"Total source albums: {stats['total_source_albums']}")

        logger.info(f"\nSyncing to target account ({self.target_client.account_name})...")
        for i, (album_id, album) in enumerate(unique_albums.items(), 1):
            upc = album.get('upc', '').upper()
            album_title = album.get('title', f"Album ID {album_id}")
            artist_name = album.get('artist', 'Unknown artist')

            already_exists = album_id in target_album_ids
            if not already_exists and upc:
                already_exists = upc in target_upcs

            if already_exists:
                logger.info(f"[{i}/{stats['unique_albums']}] ⏭️ Already favorited: {album_title} by {artist_name}")
                stats['already_favorited'] += 1
                continue

            if dry_run:
                logger.info(f"[{i}/{stats['unique_albums']}] [DRY RUN] Would favorite album: {album_title} by {artist_name}")
                stats['newly_favorited'] += 1
            else:
                if self.target_client.add_favorite_album(album_id):
                    logger.info(f"[{i}/{stats['unique_albums']}] ✅ Favorited album: {album_title} by {artist_name}")
                    stats['newly_favorited'] += 1
                    target_album_ids.add(album_id)
                    if upc:
                        target_upcs.add(upc)
                else:
                    logger.warning(f"[{i}/{stats['unique_albums']}] ❌ Failed to favorite album: {album_title} by {artist_name}")
                    stats['failed'] += 1

        logger.info("\n" + "=" * 60)
        logger.info("ALBUMS SYNC SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Source accounts: {stats['source_accounts']}")
        logger.info(f"Total source albums: {stats['total_source_albums']}")
        logger.info(f"Unique albums (after dedup): {stats['unique_albums']}")
        logger.info(f"Already in target account: {stats['already_favorited']}")
        logger.info(f"Newly favorited: {stats['newly_favorited']}")
        logger.info(f"Failed: {stats['failed']}")
        if stats['unique_albums'] > 0:
            coverage = ((stats['already_favorited'] + stats['newly_favorited']) / stats['unique_albums']) * 100
            logger.info(f"Coverage: {coverage:.1f}%")
        logger.info("=" * 60)

        return stats

    def sync_artists(self, dry_run: bool = False) -> Dict:
        """Sync favorite artists from all source accounts to target account."""
        logger.info("=" * 60)
        logger.info("Starting artists sync")
        logger.info("=" * 60)

        stats = {
            'source_accounts': len(self.source_clients),
            'total_source_artists': 0,
            'unique_artists': 0,
            'already_favorited': 0,
            'newly_favorited': 0,
            'failed': 0
        }

        unique_artists: Dict[int, Dict] = {}
        for source_client in self.source_clients:
            logger.info(f"\nFetching favorite artists from {source_client.account_name}...")
            source_artists = source_client.get_favorite_artists()
            stats['total_source_artists'] += len(source_artists)
            for artist in source_artists:
                unique_artists.setdefault(artist['id'], artist)

        logger.info(f"Fetching existing artists from target account ({self.target_client.account_name})...")
        target_artists = self.target_client.get_favorite_artists()
        target_artist_ids = {artist['id'] for artist in target_artists}
        logger.info(f"Target account has {len(target_artists)} existing favorite artists")

        stats['unique_artists'] = len(unique_artists)
        logger.info(f"\nFound {stats['unique_artists']} unique artists across {stats['source_accounts']} source accounts")
        logger.info(f"Total source artists: {stats['total_source_artists']}")

        logger.info(f"\nSyncing to target account ({self.target_client.account_name})...")
        for i, (artist_id, artist) in enumerate(unique_artists.items(), 1):
            artist_name = artist.get('name', f"Artist ID {artist_id}")

            if artist_id in target_artist_ids:
                logger.info(f"[{i}/{stats['unique_artists']}] ⏭️ Already favorited: {artist_name}")
                stats['already_favorited'] += 1
                continue

            if dry_run:
                logger.info(f"[{i}/{stats['unique_artists']}] [DRY RUN] Would favorite artist: {artist_name}")
                stats['newly_favorited'] += 1
            else:
                if self.target_client.add_favorite_artist(artist_id):
                    logger.info(f"[{i}/{stats['unique_artists']}] ✅ Favorited artist: {artist_name}")
                    stats['newly_favorited'] += 1
                    target_artist_ids.add(artist_id)
                else:
                    logger.warning(f"[{i}/{stats['unique_artists']}] ❌ Failed to favorite artist: {artist_name}")
                    stats['failed'] += 1

        logger.info("\n" + "=" * 60)
        logger.info("ARTISTS SYNC SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Source accounts: {stats['source_accounts']}")
        logger.info(f"Total source artists: {stats['total_source_artists']}")
        logger.info(f"Unique artists (after dedup): {stats['unique_artists']}")
        logger.info(f"Already in target account: {stats['already_favorited']}")
        logger.info(f"Newly favorited: {stats['newly_favorited']}")
        logger.info(f"Failed: {stats['failed']}")
        if stats['unique_artists'] > 0:
            coverage = ((stats['already_favorited'] + stats['newly_favorited']) / stats['unique_artists']) * 100
            logger.info(f"Coverage: {coverage:.1f}%")
        logger.info("=" * 60)

        return stats

    def sync_playlists(self, dry_run: bool = False, merge_playlists: bool = True) -> Dict:
        """Sync playlists from all source accounts to target account."""
        logger.info("=" * 60)
        logger.info("Starting playlists sync")
        logger.info("=" * 60)

        stats = {
            'source_accounts': len(self.source_clients),
            'total_source_playlists': 0,
            'playlists_created': 0,
            'playlists_updated': 0,
            'tracks_added': 0,
            'tracks_skipped': 0,
            'failed': 0
        }

        source_playlists: Dict[str, List[Dict]] = {}
        for source_client in self.source_clients:
            logger.info(f"\nFetching playlists from {source_client.account_name}...")
            playlists = source_client.list_user_playlists()
            stats['total_source_playlists'] += len(playlists)

            for playlist in playlists:
                name = playlist['name']
                if merge_playlists:
                    source_playlists.setdefault(name, []).append({'client': source_client, 'playlist': playlist})
                else:
                    prefixed_name = f"[{source_client.account_name}] {name}"
                    source_playlists[prefixed_name] = [{'client': source_client, 'playlist': playlist}]

        target_playlists = None

        logger.info(f"\nFound {len(source_playlists)} unique playlist names to sync")

        for playlist_name, playlist_sources in source_playlists.items():
            all_tracks: Dict[int, Dict] = {}
            seen_isrcs: Set[str] = set()

            for source_info in playlist_sources:
                source_client = source_info['client']
                source_playlist = source_info['playlist']
                tracks = source_client.get_playlist_tracks(source_playlist['id'])

                for track in tracks:
                    track_id = track['id']
                    isrc = track['isrc'].upper() if track.get('isrc') else ''
                    if track_id in all_tracks:
                        continue
                    if isrc and isrc in seen_isrcs:
                        continue
                    all_tracks[track_id] = track
                    if isrc:
                        seen_isrcs.add(isrc)

            if target_playlists is None:
                logger.info(f"Fetching existing playlists from target account ({self.target_client.account_name})...")
                target_playlists = {p['name']: p for p in self.target_client.list_user_playlists()}

            if playlist_name in target_playlists:
                target_playlist_id = target_playlists[playlist_name]['id']
                existing_tracks = self.target_client.get_playlist_tracks(target_playlist_id)
                existing_track_ids = {t['id'] for t in existing_tracks}
                existing_isrcs = {t['isrc'].upper() for t in existing_tracks if t.get('isrc')}
                stats['playlists_updated'] += 1
            else:
                if dry_run:
                    target_playlist_id = "DRY_RUN_ID"
                    existing_track_ids = set()
                    existing_isrcs = set()
                    stats['playlists_created'] += 1
                else:
                    description = f"Synced from {', '.join([s['client'].account_name for s in playlist_sources])}"
                    target_playlist_id = self.target_client.create_playlist(playlist_name, description)
                    if not target_playlist_id:
                        stats['failed'] += 1
                        continue
                    existing_track_ids = set()
                    existing_isrcs = set()
                    stats['playlists_created'] += 1

            for track_id, track in all_tracks.items():
                isrc = track['isrc'].upper() if track.get('isrc') else ''
                already_exists = track_id in existing_track_ids or (isrc and isrc in existing_isrcs)

                if already_exists:
                    stats['tracks_skipped'] += 1
                    continue

                if dry_run:
                    stats['tracks_added'] += 1
                else:
                    if self.target_client.add_track_to_playlist(target_playlist_id, track_id):
                        stats['tracks_added'] += 1
                        existing_track_ids.add(track_id)
                        if isrc:
                            existing_isrcs.add(isrc)
                    else:
                        stats['failed'] += 1

        logger.info("\n" + "=" * 60)
        logger.info("PLAYLISTS SYNC SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Source accounts: {stats['source_accounts']}")
        logger.info(f"Total source playlists: {stats['total_source_playlists']}")
        logger.info(f"Playlists created: {stats['playlists_created']}")
        logger.info(f"Playlists updated: {stats['playlists_updated']}")
        logger.info(f"Tracks added: {stats['tracks_added']}")
        logger.info(f"Tracks skipped (already in playlist): {stats['tracks_skipped']}")
        logger.info(f"Failed operations: {stats['failed']}")
        logger.info("=" * 60)

        return stats
