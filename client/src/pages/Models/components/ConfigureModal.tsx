import { useState, memo, useCallback } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { cn } from "../../../lib/utils";
import { toast } from "sonner";
import { api } from "../../../lib/api";

interface RoutingRule {
  intent: string;
  model_target: string;
}

interface ConfigureModalProps {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  editingConfigId: string | null;
  initialRules: RoutingRule[];
  initialProviderId: string;
  availableModels: Array<{ id: string; name: string; models: string[] }>;
}

const OPENROUTER_MODELS = [
  "openai/gpt-4o",
  "openai/gpt-4o-mini",
  "anthropic/claude-3.5-sonnet",
  "anthropic/claude-3-opus",
  "google/gemini-1.5-pro",
  "meta-llama/llama-3-8b-instruct",
  "mistralai/mixtral-8x7b-instruct",
];

const POPULAR_INTENTS = [
  "General Inquiries",
  "Complex Problems",
  "Image Analysis",
  "Code Assistance",
];

interface RuleRowProps {
  rule: RoutingRule;
  index: number;
  modelOptions: string[];
  onChange: (index: number, field: keyof RoutingRule, value: string) => void;
  onRemove: (index: number) => void;
}

const RuleRow = memo(function RuleRow({ rule, index, modelOptions, onChange, onRemove }: RuleRowProps) {
  const { isDark } = useTheme();

  const handleIntentChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    onChange(index, "intent", val === "Custom" ? "" : val);
  }, [index, onChange]);

  const handleIntentInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(index, "intent", e.target.value);
  }, [index, onChange]);

  const handleModelChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    onChange(index, "model_target", val === "Custom" ? "" : val);
  }, [index, onChange]);

  const handleModelInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(index, "model_target", e.target.value);
  }, [index, onChange]);

  const handleRemove = useCallback(() => onRemove(index), [index, onRemove]);

  return (
    <div className="flex gap-3 items-center">
      <div className="flex-1">
        <label className={cn("block text-[10px] font-bold uppercase tracking-widest mb-1.5", isDark ? "text-[#85948b]" : "text-[#1c1c1e]/50")}>
          Query Type (Intent)
        </label>
        <select
          value={POPULAR_INTENTS.includes(rule.intent) ? rule.intent : "Custom"}
          onChange={handleIntentChange}
          className={cn("w-full rounded-xl px-3 py-2.5 text-[13px] font-medium outline-none border", isDark ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50" : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white")}
        >
          {POPULAR_INTENTS.map((intent) => (
            <option key={intent} value={intent}>{intent}</option>
          ))}
          <option value="Custom">Custom...</option>
        </select>
        {!POPULAR_INTENTS.includes(rule.intent) && (
          <input
            type="text"
            required
            placeholder="Type custom intent..."
            value={rule.intent}
            onChange={handleIntentInput}
            className={cn("w-full mt-1.5 rounded-xl px-3 py-2 text-[12px] font-medium outline-none border", isDark ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50" : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white")}
          />
        )}
      </div>

      <div className="flex-1">
        <label className={cn("block text-[10px] font-bold uppercase tracking-widest mb-1.5", isDark ? "text-[#85948b]" : "text-[#1c1c1e]/50")}>
          AI Model
        </label>
        <select
          value={modelOptions.includes(rule.model_target) ? rule.model_target : "Custom"}
          onChange={handleModelChange}
          className={cn("w-full rounded-xl px-3 py-2.5 text-[13px] font-medium outline-none border", isDark ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50" : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white")}
        >
          {modelOptions.map((model) => (
            <option key={model} value={model}>{model.split('/').pop() || model}</option>
          ))}
          <option value="Custom">Custom...</option>
        </select>
        {!modelOptions.includes(rule.model_target) && (
          <input
            type="text"
            required
            placeholder="e.g. meta-llama/llama-3-8b"
            value={rule.model_target}
            onChange={handleModelInput}
            className={cn("w-full mt-1.5 rounded-xl px-3 py-2 text-[12px] font-medium outline-none border", isDark ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50" : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white")}
          />
        )}
      </div>

      <button
        type="button"
        onClick={handleRemove}
        className={cn("mt-5 p-2 rounded-xl transition-colors cursor-pointer", isDark ? "hover:bg-[#ffb4ab]/10 text-red-400" : "hover:bg-red-50 text-red-500")}
      >
        <span className="material-symbols-outlined text-[20px]">delete</span>
      </button>
    </div>
  );
});

export const ConfigureModal = memo(function ConfigureModal({ open, onClose, onSaved, editingConfigId, initialRules, initialProviderId, availableModels }: ConfigureModalProps) {
  const { isDark } = useTheme();
  const [routingRules, setRoutingRules] = useState<RoutingRule[]>(initialRules);
  const [submitting, setSubmitting] = useState(false);

  const currentProviderModels = availableModels.find(p => p.id === initialProviderId)?.models || [];
  const modelOptions = currentProviderModels.length > 0 ? currentProviderModels : OPENROUTER_MODELS;

  const handleAddRule = useCallback(() => {
    setRoutingRules((prev) => [...prev, { intent: "General Inquiries", model_target: modelOptions[0] || "" }]);
  }, [modelOptions]);

  const handleRemoveRule = useCallback((index: number) => {
    setRoutingRules((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleRuleChange = useCallback((index: number, field: keyof RoutingRule, value: string) => {
    setRoutingRules((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    setSubmitting(true);
    try {
      const primaryModel = routingRules.find((r) => r.model_target.trim())?.model_target.trim() || "default";
      const rulesPayload = routingRules.map((r) => ({
        intent: r.intent.trim(),
        model_override: r.model_target.trim(),
      }));

      if (editingConfigId) {
        await api.updateConfig(editingConfigId, {
          provider_id: initialProviderId,
          model_name: primaryModel,
          routing_rules: rulesPayload,
        });
      } else {
        await api.createConfig({
          provider_id: initialProviderId,
          model_name: primaryModel,
          routing_rules: rulesPayload,
        });
      }

      toast.success(editingConfigId ? "Models updated successfully!" : "Models configured successfully!");
      onClose();
      onSaved();
    } catch (err: any) {
      toast.error(err.message || "Error saving models configuration");
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className={cn("relative w-full max-w-xl rounded-[2rem] border p-6 sm:p-8 space-y-6 shadow-2xl transition-all z-10 max-h-[90vh] overflow-y-auto no-scrollbar", isDark ? "bg-[#1f1f23] border-white/[0.08] text-white" : "bg-white border-black/10 text-[#1c1c1e]")}>
        <div className="flex justify-between items-center">
          <h3 className="text-[22px] font-serif font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
            Select Chatbot Models
          </h3>
          <button onClick={onClose} className={cn("p-1.5 rounded-full transition-colors cursor-pointer", isDark ? "hover:bg-white/10 text-white/60" : "hover:bg-black/5 text-black/60")}>
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-6">
          <div className="p-4 rounded-xl border flex items-center gap-4 bg-[#8a5cf5]/10 border-[#8a5cf5]/20">
            <span className="material-symbols-outlined text-[#8a5cf5]">info</span>
            <p className={cn("text-[13px] font-medium", isDark ? "text-white/80" : "text-[#1c1c1e]/80")}>
              You don't need to provide any API keys! Simply select the models you want to use for your chatbot.
            </p>
          </div>

          <div className="space-y-4 pt-2">
            <div className="flex items-center justify-between">
              <div>
                <h4 className={cn("text-[14px] font-bold", isDark ? "text-white" : "text-[#1c1c1e]")}>Model Configuration</h4>
                <p className={cn("text-[11px] font-medium", isDark ? "text-[#85948b]" : "text-[#1c1c1e]/50")}>
                  Select which models will handle which types of queries.
                </p>
              </div>
              <button
                type="button"
                onClick={handleAddRule}
                className={cn("px-3 py-1.5 rounded-lg border transition-all text-[11px] font-bold flex items-center gap-1 cursor-pointer", isDark ? "bg-[#EBDCFF]/10 border-[#EBDCFF]/20 text-[#EBDCFF] hover:bg-[#EBDCFF]/20" : "bg-[#1c1c1e] border-[#1c1c1e] text-[#F5F5F7] hover:bg-black")}
              >
                <span className="material-symbols-outlined text-[14px]">add</span>
                Add Model
              </button>
            </div>

            {routingRules.length === 0 ? (
              <div className={cn("p-6 rounded-xl border border-dashed text-center", isDark ? "bg-[#131317] border-white/10" : "bg-[#F5F5F7] border-black/10")}>
                <p className={cn("text-[12px] font-medium", isDark ? "text-[#85948b]" : "text-[#1c1c1e]/50")}>
                  Please select at least one model for your chatbot.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {routingRules.map((rule, idx) => (
                  <RuleRow
                    key={idx}
                    rule={rule}
                    index={idx}
                    modelOptions={modelOptions}
                    onChange={handleRuleChange}
                    onRemove={handleRemoveRule}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/[0.04]">
            <button
              type="button"
              onClick={onClose}
              className={cn("px-5 py-2.5 rounded-xl font-bold text-[14px] transition-all cursor-pointer", isDark ? "hover:bg-white/5 text-white/60" : "hover:bg-black/5 text-[#1c1c1e]/60")}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className={cn("px-5 py-2.5 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-95 cursor-pointer", isDark ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]" : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black")}
            >
              {submitting ? "Saving..." : "Save Models"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
});
