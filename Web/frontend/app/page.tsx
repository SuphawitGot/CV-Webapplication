"use client";
import { useState, useRef, useCallback, useEffect } from "react";

type Violation = {
  id: number;
  filename: string;
  plate: string;
  timestamp: string;
};

export default function AdminPage() {
  const [isRunning, setIsRunning]   = useState(false);
  const [isPaused, setIsPaused]     = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [videoFile, setVideoFile]   = useState<File | null>(null);
  const [streamKey, setStreamKey]   = useState(0);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef      = useRef<ReturnType<typeof setInterval> | null>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  // ── Poll /violations while running ─────────────────────────────────────────
  useEffect(() => {
    if (isRunning) {
      pollRef.current = setInterval(async () => {
        try {
          const res = await fetch(`${API_URL}/violations`);
          if (res.ok) {
            const data = await res.json();
            setViolations(data.violations ?? []);
          }
        } catch {/* ignore */}
      }, 1500);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [isRunning, API_URL]);

  // ── Start detection (called automatically after file selection) ─────────────
  const startWithFile = useCallback(async (file: File) => {
    setIsUploading(true);
    setViolations([]);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      setStreamKey((k) => k + 1);
      setIsRunning(true);
      setIsPaused(false);
    } catch (err) {
      console.error(err);
      alert("Failed to start detection. Is the backend running?");
    }
    setIsUploading(false);
  }, [API_URL]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("video/")) {
      setVideoFile(file);
      startWithFile(file);
    }
  }, [startWithFile]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      startWithFile(file);
    }
  };

  const handleStop = async () => {
    await fetch(`${API_URL}/stop`, { method: "POST" });
    setIsRunning(false);
    setIsPaused(false);
  };

  const handlePause = async () => {
    if (isPaused) {
      await fetch(`${API_URL}/resume`, { method: "POST" });
      setIsPaused(false);
    } else {
      await fetch(`${API_URL}/pause`, { method: "POST" });
      setIsPaused(true);
    }
  };

  const captureImageUrl = (filename: string) =>
    `${API_URL}/captures/${filename}`;

  return (
    <main className="min-h-screen bg-zinc-950 flex items-center justify-center p-8">
      <div className="w-full max-w-7xl">

        {/* Title */}
        <h1 className="text-zinc-100 text-3xl font-light tracking-widest uppercase mb-10 text-center">
          Admin — Detection Dashboard
        </h1>

        <div className="flex gap-6 items-start">

          {/* Left: video panel */}
          <div className="flex-1 flex flex-col gap-4">

            {/* Drop zone — shown when NOT running */}
            {!isRunning && (
              <div
                className={`aspect-video rounded-xl border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all duration-200
                  ${isUploading ? "border-blue-500 bg-blue-500/10 cursor-wait" : ""}
                  ${isDragging  ? "border-red-500 bg-red-500/10" : ""}
                  ${!isUploading && !isDragging ? "border-zinc-700 hover:border-zinc-500 bg-zinc-800/50" : ""}`}
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onClick={() => !isUploading && fileInputRef.current?.click()}
              >
                {isUploading ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-10 h-10 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                    <p className="text-blue-400 text-sm">Starting detection…</p>
                  </div>
                ) : (
                  <>
                    <svg className="w-10 h-10 text-zinc-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                    </svg>
                    <p className="text-zinc-400 text-sm font-medium">Drop video to start detection</p>
                    <p className="text-zinc-600 text-xs mt-1">or click to browse · detection begins immediately</p>
                    {videoFile && (
                      <p className="text-zinc-500 text-xs mt-3 truncate max-w-xs">📁 {videoFile.name}</p>
                    )}
                  </>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
            )}

            {/* MJPEG stream — shown when running */}
            {isRunning && (
              <div className="aspect-video rounded-xl overflow-hidden border border-zinc-700 bg-black flex items-center justify-center relative">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  key={streamKey}
                  src={`${API_URL}/stream`}
                  alt="Detection stream"
                  className="w-full h-full object-contain"
                  style={{ willChange: "contents", imageRendering: "auto" }}
                />

                {/* Live / Paused badge */}
                <span className={`absolute top-3 left-3 flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full backdrop-blur-sm
                  ${isPaused ? "bg-black/60 text-yellow-400" : "bg-black/60 text-red-400"}`}>
                  <span className={`w-2 h-2 rounded-full ${isPaused ? "bg-yellow-400" : "bg-red-500 animate-pulse"}`} />
                  {isPaused ? "PAUSED" : "LIVE"}
                </span>

                {/* Violation count badge */}
                {violations.length > 0 && (
                  <span className="absolute top-3 right-3 bg-red-600/80 text-white text-xs font-bold px-2.5 py-1 rounded-full backdrop-blur-sm">
                    {violations.length} violation{violations.length !== 1 ? "s" : ""}
                  </span>
                )}

                {/* File name */}
                {videoFile && (
                  <span className="absolute bottom-3 left-3 text-zinc-400 text-xs bg-black/50 px-2 py-0.5 rounded-md backdrop-blur-sm truncate max-w-xs">
                    📁 {videoFile.name}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Centre: control buttons */}
          <div className="flex flex-col gap-5 items-center pt-2">

            {/* Load new video button (replaces start) */}
            <button
              id="btn-load-video"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              title="Load a new video"
              className="group relative w-14 h-14 rounded-full transition-all duration-200"
            >
              <div className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300
                ${isRunning
                  ? "bg-red-800 scale-90"
                  : "bg-red-500 hover:bg-red-400 hover:scale-110 shadow-lg shadow-red-500/30"
                }`}
              >
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
              </div>
              {isRunning && (
                <span className="absolute inset-0 rounded-full border-2 border-red-500 animate-ping" />
              )}
            </button>

            {/* Pause / Resume button */}
            <button
              id="btn-pause-detection"
              onClick={handlePause}
              disabled={!isRunning}
              title={isPaused ? "Resume detection" : "Pause detection"}
              className="group relative w-14 h-14 rounded-full transition-all duration-200"
            >
              <div className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300
                ${!isRunning
                  ? "bg-yellow-900/40 scale-90"
                  : isPaused
                    ? "bg-yellow-400 hover:bg-yellow-300 hover:scale-110 shadow-lg shadow-yellow-400/30"
                    : "bg-yellow-500 hover:bg-yellow-400 hover:scale-110 shadow-lg shadow-yellow-500/30"
                }`}
              >
                {isPaused ? (
                  <svg className="w-6 h-6 text-zinc-900 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6 text-zinc-900" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                  </svg>
                )}
              </div>
            </button>

            {/* Stop button */}
            <button
              id="btn-stop-detection"
              onClick={handleStop}
              disabled={!isRunning}
              title="Stop detection"
              className="group relative w-14 h-14 rounded-full transition-all duration-200"
            >
              <div className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300
                ${!isRunning
                  ? "bg-zinc-700 scale-90"
                  : "bg-green-500 hover:bg-green-400 hover:scale-110 shadow-lg shadow-green-500/30"
                }`}
              >
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
              </div>
            </button>
          </div>

          {/* Right: violations panel */}
          <div className="w-80 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-zinc-300 text-sm font-semibold tracking-widest uppercase">Auto-Captures</h2>
              {violations.length > 0 && (
                <span className="text-xs bg-red-600 text-white px-2 py-0.5 rounded-full font-bold">
                  {violations.length}
                </span>
              )}
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col"
                 style={{ maxHeight: "calc(56.25vw * 9/16 * 0.9)", minHeight: "240px" }}>

              {violations.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                  <svg className="w-8 h-8 text-zinc-700 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-zinc-600 text-xs">No violations captured yet</p>
                  <p className="text-zinc-700 text-xs mt-1">Detection captures automatically when a vehicle midpoint crosses the crosswalk</p>
                </div>
              ) : (
                <div className="overflow-y-auto divide-y divide-zinc-800/60 flex-1">
                  {[...violations].reverse().map((v) => (
                    <div key={v.id} className="p-3 hover:bg-zinc-800/30 transition-colors">
                      <div className="flex items-start gap-2">
                        {/* Thumbnail */}
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={captureImageUrl(v.filename)}
                          alt={`Capture ${v.id}`}
                          className="w-20 h-14 object-cover rounded-lg border border-zinc-700 bg-zinc-800 flex-shrink-0"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 mb-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                            <span className="text-red-400 text-xs font-semibold">#{v.id}</span>
                          </div>
                          {/* Plate */}
                          <p className={`font-mono text-sm tracking-wider truncate
                            ${v.plate === "Reading…" ? "text-zinc-500 italic" : "text-zinc-100"}`}>
                            {v.plate}
                          </p>
                          {/* Timestamp */}
                          <p className="text-zinc-600 text-xs mt-0.5">{v.timestamp}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Status bar */}
        <p className="text-center mt-5 text-sm tracking-widest uppercase">
          {isUploading
            ? <span className="text-blue-400">⏳ Uploading &amp; starting…</span>
            : !isRunning
              ? <span className="text-zinc-600">● Standby — drop a video to begin</span>
              : isPaused
                ? <span className="text-yellow-400">⏸ Paused</span>
                : <span className="text-red-400">● Detection running · auto-capture active</span>
          }
        </p>

      </div>
    </main>
  );
}
