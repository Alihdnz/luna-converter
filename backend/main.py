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

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://luna-converter.vercel.app"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dicionário para armazenar arquivos por sessão (simulação de sessão)
session_files = {}

# Modelo para o corpo da requisição
class ConvertRequest(BaseModel):
    session_id: str

# Rota para upload de arquivos
@app.post("/upload")
async def upload_file(files: list[UploadFile] = File(...)):
    session_id = str(uuid.uuid4())  # Simula uma sessão única para o usuário
    session_files[session_id] = []

    for file in files:
        # Ler o conteúdo do arquivo
        file_content = await file.read()

        # Armazenar o arquivo na "sessão"
        session_files[session_id].append({
            "filename": file.filename,
            "content": file_content
        })

    return JSONResponse(content={"message": "Arquivos armazenados!", "session_id": session_id})

# Rota para listar arquivos de uma sessão
@app.get("/list-files")
async def list_files(session_id: str):
    if session_id not in session_files:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    files = session_files[session_id]
    return JSONResponse(content={"files": [file["filename"] for file in files]})

# Rota para remover todos os arquivos de uma sessão
@app.post("/delete-all")
async def delete_all_files(session_id: str):
    if session_id not in session_files:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    session_files[session_id] = []
    return JSONResponse(content={"message": "Todos os arquivos foram removidos!"})

# Rota para converter imagens para WebP e baixar em um arquivo .zip
@app.post("/convert-and-zip")
async def convert_and_zip(request: ConvertRequest):
    session_id = request.session_id

    if session_id not in session_files or not session_files[session_id]:
        raise HTTPException(status_code=404, detail="Nenhum arquivo para converter")

    # Criar um buffer para o arquivo zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_data in session_files[session_id]:
            # Abrir a imagem usando Pillow
            image = Image.open(io.BytesIO(file_data["content"]))

            # Converter para WebP
            webp_buffer = io.BytesIO()
            image.save(webp_buffer, format="WEBP")

            # Adicionar a imagem WebP ao arquivo zip
            zip_file.writestr(
                f"{os.path.splitext(file_data['filename'])[0]}.webp",
                webp_buffer.getvalue()
            )

    # Retornar o arquivo zip para download
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=converted-images.zip"}
    )
