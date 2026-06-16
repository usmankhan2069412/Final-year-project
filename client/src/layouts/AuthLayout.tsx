import React from "react";
import { useLocation } from "wouter";

interface AuthLayoutProps {
  children: React.ReactNode;
  title: React.ReactNode;
  subtitle: React.ReactNode;
  extraCenter?: React.ReactNode;
  showSpinCircle?: boolean;
}

export default function AuthLayout({ children, title, subtitle, extraCenter, showSpinCircle = false }: AuthLayoutProps) {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen bg-white text-[#1c1c1e] font-sans flex relative selection:bg-[#EBDCFF] selection:text-[#1c1c1e]">
      
      {/* Left Panel - Visual Appeal Area (Hidden on Mobile) */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 relative overflow-hidden bg-[#1c1c1e] text-[#F5F5F7]">
        
        {/* Background ambient light */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#EBDCFF] rounded-full mix-blend-overlay opacity-5 blur-3xl animate-in fade-in duration-1000"></div>
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-white rounded-full mix-blend-overlay opacity-5 blur-3xl animate-in fade-in duration-1000"></div>

        {/* Logo */}
        <div 
          className="animate-in fade-in slide-in-from-bottom-4 duration-700 font-serif text-3xl font-bold tracking-tight text-[#F5F5F7] flex items-center gap-3 cursor-pointer z-10 hover:opacity-90 transition-opacity" 
          onClick={() => setLocation("/")}
        >
          <div className="w-10 h-10 bg-[#EBDCFF] rounded-xl flex items-center justify-center text-[#1c1c1e] shadow-md hover:scale-105 active:scale-95 transition-transform duration-300">
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
          </div>
          Aina
        </div>

        {/* Center Graphic */}
        <div className="flex-grow flex flex-col justify-center relative z-10 my-12">
           <h2 className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-150 fill-mode-both font-serif text-[4rem] leading-[1.05] tracking-tight mb-8" style={{ fontFamily: "'Playfair Display', serif" }}>
              {title}
           </h2>
           <p className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300 fill-mode-both text-white/60 text-xl max-w-md leading-relaxed">
             {subtitle}
           </p>
           {extraCenter && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500 fill-mode-both">
                {extraCenter}
              </div>
           )}
        </div>

        

      </div>

      {/* Right Panel - Form Area */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 relative bg-[#F5F5F7]">
        
        {/* Mobile Header (Only visible on small screens) */}
        <header className="absolute top-0 left-0 w-full flex justify-between items-center px-6 py-6 lg:hidden z-20">
            <div className="font-serif text-2xl font-bold tracking-tight text-[#1c1c1e] flex items-center gap-2 cursor-pointer" onClick={() => setLocation("/")}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#1c1c1e]">
                <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
            Aina
            </div>
        </header>

        {children}
      </div>
    </div>
  );
}
