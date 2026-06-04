#!/bin/bash
# Azure App Service startup script for URIS-AI

export PYTHONPATH=/home/site/wwwroot/src

cd /home/site/wwwroot
python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port 8000 --workers 1
