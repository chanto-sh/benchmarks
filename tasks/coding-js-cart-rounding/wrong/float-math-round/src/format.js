// Money as a plain "1234.50" string for receipts and the API (input: integer cents).
function fmt(cents) {
  const sign = cents < 0 ? "-" : "";
  const a = Math.abs(cents);
  return `${sign}${Math.floor(a / 100)}.${String(a % 100).padStart(2, "0")}`;
}

module.exports = { fmt };
