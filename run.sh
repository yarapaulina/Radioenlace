#!/usr/bin/env bash
# Inicialização do RadioLink Pro (FastAPI + React)
#   ./run.sh        -> compila o React (se necessário) e serve tudo em http://localhost:8000
#   ./run.sh dev    -> backend em :8000 + Vite com hot reload em http://localhost:5173
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

[ -d ".venv" ] && source .venv/bin/activate

if [ ! -d "frontend/node_modules" ]; then
    echo "Instalando dependências do frontend..."
    (cd frontend && npm install)
fi

if [ "$1" = "dev" ]; then
    echo "Backend: http://localhost:8000  |  Frontend (hot reload): http://localhost:5173"
    python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
    BACK_PID=$!
    trap 'kill $BACK_PID 2>/dev/null' EXIT
    (cd frontend && npm run dev)
else
    echo "Compilando frontend React..."
    (cd frontend && npm run build)
    echo "RadioLink Pro em http://localhost:8000"
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
