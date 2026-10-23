-- 002: users.email must be present and unique, ignoring case.
UPDATE users SET email = 'user' || id || '@placeholder.invalid' WHERE email IS NULL;
UPDATE users SET email = lower(email) || '+' || id WHERE id IN (
    SELECT u.id FROM users u JOIN users v ON lower(u.email) = lower(v.email) AND u.id > v.id);
-- SQLite can't add NOT NULL to an existing column, so rebuild the table.
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT
);
INSERT INTO users_new (id, email, name) SELECT id, email, name FROM users;
DROP TABLE users;
ALTER TABLE users_new RENAME TO users;
CREATE UNIQUE INDEX users_email_unique ON users (lower(email));
