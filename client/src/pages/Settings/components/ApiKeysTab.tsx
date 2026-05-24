import { useState, useEffect } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { toast } from "sonner";
import { useNotifications } from "../../../contexts/NotificationContext";
import gsap from "gsap";
import { Button } from "../../../components/ui/button";

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used: string | null;
  status: "active" | "revoked";
}

export default function ApiKeysTab() {
  const { isDark } = useTheme();
  const { fetchNotifications } = useNotifications();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const [loading, setLoading] = useState(true);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch("http://localhost:8000/api/v1/settings/api-keys", { headers });
      if (!res.ok) {
        throw new Error("Failed to load API keys.");
      }
      const data = await res.json();
      setKeys(data);
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Error retrieving API keys");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) {
      toast.error("Key name is required");
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

      const res = await fetch("http://localhost:8000/api/v1/settings/api-keys", {
        method: "POST",
        headers,
        body: JSON.stringify({ name: newKeyName.trim() }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to create API key.");
      }

      const data = await res.json();
      // data.key holds the full key shown once
      const createdKeyName = newKeyName.trim();
      setCreatedKey(data.key);
      toast.success("API key created successfully!");
      fetchNotifications();
      setNewKeyName("");
      fetchKeys();
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Failed to create API key");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevokeKey = async (keyId: string, keyName: string) => {
    if (!confirm(`Are you sure you want to revoke the key "${keyName}"? This key will immediately stop working.`)) {
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`http://localhost:8000/api/v1/settings/api-keys/${keyId}`, {
        method: "DELETE",
        headers,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to revoke API key.");
      }

      toast.success(`API key "${keyName}" has been revoked.`);
      fetchNotifications();
      fetchKeys();
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Failed to revoke API key");
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  const handleOpenModal = () => {
    setCreatedKey(null);
    setNewKeyName("");
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCreatedKey(null);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h2
            className={`text-[2rem] font-serif font-bold mb-2 ${
              c("text-[#1c1c1e]", "text-white")
            }`}
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            API Keys
          </h2>
          <p
            className={`text-[15px] font-medium ${
              c("text-[#1c1c1e]/60", "text-white/50")
            }`}
          >
            Manage credentials for your deployments.
          </p>
        </div>
        <button
          onClick={handleOpenModal}
          className={`px-5 py-3 rounded-xl font-bold text-[14px] flex items-center justify-center gap-2 transition-all shadow-md w-full sm:w-auto cursor-pointer ${
            isDark
              ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
              : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          Create New Key
        </button>
      </div>

      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2].map((i) => (
            <div
              key={i}
              className={`rounded-[1.5rem] border p-4 sm:p-6 flex flex-col md:flex-row md:items-center gap-6 ${
                isDark
                  ? "bg-[#1f1f23] border-white/[0.06]"
                  : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
              }`}
            >
              {/* Icon placeholder */}
              <div className={`w-12 h-12 rounded-2xl flex-shrink-0 ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />

              {/* Info placeholders */}
              <div className="flex-grow space-y-2">
                <div className={`h-4.5 w-32 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                <div className={`h-3.5 w-48 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                <div className="flex gap-4">
                  <div className={`h-2.5 w-24 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  <div className={`h-2.5 w-24 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                </div>
              </div>

              {/* Actions placeholders */}
              <div className="flex gap-2 justify-end">
                <div className={`w-9 h-9 rounded-xl ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                <div className={`w-9 h-9 rounded-xl ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                <div className={`w-9 h-9 rounded-xl ${isDark ? "bg-white/5" : "bg-black/5"}`} />
              </div>
            </div>
          ))}
        </div>
      ) : keys.length === 0 ? (
        <div
          className={`rounded-[1.5rem] border p-8 text-center ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <span className={`material-symbols-outlined text-[48px] ${c("text-[#1c1c1e]/30", "text-white/20")}`}>key</span>
          <p className={`text-[14px] font-medium mt-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
            No API Keys generated yet. Create one to access the API.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {keys.map((k) => {
            const isRevoked = k.status === "revoked";
            return (
              <div
                key={k.id}
                className={`rounded-[1.5rem] border p-4 sm:p-6 flex flex-col md:flex-row md:items-center gap-6 transition-all ${
                  isRevoked ? "opacity-60" : ""
                } ${
                  isDark
                    ? "bg-[#1f1f23] border-white/[0.06]"
                    : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
                }`}
              >
                <div className="flex items-start md:items-center gap-4 flex-1 min-w-0">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-black/5 text-[#1c1c1e]"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[24px]">key</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3
                        className={`text-[16px] font-bold truncate ${
                          isRevoked ? "line-through" : ""
                        } ${c("text-[#1c1c1e]", "text-white")}`}
                      >
                        {k.name}
                      </h3>
                      {isRevoked && (
                        <span className="text-[9px] px-2 py-0.5 rounded bg-red-500/10 text-red-500 dark:text-red-400 font-bold uppercase tracking-wider">
                          Revoked
                        </span>
                      )}
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mt-1.5 min-w-0">
                      <code
                        className={`text-[13px] font-mono font-medium px-2 py-0.5 rounded select-all break-all overflow-x-auto no-scrollbar max-w-full block ${
                          isDark ? "bg-[#131317] text-[#85948b]" : "bg-[#F5F5F7] text-[#1c1c1e]/60"
                        }`}
                      >
                        {k.prefix}
                      </code>
                      <span className={`text-[11px] font-medium ${c("text-[#1c1c1e]/40", "text-[#85948b]")}`}>
                        Created {new Date(k.created_at).toLocaleDateString()}
                        {k.last_used && ` · Last used ${new Date(k.last_used).toLocaleDateString()}`}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 justify-end md:justify-start">
                  {!isRevoked && (
                    <>
                      <button
                        onClick={() => handleCopy(k.prefix)}
                        className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors border cursor-pointer ${
                          isDark
                            ? "border-transparent hover:bg-white/[0.04] text-white/50 hover:text-white"
                            : "border-black/5 bg-[#F5F5F7] hover:bg-black/5 text-[#1c1c1e]/60 hover:text-[#1c1c1e]"
                        }`}
                        title="Copy prefix to clipboard"
                      >
                        <span className="material-symbols-outlined text-[18px]">content_copy</span>
                      </button>
                      <button
                        onClick={() => handleRevokeKey(k.id, k.name)}
                        className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors border cursor-pointer ${
                          isDark
                            ? "border-transparent hover:bg-[#ffb4ab]/10 text-white/30 hover:text-[#ffb4ab]"
                            : "border-black/5 bg-[#F5F5F7] hover:bg-red-50 text-red-400 hover:text-red-500"
                        }`}
                        title="Revoke key"
                      >
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* API Key Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={handleCloseModal}></div>
          <div
            className={`relative w-full max-w-md rounded-[2rem] border p-6 sm:p-8 space-y-6 shadow-2xl transition-all z-10 ${
              isDark ? "bg-[#1f1f23] border-white/[0.08] text-white" : "bg-white border-black/10 text-[#1c1c1e]"
            }`}
          >
            <div className="flex justify-between items-center">
              <h3 className="text-[22px] font-serif font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
                {createdKey ? "API Key Generated" : "Create API Key"}
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

            {!createdKey ? (
              <form onSubmit={handleCreateKey} className="space-y-5">
                <div>
                  <label htmlFor="keyName" className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                    Key Name
                  </label>
                  <input
                    id="keyName"
                    name="key_name"
                    autoComplete="off"
                    spellCheck={false}
                    type="text"
                    required
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="e.g. Production_Main_V2…"
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
                  <Button
                    type="submit"
                    loading={submitting}
                    className={`px-5 py-2.5 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-95 cursor-pointer ${
                      isDark
                        ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                        : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
                    }`}
                  >
                    {submitting ? "Generating…" : "Generate Key"}
                  </Button>
                </div>
              </form>
            ) : (
              <div className="space-y-5">
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-[13px] font-medium flex items-start gap-2.5">
                  <span className="material-symbols-outlined text-[20px] flex-shrink-0">warning</span>
                  <div>
                    <span className="font-bold">Important:</span> Copy this API key now. For security reasons, you will not be able to see it again.
                  </div>
                </div>

                <div>
                  <label htmlFor="plaintextKey" className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                    Plaintext API Key
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="plaintextKey"
                      name="plaintext_key"
                      autoComplete="off"
                      spellCheck={false}
                      type="text"
                      readOnly
                      value={createdKey}
                      className={`flex-grow rounded-xl px-4 py-3 text-[13px] font-mono outline-none transition-all ${
                        isDark ? "bg-[#131317] border border-white/[0.06] text-[#EBDCFF]" : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e]"
                      }`}
                    />
                    <button
                      onClick={() => handleCopy(createdKey)}
                      className={`px-4 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
                        isDark ? "bg-white/5 hover:bg-white/10 text-white" : "bg-black/5 hover:bg-black/10 text-[#1c1c1e]"
                      }`}
                      title="Copy Key"
                    >
                      <span className="material-symbols-outlined text-[20px]">content_copy</span>
                    </button>
                  </div>
                </div>

                <div className="flex justify-end pt-3">
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className={`px-6 py-2.5 rounded-xl font-bold text-[14px] transition-all shadow-md cursor-pointer ${
                      isDark
                        ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                        : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
                    }`}
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
