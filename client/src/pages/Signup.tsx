import { useLocation } from "wouter";
import { useState, useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP);

export default function Signup() {
  const [, setLocation] = useLocation();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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

    gsap.to(".float-icon", {
      y: -15,
      duration: 2.5,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
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
    // Mock registration
    setLocation("/dashboard");
  };

  const getPasswordStrength = () => {
    if (password.length === 0) return 0;
    if (password.length < 4) return 1;
    if (password.length < 8) return 2;
    if (password.length < 12) return 3;
    return 4;
  };

  const strength = getPasswordStrength();

  return (
    <div ref={container} className="min-h-screen bg-white text-[#1c1c1e] font-sans flex relative selection:bg-[#EBDCFF] selection:text-[#1c1c1e]">
      
      {/* Left Panel - Visual Appeal Area (Hidden on Mobile) */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 relative overflow-hidden bg-[#1c1c1e] text-[#fbfbf2]">
        
        {/* Background ambient light */}
        <div className="absolute top-0 left-0 w-[600px] h-[600px] bg-[#EBDCFF] rounded-full mix-blend-overlay opacity-10 blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-white rounded-full mix-blend-overlay opacity-5 blur-3xl"></div>

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
            <div className="brand-element mb-12">
                <div className="float-icon w-20 h-20 bg-[#EBDCFF] rounded-2xl flex items-center justify-center shadow-2xl z-20 pointer-events-auto">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1c1c1e" strokeWidth="1.5">
                        <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"></path>
                        <path d="M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0 -8"></path>
                        <path d="M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0 -16"></path>
                    </svg>
                </div>
            </div>

           <h2 className="brand-element font-serif text-[4.5rem] leading-[1.05] tracking-tight mb-8" style={{ fontFamily: "'Playfair Display', serif" }}>
              Empower your <br/><span className="italic text-[#EBDCFF]">business</span>
           </h2>
           <p className="brand-element text-white/60 text-xl max-w-md leading-relaxed">
             Join 500+ top enterprises that use Aina to deploy flawless, real-time AI automations in seconds.
           </p>

           <div className="brand-element mt-16 flex flex-wrap gap-3">
                {['WhatsApp', 'Messenger', 'Web Widget', 'REST API', 'iOS'].map((platform) => (
                  <div key={platform} className="px-5 py-2.5 rounded-full border border-white/20 text-sm font-semibold flex items-center gap-2 bg-white/5 backdrop-blur-sm shadow-sm text-white">
                    <div className="w-2.5 h-2.5 rounded-full bg-white"></div>
                    {platform}
                  </div>
                ))}
           </div>
        </div>

      </div>

      {/* Right Panel - Form Area */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 relative bg-[#fbfbf2] overflow-y-auto">
        
        {/* Mobile Header (Only visible on small screens) */}
        <header className="absolute top-0 left-0 w-full flex justify-between items-center px-6 py-6 lg:hidden">
            <div className="font-serif text-2xl font-bold tracking-tight text-[#1c1c1e] flex items-center gap-2 cursor-pointer" onClick={() => setLocation("/")}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#1c1c1e]">
                <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
            Aina
            </div>
        </header>

        <div className="w-full max-w-[420px] my-auto mt-20 lg:mt-auto">
          
          <div className="mb-8 auth-item">
            <h1 className="text-[2.5rem] font-serif font-bold text-[#1c1c1e] mb-2 tracking-tight leading-none" style={{ fontFamily: "'Playfair Display', serif" }}>
              Get <span className="italic">started</span>
            </h1>
            <p className="text-[#1c1c1e]/60 text-[15px] font-medium">Create your business account setup.</p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* Name Field */}
            <div className="space-y-2 auth-item group">
              <label className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Ahmed Khan"
                className="w-full bg-white border border-black/10 focus:border-[#1c1c1e] hover:border-black/20 rounded-xl px-4 py-3.5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 outline-none transition-all text-[15px] font-medium shadow-sm"
              />
            </div>

            {/* Email Field */}
            <div className="space-y-2 auth-item group">
              <label className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                Business Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ahmed@company.pk"
                className="w-full bg-white border border-black/10 focus:border-[#1c1c1e] hover:border-black/20 rounded-xl px-4 py-3.5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 outline-none transition-all text-[15px] font-medium shadow-sm"
              />
            </div>

            {/* Password Field */}
            <div className="space-y-2 auth-item group">
              <label className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                Password
              </label>
              <div className="relative">
                <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-white border border-black/10 focus:border-[#1c1c1e] hover:border-black/20 rounded-xl px-4 py-3.5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 pr-12 outline-none transition-all text-[15px] tracking-widest font-mono shadow-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#1c1c1e]/30 hover:text-[#1c1c1e] transition-colors"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                </button>
              </div>

               {/* Password Strength Indicator */}
               <div className="pt-2">
                <div className="flex gap-1.5 mb-2 mt-1">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-all duration-500 block ${
                        password.length === 0 ? "bg-black/5" :
                        strength >= i ? (strength === 4 ? "bg-[#1c1c1e]" : "bg-[#1c1c1e]/40") : "bg-black/5"
                      }`}
                    ></div>
                  ))}
                </div>
                <div className="text-[10px] uppercase tracking-widest font-bold text-[#1c1c1e]/40">
                  STRENGTH: <span className={strength === 4 ? "text-[#1c1c1e]" : ""}>
                    {strength === 0 ? "NONE" : strength === 1 ? "WEAK" : strength === 2 ? "FAIR" : strength === 3 ? "GOOD" : "SECURE"}
                  </span>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-item w-full mt-4 bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-sm border border-[#1c1c1e]/5 hover:shadow-md text-[15px]"
            >
              Configure Setup
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
            </button>

            {/* Divider */}
            <div className="flex items-center gap-4 py-4 auth-item text-[#1c1c1e]/10">
              <div className="h-[1px] flex-grow bg-currentColor"></div>
              <span className="text-[10px] uppercase tracking-widest text-[#1c1c1e]/40 font-bold">OR CONTINUE WITH</span>
              <div className="h-[1px] flex-grow bg-currentColor"></div>
            </div>

            {/* Social Login */}
            <button
                type="button"
                className="auth-item w-full flex items-center justify-center gap-2 bg-white hover:bg-black/5 border border-black/10 py-3.5 rounded-xl transition-all text-[13px] font-bold text-[#1c1c1e] shadow-sm"
              >
                <div className="w-4 h-4 flex-shrink-0 bg-transparent rounded-sm flex items-center justify-center">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                  </svg>
                </div>
                Sign up with Google
              </button>
          </form>

          {/* Context Switch Link */}
          <div className="mt-8 text-center pt-2 auth-item">
            <p className="text-[14px] font-medium text-[#1c1c1e]/50">
              Already have an account?{" "}
              <button
                onClick={() => setLocation("/login")}
                className="font-bold text-[#1c1c1e] hover:text-[#1c1c1e]/70 transition-colors underline decoration-2 underline-offset-4 decoration-[#EBDCFF]"
              >
                Log In
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
