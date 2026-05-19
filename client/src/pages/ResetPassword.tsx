import { useLocation } from "wouter";
import { useState, useRef, useEffect } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP);

export default function ResetPassword() {
  const [, setLocation] = useLocation();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [confirmError, setConfirmError] = useState("");
  const [apiError, setApiError] = useState("");
  
  const container = useRef<HTMLDivElement>(null);

  // Extract reset token from query string
  const [token, setToken] = useState("");
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tokenVal = params.get("token") || "";
    setToken(tokenVal);
    if (!tokenVal) {
      setApiError("Authentication token is missing. Please request a new password reset link.");
    }
  }, []);

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

  const validatePassword = (val: string) => {
    if (!val) {
      setPasswordError("Password is required");
      return false;
    }
    if (val.length < 6) {
      setPasswordError("Password must be at least 6 characters long");
      return false;
    }
    setPasswordError("");
    return true;
  };

  const validateConfirm = (val: string) => {
    if (!val) {
      setConfirmError("Please confirm your password");
      return false;
    }
    if (val !== password) {
      setConfirmError("Passwords do not match");
      return false;
    }
    setConfirmError("");
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError("");
    
    const isPasswordValid = validatePassword(password);
    const isConfirmValid = validateConfirm(confirmPassword);

    if (!isPasswordValid || !isConfirmValid || !token) {
      // Premium error shake feedback
      gsap.to(".auth-form-card", {
        x: -8,
        duration: 0.06,
        repeat: 5,
        yoyo: true,
        ease: "power1.inOut",
        onComplete: () => {
          gsap.set(".auth-form-card", { clearProps: "x" });
        }
      });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/reset-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ 
          token,
          new_password: password 
        })
      });

      if (!response.ok) {
        let errMsg = "An error occurred while resetting your password.";
        try {
          const errData = await response.json();
          errMsg = errData.detail || errMsg;
        } catch {
          if (response.status === 503) {
            errMsg = "Database service is offline. Please check connection.";
          }
        }
        throw new Error(errMsg);
      }

      setSuccess(true);
      // Stagger fade-in of success screen elements
      setTimeout(() => {
        gsap.from(".success-item", {
          y: 15,
          opacity: 0,
          duration: 0.5,
          stagger: 0.08,
          ease: "power2.out"
        });
      }, 50);
    } catch (err: any) {
      setApiError(err.message || "Failed to connect to the backend server.");
      // Shake the card on API error
      gsap.to(".auth-form-card", {
        x: -8,
        duration: 0.06,
        repeat: 5,
        yoyo: true,
        ease: "power1.inOut",
        onComplete: () => {
          gsap.set(".auth-form-card", { clearProps: "x" });
        }
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div ref={container} className="min-h-screen bg-white text-[#1c1c1e] font-sans flex relative selection:bg-[#EBDCFF] selection:text-[#1c1c1e]">
      
      {/* Left Panel - Visual Appeal Area (Hidden on Mobile) */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 relative overflow-hidden bg-[#1c1c1e] text-[#F5F5F7]">
        
        {/* Background ambient light */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#EBDCFF] rounded-full mix-blend-overlay opacity-5 blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-white rounded-full mix-blend-overlay opacity-5 blur-3xl"></div>

        {/* Logo */}
        <div 
          className="brand-element font-serif text-3xl font-bold tracking-tight text-[#F5F5F7] flex items-center gap-3 cursor-pointer z-10 hover:opacity-90 transition-opacity" 
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
           <h2 className="brand-element font-serif text-[4rem] leading-[1.05] tracking-tight mb-8" style={{ fontFamily: "'Playfair Display', serif" }}>
              Secure <br/><span className="italic text-[#EBDCFF]">credentials.</span>
           </h2>
           <p className="brand-element text-white/60 text-xl max-w-md leading-relaxed">
             Establish your new administrative password key below to seamlessly re-encrypt and claim authority over your dashboard environment.
           </p>
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
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 relative bg-[#F5F5F7]">
        
        {/* Mobile Header (Only visible on small screens) */}
        <header className="absolute top-0 left-0 w-full flex justify-between items-center px-6 py-6 lg:hidden">
            <div className="font-serif text-2xl font-bold tracking-tight text-[#1c1c1e] flex items-center gap-2 cursor-pointer" onClick={() => setLocation("/")}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#1c1c1e]">
                <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
            Aina
            </div>
        </header>

        <div className="auth-form-card w-full max-w-[420px] mt-12 lg:mt-0">
          
          {!success ? (
            <>
              <div className="mb-10 auth-item">
                <h1 className="text-[2.5rem] font-serif font-bold text-[#1c1c1e] mb-3 tracking-tight leading-none" style={{ fontFamily: "'Playfair Display', serif" }}>
                  Reset your <span className="italic">password</span>
                </h1>
                <p className="text-[#1c1c1e]/60 text-base font-medium">Please enter your new password below.</p>
              </div>

              {apiError && (
                <div className="bg-[#ea4335]/10 text-[#ea4335] border border-[#ea4335]/20 p-4 rounded-xl text-xs font-semibold flex items-start gap-2 mb-6 animate-fadeIn">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="mt-0.5 flex-shrink-0"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                  <span>{apiError}</span>
                </div>
              )}

              <form className="space-y-6" onSubmit={handleSubmit} noValidate>
                {/* Password Field */}
                <div className="space-y-2.5 auth-item group">
                  <label htmlFor="password-input" className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                    New Password
                  </label>
                  <div className="relative">
                    <input
                      id="password-input"
                      type="password"
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        if (passwordError) validatePassword(e.target.value);
                      }}
                      onBlur={() => validatePassword(password)}
                      placeholder="••••••••"
                      aria-invalid={!!passwordError}
                      className={`w-full bg-white border ${
                        passwordError ? "border-[#ea4335] focus:border-[#ea4335] focus:ring-red-100" : "border-black/10 focus:border-[#1c1c1e] focus:ring-[#EBDCFF]/50"
                      } hover:border-black/20 rounded-xl px-4 py-3.5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 outline-none transition-all text-[15px] font-medium shadow-sm focus:ring-4`}
                    />
                  </div>
                  {passwordError && (
                    <p className="text-xs text-[#ea4335] font-semibold flex items-center gap-1.5 animate-fadeIn">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                      {passwordError}
                    </p>
                  )}
                </div>

                {/* Confirm Password Field */}
                <div className="space-y-2.5 auth-item group">
                  <label htmlFor="confirm-input" className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <input
                      id="confirm-input"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => {
                        setConfirmPassword(e.target.value);
                        if (confirmError) validateConfirm(e.target.value);
                      }}
                      onBlur={() => validateConfirm(confirmPassword)}
                      placeholder="••••••••"
                      aria-invalid={!!confirmError}
                      className={`w-full bg-white border ${
                        confirmError ? "border-[#ea4335] focus:border-[#ea4335] focus:ring-red-100" : "border-black/10 focus:border-[#1c1c1e] focus:ring-[#EBDCFF]/50"
                      } hover:border-black/20 rounded-xl px-4 py-3.5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 outline-none transition-all text-[15px] font-medium shadow-sm focus:ring-4`}
                    />
                  </div>
                  {confirmError && (
                    <p className="text-xs text-[#ea4335] font-semibold flex items-center gap-1.5 animate-fadeIn">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                      {confirmError}
                    </p>
                  )}
                </div>

                {/* Submit Button */}
                <div className="auth-item w-full mt-2">
                  <button
                    type="submit"
                    disabled={loading || !token}
                    className="w-full bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-sm border border-[#1c1c1e]/5 hover:shadow-md hover:scale-[1.01] active:scale-[0.99] text-[15px] cursor-pointer disabled:opacity-50 disabled:pointer-events-none"
                  >
                    {loading ? (
                      <div className="flex items-center gap-2">
                        <svg className="animate-spin h-5 w-5 text-[#1c1c1e]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Resetting...</span>
                      </div>
                    ) : (
                      <>
                        Update Password
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* Context Switch Link */}
              <div className="mt-8 text-center auth-item">
                <button
                  onClick={() => setLocation("/login")}
                  className="font-bold text-[14px] text-[#1c1c1e] hover:text-[#1c1c1e]/70 transition-colors flex items-center justify-center gap-2 mx-auto cursor-pointer focus:outline-none focus:underline"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                  Back to Sign In
                </button>
              </div>
            </>
          ) : (
            <div className="text-center">
              {/* Success Badge */}
              <div className="success-item w-16 h-16 bg-[#eafaf1] text-[#34a853] rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-sm border border-[#34a853]/10">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>

              <h1 className="success-item text-[2.5rem] font-serif font-bold text-[#1c1c1e] mb-3 tracking-tight leading-none" style={{ fontFamily: "'Playfair Display', serif" }}>
                Success!
              </h1>
              
              <p className="success-item text-[#1c1c1e]/60 text-base font-medium mb-8 leading-relaxed">
                Your credentials have been securely updated. You can now use your new password to access your administrative dashboard.
              </p>

              <div className="success-item w-full">
                <button
                  onClick={() => setLocation("/login")}
                  className="w-full bg-[#1c1c1e] hover:bg-black text-[#F5F5F7] py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-sm hover:scale-[1.01] active:scale-[0.99] text-[15px] cursor-pointer"
                >
                  Sign In with New Password
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
