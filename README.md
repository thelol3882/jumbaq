# jumbaq

*Jumbaq* is Kazakh for "riddle". A detective game for the evening that kids play in their own home.

A parent opens the site, with no login, and does a one-minute setup: the kids' nicknames and ages, the rooms, and a checklist of household objects. Then the family plays a case of 5 episodes, one per evening. The parent reads the episode aloud, a riddle points at a real object in the home, the kids find it, and the parent types the answer. Each episode also gives a clue about one of three suspects. After episode 5 the child accuses a suspect.

Episodes are written by an LLM as strict JSON and checked by code before anyone sees them.

## Run it

Needs Docker and [uv](https://docs.astral.sh/uv/).

```sh
make up      # postgres, redis, migrations, the API and the worker
make test    # all backend tests, on the test database of `make up`
make lint    # ruff and the import-linter contracts
```

The API is on http://localhost:8000/api/v1, its docs on http://localhost:8000/api/v1/docs.

## Layout

```
backend/   FastAPI API and arq worker (package jumbaq)
infra/     the local Docker Compose stack and the database setup
deploy/    the server: its Docker Compose file and nginx behind Cloudflare
brand/     logo, colours, type and tokens for the web app
```

How the backend is built and the rules for changing it: [backend/AGENTS.md](backend/AGENTS.md).

## Deploy

[Luxen](luxen.yaml) builds the backend image, pushes it to ghcr.io and deploys it to the server with `deploy/docker-compose.yml`. The API is at https://api.jumbaq.fun. The server `.env` comes from `.env.example`.
