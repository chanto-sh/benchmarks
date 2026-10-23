// Per-line percentage discounts.
function discountFor(lineTotal, pct) {
  return (lineTotal * pct) / 100;
}

module.exports = { discountFor };
