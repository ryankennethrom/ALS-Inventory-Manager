#!/bin/bash

: "${1:?Error: must provide commit message}"

awk '
/version *=/ {
    match($0, /[0-9]+/)
    num = substr($0, RSTART, RLENGTH) + 1
    sub(/[0-9]+/, num)
}
{ print }
' app_version.py > tmp && mv tmp app_version.py

./build.sh
git add .
git commit -m "$1"
git push origin main --force
