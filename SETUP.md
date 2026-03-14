# Setup Guide

Quick step-by-step guide to get the sync running.

## Prerequisites

- Python 3.7 or higher
- Access to three Qobuz accounts (two source accounts, one target account)
- A web browser (Chrome, Firefox, Edge, Safari)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd ~/qobuz-account-sync
pip install -r requirements.txt
```

Expected output:
```
Successfully installed requests-2.31.0 ...
```

### 2. Extract Tokens (Do this for EACH account)

#### For Source Account 1:

1. **Login**
   - Go to https://play.qobuz.com
   - Login with your first source account credentials
   
2. **Open DevTools**
   - Press `F12` (or right-click → Inspect)
   - Click the **Network** tab
   
3. **Generate Activity**
   - Play any song
   - OR browse to "Favorites" or "Playlists"
   
4. **Export HAR**
   - Right-click anywhere in the Network tab
   - Select **"Save all as HAR with content"**
   - Save as `account1.har` to Downloads folder
   
5. **Extract Token**
   ```bash
   python3 extract_token_from_har.py ~/Downloads/account1.har
   ```
   
6. **Copy Token**
   - You'll see output like:
   ```
   ✅ Found token in: Request cookie: user_auth_token
   
   Token:
   ------------------------------------------------------------
   r6W5xdP3jK9mN2qL7sT8...very_long_string_here...hF4vG2nK
   ------------------------------------------------------------
   ```
   - Copy the entire token (the long string)

#### For Source Account 2:

1. **Logout** from source account 1
2. **Login** with your second source account credentials  
3. Repeat steps 2-6 above
4. Save HAR as `account2.har`
5. Run: `python3 extract_token_from_har.py ~/Downloads/account2.har`
6. Copy the token

#### For Target Account:

1. **Logout** from source account 2
2. **Login** with your target account credentials
3. Repeat steps 2-6 above
4. Save HAR as `target.har`
5. Run: `python3 extract_token_from_har.py ~/Downloads/target.har`
6. Copy the token

### 3. Create credentials.json

Copy the template:
```bash
cp credentials.json.template credentials.json
```

Edit with your tokens:
```bash
nano credentials.json
# or
vim credentials.json
# or use any text editor
```

Replace the placeholder values with your actual tokens:

```json
{
  "source_account_1_token": "r6W5xdP3jK9mN2qL7sT8hF4vG2nK...",
  "source_account_2_token": "a8Hk3mP5jX2nL9rT4sQ1vF7gN6...",
  "target_account_token": "z9Xm4bC7kL2pN5rJ8sV3gT1hF6..."
}
```

**Save and close** the file.

**Security check:**
```bash
git status
```

You should see `credentials.json` is NOT listed (it's gitignored). ✅

### 4. Test Authentication

Run a dry-run to verify tokens work:

```bash
python3 sync.py --dry-run
```

**Expected output:**
```
============================================================
Qobuz Account Sync
============================================================
Log file: logs/sync_20240314_153045.log
Dry run: True
Merge playlists: True

Loading credentials...
✅ Loaded credentials from credentials.json

Initializing Qobuz clients...

Authenticating...
✅ [Source Account 1] Authenticated successfully
✅ [Source Account 2] Authenticated successfully
✅ [Target Account] Authenticated successfully
```

If you see all three ✅ checkmarks, you're ready!

**If authentication fails:**
- Token might be expired - extract a fresh one
- Make sure you were logged in when you exported the HAR
- Double-check you copied the entire token (they're very long!)

### 5. Run Your First Sync

**Dry run first (recommended):**
```bash
python3 sync.py --dry-run
```

This shows what would happen without making changes. Review the output!

**Actual sync:**
```bash
python3 sync.py
```

**What happens:**
1. Fetches all favorites from both source accounts
2. Deduplicates by track ID and ISRC
3. Adds unique tracks to target favorites
4. Fetches all playlists from both source accounts
5. Merges playlists with same name
6. Adds missing tracks to each playlist

**Expected output (first sync):**
```
FAVORITES SYNC SUMMARY
============================================================
Source accounts: 2
Total source favorites: 1,523
Unique tracks (after dedup): 856
Already in target account: 0
Newly favorited: 856
Failed: 0
Coverage: 100.0%

PLAYLISTS SYNC SUMMARY
============================================================
Source accounts: 2
Total source playlists: 47
Playlists created: 35
Playlists updated: 0
Tracks added: 1,247
Tracks skipped (already in playlist): 0
Failed operations: 0

============================================================
SYNC COMPLETE
============================================================
✅ Sync completed successfully!

Log file: logs/sync_20240314_153512.log
```

### 6. Verify in Qobuz

1. Login to the target account at https://play.qobuz.com
2. Check **Favorites** - should see all unique tracks from both source accounts
3. Check **Playlists** - should see all playlists (merged if same name)

## Ongoing Usage

### Regular Syncs

Just run whenever you want to sync new favorites/playlists:

```bash
cd ~/qobuz-account-sync
python3 sync.py
```

Subsequent syncs are **much faster** - only processes new content!

### Automated Syncs (Optional)

Add to cron to sync daily:

```bash
# Edit crontab
crontab -e

# Add line (sync daily at 2 AM):
0 2 * * * cd ~/qobuz-account-sync && python3 sync.py >> logs/cron.log 2>&1
```

### Token Refresh

Tokens eventually expire (days to weeks). When you see authentication errors:

1. Extract fresh tokens using the HAR method (step 2 above)
2. Update `credentials.json` with new tokens
3. Re-run sync

## Troubleshooting

### "Credentials file not found"
- Make sure you created `credentials.json` in the project root
- Check it's not named `credentials.json.txt` (hide file extensions!)

### "Invalid or expired Qobuz token"
- Extract a fresh token using the HAR method
- Make sure you played a song before exporting HAR
- Verify you copied the entire token string

### "No tracks being added"
- Check if they're already in the target account
- Look for "Already in target account" messages - this is expected!
- Add new favorites to one of the source accounts and re-run

### Missing playlist tracks
- Check source account actually has the tracks in that playlist
- Look at the log file in `logs/` for detailed info
- Some tracks might not be available in the target account's region

## Advanced Usage

### Sync favorites only:
```bash
python3 sync.py --favorites-only
```

### Sync playlists only:
```bash
python3 sync.py --playlists-only
```

### Keep playlists separate (don't merge):
```bash
python3 sync.py --no-merge
```

This creates playlists like:
- `[Source Account 1] Workout Mix`
- `[Source Account 2] Workout Mix`

### Verbose logging:
```bash
python3 sync.py --verbose
```

Shows detailed debug information.

## Success!

You should now have:
- ✅ All unique favorites from both source accounts in target account
- ✅ All playlists merged (or kept separate)
- ✅ Automated workflow for future syncs
- ✅ Logs for troubleshooting in `logs/` directory

Check the main README.md for more options and details!
