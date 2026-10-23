# Retiring legacy_db

## Call sites

- `app/orders/service.py`: `open_orders` and `cancel` read and update orders.
- `app/billing/invoices.py`: `unpaid` lists unpaid invoices (via `legacy_db.query_raw`).
- `app/admin/tools.py`: `purge_test_customers` deletes test customers (imported as `qr`).

## Schema

Current schema version: 14

No new schema version is needed: the switch only changes how we connect, not the tables.

## Environment

- `ORDERS_DB_URL`: database URL; still needed by the session layer.
- `ORDERS_DB_POOL`: pool size; still needed by the session layer.
- `LEGACY_DB_TIMEOUT_S`: only used by legacy_db; drop after the migration.
- `BILLING_CURRENCY`: billing display currency; unrelated, unchanged.

## Rollback

Flip `USE_SESSION` off in `app/config/flags.py` and redeploy; legacy_db stays in place until
all call sites are migrated and verified in staging.
