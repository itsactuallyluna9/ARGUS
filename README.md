# ARGUS

Minimal hello-world full-stack app:

- Backend: Flask (`src/argus`)
- Frontend: React + Tailwind 4 + shadcn-style setup (`frontend`)
- Production: React build served by Flask

## Prerequisites

- Python 3.13+
- Node.js 20+

## Install

Backend dependencies:

```bash
uv sync
```

Frontend dependencies:

```bash
cd frontend
npm install
```

## Development

Run backend (from repo root):

```bash
uv run flask --app argus:app run --host 0.0.0.0 --port 5000 --debug
```

Run frontend (new terminal):

```bash
cd frontend
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173`.

## Production-style run

Build frontend:

```bash
cd frontend
npm run build
```

Run Flask from repo root:

```bash
uv run argus
```

Open `http://localhost:5000`. Flask serves `frontend/dist` and the API.
