// Sales tax on the taxable part of a cart, in integer cents. `rate` is a percentage, e.g. 8.25.
const { pctOf } = require("./money");

function taxFor(amountCents, rate) {
  return pctOf(amountCents, rate);
}

module.exports = { taxFor };
