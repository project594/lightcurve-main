#!/bin/bash
echo "Iniciando servidor backend de Python..."
cd python_backend
echo "Instalando dependencias..."
pip install -r requirements.txt
python3 ./app.py
uvicorn app:app --host 0.0.0.0 --port 8000
echo "Iniciando servidor Flask en http://localhost:5000"
