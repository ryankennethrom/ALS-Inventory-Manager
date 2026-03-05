#!/bin/bash

: "${1:?Error: must provide commit message}"

./build.sh
git add .
git commit -m "$1"
git push
