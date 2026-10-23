const test = require("node:test");
const assert = require("node:assert");
const path = require("node:path");
const { checkout } = require(path.join(process.cwd(), "src", "cart"));
const cases = require(process.env.CART_CASES);

test("hidden carts", () => {
  let bad = [];
  for (const c of cases) {
    const got = checkout(JSON.parse(JSON.stringify(c.cart)));
    const pick = { subtotal: got.subtotal, discount: got.discount, tax: got.tax, total: got.total };
    try { assert.deepStrictEqual(pick, c.want); } catch (e) { bad.push({ cart: c.cart, got: pick, want: c.want }); }
  }
  assert.strictEqual(bad.length, 0, `${bad.length}/${cases.length} carts wrong, e.g. ${JSON.stringify(bad[0])}`);
});
