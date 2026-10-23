// Exact money helpers: amounts are integer cents.

// "19.99" or 19.99 -> 1999
function toCents(price) {
  const s = String(price).trim();
  const m = /^(-?)(\d*)(?:\.(\d{0,2}))?$/.exec(s);
  if (!m) throw new Error(`bad price ${price}`);
  const cents = Number(m[2] || "0") * 100 + Number((m[3] || "").padEnd(2, "0"));
  return m[1] ? -cents : cents;
}

// Percentage given as a decimal (up to 4 places) -> integer ten-thousandths of a percent.
function pctUnits(pct) {
  return Math.round(Number(pct) * 10000);
}

// cents * pct / 100, rounded half up, without floating point error.
function pctOf(cents, pct) {
  const num = BigInt(cents) * BigInt(pctUnits(pct));
  const den = 1000000n;
  return Number((2n * num + den) / (2n * den));
}

module.exports = { toCents, pctOf };
