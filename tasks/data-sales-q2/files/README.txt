Order export, January-September 2026.

orders.csv  one row per order. Rows from the legacy store use MM/DD/YYYY dates.
            unit_price is what the customer paid per unit, in `currency`;
            list_price is the catalog price in USD.
            The export job retried some pages, so a few rows appear more than once.
fx.csv      monthly conversion rates: 1 unit of `currency` = usd_per_unit USD.
