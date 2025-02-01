"use client";
import { useState, useRef, useEffect } from "react";
import { ClipLoader } from "react-spinners"; 

export default function FileUploader() {
  const [files, setFiles] = useState<File[]>([]);
  const [isConverting, setIsConverting] = useState(false);
  const [isUploading, setIsUploading] = useState(false); 
  const [sessionId, setSessionId] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = 0.5; 
    }
  }, []);

  
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) return;

    const selectedFiles = Array.from(event.target.files);
    const updatedFiles = [...files, ...selectedFiles];

    setFiles(updatedFiles);
    await uploadFiles(selectedFiles); 
  };

  const apiUrl = process.env.API_URL || "http://localhost:8000";
  
  const uploadFiles = async (files: File[]) => {
    setIsUploading(true); 
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      const response = await fetch(`${apiUrl}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Falha no upload");
      }

      const data = await response.json();
      setSessionId(data.session_id); 
    } catch (error) {
      console.error("Erro no upload:", error);
    } finally {
      setIsUploading(false); 
    }
  };

  
  const removeFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    setFiles(updatedFiles);
  };

  const removeAllFiles = () => {
    setFiles([]);
  };

  const convertAndDownload = async () => {
    if (!sessionId) {
      console.error("Nenhum session_id encontrado");
      return;
    }

    setIsConverting(true); 
    try {
      const response = await fetch(`${apiUrl}/convert-and-zip`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId }), // Usa o session_id armazenado
      });

      if (!response.ok) {
        throw new Error("Falha na conversão e download");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "converted-images.zip";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Erro ao converter e baixar arquivos:", error);
    } finally {
      setIsConverting(false); 
    }
  };

  return (
    <div className="relative min-h-screen w-full flex flex-col items-center justify-center overflow-hidden">
      <video
        ref={videoRef}
        autoPlay
        loop
        muted
        className="absolute top-0 left-0 w-full h-full object-cover filter blur-md"
      >
        <source src="/moon.mp4" type="video/mp4" />
        Seu navegador não suporta vídeos HTML5.
      </video>

      <div className="absolute top-0 left-0 w-full h-full bg-black bg-opacity-50"></div>

      <div className="relative z-10 flex flex-col items-center gap-4 p-6 bg-white bg-opacity-20 rounded-lg shadow-lg">
        <input
          type="file"
          multiple
          onChange={handleFileChange}
          className="hidden"
          id="fileInput"
        />
        <label
          htmlFor="fileInput"
          className="cursor-pointer bg-blue-500 text-white p-2 rounded"
        >
          Escolher Arquivos
        </label>

        {files.length > 0 && (
          <div className="grid grid-cols-3 gap-2">
            {files.map((file, index) => (
              <div key={index} className="p-2 border rounded relative">
                <img
                  src={URL.createObjectURL(file)}
                  alt={file.name}
                  className="w-24 h-24 object-cover"
                />
                <button
                  onClick={() => removeFile(index)}
                  className="absolute top-0 right-0 bg-red-500 text-white px-2 py-1 rounded-full text-xs"
                >
                  X
                </button>
              </div>
            ))}
          </div>
        )}

        {files.length > 0 && (
          <div className="flex gap-4">
            <button
              onClick={removeAllFiles}
              className="bg-red-500 text-white p-2 rounded"
            >
              Remover Todos
            </button>
            <button
              onClick={convertAndDownload}
              disabled={isConverting || isUploading}
              className={`bg-green-500 text-white p-2 rounded ${
                isConverting || isUploading ? "opacity-50 cursor-not-allowed" : ""
              }`}
            >
              {isConverting ? "Convertendo..." : "Converter para WebP e Baixar"}
            </button>
          </div>
        )}

        {isUploading && (
          <div className="fixed top-0 left-0 w-full h-full flex items-center justify-center bg-black bg-opacity-50 z-20">
            <div className="bg-white p-6 rounded-lg shadow-lg flex flex-col items-center gap-2">
              <ClipLoader color="#3B82F6" size={40} />
              <p className="text-gray-700">Enviando arquivos...</p>
            </div>
          </div>
        )}

        {isConverting && (
          <div className="fixed top-0 left-0 w-full h-full flex items-center justify-center bg-black bg-opacity-50 z-20">
            <div className="bg-white p-6 rounded-lg shadow-lg flex flex-col items-center gap-2">
              <ClipLoader color="#10B981" size={40} /> 
              <p className="text-gray-700">Convertendo e compactando arquivos...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
