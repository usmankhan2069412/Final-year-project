import { useRef } from "react";
import { useLocation } from "wouter";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { useAuth } from "../contexts/AuthContext";

gsap.registerPlugin(useGSAP);
gsap.config({ force3D: true }); // Enforce GPU hardware acceleration globally

export default function Home() {
  const [, setLocation] = useLocation();
  const { isAuthenticated } = useAuth();
  const container = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    // 1. Hero Entrance Animations
    gsap.fromTo(".hero-item", 
      { y: 40, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 1,
        stagger: 0.15,
        ease: "power3.out",
        delay: 0.1,
      }
    );

    // 2. Infinite Continuous Animations
    gsap.to(".spin-circle", {
      rotate: 360,
      duration: 20,
      repeat: -1,
      ease: "none",
    });

    gsap.to(".float-icon", {
      y: -15,
      duration: 2,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });

  }, { scope: container });

  return (
    <div ref={container} className="min-h-screen bg-[#F5F5F7] text-[#1c1c1e] font-sans selection:bg-[#EBDCFF] selection:text-[#1c1c1e] overflow-x-hidden">
      
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-[#F5F5F7]/80 backdrop-blur-md border-b-0">
        <div className="flex justify-between items-center w-full px-6 py-4 max-w-[1400px] mx-auto hidden md:flex">
          <div className="font-serif text-2xl font-bold tracking-tight text-[#1c1c1e] flex items-center gap-2">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#1c1c1e]">
              <path d="M12 2L2 22h20L12 2z"></path>
            </svg>
            Aina
          </div>
          
          <div className="hidden md:flex gap-8 items-center bg-white/50 backdrop-blur-lg px-8 py-3 rounded-full border border-black/5 shadow-sm text-sm font-medium">
            <a className="text-[#1c1c1e]/70 hover:text-[#1c1c1e] transition-colors" href="#">Product</a>
            <a className="text-[#1c1c1e]/70 hover:text-[#1c1c1e] transition-colors" href="#">Individuals</a>
            <a className="text-[#1c1c1e]/70 hover:text-[#1c1c1e] transition-colors" href="#">Business</a>
            <a className="text-[#1c1c1e]/70 hover:text-[#1c1c1e] transition-colors" href="#">Resources</a>
          </div>

          <div className="flex gap-4 items-center">
            {isAuthenticated ? (
              <button
                onClick={() => setLocation("/dashboard")}
                className="bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff] px-5 py-2.5 rounded-full font-semibold text-sm transition-all border border-[#1c1c1e]/10 shadow-sm flex items-center gap-2"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
                Dashboard
              </button>
            ) : (
              <>
                <button
                  onClick={() => setLocation("/login")}
                  className="text-[#1c1c1e] hover:bg-black/5 px-4 py-2 rounded-full transition-colors text-sm font-semibold border border-black/20"
                >
                  Log In
                </button>
                <button
                  onClick={() => setLocation("/signup")}
                  className="bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff] px-5 py-2.5 rounded-full font-semibold text-sm transition-all border border-[#1c1c1e]/10 shadow-sm flex items-center gap-2"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                  Start Building
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-10">
        {/* Section 1: Hero */}
        <section className="relative pt-16 pb-24 px-6 md:px-12">
          <div className="max-w-[1200px] mx-auto text-center relative z-10">
            
            {/* Rotating Circular Text Element */}
            <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 lg:-translate-x-12 hidden md:flex items-center justify-center w-64 h-64 pointer-events-none">
              <div className="spin-circle absolute inset-0">
                <svg viewBox="0 0 100 100" width="100%" height="100%" className="opacity-40 text-[#1c1c1e]">
                  <path id="circlePath" d="M 50, 50 m -40, 0 a 40,40 0 1,1 80,0 a 40,40 0 1,1 -80,0" fill="transparent" />
                  <text fontSize="8" letterSpacing="2.5">
                    <textPath href="#circlePath" startOffset="0%">
                      There's been a lot of back and forth, honestly the whole thing is just going to slip.
                    </textPath>
                  </text>
                </svg>
              </div>
              <div className="w-16 h-16 bg-[#EBDCFF] rounded-full flex items-center justify-center shadow-lg border border-black/5 z-20 pointer-events-auto cursor-pointer hover:scale-105 transition-transform float-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"></path>
                  <path d="M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0 -8"></path>
                  <path d="M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0 -16"></path>
                </svg>
              </div>
            </div>

            <h1 
              className="hero-item font-serif text-[4.5rem] sm:text-[5rem] md:text-[7.5rem] leading-[0.9] text-[#1c1c1e] mb-8 will-change-transform"
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Don't code, <span className="italic font-normal">just build</span>
            </h1>
            
            <p className="hero-item text-[#1c1c1e]/70 text-lg sm:text-xl md:text-2xl max-w-2xl mx-auto font-medium mb-12 will-change-transform">
              The AI platform that turns your knowledge into clear, actionable automations in every app—no engineering degree required.
            </p>
            
            <div className="hero-item flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button onClick={() => setLocation("/builder")} className="bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff] px-8 py-4 rounded-xl font-bold text-lg transition-all border border-[#1c1c1e]/20 shadow-sm flex items-center gap-3 w-full sm:w-auto justify-center group overflow-hidden relative">
                <span className="absolute w-0 h-full bg-[#1c1c1e]/5 left-0 top-0 transition-all group-hover:w-full"></span>
                <svg className="relative z-10" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                <span className="relative z-10">Start for Free</span>
              </button>
            </div>
            
            <div className="hero-item mt-6 text-[#1c1c1e]/50 text-sm font-semibold tracking-wide uppercase">
              Available on WhatsApp, Web, and Messenger
            </div>
            
            <div className="hero-item w-12 border-t-4 border-black/20 mx-auto mt-16 rounded-full"></div>
          </div>
        </section>

        {/* Section 2: Dark Panel */}
        <section className="px-4 md:px-8 mt-12 w-full max-w-[1400px] mx-auto reveal-up">
          <div className="bg-[#1c1c1e] rounded-[3rem] p-10 md:p-24 relative overflow-hidden text-[#F5F5F7]">
            <div className="max-w-[800px] relative z-10">
              
              <div className="tags-container flex flex-wrap gap-3 mb-10">
                {['WhatsApp', 'Facebook Messenger', 'Web Widget', 'REST API', 'iOS'].map((platform) => (
                  <div key={platform} className="tag-item px-5 py-2.5 rounded-full border border-white/20 text-sm font-semibold flex items-center gap-2 bg-white/5 backdrop-blur-sm shadow-sm">
                    <div className="w-2.5 h-2.5 rounded-full bg-white"></div>
                    {platform}
                  </div>
                ))}
              </div>

              <h2 className="font-serif text-[3.5rem] md:text-[5.5rem] leading-[1.05] mb-8 tracking-tight" style={{ fontFamily: "'Playfair Display', serif" }}>
                Automate faster in all your channels,<br className="hidden md:block"/> on any platform
              </h2>

              <p className="text-xl md:text-2xl text-white/70 max-w-lg leading-relaxed">
                Seamless AI deployment in every customer interaction within seconds. Zero code required.
              </p>
              
            </div>
            
            {/* Absolute positioning element like Wispr */}
            <div className="float-icon absolute right-16 bottom-16 md:right-32 md:bottom-32 w-24 h-24 bg-[#EBDCFF] rounded-full flex items-center justify-center shadow-2xl z-20 pointer-events-auto cursor-pointer">
               <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#1c1c1e" strokeWidth="1.5">
                  <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"></path>
                  <path d="M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0 -8"></path>
                  <path d="M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0 -16"></path>
                </svg>
            </div>
          </div>
        </section>

        {/* Section 3: Faster than typing */}
        <section className="py-24 px-6 overflow-hidden bg-[#F5F5F7]">
          <div className="max-w-[1000px] mx-auto text-center draw-trigger">
            <h2 className="reveal-up font-serif text-[4rem] sm:text-[4.5rem] md:text-[6.5rem] leading-[1.1] tracking-tight relative inline-block text-[#1c1c1e]" style={{ fontFamily: "'Playfair Display', serif" }}>
              4x faster <span className="relative inline-block z-10">
                than manual replies
                {/* SVG Underline */}
                <svg className="absolute w-[110%] h-12 -bottom-4 -left-4 text-[#EBDCFF] -z-10" viewBox="0 0 300 30" preserveAspectRatio="none">
                  <path className="draw-line" d="M5,25 Q150,5 295,20" fill="none" stroke="currentColor" strokeWidth="8" strokeLinecap="round" />
                </svg>
              </span>
            </h2>
            
            <p className="reveal-up mt-16 text-xl md:text-2xl text-[#1c1c1e]/70 max-w-3xl mx-auto leading-relaxed">
              Automation that finally works is here. Aina lets you build, test, deploy, 
              and serve at the speed of thought, outperforming manual customer support queues entirely.
            </p>

            <div className="reveal-up flex flex-col sm:flex-row justify-center gap-4 mt-16">
              <button className="bg-white border border-black/20 text-[#1c1c1e] hover:bg-black/5 px-8 py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-colors">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                Try Aina
              </button>
              <button className="bg-[#EBDCFF] border border-[#1c1c1e]/20 text-[#1c1c1e] hover:bg-[#d8bfff] px-8 py-4 rounded-xl font-bold transition-colors">
                Start Building Free
              </button>
            </div>
          </div>
        </section>

        {/* Section 4: How It Works */}
        <section className="how-it-works py-20 px-6 lg:px-12 bg-white rounded-t-[3rem] shadow-[0_-10px_40px_rgba(0,0,0,0.03)] border-t border-black/5 relative z-20">
          <div className="max-w-[1400px] mx-auto">
            <h2 className="reveal-up font-serif text-[4rem] text-[#1c1c1e] text-center mb-16" style={{ fontFamily: "'Playfair Display', serif" }}>
              Build in <span className="italic">minutes</span>
            </h2>

            <div className="grid md:grid-cols-3 gap-8 px-4">
               {/* Card 1 */}
               <div className="hiw-card bg-[#1c1c1e] rounded-3xl p-10 text-[#F5F5F7] shadow-2xl relative">
                  <div className="absolute -top-6 -left-6 w-16 h-16 bg-[#EBDCFF] text-[#1c1c1e] rounded-full flex items-center justify-center text-3xl font-serif border border-black/10">1</div>
                  <h3 className="text-2xl font-serif mb-4" style={{ fontFamily: "'Playfair Display', serif" }}>Ingest Knowledge</h3>
                  <p className="text-white/70 leading-relaxed text-lg">Upload PDFs, scrape your website, or sync with your helpdesk. Aina understands your business deeply.</p>
               </div>

               {/* Card 2 */}
               <div className="hiw-card bg-[#1c1c1e] rounded-3xl p-10 text-[#F5F5F7] shadow-2xl relative">
                  <div className="absolute -top-6 -left-6 w-16 h-16 bg-[#EBDCFF] text-[#1c1c1e] rounded-full flex items-center justify-center text-3xl font-serif border border-black/10">2</div>
                  <h3 className="text-2xl font-serif mb-4" style={{ fontFamily: "'Playfair Display', serif" }}>Design Flow</h3>
                  <p className="text-white/70 leading-relaxed text-lg">Use the visual node editor to set rules, conditions, and persona tones to ensure perfect brand voice.</p>
               </div>

               {/* Card 3 */}
               <div className="hiw-card bg-[#1c1c1e] rounded-3xl p-10 text-[#F5F5F7] shadow-2xl relative">
                  <div className="absolute -top-6 -left-6 w-16 h-16 bg-[#EBDCFF] text-[#1c1c1e] rounded-full flex items-center justify-center text-3xl font-serif border border-black/10">3</div>
                  <h3 className="text-2xl font-serif mb-4" style={{ fontFamily: "'Playfair Display', serif" }}>Deploy Everywhere</h3>
                  <p className="text-white/70 leading-relaxed text-lg">With a single click, push your AI assistant live to WhatsApp, Messenger, and a floating web widget.</p>
               </div>
            </div>
          </div>
        </section>

        {/* Section 5: Made for You Container */}
        <section className="px-4 md:px-8 max-w-[1400px] mx-auto mt-12 mb-20 reveal-up">
            <div className="bg-[#1c1c1e] rounded-[3rem] p-10 md:p-24 text-[#F5F5F7] grid md:grid-cols-2 gap-16 relative overflow-hidden">
                 
                {/* Background graphic touch */}
                 <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#EBDCFF] rounded-full mix-blend-overlay opacity-10 blur-3xl"></div>

                 <div className="float-icon absolute left-8 -top-8 w-20 h-20 bg-[#EBDCFF] rounded-full flex items-center justify-center shadow-2xl z-20 pointer-events-auto cursor-pointer">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1c1c1e" strokeWidth="1.5">
                        <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"></path>
                        <path d="M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0 -8"></path>
                        <path d="M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0 -16"></path>
                    </svg>
                </div>
                
                <div className="relative z-10 flex flex-col justify-center">
                   <h2 className="font-serif text-[4.5rem] leading-[1] text-[#F5F5F7] mb-12" style={{ fontFamily: "'Playfair Display', serif" }}>
                        Aina is made <br/>
                        <span className="italic font-normal text-[#EBDCFF]">for you</span>
                   </h2>
                   
                   <div className="flex flex-wrap gap-4">
                       <button className="bg-[#EBDCFF] text-[#1c1c1e] font-semibold px-6 py-3 rounded-full shadow-lg">Automation</button>
                       <button className="bg-white/10 border border-white/20 text-white font-semibold px-6 py-3 rounded-full hover:bg-white/20 transition-colors backdrop-blur-md">Sales Teams</button>
                       <button className="bg-white/10 border border-white/20 text-white font-semibold px-6 py-3 rounded-full hover:bg-white/20 transition-colors backdrop-blur-md">Support</button>
                   </div>
                </div>

                <div className="relative z-10 flex flex-col justify-center mt-10 md:mt-0">
                    <h3 className="font-serif text-3xl mb-6 text-white" style={{ fontFamily: "'Playfair Display', serif" }}>
                        Aina for <span className="text-[#EBDCFF] italic">Efficiency</span>
                    </h3>
                    <p className="text-white/70 text-lg md:text-xl leading-relaxed mb-10">
                        Your workflows deserve a shortcut. Aina supports anyone who feels slowed down by manual coding by turning knowledge into direct automations using RAG and LLMs.
                    </p>
                    <div className="h-64 sm:h-80 w-full bg-[#F5F5F7] rounded-3xl p-6 flex flex-col justify-center items-center shadow-inner relative overflow-hidden group">
                        
                        <svg className="absolute w-full h-full opacity-10 text-black top-20 left-10 transition-transform group-hover:scale-105" viewBox="0 0 200 200">
                           <path d="M10,10 Q50,90 190,50 T100,190" fill="none" stroke="currentColor" strokeWidth="4"></path>
                        </svg>

                        <div className="float-icon w-56 h-32 bg-[#EBDCFF] border border-black/10 rounded-2xl transform -rotate-3 shadow-xl relative z-10 flex items-center justify-center text-[#1c1c1e] text-2xl font-serif font-bold tracking-tight">
                            Reduces Workload
                        </div>
                    </div>
                </div>
            </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="w-full py-16 px-8 md:px-16 max-w-[1400px] mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-16 border-t border-black/10 pt-16 relative">
           
           <div className="float-icon absolute left-0 -top-10 w-16 h-16 bg-[#EBDCFF] rounded-full flex items-center justify-center shadow-lg border border-black/5 z-20 pointer-events-auto cursor-pointer">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1c1c1e" strokeWidth="1.5">
                  <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"></path>
                  <path d="M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0 -8"></path>
                  <path d="M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0 -16"></path>
                </svg>
            </div>

          <div className="md:col-span-2">
            <h4 className="font-serif text-3xl text-[#1c1c1e] mb-6 tracking-tight" style={{ fontFamily: "'Playfair Display', serif" }}>Aina AI</h4>
            <p className="text-[#1c1c1e]/60 text-lg max-w-sm mb-6">
                Redefining the speed of communication for businesses worldwide. The standard in no-code platform tools.
            </p>
          </div>

          <div>
            <h4 className="font-serif text-2xl text-[#1c1c1e]/60 mb-8 tracking-tight" style={{ fontFamily: "'Playfair Display', serif" }}>Product</h4>
            <ul className="space-y-4 font-medium text-[#1c1c1e]/80">
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">What's New</a></li>
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Use Cases</a></li>
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Aina for Startups</a></li>
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Aina for Non-Profits</a></li>
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Web Widget</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-serif text-2xl text-[#1c1c1e]/60 mb-8 tracking-tight" style={{ fontFamily: "'Playfair Display', serif" }}>Resources</h4>
            <ul className="space-y-4 font-medium text-[#1c1c1e]/80">
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Workflows</a></li>
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Vibe Coding</a></li>
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Talk to Support</a></li>
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Talk to Sales</a></li>
              <li><a className="hover:text-[#1c1c1e] transition-colors" href="#">Help Center</a></li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}
