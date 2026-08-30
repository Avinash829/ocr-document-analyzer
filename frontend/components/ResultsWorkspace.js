"use client";

import { useMemo, useState } from "react";
import DocumentViewer from "./DocumentViewer";
import QuestionList from "./QuestionList";

export default function ResultsWorkspace({ result, onReset }) {
  const [selectedId, setSelectedId] = useState(result.questions[0]?.id || null);
  const [mobileTab, setMobileTab] = useState("Questions"); // "Questions" or "Answer Sheet"
  const [expandAll, setExpandAll] = useState(false);

  const mapping = result.mappings.find((item) => item.questionId === selectedId);
  const question = result.questions.find((item) => item.id === selectedId);
  const answer = result.answers.find((item) => item.id === mapping?.answerId);
  const regions = useMemo(() => mapping?.regions || [], [mapping]);

  return (
    <section className="mx-auto flex h-full min-h-0 max-w-[1600px] flex-col p-4 lg:p-6">
      {/* Mobile Tab Switcher */}
      <div className="mb-4 flex rounded-full bg-white shadow-[0_2px_10px_rgba(0,0,0,0.05)] border border-slate-100 p-1.5 lg:hidden">
        <button
          onClick={() => setMobileTab("Questions")}
          className={`flex-1 rounded-full py-2.5 text-[15px] font-semibold transition-colors ${mobileTab === "Questions" ? "bg-[#2B2B2B] text-white shadow-md" : "text-slate-500 hover:text-slate-800"
            }`}
        >
          Questions
        </button>
        <button
          onClick={() => setMobileTab("Answer Sheet")}
          className={`flex-1 rounded-full py-2.5 text-[15px] font-semibold transition-colors ${mobileTab === "Answer Sheet" ? "bg-[#2B2B2B] text-white shadow-md" : "text-slate-500 hover:text-slate-800"
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
      <div className="flex min-h-0 flex-1 flex-col gap-4 sm:gap-6 lg:flex-row overflow-hidden">
        {/* Questions Panel */}
        <div className={`flex w-full flex-col overflow-hidden rounded-[20px] sm:rounded-3xl bg-white shadow-sm lg:w-[420px] ${mobileTab === "Questions" ? "flex flex-1" : "hidden lg:flex"}`}>
          <div className="flex items-center justify-between border-b border-slate-100 px-4 sm:px-6 py-4">
            <h2 className="text-[15px] font-bold text-slate-900">
              Extracted Questions <span className="text-slate-500 font-normal">(from question paper)</span>
            </h2>
            <button 
              onClick={() => setExpandAll(!expandAll)}
              className="hidden sm:block rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors">
              {expandAll ? "Collapse All" : "Expand All"}
            </button>
          </div>
          <QuestionList questions={result.questions} mappings={result.mappings} selectedId={selectedId} onSelect={setSelectedId} assessmentId={result.id} expandAll={expandAll} />
        </div>

        {/* Answer Sheet Panel */}
        <div className={`flex flex-1 flex-col overflow-hidden rounded-[20px] sm:rounded-3xl bg-[#DCE0E5] shadow-sm ${mobileTab === "Answer Sheet" ? "flex flex-1" : "hidden lg:flex"}`}>
          <DocumentViewer key={selectedId || "none"} document={result.answerSheet} regions={regions} question={question} />
        </div>
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
