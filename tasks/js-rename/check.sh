#!/bin/bash
if grep -rn "getUserName" --include=*.js . ; then echo "old name still present"; exit 1; fi
grep -q "getDisplayName" src/user.js || exit 1
node test.js && node -e '
const assert=require("assert");const {getDisplayName}=require("./src/user");const {greet}=require("./src/greeting");
assert.strictEqual(getDisplayName({first:"X",last:"Y"}),"X Y");assert.strictEqual(greet(null),"Hello, anonymous!");console.log("hidden ok")'
