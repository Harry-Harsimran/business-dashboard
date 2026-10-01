# Pulse Dashboard

Multi-page Flask business dashboard — revenue, profit, growth, KPIs.
Glassmorphism UI, SQLite backend, sample dataset included.

## Quick start (no install)

```bash
pip install -r requirements.txt
python run.py
```

Opens at http://127.0.0.1:5000 — DB auto-generates on first run.

## Install as a package (optional)

```bash
pip install -e .
pulse-dashboard
```

This registers a `pulse-dashboard` command that does the same thing as
`python run.py`, from anywhere on your system.

## Regenerate sample data

```bash
python db.py
```

Drops and rebuilds `dashboard.db` from `schema.sql` + `generate_data.py`.
Swap `generate_data.py` for real inserts, or point `db.get_connection()`
at your production database, to go live.

## Project layout

```
run.py              entry point — auto-inits DB, starts server
app.py               Flask routes (/  /revenue  /profit  /growth  /kpis)
db.py                 all SQL — KPI queries computed from live tables
generate_data.py      builds the sample dataset (customers, orders, spend)
schema.sql             table definitions
templates/              Jinja pages, one per route
static/style.css        shared glassmorphism theme
```
