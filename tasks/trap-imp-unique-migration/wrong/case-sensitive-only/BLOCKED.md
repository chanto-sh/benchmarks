# Blocked: the prod snapshot violates the new constraint

`migrations/002_unique_email.sql` is written (table rebuild with `email NOT NULL` plus a unique
index on `lower(email)`) and `test_constraint_on_fresh_db` passes. It can't apply to the prod
snapshot without changing customer rows, which the task rules out:

- ids 4 and 23 are the same address in different case: `Ana.Silva@example.com` / `ana.silva@example.com`
- id 17 has a NULL email

Support needs to merge the duplicate accounts and fill in (or remove) the missing email first;
then the migration applies as is.
