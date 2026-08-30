"use client";

import { useState, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { gradeAnswer } from "../lib/api";

export default function QuestionList({ questions, mappings, selectedId, onSelect, assessmentId, expandAll }) {
  const byQuestion = new Map(mappings.map((mapping) => [mapping.questionId, mapping]));
  const [grades, setGrades] = useState({});
  const [loadingGrades, setLoadingGrades] = useState({});

  useEffect(() => {
    if (selectedId && assessmentId) {
      const mapping = byQuestion.get(selectedId);
      if (mapping?.status === "ANSWERED" && !grades[selectedId] && !loadingGrades[selectedId]) {
        fetchGrade(selectedId, mapping);
      }
    }
  }, [selectedId, assessmentId]);

  useEffect(() => {
    if (expandAll && assessmentId) {
      questions.forEach((question) => {
        const mapping = byQuestion.get(question.id);
        if (mapping?.status === "ANSWERED" && !grades[question.id] && !loadingGrades[question.id]) {
          fetchGrade(question.id, mapping);
        }
      });
    }
  }, [expandAll, assessmentId, questions, grades, loadingGrades]);

  const fetchGrade = async (qId, mapping) => {
    setLoadingGrades(prev => ({ ...prev, [qId]: true }));
    try {
      const data = await gradeAnswer(assessmentId, {
        mappingId: mapping.id,
        questionId: qId,
        answerId: mapping.answerId
      });
      setGrades(prev => ({ ...prev, [qId]: data }));
    } catch (err) {
      console.error("Failed to fetch grade", err);
    } finally {
      setLoadingGrades(prev => ({ ...prev, [qId]: false }));
    }
  };

  const handleSelect = (questionId) => {
    onSelect(questionId);
    // Grade fetching is now handled by the useEffect above
  };

  return (
    <div className="flex-1 overflow-y-auto bg-transparent p-2 sm:p-4 lg:p-6">
      {questions.length === 0 && (
        <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-800">
          No questions could be extracted. Check the degraded status or try a clearer scan.
        </p>
      )}

      <div className="space-y-0">
        {questions.map((question) => {
          const mapping = byQuestion.get(question.id);
          const isSelected = selectedId === question.id;
          const isExpanded = isSelected || expandAll;
          const grade = grades[question.id];
          const isLoading = loadingGrades[question.id];

          let scoreText = mapping?.status;
          let scoreBg = "bg-slate-100";
          let scoreColor = "text-slate-500";

          if (mapping?.status === "ANSWERED") scoreText = isLoading ? "..." : (grade ? `${grade.score}/${grade.maxScore}` : "ANSWERED");
          if (grade) {
            if (grade.isCorrect) {
              scoreBg = "bg-[#E6F6E9]";
              scoreColor = "text-[#1DB335]";
            } else {
              scoreBg = "bg-[#FCECE8]";
              scoreColor = "text-[#EA643A]";
            }
          } else if (mapping?.status === "ANSWERED") {
            scoreBg = "bg-[#E6F6E9]";
            scoreColor = "text-[#1DB335]";
          }

          return (
            <div key={question.id} className={`group flex flex-col transition-all duration-200 mb-3`}>
              <div
                onClick={() => handleSelect(question.id)}
                role="button"
                tabIndex={0}
                className={`flex w-full flex-col p-4 sm:p-5 text-left cursor-pointer transition-all ${isSelected
                  ? "rounded-2xl border-2 border-[#EA643A] bg-white shadow-md z-10 relative"
                  : "rounded-2xl bg-white shadow-sm border border-slate-100 hover:shadow-md"
                  }`}
              >
                {/* Top Row: Number, Score & Chevron */}
                <div className="flex w-full items-center justify-between mb-3 sm:mb-4">
                  {/* Number Circle */}
                  <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#515151] text-[14px] font-bold text-white shadow-sm">
                    {question.displayNumber}
                  </div>

                  {/* Score & Chevron */}
                  <div className="flex items-center gap-2 sm:gap-3">
                    <span className={`px-3 py-1 rounded-full text-[13px] sm:text-[14px] font-bold ${scoreBg} ${scoreColor}`}>
                      {scoreText}
                    </span>
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#F5F6F8]">
                      {isExpanded ? (
                        <ChevronUp size={18} className="text-slate-600 shrink-0" />
                      ) : (
                        <ChevronDown size={18} className="text-slate-600 shrink-0" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Text Content */}
                <p className={`text-[14px] sm:text-[15px] leading-relaxed transition-colors ${isSelected ? "text-slate-900" : "text-slate-700 line-clamp-2 sm:line-clamp-none"}`}>
                  {question.text}
                </p>

                {/* Expanded AI Feedback */}
                {isExpanded && grade && (
                  <div className="mt-4 rounded-xl bg-[#F8F9FA] p-4 text-left border border-slate-50">
                    <p className="text-[14px] font-bold text-slate-900">AI Feedback</p>
                    <p className="mt-2 text-[14px] leading-relaxed text-slate-700">{grade.feedback}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
