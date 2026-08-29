"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

export default function QuestionList({ questions, mappings, selectedId, onSelect, assessmentId }) {
  const byQuestion = new Map(mappings.map((mapping) => [mapping.questionId, mapping]));
  const [grades, setGrades] = useState({});
  const [loadingGrades, setLoadingGrades] = useState({});

  const handleSelect = async (questionId) => {
    onSelect(questionId);
    
    // Fetch grade if answered and not already fetched
    const mapping = byQuestion.get(questionId);
    if (mapping?.status === "ANSWERED" && !grades[questionId] && !loadingGrades[questionId] && assessmentId) {
      setLoadingGrades(prev => ({ ...prev, [questionId]: true }));
      try {
        const res = await fetch(`/api/assessments/${assessmentId}/grade`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mappingId: mapping.id,
            questionId: questionId,
            answerId: mapping.answerId
          })
        });
        if (res.ok) {
          const data = await res.json();
          setGrades(prev => ({ ...prev, [questionId]: data }));
        }
      } catch (err) {
        console.error("Failed to fetch grade", err);
      } finally {
        setLoadingGrades(prev => ({ ...prev, [questionId]: false }));
      }
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-white p-4 lg:p-6">
      {questions.length === 0 && (
        <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-800">
          No questions could be extracted. Check the degraded status or try a clearer scan.
        </p>
      )}
      
      <div className="space-y-0">
        {questions.map((question) => {
          const mapping = byQuestion.get(question.id);
          const isSelected = selectedId === question.id;
          const grade = grades[question.id];
          const isLoading = loadingGrades[question.id];
          
          let scoreText = mapping?.status;
          let scoreColor = "text-slate-500";
          if (mapping?.status === "ANSWERED") scoreText = isLoading ? "..." : (grade ? `${grade.score}/${grade.maxScore}` : "ANSWERED");
          if (grade) {
            scoreColor = grade.isCorrect ? "text-[#1DB335]" : "text-[#EA643A]";
          } else if (mapping?.status === "ANSWERED") {
            scoreColor = "text-[#1DB335]";
          }

          return (
            <div key={question.id} className={`group flex flex-col transition-all duration-200 ${isSelected ? "my-3" : ""}`}>
              <button
                onClick={() => handleSelect(question.id)}
                className={`flex w-full items-start gap-4 p-4 text-left transition-all ${
                  isSelected 
                    ? "rounded-2xl border-2 border-[#EA643A] bg-white shadow-[0_4px_20px_-4px_rgba(234,100,58,0.15)]" 
                    : "border-b border-slate-100 bg-white hover:bg-slate-50"
                }`}
              >
                {/* Number Circle */}
                <div className={`mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full text-[13px] font-bold text-white transition-colors ${
                  isSelected ? "bg-[#EA643A]" : "bg-slate-600"
                }`}>
                  {question.displayNumber}
                </div>
                
                {/* Text Content */}
                <div className="flex-1">
                  <p className={`text-[15px] leading-relaxed transition-colors ${isSelected ? "text-slate-900 font-medium" : "text-slate-700 line-clamp-2"}`}>
                    {question.text}
                  </p>
                  
                  {/* Expanded AI Feedback */}
                  {isSelected && grade && (
                    <div className="mt-4 rounded-xl bg-[#F8F9FA] p-4 text-left">
                      <p className="text-[13px] font-bold text-slate-900">AI Feedback</p>
                      <p className="mt-1 text-[14px] leading-relaxed text-slate-700">{grade.feedback}</p>
                    </div>
                  )}
                </div>

                {/* Score & Chevron */}
                <div className="flex shrink-0 items-center gap-3">
                  <span className={`text-[15px] font-bold ${scoreColor}`}>
                    {scoreText}
                  </span>
                  {isSelected ? (
                    <ChevronUp size={20} className="text-slate-400" />
                  ) : (
                    <ChevronDown size={20} className="text-slate-300 group-hover:text-slate-500" />
                  )}
                </div>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
