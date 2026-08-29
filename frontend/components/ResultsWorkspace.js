"use client";

import { useMemo, useState } from "react";
import DocumentViewer from "./DocumentViewer";
import QuestionList from "./QuestionList";

export default function ResultsWorkspace({ result, onReset }) {
  const [selectedId, setSelectedId] = useState(result.questions[0]?.id || null);
  const [mobileTab, setMobileTab] = useState("Questions"); // "Questions" or "Answer Sheet"

  const mapping = result.mappings.find((item) => item.questionId === selectedId);
  const question = result.questions.find((item) => item.id === selectedId);
  const answer = result.answers.find((item) => item.id === mapping?.answerId);
  const regions = useMemo(() => mapping?.regions || [], [mapping]);

  return (
    <section className="mx-auto flex h-full max-w-[1600px] flex-col p-4 lg:p-6">
      {/* Mobile Tab Switcher */}
      <div className="mb-4 flex rounded-full bg-slate-900 p-1 lg:hidden">
        <button
          onClick={() => setMobileTab("Questions")}
          className={`flex-1 rounded-full py-2.5 text-sm font-semibold transition-colors ${mobileTab === "Questions" ? "bg-white text-slate-900" : "text-white"
            }`}
        >
          Questions
        </button>
        <button
          onClick={() => setMobileTab("Answer Sheet")}
          className={`flex-1 rounded-full py-2.5 text-sm font-semibold transition-colors ${mobileTab === "Answer Sheet" ? "bg-white text-slate-900" : "text-white"
            }`}
        >
          Answer Sheet
        </button>
      </div>

      {result.processing.stage === "DEGRADED" && (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          Limited processing: {result.processing.degradedReasons.join(", ").replaceAll("_", " ")}. No unavailable AI/OCR result was fabricated.
        </div>
      )}

      {/* Main Grid Workspace */}
      <div className="flex flex-1 min-h-[600px] gap-6 overflow-hidden">
        {/* Questions Panel */}
        <div className={`flex w-full lg:w-[420px] flex-col overflow-hidden rounded-3xl bg-white shadow-sm ${mobileTab === "Questions" ? "block" : "hidden lg:flex"}`}>
          <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
            <h2 className="text-[15px] font-bold text-slate-900">Extracted Questions <span className="text-slate-500 font-normal">(from question paper)</span></h2>
            <button className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Expand All</button>
          </div>
          <QuestionList questions={result.questions} mappings={result.mappings} selectedId={selectedId} onSelect={setSelectedId} assessmentId={result.id} />
        </div>

        {/* Answer Sheet Panel */}
        <div className={`flex flex-1 flex-col overflow-hidden rounded-3xl bg-[#DCE0E5] shadow-sm ${mobileTab === "Answer Sheet" ? "block" : "hidden lg:flex"}`}>
          <DocumentViewer key={selectedId || "none"} document={result.answerSheet} regions={regions} />
        </div>

        {/* Answer Details Panel - Desktop Only (As requested) */}
        <aside className="hidden lg:flex w-[320px] flex-col overflow-y-auto rounded-3xl bg-white shadow-sm p-6">
          <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400">Answer details</p>
          {question ? (
            <>
              <h3 className="mt-4 text-[22px] font-bold text-slate-900">Question {question.displayNumber}</h3>
              <p className="mt-3 whitespace-pre-line text-[15px] leading-relaxed text-slate-600">{question.text}</p>

              <hr className="my-6 border-slate-100" />

              <div className="space-y-4">
                <Detail label="Status" value={mapping?.status} />
                <Detail label="Confidence" value={mapping ? `${Math.round(mapping.confidence * 100)}%` : "—"} />
                <Detail label="Pages" value={regions.length ? [...new Set(regions.map((item) => item.page))].join(", ") : "—"} />
              </div>

              <div className="mt-8 rounded-2xl border border-slate-100 bg-slate-50 p-5">
                <p className="text-[13px] font-bold text-slate-500">Extracted answer</p>
                <p className="mt-3 whitespace-pre-line text-[15px] leading-relaxed text-slate-800">
                  {answer?.text || (mapping?.status === "UNANSWERED" ? "No answer was confidently identified." : "Review the highlighted candidate region.")}
                </p>
              </div>
            </>
          ) : (
            <p className="mt-4 text-sm text-slate-500">Select a question to inspect its answer.</p>
          )}
        </aside>
      </div>
    </section>
  );
}

function Detail({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[14px] font-medium text-slate-500">{label}</span>
      <span className="text-right text-[14px] font-bold text-slate-900">{value || "—"}</span>
    </div>
  );
}
