"use client";

import { useMemo, useState } from "react";
import { absoluteAssetUrl } from "@/lib/api";

export default function DocumentViewer({ document, regions }) {
  const regionPages = useMemo(() => [...new Set(regions.map((region) => region.page))], [regions]);
  const [page, setPage] = useState(regionPages[0] || 1);
  const [zoom, setZoom] = useState(1);
  const pageData = document.pages.find((item) => item.page === page) || document.pages[0];
  const visible = regions.filter((region) => region.page === page);

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-slate-100">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2">
          <button aria-label="Previous page" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} className="viewer-button">←</button>
          <span className="min-w-24 text-center text-xs font-medium text-slate-600">Page {page} of {document.pageCount}</span>
          <button aria-label="Next page" disabled={page >= document.pageCount} onClick={() => setPage((value) => value + 1)} className="viewer-button">→</button>
        </div>
        <div className="flex items-center gap-2"><button aria-label="Zoom out" onClick={() => setZoom((value) => Math.max(.5, value - .25))} className="viewer-button">−</button><span className="w-12 text-center text-xs text-slate-600">{Math.round(zoom * 100)}%</span><button aria-label="Zoom in" onClick={() => setZoom((value) => Math.min(2.5, value + .25))} className="viewer-button">+</button><button onClick={() => setZoom(1)} className="viewer-button px-3">Fit</button></div>
      </div>
      {regionPages.length > 1 && <div className="flex gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800"><span>Answer continues:</span>{regionPages.map((number) => <button key={number} onClick={() => setPage(number)} className={`underline ${page === number ? "font-bold" : ""}`}>page {number}</button>)}</div>}
      <div className="min-h-0 flex-1 overflow-auto p-5">
        <div className="relative mx-auto origin-top bg-white shadow-xl" style={{ width: `${Math.min(pageData.width, 900) * zoom}px`, aspectRatio: `${pageData.width}/${pageData.height}` }}>
          {/* The server controls this authenticated/ephemeral source; plain img keeps overlays dimensionally exact. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={absoluteAssetUrl(pageData.imageUrl)} alt={`Student answer sheet page ${page}`} className="absolute inset-0 size-full select-none" draggable="false" />
          {visible.map((region, index) => <div key={`${page}-${index}`} aria-label="Mapped answer region" className="absolute rounded-md border-2 border-amber-500 bg-amber-300/25 shadow-[0_0_0_2px_rgba(255,255,255,.7)]" style={{ left: `${region.bbox.x / region.pageWidth * 100}%`, top: `${region.bbox.y / region.pageHeight * 100}%`, width: `${region.bbox.width / region.pageWidth * 100}%`, height: `${region.bbox.height / region.pageHeight * 100}%` }} />)}
        </div>
      </div>
    </div>
  );
}
