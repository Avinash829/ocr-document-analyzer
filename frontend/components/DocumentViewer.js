"use client";

import { useMemo, useState, useRef, useEffect } from "react";
import { absoluteAssetUrl } from "@/lib/api";
import { Minus, Plus, ChevronLeft, ChevronRight } from "lucide-react";

export default function DocumentViewer({ document, regions, question }) {
  const regionPages = useMemo(() => [...new Set(regions.map((region) => region.page))], [regions]);
  const [page, setPage] = useState(regionPages[0] || 1);
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef(null);

  const pageData = document.pages.find((item) => item.page === page) || document.pages[0];
  const visible = regions.filter((region) => region.page === page);

  useEffect(() => {
    if (visible.length > 0 && containerRef.current) {
      // Find the first/topmost region
      const topRegion = visible.reduce((prev, current) => (prev.bbox.y < current.bbox.y) ? prev : current);

      // Calculate where it is vertically (percentage of total height)
      const topPercent = topRegion.bbox.y / topRegion.pageHeight;

      // The child has a fixed aspect ratio, so scrollHeight is immediately accurate.
      // We subtract the padding (24px) from scrollHeight for the inner content height.
      const innerHeight = containerRef.current.scrollHeight - 48; // p-6 is 24px top + 24px bottom
      const regionCenter = (topPercent * innerHeight) + 24;

      const clientHeight = containerRef.current.clientHeight;
      containerRef.current.scrollTo({
        top: Math.max(0, regionCenter - (clientHeight / 2)),
        behavior: 'smooth'
      });
    }
  }, [visible, zoom]);

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-[#DCE0E5]">
      {/* Dark Toolbar Header */}
      <div className="flex h-[60px] shrink-0 items-center justify-between bg-[#2B2B2B] px-4 sm:px-6">
        <div className="flex items-center gap-6">
          <h2 className="hidden sm:block text-[15px] font-bold text-white">Answer Sheet</h2>

          {/* Zoom Controls */}
          <div className="flex items-center rounded-xl bg-[#3D3D3D] px-2 py-1.5 text-white shadow-sm">
            <button aria-label="Zoom out" onClick={() => setZoom((value) => Math.max(.25, value - .25))} className="flex items-center justify-center p-1 hover:text-slate-300">
              <Minus size={16} strokeWidth={3} />
            </button>
            <span className="w-[42px] text-center text-[12px] font-bold">{Math.round(zoom * 100)}%</span>
            <button aria-label="Zoom in" onClick={() => setZoom((value) => Math.min(2.5, value + .25))} className="flex items-center justify-center p-1 hover:text-slate-300">
              <Plus size={16} strokeWidth={3} />
            </button>
          </div>
        </div>

        {/* Page Controls */}
        <div className="flex items-center rounded-xl bg-[#3D3D3D] px-2 py-1.5 text-white shadow-sm">
          <button aria-label="Previous page" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} className="flex items-center justify-center p-1 hover:text-slate-300 disabled:opacity-50">
            <ChevronLeft size={16} strokeWidth={3} />
          </button>
          <span className="min-w-[70px] text-center text-[12px] font-bold">Page {page} of {document.pageCount}</span>
          <button aria-label="Next page" disabled={page >= document.pageCount} onClick={() => setPage((value) => value + 1)} className="flex items-center justify-center p-1 hover:text-slate-300 disabled:opacity-50">
            <ChevronRight size={16} strokeWidth={3} />
          </button>
        </div>
      </div>

      {regionPages.length > 1 && (
        <div className="flex gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800">
          <span>Answer continues:</span>
          {regionPages.map((number) => (
            <button key={number} onClick={() => setPage(number)} className={`underline ${page === number ? "font-bold" : ""}`}>page {number}</button>
          ))}
        </div>
      )}

      {/* Document Area */}
      <div ref={containerRef} className="min-h-0 flex-1 overflow-auto p-0 sm:p-6 scroll-smooth">
        <div className="relative mx-auto origin-top bg-white shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-all duration-200" style={{ width: `${zoom * 100}%`, minWidth: `${zoom * 100}%`, aspectRatio: `${pageData.width}/${pageData.height}` }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={absoluteAssetUrl(pageData.imageUrl)} alt={`Student answer sheet page ${page}`} className="absolute inset-0 size-full select-none" draggable="false" />

          {/* Highlights */}
          {visible.map((region, index) => {
            const left = `${region.bbox.x / region.pageWidth * 100}%`;
            const top = `${region.bbox.y / region.pageHeight * 100}%`;
            const width = `${region.bbox.width / region.pageWidth * 100}%`;
            const height = `${region.bbox.height / region.pageHeight * 100}%`;

            return (
              <div
                key={`${page}-${index}`}
                aria-label="Mapped answer region"
                className="absolute z-10 rounded-[4px] border-2 border-[#1DB335] bg-[#1DB335]/15 shadow-[0_0_0_2px_rgba(255,255,255,0.3)] transition-all"
                style={{ left, top, width, height }}
              >
                {/* Badge (Q1, Q2, etc) */}
                {question && (
                  <div className="absolute -left-0.5 -top-6 flex h-6 items-center justify-center rounded-t-[6px] bg-[#1DB335] px-2.5 text-[12px] font-bold text-white">
                    Q{question.displayNumber}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
