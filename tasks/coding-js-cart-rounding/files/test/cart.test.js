const test = require("node:test");
const assert = require("node:assert");
const { checkout } = require("../src/cart");

test("simple cart", () => {
  assert.deepStrictEqual(checkout({ items: [{ sku: "A", price: "10.00", qty: 2 }], taxRate: 10 }),
    { subtotal: "20.00", discount: "0.00", tax: "2.00", total: "22.00" });
});

test("discount and tax round per the README", () => {
  assert.deepStrictEqual(
    checkout({ items: [{ sku: "MUG", price: "19.99", qty: 3, discountPct: 15 }], taxRate: 8.25 }),
    { subtotal: "59.97", discount: "9.00", tax: "4.21", total: "55.18" });
});

test("receipt adds up", () => {
  const r = checkout({ items: [
    { sku: "A", price: "0.35", qty: 1, discountPct: 10 },
    { sku: "B", price: "1.15", qty: 3, discountPct: 50 },
    { sku: "C", price: "4.99", qty: 1, taxExempt: true },
  ], taxRate: 7.375 });
  assert.deepStrictEqual(r, { subtotal: "8.79", discount: "1.77", tax: "0.15", total: "7.17" });
});
