"use client";

import { useMemo, useState } from "react";
import DocumentViewer from "./DocumentViewer";
import QuestionList from "./QuestionList";

export default function ResultsWorkspace({ result, onReset }) {
  const [selectedId, setSelectedId] = useState(result.questions[0]?.id || null);
  const mapping = result.mappings.find((item) => item.questionId === selectedId);
  const question = result.questions.find((item) => item.id === selectedId);
  const answer = result.answers.find((item) => item.id === mapping?.answerId);
  const regions = useMemo(() => mapping?.regions || [], [mapping]);

  return (
    <section className="mx-auto max-w-[1500px] p-3 sm:p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold text-slate-950">Assessment results</h2><p className="text-xs text-slate-500">{result.summary.answered} answered · {result.summary.unanswered} unanswered · {result.summary.ambiguous} ambiguous · {result.summary.unmatchedAnswers} unmatched</p></div><button onClick={onReset} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50">New assessment</button></div>
      {result.processing.stage === "DEGRADED" && <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">Limited processing: {result.processing.degradedReasons.join(", ").replaceAll("_", " ")}. No unavailable AI/OCR result was fabricated.</div>}
      <div className="grid h-[calc(100vh-160px)] min-h-[650px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg lg:grid-cols-[310px_minmax(0,1fr)_300px]">
        <QuestionList questions={result.questions} mappings={result.mappings} selectedId={selectedId} onSelect={setSelectedId} />
        <DocumentViewer key={selectedId || "none"} document={result.answerSheet} regions={regions} />
        <aside className="overflow-y-auto border-l border-slate-200 bg-white p-5">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Answer details</p>
          {question ? <><h3 className="mt-3 text-xl font-semibold text-slate-950">Question {question.displayNumber}</h3><p className="mt-2 whitespace-pre-line text-sm leading-6 text-slate-600">{question.text}</p><hr className="my-5 border-slate-200" /><div className="space-y-4 text-sm"><Detail label="Status" value={mapping?.status} /><Detail label="Confidence" value={mapping ? `${Math.round(mapping.confidence * 100)}%` : "—"} /><Detail label="Pages" value={regions.length ? [...new Set(regions.map((item) => item.page))].join(", ") : "—"} /></div><div className="mt-6 rounded-xl bg-slate-50 p-4"><p className="text-xs font-semibold text-slate-500">Extracted answer</p><p className="mt-2 whitespace-pre-line text-sm leading-6 text-slate-700">{answer?.text || (mapping?.status === "UNANSWERED" ? "No answer was confidently identified." : "Review the highlighted candidate region.")}</p></div></> : <p className="mt-4 text-sm text-slate-500">Select a question to inspect its answer.</p>}
        </aside>
      </div>
    </section>
  );
}

function Detail({ label, value }) { return <div className="flex items-center justify-between gap-3"><span className="text-slate-500">{label}</span><span className="text-right text-xs font-semibold text-slate-800">{value || "—"}</span></div>; }
