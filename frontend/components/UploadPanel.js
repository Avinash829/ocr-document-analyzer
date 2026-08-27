"use client";

import { useState } from "react";
import FilePicker from "./FilePicker";

export default function UploadPanel({ onSubmit, busy }) {
  const [questionPaper, setQuestionPaper] = useState(null);
  const [answerSheet, setAnswerSheet] = useState(null);

  function submit(event) {
    event.preventDefault();
    if (questionPaper && answerSheet) onSubmit(questionPaper, answerSheet);
  }

  return (
    <section className="mx-auto mt-14 max-w-3xl rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_20px_60px_rgba(15,23,42,.08)] sm:p-9">
      <div className="mb-8 text-center">
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">NEW ASSESSMENT</span>
        <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">Find every answer, precisely</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-600">Upload a question paper and one student’s answer sheet. Veda extracts, maps, and locates their work without hiding uncertainty.</p>
      </div>
      <form onSubmit={submit}>
        <div className="grid gap-5 sm:grid-cols-2">
          <FilePicker id="question-paper" label="Question paper" hint="PDF, PNG, JPEG or WebP" file={questionPaper} onChange={setQuestionPaper} />
          <FilePicker id="answer-sheet" label="Student answer sheet" hint="PDF, PNG, JPEG or WebP" file={answerSheet} onChange={setAnswerSheet} />
        </div>
        <button disabled={!questionPaper || !answerSheet || busy} className="mt-7 w-full rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none">
          {busy ? "Starting…" : "Analyze assessment"}
        </button>
      </form>
      <p className="mt-4 text-center text-xs text-slate-400">Files are temporary and automatically expire from the processing server.</p>
    </section>
  );
}
