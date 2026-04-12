from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import shutil
import uuid
import datetime

from . import database
from . import api_client
from .classes import CLASS_NAMES

app = FastAPI()

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    database.init_db()

@app.get("/api/classes")
def get_classes():
    return CLASS_NAMES

@app.post("/api/predict")
async def predict_image(file: UploadFile = File(...)):
    print(f"[{datetime.datetime.now()}] 開始讀取上傳檔案: {file.filename}")
    from PIL import Image
    import io
    
    # Read original file content into PIL Image
    contents = await file.read()
    print(f"[{datetime.datetime.now()}] 檔案讀取完成，大小: {len(contents)} bytes")
    image = Image.open(io.BytesIO(contents))
    
    # 1. Perform inference with original resolution Image object
    results = api_client.infer(image)
    if results is None:
        raise HTTPException(status_code=500, detail="Inference failed")
    
    # Generate unique ID for this identification
    file_id = str(uuid.uuid4())
    
    # 2. Save original file (save raw bytes to preserve exact file)
    orig_filename = f"{file_id}_orig{os.path.splitext(file.filename)[1]}"
    orig_path = os.path.join(UPLOAD_DIR, orig_filename)
    with open(orig_path, "wb") as f:
        f.write(contents)
    
    # 3. Save a resized thumbnail for DB and Web display
    thumb_filename = f"{file_id}_thumb.jpg"
    thumb_path = os.path.join(UPLOAD_DIR, thumb_filename)
    
    # Ensure RGB and resize
    thumbnail = image.convert('RGB').resize((224, 224))
    thumbnail.save(thumb_path, "JPEG")
    
    # 4. Store in DB
    record_id = database.log_identification(orig_path, thumb_path, results)
    
    return {
        "id": record_id,
        "image_url": f"/uploads/{thumb_filename}",
        "original_url": f"/uploads/{orig_filename}",
        "predictions": results
    }

@app.post("/api/feedback")
async def receive_feedback(
    id: str = Form(...),
    is_correct: bool = Form(...),
    corrected_class: Optional[str] = Form(None)
):
    database.update_feedback(id, is_correct, corrected_class)
    return {"status": "success"}

@app.get("/api/history")
def get_history():
    return database.get_history()

# Serve uploads and frontend
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=13984)
