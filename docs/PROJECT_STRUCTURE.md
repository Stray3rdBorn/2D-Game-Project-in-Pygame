# Project structure

```
project root                              everything lives here
├── README.md                      [C]    full project description, architecture, security summary
├── LICENSE                        [C]    MIT license
├── docs/                                 documents about the project
│   ├── PROJECT_STRUCTURE.md       [C]    this file
│   ├── SECURITY_LOG.md            [C]    every security issue: covered, how, and still open
│   └── screenshots/                      game screenshots for the README
├── requirements.txt               [C]    packages the game needs (pygame, requests)
├── pytest.ini                     [C]    tells pytest to look in the tests folder
├── .gitignore                     [C]    files git must never upload (venv, .env)
├── docker-compose.yml             [C]    starts database, Redis and server together on GitHub CI
├── .github/                              GitHub settings folder
│   └── workflows/                        automation scripts
│       ├── ci.yml                 [C]    runs all tests and the Docker check on every push
│       └── release.yml            [C]    on a version tag: tests, builds the exe, publishes the release
│
├── client/                               the game the player runs
│   ├── main.py                    [W]    gameplay: player, enemies, waves, scoring
│   ├── app.py                     [W]    start file: builds the screens, runs the game loop
│   ├── views.py                   [W]    every screen: menu, login, register, leaderboard, dashboard, play, game over
│   ├── screens.py                 [W]    screen switcher, holds the session and network
│   ├── ui.py                      [W]    own widgets: label, button, text box
│   ├── network.py                 [W]    talks to the server in the background
│   ├── storage.py                 [W]    saves and loads the login token on disk
│   ├── paths.py                   [W]    the one folder where the game saves its files
│   └── server_address.py          [W]    the server address, replaced by the release build
│
├── tests/                                tests for the game
│   ├── conftest.py                [W]    shared test setup (no window, finds client folder)
│   ├── test_game.py               [W]    gameplay tests
│   ├── test_storage.py            [W]    token file tests
│   ├── test_paths.py              [W]    save folder and default address tests
│   ├── test_network.py            [W]    server call tests with a fake server
│   ├── test_ui.py                 [W]    widget tests
│   ├── test_screens.py            [W]    screen switcher tests
│   └── test_views.py              [W]    every screen and every flow
│
└── server/                               everything that runs on the server
    ├── Dockerfile                 [C]    recipe that packs the server into a Docker image
    ├── .dockerignore              [C]    files the image must not contain
    ├── requirements.txt           [C]    packages the server needs
    ├── requirements-dev.txt       [C]    server packages plus test tools
    ├── pytest.ini                 [C]    pytest settings for the server tests
    ├── .env                       [C]    real secrets and addresses (never on GitHub)
    ├── .env.example               [C]    same list with placeholders (public)
    ├── venv/                      [G]    private Python packages folder
    │
    ├── app/                              FastAPI: the part the game talks to
    │   ├── __init__.py            [G]    empty file that makes this a Python package
    │   ├── main.py                [W]    endpoints: /health, /scores, /leaderboard, /me
    │   ├── auth.py                [W]    reads and checks the token on each request
    │   ├── django_app.py          [W]    plugs Django into FastAPI
    │   ├── database.py            [W]    PostgreSQL connection
    │   ├── models.py              [W]    the Score table
    │   ├── schemas.py             [W]    shapes of requests and answers
    │   ├── ranking.py             [W]    leaderboard logic, Redis first, PostgreSQL fallback
    │   └── cache.py               [W]    Redis connection
    │
    ├── tests/                            tests for the server
    │   ├── conftest.py            [W]    fake database, fake Redis, token maker
    │   ├── test_api.py            [W]    scores, leaderboard, /me, Redis failures
    │   └── test_auth.py           [W]    register, login, token expiry
    │
    └── web/                              Django: accounts and admin page
        ├── manage.py              [G]    Django command tool (migrate, createsuperuser)
        ├── staticfiles/           [G]    admin page styling, made by collectstatic
        ├── config/                       Django project settings
        │   ├── __init__.py        [G]    empty package file
        │   ├── asgi.py            [G]    default start point for Django
        │   ├── wsgi.py            [G]    default old style start point, if present
        │   ├── settings.py        [E]    I edited: secret key, database, whitenoise, static folder
        │   └── urls.py            [E]    I replaced it: admin and the two api paths
        └── accounts/                     Django app for users
            ├── __init__.py        [G]    empty package file
            ├── apps.py            [G]    default app registration
            ├── models.py          [W]    Score table, read only
            ├── views.py           [W]    register and login endpoints
            ├── tokens.py          [W]    creates the login token
            ├── admin.py           [W]    shows scores in the admin page
            └── migrations/               database change history
                ├── __init__.py            [G]    empty package file
                ├── 0001_initial.py        [E]    generated, I edited 3 small spots
                └── 0002_remove_apikey.py  [G]    generated, deletes the old key table
```

## Interview order, most important first

1. `server/app/auth.py` and `server/web/accounts/tokens.py`: how tokens are made and checked, and why one secret is shared.
2. `server/app/main.py`, `ranking.py` and `cache.py`: the endpoints, the Redis leaderboard and the fallback to PostgreSQL.
3. `server/web/accounts/views.py` and `server/app/django_app.py`: register and login, and Django mounted inside FastAPI.
4. `client/network.py` and `client/storage.py`: background calls with a queue, and safe token storage.
5. `client/views.py`, `screens.py`, `ui.py` and `app.py`: the screens and how the game loop ties them together.
6. `server/tests` and `tests`: what is tested and why.
7. `docker-compose.yml`, `Dockerfile` and `ci.yml`: how GitHub builds and tests the whole stack.

For the two [E] files, `settings.py` and `urls.py`, explain only the lines I changed.
