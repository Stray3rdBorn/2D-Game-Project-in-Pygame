# DecaDome

[![CI](https://github.com/Stray3rdBorn/2D-Game-Project-in-Pygame/actions/workflows/ci.yml/badge.svg)](https://github.com/Stray3rdBorn/2D-Game-Project-in-Pygame/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/Stray3rdBorn/2D-Game-Project-in-Pygame)](https://github.com/Stray3rdBorn/2D-Game-Project-in-Pygame/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

**A 2D top down arena shooter with accounts and a global online leaderboard.** Survive ten waves of enemies, then see where your best score ranks against everyone else.

I built DecaDome as a game dev hobby which turned into a full stack project. The game is written in Python with Pygame. Behind it sits a real backend: FastAPI with Django mounted inside it, PostgreSQL, Redis, JWT login, tests, Docker, a CI pipeline, HTTPS hosting and a downloadable Windows exe built by GitHub Actions.

|                              |                                                                                             |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| Download the game (Windows)  | [Latest release](https://github.com/Stray3rdBorn/2D-Game-Project-in-Pygame/releases/latest) |
| Landing page and live top 10 | [decadome.pages.dev](https://decadome.pages.dev/)                                           |
| Live API                     | `https://decadome.onrender.com` (`/health`, `/leaderboard`)                                 |
| Source code                  | This repository                                                                             |

The API runs on a free hosting plan. After 15 minutes without a visitor it goes to sleep, and the first request afterwards takes about a minute. The game and the landing page both know this and wait.

## Table of contents

1. [Screenshots](#screenshots)
2. [Features](#features)
3. [Download and play](#download-and-play)
4. [Gameplay](#gameplay)
5. [Architecture](#architecture)
6. [Tech stack](#tech-stack)
7. [Folder structure](#folder-structure)
8. [Run it from source](#run-it-from-source)
9. [Configuration](#configuration)
10. [API reference](#api-reference)
11. [Testing](#testing)
12. [CI and releases](#ci-and-releases)
13. [Deployment](#deployment)
14. [Security](#security)
15. [Known limitations](#known-limitations)
16. [How the game works inside](#how-the-game-works-inside)
17. [Roadmap](#roadmap)
18. [License](#license)
19. [Contact](#contact)

## Screenshots

Gameplay screenshots

![Main menu](docs/screenshots/menu1.png)
![Main menu](docs/screenshots/menu2.png)
![Gameplay](docs/screenshots/gameplay.png)
![Leaderboard](docs/screenshots/leaderboard.png)
![Dashboard](docs/screenshots/dashboard.png)
![Game over](docs/screenshots/game-over1.png)
![Game over](docs/screenshots/game-over2.png)
![Login](docs/screenshots/login.png)
![Register](docs/screenshots/register.png)

## Features

**Game**

- Ten waves of enemies with two enemy types (grunts and tanks), growing speed and a growing tank chance.
- Wave bonus scoring, a hit immunity window, and a win or loss at the end of every run.
- Seven screens built with my own small widget set: menu, login, register, leaderboard, dashboard, play and game over.
- Guests can play without an account. Registering is only needed to appear on the leaderboard.
- A run that finishes while you are logged out, or after your login expired, is kept in memory and saved right after you log in.
- The window never freezes while it talks to the server. All network calls run in a background thread.

**Backend**

- Register and login with salted password hashes and signed JWT tokens that expire after 1 day.
- A score API that checks every value on the server.
- A leaderboard with the best score per player, ranked in Redis with an automatic PostgreSQL fallback.
- A Django admin panel for managing users and scores.

**Web and delivery**

- A static landing page on Cloudflare Pages with the live top 10, a download button, and SmartScreen and checksum help.
- A Windows exe built by GitHub Actions when I push a version tag, with a SHA256 checksum published next to it.
- Automatic deploys of the server, only after the CI checks pass.

## Download and play

1. Go to the [latest release](https://github.com/Stray3rdBorn/2D-Game-Project-in-Pygame/releases/latest) and download `DecaDome.exe` (Windows 10 or 11).
2. Run it. Windows SmartScreen will say "Windows protected your PC". I have not bought a code signing certificate, and SmartScreen warns about every new unsigned file. Click **More info**, then **Run anyway**.
3. To check that the file is the one my pipeline built, download `DecaDome.exe.sha256` from the same release and run this in PowerShell, in the folder with the exe:

   ```powershell
   certutil -hashfile DecaDome.exe SHA256
   ```

   The value printed must match the value in the `.sha256` file.

4. Some antivirus programs flag exes made by PyInstaller by mistake. This is a known problem with that packaging tool. The checksum is how you can verify the file.

The game saves two small files in `%LOCALAPPDATA%\DecaDome`: `highscore.json` (your best local score) and `session.json` (your login token). Deleting that folder logs you out and resets the local high score.

## Gameplay

You control a blue circle in the middle of the arena. Enemies spawn just outside the screen edges and walk straight at you. Clear all 10 waves to reach the win screen. If your HP reaches zero first, the run is over.

### Controls

| Action                             | Input                         |
| ---------------------------------- | ----------------------------- |
| Move                               | `W` `A` `S` `D` or arrow keys |
| Aim                                | Mouse                         |
| Shoot                              | Hold left mouse button        |
| Start or play again                | `Space`                       |
| Leave a round or a screen, or quit | `Esc`                         |

### Enemies

| Enemy | Color  | HP  | Size  | Speed             | Points |
| ----- | ------ | --- | ----- | ----------------- | ------ |
| Grunt | Red    | 1   | Small | Full wave speed   | 10     |
| Tank  | Purple | 3   | Large | 60% of wave speed | 30     |

Tanks do not appear in wave 1. Each wave adds 10 percentage points to the chance that a spawn is a tank, up to a cap of 60% from wave 7 onward.

### Player

- 5 HP at the start of a run.
- Touching an enemy removes that enemy and costs 1 HP. You are then immune for 1 second, and the player blinks while immune.
- The player moves faster than any enemy, so running away always works.

### Waves and scoring

- Wave `n` spawns `5 + 5n` enemies, one every 0.6 seconds, from random points just outside the four screen edges.
- Enemy speed is `70 + 12n` pixels per second, capped at 220.
- Each kill gives its enemy's points: 10 for a grunt, 30 for a tank.
- Clearing wave `n` gives a bonus of `50 * n` points, followed by a 3 second break before the next wave.
- Clearing wave 10 ends the game with a win. Dying on the same frame as the final kill counts as a loss.
- A run counts for the leaderboard only when you are logged in. Your best score per player is what ranks.

### Screens and flow

| Screen             | What it does                                                                           |
| ------------------ | -------------------------------------------------------------------------------------- |
| Menu               | Start, login, register, leaderboard. Shows your name when logged in.                   |
| Register and login | Two text boxes and a button. Errors from the server are shown in plain words.          |
| Leaderboard        | Top 10 for anyone, with your own row highlighted when you are logged in.               |
| Dashboard          | Your username, best score, rank and total number of runs.                              |
| Play               | The game itself.                                                                       |
| Game over          | Score, win or loss, the top 10 and your own row. Saves the run when you are logged in. |

## Architecture

```
                      ┌──────────────────────────────┐
                      │  Pygame client (Windows exe) │
                      │  screens, widgets, gameplay  │
                      └──────────────┬───────────────┘
                                     │  HTTPS, JSON, Bearer token
                                     ▼
 ┌──────────────────┐     ┌───────────────────────────────────────────┐
 │ Landing page     │     │  One service on Render (Docker image)     │
 │ Cloudflare Pages │────▶│                                           │
 │ static files     │ GET │   FastAPI  /scores /leaderboard /me       │
 │ top 10 + download│     │      │ /health                            │
 └──────────────────┘     │      │  mounts Django at "/"              │
                          │      ▼                                    │
                          │   Django  /api/register /api/login /admin │
                          └──────────┬───────────────────┬────────────┘
                                     │                   │
                                     ▼                   ▼
                            ┌─────────────────┐  ┌────────────────────┐
                            │ PostgreSQL      │  │ Redis              │
                            │ (Neon)          │  │ (Render Key Value) │
                            │ users + scores  │  │ ranked best scores │
                            └─────────────────┘  └────────────────────┘
```

### How the pieces are connected

I run FastAPI and Django as one web service on purpose. FastAPI is the front door: it answers `/health`, `/scores`, `/leaderboard` and `/me` itself. Everything it does not recognise is handed to Django, which I mounted at `/` with `app.mount("/", django_asgi)`. Django answers `/api/register`, `/api/login` and `/admin/`. One service means one address, one deploy, and one free hosting slot.

Both frameworks talk to the same PostgreSQL database. Django owns the user accounts and creates the user tables through its migrations. FastAPI owns the `scores` table, which SQLAlchemy creates at startup. Django shows the scores in the admin panel through an unmanaged model, which means Django reads that table but never creates or changes it.

The two frameworks trust each other through the token, not through shared code. Django creates a JWT when someone registers or logs in. FastAPI checks the signature with the same `JWT_SECRET` and reads the user id and name from it. FastAPI never looks the user up in the database to check a token.

Redis is only a fast ranking list (a sorted set). PostgreSQL is the source of truth. If Redis is empty, wiped or down, the API reads the ranking straight from PostgreSQL, and rebuilds Redis from PostgreSQL when the server starts and when a new score arrives while Redis is empty.

### Request flows

**Register or login.** The game sends the username and password to `POST /api/register` or `/api/login`. Django validates them, stores or checks the password hash, and returns a token and the username. The game keeps the token in memory and saves it in `session.json`. The password is never saved.

**Saving a run.** At the end of a round, if you are logged in, the game sends `POST /scores` with the score, the wave reached and a won flag, plus the header `Authorization: Bearer <token>`. FastAPI checks the token, checks the numbers, writes the row to PostgreSQL, and updates Redis with the new best score. If the token has expired, the server answers `401`, the game keeps the run in memory, asks you to log in and sends it again after login.

**Reading the leaderboard.** The game and the landing page call `GET /leaderboard`. FastAPI reads the top entries from Redis, falls back to PostgreSQL when Redis has nothing, and adds your own rank when a valid token is sent.

**Server start.** FastAPI creates the `scores` table if it is missing and rebuilds the Redis ranking from PostgreSQL. This is why the free Redis instance, which loses its data on every restart, does not matter.

**Landing page.** A static page fetches `GET /leaderboard` with JavaScript and builds the table with `textContent`, never as HTML. It waits up to 90 seconds and explains that the free server is waking up.

## Tech stack

Every tool below has one job. The "why" column is the reason I picked it for this project.

### Game client

| Tool                     | Purpose                                  | Why I chose it                                                            |
| ------------------------ | ---------------------------------------- | ------------------------------------------------------------------------- |
| Python 3.12+             | Language of the game and the server      | One language for every part, and the language I wanted to be strongest in |
| Pygame                   | Window, drawing, input, game loop        | A direct way to write a 2D game loop myself instead of using an engine    |
| My own widgets (`ui.py`) | Label, Button, TextInput                 | I wanted to understand how UI works, so I did not use a UI library        |
| `requests`               | HTTP calls to the API                    | The standard Python HTTP client, with simple timeouts and error types     |
| `python-dotenv`          | Reads `ARENA_API_URL` from a `.env` file | Keeps the server address out of the code during development               |
| PyInstaller              | Packs the game into one `.exe`           | Players do not need Python installed                                      |

### Backend

| Tool                      | Purpose                                                         | Why I chose it                                                             |
| ------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------- |
| FastAPI                   | The score API: `/scores`, `/leaderboard`, `/me`, `/health`      | Modern, fast, automatic request validation and interactive docs            |
| Pydantic (inside FastAPI) | Checks every request body and shapes every response             | Bad values are rejected before my code runs                                |
| Django                    | Accounts, password hashing, register and login, the admin panel | A mature, well tested account system, and an admin panel for free          |
| Uvicorn                   | Runs the combined app                                           | The standard server for FastAPI                                            |
| SQLAlchemy                | Talks to PostgreSQL from FastAPI                                | Values are always sent separately from the SQL, which blocks SQL injection |
| psycopg 3                 | PostgreSQL driver                                               | Used by both SQLAlchemy and Django                                         |
| PyJWT                     | Creates and verifies tokens                                     | A small, widely used JWT library                                           |
| Redis (redis-py)          | Sorted set for the leaderboard                                  | A sorted set ranks and fetches the top N in milliseconds                   |
| WhiteNoise                | Serves the admin panel's CSS from the same service              | No extra static file server needed                                         |

### Data and hosting

| Tool                 | Purpose                                       | Why I chose it                                                       |
| -------------------- | --------------------------------------------- | -------------------------------------------------------------------- |
| PostgreSQL           | The permanent record of users and every score | A real relational database, and the industry default                 |
| Neon                 | Hosts PostgreSQL online                       | Free tier, enforces encrypted connections                            |
| Render (web service) | Runs the Docker image of the server           | Free tier, deploys straight from GitHub                              |
| Render Key Value     | Hosts Redis online                            | Free, in the same region as the server so the internal address works |
| Cloudflare Pages     | Serves the landing page                       | Free static hosting with custom security headers                     |
| GitHub Releases      | Hosts the exe download                        | Free, and the release page keeps the checksum next to the file       |

### Quality and delivery

| Tool                           | Purpose                                                 | Why I chose it                                                      |
| ------------------------------ | ------------------------------------------------------- | ------------------------------------------------------------------- |
| pytest                         | All tests                                               | Short tests, good fixtures                                          |
| fakeredis                      | An in memory Redis for server tests                     | Tests need no running Redis                                         |
| httpx and FastAPI's TestClient | Calls the API in tests                                  | Tests run the real app without a network                            |
| flake8                         | Lint                                                    | Stops syntax errors and undefined names in CI                       |
| Docker and Docker Compose      | Build and run PostgreSQL, Redis and the server together | The same stack on any machine, and a smoke test in CI               |
| GitHub Actions                 | CI, release build                                       | Runs on every push, and builds the Windows exe on a Windows machine |

## Folder structure

```
.
├── client/                      the game the player runs
│   ├── app.py                   start file: builds the screens and runs the loop
│   ├── main.py                  gameplay: player, bullets, enemies, waves, scoring
│   ├── views.py                 every screen: menu, login, register, leaderboard, dashboard, play, game over
│   ├── screens.py               screen switcher, holds the session, network and pending run
│   ├── ui.py                    my own widgets: label, button, text box
│   ├── network.py               talks to the server in a background thread
│   ├── storage.py               saves and loads the login token
│   ├── paths.py                 the one folder where the game saves its files
│   └── server_address.py        the server address, replaced by the release build
│
├── tests/                       tests for the game (run without a window)
│
├── server/                      everything that runs online
│   ├── Dockerfile               recipe for the server image
│   ├── requirements.txt         server dependencies
│   ├── requirements-dev.txt     server dependencies plus test tools
│   ├── app/                     the FastAPI part
│   │   ├── main.py              endpoints, CORS, and the mount of Django
│   │   ├── auth.py              reads and checks the token
│   │   ├── schemas.py           request and response shapes and limits
│   │   ├── models.py            the scores table
│   │   ├── database.py          PostgreSQL connection
│   │   ├── cache.py             Redis connection
│   │   ├── ranking.py           Redis leaderboard with PostgreSQL fallback
│   │   └── django_app.py        loads Django so FastAPI can mount it
│   ├── web/                     the Django part
│   │   ├── manage.py            Django's command tool
│   │   ├── config/              settings and URLs
│   │   └── accounts/            register and login, token creation, admin setup
│   └── tests/                   server tests (in memory database and Redis)
│
├── landing/                     static landing page for Cloudflare Pages
│   ├── index.html               the page
│   ├── style.css                all styling
│   ├── script.js                loads the live top 10
│   └── _headers                 security headers for Cloudflare Pages
│
├── docs/                        documents about the project
│   ├── PROJECT_STRUCTURE.md     the same folder map with notes on each file
│   ├── SECURITY_LOG.md          every security issue: covered, how, and still open
│   └── screenshots/             game screenshots for this README
│
├── .github/workflows/
│   ├── ci.yml                   tests, lint and the Docker smoke test on every push
│   └── release.yml              builds and publishes the exe when I push a version tag
│
├── docker-compose.yml           PostgreSQL, Redis and the server together (used by CI)
├── pytest.ini                   tells pytest the game tests are in tests/
├── requirements.txt             game dependencies
├── LICENSE
└── README.md
```

## Run it from source

### The game only

You need Python 3.12 or newer.

```bash
git clone https://github.com/Stray3rdBorn/2D-Game-Project-in-Pygame.git
cd 2D-Game-Project-in-Pygame

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS and Linux

pip install -r requirements.txt
python client/app.py
```

With no setting, the game looks for a server at `http://127.0.0.1:8000`. Without a running server you can still play as a guest, and the screens that need the server show an error message.

To point the game at another server, create `client/.env` with one line:

```
ARENA_API_URL=https://decadome.onrender.com
```

The game only accepts `https` addresses, except for `localhost` and `127.0.0.1`.

### The server on my own computer

You need PostgreSQL and Redis. On Windows I use Memurai as Redis.

```bash
cd server
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS and Linux

pip install -r requirements.txt
```

Create `server/.env` from `server/.env.example` and fill in your own values (see [Configuration](#configuration)). Then:

```bash
python web/manage.py migrate
python web/manage.py createsuperuser
uvicorn app.main:app --reload
```

The API is now on `http://127.0.0.1:8000`. FastAPI's interactive docs are at `/docs` and the Django admin is at `/admin/`.

### Server and database with Docker

```bash
docker compose up --build
```

This starts PostgreSQL, Redis and the server on port 8000. The passwords in `docker-compose.yml` are for local development only. I use this file mainly in CI, because Docker does not run on my own laptop.

## Configuration

### Server (`server/.env` locally, Render's Environment online)

| Variable               | Needed | Meaning                                                                                                                      |
| ---------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`         | yes    | PostgreSQL address, in the form `postgresql+psycopg://user:password@host:5432/name`. Online it ends with `?sslmode=require`. |
| `SECRET_KEY`           | yes    | Django's signing key. Long and random.                                                                                       |
| `JWT_SECRET`           | yes    | Signs the login tokens. Long and random, different from `SECRET_KEY`.                                                        |
| `REDIS_URL`            | no     | Redis address. Defaults to `redis://localhost:6379/0`.                                                                       |
| `DEBUG`                | no     | Set to `1` only on my own computer. Anything else means production mode.                                                     |
| `ALLOWED_HOSTS`        | online | Comma separated host names the server answers to, without `https://`.                                                        |
| `CSRF_TRUSTED_ORIGINS` | online | Comma separated `https://` addresses allowed to submit the admin login form.                                                 |
| `CORS_ORIGINS`         | online | Comma separated `https://` addresses allowed to read the API from a browser. Only my landing page.                           |

### Game

| Setting                             | Where                                                       | Meaning                                                                              |
| ----------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `ARENA_API_URL`                     | `client/.env` or an environment variable                    | Server address while developing. Overrides the built in one.                         |
| `client/server_address.py`          | repository                                                  | Stays on the local address. The release build overwrites it with the online address. |
| `ARENA_API_URL` repository variable | GitHub, Settings, Secrets and variables, Actions, Variables | The online address the release build puts into the exe. It is not a secret.          |

(The setting is still called `ARENA_API_URL` from before the game was renamed. It is only an internal name.)

## API reference

Base address: `https://decadome.onrender.com`. All bodies are JSON. Protected endpoints need the header `Authorization: Bearer <token>`.

| Method and path             | Auth         | Body or query                                                   | Answers                                                                                                           |
| --------------------------- | ------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `GET /health`               | none         |                                                                 | `200 {"status": "ok"}`                                                                                            |
| `POST /api/register`        | none         | `{"username": "...", "password": "..."}`                        | `201 {"token", "username"}`, or `400 {"detail": "..."}` with the first validation problem                         |
| `POST /api/login`           | none         | `{"username": "...", "password": "..."}`                        | `200 {"token", "username"}`, or `401 {"detail": "Wrong username or password"}`                                    |
| `POST /scores`              | required     | `{"score": 0 to 100000, "wave_reached": 1 to 10, "won": false}` | `201` with the saved row, `401` for a missing, wrong or expired token, `422` for values out of range              |
| `GET /leaderboard?limit=10` | optional     | `limit` from 1 to 100                                           | `200 {"entries": [{"rank", "player_name", "score"}], "me": {...} or null}`. `me` appears only with a valid token. |
| `GET /me`                   | required     |                                                                 | `200 {"username", "total_runs", "best_score", "rank"}`                                                            |
| `/admin/`                   | Django login |                                                                 | The admin panel                                                                                                   |

The token is a JWT signed with HS256. It holds `sub` (user id), `username`, `iat` and `exp`, and it lives for exactly 1 day.

Example:

```bash
curl -X POST https://decadome.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "a-strong-pass-77"}'

curl -X POST https://decadome.onrender.com/scores \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"score": 1200, "wave_reached": 4, "won": false}'
```

### Data model

One table I own, `scores`, created by SQLAlchemy:

| Column         | Type                     | Note                              |
| -------------- | ------------------------ | --------------------------------- |
| `id`           | integer                  | primary key                       |
| `user_id`      | integer                  | Django's user id, indexed         |
| `player_name`  | string, 20               | the username cut to 20 characters |
| `score`        | integer                  | indexed                           |
| `wave_reached` | integer                  | 1 to 10                           |
| `won`          | boolean                  |                                   |
| `created_at`   | timestamp with time zone | set by the database               |

The user table and the password hashes belong to Django. The ranking is the best score per `user_id`.

## Testing

| Suite        | Count | Where           | Run with                           |
| ------------ | ----- | --------------- | ---------------------------------- |
| Game tests   | 98    | `tests/`        | `pytest` in the project root       |
| Server tests | 44    | `server/tests/` | `python -m pytest` inside `server` |

```bash
# game tests
pip install pytest
pytest

# server tests
cd server
pip install -r requirements-dev.txt
python -m pytest
```

**Game tests** run Pygame with no window and no sound. They cover collision, screen bounds, movement, hit immunity, enemy chasing, tank spawning, wave growth, high score saving, a headless 10 second run, the widgets, the screen switcher, every screen and its flow, the background network layer with a fake server (including timeouts and the plain http refusal), and the token file (damaged files, expired tokens, save failures).

**Server tests** use an in memory database and fakeredis, so they need no running services. They cover token creation and checking (wrong signature, garbage, expired), register and login rules, score validation, ranking by best score, the PostgreSQL fallback when Redis is empty or down, CORS (allowed origin, foreign origin, blocked methods), and the production settings (secure cookies, HSTS, allowed hosts, database options).

For the security protections I also changed the code on purpose and confirmed that the matching test fails, to make sure the tests really watch for it.

## CI and releases

**`ci.yml`** runs on every push and pull request to `main`, and by hand. The workflow only has read permission on the repository, and a newer push cancels the older run on the same branch. Jobs:

1. **Game tests** on Python 3.12 and 3.13: lint (syntax errors and undefined names fail the build, a style report does not) and `pytest`.
2. **Server tests** on Python 3.12 and 3.13: lint and `python -m pytest`.
3. **Docker Compose smoke test**: builds the images, starts PostgreSQL, Redis and the server, checks `/health`, `/leaderboard` and the admin login page, then registers a user, logs in, submits a score and checks that `/me` reports rank 1.

**`release.yml`** runs only when I push a tag that starts with `v`, for example `v1.0.0`. It runs on a Windows machine with the permission `contents: write` and nothing else:

1. Runs the game tests. A failing test stops the release.
2. Writes the online server address from the `ARENA_API_URL` repository variable into `client/server_address.py`. It stops if the variable is empty.
3. Builds one exe with PyInstaller (pinned to an exact version), windowed, no console.
4. Starts the exe for 8 seconds and fails if it closes by itself.
5. Writes a SHA256 checksum file.
6. Creates the GitHub release with the exe and the checksum, using GitHub's own `gh` tool and no third party action.

To publish a new version:

```bash
git tag v1.0.1
git push origin v1.0.1
```

## Deployment

| Part                      | Where                                              | Notes                                                                                                                                                                            |
| ------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Server (FastAPI + Django) | Render web service, Docker, Singapore              | Root directory `server`. Auto deploy is set to "After CI Checks Pass", so untested code never goes live. Start command runs `migrate` and then Uvicorn on the port Render gives. |
| PostgreSQL                | Neon, Singapore                                    | Direct (not pooled) connection, `sslmode=require`                                                                                                                                |
| Redis                     | Render Key Value, Singapore                        | Internal address, same region as the server                                                                                                                                      |
| Landing page              | Cloudflare Pages, build output directory `landing` | Deploys from `main`, headers from `landing/_headers`                                                                                                                             |
| Game download             | GitHub Releases                                    | Built by `release.yml`                                                                                                                                                           |

The Docker image installs the dependencies, copies the code, and collects the admin panel's CSS at build time with dummy values, so no real secret ever enters the image. The real values exist only in Render's environment settings.

Free plan facts I designed around: the server sleeps after 15 minutes without traffic and takes about a minute to wake up, so the game uses a 70 second timeout and sends a wake up request on launch, and the landing page waits up to 90 seconds. The free Redis loses its data on every restart, so the leaderboard is rebuilt from PostgreSQL at startup. The free database also sleeps, so the connection pool tests each connection before using it (`pool_pre_ping`).

## Security

I kept a security log through every stage of this project. The complete table, with the stage in which each item was handled, is in [`docs/SECURITY_LOG.md`](docs/SECURITY_LOG.md). This section is the summary: what I solved and how, and what I did not solve and why.

What is at stake in this project is low: there is no payment data, no email address and no personal information beyond a username and a password. I treated it like a real public service anyway, because the server is on the internet.

### What I solved, and how

**Accounts and passwords**

- _Plain text passwords._ Django stores only a salted PBKDF2 hash. The game never saves the password, and it empties the password box the moment the request is sent.
- _Weak passwords._ Django's four password rules run on register: minimum length, not a common password, not all digits, not too similar to the username.
- _Leaking which half of a login was wrong._ There is one message for a wrong name and a wrong password.
- _The old API key design._ In my first version a long API key was shown on a web page and copied by hand into a file. I removed it. Login now returns a token that the game stores itself, and the key table is dropped by a migration.

**Tokens**

- _Forged tokens._ Tokens are signed with HS256 and `JWT_SECRET`. The server accepts only HS256, so the "choose a weaker algorithm" trick fails. A wrong signature, garbage or an expired token all return `401`. This is tested.
- _A stolen token that works forever._ Tokens expire after exactly 1 day. This is tested.
- _A leaked `JWT_SECRET`._ The recovery is to change the value in Render. Everybody logs in again once.
- _Token file damage._ The game writes the token file atomically (a temporary file, then a swap), sets owner only permission on Linux and macOS, treats a damaged or wrong shaped file as logged out, and deletes an expired token when loading. A tampered file only causes a `401`.
- _Token location._ The token is saved in `%LOCALAPPDATA%`, which stays on the PC, not in the roaming folder that can follow an account to other computers.

**The API**

- _Absurd or malicious values._ Pydantic checks score 0 to 100000 and wave 1 to 10, and `422` is returned otherwise. Leaderboard `limit` is 1 to 100.
- _SQL injection._ All database access goes through SQLAlchemy and Django, which send values separately from the query.
- _Redis failure._ If Redis is down or empty, the leaderboard falls back to PostgreSQL. This is tested.
- _Cross site request forgery on the JSON endpoints._ The register and login endpoints are exempt from CSRF on purpose. They use no cookies, so there is nothing for a forged page to ride on. The admin panel keeps full CSRF protection.
- _Any website reading the API from a browser._ CORS allows only my landing page address, only `GET`, no cookies and no wildcard. A browser `POST` from the landing page is refused. Four tests cover this.
- _Raw server text on screen._ The game shows only plain string messages from the server, and everything else becomes "Server error".

**Transport and hosting**

- _No HTTPS._ Render serves the API over HTTPS and Cloudflare serves the landing page over HTTPS. The game refuses any server address that is not `https`, except `localhost` and `127.0.0.1`, and this includes the trick address `localhost.evil.com`. Redirects are never followed, so credentials cannot be sent somewhere else.
- _Django knowing a request was secure._ Render handles HTTPS and passes plain http inside. Django trusts the `X-Forwarded-Proto` header for this, which is safe because only Render's front door can reach the server.
- _Admin cookies and HSTS._ In production the session and CSRF cookies are `Secure`, and HSTS is sent for one year.
- _Admin login forged from another website._ `CSRF_TRUSTED_ORIGINS` lists only the real HTTPS address. Checked live: my origin is accepted and a foreign origin gets `403`.
- _Detailed error pages leaking code._ `DEBUG` is off unless `DEBUG=1` is set, and only my own computer sets it. An unknown address returns a plain "Not Found".
- _Host header attacks._ `ALLOWED_HOSTS` comes from the environment and defaults to localhost. A foreign host name gets `400`.
- _Unencrypted database connection._ `sslmode=require` reaches the driver, and Neon enforces it.
- _Secrets on GitHub or in the image._ Real secrets exist only in Render's environment. `.env` is ignored by git, `.env.example` has placeholders, and the image build uses dummy values. `SECRET_KEY` and `JWT_SECRET` are separate on purpose.
- _Untested code going live._ Render deploys only after CI checks pass.
- _Accounts that hold the secrets._ Two factor login on GitHub, Render, Neon and Cloudflare is part of my deployment checklist.
- _Django deployment check._ I ran `check --deploy` on the production settings. The remaining warnings are accepted on purpose: the HTTPS redirect (Render already redirects, and the game refuses http), the subdomain and preload HSTS options (wrong for a shared `onrender.com` address), and the email warning (this project sends no email).

**The landing page**

- _Script injection through player names._ Names are placed with `textContent`, never as HTML. I tested it in a real browser with the name `<img src=x onerror=...>`: it showed as text and nothing ran.
- _Injected scripts or foreign requests._ A Content Security Policy allows scripts and styles only from the site itself and requests only to the API address. The page also sends `nosniff`, no referrer, and frame blocking against clickjacking. Tested in a real browser under the same policy with no violations.

**The game**

- _Huge input and control characters._ Text boxes cap length (20 for new usernames, 128 for passwords) and ignore control keys.
- _Double clicks and late answers._ A button locks while a request is open, and a second Enter sends nothing. An answer that arrives after you left a screen is ignored. A late save answer cannot cause a second save. All tested.
- _Malformed server data._ Leaderboard and login answers are checked for shape before use.
- _Disk errors._ If the token file cannot be written, you stay logged in for the session.
- _One player's unsaved run saved for another._ Logging out clears the waiting run.
- _Guest runs counted._ Guest runs and rounds left with `Esc` are never sent.

**The exe**

- _An unsigned exe and no proof that it is mine._ A SHA256 checksum is built in the release job and published next to the exe, and the landing page explains the SmartScreen warning and the check. I did not pay for a code signing certificate.
- _A fake or tampered release._ Releases are created only by the release workflow, which runs only on tags starting with `v`, and only I can push tags. The job has `contents: write` and nothing else, and uses no third party action.
- _A broken exe going out._ The release job runs all game tests first, then starts the built exe and fails if it closes by itself.
- _Secrets inside the exe._ The exe holds only the public server address. The job fails if the address variable is missing, so a local address is never shipped.
- _A build tool changing under me._ PyInstaller is pinned to an exact version in the release job.

### What I did not solve, and why

These are real, known gaps. I chose not to fix them for this low stakes project. For each one I say whether it can be fixed and whether I think it is needed.

| ID  | Issue                                                                                                                                                                                                          | Risk                                 | Can it be fixed?                                                                                                           | Do I need it?                                                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| B5  | The admin page at `/admin/` is public, so anyone can try passwords on it. The admin account has a long unique password.                                                                                        | Medium                               | Yes: rename the path, or limit login attempts                                                                              | The strong password limits the damage. The rest is optional.                            |
| B6  | No limit on wrong login attempts, so a script can guess passwords. The same goes for register spam.                                                                                                            | Medium to high                       | Yes: a small attempt counter in Redis per address                                                                          | **The most important open item.** I documented it instead of building it in this stage. |
| B7  | Score cheating. A modified client can send any score up to 100000, while normal play tops out far lower (about 12,500 by my estimate from the wave rules).                                                     | Medium for the leaderboard's honesty | Partly: a tighter cap is one line and a rate limit on `/scores` is small. Replaying every game on the server is too heavy. | The cap yes, the rest optional                                                          |
| B8  | The server does not enforce the 20 character username limit. A direct request could create a long name that collides with another after it is cut to 20.                                                       | Low                                  | Yes, one line in the register code                                                                                         | Nice to have                                                                            |
| B9  | If the server saves a run but the answer is lost, the game retries and the run is saved twice. The total run count goes up by one extra. The best score is not affected.                                       | Low                                  | Yes, with a run id sent by the game                                                                                        | No                                                                                      |
| B10 | A token cannot be cancelled before its 1 day is over. Logout only deletes the local copy.                                                                                                                      | Low                                  | Yes, with a server side deny list                                                                                          | No. It lives 1 day and can only post scores.                                            |
| B11 | The token file is not encrypted on disk.                                                                                                                                                                       | Low                                  | Yes, with the Windows credential store                                                                                     | No. Same level of risk as most game launchers.                                          |
| B12 | One password box on register. A typo locks out a new account, and there is no reset because I send no email.                                                                                                   | Medium for users                     | Yes, a second box                                                                                                          | Worth it. An admin can reset a password by hand.                                        |
| B14 | Nothing watches the dependency list for known vulnerabilities.                                                                                                                                                 | Low to medium                        | Yes, GitHub Dependabot with one small file                                                                                 | Good practice                                                                           |
| B15 | Redis keeps a score after an admin deletes it, until the server restarts.                                                                                                                                      | Low                                  | Yes                                                                                                                        | No                                                                                      |
| B16 | No limit on request body size at the FastAPI layer. Pydantic rejects bad shapes but still reads the body.                                                                                                      | Low                                  | Yes                                                                                                                        | No. Render has its own limits.                                                          |
| B17 | `/docs` (the API documentation page) is public.                                                                                                                                                                | Very low                             | Yes                                                                                                                        | No                                                                                      |
| B18 | Usernames are not moderated.                                                                                                                                                                                   | Low                                  | Yes, by deleting the user in the admin panel                                                                               | No. I handle it by hand.                                                                |
| B19 | Packages are not pinned. `requirements.txt` uses minimum versions, and the Docker base image is not pinned to a digest. A bad new release would be installed on the next deploy. (Only PyInstaller is pinned.) | Low                                  | Yes, with a lock file                                                                                                      | No for a low stakes project                                                             |
| B20 | The free hosting tiers have no protection against floods of requests and no real backups of the database.                                                                                                      | Low                                  | Partly, Cloudflare in front of the API                                                                                     | No. Losing the database means losing all scores, which I accept.                        |
| B21 | Antivirus programs sometimes flag exes made by PyInstaller as a virus by mistake.                                                                                                                              | Medium for downloads                 | Partly: signing, a folder build, reporting the false positive                                                              | No. I explain it in the README and publish the checksum.                                |

One more known behavior is described in the limitations below: the expired token case.

**Reporting a vulnerability.** If you find one, please contact me through my [GitHub profile](https://github.com/Stray3rdBorn) and do not post it in a public issue.

## Known limitations

- **The server sleeps.** On the free plan, the first request after 15 minutes of silence takes about a minute. The game waits up to 70 seconds and the landing page up to 90 seconds.
- **An expired token while a run ends.** Tokens last 1 day. If the token has expired when a run ends, the server answers `401`. The game keeps the run in memory, asks you to log in, and saves the run right after you log in. If you close the game before logging in again, that run is lost. I decided not to build a refresh token system, because the cost is high for a low stakes game, and I documented the behavior instead.
- **The leaderboard is only as honest as the clients.** See B7.
- **The exe is not signed.** See the download steps for the SmartScreen warning and the checksum.
- **Windows only.** The exe is built for Windows. The game itself runs from source on any system with Python and Pygame.
- **There is no password reset.** There is no email. An admin can set a new password in the admin panel.

## How the game works inside

The whole game is one loop that runs 60 times per second: read input, update the game state, draw the frame, repeat.

- **Game loop.** Update and draw are separate steps. State changes happen as numbers inside Python objects, and the screen is repainted from those numbers every frame.
- **Delta time.** All movement is multiplied by the seconds since the last frame, so speed stays the same on slow and fast machines. The value is capped at 0.05 seconds to avoid large jumps after a freeze.
- **State machine.** The game is always in exactly one state: `menu`, `playing`, `victory` or `game_over`. Each frame runs only the code for the current state.
- **Screens.** Above the gameplay, a screen manager holds exactly one active screen (menu, login, register, leaderboard, dashboard, play, game over). Each screen has `handle_event`, `update` and `draw`, and switching a screen replaces the active one.
- **Vector movement.** Movement is direction times speed times delta time. Directions are normalized so diagonal movement is not faster.
- **Circle collision.** Every object is a circle, and two objects collide when the distance between their centers is smaller than the sum of their radii.
- **Data driven enemies.** One `Enemy` class holds HP, radius, color, speed and points. A tank is the same class created with different values, chosen by a weighted random roll when it spawns.
- **Network without freezing.** Every server call runs in a background thread and puts its result in a queue. The main loop reads the queue once per frame, so the window never freezes, even while the server wakes up.
- **A session object.** One `Session` holds the token and the username. It loads the saved token at startup, throws away an expired one, and clears itself on logout.

## Roadmap

- A boss enemy, saved for later.
- A login attempt limit (B6), a second password box (B12) and Dependabot (B14), the three items I would do first.

## License

MIT. See [LICENSE](LICENSE).

## Contact

I am Wahid, ([Stray3rdBorn](https://github.com/Stray3rdBorn) on GitHub). For bugs and questions about the project, open an issue in this repository.
