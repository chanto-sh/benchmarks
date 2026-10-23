# Blocked: no September ledger export

`reconcile()` is implemented and tested, but `python3 reconcile.py 2026-09` fails:
`exports/ledger_2026-09.csv` doesn't exist. Only the bank statement for September
(`exports/bank_2026-09.csv`) and the August ledger are present. I didn't produce
recon_2026-09.json; please re-export the September ledger from the GL and rerun.
