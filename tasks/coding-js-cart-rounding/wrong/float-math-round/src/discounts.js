// Per-line percentage discounts, in integer cents.
const { pctOf } = require("./money");

// Discount on one line, rounded to the cent (half up).
function discountFor(lineCents, pct) {
  return pctOf(lineCents, pct);
}

module.exports = { discountFor };
