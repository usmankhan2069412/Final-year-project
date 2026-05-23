import { useState, useEffect } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { toast } from "sonner";

interface SubscriptionPlan {
  id: string;
  name: string;
  price_pkr: number;
  max_bots: number | null;
  max_messages_per_month: number | null;
  max_members: number | null;
  features: string[];
  is_popular: boolean;
}

interface SubscriptionUsage {
  bots_used: number;
  messages_used: number;
  members_count: number;
}

interface Subscription {
  id: string;
  plan: SubscriptionPlan;
  status: string;
  period_start: string;
  period_end: string;
  usage: SubscriptionUsage;
}

interface BillingHistoryItem {
  id: string;
  date: string;
  amount: number;
  status: string;
  invoice: string;
}

export default function UsageBillingTab() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [history, setHistory] = useState<BillingHistoryItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [updatingPlanId, setUpdatingPlanId] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      // 1. Fetch current subscription & usage
      const subRes = await fetch("http://localhost:8000/api/v1/billing/subscription", { headers });
      if (!subRes.ok) {
        throw new Error("Failed to load subscription details.");
      }
      const subData: Subscription = await subRes.json();
      setSubscription(subData);

      // 2. Fetch billing history
      const historyRes = await fetch("http://localhost:8000/api/v1/billing/history", { headers });
      if (historyRes.ok) {
        const historyData: BillingHistoryItem[] = await historyRes.json();
        setHistory(historyData);
      }

      // 3. Fetch available plans
      const plansRes = await fetch("http://localhost:8000/api/v1/billing/plans", { headers });
      if (plansRes.ok) {
        const plansData: SubscriptionPlan[] = await plansRes.json();
        setPlans(plansData);
      }
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Error retrieving billing details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubscribe = async (planId: string) => {
    setUpdatingPlanId(planId);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch("http://localhost:8000/api/v1/billing/subscribe", {
        method: "POST",
        headers,
        body: JSON.stringify({ plan_id: planId }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to update subscription.");
      }

      const updatedSub: Subscription = await res.json();
      setSubscription(updatedSub);
      toast.success(`Successfully switched to the ${updatedSub.plan.name} plan!`);
      window.dispatchEvent(
        new CustomEvent("new-notification", {
          detail: {
            title: "Plan Upgraded",
            details: `Successfully switched to the ${updatedSub.plan.name} plan.`,
          },
        })
      );
      setIsModalOpen(false);

      // Refresh billing history after plan change
      const historyRes = await fetch("http://localhost:8000/api/v1/billing/history", { headers });
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setHistory(historyData);
      }
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Failed to upgrade subscription");
    } finally {
      setUpdatingPlanId(null);
    }
  };

  const daysRemaining = (periodEndStr: string) => {
    const diffTime = new Date(periodEndStr).getTime() - new Date().getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

  const renderUsageBar = (label: string, used: number, total: number | null) => {
    if (!subscription) return null;
    const isUnlimited = total === null;
    const pct = isUnlimited ? 0 : Math.min(100, Math.round((used / total) * 100));

    return (
      <div key={label}>
        <div className="flex justify-between text-[14px] mb-3">
          <span className={`font-semibold ${c("text-[#1c1c1e]/70", "text-[#bbcac0]")}`}>
            {label}
          </span>
          <span className={`font-bold ${c("text-[#1c1c1e]", "text-white")}`}>
            {used.toLocaleString()} / {isUnlimited ? "Unlimited" : total.toLocaleString()}
          </span>
        </div>
        <div className={`w-full h-2 rounded-full overflow-hidden shadow-inner ${c("bg-black/5", "bg-[#131317]")}`}>
          <div
            className={`h-full rounded-full transition-all ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}
            style={{ width: `${isUnlimited ? 5 : pct}%` }}
          ></div>
        </div>
        <p className={`text-right text-[11px] font-bold mt-2 ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
          {isUnlimited ? "Unlimited quota" : `${pct}% used · Resets in ${daysRemaining(subscription.period_end)} days`}
        </p>
      </div>
    );
  };

  if (loading || !subscription) {
    return (
      <div className="space-y-8 animate-pulse">
        {/* Header */}
        <div>
          <div className={`h-10 rounded-lg w-1/3 mb-2 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          <div className={`h-4.5 rounded-lg w-1/2 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
        </div>

        {/* Current Plan Card */}
        <div className={`rounded-[2rem] border p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-6 ${isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-sm"}`}>
          <div className="space-y-3 flex-1">
            <div className={`h-3 w-20 rounded ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
            <div className={`h-6 w-36 rounded-lg ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
            <div className={`h-4 w-48 rounded-lg ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
          </div>
          <div className={`h-12 w-32 rounded-xl ${isDark ? "bg-[#2a2a2e]" : "bg-black/10"}`} />
        </div>

        {/* Resource Consumption Card */}
        <div className={`rounded-[2rem] border p-6 sm:p-8 space-y-6 ${isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-sm"}`}>
          <div className={`h-6 w-48 rounded-lg ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-3">
                <div className="flex justify-between">
                  <div className={`h-4 w-28 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  <div className={`h-4 w-20 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                </div>
                <div className={`w-full h-2 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                <div className={`h-3.5 w-40 rounded self-end ml-auto ${isDark ? "bg-white/5" : "bg-black/5"}`} />
              </div>
            ))}
          </div>
        </div>

        {/* Billing History Card */}
        <div className={`rounded-[2rem] border p-6 sm:p-8 space-y-6 ${isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-sm"}`}>
          <div className={`h-6 w-36 rounded-lg ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className={`border-b ${isDark ? "border-white/[0.06] text-white/30" : "border-black/5 text-black/30"}`}>
                  <th className="pb-3 pr-4 text-[11px] font-bold uppercase tracking-widest">Invoice</th>
                  <th className="pb-3 px-4 text-[11px] font-bold uppercase tracking-widest">Date</th>
                  <th className="pb-3 px-4 text-[11px] font-bold uppercase tracking-widest">Amount</th>
                  <th className="pb-3 pl-4 text-right text-[11px] font-bold uppercase tracking-widest">Status</th>
                </tr>
              </thead>
              <tbody>
                {[1, 2].map((i) => (
                  <tr key={i}>
                    <td className="py-4 pr-4">
                      <div className={`h-4 w-28 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                    </td>
                    <td className="py-4 px-4">
                      <div className={`h-4 w-20 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                    </td>
                    <td className="py-4 px-4">
                      <div className={`h-4 w-24 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                    </td>
                    <td className="py-4 pl-4 text-right">
                      <div className={`w-16 h-5 rounded-full ml-auto ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h2
          className={`text-[2rem] font-serif font-bold mb-2 ${
            c("text-[#1c1c1e]", "text-white")
          }`}
          style={{ fontFamily: "'Playfair Display', serif" }}
        >
          Usage & Billing
        </h2>
        <p
          className={`text-[15px] font-medium ${
            c("text-[#1c1c1e]/60", "text-white/50")
          }`}
        >
          Monitor your resource consumption and subscription plan.
        </p>
      </div>

      {/* Plan card */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 relative overflow-hidden shadow-md ${
          isDark
            ? "bg-[#1f1f23] border-[#EBDCFF]/30"
            : "bg-[#1c1c1e] border-black text-[#F5F5F7]"
        }`}
      >
        <div
          className={`absolute top-0 left-0 w-full h-1 ${
            isDark ? "bg-gradient-to-r from-[#EBDCFF] to-transparent" : "bg-[#EBDCFF]"
          }`}
        ></div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div>
            <p
              className={`text-[11px] font-bold uppercase tracking-[0.2em] mb-2 ${
                isDark ? "text-[#EBDCFF]" : "text-[#EBDCFF]/80"
              }`}
            >
              Current Plan
            </p>
            <h3 className="text-[1.75rem] font-serif font-bold">{subscription.plan.name}</h3>
            <p className={`text-[14px] font-medium mt-1 ${isDark ? "text-white/70" : "text-white/60"}`}>
              {subscription.plan.price_pkr === 0 
                ? "Free plan" 
                : `PKR ${subscription.plan.price_pkr.toLocaleString()} / month`}
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className={`px-6 py-3 rounded-xl font-bold text-[14px] transition-all shadow-sm w-full sm:w-auto cursor-pointer ${
              isDark
                ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                : "bg-white text-[#1c1c1e] hover:bg-black/5"
            }`}
          >
            Change Plan
          </button>
        </div>
      </div>

      {/* Usage bars */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 space-y-8 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <h3
          className={`text-[18px] font-serif font-bold ${
            c("text-[#1c1c1e]", "text-white")
          }`}
        >
          Resource Consumption
        </h3>
        <div className="space-y-6">
          {renderUsageBar("Chatbots Created", subscription.usage.bots_used, subscription.plan.max_bots)}
          {renderUsageBar("Monthly Messages Sent", subscription.usage.messages_used, subscription.plan.max_messages_per_month)}
          {renderUsageBar("Team Members Added", subscription.usage.members_count, subscription.plan.max_members)}
        </div>
      </div>

      {/* Billing History / Invoices */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <h3 className={`text-[18px] font-serif font-bold mb-6 ${c("text-[#1c1c1e]", "text-white")}`}>
          Billing History
        </h3>
        {history.length === 0 ? (
          <p className={`text-[14px] font-medium text-center py-6 ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
            No past invoices or payment history.
          </p>
        ) : (
          <div className="overflow-x-auto no-scrollbar">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className={`border-b text-[11px] font-bold uppercase tracking-widest ${c("text-[#1c1c1e]/40 border-black/5", "text-white/30 border-white/[0.06]")}`}>
                  <th className="pb-3 pr-4">Invoice</th>
                  <th className="pb-3 px-4">Date</th>
                  <th className="pb-3 px-4">Amount</th>
                  <th className="pb-3 pl-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/[0.03] dark:divide-white/[0.03]">
                {history.map((item) => (
                  <tr key={item.id} className={`text-[13px] font-medium ${c("text-[#1c1c1e]/80", "text-white/70")}`}>
                    <td className="py-4 pr-4 font-mono">{item.invoice}</td>
                    <td className="py-4 px-4">{new Date(item.date).toLocaleDateString()}</td>
                    <td className="py-4 px-4">PKR {item.amount.toLocaleString()}</td>
                    <td className="py-4 pl-4 text-right">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        item.status === "paid" 
                          ? "bg-green-500/10 text-green-500" 
                          : "bg-amber-500/10 text-amber-500"
                      }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Upgrade Plan Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsModalOpen(false)}></div>
          <div
            className={`relative w-full max-w-2xl rounded-[2rem] border p-6 sm:p-8 space-y-6 shadow-2xl z-10 overflow-y-auto max-h-[90vh] no-scrollbar ${
              isDark ? "bg-[#1f1f23] border-white/[0.08] text-white" : "bg-white border-black/10 text-[#1c1c1e]"
            }`}
          >
            <div className="flex justify-between items-center">
              <h3 className="text-[22px] font-serif font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
                Select a Subscription Plan
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className={`p-1.5 rounded-full transition-colors cursor-pointer ${
                  isDark ? "hover:bg-white/10 text-white/60" : "hover:bg-black/5 text-black/60"
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              {plans.map((p) => {
                const isCurrent = p.id === subscription.plan.id;
                const isSubmittingThis = updatingPlanId === p.id;
                return (
                  <div
                    key={p.id}
                    className={`rounded-2xl border p-5 flex flex-col justify-between relative transition-all ${
                      isCurrent 
                        ? (isDark ? "border-[#EBDCFF] bg-[#EBDCFF]/5" : "border-[#1c1c1e] bg-black/5")
                        : (isDark ? "border-white/[0.06] bg-[#131317]" : "border-black/5 bg-[#F5F5F7]")
                    }`}
                  >
                    {p.is_popular && (
                      <span className="absolute -top-2.5 right-4 px-2 py-0.5 rounded bg-[#EBDCFF] text-[#1c1c1e] text-[9px] font-bold uppercase tracking-wider shadow-sm">
                        Popular
                      </span>
                    )}

                    <div>
                      <h4 className="text-[16px] font-bold">{p.name}</h4>
                      <p className="text-[20px] font-serif font-bold mt-2">
                        {p.price_pkr === 0 ? "Free" : `PKR ${p.price_pkr.toLocaleString()}`}
                        <span className="text-[12px] font-medium font-sans text-white/50 dark:text-white/50 text-[#1c1c1e]/50 ml-1">/ mo</span>
                      </p>
                      
                      <ul className="space-y-2 mt-4 text-[12px] font-medium text-left">
                        <li className="flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[16px] text-green-500">check_circle</span>
                          <span>{p.max_bots === null ? "Unlimited Chatbots" : `${p.max_bots} Chatbots`}</span>
                        </li>
                        <li className="flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[16px] text-green-500">check_circle</span>
                          <span>{p.max_messages_per_month === null ? "Unlimited Messages" : `${p.max_messages_per_month.toLocaleString()} Msg/mo`}</span>
                        </li>
                        <li className="flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[16px] text-green-500">check_circle</span>
                          <span>{p.max_members === null ? "Unlimited Members" : `${p.max_members} Team Members`}</span>
                        </li>
                        {p.features.map((f, i) => (
                          <li key={i} className="flex items-center gap-1.5">
                            <span className="material-symbols-outlined text-[16px] text-green-500">check_circle</span>
                            <span>{f}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <button
                      disabled={isCurrent || updatingPlanId !== null}
                      onClick={() => handleSubscribe(p.id)}
                      className={`w-full mt-6 py-2.5 rounded-xl font-bold text-[12px] transition-all text-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${
                        isCurrent 
                          ? (isDark ? "bg-white/10 text-white/40" : "bg-black/10 text-[#1c1c1e]/40")
                          : (isDark ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]" : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black")
                      }`}
                    >
                      {isCurrent ? "Current Plan" : isSubmittingThis ? "Switching..." : "Choose Plan"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
