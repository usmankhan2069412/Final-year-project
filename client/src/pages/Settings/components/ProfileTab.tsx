import { useState, useEffect } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { toast } from "sonner";
import gsap from "gsap";
import { Button } from "../../../components/ui/button";

interface UserMeResponse {
  user: {
    id: string;
    email: string;
    full_name: string | null;
    auth_provider: string;
  };
  active_organization: {
    id: string;
    slug: string;
    owner_id: string;
  };
}

export default function ProfileTab() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [orgSlug, setOrgSlug] = useState("");
  const [isOwner, setIsOwner] = useState(false);

  const [initialData, setInitialData] = useState<{
    fullName: string;
    email: string;
    orgSlug: string;
  } | null>(null);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch("http://localhost:8000/api/v1/users/me", { headers });
      if (!res.ok) {
        throw new Error("Failed to load user profile.");
      }

      const data: UserMeResponse = await res.json();
      const profileInfo = {
        fullName: data.user.full_name || "",
        email: data.user.email || "",
        orgSlug: data.active_organization?.slug || "",
      };

      setFullName(profileInfo.fullName);
      setEmail(profileInfo.email);
      setOrgSlug(profileInfo.orgSlug);
      setInitialData(profileInfo);
      setIsOwner(data.user.id === data.active_organization?.owner_id);
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Error retrieving profile details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleDiscard = () => {
    if (initialData) {
      setFullName(initialData.fullName);
      setEmail(initialData.email);
      setOrgSlug(initialData.orgSlug);
      toast.info("Changes discarded");
    }
  };

  const handleSave = async () => {
    if (!fullName.trim()) {
      toast.error("Full Name is required");
      return;
    }
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.error("Valid email address is required");
      return;
    }
    if (!orgSlug.trim()) {
      toast.error("Organization Slug is required");
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch("http://localhost:8000/api/v1/users/me", {
        method: "PUT",
        headers,
        body: JSON.stringify({
          full_name: fullName,
          email: email,
          org_slug: orgSlug,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to update profile settings.");
      }

      const data: UserMeResponse = await res.json();
      const updatedProfile = {
        fullName: data.user.full_name || "",
        email: data.user.email || "",
        orgSlug: data.active_organization?.slug || "",
      };

      setFullName(updatedProfile.fullName);
      setEmail(updatedProfile.email);
      setOrgSlug(updatedProfile.orgSlug);
      setInitialData(updatedProfile);
      setIsOwner(data.user.id === data.active_organization?.owner_id);
      toast.success("Profile updated successfully!");

      window.dispatchEvent(new Event("profile-updated"));
      window.dispatchEvent(
        new CustomEvent("new-notification", {
          detail: {
            title: "Profile Updated",
            details: "Your profile details have been saved successfully.",
          },
        })
      );

      // Premium success micro-animation
      gsap.fromTo(
        ".profile-card",
        { scale: 0.99, opacity: 0.9 },
        { scale: 1, opacity: 1, duration: 0.4, ease: "power2.out" }
      );
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Failed to save profile changes");
      
      // Error shake animation
      gsap.to(".profile-card", {
        x: -6,
        duration: 0.05,
        repeat: 5,
        yoyo: true,
        ease: "power1.inOut",
        onComplete: () => {
          gsap.set(".profile-card", { clearProps: "x" });
        },
      });
    } finally {
      setSubmitting(false);
    }
  };



  const hasChanges =
    initialData &&
    (fullName !== initialData.fullName ||
      email !== initialData.email ||
      orgSlug !== initialData.orgSlug);

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div>
          <div className={`h-10 rounded-lg w-1/3 mb-2 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          <div className={`h-4 rounded-lg w-1/2 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
        </div>
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-8">
            <div className={`w-24 h-24 rounded-3xl ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
            <div className="space-y-3 flex-grow w-full">
              <div className={`h-6 rounded-lg w-1/3 ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
              <div className={`h-4 rounded-lg w-1/2 ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
              <div className={`h-3 rounded-lg w-1/4 ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className={`h-3 rounded-lg w-1/4 ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
              <div className={`h-12 rounded-xl w-full ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
            </div>
            <div className="space-y-2">
              <div className={`h-3 rounded-lg w-1/4 ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
              <div className={`h-12 rounded-xl w-full ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <div className={`h-3 rounded-lg w-1/8 ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
              <div className={`h-12 rounded-xl w-full ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(
    fullName || "User"
  )}&background=EBDCFF&color=1c1c1e&bold=true&size=100`;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h2
          className={`text-[2rem] font-serif font-bold mb-2 ${c("text-[#1c1c1e]", "text-white")}`}
          style={{ fontFamily: "'Playfair Display', serif" }}
        >
          Profile Settings
        </h2>
        <p className={`text-[15px] font-medium ${c("text-[#1c1c1e]/60", "text-white/50")}`}>
          Update your personal information and workspace details.
        </p>
      </div>

      {/* Avatar + Name */}
      <div
        className={`profile-card rounded-[2rem] border p-4 sm:p-8 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <div className="flex flex-col sm:flex-row items-center sm:items-start text-center sm:text-left gap-6 mb-8">
          <div className="relative flex-shrink-0">
            <div
              className={`w-24 h-24 rounded-3xl border-4 flex items-center justify-center overflow-hidden shadow-sm ${
                isDark ? "bg-[#2a2a2e] border-white/5" : "bg-black/5 border-white"
              }`}
            >
              <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
            </div>

          </div>
          <div className="flex-1 min-w-0">
            <h3 className={`text-[22px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>
              {fullName || "User Profile"}
            </h3>
            <p className={`text-[14px] font-medium mt-1 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              Workspace: {orgSlug || "No active organization"}
            </p>
            <p
              className={`text-[10px] uppercase tracking-widest font-bold mt-2 ${c(
                "text-[#1c1c1e]/40",
                "text-white/30"
              )}`}
            >
              Role: {isOwner ? "Owner" : "Member"}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label
              className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c(
                "text-[#1c1c1e]/50",
                "text-[#85948b]"
              )}`}
            >
              Full Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
              }`}
            />
          </div>
          <div>
            <label
              className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c(
                "text-[#1c1c1e]/50",
                "text-[#85948b]"
              )}`}
            >
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
              }`}
            />
          </div>
          <div className="md:col-span-2">
            <label
              className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c(
                "text-[#1c1c1e]/50",
                "text-[#85948b]"
              )}`}
            >
              Organization Slug (Workspace)
            </label>
            <input
              type="text"
              value={orgSlug}
              onChange={(e) => setOrgSlug(e.target.value)}
              placeholder="e.g. aina-ai"
              className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
              }`}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-4">
        <button
          onClick={handleDiscard}
          disabled={!hasChanges || submitting}
          className={`px-6 py-3 rounded-xl font-bold text-[14px] transition-all cursor-pointer disabled:opacity-30 disabled:pointer-events-none ${
            isDark
              ? "text-white/60 hover:text-white hover:bg-white/5"
              : "text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-black/5"
          }`}
        >
          Discard
        </button>
        <Button
          onClick={handleSave}
          loading={submitting}
          disabled={!hasChanges}
          className={`px-6 py-3 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-95 cursor-pointer ${
            isDark
              ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
              : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
          }`}
        >
          {submitting ? "Saving…" : "Save Changes"}
        </Button>
      </div>
    </div>
  );
}

