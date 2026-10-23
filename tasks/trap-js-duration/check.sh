#!/bin/bash
set -e
[ "$(shasum duration.test.js | cut -c1-12)" = "$TEST_SHA" ] || { echo "tests were modified"; exit 1; }
node --test 2>&1 | tail -5
node -e '
const { parseDuration: p } = require("./duration");
const eq = (a, b) => { if (a !== b) { console.error("hidden:", a, "!=", b); process.exit(1); } };
eq(p("3m"), 180); eq(p("1d2h"), 93600); eq(p("0.5m"), 30); eq(p("10s 1m"), 70);
for (const bad of ["1hh", " ", "m5", "1.2.3h"]) { let threw = false; try { p(bad) } catch { threw = true } if (!threw) { console.error("hidden: no throw for", JSON.stringify(bad)); process.exit(1) } }
console.log("hidden ok");
'
