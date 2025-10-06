# Backend Python para Análisis de CSV con Modelo PyTorch

Este backend utiliza un modelo de PyTorch entrenado para analizar archivos CSV y devolver tres números relacionados con la detección de exoplanetas:

1. **Probabilidad de detección** (0-100%): Calculada por el modelo PyTorch entrenado
2. **Período orbital estimado** (días): Basado en características del archivo
3. **Radio planetario estimado** (×R⊕): Estimado basado en variabilidad de datos

## Requisitos Previos

Asegúrate de tener estos archivos en el directorio `python_backend/`:
- `model.pth`: Modelo PyTorch entrenado
- `scaler.pkl`: Scaler para normalización de datos

## Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Inicia el servidor:
```bash
python app.py
```

2. El servidor estará disponible en `http://localhost:5000`

3. Endpoints disponibles:
   - `POST /analyze`: Analiza un archivo CSV
   - `GET /health`: Verifica el estado del servidor y modelo

## Formato de archivo CSV

El archivo CSV debe tener **exactamente 34 columnas numéricas** para que el modelo funcione correctamente. El modelo espera las siguientes características:

- Columnas 1-34: Features numéricas para el modelo PyTorch
- Todas las columnas deben ser valores numéricos
- No se permiten valores faltantes (NaN)

Ejemplo de estructura:
```csv
koi_period,koi_time0bk,koi_impact,koi_duration,koi_depth,koi_prad,koi_teq,koi_insol,koi_model_snr,koi_tce_plnt_num,koi_tce_delivname,koi_steff,koi_slogg,koi_srad,ra,dec,koi_kepmag,koi_gmag,koi_rmag,koi_imag,koi_zmag,koi_jmag,koi_hmag,koi_kmag,koi_fwm_sra,koi_fwm_sdec,koi_fwm_sra_err,koi_fwm_sdec_err,koi_fwm_prao,koi_fwm_pdec,koi_fwm_prao_err,koi_fwm_pdec_err,koi_dicco_mra,koi_dicco_mdec
10.304,1325.292,0.0,2.078,0.0001,1.0,1000.0,1.0,10.0,1,Kepler,5777.0,4.4,1.0,290.0,45.0,15.0,15.0,15.0,15.0,15.0,15.0,15.0,15.0,290.0,45.0,0.1,0.1,0.0,0.0,0.1,0.1,0.0,0.0
```

## Respuesta del API

```json
{
  "probability": 85.5,
  "period": 12.3,
  "radius": 1.8,
  "found": true,
  "data_points": 3,
  "columns": 34,
  "predictions": [0.85, 0.92, 0.78]
}
```

## Arquitectura del Modelo

El modelo PyTorch tiene la siguiente arquitectura:
- Input: 34 features
- Hidden layers: 64 → 64 → 64 → 32 → 1
- Activation: ReLU
- Output: Sigmoid (probabilidad)

## Verificación del Estado

Puedes verificar si el modelo se cargó correctamente visitando:
```
GET http://localhost:5000/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "message": "Backend Python funcionando",
  "model_status": "loaded",
  "scaler_status": "loaded"
}
```
