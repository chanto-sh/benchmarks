#!/bin/bash
set -e
cp -R "$(dirname "$0")/pristine/." .
go test ./... 2>&1
