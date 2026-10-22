#!/bin/bash
# 말리동화(교육용) — Google Drive → 오르카 작업장 감시기 (Polling 방식 — Google Drive 가상FS 호환)

DRIVE_FOLDER="/Users/joy/Library/CloudStorage/GoogleDrive-yookwanhee6@gmail.com/내 드라이브/롱폼 소재/기획서"
ORCA_WORKSPACE="/Volumes/맥 매니 HDD/말리동화(교육용)/output/orca/workspace"
LOG_FILE="/Volumes/맥 매니 HDD/말리동화(교육용)/logs/watcher.log"
PID_FILE="/Volumes/맥 매니 HDD/말리동화(교육용)/logs/watcher.pid"
PROCESSED_FILE="$ORCA_WORKSPACE/.processed_files"

mkdir -p "$ORCA_WORKSPACE"
mkdir -p "$(dirname "$LOG_FILE")"

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE" 2>/dev/null
}

# Already running check
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        log_msg "이미 실행 중 (PID: $OLD_PID). 중복 시작하지 않습니다."
        exit 0
    fi
fi

echo "$$" > "$PID_FILE"
log_msg "감시기 시작 (Polling 5초) — 대상: $DRIVE_FOLDER"
log_msg "오르카 작업장: $ORCA_WORKSPACE"
log_msg "⚠️  오르카 렌더는 자동 시작하지 않습니다 ($AutoRun = false)"

# Create processed tracking file if not exists
touch "$PROCESSED_FILE"

# Process a single file
process_file() {
    local src="$1"
    local filename=$(basename "$src")
    local checksum
    checksum=$(md5 -q "$src" 2>/dev/null | head -c 16)
    local marker="${filename}:${checksum}"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local dest="$ORCA_WORKSPACE/${timestamp}_${filename}"
    local skeleton="${dest%.md}_${timestamp}_skeleton.json"
    
    # Skip if already processed
    if grep -qF "$marker" "$PROCESSED_FILE" 2>/dev/null; then
        return 0
    fi
    
    # Skip skeleton files and temp files
    case "$filename" in
        *_skeleton.json|*~|.*) return 0 ;;
    esac
    
    log_msg "파일 감지: $filename"
    
    # Copy to workspace
    if cp "$src" "$dest" 2>/dev/null; then
        log_msg "→ 작업장 복사: $(basename "$dest")"
        
        # Create skeleton check (NO AUTO RENDER)
        cat > "$skeleton" <<JSON
{
  "source": "$filename",
  "timestamp": "$timestamp",
  "checksum": "$checksum",
  "status": "ready_to_parse",
  "autoRender": false,
  "note": "수동 렌더링 대기 중 — $AutoRun = false"
}
JSON
        log_msg "→ 골격 점검 파일: $(basename "$skeleton")"
        log_msg "✋ 렌더링은 수동 트리거 필요"
        
        # Mark as processed
        echo "$marker" >> "$PROCESSED_FILE"
    else
        log_msg "❌ 복사 실패: $filename"
    fi
}

# Check if drive folder exists
if [ ! -d "$DRIVE_FOLDER" ]; then
    log_msg "❌ 감시 폴더 없음: $DRIVE_FOLDER"
    rm -f "$PID_FILE"
    exit 1
fi

# Main polling loop
FIRST_RUN=true

while true; do
    if [ "$FIRST_RUN" = true ]; then
        log_msg "초기 스캔 중..."
        FIRST_RUN=false
    fi
    
    # Find all .md files
    while IFS= read -r -d '' file; do
        process_file "$file"
    done < <(find "$DRIVE_FOLDER" -name "*.md" -type f -print0 2>/dev/null)
    
    sleep 5
done

log_msg "감시기 종료"
rm -f "$PID_FILE"
