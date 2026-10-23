const test = require("node:test");
const assert = require("node:assert");
const { parseDuration } = require("./duration");

test("single units", () => {
  assert.strictEqual(parseDuration("45s"), 45);
  assert.strictEqual(parseDuration("2d"), 172800);
});

test("combined units", () => {
  assert.strictEqual(parseDuration("1h30m"), 5400);
  assert.strictEqual(parseDuration("1h 5m 3s"), 3903);
});

test("decimals", () => {
  assert.strictEqual(parseDuration("1.5h"), 5400);
});

test("invalid input throws", () => {
  for (const bad of ["", "abc", "5x", "h", "1h-5m"]) {
    assert.throws(() => parseDuration(bad), Error, bad);
  }
});
