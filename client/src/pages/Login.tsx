import { useLocation } from "wouter";
import { useState } from "react";
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from "../contexts/AuthContext";
import { Button } from "../components/ui/button";
import { toast } from "sonner";
import AuthLayout from "../layouts/AuthLayout";
import { apiRequest } from "../lib/api";

export default function Login() {
  const [, setLocation] = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  
  // Validation States
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [apiError, setApiError] = useState("");

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

  const validatePassword = (val: string) => {
    if (!val) {
      setPasswordError("Password is required");
      return false;
    }
    if (val.length < 6) {
      setPasswordError("Password must be at least 6 characters");
      return false;
    }
    setPasswordError("");
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError("");
    
    const isEmailValid = validateEmail(email);
    const isPasswordValid = validatePassword(password);

    if (!isEmailValid || !isPasswordValid) {
      triggerShake();
      return;
    }

    setLoading(true);
    try {
      const data = await apiRequest("POST", "/auth/login", { email, password });
      login(data.access_token);
      toast.success("Successfully logged in!");
      setLocation("/dashboard");
    } catch (err: any) {
      setApiError(err.message || "Failed to connect to the backend server.");
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true);
      setApiError("");
      try {
        const data = await apiRequest("POST", "/auth/google-login", { token: tokenResponse.access_token });
        login(data.access_token);
        toast.success("Successfully logged in with Google!");
        setLocation("/dashboard");
      } catch (err: any) {
        setApiError(err.message || "Failed to authenticate with Google.");
        triggerShake();
      } finally {
        setLoading(false);
      }
    },
    onError: () => {
      setApiError("Google Sign-In was unsuccessful. Please try again.");
    }
  });

  return (
    <AuthLayout
      title={<>Don't code, <br/><span className="italic text-[#EBDCFF]">just build</span>.</>}
      subtitle="Sign in to access your AI automations, deploy new flows, and manage customer interactions across all channels."
      showSpinCircle={true}
    >
      <div className={`auth-form-card w-full max-w-[420px] mt-12 lg:mt-0 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300 fill-mode-both ${isShaking ? 'animate-[shake_0.4s_ease-in-out]' : ''}`}>
        
        <div className="mb-10 animate-in fade-in slide-in-from-bottom-2 duration-500 delay-400 fill-mode-both">
          <h1 className="text-[2.5rem] font-serif font-bold text-[#1c1c1e] mb-3 tracking-tight leading-none" style={{ fontFamily: "'Playfair Display', serif" }}>
            Welcome <span className="italic">back</span>
          </h1>
          <p className="text-[#1c1c1e]/60 text-base font-medium">Please enter your details to sign in.</p>
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
                  placeholder="name@company.com"
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

          {/* Password Field */}
          <div className="space-y-2.5 group animate-in fade-in slide-in-from-bottom-2 duration-500 delay-[500ms] fill-mode-both">
            <div className="flex justify-between items-center">
              <label htmlFor="password-input" className="block text-[11px] font-bold text-[#1c1c1e]/50 uppercase tracking-widest group-focus-within:text-[#1c1c1e] transition-colors">
                Password
              </label>
              <button
                type="button"
                onClick={() => setLocation("/forgot-password")}
                className="text-[10px] font-bold text-[#1c1c1e]/40 hover:text-[#1c1c1e] transition-colors uppercase tracking-wider cursor-pointer focus:outline-none"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <input
                  id="password-input"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (passwordError) validatePassword(e.target.value);
                  }}
                  onBlur={() => validatePassword(password)}
                  placeholder="••••••••"
                  aria-invalid={!!passwordError}
                  aria-describedby={passwordError ? "password-error" : undefined}
                  className={`w-full bg-white border ${
                    passwordError ? "border-[#ea4335] focus:border-[#ea4335] focus:ring-red-100" : "border-black/10 focus:border-[#1c1c1e] focus:ring-[#EBDCFF]/50"
                  } hover:border-black/20 rounded-xl px-4 py-3.5 pr-12 text-[#1c1c1e] placeholder:text-[#1c1c1e]/30 outline-none transition-all text-[15px] font-medium shadow-sm focus:ring-4 ${
                    showPassword ? "" : "tracking-widest"
                  }`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#1c1c1e]/30 hover:text-[#1c1c1e] transition-colors focus:outline-none"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                )}
              </button>
            </div>
            {passwordError && (
              <p id="password-error" className="text-xs text-[#ea4335] font-semibold flex items-center gap-1.5 animate-fadeIn">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                {passwordError}
              </p>
            )}
          </div>

          {/* Submit Button */}
          <div className="w-full mt-2 animate-in fade-in slide-in-from-bottom-2 duration-500 delay-[550ms] fill-mode-both">
            <Button
              type="submit"
              loading={loading}
              className="w-full bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] py-4 h-auto rounded-xl font-bold flex items-center justify-center gap-2 border border-[#1c1c1e]/5 text-[15px] hover:shadow-md hover:scale-[1.01] active:scale-[0.99]"
            >
              {loading ? "Signing In..." : "Sign In"}
            </Button>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-4 py-4 text-[#1c1c1e]/10 animate-in fade-in slide-in-from-bottom-2 duration-500 delay-[600ms] fill-mode-both">
            <div className="h-[1px] flex-grow bg-currentColor"></div>
            <span className="text-[10px] uppercase tracking-widest text-[#1c1c1e]/40 font-bold">OR CONTINUE WITH</span>
            <div className="h-[1px] flex-grow bg-currentColor"></div>
          </div>

          {/* Social Login */}
          <div className="w-full animate-in fade-in slide-in-from-bottom-2 duration-500 delay-[650ms] fill-mode-both">
            <button
              type="button"
              onClick={() => loginWithGoogle()}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-white hover:bg-black/5 border border-black/10 py-3.5 rounded-xl transition-all text-[13px] font-bold text-[#1c1c1e] shadow-sm hover:scale-[1.01] active:scale-[0.99] cursor-pointer disabled:opacity-75 disabled:pointer-events-none"
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
          </div>
        </form>

        {/* Context Switch Link */}
        <div className="mt-10 text-center animate-in fade-in slide-in-from-bottom-2 duration-500 delay-[700ms] fill-mode-both">
          <p className="text-[14px] font-medium text-[#1c1c1e]/50">
            Don't have an account?{" "}
            <button
              onClick={() => setLocation("/signup")}
              className="font-bold text-[#1c1c1e] hover:text-[#1c1c1e]/70 transition-colors underline decoration-2 underline-offset-4 decoration-[#EBDCFF] focus:outline-none focus:ring-2 focus:ring-[#EBDCFF] rounded-md px-1"
            >
              Sign Up
            </button>
          </p>
        </div>
      </div>
    </AuthLayout>
  );
}
