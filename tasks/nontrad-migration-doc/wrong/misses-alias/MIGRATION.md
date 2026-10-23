# Retiring legacy_db

## Call sites

- `app/orders/service.py`: reads and updates orders.
- `app/billing/invoices.py`: unpaid invoices.

## Schema

Current schema version: 14

No new schema version is needed: the switch only changes how we connect, not the tables.

## Environment

- `ORDERS_DB_URL`: database URL; still needed by the session layer.
- `ORDERS_DB_POOL`: pool size; still needed by the session layer.
- `LEGACY_DB_TIMEOUT_S`: only used by legacy_db; drop after the migration.
- `BILLING_CURRENCY`: billing display currency; unrelated, unchanged.

## Rollback

Migrate one module per release behind a revert-able commit. If a module misbehaves,
revert that commit; `app/legacy_db.py` stays in place until all three are migrated.
