import { useLocation } from "wouter";
import { useState } from "react";
import { Button } from "../components/ui/button";
import AuthLayout from "../layouts/AuthLayout";
import { apiRequest } from "../lib/api";

export default function ForgotPassword() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [apiError, setApiError] = useState("");
  const [isShaking, setIsShaking] = useState(false);

  const triggerShake = () => {
    setIsShaking(true);
    setTimeout(() => setIsShaking(false), 400);
  };

  const validateEmail = (val: string) => {
    if (!val.trim()) {
      setEmailError("Email is required");
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(val)) {
      setEmailError("Please enter a valid email address");
      return false;
    }
    setEmailError("");
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError("");
    
    const isEmailValid = validateEmail(email);

    if (!isEmailValid) {
      triggerShake();
      return;
    }

    setLoading(true);
    try {
      await apiRequest("POST", "/auth/forgot-password", { email });
      setSuccess(true);
    } catch (err: any) {
      setApiError(err.message || "Failed to connect to the backend server.");
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title={<>Lost your <br/><span className="italic text-[#EBDCFF]">credentials?</span></>}
      subtitle="No worries. Provide your registered business email address, and we'll transmit a secure access key to restore your dashboard profile immediately."
      showSpinCircle={true}
    >
      <div className={`auth-form-card w-full max-w-[420px] mt-12 lg:mt-0 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300 fill-mode-both ${isShaking ? 'animate-[shake_0.4s_ease-in-out]' : ''}`}>
        
        {!success ? (
          <>
            <div className="mb-10 animate-in fade-in slide-in-from-bottom-2 duration-500 delay-400 fill-mode-both">
              <h1 className="text-[2.5rem] font-serif font-bold text-[#1c1c1e] mb-3 tracking-tight leading-none" style={{ fontFamily: "'Playfair Display', serif" }}>
                Reset your <span className="italic">password</span>
              </h1>
              <p className="text-[#1c1c1e]/60 text-base font-medium">We'll send you instructions to reset your password.</p>
            </div>

            {apiError && (
              <div className="bg-[#ea4335]/10 text-[#ea4335] border border-[#ea4335]/20 p-4 rounded-xl text-xs font-semibold flex items-start gap-2 mb-6 animate-fadeIn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="mt-0.5 flex-shrink-0"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <span>{apiError}</span>
              </div>
            )}

            <form className="space-y-6" onSubmit={handleSubmit} noValidate>
              {/* Email Field */}
              <div className="space-y-2.5 group animate-in fade-in slide-in-from-bottom-2 duration-500 delay-[450ms] fill-mode-both">
                <label htmlFor="email-input" className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                  Business Email
                </label>
                <div className="relative">
                  <input
                    id="email-input"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (emailError) validateEmail(e.target.value);
                    }}
                    onBlur={() => validateEmail(email)}
                    placeholder="ahmed@company.pk"
                    aria-invalid={!!emailError}
                    aria-describedby={emailError ? "email-error" : undefined}
                    className={`w-full bg-white border ${
                      emailError ? "border-[#ea4335] focus:border-[#ea4335] focus:ring-red-100" : "border-black/10 focus:border-[#1c1c1e] focus:ring-[#EBDCFF]/50"
                    } hover:border-black/20 rounded-xl px-4 py-3.5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 outline-none transition-all text-[15px] font-medium shadow-sm focus:ring-4`}
                  />
                </div>
                {emailError && (
                  <p id="email-error" className="text-xs text-[#ea4335] font-semibold flex items-center gap-1.5 animate-fadeIn">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    {emailError}
                  </p>
                )}
              </div>

              {/* Submit Button */}
              <div className="w-full mt-2 animate-in fade-in slide-in-from-bottom-2 duration-500 delay-[500ms] fill-mode-both">
                <Button
                  type="submit"
                  loading={loading}
                  className="w-full bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] py-4 h-auto rounded-xl font-bold flex items-center justify-center gap-2 border border-[#1c1c1e]/5 text-[15px] hover:shadow-md hover:scale-[1.01] active:scale-[0.99]"
                >
                  {loading ? "Transmitting key…" : "Send Reset Link"}
                </Button>
              </div>
            </form>

            {/* Context Switch Link */}
            <div className="mt-8 text-center animate-in fade-in slide-in-from-bottom-2 duration-500 delay-[550ms] fill-mode-both">
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
            <div className="w-16 h-16 bg-[#eafaf1] text-[#34a853] rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-sm border border-[#34a853]/10 animate-in zoom-in duration-500 delay-100">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>

            <h1 className="text-[2.5rem] font-serif font-bold text-[#1c1c1e] mb-3 tracking-tight leading-none animate-in fade-in slide-in-from-bottom-2 duration-500 delay-200 fill-mode-both" style={{ fontFamily: "'Playfair Display', serif" }}>
              Check your <span className="italic">inbox</span>
            </h1>
            
            <p className="text-[#1c1c1e]/60 text-base font-medium mb-8 leading-relaxed animate-in fade-in slide-in-from-bottom-2 duration-500 delay-300 fill-mode-both">
              We've sent a secure password reset link to <strong className="text-[#1c1c1e] font-semibold">{email}</strong>. Please follow the instructions in the email to configure your new credentials.
            </p>

            <div className="w-full animate-in fade-in slide-in-from-bottom-2 duration-500 delay-400 fill-mode-both">
              <button
                onClick={() => setLocation("/login")}
                className="w-full bg-[#1c1c1e] hover:bg-black text-[#F5F5F7] py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-sm hover:scale-[1.01] active:scale-[0.99] text-[15px] cursor-pointer"
              >
                Return to Sign In
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
              </button>
            </div>

            <div className="mt-6 text-xs text-[#1c1c1e]/40 font-medium animate-in fade-in slide-in-from-bottom-2 duration-500 delay-500 fill-mode-both">
              Didn't receive email? Check spam folder or try again in 2 minutes.
            </div>
          </div>
        )}
      </div>
    </AuthLayout>
  );
}
