#!/bin/zsh
set -euo pipefail
WORKDIR="/Users/ladorezr/.openclaw/workspace"
SKILLDIR="$WORKDIR/skills/paper-radar"
PLIST="$HOME/Library/LaunchAgents/ai.openclaw.paper-radar.daily.plist"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>ai.openclaw.paper-radar.daily</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$SKILLDIR/scripts/build_site.py</string>
  </array>
  <key>WorkingDirectory</key><string>$WORKDIR</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>8</integer>
    <key>Minute</key><integer>30</integer>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$SKILLDIR/output/launchd.log</string>
  <key>StandardErrorPath</key><string>$SKILLDIR/output/launchd.err.log</string>
</dict>
</plist>
PLIST
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"
echo "installed: $PLIST"
