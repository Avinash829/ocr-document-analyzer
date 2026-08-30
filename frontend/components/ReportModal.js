import { X } from "lucide-react";

export default function ReportModal({ isOpen, onClose, totalScore, maxScore, feedback, isLoading, onReset }) {
  if (!isOpen) return null;

  const percentage = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;
  
  // Dynamic color based on percentage
  let ringColor = "text-emerald-500";
  if (percentage < 50) ringColor = "text-red-500";
  else if (percentage < 80) ringColor = "text-amber-500";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-md transform overflow-hidden rounded-3xl bg-white p-6 sm:p-8 shadow-2xl transition-all">
        <button 
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
        >
          <X size={20} />
        </button>

        <div className="text-center">
          <h3 className="text-xl font-bold text-slate-900">Final Assessment Report</h3>
          
          {/* Circular Progress */}
          <div className="relative mx-auto mt-8 flex h-40 w-40 items-center justify-center">
            <svg className="absolute h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                className="text-slate-100"
                strokeWidth="8"
                stroke="currentColor"
                fill="transparent"
                r="40"
                cx="50"
                cy="50"
              />
              {/* Foreground circle */}
              <circle
                className={`${ringColor} transition-all duration-1000 ease-out`}
                strokeWidth="8"
                strokeDasharray={251.2}
                strokeDashoffset={251.2 - (251.2 * percentage) / 100}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                r="40"
                cx="50"
                cy="50"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-4xl font-black text-slate-900">{percentage}%</span>
              <span className="mt-1 text-sm font-semibold text-slate-500">
                {totalScore} / {maxScore}
              </span>
            </div>
          </div>

          {/* AI Feedback */}
          <div className="mt-8 rounded-2xl bg-slate-50 p-5 text-left border border-slate-100 min-h-[100px] flex items-center justify-center">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center gap-2 text-slate-400">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600"></div>
                <span className="text-sm font-medium">Generating AI Summary...</span>
              </div>
            ) : (
              <div>
                <p className="text-sm font-bold text-slate-900 mb-2">AI Performance Summary</p>
                <p className="text-[14px] leading-relaxed text-slate-700">
                  {feedback || "No feedback generated."}
                </p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="mt-8 flex flex-col sm:flex-row gap-3">
            <button
              onClick={onClose}
              className="flex-1 rounded-xl border-2 border-slate-200 bg-white py-3 font-bold text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-all"
            >
              Review Answers
            </button>
            <button
              onClick={onReset}
              className="flex-1 rounded-xl bg-[#EA643A] py-3 font-bold text-white shadow-md shadow-orange-500/20 hover:bg-[#d65730] hover:shadow-lg transition-all"
            >
              Grade New Paper
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
