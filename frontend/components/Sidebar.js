"use client";

import { LayoutGrid, Presentation, FileText, ClipboardList, Clock, PanelLeftClose, PanelLeftOpen, Settings } from "lucide-react";

export default function Sidebar({ isOpen, setIsOpen, isCollapsed, setIsCollapsed }) {
  const navItems = [
    { name: "Home", icon: LayoutGrid, active: false },
    { name: "My Classroom", icon: Presentation, imgSrc: "/assets/classroom.png", active: false },
    { name: "Assignments", icon: FileText, active: false },
    { name: "Exams", icon: ClipboardList, imgSrc: "/assets/exam.png", active: true },
    { name: "My Library", icon: Clock, imgSrc: "/assets/library.png", active: false },
  ];

  const bottomNavItems = [
    { name: "Settings", icon: Settings, imgSrc: "/assets/settings.png", active: false },
  ];

  const renderNavItem = (item) => (
    <a
      key={item.name}
      href="#"
      title={isCollapsed ? item.name : undefined}
      className={`flex items-center rounded-xl transition-all ${
        isCollapsed ? "justify-center h-12 w-12 mx-auto" : "gap-3 px-4 py-3"
      } ${
        item.active
          ? "bg-[#F3F4F6] text-slate-900 shadow-sm"
          : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
      }`}
    >
      {item.imgSrc ? (
        <img src={item.imgSrc} alt={item.name} className="h-5 w-5 shrink-0 object-contain" />
      ) : (
        <item.icon size={20} className={`shrink-0 ${item.active ? "text-slate-800" : "text-slate-400"}`} />
      )}
      {!isCollapsed && <span className="text-[14px] font-semibold whitespace-nowrap">{item.name}</span>}
    </a>
  );

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-white transition-all duration-300 ease-in-out lg:static lg:translate-x-0 lg:rounded-2xl lg:shadow-xl border-r lg:border-none border-slate-200 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        } ${isCollapsed ? "w-[88px]" : "w-[260px]"}`}
      >
        {/* Logo Area */}
        <div className={`flex h-[72px] items-center pt-2 ${isCollapsed ? "justify-center px-0" : "justify-between px-6"}`}>
          {!isCollapsed && (
            <div className="flex items-center gap-[6px]">
              <img src="/assets/logo.png" alt="VedaAI Logo" className="h-7 w-auto object-contain" />
              <img src="/assets/vedaaitext.png" alt="VedaAI" className="h-4 w-auto object-contain mt-0.5" />
            </div>
          )}
          
          {/* Mobile close button */}
          <button onClick={() => setIsOpen(false)} className="lg:hidden p-1.5 hover:opacity-80 transition-opacity">
            <img src="/assets/sidebartoggle.png" alt="Close Sidebar" className="h-5 w-5 object-contain rotate-180" />
          </button>
          
          {/* Desktop collapse toggle */}
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)} 
            className={`hidden lg:flex items-center justify-center p-1.5 hover:opacity-80 transition-opacity ${isCollapsed ? "" : "-mr-2"}`}
          >
            <img 
              src="/assets/sidebartoggle.png" 
              alt="Toggle Sidebar" 
              className={`h-5 w-5 object-contain transition-transform duration-300 ${isCollapsed ? "rotate-180" : ""}`} 
            />
          </button>
        </div>

        {/* AI Toolkit Button */}
        <div className={`mt-4 ${isCollapsed ? "px-4" : "px-5"}`}>
          <button className={`flex items-center justify-center gap-2 rounded-full bg-[#303030] text-sm font-medium text-white shadow-[0_0_0_2px_#EA643A] hover:bg-[#404040] transition-all overflow-hidden ${
            isCollapsed ? "h-12 w-12 p-0 mx-auto" : "w-full px-4 py-3"
          }`}>
            <img src="/assets/ailogo.png" alt="AI Toolkit" className="h-4 w-4 shrink-0" />
            {!isCollapsed && <span className="whitespace-nowrap font-semibold">AI Teacher's Toolkit</span>}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col flex-1 px-4 mt-8 space-y-2 overflow-y-auto">
          <div className="space-y-2 flex-1">
            {navItems.map(renderNavItem)}
          </div>
          
          <div className="pb-2">
            {bottomNavItems.map(renderNavItem)}
          </div>
        </nav>

        {/* School Card */}
        <div className={`p-4 ${isCollapsed ? "flex justify-center" : ""}`}>
          <div className={`flex items-center rounded-2xl bg-[#F4F4F4] ${isCollapsed ? "justify-center p-2 w-[52px] h-[52px]" : "gap-3 p-3 w-full"}`}>
            <div className="flex h-[36px] w-[36px] shrink-0 items-center justify-center rounded-full bg-white text-green-700 shadow-sm overflow-hidden">
              <img src="/assets/schoolicon.png" alt="School" className="h-full w-full object-cover" />
            </div>
            {!isCollapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-bold leading-tight text-slate-900">Delhi Public School</p>
                <p className="truncate text-[11px] text-slate-500 mt-0.5">Bokaro Steel City</p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
