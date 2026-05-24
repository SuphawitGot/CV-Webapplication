"use client";
import { useState } from "react";

type Violation = {
  id: number;
  plate: string;
  imageUrl: string;
  timestamp: string;
};

const MOCK_DATA: Violation[] = [
  { id: 1, plate: "กข 1234", imageUrl: "https://placehold.co/120x80/1a1a1a/555?text=CAM", timestamp: "2024-01-15 09:32" },
  { id: 2, plate: "ขค 5678", imageUrl: "https://placehold.co/120x80/1a1a1a/555?text=CAM", timestamp: "2024-01-15 10:14" },
  { id: 3, plate: "คง 9012", imageUrl: "https://placehold.co/120x80/1a1a1a/555?text=CAM", timestamp: "2024-01-15 11:05" },
];

export default function UserPage() {
  const [search, setSearch] = useState("");

  const filtered = MOCK_DATA.filter((v) =>
    v.plate.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <main className="min-h-screen bg-zinc-950 flex items-center justify-center p-8">
      <div className="w-full max-w-2xl">

        {/* Title */}
        <h1 className="text-zinc-100 text-3xl font-light tracking-widest uppercase mb-10 text-center">
          User
        </h1>

        {/* Card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">

          {/* Search bar */}
          <div className="relative mb-8">
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search licence plate..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl pl-10 pr-4 py-3 text-zinc-100 placeholder-zinc-500 text-sm focus:outline-none focus:border-zinc-500 transition-colors"
            />
          </div>

          {/* Table header */}
          <div className="grid grid-cols-3 text-xs text-zinc-500 uppercase tracking-widest pb-3 border-b border-zinc-800 mb-2">
            <span>Licence plate</span>
            <span className="text-center">Timestamp</span>
            <span className="text-right">Evidence</span>
          </div>

          {/* Rows */}
          <div className="divide-y divide-zinc-800/60">
            {filtered.length === 0 ? (
              <p className="text-zinc-600 text-sm text-center py-8">No results found</p>
            ) : (
              filtered.map((v) => (
                <div key={v.id} className="grid grid-cols-3 items-center py-4 hover:bg-zinc-800/30 rounded-lg px-2 transition-colors">

                  {/* Plate */}
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-red-500/70" />
                    <span className="text-zinc-100 font-mono text-sm tracking-wider">{v.plate}</span>
                  </div>

                  {/* Timestamp */}
                  <span className="text-zinc-500 text-xs text-center">{v.timestamp}</span>

                  {/* Image link */}
                  <div className="flex justify-end">
                    <a
                      href={v.imageUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-100 transition-colors border border-zinc-700 hover:border-zinc-500 rounded-lg px-3 py-1.5"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      View
                    </a>
                  </div>

                </div>
              ))
            )}
          </div>

          {/* Count */}
          <p className="text-zinc-600 text-xs mt-6 text-right">
            {filtered.length} violation{filtered.length !== 1 ? "s" : ""} found
          </p>

        </div>
      </div>
    </main>
  );
}
