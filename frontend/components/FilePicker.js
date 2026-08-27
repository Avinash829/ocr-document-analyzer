"use client";

export default function FilePicker({ id, label, hint, file, onChange }) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-semibold text-slate-800">{label}</label>
      <label htmlFor={id} className="group flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-5 text-center transition hover:border-indigo-400 hover:bg-indigo-50/40 focus-within:ring-2 focus-within:ring-indigo-500">
        <span aria-hidden="true" className="mb-3 grid size-11 place-items-center rounded-xl bg-white text-xl shadow-sm">↑</span>
        <span className="max-w-full truncate text-sm font-medium text-slate-800">{file ? file.name : "Choose a file"}</span>
        <span className="mt-1 text-xs text-slate-500">{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : hint}</span>
        <input id={id} className="sr-only" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg,image/webp" onChange={(event) => onChange(event.target.files?.[0] || null)} />
      </label>
    </div>
  );
}
