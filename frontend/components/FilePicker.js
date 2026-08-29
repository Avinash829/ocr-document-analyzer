"use client";

import { Upload } from "lucide-react";

export default function FilePicker({ id, titlePrefix, highlightText, hint, file, onChange }) {
  return (
    <label 
      htmlFor={id} 
      className="flex h-full w-full cursor-pointer flex-col items-center justify-center bg-white"
    >
      <div className="mb-[10px] flex h-[34px] w-[34px] items-center justify-center rounded-[7px] bg-[#F5F5F5] text-[#858585]">
        <Upload size={18} />
      </div>
      
      <span className="mb-[4px] text-[15px] font-semibold text-[#171717]">
        {file ? (
          <span className="truncate max-w-[200px] inline-block align-bottom">{file.name}</span>
        ) : (
          <>
            {titlePrefix} <span className="text-[#f05f37]">{highlightText}</span>
          </>
        )}
      </span>
      
      <span className="text-[12px] text-[#9CA3AF]">
        {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : hint}
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
