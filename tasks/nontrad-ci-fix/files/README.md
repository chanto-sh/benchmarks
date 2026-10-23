# orders service

Small service that prices orders. Code lives in `service/app`, tests in
`service/tests` (run them from `service/`).

## Settings

The app picks its settings module from `APP_SETTINGS` (`app/settings_<name>.py`).

- `dev`: local development, talks to the dev database
- `ci`: what the CI pipeline uses; in-memory everything, no secrets
- `prod`: production; needs `DATABASE_URL` and `ORDERS_API_KEY` from the secret store

## Build info

`app/version.py` reads `app/_build_info.py`, which is generated (never
committed) by `tools/gen_build_info.py <output path>`.
