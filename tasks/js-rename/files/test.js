const assert = require("assert");
const { getUserName } = require("./src/user");
const { greet } = require("./src/greeting");
const { report } = require("./src/report");

assert.strictEqual(getUserName({ first: "Ada", last: "Lovelace" }), "Ada Lovelace");
assert.strictEqual(getUserName({ nickname: "ada" }), "ada");
assert.strictEqual(getUserName(null), "anonymous");
assert.strictEqual(greet({ nickname: "bob" }), "Hello, bob!");
assert.strictEqual(report([{ nickname: "a" }, { first: "B", last: "C" }]), "a, B C");
console.log("all tests passed");
