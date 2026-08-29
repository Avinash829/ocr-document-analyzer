"use client";

import { Upload, X } from "lucide-react";

export default function FilePicker({ id, titlePrefix, highlightText, hint, file, onChange }) {
  if (file) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-white p-2">
        <div className="relative flex items-center gap-[12px] rounded-[10px] p-2">
          {/* The X button to deselect */}
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              onChange(null);
            }}
            className="absolute -right-1 -top-1 z-10 flex h-[22px] w-[22px] items-center justify-center rounded-full bg-[#5E5E5E] text-white hover:bg-[#404040]"
            title="Remove file"
          >
            <X size={12} strokeWidth={3} />
          </button>

          {/* PDF Icon block */}
          <div className="flex h-[36px] w-[36px] shrink-0 items-center justify-center rounded-[8px] bg-[#EB5757] text-[10px] font-bold text-white shadow-sm">
            PDF
          </div>
          <div className="flex flex-col justify-center">
            <span className="text-[13px] font-bold text-[#171717] truncate max-w-[130px] sm:max-w-[200px] leading-tight">
              {file.name}
            </span>
            <span className="text-[11px] font-medium text-[#9CA3AF] mt-[4px] leading-tight">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <label 
      htmlFor={id} 
      className="flex h-full w-full cursor-pointer flex-col items-center justify-center bg-white hover:bg-slate-50 transition-colors"
    >
      <div className="mb-[10px] flex h-[34px] w-[34px] items-center justify-center rounded-[7px] bg-[#F5F5F5] text-[#858585]">
        <Upload size={18} />
      </div>
      
      <span className="mb-[4px] text-[15px] font-semibold text-[#171717]">
        {titlePrefix} <span className="text-[#f05f37]">{highlightText}</span>
      </span>
      
      <span className="text-[12px] text-[#9CA3AF]">
        {hint}
      </span>
      
      <input 
        id={id} 
        className="sr-only" 
        type="file" 
        accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg,image/webp" 
        onChange={(event) => onChange(event.target.files?.[0] || null)} 
      />
    </label>
  );
}
