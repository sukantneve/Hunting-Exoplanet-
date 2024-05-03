import uvicorn
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
import tensorflow as tf
from keras.models import load_model  # Direct import from tensorflow.keras
from io import StringIO, BytesIO
import os
import traceback
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()
logging.basicConfig(filename='error.log', level=logging.ERROR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Constants
THRESHOLD = 0.5
MODEL_PATH = 'RNN_15-4.h5'
# Load and compile the model globally if it exists
model = None


async def load_model_async():
    global model
    try:
        if model is None:
            model = load_model(MODEL_PATH)
    except Exception as e:
        logging.error(f"Error loading the model: {e}")
        traceback.print_exc()


@app.on_event("startup")
async def startup_event():
    await load_model_async()


# Preprocess data directly from the upload without saving to disk
async def preprocess_data(file: UploadFile):
    try:
        # Assuming the file is CSV and fits in memory, adjust as necessary
        data = pd.read_csv(file.file)
        x_test = data.iloc[:, 1:].values
        y_test = data.iloc[:, 0].values - 1
        return data, x_test, y_test
    except pd.errors.ParserError as e:
        logging.error(f"Error parsing CSV file: {e}")
        raise HTTPException(
            status_code=422, detail="Validation Error: Invalid CSV file format")
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Internal Server Error")


# Prediction function optimized for memory usage
async def predict(x_test, y_test):
    try:
        x_test = x_test.reshape((x_test.shape[0], x_test.shape[1], 1))
        y_predict = model.predict(x_test)
        y_pred = (y_predict > THRESHOLD).astype(int)
        return y_pred, y_predict
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Internal Server Error")


@app.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)):
    if model is None:
        return JSONResponse(content={"error": "Model is not loaded"}, status_code=503)
    try:
        data, x_test, y_test = await preprocess_data(file)
        y_pred, y_predict = await predict(x_test, y_test)
        data.insert(0, "Direction", ["True" if pred else "False" for pred in y_pred])
        data.insert(1, "Probability", [float(prob) for prob in y_predict])
        output_buffer = BytesIO()
        data.to_excel(output_buffer, index=False)
        output_buffer.seek(0)
        return StreamingResponse(output_buffer,
                                 media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={'Content-Disposition': 'attachment; filename="predictions_new.xlsx"'})
    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)


@app.get("/")
async def root():
    return {"message": "Welcome to the RNN Prediction API"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
