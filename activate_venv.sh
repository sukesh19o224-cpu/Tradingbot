#!/bin/bash
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ venv activated"
else
    python3 -m venv venv
    source venv/bin/activate
    pip install -U pip
    pip install -r requirements.txt
    echo "✅ venv created"
fi
