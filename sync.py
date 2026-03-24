#!/usr/bin/env python3
"""
Qobuz Account Sync - Main sync script

Syncs favorites and playlists from multiple source Qobuz accounts to a target account.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from src.qobuz_client import QobuzClient
from src.sync_service import QobuzSyncService
from src.utils.credentials import parse_credentials, load_credentials_from_env, CredentialsError
from src.utils.logger import setup_logger


def main():
    parser = argparse.ArgumentParser(
        description='Sync Qobuz favorites and playlists from multiple source accounts to target account'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate sync without making changes'
    )
    parser.add_argument(
        '--favorites-only',
        action='store_true',
        help='Only sync favorites, skip playlists'
    )
    parser.add_argument(
        '--playlists-only',
        action='store_true',
        help='Only sync playlists, skip favorites'
    )
    parser.add_argument(
        '--albums-only',
        action='store_true',
        help='Only sync favorite albums'
    )
    parser.add_argument(
        '--artists-only',
        action='store_true',
        help='Only sync favorite artists'
    )
    parser.add_argument(
        '--skip-albums',
        action='store_true',
        help='Skip syncing favorite albums'
    )
    parser.add_argument(
        '--skip-artists',
        action='store_true',
        help='Skip syncing favorite artists'
    )
    parser.add_argument(
        '--no-merge',
        action='store_true',
        help='Keep playlists separate instead of merging by name'
    )
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to credentials file (default: credentials.json)'
    )
    parser.add_argument(
        '--log-file',
        help='Path to log file (default: auto-generated in logs/)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()

    only_flags = [args.favorites_only, args.playlists_only, args.albums_only, args.artists_only]
    if sum(1 for flag in only_flags if flag) > 1:
        parser.error("Only one of --favorites-only, --playlists-only, --albums-only, --artists-only can be used at a time")

    sync_tracks = True
    sync_playlists = True
    sync_albums = not args.skip_albums
    sync_artists = not args.skip_artists

    if args.favorites_only:
        sync_tracks = True
        sync_playlists = False
        sync_albums = False
        sync_artists = False
    elif args.playlists_only:
        sync_tracks = False
        sync_playlists = True
        sync_albums = False
        sync_artists = False
    elif args.albums_only:
        sync_tracks = False
        sync_playlists = False
        sync_albums = True
        sync_artists = False
    elif args.artists_only:
        sync_tracks = False
        sync_playlists = False
        sync_albums = False
        sync_artists = True
    
    # Set up logging
    if args.log_file:
        log_file = args.log_file
    else:
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'sync_{timestamp}.log'
    
    log_level = 'DEBUG' if args.verbose else 'INFO'
    import logging
    logger = setup_logger('qobuz_sync', str(log_file), getattr(logging, log_level))
    
    logger.info("=" * 60)
    logger.info("Qobuz Account Sync")
    logger.info("=" * 60)
    logger.info(f"Log file: {log_file}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Merge playlists: {not args.no_merge}")
    logger.info(f"Sync tracks: {sync_tracks}")
    logger.info(f"Sync playlists: {sync_playlists}")
    logger.info(f"Sync albums: {sync_albums}")
    logger.info(f"Sync artists: {sync_artists}")
    
    try:
        # Load credentials
        logger.info("\nLoading credentials...")
        
        # Try environment variables first
        credentials = load_credentials_from_env()
        if credentials:
            logger.info("✅ Loaded credentials from environment variables")
        else:
            # Fall back to credentials file
            credentials = parse_credentials(args.credentials)
            logger.info(f"✅ Loaded credentials from {args.credentials}")
        
        # Initialize clients
        logger.info("\nInitializing Qobuz clients...")
        
        source_1_client = QobuzClient(credentials['source_account_1_token'], "Source Account 1")
        source_2_client = QobuzClient(credentials['source_account_2_token'], "Source Account 2")
        target_client = QobuzClient(credentials['target_account_token'], "Target Account")
        
        # Authenticate all clients
        logger.info("\nAuthenticating...")
        source_1_client.authenticate()
        source_2_client.authenticate()
        target_client.authenticate()
        
        # Create sync service
        source_clients = [source_1_client, source_2_client]
        sync_service = QobuzSyncService(source_clients, target_client)
        
        run_stats = {}

        # Sync tracks favorites
        if sync_tracks:
            logger.info("\n")
            run_stats['tracks'] = sync_service.sync_favorites(dry_run=args.dry_run)

        # Sync favorite albums
        if sync_albums:
            logger.info("\n")
            run_stats['albums'] = sync_service.sync_albums(dry_run=args.dry_run)

        # Sync favorite artists
        if sync_artists:
            logger.info("\n")
            run_stats['artists'] = sync_service.sync_artists(dry_run=args.dry_run)

        # Sync playlists
        if sync_playlists:
            logger.info("\n")
            run_stats['playlists'] = sync_service.sync_playlists(
                dry_run=args.dry_run,
                merge_playlists=not args.no_merge
            )
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("SYNC COMPLETE")
        logger.info("=" * 60)
        
        if args.dry_run:
            logger.info("This was a DRY RUN - no changes were made")
            logger.info("Run without --dry-run to actually sync")
        else:
            logger.info("✅ Sync completed successfully!")

        if 'tracks' in run_stats:
            logger.info(f"Tracks: +{run_stats['tracks']['newly_favorited']} new, {run_stats['tracks']['already_favorited']} already in target")
        if 'albums' in run_stats:
            logger.info(f"Albums: +{run_stats['albums']['newly_favorited']} new, {run_stats['albums']['already_favorited']} already in target")
        if 'artists' in run_stats:
            logger.info(f"Artists: +{run_stats['artists']['newly_favorited']} new, {run_stats['artists']['already_favorited']} already in target")
        if 'playlists' in run_stats:
            logger.info(f"Playlists: {run_stats['playlists']['playlists_created']} created, {run_stats['playlists']['playlists_updated']} updated, {run_stats['playlists']['tracks_added']} tracks added")
        
        logger.info(f"\nLog file: {log_file}")
        
        return 0
        
    except CredentialsError as e:
        logger.error(f"\n❌ Credentials error: {e}")
        logger.error("\nPlease ensure credentials.json exists with the following format:")
        logger.error('''{
  "source_account_1_token": "your_token_here",
  "source_account_2_token": "your_token_here",
  "target_account_token": "your_token_here"
}''')
        logger.error("\nOr set environment variables:")
        logger.error("  QOBUZ_SOURCE_ACCOUNT_1_TOKEN")
        logger.error("  QOBUZ_SOURCE_ACCOUNT_2_TOKEN")
        logger.error("  QOBUZ_TARGET_ACCOUNT_TOKEN")
        return 1
        
    except Exception as e:
        logger.error(f"\n❌ Sync failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
