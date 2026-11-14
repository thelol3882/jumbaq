# jumbaq

*Jumbaq* is Kazakh for "riddle". A detective game for the evening that kids play in their own home.

A parent opens the site, with no login, and does a one-minute setup: the kids' nicknames and ages, the rooms, and a checklist of household objects. Then the family plays a case of 5 episodes, one per evening. The parent reads the episode aloud, a riddle points at a real object in the home, the kids find it, and the parent types the answer. Each episode also gives a clue about one of three suspects. After episode 5 the child accuses a suspect.

Episodes are written by an LLM as strict JSON and checked by code before anyone sees them.

## Run it

Needs Docker and [uv](https://docs.astral.sh/uv/).

```sh
make up      # postgres, redis, migrations, the API, the worker and the web app
make test    # all backend tests, on the test database of `make up`
make lint    # ruff and the import-linter contracts
```

The web app is on http://localhost:3000, the API on http://localhost:8000/api/v1 and its docs on http://localhost:8000/api/v1/docs.

## Layout

```
backend/   FastAPI API and arq worker (package jumbaq)
web/app/   Next.js web app at jumbaq.fun (standalone server)
infra/     the local Docker Compose stack and the database setup
deploy/    the server: its Docker Compose file and nginx behind Cloudflare
brand/     logo, colours, type and tokens for the web app
```

How the backend is built and the rules for changing it: [backend/AGENTS.md](backend/AGENTS.md). The web app: [web/app/AGENTS.md](web/app/AGENTS.md).

## Limitations

There are no accounts. A family lives in a cookie on one browser for a year. A new phone, another browser or cleared browser data loses the family and its progress. For a subscriber that also means the subscription can't be managed from the new device.

## Roadmap

An optional email to save the family and move it to another device. Playing as a guest stays the default.

## Switching Claude on and off

The owner pays for the model, so the owner decides when it runs. The switch and the daily limit of model calls for all families together live in the database and are changed from the server, with no HTTP endpoint. While the model is off, every family still plays: new cases and episodes use the built-in ones. Until the switch is used for the first time, the settings decide (`JUMBAQ_AI_PROVIDER` and `JUMBAQ_AI_DAILY_CALL_LIMIT`).

On the server, from the folder with `docker-compose.yml`:

```sh
docker compose -f deploy/docker-compose.yml exec api python -m jumbaq.ai.control status
docker compose -f deploy/docker-compose.yml exec api python -m jumbaq.ai.control on
docker compose -f deploy/docker-compose.yml exec api python -m jumbaq.ai.control limit 1000
docker compose -f deploy/docker-compose.yml exec api python -m jumbaq.ai.control off
```

`status` prints whether the model is on, the daily limit, today's calls and whether each value comes from the table or the settings. A change applies to the next model call, with no restart. `limit` stays when the model is switched off and on. On a laptop, `make ai-status`, `make ai-on`, `make ai-off` and `make ai-limit n=1000` do the same inside the running stack.

## Deploy

[Luxen](luxen.yaml) builds the backend and web images, pushes them to ghcr.io and deploys them to the server with `deploy/docker-compose.yml`. The web app is at https://jumbaq.fun, the API at https://api.jumbaq.fun. The server `.env` comes from `.env.example`.
