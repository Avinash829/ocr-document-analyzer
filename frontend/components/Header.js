"use client";

import Image from "next/image";
import { ArrowLeft, Bell, HelpCircle, Menu, ChevronDown, ClipboardList, Sparkles } from "lucide-react";

export default function Header({ onMenuClick }) {
  return (
    <header className="flex h-[72px] items-center justify-between bg-white px-4 border-b border-slate-200 lg:border-none lg:px-8">
      {/* Mobile Left: Logo */}
      <div className="flex items-center gap-2 lg:hidden">
        <img src="/assets/logo.png" alt="VedaAI Logo" className="h-7 w-auto object-contain" />
      </div>

      {/* Desktop Left: Breadcrumbs */}
      <div className="hidden lg:flex items-center gap-3 text-slate-800">
        <button className="text-slate-400 hover:text-slate-600">
          <ArrowLeft size={20} />
        </button>
        <div className="flex items-center gap-2 text-sm font-semibold">
          <img src="/assets/exam.png" alt="Exams" className="h-[18px] w-[18px] object-contain opacity-80" />
          Exams
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4 lg:gap-6">
        <button className="hidden lg:block text-slate-500 hover:text-slate-800">
          <HelpCircle size={22} />
        </button>
        <button className="relative text-slate-500 hover:text-slate-800">
          <Bell size={22} />
          <span className="absolute top-0 right-0 h-2 w-2 rounded-full bg-[#EA643A] border border-white"></span>
        </button>

        {/* AI Symbol */}
        <button className="flex items-center justify-center hover:opacity-80 transition-opacity">
          <img src="/assets/headerailogo.png" alt="AI Features" className="h-[22px] w-[22px] object-contain" />
        </button>

        <div className="flex items-center gap-2 cursor-pointer">
          <div className="h-8 w-8 rounded-full overflow-hidden bg-slate-200">
            {/* Placeholder for Avatar */}
            <div className="h-full w-full bg-[url('https://i.pravatar.cc/150?u=a042581f4e29026024d')] bg-cover"></div>
          </div>
          <span className="hidden lg:block text-sm font-medium text-slate-700">Madhur Rastogi</span>
          <ChevronDown size={16} className="hidden lg:block text-slate-400" />
        </div>
        <button onClick={onMenuClick} className="lg:hidden text-slate-800">
          <Menu size={24} />
        </button>
      </div>
    </header>
  );
}
