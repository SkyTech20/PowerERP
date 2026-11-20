# PowerERP: how the code is organized

All the server code is in `powererp/` (the plan was Docs/PowerERP-Organizacao-Codigo.md in the Workflow folder);
`app.py` only builds the app. New code follows these rules.

## Layers

```
api (Flask routes)  ->  service (business rules)  ->  repository (database)  ->  models (tables, migrations)
        \-- schemas (API format <-> domain objects)
```

- **api**: reads the request, calls one service method, returns JSON. No business rule, no SQL.
- **service**: a class per responsibility, its dependencies (repositories, other services) given in `__init__`.
  No Flask import: a service can be tested without the web app.
- **repository**: the only place that reads or writes tables (`powererp/db`, SQLAlchemy Core).
- **schemas**: translate the API / PowerWARE format (`cCode`, `"12.50"`) to domain objects and back.
- **powererp/core**: errors (`AppError`), value parsing (`values`), pagination, HTTP helpers. Shared, no rules.
- **powererp/factory.py**: `create_app()` builds the app and registers the services in the `Container`.
  No module-level state.

## Rules

- Errors: raise `AppError(code, field)` (or a subclass); one handler turns it into `{"error", "field"}`.
- One transaction per request (`powererp.database.current()`); never commit inside a service.
- New tables only through an Alembic migration (`alembic revision --autogenerate -m "..."`, then review it).
- Type hints on public functions and methods.
- Before a commit: `ruff check .`, `black .`, `mypy`, `python -m pytest` (the CI runs the same).
- Tests: the API tests in `tests/` are the contract (screens, SkyAI); add unit tests for every service.

## Front-end (`static/`)

Plain ES modules loaded by the browser (`<script type="module" src="assets/js/main.js">`): no bundler, no build step.

- **core.js**: shared helpers only (`t`, formatting, `api`, toasts). It imports no other module.
- **state.js**: the shared state (user, screen shown, lookup cache). Other modules read the exported
  variables and change them only through the setters (`setUser`, `setView`, `setPrefill`).
- **resources/*.js**: a new screen of an existing kind is a list / form definition added to `RES`
  (`Object.assign(RES, {...})`), not new rendering code.
- **screens/*.js**: one file per screen that is not a generic list or form.
- Every text through `t("key")`, with the key in EN and FR in the `i18n*.js` file of its area (plain scripts, `window.ERP_I18N`).
- Avoid import cycles with `core.js`: give it a callback instead (see `setUnauthorizedHandler`).
