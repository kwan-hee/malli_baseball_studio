#!/bin/bash
# 말리동화(교육용) — Google Drive → 오르카 작업장 감시기 설치 스크립트

set -e

PROJECT="/Volumes/맥 매니 HDD/말리동화(교육용)"
SCRIPT_DIR="$PROJECT/scripts"
WATCHER_SCRIPT="$SCRIPT_DIR/orca_watcher.sh"
PLIST_NAME="com.joy.malldonghwa.orca.watcher"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LOG_DIR="$PROJECT/logs"

# Google Drive sync folder (create if not exists)
DRIVE_BASE="$HOME/Library/CloudStorage/GoogleDrive-yookwanhee6@gmail.com/내 드라이브"
DRIVE_FOLDER="$DRIVE_BASE/롱폼 소재/기획서"

# Create folders if they don't exist
if [ ! -d "$DRIVE_BASE" ]; then
    echo "❌ Google Drive sync folder not found: $DRIVE_BASE"
    echo "Google Drive Desktop이 실행 중인지 확인하세요."
    exit 1
fi

mkdir -p "$DRIVE_FOLDER"
echo "✅ 감시 대상 폴더: $DRIVE_FOLDER"

# Create directories
mkdir -p "$SCRIPT_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$PROJECT/output/orca/workspace"

# Install fswatch if not present
if ! command -v fswatch >/dev/null 2>&1; then
    echo "== fswatch 설치 중 (brew 필요) =="
    if command -v brew >/dev/null 2>&1; then
        brew install fswatch
    else
        echo "❌ Homebrew가 없습니다. https://brew.sh 에서 설치 후 다시 실행하세요."
        exit 1
    fi
fi

# Create watcher script
cat > "$WATCHER_SCRIPT" <<'WATCHER_EOF'
#!/bin/bash
# 파일 시스템 감시기 — Google Drive 기획서 → 오르카 작업장

DRIVE_FOLDER="__DRIVE_FOLDER__"
ORCA_WORKSPACE="__PROJECT__/output/orca/workspace"
LOG_FILE="__LOG_DIR__/watcher.log"
PID_FILE="__LOG_DIR__/watcher.pid"

mkdir -p "$ORCA_WORKSPACE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 감시기 시작 — 대상: $DRIVE_FOLDER" >> "$LOG_FILE"
echo "$$" > "$PID_FILE"

# Function: process new/updated file
process_file() {
    local file="$1"
    local filename=$(basename "$file")
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 파일 감지: $filename" >> "$LOG_FILE"
    
    # Copy to orca workspace with timestamp
    local dest="$ORCA_WORKSPACE/${timestamp}_${filename}"
    cp "$file" "$dest"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] → 오르카 작업장으로 복사: $dest" >> "$LOG_FILE"
    
    # Create skeleton check (dry-run only, never trigger render)
    local skeleton_file="${dest%.md}_skeleton.json"
    echo "{\"source\":\"$filename\",\"timestamp\":\"$timestamp\",\"status\":\"ready_to_parse\",\"autoRender\":false}" > "$skeleton_file"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 골격 점검 파일 생성 (렌더링 안 함): $skeleton_file" >> "$LOG_FILE"
    
    # NEVER auto-trigger Orca render — $AutoRun = $false
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✋ 오르카 렌더링은 자동 시작하지 않습니다. 선생님이 수동으로 트리거해야 합니다." >> "$LOG_FILE"
}

# Watch for .md file changes
fswatch -o "$DRIVE_FOLDER" | while read event; do
    find "$DRIVE_FOLDER" -name "*.md" -mtime -0.0007 -type f 2>/dev/null | while read file; do
        process_file "$file"
    done
done >> "$LOG_FILE" 2>&1
WATCHER_EOF

# Replace placeholders
sed -i '' "s|__DRIVE_FOLDER__|$DRIVE_FOLDER|g" "$WATCHER_SCRIPT"
sed -i '' "s|__PROJECT__|$PROJECT|g" "$WATCHER_SCRIPT"
sed -i '' "s|__LOG_DIR__|$LOG_DIR|g" "$WATCHER_SCRIPT"
chmod +x "$WATCHER_SCRIPT"

# Create LaunchAgent plist
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$WATCHER_SCRIPT</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/watcher_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/watcher_stderr.log</string>
</dict>
</plist>
EOF

# Load LaunchAgent
launchctl load "$PLIST_PATH" 2>/dev/null || launchctl bootstrap gui/$(id -u) "$PLIST_PATH" 2>/dev/null || true

echo ""
echo "✅ 설치 완료!"
echo ""
echo "📁 감시 대상 (폴더 자동 생성됨): $DRIVE_FOLDER"
echo "🎯 오르카 작업장: $PROJECT/output/orca/workspace"
echo "📝 로그 파일: $LOG_DIR/watcher.log"
echo "🔄 LaunchAgent: $PLIST_PATH"
echo ""
echo "⚠️  오르카 렌더는 자동 시작되지 않습니다 ($AutoRun = false)"
echo "   기획서가 감지되면 작업장에 복사 + 골격 점검 파일만 생성됩니다."
echo "   렌더링 시작은 직접 하셔야 합니다."
echo ""
echo "📋 관리 명령:"
echo "   시작: launchctl start $PLIST_NAME"
echo "   중지: launchctl stop $PLIST_NAME"
echo "   상태: launchctl list | grep $PLIST_NAME"
echo ""
echo "🧪 즉시 테스트:"
echo "   touch '$DRIVE_FOLDER/test_기획서.md'"
