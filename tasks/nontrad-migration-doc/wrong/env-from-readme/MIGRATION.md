# Retiring legacy_db

## Call sites

- `app/orders/service.py`: `open_orders` and `cancel` read and update orders.
- `app/billing/invoices.py`: `unpaid` lists unpaid invoices (via `legacy_db.query_raw`).
- `app/admin/tools.py`: `purge_test_customers` deletes test customers (imported as `qr`).

## Schema

Current schema version: 14

No new schema version is needed: the switch only changes how we connect, not the tables.

## Environment

- `ORDERS_DB_URL`
- `ORDERS_DB_POOL`
- `LEGACY_DB_TIMEOUT_S`
- `BILLING_CURRENCY`
- `DB_PASSWORD`
- `ORDERS_DB_REPLICA`

## Rollback

Migrate one module per release behind a revert-able commit. If a module misbehaves,
revert that commit; `app/legacy_db.py` stays in place until all three are migrated.
