#!/bin/bash

# Install requirements
python -m pip install -r requirements.txt

# If user passed argument, use it
if [ "$1" == "--prod" ]; then
    python main.py
else
    python main.py --test
fi

