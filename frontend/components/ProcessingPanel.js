const STAGES = ["VALIDATING", "READING_QUESTION_PAPER", "EXTRACTING_QUESTIONS", "READING_ANSWER_SHEET", "EXTRACTING_ANSWERS", "MAPPING_ANSWERS", "VALIDATING_RESULTS", "FINALIZING"];

export default function ProcessingPanel({ processing }) {
  const active = Math.max(0, STAGES.indexOf(processing.stage));
  return (
    <section className="mx-auto mt-24 max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-xl shadow-slate-200/50" aria-live="polite">
      <div className="mx-auto mb-6 size-14 animate-spin rounded-full border-4 border-indigo-100 border-t-indigo-600" />
      <h2 className="text-xl font-semibold text-slate-950">Analyzing assessment</h2>
      <p className="mt-2 text-sm text-slate-600">{processing.message}</p>
      {processing.progress != null && <div className="mt-7 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-indigo-600 transition-all" style={{ width: `${processing.progress}%` }} /></div>}
      <div className="mt-3 flex justify-between text-xs text-slate-400"><span>{STAGES[active]?.replaceAll("_", " ")}</span><span>{processing.progress != null ? `${processing.progress}%` : ""}</span></div>
    </section>
  );
}
