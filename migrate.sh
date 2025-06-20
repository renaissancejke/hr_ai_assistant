#!/usr/bin/env bash
set -euo pipefail

# ───── 0. ждём Postgres ─────
# (если у вас уже есть «wait-for» – оставьте свой)
host="${DB_HOST:-db}"
port="${DB_PORT:-5432}"
until python - <<PY
import socket, sys, os
sys.exit(0) if not socket.socket().connect_ex((
    os.getenv("DB_HOST","db"), int(os.getenv("DB_PORT","5432"))
)) else sys.exit(1)
PY
do sleep 2; done

# ───── 1. миграции ─────
echo "⚙️  alembic upgrade head"
alembic upgrade head

# ───── 2. запускаем то, что передали в CMD ─────
echo "🚀 starting: $*"
exec "$@"
