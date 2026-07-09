#!/bin/bash

: "${1:?Error: must provide commit message}"

git add .
git commit -m "$1"
git push origin main --force

./build.sh

