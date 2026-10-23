// Sales tax on the taxable part of a cart. `rate` is a percentage, e.g. 8.25.
function taxFor(amount, rate) {
  return (amount * rate) / 100;
}

module.exports = { taxFor };
