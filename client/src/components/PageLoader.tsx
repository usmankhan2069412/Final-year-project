import { useTheme } from "../contexts/ThemeContext";

interface PageLoaderProps {
  page?: "dashboard" | "inbox" | "builder" | "settings" | "models" | "analytics" | "public" | "home" | "login" | "signup";
  contentOnly?: boolean;
}

export default function PageLoader({ page = "dashboard", contentOnly = false }: PageLoaderProps) {
  const { isDark } = useTheme();

  // Dynamic light/dark theme color helper
  const c = (light: string, dark: string) => (isDark ? dark : light);

  // ── Home/Landing Page Skeleton ──
  if (page === "home") {
    return (
      <div
        className="min-h-screen bg-[#F5F5F7] text-[#1c1c1e] font-sans overflow-x-hidden transition-colors duration-300 relative"
      >
        {/* Navigation Skeleton */}
        <nav className="fixed top-0 w-full z-50 bg-[#F5F5F7]/80 backdrop-blur-md">
          <div className="flex justify-between items-center w-full px-6 py-4 max-w-[1400px] mx-auto">
            <div className="flex items-center gap-2 animate-pulse">
              <div className="w-10 h-10 bg-black/10 rounded-xl" />
              <div className="w-16 h-6 bg-black/10 rounded-lg" />
            </div>
            
            <div className="hidden md:flex gap-8 items-center bg-white/50 backdrop-blur-lg px-8 py-3 rounded-full border border-black/5 shadow-sm">
              <div className="w-16 h-4 bg-black/5 rounded" />
              <div className="w-20 h-4 bg-black/5 rounded" />
              <div className="w-16 h-4 bg-black/5 rounded" />
              <div className="w-20 h-4 bg-black/5 rounded" />
            </div>

            <div className="flex gap-4 items-center animate-pulse">
              <div className="w-16 h-9 rounded-full bg-black/5" />
              <div className="w-32 h-9 rounded-full bg-[#EBDCFF]" />
            </div>
          </div>
        </nav>

        {/* Hero Section Skeleton */}
        <main className="pt-32 pb-10">
          <section className="relative pt-16 pb-24 px-6 md:px-12 animate-pulse">
            <div className="max-w-[1200px] mx-auto text-center relative">
              {/* Rotating badge outline */}
              <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 lg:-translate-x-12 hidden md:flex items-center justify-center w-64 h-64">
                <div className="w-64 h-64 rounded-full border border-dashed border-black/10" />
              </div>

              {/* Huge heading */}
              <div className="space-y-4 mb-8">
                <div className="h-16 md:h-24 w-80 sm:w-2/3 md:w-[680px] mx-auto rounded-2xl bg-black/10" />
                <div className="h-16 md:h-24 w-60 sm:w-1/2 md:w-[480px] mx-auto rounded-2xl bg-[#EBDCFF]" />
              </div>
              
              {/* Description */}
              <div className="space-y-2.5 mb-12">
                <div className="h-5 w-4/5 sm:w-2/3 md:w-[600px] mx-auto rounded-lg bg-black/5" />
                <div className="h-5 w-3/5 sm:w-1/2 md:w-[450px] mx-auto rounded-lg bg-black/5" />
              </div>
              
              {/* CTA button */}
              <div className="h-14 w-44 mx-auto rounded-xl bg-[#EBDCFF] border border-black/10 shadow-sm" />
              
              {/* Info text */}
              <div className="h-4 w-72 mx-auto rounded bg-black/5 mt-6" />
            </div>
          </section>
        </main>
      </div>
    );
  }

  // ── Login Split Screen Page Skeleton ──
  if (page === "login") {
    return (
      <div className="min-h-screen bg-white text-[#1c1c1e] font-sans flex relative overflow-hidden">
        {/* Left Panel */}
        <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-[#1c1c1e] text-[#F5F5F7] relative overflow-hidden animate-pulse">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#EBDCFF] rounded-full mix-blend-overlay opacity-5 blur-3xl" />
          
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#EBDCFF]/30 rounded-xl" />
            <div className="w-16 h-6 bg-white/10 rounded-lg" />
          </div>

          {/* Graphics Text */}
          <div className="space-y-4 my-12">
            <div className="h-12 w-64 rounded-xl bg-white/10" />
            <div className="h-12 w-48 rounded-xl bg-[#EBDCFF]/30" />
            <div className="space-y-2 pt-4">
              <div className="h-4.5 w-80 rounded-lg bg-white/5" />
              <div className="h-4.5 w-64 rounded-lg bg-white/5" />
            </div>
          </div>

          {/* Bottom spacer */}
          <div className="w-12 h-1 bg-white/10 rounded-full" />
        </div>

        {/* Right Panel */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 bg-[#F5F5F7] animate-pulse">
          <div className="w-full max-w-[420px] space-y-8">
            <div className="space-y-3">
              <div className="h-10 w-44 rounded-xl bg-black/10" />
              <div className="h-5 w-64 rounded-lg bg-black/5" />
            </div>

            <div className="space-y-6">
              {/* Email */}
              <div className="space-y-2">
                <div className="h-3.5 w-24 rounded bg-black/5" />
                <div className="h-12 w-full rounded-xl bg-white border border-black/5 shadow-sm" />
              </div>

              {/* Password */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <div className="h-3.5 w-20 rounded bg-black/5" />
                  <div className="h-3 w-28 rounded bg-black/5" />
                </div>
                <div className="h-12 w-full rounded-xl bg-white border border-black/5 shadow-sm" />
              </div>

              {/* Button */}
              <div className="h-12 w-full rounded-xl bg-[#EBDCFF] border border-black/5 shadow-sm" />
              
              {/* Divider */}
              <div className="flex items-center gap-3">
                <div className="h-[1px] flex-1 bg-black/5" />
                <div className="h-3.5 w-32 rounded bg-black/5" />
                <div className="h-[1px] flex-1 bg-black/5" />
              </div>

              {/* Google Button */}
              <div className="h-12 w-full rounded-xl bg-white border border-black/10 shadow-sm" />
            </div>

            <div className="h-4 w-48 mx-auto rounded bg-black/5 mt-10" />
          </div>
        </div>
      </div>
    );
  }

  // ── Signup Split Screen Page Skeleton ──
  if (page === "signup") {
    return (
      <div className="min-h-screen bg-white text-[#1c1c1e] font-sans flex relative overflow-hidden">
        {/* Left Panel */}
        <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-[#1c1c1e] text-[#F5F5F7] relative overflow-hidden animate-pulse">
          <div className="absolute top-0 left-0 w-[600px] h-[600px] bg-[#EBDCFF] rounded-full mix-blend-overlay opacity-10 blur-3xl" />
          
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#EBDCFF]/30 rounded-xl" />
            <div className="w-16 h-6 bg-white/10 rounded-lg" />
          </div>

          {/* Graphics Text */}
          <div className="space-y-4 my-12">
            <div className="h-12 w-64 rounded-xl bg-white/10" />
            <div className="h-12 w-48 rounded-xl bg-[#EBDCFF]/30" />
            <div className="space-y-2 pt-4">
              <div className="h-4.5 w-80 rounded-lg bg-white/5" />
              <div className="h-4.5 w-64 rounded-lg bg-white/5" />
            </div>
            
            {/* Tag bubbles */}
            <div className="flex flex-wrap gap-2.5 pt-6">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-9 w-24 rounded-full bg-white/5 border border-white/10" />
              ))}
            </div>
          </div>

          {/* Bottom spacer */}
          <div className="w-12 h-1 bg-white/10 rounded-full" />
        </div>

        {/* Right Panel */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 bg-[#F5F5F7] animate-pulse">
          <div className="w-full max-w-[420px] space-y-6">
            <div className="space-y-3">
              <div className="h-10 w-44 rounded-xl bg-black/10" />
              <div className="h-5 w-60 rounded-lg bg-black/5" />
            </div>

            <div className="space-y-5">
              {/* Name */}
              <div className="space-y-2">
                <div className="h-3.5 w-20 rounded bg-black/5" />
                <div className="h-12 w-full rounded-xl bg-white border border-black/5 shadow-sm" />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <div className="h-3.5 w-24 rounded bg-black/5" />
                <div className="h-12 w-full rounded-xl bg-white border border-black/5 shadow-sm" />
              </div>

              {/* Password */}
              <div className="space-y-2">
                <div className="h-3.5 w-20 rounded bg-black/5" />
                <div className="h-12 w-full rounded-xl bg-white border border-black/5 shadow-sm" />
                <div className="flex gap-1.5 pt-1.5">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-1.5 flex-1 rounded-full bg-black/5" />
                  ))}
                </div>
                <div className="h-3 w-24 rounded bg-black/5 mt-1" />
              </div>

              {/* Button */}
              <div className="h-12 w-full rounded-xl bg-[#EBDCFF] border border-black/5 shadow-sm" />
              
              {/* Divider */}
              <div className="flex items-center gap-3">
                <div className="h-[1px] flex-1 bg-black/5" />
                <div className="h-3.5 w-32 rounded bg-black/5" />
                <div className="h-[1px] flex-1 bg-black/5" />
              </div>

              {/* Google Button */}
              <div className="h-12 w-full rounded-xl bg-white border border-black/10 shadow-sm" />
            </div>

            <div className="h-4.5 w-52 mx-auto rounded bg-black/5 mt-8" />
          </div>
        </div>
      </div>
    );
  }

  // ── Public Pages Skeleton (Auth flow fallback: reset password etc.) ──
  if (page === "public") {
    return (
      <div
        className={`min-h-screen flex items-center justify-center font-sans transition-colors duration-300 relative overflow-hidden ${c(
          "bg-[#F5F5F7] text-[#1c1c1e]",
          "bg-[#131317] text-[#e4e1e7]"
        )}`}
      >
        <div
          className={`absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${c(
            "bg-[#EBDCFF] opacity-10 mix-blend-multiply",
            "bg-[#EBDCFF] opacity-5 mix-blend-screen"
          )}`}
        ></div>
        
        <div
          className={`w-full max-w-md p-8 rounded-[2rem] border animate-pulse space-y-6 ${c(
            "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
            "bg-[#1f1f23] border-white/[0.06]"
          )}`}
        >
          {/* Logo placeholder */}
          <div className={`w-16 h-16 mx-auto rounded-2xl ${c("bg-black/5", "bg-white/5")}`} />
          
          {/* Title & subtitle */}
          <div className="space-y-3 text-center">
            <div className={`h-6.5 w-36 mx-auto rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`h-4 w-56 mx-auto rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
          </div>
          
          {/* Input fields */}
          <div className="space-y-4 pt-2">
            <div className="space-y-2">
              <div className={`h-3 w-16 rounded ${c("bg-black/5", "bg-white/5")}`} />
              <div className={`h-12 w-full rounded-2xl ${c("bg-black/5", "bg-white/5")}`} />
            </div>
            <div className="space-y-2">
              <div className={`h-3 w-16 rounded ${c("bg-black/5", "bg-white/5")}`} />
              <div className={`h-12 w-full rounded-2xl ${c("bg-black/5", "bg-white/5")}`} />
            </div>
          </div>
          
          {/* Button */}
          <div className={`h-12 w-full rounded-2xl pt-2 ${c("bg-black/10", "bg-white/10")}`} />
        </div>
      </div>
    );
  }

  // ── Helper to render inner content skeletons ──
  const renderContentSkeleton = () => (
    <>
      {/* A. DASHBOARD / ANALYTICS LAYOUT */}
      {(page === "dashboard" || page === "analytics") && (
        <>
          <div className="space-y-3">
            <div className={`h-12 w-1/3 rounded-2xl animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`h-6 w-1/2 rounded-xl animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 md:gap-6 mb-8 md:mb-12">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className={`rounded-[20px] md:rounded-3xl border p-5 md:p-6 relative overflow-hidden animate-pulse min-h-[120px] ${
                  i === 1 ? "col-span-2 lg:col-span-1" : "col-span-1"
                } ${c(
                  "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
                  "bg-[#1f1f23] border-white/[0.06]"
                )}`}
              >
                <div className="flex justify-between items-start mb-6">
                  <div className={`w-10 h-10 md:w-12 md:h-12 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`w-12 h-6 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
                </div>
                <div className={`w-2/3 h-3 rounded-full mb-3 ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`w-1/2 h-8 rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
              </div>
            ))}
          </div>

          <div
            className={`rounded-[2rem] border overflow-hidden p-6 space-y-6 animate-pulse ${c(
              "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
              "bg-[#1f1f23] border-white/[0.06]"
            )}`}
          >
            <div className={`flex justify-between items-center pb-4 border-b ${c("border-black/5", "border-white/5")}`}>
              <div className="space-y-2">
                <div className={`h-6 w-48 rounded ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-4.5 w-80 rounded ${c("bg-black/5", "bg-white/5")}`} />
              </div>
              <div className={`h-9 w-32 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
            </div>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-4 py-2">
                  <div className={`w-12 h-12 rounded-2xl ${c("bg-black/5", "bg-white/5")}`} />
                  <div className="flex-1 space-y-2">
                    <div className={`h-4 w-40 rounded ${c("bg-black/5", "bg-white/5")}`} />
                    <div className={`h-3 w-28 rounded ${c("bg-black/5", "bg-white/5")}`} />
                  </div>
                  <div className={`w-20 h-6 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`w-32 h-4 rounded ${c("bg-black/5", "bg-white/5")}`} />
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* B. INBOX LAYOUT */}
      {page === "inbox" && (
        <div
          className={`flex rounded-[2rem] border h-[calc(100vh-8rem)] overflow-hidden ${c(
            "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
            "bg-[#1f1f23] border-white/[0.06]"
          )}`}
        >
          {/* Left sidebar chats pane */}
          <div className={`w-80 lg:w-96 flex flex-col border-r p-4 space-y-4 ${c("border-black/5", "border-white/5")}`}>
            <div className={`h-10 w-full rounded-xl animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`h-8 w-full rounded-lg animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
            <div className="flex-1 space-y-2 overflow-hidden">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className={`p-4 rounded-2xl border flex items-start gap-3.5 animate-pulse ${c(
                    "border-black/5 bg-[#F5F5F7]/50",
                    "border-white/[0.04] bg-[#131317]/40"
                  )}`}
                >
                  <div className={`w-10 h-10 rounded-xl flex-shrink-0 ${c("bg-black/5", "bg-white/5")}`} />
                  <div className="flex-1 space-y-2 min-w-0">
                    <div className="flex justify-between items-center">
                      <div className={`h-3 w-12 rounded ${c("bg-black/5", "bg-white/5")}`} />
                      <div className={`h-2.5 w-10 rounded ${c("bg-black/5", "bg-white/5")}`} />
                    </div>
                    <div className={`h-4 w-28 rounded ${c("bg-black/5", "bg-white/5")}`} />
                    <div className={`h-3 w-36 rounded ${c("bg-black/5", "bg-white/5")}`} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right main conversation view */}
          <div className="flex-1 hidden md:flex flex-col items-center justify-center p-8 text-center animate-pulse">
            <div className={`w-20 h-20 rounded-3xl mb-6 flex items-center justify-center ${c("bg-black/5 text-black/10", "bg-white/5 text-white/10")}`}>
              <span className="material-symbols-outlined text-[40px]">forum</span>
            </div>
            <div className={`h-6 w-48 rounded-lg mb-2 ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`h-4.5 w-64 rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
          </div>
        </div>
      )}

      {/* C. MODELS & ROUTING LAYOUT */}
      {page === "models" && (
        <>
          <div className="space-y-3">
            <div className={`h-12 w-1/3 rounded-2xl animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`h-6 w-1/2 rounded-xl animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
          </div>

          {/* Routing Fabric visual canvas block */}
          <div
            className={`rounded-[2rem] border p-8 space-y-8 animate-pulse ${c(
              "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
              "bg-[#1f1f23] border-white/[0.06]"
            )}`}
          >
            <div className="flex justify-between items-center">
              <div className={`h-6 w-48 rounded ${c("bg-black/5", "bg-white/5")}`} />
              <div className={`h-8 w-20 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
            </div>
            <div className="flex flex-col md:flex-row items-center justify-center gap-6 py-6">
              {/* Origin */}
              <div className={`rounded-[1.5rem] p-6 w-48 h-36 border flex flex-col items-center justify-center gap-2 ${c("bg-[#F5F5F7] border-black/5", "bg-[#131317] border-white/[0.06]")}`}>
                <div className={`w-12 h-12 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-4 w-24 rounded ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-3 w-28 rounded ${c("bg-black/5", "bg-white/5")}`} />
              </div>
              {/* Arrow */}
              <div className={`h-2.5 w-12 rounded ${c("bg-black/5", "bg-white/5")}`} />
              {/* Router */}
              <div className={`rounded-[1.5rem] p-6 w-48 h-36 border-2 border-dashed flex flex-col items-center justify-center gap-2 ${c("bg-[#F5F5F7] border-black/10", "bg-[#131317] border-white/[0.1]")}`}>
                <div className={`w-12 h-12 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-4 w-24 rounded ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-3 w-28 rounded ${c("bg-black/5", "bg-white/5")}`} />
              </div>
              {/* Arrow */}
              <div className={`h-2.5 w-12 rounded ${c("bg-black/5", "bg-white/5")}`} />
              {/* Targets */}
              <div className="flex flex-col gap-3">
                {[1, 2].map((i) => (
                  <div
                    key={i}
                    className={`rounded-2xl px-5 py-4 w-64 h-20 border flex items-center justify-between gap-4 ${c(
                      "bg-[#F5F5F7] border-black/5",
                      "bg-[#131317] border-white/[0.04]"
                    )}`}
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className={`h-3 w-16 rounded ${c("bg-black/5", "bg-white/5")}`} />
                      <div className={`h-4 w-28 rounded ${c("bg-black/5", "bg-white/5")}`} />
                    </div>
                    <div className={`w-10 h-10 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom Settings & Backends row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Settings Panel */}
            <div
              className={`rounded-[2rem] border p-8 space-y-6 animate-pulse ${c(
                "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
                "bg-[#1f1f23] border-white/[0.06]"
              )}`}
            >
              <div className={`h-6 w-36 rounded ${c("bg-black/5", "bg-white/5")}`} />
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex justify-between">
                      <div className={`h-3 w-24 rounded ${c("bg-black/5", "bg-white/5")}`} />
                      <div className={`h-3 w-12 rounded ${c("bg-black/5", "bg-white/5")}`} />
                    </div>
                    <div className={`h-2.5 w-full rounded-full ${c("bg-black/5", "bg-white/5")}`} />
                  </div>
                ))}
              </div>
            </div>

            {/* Backends Table */}
            <div
              className={`rounded-[2rem] border overflow-hidden lg:col-span-2 p-8 space-y-6 animate-pulse ${c(
                "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
                "bg-[#1f1f23] border-white/[0.06]"
              )}`}
            >
              <div className="space-y-2">
                <div className={`h-6 w-48 rounded ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-4.5 w-64 rounded ${c("bg-black/5", "bg-white/5")}`} />
              </div>
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-4 py-2">
                    <div className={`w-10 h-10 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                    <div className="flex-1 space-y-1.5">
                      <div className={`h-4 w-32 rounded ${c("bg-black/5", "bg-white/5")}`} />
                      <div className={`h-3 w-64 rounded ${c("bg-black/5", "bg-white/5")}`} />
                    </div>
                    <div className={`w-16 h-6 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* D. BOT BUILDER STEPPER LAYOUT */}
      {page === "builder" && (
        <div className="max-w-6xl mx-auto animate-pulse">
          {/* Step header */}
          <div className="mb-6">
            <div className="flex items-center gap-2.5 mb-3 flex-wrap">
              <div className={`h-6 w-24 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
              <div className={`h-4 w-20 rounded ${c("bg-black/5", "bg-white/5")}`} />
            </div>
            <div className={`h-10 md:h-12 w-3/4 md:w-1/2 rounded-2xl mb-3 ${c("bg-black/5", "bg-white/5")}`} />
            <div className="space-y-2">
               <div className={`h-4 w-full max-w-2xl rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
               <div className={`h-4 w-2/3 max-w-lg rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
            </div>
          </div>

          {/* Step 1 Persona Layout */}
          <div className="max-w-2xl mx-auto space-y-6">
            {/* Card 1: Bot Basic Identity */}
            <div
              className={`rounded-[2rem] border p-5 sm:p-8 ${c(
                "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
                "bg-[#1f1f23] border-white/[0.06]"
              )}`}
            >
              <div className="flex items-center gap-2.5 mb-6">
                <div className={`w-6 h-6 rounded-md ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-5 w-32 rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
              </div>
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className={`h-3 w-20 rounded ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`h-12 w-full rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                </div>
                {/* Info Alert Skeleton */}
                <div className={`rounded-2xl border p-4 flex gap-3.5 ${c("bg-[#F5F5F7] border-black/5", "bg-[#131317] border-white/[0.04]")}`}>
                   <div className={`w-6 h-6 rounded-md flex-shrink-0 ${c("bg-black/5", "bg-white/5")}`} />
                   <div className="space-y-2 flex-1">
                     <div className={`h-4 w-40 rounded ${c("bg-black/5", "bg-white/5")}`} />
                     <div className={`h-3 w-full rounded ${c("bg-black/5", "bg-white/5")}`} />
                     <div className={`h-3 w-4/5 rounded ${c("bg-black/5", "bg-white/5")}`} />
                   </div>
                </div>
              </div>
            </div>

            {/* Card 2: Persona Details */}
            <div
              className={`rounded-[2rem] border p-5 sm:p-8 space-y-6 ${c(
                "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
                "bg-[#1f1f23] border-white/[0.06]"
              )}`}
            >
              <div className="flex items-center gap-2.5 mb-2">
                <div className={`w-6 h-6 rounded-md ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-5 w-36 rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
              </div>

              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="space-y-2">
                  <div className={`h-3 w-32 rounded ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`${i === 3 || i === 4 ? "h-24" : i === 5 ? "h-16" : "h-12"} w-full rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                </div>
              ))}

              {/* Human-feel tips */}
              <div className={`rounded-2xl p-5 border space-y-4 ${c("bg-[#F5F5F7] border-black/5", "bg-[#131317] border-white/[0.06]")}`}>
                <div className="flex items-center gap-2">
                  <div className={`w-5 h-5 rounded-md ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`h-4 w-32 rounded ${c("bg-black/5", "bg-white/5")}`} />
                </div>
                <div className="space-y-2.5">
                  {[1, 2, 3, 4].map((j) => (
                    <div key={j} className="flex gap-3">
                      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${c("bg-black/10", "bg-white/10")}`} />
                      <div className={`h-3 w-full rounded ${c("bg-black/5", "bg-white/5")}`} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation buttons */}
          <div className={`flex items-center justify-between mt-8 pt-6 border-t ${c("border-black/5", "border-white/[0.06]")}`}>
             <div className={`h-12 w-28 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
             <div className={`h-3 w-32 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
             <div className={`h-12 w-36 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
          </div>
        </div>
      )}

      {/* E. SETTINGS TABBED LAYOUT */}
      {page === "settings" && (
        <>
          {/* Tab Bar placeholder */}
          <div className={`border-b flex gap-6 pb-2 animate-pulse ${c("border-black/5", "border-white/5")}`}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className={`h-6 w-20 rounded ${c("bg-black/5", "bg-white/5")}`} />
            ))}
          </div>

          {/* Settings layout card */}
          <div
            className={`max-w-4xl mx-auto rounded-[2rem] border p-8 space-y-8 animate-pulse ${c(
              "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
              "bg-[#1f1f23] border-white/[0.06]"
            )}`}
          >
            {/* Profile row */}
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
              <div className={`w-24 h-24 rounded-3xl ${c("bg-black/5", "bg-white/5")}`} />
              <div className="space-y-3 flex-grow w-full">
                <div className={`h-6 w-40 rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-4.5 w-60 rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-3.5 w-28 rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
              </div>
            </div>

            {/* Form fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="space-y-2">
                  <div className={`h-4 w-28 rounded ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`h-12 w-full rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                </div>
              ))}
            </div>

            {/* Actions row */}
            <div className="flex justify-end gap-3 pt-4">
              <div className={`h-11 w-24 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
              <div className={`h-11 w-32 rounded-xl ${c("bg-black/10", "bg-white/10")}`} />
            </div>
          </div>
        </>
      )}
    </>
  );

  // Dynamic padding helper based on active page
  const getPaddingClass = () => {
    switch (page) {
      case "inbox":
        return ""; // Inbox has zero padding for its main layout
      case "builder":
        return "px-4 sm:px-8 lg:px-12 py-6 sm:py-8";
      case "models":
        return "p-4 sm:p-8 lg:p-12";
      case "settings":
        return "p-4 sm:p-8 lg:p-12";
      default:
        return "p-4 sm:p-6 lg:p-10";
    }
  };

  // ── Content Only Render ──
  if (contentOnly) {
    return (
      <div className={`flex-grow flex flex-col z-10 space-y-8 overflow-hidden relative ${getPaddingClass()}`}>
        {renderContentSkeleton()}
      </div>
    );
  }

  // ── Protected Pages Layout Container (Sidebar + TopBar Wrapper) ──
  return (
    <div
      className={`min-h-screen flex font-sans transition-colors duration-300 ${c(
        "bg-[#F5F5F7] text-[#1c1c1e]",
        "bg-[#131317] text-[#e4e1e7]"
      )}`}
    >
      {/* Sidebar Skeleton */}
      <aside
        className={`hidden md:flex h-screen sticky top-0 flex-shrink-0 w-64 border-r flex-col p-4 space-y-6 ${c(
          "bg-[#F5F5F7] border-black/5",
          "bg-[#111115] border-white/5"
        )}`}
      >
        <div className={`h-16 flex items-center border-b px-1 pb-4 gap-3 ${c("border-black/5", "border-white/5")}`}>
          <div className={`w-9 h-9 rounded-xl animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
          <div className="space-y-1.5 flex-1">
            <div className={`h-4 w-16 rounded animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`h-2.5 w-10 rounded animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
          </div>
        </div>

        <div className="flex-1 space-y-4 pt-2">
          <div className={`h-3 w-16 rounded animate-pulse px-2 ${c("bg-black/5", "bg-white/5")}`} />
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-3 px-2 py-1">
              <div className={`w-5 h-5 rounded animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
              <div className={`h-3.5 w-24 rounded animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
            </div>
          ))}
        </div>

        <div className={`border-t pt-4 space-y-4 ${c("border-black/5", "border-white/5")}`}>
          <div className={`h-9 w-full rounded-xl animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
          <div className={`h-3.5 w-24 rounded animate-pulse mx-2 ${c("bg-black/5", "bg-white/5")}`} />
          <div className={`h-3.5 w-20 rounded animate-pulse mx-2 ${c("bg-black/5", "bg-white/5")}`} />
        </div>
      </aside>

      {/* Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div
          className={`absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${c(
            "bg-[#EBDCFF] opacity-10 mix-blend-multiply",
            "bg-[#EBDCFF] opacity-5 mix-blend-screen"
          )}`}
        ></div>

        {/* TopBar Skeleton */}
        <header
          className={`h-16 border-b flex items-center justify-between px-6 md:px-10 flex-shrink-0 z-10 sticky top-0 ${c(
            "bg-[#F5F5F7]/80 backdrop-blur-md border-black/5",
            "bg-[#111115]/90 backdrop-blur-md border-white/5"
          )}`}
        >
          <div className={`h-9 w-40 md:w-64 rounded-xl animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
          <div className="flex items-center gap-4">
            <div className={`w-8 h-8 rounded-full animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`w-8 h-8 rounded-full animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`w-10 h-10 rounded-full animate-pulse ${c("bg-black/5", "bg-white/5")}`} />
          </div>
        </header>

        <main className={`flex-grow overflow-y-auto z-10 ${getPaddingClass()}`}>
          {renderContentSkeleton()}
        </main>
      </div>
    </div>
  );
}
