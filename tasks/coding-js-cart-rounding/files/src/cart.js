const { discountFor } = require("./discounts");
const { taxFor } = require("./tax");
const { fmt } = require("./format");

// Price a cart: { items: [{ sku, price: "19.99", qty, discountPct?, taxExempt? }], taxRate }.
// Returns { subtotal, discount, tax, total } as "0.00" strings (see README for the rules).
function checkout(cart) {
  let subtotal = 0;
  let discount = 0;
  let taxable = 0;
  for (const item of cart.items) {
    const line = Number(item.price) * item.qty;
    const d = discountFor(line, item.discountPct || 0);
    subtotal += line;
    discount += d;
    if (!item.taxExempt) taxable += line - d;
  }
  const tax = taxFor(taxable, cart.taxRate || 0);
  const total = subtotal - discount + tax;
  return { subtotal: fmt(subtotal), discount: fmt(discount), tax: fmt(tax), total: fmt(total) };
}

module.exports = { checkout };
