"use client";

import { useEffect, useState } from "react";
import { createAssessment, getJob, getResult } from "@/lib/api";
import ProcessingPanel from "./ProcessingPanel";
import ResultsWorkspace from "./ResultsWorkspace";
import UploadPanel from "./UploadPanel";


export default function AssessmentWorkspace() {
  const [state, setState] = useState({ view: "upload", busy: false, jobId: null, processing: null, result: null, error: null });

  async function submit(question, answer) {
    setState((old) => ({ ...old, busy: true, error: null }));
    try {
      const job = await createAssessment(question, answer);
      setState({ view: "processing", busy: false, jobId: job.id, processing: job.processing, result: null, error: null });
    } catch (error) { setState((old) => ({ ...old, busy: false, error: error.message })); }
  }

  useEffect(() => {
    if (state.view !== "processing" || !state.jobId) return;
    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const job = await getJob(state.jobId);
        if (cancelled) return;
        if (["COMPLETED", "DEGRADED"].includes(job.processing.stage)) {
          clearInterval(timer);
          const result = await getResult(state.jobId);
          if (!cancelled) setState((old) => ({ ...old, view: "results", processing: job.processing, result }));
        } else if (job.processing.stage === "ERROR") {
          clearInterval(timer);
          setState((old) => ({ ...old, view: "error", processing: job.processing, error: job.error?.message || "Processing failed." }));
        } else setState((old) => ({ ...old, processing: job.processing }));
      } catch (error) { clearInterval(timer); if (!cancelled) setState((old) => ({ ...old, view: "error", error: error.message })); }
    }, 1200);
    return () => { cancelled = true; clearInterval(timer); };
  }, [state.view, state.jobId]);

  const reset = () => setState({ view: "upload", busy: false, jobId: null, processing: null, result: null, error: null });
  if (state.view === "processing") return <ProcessingPanel processing={state.processing} />;
  if (state.view === "results") return <ResultsWorkspace result={state.result} onReset={reset} />;
  if (state.view === "error") return <ErrorPanel message={state.error} onReset={reset} />;
  return <div className="px-4"><UploadPanel onSubmit={submit} busy={state.busy} />{state.error && <p role="alert" className="mx-auto mt-4 max-w-3xl rounded-xl bg-rose-50 p-3 text-center text-sm text-rose-700">{state.error}</p>}</div>;
}

function ErrorPanel({ message, onReset }) { return <section className="mx-auto mt-24 max-w-lg rounded-3xl border border-rose-200 bg-white p-8 text-center shadow-lg"><div className="mx-auto grid size-12 place-items-center rounded-full bg-rose-50 text-xl text-rose-700">!</div><h2 className="mt-5 text-xl font-semibold text-slate-950">Processing stopped</h2><p className="mt-2 text-sm text-slate-600">{message}</p><button onClick={onReset} className="mt-6 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white">Try another upload</button></section>; }
