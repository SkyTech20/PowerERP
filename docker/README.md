# PowerERP with Docker: PostgreSQL + the ERP

`docker-compose.yml` in this folder runs PowerERP on its own, on a server: a PostgreSQL 16 database and the ERP.
Each project is one client, with its own database volume, port and backups folder.

| File | Use |
|---|---|
| `docker/docker-compose.yml` | the ERP on a server (this guide) |
| `docker/.env.example` | the settings to copy into `docker/.env` |
| `../docker-compose.yml` | development and tests: PostgreSQL on port 5433 (databases `powererp` and `powererp_test`) |
| `../../docker/docker-compose.demo.yml` | the demo server: SkyAI + PowerERP together |

## Start

```bash
cd PowerERP/docker
cp .env.example .env        # then set ERP_DB_PASSWORD and ERP_ADMIN_PASSWORD
docker compose up -d --build
docker compose ps           # db and erp "healthy" after ~30 s
```

PowerShell is the same, with `Copy-Item .env.example .env`.

- Open `http://localhost:5050/` (on the server) and sign in as `admin` with `ERP_ADMIN_PASSWORD`. The first start creates the tables (Alembic migrations) and the administrator.
- The port is published on `127.0.0.1` only (`ERP_BIND`): put nginx in front with HTTPS, or set `ERP_BIND=0.0.0.0` to open it on the network.
- The database is not published on the host. Only the ERP reaches it, inside the Docker network.
- Data: the volume `<project>_pgdata`. Backups: the folder `ERP_BACKUP_DIR` (default `docker/backups`).

## Every day

```bash
docker compose logs -f erp          # the ERP log
docker compose restart erp
docker compose down                 # stop (the data stays in the volume)
docker compose up -d                # start again
```

## Update to a new version

```bash
git pull
docker compose up -d --build        # rebuilds the image; the migrations run when the ERP starts
docker image prune -f               # removes the old images
```

New tables start empty on an existing database. On a demo, **Dashboard → Reset demo data** fills them.

## Backups

- **Administration → Backups** in the ERP: the interval, the folder (keep `/app/backups`, it is the mounted `ERP_BACKUP_DIR`) and how many copies to keep. The files are `powererp-YYYYMMDD-HHMMSS.dump` (`pg_dump --format=custom`).
- A copy by hand, from the server:

```bash
docker compose exec -T db pg_dump -U powererp -d powererp --format=custom > powererp-manual.dump
```

### Restore a backup

This replaces the whole database with the dump.

```bash
docker compose stop erp
docker compose exec -T db dropdb -U powererp --force powererp
docker compose exec -T db createdb -U powererp powererp
docker compose exec -T db pg_restore -U powererp -d powererp --no-owner < backups/powererp-20261120-030000.dump
docker compose start erp
```

## Several clients on one server

There is one project per client: its own `.env`, with another project name, port and backups folder.

```bash
cp .env.example client-b.env       # COMPOSE_PROJECT_NAME=powererp-client-b, ERP_PORT=5051, ERP_BACKUP_DIR=./backups-client-b
docker compose --env-file client-b.env up -d
docker compose --env-file client-b.env logs -f erp
```

Each project has its own volume (`powererp-client-b_pgdata`), so the databases never mix.

## HTTPS with nginx

Set `ERP_COOKIE_SECURE=1` in `.env` (the login cookie then travels over HTTPS only), then `docker compose up -d`. Example site:

```nginx
server {
    listen 443 ssl;
    server_name erp.example.com;
    # ssl_certificate / ssl_certificate_key (e.g. certbot)
    client_max_body_size 50m;
    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

## Start over (deletes everything)

```bash
docker compose down -v              # -v removes the database volume
docker compose up -d
```

## Build an image to push (demo server)

```bash
docker compose build                                   # ERP_IMAGE and ERP_DOCKERFILE from .env
docker push skytnttech/skyai-demo-erp-sample:latest    # when ERP_IMAGE is that name
```

With `ERP_DOCKERFILE=Dockerfile.demo` the image only carries the fictitious data of `data/demo` (set `ERP_DATASET=demo`).
