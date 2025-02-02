from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image  
import io
import zipfile
import os
import uuid

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

@app.post("/convert-and-zip")
async def convert_and_zip(request: ConvertRequest):
    session_id = request.session_id

    if session_id not in session_files or not session_files[session_id]:
        raise HTTPException(status_code=404, detail="Nenhum arquivo para converter")

    zip_buffer = io.BytesIO()

    async def generate_zip():
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file_data in session_files[session_id]:
                image = Image.open(io.BytesIO(file_data["content"]))

                webp_buffer = io.BytesIO()
                image.save(webp_buffer, format="WEBP") 
                zip_file.writestr(
                    f"{os.path.splitext(file_data['filename'])[0]}.webp",
                    webp_buffer.getvalue()
                )

                webp_buffer.close()

        zip_buffer.seek(0)
        yield zip_buffer.getvalue()

    return StreamingResponse(
        generate_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=converted-images.zip"}
    )