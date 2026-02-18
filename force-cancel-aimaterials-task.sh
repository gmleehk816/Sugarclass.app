#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
SERVICE_NAME="${SERVICE_NAME:-aimaterials-backend}"
TASK_ID=""
ALL_ACTIVE=false

usage() {
  cat <<'EOF'
Force-cancel AI Materials V8 ingestion tasks.

Usage:
  ./force-cancel-aimaterials-task.sh --task-id <task_id>
  ./force-cancel-aimaterials-task.sh --all-active

Options:
  --task-id <task_id>   Cancel a specific task id.
  --all-active          Cancel all tasks with status pending/running/cancelling.
  --compose-file <file> Docker compose file (default: docker-compose.prod.yml).
  --service <name>      Backend service name (default: aimaterials-backend).
  -h, --help            Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task-id)
      TASK_ID="${2:-}"
      shift 2
      ;;
    --all-active)
      ALL_ACTIVE=true
      shift
      ;;
    --compose-file)
      COMPOSE_FILE="${2:-}"
      shift 2
      ;;
    --service)
      SERVICE_NAME="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ "$ALL_ACTIVE" != true && -z "$TASK_ID" ]]; then
  echo "Error: provide --task-id <task_id> or --all-active"
  usage
  exit 1
fi

if [[ "$ALL_ACTIVE" == true && -n "$TASK_ID" ]]; then
  echo "Error: use either --task-id or --all-active, not both"
  exit 1
fi

echo "Using compose file: $COMPOSE_FILE"
echo "Using service: $SERVICE_NAME"

if [[ "$ALL_ACTIVE" == true ]]; then
  docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" python - <<'PY'
import sqlite3

db_path = "/app/database/rag_content.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
columns = {row[1] for row in cur.execute("PRAGMA table_info(v8_processing_tasks)").fetchall()}

set_parts = ["status='cancelled'", "message='Force-cancelled by admin script'"]
if "cancel_requested" in columns:
    set_parts.append("cancel_requested=1")
if "cancelled_at" in columns:
    set_parts.append("cancelled_at=COALESCE(cancelled_at, CURRENT_TIMESTAMP)")
if "completed_at" in columns:
    set_parts.append("completed_at=COALESCE(completed_at, CURRENT_TIMESTAMP)")

sql = f"""
UPDATE v8_processing_tasks
SET {', '.join(set_parts)}
WHERE status IN ('pending', 'running', 'cancelling')
"""
cur.execute(sql)
conn.commit()
print("updated_rows:", cur.rowcount)

rows = cur.execute("""
SELECT task_id, status, progress, message
FROM v8_processing_tasks
WHERE status IN ('pending', 'running', 'cancelling')
ORDER BY created_at DESC
LIMIT 10
""").fetchall()
print("remaining_active_tasks:", rows)
conn.close()
PY
else
  docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" python - "$TASK_ID" <<'PY'
import sqlite3
import sys

task_id = sys.argv[1]
db_path = "/app/database/rag_content.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
columns = {row[1] for row in cur.execute("PRAGMA table_info(v8_processing_tasks)").fetchall()}

before = cur.execute("""
SELECT task_id, status, progress, message
FROM v8_processing_tasks
WHERE task_id = ?
""", (task_id,)).fetchone()
print("before:", before)

set_parts = ["status='cancelled'", "message='Force-cancelled by admin script'"]
if "cancel_requested" in columns:
    set_parts.append("cancel_requested=1")
if "cancelled_at" in columns:
    set_parts.append("cancelled_at=COALESCE(cancelled_at, CURRENT_TIMESTAMP)")
if "completed_at" in columns:
    set_parts.append("completed_at=COALESCE(completed_at, CURRENT_TIMESTAMP)")

sql = f"""
UPDATE v8_processing_tasks
SET {', '.join(set_parts)}
WHERE task_id = ?
"""
cur.execute(sql, (task_id,))
conn.commit()
print("updated_rows:", cur.rowcount)

after = cur.execute("""
SELECT task_id, status, progress, message
FROM v8_processing_tasks
WHERE task_id = ?
""", (task_id,)).fetchone()
print("after:", after)
conn.close()
PY
fi

echo "Restarting backend to stop any stuck worker..."
docker compose -f "$COMPOSE_FILE" restart "$SERVICE_NAME"

cat <<'EOF'

Done.
If admin UI still shows stale "cancelling" panel, clear browser local storage key:
  localStorage.removeItem('aimaterials_v8_active_task_id'); location.reload();
EOF
