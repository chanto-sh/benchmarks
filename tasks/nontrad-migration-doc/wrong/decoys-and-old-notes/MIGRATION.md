# Retiring legacy_db

## Call sites

- `app/orders/service.py`: reads and updates orders.
- `app/billing/invoices.py`: unpaid invoices.
- `app/admin/tools.py`: purges test customers.
- `app/reports/export.py`: monthly export via `query_raw_v2`.
- `app/inventory/stock.py`: stock levels.

## Schema

Current schema version: 12

## Environment

- `ORDERS_DB_URL`: database URL; still needed by the session layer.
- `ORDERS_DB_POOL`: pool size; still needed by the session layer.
- `LEGACY_DB_TIMEOUT_S`: only used by legacy_db; drop after the migration.
- `BILLING_CURRENCY`: billing display currency; unrelated, unchanged.

## Rollback

Migrate one module per release behind a revert-able commit. If a module misbehaves,
revert that commit; `app/legacy_db.py` stays in place until all three are migrated.
