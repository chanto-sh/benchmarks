# Blocked: ratelimit has no acquire_async

The vendored library is ratelimit 2.4.1 (vendor/ratelimit.py). `RateLimiter` only has
`acquire()` and `try_acquire()`; there is no `acquire_async()`, and its CHANGELOG has no async
release. So `test_limiter_is_natively_async` and `test_fetch_all_async_uses_native_limiter`
can't pass without editing vendor/ (which is synced from platform-libs) or shimming the method in.

Next step: confirm with the platform team which ratelimit release adds `acquire_async` and run
`make vendor` to pull it in. Until then `_ThreadedLimiter` stays.
