from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import io
import zipfile
import os
import uuid
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://luna-converter.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_files = {}

class ConvertRequest(BaseModel):
    session_id: str

@app.post("/upload")
async def upload_file(files: list[UploadFile] = File(...)):
    session_id = str(uuid.uuid4()) 
    session_files[session_id] = []

    for file in files:
        file_content = await file.read()
        session_files[session_id].append({
            "filename": file.filename,
            "content": file_content
        })

    return JSONResponse(content={"message": "Arquivos armazenados!", "session_id": session_id})

@app.get("/list-files")
async def list_files(session_id: str):
    if session_id not in session_files:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    files = session_files[session_id]
    return JSONResponse(content={"files": [file["filename"] for file in files]})

@app.post("/delete-all")
async def delete_all_files(session_id: str):
    if session_id not in session_files:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    session_files[session_id] = []
    return JSONResponse(content={"message": "Todos os arquivos foram removidos!"})

async def convert_image(file_data):
    return await asyncio.to_thread(process_image, file_data) 


def process_image(file_data):
    image = Image.open(io.BytesIO(file_data["content"]))
    webp_buffer = io.BytesIO()
    image.save(webp_buffer, format="WEBP")
    return (f"{os.path.splitext(file_data['filename'])[0]}.webp", webp_buffer.getvalue())


@app.post("/convert-and-zip")
async def convert_and_zip(request: ConvertRequest):
    session_id = request.session_id

    if session_id not in session_files or not session_files[session_id]:
        raise HTTPException(status_code=404, detail="Nenhum arquivo para converter")

    zip_buffer = io.BytesIO()

    converted_images = await asyncio.gather(*[convert_image(file) for file in session_files[session_id]])

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in converted_images:
            zip_file.writestr(filename, content)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=converted-images.zip"}
    )
