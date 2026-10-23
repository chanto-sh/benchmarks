# ratelimit changelog

## 2.4.1
- Fix refill drift when the clock goes backwards.

## 2.4.0
- `try_acquire()` for non-blocking callers.
- Injectable `clock` and `sleep` for tests.

## 2.3.0
- Thread-safe `acquire()`.
