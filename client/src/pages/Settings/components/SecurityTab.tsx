import { useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { toast } from "sonner";
import { useNotifications } from "../../../contexts/NotificationContext";
import gsap from "gsap";

const getDeviceFromUA = () => {
  const ua = navigator.userAgent;
  let os = "Device";
  let icon = "devices";

  if (/windows/i.test(ua)) {
    os = "Windows PC";
    icon = "desktop_windows";
  } else if (/macintosh|mac os x/i.test(ua)) {
    os = "MacBook Pro";
    icon = "laptop_mac";
  } else if (/linux/i.test(ua)) {
    os = "Linux PC";
    icon = "desktop_windows";
  } else if (/iphone|ipad|ipod/i.test(ua)) {
    os = "iOS Device";
    icon = "smartphone";
  } else if (/android/i.test(ua)) {
    os = "Android Device";
    icon = "smartphone";
  }

  let browser = "";
  if (/chrome|crios/i.test(ua) && !/edge|edg/i.test(ua) && !/opr/i.test(ua)) {
    browser = "Chrome";
  } else if (/firefox|fxios/i.test(ua)) {
    browser = "Firefox";
  } else if (/safari/i.test(ua) && !/chrome|crios/i.test(ua)) {
    browser = "Safari";
  } else if (/edge|edg/i.test(ua)) {
    browser = "Edge";
  } else if (/opr/i.test(ua)) {
    browser = "Opera";
  }

  return {
    name: browser ? `${browser} on ${os}` : os,
    icon
  };
};

export default function SecurityTab() {
  const { isDark } = useTheme();
  const { fetchNotifications } = useNotifications();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  // States
  const [mfaEnabled, setMfaEnabled] = useState(true);
  const [devices, setDevices] = useState(() => {
    const current = getDeviceFromUA();
    return [
      { id: 1, device: current.name, loc: "Current Session", icon: current.icon, active: true },
      { id: 2, device: "Mobile App Session", loc: "Karachi, PK", icon: "smartphone", active: false },
    ];
  });

  // Modal States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const toggleMfa = () => {
    const nextState = !mfaEnabled;
    setMfaEnabled(nextState);
    toast.success(
      nextState
        ? "Two-Factor Authentication enabled successfully."
        : "Two-Factor Authentication disabled."
    );
  };

  const handleRevokeDevice = (id: number, deviceName: string) => {
    setDevices((prev) => prev.filter((d) => d.id !== id));
    toast.success(`Session for ${deviceName} has been successfully revoked.`);
  };

  const handleOpenModal = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword) {
      toast.error("Current password is required");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("New password must be at least 8 characters long");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match");
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

      const res = await fetch("http://localhost:8000/api/v1/users/me/password", {
        method: "PUT",
        headers,
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to change password.");
      }

      toast.success("Password changed successfully!");
      fetchNotifications();
      setIsModalOpen(false);
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Failed to reset password.");
      
      // Error shake animation
      gsap.to(".password-modal-content", {
        x: -6,
        duration: 0.05,
        repeat: 5,
        yoyo: true,
        ease: "power1.inOut",
        onComplete: () => {
          gsap.set(".password-modal-content", { clearProps: "x" });
        },
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h2
          className={`text-[2rem] font-serif font-bold mb-2 ${c("text-[#1c1c1e]", "text-white")}`}
          style={{ fontFamily: "'Playfair Display', serif" }}
        >
          Security Center
        </h2>
        <p className={`text-[15px] font-medium ${c("text-[#1c1c1e]/60", "text-white/50")}`}>
          Manage authentication, devices and access controls.
        </p>
      </div>

      <div
        className={`rounded-[2rem] border p-4 sm:p-8 space-y-6 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <div
          className={`flex flex-row items-center justify-between p-4 sm:p-6 rounded-2xl border gap-4 ${
            isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
          }`}
        >
          <div className="min-w-0">
            <h3 className={`text-[15px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>
              Two-Factor Authentication
            </h3>
            <p className={`text-[13px] font-medium mt-1.5 max-w-sm ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              Protect your account with an extra layer via Authenticator app.
            </p>
          </div>
          {/* Toggle Switch */}
          <button
            onClick={toggleMfa}
            aria-label="Toggle two-factor authentication"
            className={`w-12 h-6 rounded-full relative cursor-pointer outline-none transition-all flex-shrink-0 ${
              mfaEnabled
                ? isDark
                  ? "bg-[#EBDCFF]"
                  : "bg-[#1c1c1e]"
                : "bg-black/10 dark:bg-white/10"
            }`}
          >
            <div
              className={`absolute top-1 w-4 h-4 rounded-full transition-all shadow-sm ${
                mfaEnabled
                  ? `right-1 ${isDark ? "bg-[#1c1c1e]" : "bg-[#F5F5F7]"}`
                  : `left-1 ${isDark ? "bg-white/40" : "bg-black/30"}`
              }`}
            ></div>
          </button>
        </div>

        <button
          onClick={handleOpenModal}
          className={`w-full py-4 rounded-xl font-bold text-[14px] flex items-center justify-center gap-2 transition-all border cursor-pointer ${
            isDark
              ? "bg-[#131317] border-white/[0.06] hover:bg-[#2a2a2e] text-white"
              : "bg-[#F5F5F7] border-black/5 hover:bg-black/5 text-[#1c1c1e]"
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">lock_reset</span>
          Change Password
        </button>
      </div>

      <div
        className={`rounded-[2rem] border p-4 sm:p-8 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <div>
          <h3 className={`text-[18px] font-serif font-bold mb-1.5 ${c("text-[#1c1c1e]", "text-white")}`}>
            Authorized Devices
          </h3>
          <p className={`text-[13px] font-medium mb-6 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
            These are the devices and browsers that have recently logged into your account. You can revoke any session that you do not recognize.
          </p>
        </div>
        {devices.length === 0 ? (
          <p className={`text-[14px] font-medium text-center py-6 ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
            No authorized devices tracked.
          </p>
        ) : (
          <div className="space-y-4">
            {devices.map((d) => (
              <div
                key={d.id}
                className={`flex items-center justify-between p-4 sm:p-5 rounded-2xl border transition-colors gap-3 ${
                  isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
                }`}
              >
                <div className="flex items-center gap-3 sm:gap-4 min-w-0">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      isDark ? "bg-white/5" : "bg-white shadow-sm"
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined text-[20px] ${c(
                        "text-[#1c1c1e]/60",
                        "text-[#85948b]"
                      )}`}
                    >
                      {d.icon}
                    </span>
                  </div>
                  <div className="min-w-0">
                    <p className={`text-[14px] font-bold truncate ${c("text-[#1c1c1e]", "text-white")}`}>
                      {d.device}
                    </p>
                    <p
                      className={`text-[12px] font-medium mt-0.5 truncate ${c(
                        "text-[#1c1c1e]/50",
                        "text-[#85948b]"
                      )}`}
                    >
                      {d.loc} •{" "}
                      <span
                        className={`font-bold ${
                          d.active
                            ? c("text-[#1c1c1e]", "text-[#EBDCFF]")
                            : c("text-[#1c1c1e]/40", "text-white/30")
                        }`}
                      >
                        {d.active ? "Active Now" : "14h ago"}
                      </span>
                    </p>
                  </div>
                </div>
                {!d.active && (
                  <button
                    onClick={() => handleRevokeDevice(d.id, d.device)}
                    className={`text-[12px] font-bold px-3 py-1.5 rounded-lg transition-colors flex-shrink-0 cursor-pointer ${c(
                      "text-red-600 hover:bg-red-50",
                      "text-[#ffb4ab] hover:bg-[#ffb4ab]/10"
                    )}`}
                  >
                    Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Password Reset Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Glassmorphic overlay */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={handleCloseModal}
          ></div>

          {/* Modal box */}
          <div
            className={`password-modal-content relative w-full max-w-md rounded-[2rem] border p-6 sm:p-8 space-y-6 shadow-2xl transition-all scale-100 z-10 ${
              isDark ? "bg-[#1f1f23] border-white/[0.08] text-white" : "bg-white border-black/10 text-[#1c1c1e]"
            }`}
          >
            <div className="flex justify-between items-center">
              <h3 className="text-[22px] font-serif font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
                Change Password
              </h3>
              <button
                onClick={handleCloseModal}
                className={`p-1.5 rounded-full transition-colors cursor-pointer ${
                  isDark ? "hover:bg-white/10 text-white/60" : "hover:bg-black/5 text-black/60"
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handlePasswordSubmit} className="space-y-5">
              <div>
                <label htmlFor="currentPassword" className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Current Password
                </label>
                <input
                  id="currentPassword"
                  name="current_password"
                  autoComplete="current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className={`w-full rounded-xl px-4 py-3 text-[14px] font-medium outline-none transition-all shadow-inner ${
                    isDark
                      ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                      : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                  }`}
                />
              </div>

              <div>
                <label htmlFor="newPassword" className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  New Password
                </label>
                <input
                  id="newPassword"
                  name="new_password"
                  autoComplete="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className={`w-full rounded-xl px-4 py-3 text-[14px] font-medium outline-none transition-all shadow-inner ${
                    isDark
                      ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                      : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                  }`}
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Confirm New Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirm_password"
                  autoComplete="new-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={`w-full rounded-xl px-4 py-3 text-[14px] font-medium outline-none transition-all shadow-inner ${
                    isDark
                      ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                      : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                  }`}
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className={`px-5 py-2.5 rounded-xl font-bold text-[14px] transition-all cursor-pointer ${
                    isDark ? "hover:bg-white/5 text-white/60" : "hover:bg-black/5 text-[#1c1c1e]/60"
                  }`}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`px-5 py-2.5 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-95 cursor-pointer ${
                    isDark
                      ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                      : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
                  }`}
                >
                  {submitting ? "Updating…" : "Update Password"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

