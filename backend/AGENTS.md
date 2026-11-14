# jumbaq backend: how to write code here

For people and AI agents. Read this before you change anything in `backend/`.

jumbaq is a web app for families with no login. A parent sets up the family (kids' nicknames and ages, rooms, household objects) and plays detective cases of 5 episodes that an LLM writes. The package is `jumbaq` in `backend/jumbaq`. Every module follows the pattern below, and `families` is the reference. New code and every new module follow this file.

## Stack

FastAPI, SQLAlchemy 2 (async) with asyncpg, PostgreSQL 18, Redis, arq, Alembic, Pydantic 2, uv, ruff, import-linter, pytest.

## Layout of a module

```
families/
  domain.py        frozen dataclasses and state rules, no imports from other layers
  errors.py        NoFamilySessionError(NotAuthenticatedError) with a fixed ErrorCode
  events.py        frozen dataclasses this module publishes
  models.py        ORM models (only repositories/sql.py and migrations use them)
  repositories/    families.py = Protocol, sql.py = SQLAlchemy version returning domain objects
  queries.py       read-only SQL for screens, returns view objects
  uow.py           FamiliesUoW(UnitOfWork) attaching the repositories and queries
  services/        classes, like families.py with FamilyService
  routers/         family.py
  schemas.py       request and response bodies
  deps.py          FamilyServiceDep, FamilyDep and other FastAPI wiring
  public.py        what other modules may import
  handlers.py      what happens after an event, run by the worker from the outbox
```

`families` has no `handlers.py` because it reacts to no event. `cases` shows one: `cases/handlers.py` with `CasesHandlers.family_created`.

## Starting a new module

1. Write `domain.py`, `errors.py`, `repositories/`, `queries.py` (screens only), `uow.py`, `services/` classes, `deps.py`, and `public.py` if other modules need something.
2. Other modules are used only through their `public.py`. If one has none yet, add it with the small thing you need (see `families/public.py`).
3. Add the module to `jumbaq/models.py`, to `main.py` (its routers) and, if it has handlers, to `build_handlers` in `worker/main.py`.
4. Add the module to the contracts at the end of `.importlinter`: one "through public" contract of its own (copy `cases-through-public`) and its name in the forbidden lists of the other contracts.
5. If its routers or `deps.py` use `FamilyDep`, add these two lines to `ignore_imports` of the `family-deps-only-in-routers-and-deps` contract (the commented example is there):
   ```
   jumbaq.<module>.routers.* -> jumbaq.families.deps
   jumbaq.<module>.deps -> jumbaq.families.deps
   ```
6. Pure rules in `domain.py` get unit tests.

## Rules

1. **Router:** HTTP only. Takes a service from `deps.py`, and `FamilyDep` where the endpoint acts for a family. Calls one service method, returns a schema. No SQL, no repositories, no business rules, no `try/except`. There are no roles.
2. **Service:** a class with its dependencies in `__init__`. Every method that acts for a family gets a `FamilyRef(family_id)` from `core/family.py`, never a `Request` and never a cookie. No `fastapi`, `starlette` or `sqlalchemy` imports.
3. **Transaction:** `async with self._uow() as uow:` and `await uow.commit()` for a change. Leaving the block without a commit rolls back, for every unit of work. Never open a session yourself: only `core.db.UnitOfWork` opens a transaction. It is `UnitOfWork(sessionmaker, *, nudge=None)`. A module's factory is a `Callable[[], XUoW]`, built in `deps.py` with `partial(XUoW, sessionmaker, nudge=nudge_worker(queue))`.
4. **Repository:** SQL only, returns domain objects. Domain rules stay in the service. There is no row-level security, so the repository filters by `family_id` itself: a method that reads or changes family data takes the family. A query in `queries.py` does the same.
5. **Reads vs changes (light CQRS):** a change goes service, domain object, repository. A screen that only shows data uses a query in `queries.py`: one SQL query with joins, view objects straight to the response. Queries run in a unit of work and never change data.
6. **Time:** from the injected `Clock`, never `datetime.now()`. Every time users see or rules use is set by the service from the `Clock`. `now()` in the database only fills technical columns.
7. **Other modules:** import only their `public.py`. For something that happens after a change, use an event (rule 8), not a call into their service.
8. **Side effects** (plan the next case, call the LLM): `await uow.publish(Event(...))` with an event from your `events.py`. It goes to the `outbox` table in the same transaction, and the worker runs the handler after the commit. Never call another module's service in the middle of a transaction. Every event has `family_id`, and the handler opens its own unit of work for that family. An event carries only ids: never a secret or personal data (the outbox is kept in the database and its backups), so the handler loads what it needs. A handler must be safe to run twice, because a row can be delivered again: `CasePlanning.open_first` uses `ON CONFLICT DO NOTHING`. In a handler, raise temporary errors (network, Redis, LLM 429 or 5xx) so the outbox retries them. After 5 failed attempts a row gets `failed_at`. There is no command to send it again yet. The worker takes due rows directly with `FOR UPDATE SKIP LOCKED`, so many workers are safe.
9. **Errors:** raise the named errors of your `errors.py`. A new code goes into `core/error_codes.py`. Never rename a code value, because the web app will use it as a translation key.
10. **Family:** comes only from the session cookie (`FamilyDep` in `families/deps.py`), never from the URL or the body. Only routers and `deps.py` use `FamilyDep`. Services, handlers and the worker get a `FamilyRef`.
11. **Nothing is deleted:** the app connects as `jumbaq_app`, which can SELECT, INSERT and UPDATE but has no DELETE. Change a status instead. The tables belong to `jumbaq_owner`, which runs the migrations.
12. **CSRF:** every non-GET request under `/api/v1` needs the header `X-Requested-With: jumbaq` (`core/csrf.py`, added on the API router in `main.py`). Tests and clients send it.
13. **Comments:** only where they explain why. Names should say what.

## Adding an endpoint

1. Schema in `schemas.py`, with `Annotated` types and field validators.
2. Method on the service, with the rules and the errors. Add a repository method only if the storage needs one.
3. Endpoint in `routers/`, with `FamilyDep` if it acts for a family, and the service from `deps.py`.
4. A new event, if something else should react, plus its handler in `handlers.py` and its line in `build_handlers` in `worker/main.py`.
5. Tests: the happy path, every error code, no cookie gives 401, another family's data gives 404.

## Adding an error code

1. `core/error_codes.py`: `DOMAIN_NAME = "domain.name"`. The value will be a translation key in the web app, so it never changes once used.
2. Your module's `errors.py`: a named error with that code.

There is no web app yet. When it comes, it adds the same values to its translations.

## Adding a table

1. Model in `<module>/models.py`, and import the module in `jumbaq/models.py`.
2. Family data has a `family_id` foreign key to `family.id`.
3. `make migration m="add something"`. Read the file and tidy it before you commit it.
4. `make test`.

`case` and `user` are reserved words in PostgreSQL. Name such tables like `case_file`. The default privileges give `jumbaq_app` SELECT, INSERT and UPDATE, so a migration needs no grants.

## Tests

- Real PostgreSQL and Redis from `make up`: the `jumbaq_test` database and Redis database 1. No fake repositories.
- Tests never clean the database. Every test makes its own family with `create_family` from `tests/flows.py`.
- API tests use the `live_client` fixture, so they go through the real app as `jumbaq_app`.
- Handler tests call `OutboxDelivery.deliver_due()` with `build_handlers` of the worker, because no worker runs in the tests. The `quiet_outbox` fixture marks the rows of earlier tests processed first. See `tests/test_first_case.py`.
- Check that a new test can fail: break the rule in the code on purpose, run the test, and put the code back.

## Commands

From the repository root, with `make up` running:

- `make test`: all tests.
- `make test-unit`: tests that need no services.
- `make lint`: ruff, the format check and import-linter. import-linter enforces the rules above, so a broken contract means the code is in the wrong layer, not that the contract is wrong.
- `make fmt`: fixes the format.
- `make migration m="add something"`: a new migration. Read the file before you commit it.

## Pull requests and commits

- Commits: one line, `type: title`. Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`.
- The title is a plain lower-case English phrase that says what changed. Examples:
  - `feat: show when a user was last active in the user list`
  - `fix: keep the day arrows of the board in place when the day changes`
  - `refactor: share the search box of the customer list`
  - `test: compare the health migration with the newest one`
  - `docs: describe the platform chain and the lock order of the audit chains`
- No body. No trailers of any kind: no `Co-Authored-By`, no "Generated with", no session links, no `Signed-off-by`.
- Small commits, one topic each.
- Run `make lint` and `make test` before every commit.
- Do not push and do not open pull requests unless asked.
- Do not change `.importlinter` to make a check pass. If a rule is wrong, change it on its own and say why.
- Changes to `core/`, `.importlinter`, `migrations/` or this file need a review by Dias.
