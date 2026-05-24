"use client";
import { useState, useRef, useCallback, useEffect } from "react";

export default function AdminPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoURL, setVideoURL] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    fetch(`${API_URL}/`)
        .then(r => r.json())
        .then(data => console.log(data))  // should print { message: "FastAPI is running" }
}, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("video/")) {
      setVideoFile(file);
      setVideoURL(URL.createObjectURL(file));
    }
  }, []);
  

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      setVideoURL(URL.createObjectURL(file));
    }
  };

  const handleStart = async () => {
    if (!videoFile) return alert("Please upload a video first");
    const formData = new FormData();
    formData.append("file", videoFile);
    await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
    await fetch(`${API_URL}/start`, { method: "POST" });
    setIsRunning(true);
  };

  const handleStop = async () => {
    await fetch(`${API_URL}/stop`, { method: "POST" });
    setIsRunning(false);
  };

  return (
    <main className="min-h-screen bg-zinc-950 flex items-center justify-center p-8">
      <div className="w-full max-w-7xl">

        {/* Title */}
        <h1 className="text-zinc-100 text-3xl font-light tracking-widest uppercase mb-10 text-center">
          Admin
        </h1>

        {/* Card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 flex gap-8 items-center">

          {/* Drop zone */}
          <div
            className={`flex-1 aspect-video rounded-xl border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all duration-200
              ${isDragging ? "border-red-500 bg-red-500/10" : "border-zinc-700 hover:border-zinc-500 bg-zinc-800/50"}`}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => fileInputRef.current?.click()}
          >
            {videoURL ? (
              <video src={videoURL} className="w-full h-full object-cover rounded-xl" controls />
            ) : (
              <>
                <svg className="w-10 h-10 text-zinc-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                </svg>
                <p className="text-zinc-400 text-sm">Drag video here</p>
                <p className="text-zinc-600 text-xs mt-1">or click to browse</p>
              </>
            )}
            <input ref={fileInputRef} type="file" accept="video/*" className="hidden" onChange={handleFileChange} />
          </div>

          {/* Buttons */}
          <div className="flex flex-col gap-5 items-center">

            {/* Red button */}
            <button
              onClick={handleStart}
              disabled={isRunning}
              className="group relative w-14 h-14 rounded-full transition-all duration-200"
              title="Start detection"
            >
              <div className={`w-14 h-14 rounded-full transition-all duration-300
                ${isRunning
                  ? "bg-red-800 scale-90"
                  : "bg-red-500 hover:bg-red-400 hover:scale-110 shadow-lg shadow-red-500/30"
                }`}
              />
              {isRunning && (
                <span className="absolute inset-0 rounded-full border-2 border-red-500 animate-ping" />
              )}
            </button>

            {/* Green button */}
            <button
              onClick={handleStop}
              disabled={!isRunning}
              className="group relative w-14 h-14 rounded-full transition-all duration-200"
              title="Stop detection"
            >
              <div className={`w-14 h-14 rounded-full transition-all duration-300
                ${!isRunning
                  ? "bg-green-800 scale-90"
                  : "bg-green-500 hover:bg-green-400 hover:scale-110 shadow-lg shadow-green-500/30"
                }`}
              />
            </button>

          </div>
        </div>

        {/* Status */}
        <p className="text-center mt-4 text-sm tracking-widest uppercase">
          {isRunning
            ? <span className="text-red-400">● Detection running</span>
            : <span className="text-zinc-600">● Standby</span>
          }
        </p>

      </div>
    </main>
  );
}
