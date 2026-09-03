# Component Evaluation Report: Intent Classification Router

* **Date:** 2026-09-03 17:19:45
* **Total Samples:** 25
* **Overall Accuracy:** 100.00%
* **Macro F1:** 1.0000
* **Average Latency:** 3352.16 ms

## Per-Class Performance
| Intent | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| **RAG_LOOKUP** | 1.00 | 1.00 | 1.00 | 6 |
| **CONVERSATIONAL** | 1.00 | 1.00 | 1.00 | 6 |
| **AGENT_HANDOFF** | 1.00 | 1.00 | 1.00 | 4 |
| **FRUSTRATION** | 1.00 | 1.00 | 1.00 | 4 |
| **HISTORY_TRANSFORM** | 1.00 | 1.00 | 1.00 | 5 |

## Confusion Matrix
```
------------------------------------------------------------------------------------------------------------------
Actual \ Pred      RAG_LOOKUP         CONVERSATIONAL     AGENT_HANDOFF      FRUSTRATION        HISTORY_TRANSFORM  
------------------------------------------------------------------------------------------------------------------
RAG_LOOKUP         6                  0                  0                  0                  0                  
CONVERSATIONAL     0                  6                  0                  0                  0                  
AGENT_HANDOFF      0                  0                  4                  0                  0                  
FRUSTRATION        0                  0                  0                  4                  0                  
HISTORY_TRANSFORM  0                  0                  0                  0                  5                  
------------------------------------------------------------------------------------------------------------------
```

## Detailed Test Case Results
| ID | Language | Message | Expected | Predicted | Status | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| rt_01 | en | What is the refund policy of Aina AI? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 22729.43 ms |
| rt_02 | en | How much does the professional tier cost per month? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 2860.07 ms |
| rt_03 | roman_urdu | Aina platform mein document upload karne ka tareeqa kya hai? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 4448.69 ms |
| rt_04 | urdu | کیا واٹس ایپ انٹیگریشن سپورٹڈ ہے؟ | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 3639.18 ms |
| rt_05 | en | Can you tell me about the team member limits on starter plan? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 2981.09 ms |
| rt_06 | en | Hello, good morning! | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 3511.81 ms |
| rt_07 | roman_urdu | Assalam o alaikum | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 0.09 ms |
| rt_08 | urdu | السلام علیکم، آپ کیسے ہیں؟ | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 2741.54 ms |
| rt_09 | en | Thank you so much for your help! | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 5740.93 ms |
| rt_10 | roman_urdu | Bohot shukriya aap ka | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 3889.29 ms |
| rt_11 | roman_urdu | Allah hafiz, see you later | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 3545.65 ms |
| rt_12 | en | I want to talk to a human support agent | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 6.14 ms |
| rt_13 | roman_urdu | Mujhe kisi human agent se connect karo | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 0.08 ms |
| rt_14 | en | Transfer me to your customer care representative | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 0.07 ms |
| rt_15 | urdu | مجھے کسی انسان سے بات کرنی ہے | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 3122.37 ms |
| rt_16 | en | This is totally useless, you don't understand anything! | FRUSTRATION | FRUSTRATION | ✅ PASS | 3241.84 ms |
| rt_17 | roman_urdu | Bakwas service hai, bilkul samajh nahi aa raha tumhein | FRUSTRATION | FRUSTRATION | ✅ PASS | 4094.29 ms |
| rt_18 | en | You are wasting my time, stupid bot | FRUSTRATION | FRUSTRATION | ✅ PASS | 3762.44 ms |
| rt_19 | urdu | یہ بالکل فضول بوٹ ہے | FRUSTRATION | FRUSTRATION | ✅ PASS | 3199.8 ms |
| rt_20 | en | Please translate the above answer into Roman Urdu | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 0.16 ms |
| rt_21 | roman_urdu | Is ko thora short aur concise kar do | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 4106.2 ms |
| rt_22 | en | Make it in bullet points | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 0.11 ms |
| rt_23 | en | Summarize the previous response in 2 sentences | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 0.11 ms |
| rt_24 | urdu | اس کا خلاصہ لکھیں | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 3003.91 ms |
| rt_25 | en | How does pgvector hybrid search work with reciprocal rank fusion? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 3178.65 ms |
