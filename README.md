# MC Server Manager

Self-hosted Minecraft server management panel built with FastAPI and Next.js. It gives you a web UI for running a Java Minecraft server, managing profiles, uploading worlds and server jars, handling mods, creating backups, watching metrics, and sending console commands.

## Features

- Start, stop, restart, and inspect a Minecraft server process from the browser
- Profile-based server configuration with Minecraft version, server type, jar path, world name, RAM limits, and Java arguments
- EULA acceptance flow per world before server startup
- Live console output and command execution through WebSockets
- CPU, memory, and server status monitoring
- Server jar upload and management
- World upload, selection, and deletion
- Mod upload, enable/disable, and deletion
- Manual world backups, backup download, and admin-only restore
- JWT login with seeded admin account on first startup
- Playit.gg tunnel status and attach/detach controls for remote access
- Docker Compose setup for backend, frontend, persistent data, logs, and Minecraft port exposure

## Tech Stack

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS, Axios, Zustand
- **Backend:** FastAPI, SQLAlchemy async, SQLite, Pydantic, JWT auth
- **Runtime:** Python 3.12, Node.js 20, Eclipse Temurin Java 25 JRE
- **Deployment:** Docker Compose

## Architecture

```text
Browser
  |
  | HTTP + WebSocket
  v
Next.js frontend :3000
  |
  | REST API
  v
FastAPI backend :8000
  |
  | subprocess + stdin/stdout
  v
Minecraft Java server :25565

Persistent files:
  backend/data   -> SQLite DB, worlds, mods, backups, server jars
  backend/logs   -> server logs
```

## Quick Start

### 1. Clone

```bash
git clone https://github.com/abbeyraa/mc-server-mng.git
cd mc-server-mng
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` before public deployment:

```env
SERVER_HOST=localhost
FRONTEND_PORT=3000
BACKEND_PORT=8000
MINECRAFT_PORT=25565
NEXT_PUBLIC_API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000

SECRET_KEY=change-me-to-a-random-secret-key-at-least-32-chars
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
```

Use a strong `SECRET_KEY` and change `ADMIN_PASSWORD` before exposing the panel.

### 3. Run with Docker Compose

```bash
docker compose up -d --build
```

Open:

- Frontend: <http://localhost:3000>
- Backend health check: <http://localhost:8000/health>
- API docs: <http://localhost:8000/docs>
- Minecraft server port: `localhost:25565`

Default first login comes from `.env`:

```text
username: admin
password: changeme
```

## First Server Setup

1. Upload a Minecraft server `.jar` from the Jars page.
2. Upload or create/select a world from the Worlds page.
3. Create a server profile with jar path, world name, RAM limits, and Java arguments.
4. Activate the profile.
5. Accept the Minecraft EULA from the dashboard.
6. Start the server.
7. Use Console page for live logs and commands.

## Playit.gg Tunnel

The dashboard includes Playit.gg tunnel controls. Docker Compose mounts:

```yaml
/opt/playit:/opt/playit:ro
/run/playit:/host/run/playit:ro
```

Expected mode is native systemd on the host. If the daemon is unavailable, start it on the host:

```bash
sudo systemctl start playit
```

The panel targets Minecraft at `127.0.0.1:25565` and stores the configured join domain in the backend database.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` for local frontend development.

## API Surface

Backend routes are mounted under `/api/v1`:

- `/auth` - login and current user
- `/server` - status, start, stop, restart, EULA
- `/profiles` - server profile CRUD and activation
- `/jars` - server jar upload and deletion
- `/worlds` - world upload, selection, deletion
- `/mods` - mod upload, toggle, deletion
- `/backup` - backup list, create, restore, download
- `/metrics` - system metrics
- `/console` - server command dispatch
- `/playit` - Playit.gg domain and attach state

WebSocket endpoints:

- `/ws/console?token=<jwt>` - live Minecraft server console
- `/ws/metrics?token=<jwt>` - live metrics stream
- `/ws/playit-console?token=<jwt>` - Playit attach logs

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers and dependencies
│   │   ├── core/         # config, DB, security, logging
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # server, backup, world, jar, mod logic
│   │   └── websockets/   # console and metrics streams
│   ├── data/             # runtime data volume
│   └── logs/             # runtime logs volume
├── frontend/
│   └── src/
│       ├── app/          # Next.js app routes
│       ├── components/   # dashboard and console components
│       ├── hooks/        # WebSocket and metrics hooks
│       └── lib/          # API and auth helpers
├── docker-compose.yml
└── .env.example
```

## Roadmap / Future Updates

- Modpack installer for CurseForge, Modrinth, and ZIP-based packs
- Automatic server jar downloader for Vanilla, Paper, Fabric, Forge, and Quilt
- Scheduled backups with retention rules
- Backup upload to S3-compatible storage, Google Drive, or another remote target
- Player management tools for whitelist, ban list, ops, and online player actions
- Resource usage alerts for high CPU, high memory, crashes, and disk space
- Multi-server support from one dashboard
- Server event log with audit trail for admin actions
- Plugin management for Paper/Spigot servers
- Safer role management UI for admin, manager, and read-only users
- One-click world import/export with metadata preview
- Automatic crash report detection and readable crash summaries

## Security Notes

- Change `SECRET_KEY` and `ADMIN_PASSWORD` before deployment.
- Put the panel behind HTTPS when exposed outside a private network.
- Restrict `CORS_ORIGINS` to trusted frontend origins.
- Backup restore is admin-only and requires the server to be stopped.
- Keep `backend/data` and `backend/logs` out of public artifacts because they may contain worlds, credentials, and player data.

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).
