# Qobuz Account Sync

Sync tracks, albums, artists, and playlists from two source Qobuz accounts into a shared target account. Automatically deduplicates and skips already-synced items.

## ✨ Features

- 🔄 **Sync favorite tracks, albums, and artists** from multiple source accounts to target account
- 🎵 **Sync playlists** with smart merging or keep separate
- 🎯 **Automatic deduplication**
  - tracks: by ID + ISRC
  - albums: by ID + UPC
  - artists: by ID
- 🔐 **Token-based authentication** - works with any Qobuz account type (email, Google, Facebook)
- 🧪 **Dry-run mode** - test before making changes
- 📊 **Detailed reporting** - comprehensive logs of all operations
- 🚀 **Efficient** - skips already-synced content on subsequent runs

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ~/qobuz-account-sync
pip install -r requirements.txt
```

### 2. Get Your Qobuz Tokens

You need authentication tokens for **three accounts**: two source accounts and one target account.

#### Token Extraction Method (HAR File)

For each account:

1. **Login to Qobuz**
   - Open https://play.qobuz.com
   - Login with the account credentials

2. **Open Browser DevTools**
   - Press `F12` or right-click → "Inspect"
   - Go to the **Network** tab

3. **Generate Network Activity**
   - Play a song, or browse playlists/favorites
   - You should see network requests appearing

4. **Export HAR File**
   - Right-click anywhere in the Network tab
   - Select **"Save all as HAR with content"**
   - Save as `account1.har`, `account2.har`, or `target.har`

5. **Extract Token**
   ```bash
   python extract_token_from_har.py account1.har
   ```
   
   This will print the token. Copy it for the next step.

6. **Repeat for all three accounts** (source account 1, source account 2, target account)

### 3. Create credentials.json

Create a file named `credentials.json` in the project root (this file is `.gitignore`d):

```json
{
  "source_account_1_token": "paste_source_account_1_token_here",
  "source_account_2_token": "paste_source_account_2_token_here",
  "target_account_token": "paste_target_account_token_here"
}
```

**Alternative: Environment Variables**

Instead of a credentials file, you can set environment variables:

```bash
export QOBUZ_SOURCE_ACCOUNT_1_TOKEN="your_token"
export QOBUZ_SOURCE_ACCOUNT_2_TOKEN="your_token"
export QOBUZ_TARGET_ACCOUNT_TOKEN="your_token"
```

### 4. Test Authentication

Test that your tokens work:

```bash
# This will verify all three accounts can authenticate
python sync.py --dry-run
```

If authentication succeeds, you'll see:
```
✅ [Source Account 1] Authenticated successfully
✅ [Source Account 2] Authenticated successfully
✅ [Target Account] Authenticated successfully
```

### 5. Run the Sync!

**Dry run first (recommended):**
```bash
python sync.py --dry-run
```

This shows what would be synced without making changes.

**Actual sync:**
```bash
python sync.py
```

That's it! The script will:
- Fetch favorite tracks, albums, and artists from both source accounts
- Deduplicate tracks (ID/ISRC), albums (ID/UPC), and artists (ID)
- Add only missing favorites to the target account
- Fetch all playlists from both source accounts
- Merge playlists with the same name (or keep separate with `--no-merge`)
- Add missing tracks to each playlist

## 📋 Usage Examples

### Basic Sync (Favorites + Playlists)
```bash
# Dry run to see what would happen
python sync.py --dry-run

# Actually sync
python sync.py
```

### Sync Tracks Favorites Only (Backwards Compatible)
```bash
python sync.py --favorites-only
```

### Sync Playlists Only
```bash
python sync.py --playlists-only
```

### Sync Albums Only
```bash
python sync.py --albums-only
```

### Sync Artists Only
```bash
python sync.py --artists-only
```

### Skip Albums and Artists
```bash
python sync.py --skip-albums --skip-artists
```

### Keep Playlists Separate (Don't Merge)
```bash
# Creates playlists like "[Source Account 1] Road Trip" and "[Source Account 2] Road Trip"
python sync.py --no-merge
```

### Custom Credentials File
```bash
python sync.py --credentials my_credentials.json
```

### Verbose Logging
```bash
python sync.py --verbose
```

## 🔄 Running Again (No Duplicates!)

**You can run the sync as many times as you want** - it automatically detects and skips already-synced content:

```bash
python sync.py
```

What happens:
- ✅ Checks which tracks are already favorited in target account
- ✅ Only adds NEW favorites
- ✅ Checks which tracks are in existing playlists
- ✅ Only adds MISSING tracks to playlists
- ✅ Skips all duplicates

Example output:
```
[Target Account] Retrieved 1247 favorite tracks
Found 856 unique tracks across 2 source accounts
Already in target account: 742
Newly favorited: 114
```

## 📊 Command Line Options

```bash
python sync.py [options]

Options:
  --dry-run
      Test mode - shows what would be synced without making changes
      
  --favorites-only
      Only sync favorites, skip playlists
      
  --playlists-only
      Only sync playlists, skip favorites

  --albums-only
      Only sync favorite albums

  --artists-only
      Only sync favorite artists

  --skip-albums
      Skip syncing favorite albums

  --skip-artists
      Skip syncing favorite artists
      
  --no-merge
      Keep playlists separate instead of merging by name.
      Creates "[Source Account 1] Playlist Name" and "[Source Account 2] Playlist Name"
      
  --credentials PATH
      Path to credentials file (default: credentials.json)
      
  --log-file PATH
      Path to log file (default: auto-generated logs/sync_YYYYMMDD_HHMMSS.log)
      
  --verbose
      Enable verbose debug logging
```

## 🎯 How Deduplication Works

### Favorites Deduplication

#### Tracks
1. **Fetch from sources**: Get all favorite tracks from both source accounts
2. **Deduplicate by ID**: If same track ID appears multiple times, keep only one
3. **Deduplicate by ISRC**: If different track IDs have same ISRC code, keep only first
4. **Check target**: See which tracks already exist in target account
5. **Sync unique tracks**: Only add tracks not already in target favorites

#### Albums
1. Fetch favorite albums from all source accounts
2. Deduplicate by album ID, then by UPC where available
3. Skip albums already in target favorites (ID/UPC)

#### Artists
1. Fetch favorite artists from all source accounts
2. Deduplicate by artist ID
3. Skip artists already in target favorites

### Playlist Deduplication

1. **Merge by name** (default): Playlists with the same name from both source accounts are combined
2. **Deduplicate tracks**: Within each playlist, remove duplicates by track ID and ISRC
3. **Update existing**: If playlist already exists in target account, only add missing tracks
4. **Create new**: If playlist doesn't exist, create it with all unique tracks

## 📁 Project Structure

```
qobuz-account-sync/
├── src/
│   ├── __init__.py
│   ├── qobuz_client.py          # Qobuz API client
│   ├── sync_service.py          # Sync orchestration
│   └── utils/
│       ├── __init__.py
│       ├── credentials.py       # Credential parsing
│       └── logger.py            # Logging setup
├── logs/                        # Auto-generated log files
├── sync.py                      # Main sync script
├── extract_token_from_har.py    # HAR token extractor
├── credentials.json             # Your tokens (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

## 🔧 Technical Details

### Authentication

Uses token-based authentication via browser session cookies:
- No app ID or app secret required
- Works with Google/Facebook/email login
- Tokens extracted from HAR file (browser DevTools export)
- Tokens typically last days to weeks

### API Endpoints Used

- `GET /api.json/0.2/favorite/getUserFavorites` - Get favorites
- `POST /api.json/0.2/favorite/create` - Add favorite
- `GET /api.json/0.2/playlist/getUserPlaylists` - List playlists
- `GET /api.json/0.2/playlist/get` - Get playlist tracks
- `POST /api.json/0.2/playlist/create` - Create playlist
- `POST /api.json/0.2/playlist/addTracks` - Add track to playlist

### Rate Limiting

The client includes small delays (50ms) between write operations to avoid rate limiting.

## 🐛 Troubleshooting

### Token Invalid/Expired

```
❌ Invalid or expired Qobuz token for Source Account 1
```

**Solution:** Get a fresh token using the HAR file method (see step 2 above). Tokens typically last days to weeks but do expire.

### Credentials File Not Found

```
❌ Credentials error: Credentials file not found: credentials.json
```

**Solution:** Create `credentials.json` with your three tokens (see step 3 above), or use environment variables.

### Authentication Fails for One Account

**Solution:** 
1. Verify you exported the HAR file while logged into the correct account
2. Make sure you played a song or browsed the library before exporting
3. Extract a fresh token from a new HAR export
4. Update the specific token in `credentials.json`

### Duplicate Playlists Created

If you accidentally created duplicates (e.g., by running with `--no-merge` when you wanted to merge):

1. Manually delete the duplicate playlists in Qobuz web player
2. Next sync will update the remaining playlists (no more duplicates with default merge mode)

### No Tracks Being Added

Check the log output:
- If it says "Already in target account" or "Already in playlist", that's expected behavior
- The sync is working correctly - it's just skipping duplicates
- Add new favorites/tracks to one of the source accounts and re-run to see them sync

## 🔒 Security Notes

- **credentials.json is gitignored** - never committed to repo
- **Tokens are sensitive** - treat like passwords
- Store credentials securely, use environment variables in production
- Tokens provide full account access
- Consider using a separate dedicated target account

## 📈 What to Expect

### First Sync Example

```
FAVORITES SYNC SUMMARY
=============================================================
Source accounts: 2
Total source favorites: 1,523
Unique tracks (after dedup): 856
Already in target account: 0
Newly favorited: 856
Failed: 0
Coverage: 100.0%

PLAYLISTS SYNC SUMMARY
=============================================================
Source accounts: 2
Total source playlists: 47
Playlists created: 35
Playlists updated: 0
Tracks added: 1,247
Tracks skipped (already in playlist): 0
Failed operations: 0
```

### Subsequent Syncs

Much faster! Only processes new content:

```
FAVORITES SYNC SUMMARY
=============================================================
Source accounts: 2
Total source favorites: 1,538
Unique tracks (after dedup): 871
Already in target account: 856
Newly favorited: 15
Failed: 0
Coverage: 100.0%
```

## 🤝 Reference

This project is based on the [spotify2qobuz](https://github.com/lievencardoen/spotify2qobuz) reference implementation, using the same token-based authentication approach for the Qobuz API.

## 📄 License

MIT License - free to use and modify

## 📞 Support

Check the auto-generated log files in `logs/` for detailed information about sync operations and any errors.

---

**Happy Syncing! 🎵 → 🎵 → 🎵**

## 🧪 Testing

This project includes a comprehensive test suite with mocked Qobuz API responses.

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Coverage

- **Unit Tests:** Credentials parsing, QobuzClient, SyncService
- **Integration Tests:** End-to-end sync workflows
- **Mocked API:** All tests run without real Qobuz credentials
- **Coverage Areas:** Authentication, favorites sync, playlists sync, deduplication, error handling

See [TESTING.md](TESTING.md) for detailed testing documentation.
