import AssessmentWorkspace from "@/components/AssessmentWorkspace";

export default function Home() {
  return (
    <main className="min-h-screen">
      <header className="border-b border-slate-200 bg-white/90 px-5 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-indigo-600 text-lg font-bold text-white">V</div>
            <div><h1 className="font-semibold text-slate-950">Veda</h1><p className="text-xs text-slate-500">Assessment answer mapper</p></div>
          </div>
          <p className="hidden text-sm text-slate-500 sm:block">Teacher workspace</p>
        </div>
      </header>
      <AssessmentWorkspace />
    </main>
  );
}
