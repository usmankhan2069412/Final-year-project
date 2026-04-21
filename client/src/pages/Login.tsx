import { useLocation } from "wouter";
import { useState, useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP);

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const container = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    // Left panel animations
    gsap.from(".brand-element", {
      y: 40,
      opacity: 0,
      duration: 1,
      stagger: 0.2,
      ease: "power3.out",
    });

    gsap.to(".spin-circle", {
      rotate: 360,
      duration: 25,
      repeat: -1,
      ease: "none",
    });

    // Right panel / form animations
    gsap.from(".auth-item", {
      y: 20,
      opacity: 0,
      duration: 0.6,
      stagger: 0.08,
      ease: "power2.out",
      delay: 0.2
    });
  }, { scope: container });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock authentication
    setLocation("/dashboard");
  };

  return (
    <div ref={container} className="min-h-screen bg-white text-[#1c1c1e] font-sans flex relative selection:bg-[#EBDCFF] selection:text-[#1c1c1e]">
      
      {/* Left Panel - Visual Appeal Area (Hidden on Mobile) */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 relative overflow-hidden bg-[#1c1c1e] text-[#fbfbf2]">
        
        {/* Background ambient light */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#EBDCFF] rounded-full mix-blend-overlay opacity-5 blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-white rounded-full mix-blend-overlay opacity-5 blur-3xl"></div>

        {/* Logo */}
        <div 
          className="brand-element font-serif text-3xl font-bold tracking-tight text-[#fbfbf2] flex items-center gap-3 cursor-pointer z-10" 
          onClick={() => setLocation("/")}
        >
          <div className="w-10 h-10 bg-[#EBDCFF] rounded-xl flex items-center justify-center text-[#1c1c1e]">
             <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
          </div>
          Aina
        </div>

        {/* Center Graphic */}
        <div className="flex-grow flex flex-col justify-center relative z-10 my-12">
           <h2 className="brand-element font-serif text-[4rem] leading-[1.05] tracking-tight mb-8" style={{ fontFamily: "'Playfair Display', serif" }}>
              Don't code, <br/><span className="italic text-[#EBDCFF]">just build</span>.
           </h2>
           <p className="brand-element text-white/60 text-xl max-w-md leading-relaxed">
             Sign in to access your AI automations, deploy new flows, and manage customer interactions across all channels.
           </p>

           <div className="brand-element mt-16 flex items-center gap-4">
              <div className="flex -space-x-3">
                 {[1,2,3,4].map((i) => (
                    <div key={i} className={`w-10 h-10 rounded-full border-2 border-[#1c1c1e] bg-white/10 flex items-center justify-center overflow-hidden backdrop-blur-md`}>
                       <img src={`https://i.pravatar.cc/100?img=${i+10}`} alt="avatar" className="w-full h-full object-cover" />
                    </div>
                 ))}
              </div>
              <p className="text-sm font-medium text-white/50">Joined by 500+ businesses</p>
           </div>
        </div>

        {/* Decorative Floating Element */}
        <div className="absolute right-16 top-1/2 -translate-y-1/2 w-80 h-80 pointer-events-none opacity-20">
            <div className="spin-circle absolute inset-0 text-white">
                <svg viewBox="0 0 100 100" width="100%" height="100%">
                    <path id="circlePath" d="M 50, 50 m -40, 0 a 40,40 0 1,1 80,0 a 40,40 0 1,1 -80,0" fill="transparent" />
                    <text fontSize="8.5" letterSpacing="3.5" fill="currentColor">
                    <textPath href="#circlePath" startOffset="0%">
                        AUTOMATION THAT ACTUALLY WORKS •
                    </textPath>
                    </text>
                </svg>
            </div>
        </div>

      </div>

      {/* Right Panel - Form Area */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 relative bg-[#fbfbf2]">
        
        {/* Mobile Header (Only visible on small screens) */}
        <header className="absolute top-0 left-0 w-full flex justify-between items-center px-6 py-6 lg:hidden">
            <div className="font-serif text-2xl font-bold tracking-tight text-[#1c1c1e] flex items-center gap-2 cursor-pointer" onClick={() => setLocation("/")}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#1c1c1e]">
                <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
            Aina
            </div>
        </header>

        <div className="w-full max-w-[420px] mt-12 lg:mt-0">
          
          <div className="mb-10 auth-item">
            <h1 className="text-[2.5rem] font-serif font-bold text-[#1c1c1e] mb-3 tracking-tight leading-none" style={{ fontFamily: "'Playfair Display', serif" }}>
              Welcome <span className="italic">back</span>
            </h1>
            <p className="text-[#1c1c1e]/60 text-base font-medium">Please enter your details to sign in.</p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Email Field */}
            <div className="space-y-2.5 auth-item group">
              <label className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                Business Email
              </label>
              <div className="relative">
                <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full bg-white border border-black/10 focus:border-[#1c1c1e] hover:border-black/20 rounded-xl px-4 py-3.5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 outline-none transition-all text-[15px] font-medium shadow-sm"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-2.5 auth-item group">
              <div className="flex justify-between items-center">
                <label className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                  Password
                </label>
                <a
                  href="#"
                  className="text-[10px] font-bold text-[#1c1c1e]/40 hover:text-[#1c1c1e] transition-colors uppercase tracking-wider"
                >
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-white border border-black/10 focus:border-[#1c1c1e] hover:border-black/20 rounded-xl px-4 py-3.5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 outline-none transition-all text-[15px] font-medium tracking-widest shadow-sm"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-item w-full mt-2 bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-sm border border-[#1c1c1e]/5 hover:shadow-md text-[15px]"
            >
              Sign In
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>
            </button>

            {/* Divider */}
            <div className="flex items-center gap-4 py-4 auth-item text-[#1c1c1e]/10">
              <div className="h-[1px] flex-grow bg-currentColor"></div>
              <span className="text-[10px] uppercase tracking-widest text-[#1c1c1e]/40 font-bold">OR CONTINUE WITH</span>
              <div className="h-[1px] flex-grow bg-currentColor"></div>
            </div>

            {/* Social Login */}
            <div className="grid grid-cols-2 gap-3 auth-item">
              <button
                type="button"
                className="flex items-center justify-center gap-2 bg-white hover:bg-black/5 border border-black/10 py-3.5 rounded-xl transition-all text-[13px] font-bold text-[#1c1c1e] shadow-sm"
              >
                <div className="w-4 h-4 flex-shrink-0 bg-transparent rounded-sm flex items-center justify-center">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                  </svg>
                </div>
                Google
              </button>
              <button
                type="button"
                className="flex items-center justify-center gap-2 bg-white hover:bg-black/5 border border-black/10 py-3.5 rounded-xl transition-all text-[13px] font-bold text-[#1c1c1e] shadow-sm"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[#1c1c1e]/70"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
                SAML
              </button>
            </div>
          </form>

          {/* Context Switch Link */}
          <div className="mt-10 text-center auth-item">
            <p className="text-[14px] font-medium text-[#1c1c1e]/50">
              Don't have an account?{" "}
              <button
                onClick={() => setLocation("/signup")}
                className="font-bold text-[#1c1c1e] hover:text-[#1c1c1e]/70 transition-colors underline decoration-2 underline-offset-4 decoration-[#EBDCFF]"
              >
                Sign Up
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
