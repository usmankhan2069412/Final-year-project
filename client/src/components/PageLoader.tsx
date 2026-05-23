import { useTheme } from "../contexts/ThemeContext";

interface PageLoaderProps {
  page?: "dashboard" | "inbox" | "builder" | "settings" | "models" | "analytics" | "public";
  contentOnly?: boolean;
}

export default function PageLoader({ page = "dashboard", contentOnly = false }: PageLoaderProps) {
  const { isDark } = useTheme();

  // Dynamic light/dark theme color helper
  const c = (light: string, dark: string) => (isDark ? dark : light);

  // ── Public Pages Skeleton (Auth flow: login, signup, reset password) ──
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

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={`rounded-3xl border p-6 space-y-6 animate-pulse ${c(
                  "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
                  "bg-[#1f1f23] border-white/[0.06]"
                )}`}
              >
                <div className="flex justify-between items-start">
                  <div className={`w-12 h-12 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`w-12 h-6 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
                </div>
                <div className="space-y-3">
                  <div className={`h-3 w-16 rounded ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`h-8 w-24 rounded-lg ${c("bg-black/5", "bg-white/5")}`} />
                </div>
                <div className={`h-1.5 w-full rounded-full ${c("bg-black/5", "bg-white/5")}`} />
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
        <div
          className={`rounded-[1.5rem] border p-6 space-y-6 animate-pulse ${c(
            "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]",
            "bg-[#1f1f23] border-white/[0.06]"
          )}`}
        >
          {/* Stepper bar header */}
          <div className={`flex items-center justify-between flex-wrap gap-4 pb-4 border-b ${c("border-black/5", "border-white/5")}`}>
            <div className="flex items-center gap-2">
              <div className={`h-6 w-24 rounded-full ${c("bg-black/5", "bg-white/5")}`} />
              <div className={`h-4.5 w-16 rounded ${c("bg-black/5", "bg-white/5")}`} />
            </div>
            <div className={`h-8 w-24 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
          </div>

          {/* Step info header */}
          <div className="space-y-3">
            <div className={`h-10 w-1/2 rounded-2xl ${c("bg-black/5", "bg-white/5")}`} />
            <div className={`h-5 w-3/4 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
          </div>

          {/* Step panel layout */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
            {/* Form fields pane (2/3 width) */}
            <div className="lg:col-span-2 space-y-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <div className={`h-4.5 w-32 rounded ${c("bg-black/5", "bg-white/5")}`} />
                  <div className={`h-12 w-full rounded-2xl ${c("bg-black/5", "bg-white/5")}`} />
                </div>
              ))}
            </div>

            {/* Assistant preview / chat simulator pane (1/3 width) */}
            <div className={`rounded-[2rem] border p-6 h-80 flex flex-col justify-between ${c("bg-[#F5F5F7] border-black/5", "bg-[#131317] border-white/[0.06]")}`}>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-xl ${c("bg-black/5", "bg-white/5")}`} />
                  <div className="space-y-2">
                    <div className={`h-4.5 w-24 rounded ${c("bg-black/5", "bg-white/5")}`} />
                    <div className={`h-3 w-16 rounded ${c("bg-black/5", "bg-white/5")}`} />
                  </div>
                </div>
                <div className={`h-2.5 w-full rounded ${c("bg-black/5", "bg-white/5")}`} />
                <div className={`h-2.5 w-5/6 rounded ${c("bg-black/5", "bg-white/5")}`} />
              </div>
              <div className={`h-10 w-full rounded-xl ${c("bg-black/10", "bg-white/10")}`} />
            </div>
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
