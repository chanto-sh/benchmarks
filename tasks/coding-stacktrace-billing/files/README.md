# billing

Monthly invoice run: `python3 billing/run.py invoices/2026-08.csv` (rates from `rates.csv`,
or `$BILLING_RATES`). Each line is converted to the invoice currency and rounded to the cent.

Sample output:

```
INV-0801  acme-01  (USD)
  Hosting                    1200.00 USD ->    1200.00 USD
  Support hours               350.50 USD ->     350.50 USD
  TOTAL                                        1550.50 USD

INV-0802  globex eu  (EUR)
  Licences                    980.00 EUR ->     980.00 EUR
  Training                    410.25 EUR ->     410.25 EUR
  TOTAL                                        1390.25 EUR
```
