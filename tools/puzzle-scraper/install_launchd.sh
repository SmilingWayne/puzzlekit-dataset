#!/bin/zsh
# Install / update the launchd LaunchAgent for daily puzzle scrapes (09:00/19:00).
#
# macOS TCC blocks launchd-spawned processes from reading ~/Desktop, so the
# job is launched through a tiny helper .app bundle kept at a stable path:
#     ~/Library/Application Support/PuzzleKit/puzzle-scraper.app
# Grant that app "Full Disk Access" once in System Settings (Privacy &
# Security -> Full Disk Access). The grant survives reinstalls as long as the
# bundle path stays the same.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LABEL="com.puzzlekit.puzzle-scraper"
OLD_LABEL="com.puzzlekit.masyu-scraper"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$REPO_ROOT/tools/puzzle-scraper/logs"
HELPER_APP="$HOME/Library/Application Support/PuzzleKit/puzzle-scraper.app"
OLD_HELPER_APP="$HOME/Library/Application Support/PuzzleKit/masyu-scraper.app"
HELPER_BIN="$HELPER_APP/Contents/MacOS/puzzle-scraper-helper"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

mkdir -p "$HELPER_APP/Contents/MacOS"
cp "$REPO_ROOT/tools/puzzle-scraper/helper_app/Info.plist" "$HELPER_APP/Contents/Info.plist"
cc -O2 -o "$HELPER_BIN" "$REPO_ROOT/tools/puzzle-scraper/helper_app/helper.c"
codesign -f -s - "$HELPER_APP" 2>/dev/null || true

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HELPER_BIN</string>
        <string>$REPO_ROOT/tools/puzzle-scraper/run_daily.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>9</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>19</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/daily.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/daily.err.log</string>
    <key>WorkingDirectory</key>
    <string>$REPO_ROOT</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$OLD_LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$OLD_LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
if [[ -d "$OLD_HELPER_APP" ]]; then
    rm -rf "$OLD_HELPER_APP"
    echo "Removed legacy helper: $OLD_HELPER_APP"
fi
echo "Installed: $PLIST"
echo "Helper app: $HELPER_APP"
echo ""
echo "One-time step: grant puzzle-scraper.app Full Disk Access in"
echo "  System Settings -> Privacy & Security -> Full Disk Access -> +"
echo "  (Cmd+Shift+G and paste: $HOME/Library/Application Support/PuzzleKit/)"
echo "  Select puzzle-scraper.app and enable it."
echo "  If masyu-scraper.app is still listed, remove it (legacy)."
echo ""
echo "then run: launchctl kickstart gui/$(id -u)/$LABEL"
launchctl list | grep "$LABEL" || echo "job not visible in launchctl list"
