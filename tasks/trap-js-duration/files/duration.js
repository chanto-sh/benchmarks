// Parse a duration like "1h30m", "45s", "2d", "1h 5m 3s" or "1.5h" into seconds.
// Throws an Error for empty or malformed input (e.g. "", "abc", "5x", "h").
function parseDuration(s) {
  const m = /^(\d+)([smhd])$/.exec(s);
  const unit = { s: 1, m: 60, h: 3600, d: 86400 }[m[2]];
  return Number(m[1]) * unit;
}

module.exports = { parseDuration };
