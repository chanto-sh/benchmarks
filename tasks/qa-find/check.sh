#!/bin/bash
grep -q "SVC_HTTP_TIMEOUT_MS" "$OUTPUT_FILE" && grep -Eq "4500|4\.5 ?s" "$OUTPUT_FILE" && echo ok || { echo "answer missing"; exit 1; }
