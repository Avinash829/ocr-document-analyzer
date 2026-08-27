const colors = {
  ANSWERED: "bg-emerald-50 text-emerald-700",
  UNANSWERED: "bg-slate-100 text-slate-600",
  AMBIGUOUS: "bg-amber-50 text-amber-700",
};

export default function QuestionList({ questions, mappings, selectedId, onSelect }) {
  const byQuestion = new Map(mappings.map((mapping) => [mapping.questionId, mapping]));
  return (
    <aside className="flex min-h-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-5"><p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Questions</p><h2 className="mt-1 text-lg font-semibold text-slate-950">Extracted paper</h2></div>
      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        {questions.length === 0 && <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-800">No questions could be extracted. Check the degraded status or try a clearer scan.</p>}
        {questions.map((question) => {
          const mapping = byQuestion.get(question.id);
          return <button key={question.id} onClick={() => onSelect(question.id)} className={`mb-2 w-full rounded-xl border p-3 text-left transition focus:outline-none focus:ring-2 focus:ring-indigo-500 ${selectedId === question.id ? "border-indigo-300 bg-indigo-50" : "border-transparent hover:bg-slate-50"}`}>
            <div className="flex items-center justify-between gap-2"><span className="font-semibold text-slate-900">{question.displayNumber}</span><span className={`rounded-full px-2 py-1 text-[10px] font-bold ${colors[mapping?.status] || colors.UNANSWERED}`}>{mapping?.status || "UNANSWERED"}</span></div>
            <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{question.text}</p>
          </button>;
        })}
      </div>
    </aside>
  );
}
