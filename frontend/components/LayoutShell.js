"use client";

import { useState } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function LayoutShell({ children }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-gradient-to-b from-gray-100 via-gray-200 to-gray-300 font-sans text-slate-900 overflow-hidden lg:p-4 lg:gap-4">
      <Sidebar
        isOpen={isSidebarOpen}
        setIsOpen={setIsSidebarOpen}
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
      />
      <div className="flex flex-1 flex-col overflow-hidden gap-4">
        <div className="hidden lg:block rounded-2xl overflow-hidden bg-white shadow-sm">
          <Header onMenuClick={() => setIsSidebarOpen(true)} />
        </div>
        <div className="lg:hidden">
          <Header onMenuClick={() => setIsSidebarOpen(true)} />
        </div>
        <main className="flex-1 overflow-y-auto ">
          {children}
        </main>
      </div>
    </div>
  );
}
