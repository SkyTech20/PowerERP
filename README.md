# PowerERP

A small PowerERP-like ERP for demos and tests.

- The full ERP menu is visible (General Ledger, Accounts Payable, Purchasing, Accounts Receivable, Sales, Inventory, Production, HR / Payroll, Fixed Assets, Projects, CRM, Reports, Administration), but only these modules work:
  - **GL Accounts / Cost Centers**
  - **Suppliers**
  - **Invoices** (supplier / AP invoices, with lines, GL and cost center)
  - **Purchase orders** (with lines)
  - **Receptions** (with lines; picking a PO pre-fills the supplier and the lines)
- Each working module has a maintenance screen: list, search, sort, filter, create, edit, delete.
- **English / French** toggle in the top bar (remembered in the browser and per user).
- **Login and users:** every screen needs a login. **Administration → Users** (administrators only) creates, edits, deactivates and deletes users (username, name, email, role *Administrator* / *User*, language, password). Each user changes their own password by clicking their name in the top bar.
- **SkyAI integration:** the ERP also answers the PowerWARE web services that SkyAI calls (same paths, parameters and XML as the SkyAI mock API). SkyAI reads suppliers, GL accounts, POs and receptions from the ERP, and the invoice it creates at the end of its process shows up in **Invoices** (source "SkyAI").
- **SQLite database** (`db/powererp.db`, or `ERP_DB_PATH`): users and all ERP data are saved there after every change and survive a restart. An empty database is seeded from `data/*.json` (or `data/demo/`). **Dashboard → Reset demo data** restores the original data; **Dashboard → Clear all data** (`POST /api/clear`) empties everything, to start a demo from a blank ERP. Delete the database file to start over completely (users included).
- Taxes: on purchase orders and receptions, TPS (5%) and TVQ (9.975%) are calculated on subtotal + freight when the supplier has a TPS / TVQ number (supplier form, Terms & taxes). Existing records keep their stored taxes until a line, the freight or the supplier is changed.
- Demo dataset: with `ERP_DATASET=demo` (set by `docker\rebuild.ps1 -DemoData` / `rebuild.sh --demo-data`) the ERP loads the fictitious French data in `data/demo/` instead of `data/*.json`: GL accounts, cost centers, 5 suppliers and no invoices. It covers the 5 demo scenarios, and the matching invoice PDFs (in French) are in `demo-invoices/`:

  | # | Scenario | Supplier | Invoice | Data in the ERP |
  |---|---|---|---|---|
  | 1 | With PO, one reception | LUMPRO | LP-88310 | PO 500201 + reception 700201 |
  | 2 | With PO, reception missing | PAPCEN | PC-20511 | PO 500301 only; register the reception during the demo |
  | 3 | Without PO | HORIZN | H-2026-1042 | Supplier only |
  | 4 | With PO, PO and reception missing | SECNOR | SN-7742 | Supplier only; register PO 500401 and its reception during the demo |
  | 5 | With PO, two receptions | TECBUR | TB-24518 | PO 500101 + receptions 700101 and 700102 |

The demo data (1,135 suppliers, 351 GL accounts, 2,702 cost centers, POs and receptions) uses the same field names as the PowerWARE / SkyAI feeds (`cCode`, `cCC1`, `ttPOheader`, `NoReception`, ...).

## Run

### Python

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5050/ (change the port with the `PORT` environment variable).

The first start creates the administrator `admin` with the password in `ERP_ADMIN_PASSWORD`; without it a random password is printed in the console. Then create the other users in **Administration → Users**.

### Docker

```bash
docker build -t erp-sample .
docker run -d -p 5050:5050 -v "$PWD/powererp-data:/app/db" -e ERP_ADMIN_PASSWORD=change-me --name erp-sample erp-sample
```

The database is `/app/db/powererp.db` inside the container; mount `/app/db` (a folder or a named volume) to keep it when the container is recreated. SQLite needs no server: it is a file written by the ERP itself. Run a single ERP container per database file.

### Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `ERP_DB_PATH` | `db/powererp.db` (`/app/db/powererp.db` in Docker) | SQLite file |
| `ERP_ADMIN_USER` / `ERP_ADMIN_PASSWORD` | `admin` / random (printed in the log) | Administrator created when the database has no user |
| `ERP_SECRET_KEY` | random, saved in the database | Signs the login cookie |
| `ERP_COOKIE_SECURE` | off | `1` sends the login cookie over HTTPS only (set it behind HTTPS) |
| `ERP_API_KEY` | none | Lets scripts call `/api/...` without a login, and, when set, is required by the PowerWARE web services (header `X-API-Key`) |
| `ERP_DATASET` | full data | `demo` seeds from `data/demo/` |

## Security and SkyAI

- The screens and `/api/...` need a login (session cookie `powererp_session`, 12 hours), or the header `X-API-Key: <ERP_API_KEY>`. `/api/users` is for administrators. `GET /api/health` is open (Docker healthcheck).
- The PowerWARE web services (`/cgi-bin/...`, used by SkyAI) do not use the login. They stay open while `ERP_API_KEY` is empty, so SkyAI keeps working without any change. To protect them, set `ERP_API_KEY` and, in SkyAI **Configuration → APIs**, set each PowerERP API's authentication to *API Key*, in the header `X-API-Key`.

## Connect SkyAI to PowerERP

In SkyAI, open **Configuration → APIs** and, in every SkyAI / PowerWARE API, replace the mock API host (`http://skyai-api:5002`) with PowerERP host. The rest of the URL stays the same:

| SkyAI API | URL |
|---|---|
| PO Details | `http://<erp-host>:5050/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI/getPODetails.p` |
| Unbilled PO | `.../SkyAI/getUnbilledPO.p` |
| Unbilled Receiving | `.../SkyAI/getUnbilledReceiving.p` |
| Receiving Details | `.../SkyAI/getReceivingDetails.p` |
| GL Accounts | `.../SkyAI/getGLaccounts.p` |
| Supplier Terms | `.../SkyAI/getSupplierTerm.p` |
| Invoice creation without PO | `.../SkyAI/apInvoiceNoPO.p` (POST) |
| Invoice creation with PO | `.../SkyAI/apInvoiceWithPO.p` (POST) |

`<erp-host>` depends on where SkyAI runs:

- SkyAI backend running in Docker, PowerERP running on the host machine: `host.docker.internal`.
- Both in Docker: add PowerERP to the same network as the backend and use the service name, e.g. in `docker/docker-compose.yml`:

  ```yaml
  erp-sample:
    build:
      context: ../PowerERP
    container_name: erp-sample
    ports:
      - "5050:5050"
    networks:
      - invoice-dev-network
  ```

  and use `http://erp-sample:5050`.

What happens when SkyAI creates an invoice:

- `apInvoiceNoPO.p` / `apInvoiceWithPO.p` create the invoice in the ERP, with its lines (GL / cost centers for invoices without PO, receptions for invoices with PO). It is listed in **Invoices** with the "SkyAI" badge, as *Draft* when SkyAI sends `lIncomplete=true`, otherwise *Posted*.
- The receptions billed by an invoice with PO leave `getUnbilledReceiving.p`.
- A second invoice with the same supplier and invoice number is rejected with `Facture existante`, like PowerWARE. `?simulate_error=1`, or an invoice number containing `FAIL` / `ERROR`, also returns that error (same as the mock API).
- **Dashboard → Reset demo data** puts everything back for the next demo.

## Project structure

```
app.py          # Flask entry point: database, login, ERP and PowerWARE services
db.py           # SQLite storage (users, settings, ERP data)
auth.py         # Login, users API (/api/auth/..., /api/users) and access control
erp_api.py      # JSON API (/api/...) and static file serving
powerware_api.py # PowerWARE-compatible web services used by SkyAI
static/         # UI: index.html, app.js, i18n.js (EN/FR), styles.css — no build step
data/           # Seed data (JSON) for an empty database
```

## API

All endpoints return JSON. Lists accept `q` (search), `page`, `size`, `sort`, `dir` (`asc`/`desc`) and `f_<field>` filters.

| Resource | Endpoints |
|---|---|
| GL accounts | `GET/POST /api/gl-accounts`, `GET/PUT/DELETE /api/gl-accounts/<code>` |
| Cost centers | `GET/POST /api/cost-centers`, `GET/PUT/DELETE /api/cost-centers/<cc1>[/<cc2>]` |
| Suppliers | `GET/POST /api/suppliers`, `GET/PUT/DELETE /api/suppliers/<code>` |
| Purchase orders | `GET/POST /api/purchase-orders`, `GET/PUT/DELETE /api/purchase-orders/<po>` |
| Receptions | `GET/POST /api/receptions`, `GET/PUT/DELETE /api/receptions/<no>` |
| Invoices | `GET/POST /api/invoices`, `GET/PUT/DELETE /api/invoices/<id>` |
| Login | `POST /api/auth/login` `{username, password}`, `POST /api/auth/logout`, `GET /api/auth/me`, `POST /api/auth/password` `{current, password}` |
| Users (admin) | `GET/POST /api/users`, `GET/PUT/DELETE /api/users/<id>` |
| Other | `GET /api/health`, `GET /api/summary`, `GET /api/lookups/<suppliers\|gl\|cc\|po\|terms\|buyers>?q=`, `POST /api/reset`, `POST /api/clear` |

Errors come back as `{"error": "required" | "duplicate" | "numeric" | "not_found", "field": "..."}`.
