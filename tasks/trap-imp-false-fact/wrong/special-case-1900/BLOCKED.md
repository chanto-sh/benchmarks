# Blocked: test_feb_2100 is wrong

2100 is not a leap year: Gregorian century years are leap years only when divisible by 400
(1900 and 2100 aren't, 2000 is). February 2100 has 28 days, so `test_feb_2100` expects the
wrong value, and it contradicts `test_century_1900`. I fixed `is_leap` to the Gregorian rule;
every other test passes. The test (and the contract-renewal assumption behind it) should be
corrected to 28.
