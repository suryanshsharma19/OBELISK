#!/bin/bash
# backup.sh — Backup PostgreSQL and Neo4j data
# Usage: ./scripts/backup.sh [--output-dir /path]

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }

# Defaults
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=14

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --output-dir) BACKUP_DIR="$2"; shift 2 ;;
    *) shift ;;
  esac
done

mkdir -p "$BACKUP_DIR"

# ---------- PostgreSQL Backup ----------
info "Backing up PostgreSQL"
DB_URL="${DATABASE_URL:-postgresql://obelisk:obelisk@localhost:5432/obelisk}"

# Extract connection details from URL
DB_HOST=$(echo "$DB_URL" | sed -n 's|.*@\(.*\):.*|\1|p')
DB_PORT=$(echo "$DB_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
DB_NAME=$(echo "$DB_URL" | sed -n 's|.*/\(.*\)|\1|p')
DB_USER=$(echo "$DB_URL" | sed -n 's|.*://\(.*\):.*@.*|\1|p')

PG_BACKUP="$BACKUP_DIR/pg_${TIMESTAMP}.sql.gz"

if command -v pg_dump >/dev/null 2>&1; then
  PGPASSWORD=$(echo "$DB_URL" | sed -n 's|.*://.*:\(.*\)@.*|\1|p') \
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" \
    | gzip > "$PG_BACKUP"
  info "PostgreSQL backup: $PG_BACKUP"
elif command -v docker >/dev/null 2>&1; then
  docker compose exec -T postgres pg_dump -U obelisk obelisk \
    | gzip > "$PG_BACKUP"
  info "PostgreSQL backup (via Docker): $PG_BACKUP"
else
  warn "pg_dump not found, skipping PostgreSQL backup"
fi

# ---------- Neo4j Backup ----------
info "Backing up Neo4j"
NEO4J_BACKUP="$BACKUP_DIR/neo4j_${TIMESTAMP}.dump"

if command -v docker >/dev/null 2>&1; then
  docker compose exec -T neo4j neo4j-admin database dump neo4j \
    --to-stdout > "$NEO4J_BACKUP" 2>/dev/null || warn "Neo4j backup failed"
  info "Neo4j backup: $NEO4J_BACKUP"
else
  warn "Docker not found, skipping Neo4j backup"
fi

# ---------- Cleanup old backups ----------
info "Cleaning backups older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.dump" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true

info "Backup complete. Files in: $BACKUP_DIR"
ls -lh "$BACKUP_DIR"/*"${TIMESTAMP}"* 2>/dev/null || true
