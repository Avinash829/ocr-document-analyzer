"use client";

import { useState } from "react";
import FilePicker from "./FilePicker";
import { ArrowRight } from "lucide-react";

export default function UploadPanel({ onSubmit, busy }) {
  const [questionPaper, setQuestionPaper] = useState(null);
  const [answerSheet, setAnswerSheet] = useState(null);

  function submit(event) {
    event.preventDefault();

    if (questionPaper && answerSheet && !busy) {
      onSubmit(questionPaper, answerSheet);
    }
  }

  const canStart = questionPaper && answerSheet && !busy;

  return (
    <section className="mx-auto flex h-full w-full flex-col items-center px-4 pt-1 sm:pt-8">
      {/* Header */}
      <div className="w-full text-center">
        {/* Desktop Heading */}
        <h2 className="hidden sm:flex items-center justify-center text-[34px] font-bold leading-none tracking-[-1.5px]">
          <span className="text-[#272727]">Upload</span>
          <span className="ml-1 rounded-[7px] bg-[#f9e4da] px-[10px] py-[7px] text-[#f05f37]">
            Question Paper &amp; Answer Sheets
          </span>
        </h2>

        {/* Mobile Heading */}
        <h2 className="sm:hidden text-center text-[22px] font-bold leading-tight tracking-tight text-[#272727]">
          Upload Question Paper<br />
          &amp; Answer Sheets
        </h2>

        <p className="mt-[2px] sm:mt-[9px] text-[15px] sm:text-[17px] font-normal leading-[22px] text-[#303030]">
          Upload both files to get started
        </p>
      </div>

      {/* Teacher Graphic */}
      <div className="relative mt-[16px] sm:mt-[24px] h-[100px] w-[100px] sm:h-[130px] sm:w-[130px] shrink-0">
        {/* Teacher - BACK layer */}
        <img
          src="/assets/teacherlogo.png"
          alt="Teacher"
          className="absolute left-1/2 top-1/2 z-10 h-[80px] w-[80px] sm:h-[120px] sm:w-[120px] -translate-x-1/2 -translate-y-1/2 rounded-full object-cover"
        />

        {/* Rotating icons + circle - FRONT layer */}
        <img
          src="/assets/iconsaroundteacherlogo.png"
          alt=""
          aria-hidden="true"
          className="absolute left-1/2 top-1/2 z-20 h-[80px] w-[80px] sm:h-[100px] sm:w-[100px] -translate-x-1/2 -translate-y-1/2 object-contain opacity-90 animate-[spin_30s_linear_infinite]"
        />
      </div>

      {/* Upload Form */}
      <form
        onSubmit={submit}
        className="mt-[16px] sm:mt-[18px] w-full max-w-[716px]"
      >
        {/* Gray outer container: stacked on mobile, grid on desktop */}
        <div className="flex flex-col sm:grid sm:h-[181px] sm:grid-cols-2 gap-[8px] sm:gap-[14px] rounded-[20px] bg-[#eeeeee] p-[8px] sm:p-[10px]">
          {/* Question Paper */}
          <div className="h-[110px] sm:h-[159px] overflow-hidden rounded-[16px] border-2 border-dashed border-[#d8d8d8] bg-white">
            <FilePicker
              id="question-paper"
              titlePrefix="Upload"
              highlightText="Question Paper"
              hint="Max 10MB"
              file={questionPaper}
              onChange={setQuestionPaper}
            />
          </div>

          {/* Answer Sheet */}
          <div className="h-[110px] sm:h-[159px] overflow-hidden rounded-[16px] border-2 border-dashed border-[#d8d8d8] bg-white">
            <FilePicker
              id="answer-sheet"
              titlePrefix="Upload"
              highlightText="Answer Sheet"
              hint="Max 10MB"
              file={answerSheet}
              onChange={setAnswerSheet}
            />
          </div>
        </div>

        {/* Button + Footer */}
        <div className="mt-[24px] sm:mt-[32px] flex flex-col items-center">
          <button
            type="submit"
            disabled={!canStart}
            className={[
              "inline-flex h-[36px] w-[142px] items-center justify-center gap-2",
              "rounded-full px-[15px]",
              "text-[13px] font-medium leading-none text-gray-200",
              "transition-colors",
              "disabled:cursor-not-allowed",
              canStart
                ? "bg-gray-400 hover:bg-[#e5552e]"
                : "bg-gray-400",
            ].join(" ")}
          >
            <span>
              {busy ? "Starting…" : "Start Mapping"}
            </span>

            <ArrowRight
              size={18}
              strokeWidth={2}
            />
          </button>

          <p className="mt-[16px] max-w-[420px] text-center text-[12px] font-normal leading-[17px] text-gray-500">
            Once both files are uploaded, you'll able to map
            answers with questions
          </p>
        </div>
      </form>
    </section>
  );
}