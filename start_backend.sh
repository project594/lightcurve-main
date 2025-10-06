#!/bin/bash
echo "Iniciando servidor backend de Python..."
cd python_backend
echo "Instalando dependencias..."
pip install -r requirements.txt
echo "Iniciando servidor Flask en http://localhost:5000"
python3 ./app.py
