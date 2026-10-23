// Money as a plain "1234.50" string for receipts and the API.
function fmt(amount) {
  return amount.toFixed(2);
}

module.exports = { fmt };
