import { useRef, useState } from "react";
import { useLocation } from "wouter";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import {
  ArrowRight,
  BarChart3,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Database,
  FileText,
  GraduationCap,
  Languages,
  LayoutDashboard,
  Menu,
  MessageCircle,
  Network,
  PlayCircle,
  Rocket,
  Search,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Users,
  Workflow,
  X,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

gsap.registerPlugin(useGSAP);
gsap.config({ force3D: true });

const displayFont = { fontFamily: "'Playfair Display', serif" };
const headingFont = { fontFamily: "'Space Grotesk', sans-serif" };

const navItems = [
  { label: "Idea", href: "#idea" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Execution", href: "#execution" },
  { label: "Demo", href: "#demo" },
  { label: "Architecture", href: "#architecture" },
];

const projectStory = [
  {
    label: "Problem",
    title: "Small teams need support automation, but setup is too technical.",
    body: "Many Pakistani SMEs and institutes already answer customers on WhatsApp, but they do not have the time or engineering resources to build an AI support system.",
    icon: Users,
    accent: "#ffb4ab",
  },
  {
    label: "Idea",
    title: "Let users upload knowledge and deploy an assistant without code.",
    body: "Aina turns files, website content, guidelines, contact details, and a chosen persona into a ready chatbot powered by retrieval-augmented generation.",
    icon: Sparkles,
    accent: "#EBDCFF",
  },
  {
    label: "Execution",
    title: "A complete app, not only a landing-page concept.",
    body: "The project includes authentication, bot builder, knowledge ingestion, real-time testing, WhatsApp and web deployment, analytics, model routing, and handoff flows.",
    icon: Workflow,
    accent: "#b0c6ff",
  },
  {
    label: "Outcome",
    title: "A practical AI agent that can answer from trusted sources.",
    body: "A business owner can create, test, and monitor a multilingual assistant while keeping humans available for escalations.",
    icon: CheckCircle2,
    accent: "#59eeb4",
  },
];

const buildSteps = [
  {
    step: "01",
    title: "Persona",
    copy: "Define the bot name, tone, greeting, fallback behavior, and identity.",
    icon: Bot,
    preview: ["Friendly tone", "Multilingual ready", "Custom greeting" ,"Fallback messages" ],
    accent: "#EBDCFF",
  },
  {
    step: "02",
    title: "Knowledge",
    copy: "Upload documents, paste guidelines, add websites, and include contact channels.",
    icon: UploadCloud,
    preview: ["PDF indexed", "Website crawled", "FAQ chunks"],
    accent: "#b0c6ff",
  },
  {
    step: "03",
    title: "Test",
    copy: "Chat with the assistant before launch and inspect returned source chunks.",
    icon: MessageCircle,
    preview: ["Streaming reply", "Source-backed", "Memory enabled"],
    accent: "#f5c5ff",
  },
  {
    step: "04",
    title: "Deploy",
    copy: "Publish the same assistant to WhatsApp or an embeddable web widget.",
    icon: Rocket,
    preview: ["WhatsApp live", "Web widget", "Active status"],
    accent: "#59eeb4",
  },
];

const architectureSteps = [
  { title: "Upload files or website", icon: FileText },
  { title: "Extract, clean, and chunk", icon: Database },
  { title: "Embed and search vectors", icon: Search },
  { title: "Route intent semantically", icon: Network },
  { title: "Generate grounded reply", icon: BrainCircuit },
  { title: "Track analytics and handoff", icon: BarChart3 },
];

const stackBadges = [
  "React",
  "TypeScript",
  "FastAPI",
  "PostgreSQL",
  "pgvector",
  "RAG",
  "SSE",
  "WhatsApp API",
];

function IconBadge({ icon: Icon, tone = "light" }: { icon: LucideIcon; tone?: "light" | "dark" }) {
  return (
    <div
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border ${
        tone === "dark"
          ? "border-white/10 bg-white/10 text-[#EBDCFF]"
          : "border-black/5 bg-[#EBDCFF] text-[#1c1c1e]"
      }`}
    >
      <Icon className="h-5 w-5" aria-hidden="true" />
    </div>
  );
}

function SectionKicker({ children, tone = "light" }: { children: string; tone?: "light" | "dark" }) {
  return (
    <span
      className={`mb-4 inline-flex rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.2em] ${
        tone === "dark"
          ? "border-white/10 bg-white/5 text-white/60"
          : "border-black/5 bg-white text-[#1c1c1e]/50"
      }`}
      style={headingFont}
    >
      {children}
    </span>
  );
}

function ProductFlowMockup() {
  return (
    <div className="home-reveal mx-auto mt-14 w-full max-w-6xl overflow-hidden rounded-lg border border-black/10 bg-white shadow-[0_24px_90px_rgba(28,28,30,0.12)]">
      <div className="flex items-center justify-between border-b border-black/5 bg-[#F5F5F7] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-[#ffb4ab]" />
          <span className="h-3 w-3 rounded-full bg-[#f5c5ff]" />
          <span className="h-3 w-3 rounded-full bg-[#59eeb4]" />
        </div>
        <div className="hidden rounded-full border border-black/5 bg-white px-4 py-1.5 text-xs font-bold text-[#1c1c1e]/60 sm:block">
          Aina Builder / Live Project Overview
        </div>
        <div className="h-7 w-7 rounded-lg border border-black/5 bg-white" />
      </div>

      <div className="grid gap-0 lg:grid-cols-[1.05fr_0.9fr_1.05fr]">
        <div className="border-b border-black/5 p-5 sm:p-6 lg:border-b-0 lg:border-r">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#1c1c1e]/40">Knowledge Uploaded</p>
              <h3 className="mt-1 text-xl font-bold text-[#1c1c1e]" style={headingFont}>
                Sources become searchable
              </h3>
            </div>
            <IconBadge icon={UploadCloud} />
          </div>

          <div className="space-y-3">
            {[
              { name: "Price-list.pdf", meta: "36 chunks indexed", width: "w-10/12" },
              { name: "Website FAQ", meta: "12 pages crawled", width: "w-8/12" },
              { name: "Support rules", meta: "Escalation policy", width: "w-9/12" },
            ].map((item) => (
              <div key={item.name} className="rounded-lg border border-black/5 bg-[#F5F5F7] p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white text-[#5c3ea3]">
                    <FileText className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold text-[#1c1c1e]">{item.name}</p>
                    <p className="text-xs font-medium text-[#1c1c1e]/50">{item.meta}</p>
                  </div>
                  <CheckCircle2 className="h-5 w-5 text-[#0b9662]" aria-hidden="true" />
                </div>
                <div className="mt-3 h-2 rounded-full bg-white">
                  <div className={`h-2 rounded-full bg-[#EBDCFF] ${item.width}`} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative border-b border-black/5 bg-[#1c1c1e] p-5 text-[#F5F5F7] sm:p-6 lg:border-b-0 lg:border-r">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-white/40">Aina RAG Engine</p>
              <h3 className="mt-1 text-xl font-bold" style={headingFont}>
                Search, route, answer
              </h3>
            </div>
            <IconBadge icon={BrainCircuit} tone="dark" />
          </div>

          <div className="grid gap-3">
            {[
              ["Language", "Roman Urdu detected"],
              ["Intent", "RAG_LOOKUP"],
              ["Model route", "Support assistant"],
              ["Confidence", "Source-backed"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-white/10 bg-white/[0.04] p-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-white/40">{label}</p>
                <p className="mt-1 text-sm font-semibold text-white/85">{value}</p>
              </div>
            ))}
          </div>

          <div className="flow-pulse mt-5 rounded-lg border border-[#EBDCFF]/30 bg-[#EBDCFF]/10 p-4">
            <div className="mb-2 flex items-center gap-2 text-[#EBDCFF]">
              <Zap className="h-4 w-4" aria-hidden="true" />
              <span className="text-xs font-bold uppercase tracking-[0.16em]">Live pipeline</span>
            </div>
            <p className="text-sm leading-relaxed text-white/70">
              {"User question -> vector search -> prompt construction -> streamed response -> analytics event."}
            </p>
          </div>
        </div>

        <div className="p-5 sm:p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#1c1c1e]/40">WhatsApp / Web Reply</p>
              <h3 className="mt-1 text-xl font-bold text-[#1c1c1e]" style={headingFont}>
                Customer receives answer
              </h3>
            </div>
            <IconBadge icon={MessageCircle} />
          </div>

          <div className="rounded-lg border border-black/5 bg-[#F5F5F7] p-4">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#59eeb4] text-[#003826]">
                <Bot className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <p className="text-sm font-bold text-[#1c1c1e]">Aina Support Bot</p>
                <p className="text-xs font-medium text-[#0b9662]">Online on WhatsApp</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="ml-auto max-w-[82%] rounded-lg bg-white p-3 text-sm font-medium text-[#1c1c1e] shadow-sm">
                Price list bhej dein? Delivery charges bhi bata dein.
              </div>
              <div className="max-w-[88%] rounded-lg bg-[#EBDCFF] p-3 text-sm font-medium leading-relaxed text-[#1c1c1e]">
                Sure. Large pizza Rs. 1,499 hai. Delivery Rs. 150 hai, aur orders usually 35 minutes mein deliver hotay hain.
              </div>
              <div className="flex flex-wrap gap-2 pt-1 text-[11px] font-bold uppercase tracking-[0.12em] text-[#1c1c1e]/50">
                <span className="rounded-full bg-white px-3 py-1">Source: Price-list.pdf</span>
                <span className="rounded-full bg-white px-3 py-1">Escalation ready</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function BuildStepPreview({ step }: { step: (typeof buildSteps)[number] }) {
  const Icon = step.icon;

  return (
    <article className="home-reveal rounded-lg border border-black/5 bg-white p-5 shadow-[0_10px_35px_rgba(28,28,30,0.04)]">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#1c1c1e]/40">{step.step}</span>
          <h3 className="mt-1 text-2xl font-bold text-[#1c1c1e]" style={headingFont}>
            {step.title}
          </h3>
        </div>
        <div
          className="flex h-11 w-11 items-center justify-center rounded-lg border border-black/5 text-[#1c1c1e]"
          style={{ backgroundColor: step.accent }}
        >
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
      <p className="min-h-[72px] text-sm font-medium leading-relaxed text-[#1c1c1e]/60">{step.copy}</p>

      <div className="mt-5 rounded-lg border border-black/5 bg-[#F5F5F7] p-3">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1c1c1e]/40">Mini preview</span>
          <span className="h-2 w-2 rounded-full bg-[#0b9662]" />
        </div>
        <div className="space-y-2">
          {step.preview.map((item) => (
            <div key={item} className="flex items-center gap-2 rounded-lg bg-white px-3 py-2">
              <CheckCircle2 className="h-4 w-4 text-[#0b9662]" aria-hidden="true" />
              <span className="text-sm font-semibold text-[#1c1c1e]/80">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}

export default function AinaLanding() {
  const [, setLocation] = useLocation();
  const { isAuthenticated } = useAuth();
  const container = useRef<HTMLDivElement>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const openBuilder = () => setLocation(isAuthenticated ? "/builder" : "/signup");
  const openDashboard = () => setLocation(isAuthenticated ? "/dashboard" : "/login");

  useGSAP(
    () => {
      const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      if (prefersReducedMotion) {
        gsap.set(".home-reveal", { opacity: 1, y: 0 });
        return;
      }

      const entrance = gsap.fromTo(
        ".home-reveal",
        { y: 28, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          stagger: 0.08,
          ease: "power3.out",
        }
      );

      const pulse = gsap.to(".flow-pulse", {
        boxShadow: "0 0 0 1px rgba(235, 220, 255, 0.45), 0 0 34px rgba(235, 220, 255, 0.18)",
        duration: 1.7,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });

      const float = gsap.to(".mock-float", {
        y: -8,
        duration: 2.4,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });

      return () => {
        entrance.kill();
        pulse.kill();
        float.kill();
      };
    },
    { scope: container }
  );

  return (
    <div
      ref={container}
      className="min-h-screen overflow-x-hidden bg-[#F5F5F7] text-[#1c1c1e] selection:bg-[#EBDCFF] selection:text-[#1c1c1e]"
    >
      <header className="fixed left-0 top-0 z-50 w-full border-b border-black/5 bg-[#F5F5F7]/90 backdrop-blur-xl">
        <nav className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8" aria-label="Project navigation">
          <a href="#top" aria-label="Aina AI Home" className="flex min-w-0 items-center gap-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] rounded-lg">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#EBDCFF] text-[#1c1c1e]">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
            </div>
            <div className="min-w-0">
              <p className="truncate text-base font-black tracking-tight text-[#1c1c1e]" style={headingFont}>
                Aina AI
              </p>
              
            </div>
          </a>

          <div className="hidden items-center gap-1 rounded-full border border-black/5 bg-white/75 p-1 text-sm font-bold shadow-sm lg:flex">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="rounded-full px-4 py-2 text-[#1c1c1e]/60 transition-colors hover:bg-[#EBDCFF] hover:text-[#1c1c1e] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3]"
              >
                {item.label}
              </a>
            ))}
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <button
              onClick={openDashboard}
              className="hidden items-center gap-2 rounded-lg border border-black/10 bg-white px-4 py-2.5 text-sm font-bold text-[#1c1c1e] transition-colors hover:bg-black/5 sm:flex focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2"
            >
              <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
              {isAuthenticated ? "Dashboard" : "Sign In"}
            </button>
            <button
              onClick={openBuilder}
              className="flex items-center gap-2 rounded-lg border border-[#1c1c1e]/10 bg-[#EBDCFF] px-4 py-2.5 text-sm font-black text-[#1c1c1e] shadow-sm transition-colors hover:bg-[#d8bfff] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2"
            >
              Open Builder
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
            <button
              aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-black/10 bg-white text-[#1c1c1e] lg:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3]"
            >
              {isMobileMenuOpen ? (
                <X className="h-5 w-5" aria-hidden="true" />
              ) : (
                <Menu className="h-5 w-5" aria-hidden="true" />
              )}
            </button>
          </div>
        </nav>

        {isMobileMenuOpen && (
          <div className="absolute left-0 top-full w-full border-b border-black/5 bg-[#F5F5F7] p-4 shadow-lg lg:hidden">
            <nav className="flex flex-col gap-2" aria-label="Mobile navigation">
              {navItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="rounded-lg px-4 py-3 text-sm font-bold text-[#1c1c1e]/80 transition-colors hover:bg-black/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3]"
                >
                  {item.label}
                </a>
              ))}
              <div className="mt-2 flex flex-col gap-2 pt-2 border-t border-black/5 sm:hidden">
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false);
                    openDashboard();
                  }}
                  className="flex items-center justify-center gap-2 rounded-lg border border-black/10 bg-white px-4 py-3 text-sm font-bold text-[#1c1c1e] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3]"
                >
                  <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
                  {isAuthenticated ? "Dashboard" : "Sign In"}
                </button>
              </div>
            </nav>
          </div>
        )}
      </header>

      <main id="top" className="pt-24">
        <section className="px-4 pb-16 pt-10 sm:px-6 lg:px-8 lg:pb-24">
          <div className="mx-auto max-w-[1240px]">
            <div className="home-reveal mx-auto max-w-5xl text-center">
              
              <h1
                className="text-4xl font-semibold leading-[0.92] tracking-tight text-[#1c1c1e] sm:text-[5rem] lg:text-[6.9rem] text-balance"
                style={displayFont}
              >
                Aina AI: turn business knowledge into a{" "}
                <span className="italic text-[#c09def]">WhatsApp ready chatbot</span>
              </h1>
              <p className="mx-auto mt-7 max-w-3xl text-base font-medium leading-8 text-[#1c1c1e]/68 sm:text-xl">
                A no-code AI chatbot builder for Pakistani SMEs and educational institutions,supported in English, Urdu, and Roman Urdu through RAG, deployment, analytics, and human handoff.
              </p>
              <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <button
                  onClick={openBuilder}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#1c1c1e] px-6 py-4 text-sm font-black text-[#F5F5F7] shadow-[0_16px_42px_rgba(28,28,30,0.22)] transition-transform hover:-translate-y-0.5 sm:w-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2"
                >
                  Open Builder
                  <Rocket className="h-4 w-4" aria-hidden="true" />
                </button>
               
                <a
                  href="#architecture"
                  className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#5c3ea3]/20 bg-[#EBDCFF] px-6 py-4 text-sm font-black text-[#1c1c1e] transition-colors hover:bg-[#d8bfff] sm:w-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2"
                >
                  See Architecture
                  <Network className="h-4 w-4" aria-hidden="true" />
                </a>
              </div>
            </div>

            <ProductFlowMockup />
          </div>
        </section>

        <section id="idea" className="scroll-mt-24 bg-white px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-[1240px]">
            <div className="home-reveal max-w-3xl">
              <SectionKicker>Project Story</SectionKicker>
              <p className="mt-5 text-lg font-medium leading-8 text-[#1c1c1e]/60">
                This section gives evaluators a fast overview of the problem, the proposed solution, the execution, and
                the result. It makes Aina feel like a complete final-year project instead of a generic template.
              </p>
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {projectStory.map((item) => {
                const Icon = item.icon;
                return (
                  <article key={item.label} className="home-reveal rounded-lg border border-black/5 bg-[#F5F5F7] p-5">
                    <div className="mb-6 flex items-center justify-between">
                      <span className="text-xs font-black uppercase tracking-[0.2em] text-[#1c1c1e]/40">{item.label}</span>
                      <div
                        className="flex h-10 w-10 items-center justify-center rounded-lg border border-black/5 text-[#1c1c1e]"
                        style={{ backgroundColor: item.accent }}
                      >
                        <Icon className="h-5 w-5" aria-hidden="true" />
                      </div>
                    </div>
                    <h3 className="text-xl font-black leading-snug text-[#1c1c1e] text-balance" style={headingFont}>
                      {item.title}
                    </h3>
                    <p className="mt-4 text-sm font-medium leading-7 text-[#1c1c1e]/60">{item.body}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section id="how-it-works" className="scroll-mt-24 px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-[1240px]">
            <div className="home-reveal flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
              <div className="max-w-3xl">
                <SectionKicker>How It Works</SectionKicker>
                <h2 className="text-4xl font-black tracking-tight text-[#1c1c1e] sm:text-5xl text-balance" style={headingFont}>
                  A real four-step builder, shown as the center of the product.
                </h2>
              </div>
              <button
                onClick={openBuilder}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#EBDCFF] px-5 py-3 text-sm font-black text-[#1c1c1e] transition-colors hover:bg-[#d8bfff] sm:w-fit focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2"
              >
                Open the actual builder
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {buildSteps.map((step) => (
                <BuildStepPreview key={step.step} step={step} />
              ))}
            </div>
          </div>
        </section>

        <section id="execution" className="scroll-mt-24 bg-[#1c1c1e] px-4 py-20 text-[#F5F5F7] sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto grid max-w-[1240px] gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div className="home-reveal">
              <SectionKicker tone="dark">Local Context</SectionKicker>
              <h2 className="text-4xl font-black tracking-tight sm:text-5xl text-balance" style={headingFont}>
                Built for the way local customers actually message businesses.
              </h2>
              <p className="mt-5 text-lg font-medium leading-8 text-white/60">
                Aina is strongest when it shows its local purpose: WhatsApp first support, Pakistani business workflows,
                and multilingual conversations where users may switch between English, Urdu, and Roman Urdu.
              </p>
              
            </div>

            <div className="home-reveal rounded-lg border border-white/10 bg-white/[0.04] p-5">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-white/40">Execution Snapshot</p>
                  <h3 className="mt-1 text-2xl font-black" style={headingFont}>
                    What the project includes
                  </h3>
                </div>
                <IconBadge icon={ShieldCheck} tone="dark" />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  "Multi-tenant authentication",
                  "Persona and bot lifecycle",
                  "Document and website ingestion",
                  "Hybrid retrieval with source chunks",
                  "Streaming test chat",
                  "WhatsApp and web deployment",
                  "Analytics by channel and language",
                  "Human agent handoff",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3 rounded-lg border border-white/10 bg-[#131317] p-3">
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-[#59eeb4]" aria-hidden="true" />
                    <span className="text-sm font-bold text-white/80">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="demo" className="scroll-mt-24 bg-white px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-[1240px]">
            <div className="home-reveal grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
              <div>
                <SectionKicker>Demo</SectionKicker>
                <h2 className="text-4xl font-black tracking-tight text-[#1c1c1e] sm:text-5xl text-balance" style={headingFont}>
                  A product-style demo that shows testing, sources, analytics, and handoff.
                </h2>
                <p className="mt-5 text-lg font-medium leading-8 text-[#1c1c1e]/60">
                  Instead of abstract marketing blocks, this section gives the visitor a preview of what happens after a
                  bot is trained: a chat is tested, sources are returned, and performance is measured.
                </p>
                <div className="mt-7 flex flex-col gap-3 sm:flex-row">
                  <button
                    onClick={openBuilder}
                    className="flex items-center justify-center gap-2 rounded-lg bg-[#1c1c1e] px-5 py-3 text-sm font-black text-[#F5F5F7] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2"
                  >
                    Try in Builder
                    <MessageCircle className="h-4 w-4" aria-hidden="true" />
                  </button>
                  <button
                    onClick={openDashboard}
                    className="flex items-center justify-center gap-2 rounded-lg border border-black/10 bg-[#F5F5F7] px-5 py-3 text-sm font-black text-[#1c1c1e] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2"
                  >
                    View Dashboard
                    <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
                  </button>
                </div>
              </div>

              <div className="rounded-lg border border-black/10 bg-[#F5F5F7] p-4 shadow-[0_20px_70px_rgba(28,28,30,0.10)]">
                <div className="grid gap-4 lg:grid-cols-[1.08fr_0.92fr]">
                  <div className="rounded-lg border border-black/5 bg-white p-4">
                    <div className="mb-4 flex items-center justify-between border-b border-black/5 pb-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#EBDCFF]">
                          <Bot className="h-5 w-5" aria-hidden="true" />
                        </div>
                        <div>
                          <p className="text-sm font-black text-[#1c1c1e]">Test Live Behavior</p>
                          <p className="text-xs font-bold text-[#1c1c1e]/45">Builder Step 3</p>
                        </div>
                      </div>
                      <span className="rounded-full bg-[#59eeb4]/20 px-3 py-1 text-[11px] font-black uppercase tracking-[0.12em] text-[#005138]">
                        Streaming
                      </span>
                    </div>

                    <div className="space-y-3">
                      <div className="ml-auto max-w-[82%] rounded-lg bg-[#F5F5F7] p-3 text-sm font-semibold text-[#1c1c1e]">
                        Can I talk to a human agent?
                      </div>
                      <div className="max-w-[88%] rounded-lg bg-[#EBDCFF] p-3 text-sm font-semibold leading-6 text-[#1c1c1e]">
                        I can connect you to an available support agent. I have also saved the conversation context for
                        a smoother handoff.
                      </div>
                      
                    </div>
                  </div>

                  <div className="grid gap-4">
                    {[
                      { label: "Deflection rate", value: "74%", icon: Zap },
                      { label: "Avg response", value: "1.8s", icon: BarChart3 },
                      { label: "Languages", value: "Multilingual", icon: Languages },
                    ].map((item) => {
                      const Icon = item.icon;
                      return (
                        <div key={item.label} className="rounded-lg border border-black/5 bg-white p-4">
                          <div className="mb-5 flex items-center justify-between">
                            <p className="text-xs font-black uppercase tracking-[0.18em] text-[#1c1c1e]/40">
                              {item.label}
                            </p>
                            <Icon className="h-5 w-5 text-[#5c3ea3]" aria-hidden="true" />
                          </div>
                          <p className="text-3xl font-black text-[#1c1c1e]" style={headingFont}>
                            {item.value}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="architecture" className="scroll-mt-24 px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-[1240px]">
            <div className="home-reveal max-w-3xl">
              <SectionKicker>Architecture</SectionKicker>
              <h2 className="text-4xl font-black tracking-tight text-[#1c1c1e] sm:text-5xl text-balance" style={headingFont}>
                The technical pipeline is visible without turning the page into documentation.
              </h2>
              <p className="mt-5 text-lg font-medium leading-8 text-[#1c1c1e]/60">
                This gives examiners a clean map of the system: ingestion, retrieval, semantic routing, generation,
                deployment, analytics, and human handoff.
              </p>
            </div>

            <div className="mt-10 rounded-lg border border-black/5 bg-white p-5 shadow-[0_12px_45px_rgba(28,28,30,0.05)]">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
                {architectureSteps.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.title} className="home-reveal relative rounded-lg border border-black/5 bg-[#F5F5F7] p-4">
                      <div className="mb-4 flex items-center justify-between">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#EBDCFF] text-[#1c1c1e]">
                          <Icon className="h-5 w-5" aria-hidden="true" />
                        </div>
                        <span className="text-xs font-black text-[#1c1c1e]/30">0{index + 1}</span>
                      </div>
                      <p className="text-sm font-black leading-6 text-[#1c1c1e]" style={headingFont}>
                        {item.title}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-black/5 bg-[#1c1c1e] px-4 py-12 text-[#F5F5F7] sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-[1240px] gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <div className="mb-5 flex items-center gap-3">
              
            <div className="min-w-0">
              <p className="truncate text-3xl font-black tracking-tight text-white" style={headingFont}>
                Aina AI
              </p>
              
            </div>
            </div>
            <p className="max-w-2xl text-sm font-medium leading-7 text-white/60">
              A Project which only focused on no-code AI chatbot creation, knowledge-grounded responses,
              WhatsApp deployment, analytics, and practical support workflows for local organizations.
            </p>
          </div>

          <div className="lg:text-right">
            <div className="mb-5 flex flex-wrap gap-2 lg:justify-end">
              {stackBadges.map((badge) => (
                <span key={badge} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-bold text-white/60">
                  {badge}
                </span>
              ))}
            </div>
            <div className="flex flex-wrap gap-3 lg:justify-end">
              <button onClick={openBuilder} className="rounded-lg bg-[#EBDCFF] px-4 py-2.5 text-sm font-black text-[#1c1c1e] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2">
                Builder
              </button>
              <button onClick={openDashboard} className="rounded-lg border border-white/10 px-4 py-2.5 text-sm font-black text-white/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2 focus-visible:ring-offset-[#1c1c1e]">
                Dashboard
              </button>
              <a href="#architecture" className="rounded-lg border border-white/10 px-4 py-2.5 text-sm font-black text-white/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c3ea3] focus-visible:ring-offset-2 focus-visible:ring-offset-[#1c1c1e]">
                Architecture
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
