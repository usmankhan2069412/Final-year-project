# Component Evaluation Report: Intent Classification Router

* **Date:** 2026-09-22 12:23:02
* **Total Samples:** 52
* **Overall Accuracy:** 98.08%
* **Macro F1:** 0.9808
* **Average Latency:** 423.63 ms

## Per-Class Performance
| Intent | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| **RAG_LOOKUP** | 0.93 | 1.00 | 0.96 | 13 |
| **CONVERSATIONAL** | 1.00 | 1.00 | 1.00 | 11 |
| **AGENT_HANDOFF** | 1.00 | 1.00 | 1.00 | 11 |
| **FRUSTRATION** | 1.00 | 1.00 | 1.00 | 8 |
| **HISTORY_TRANSFORM** | 1.00 | 0.89 | 0.94 | 9 |

## Confusion Matrix
```
------------------------------------------------------------------------------------------------------------------
Actual \ Pred      RAG_LOOKUP         CONVERSATIONAL     AGENT_HANDOFF      FRUSTRATION        HISTORY_TRANSFORM  
------------------------------------------------------------------------------------------------------------------
RAG_LOOKUP         13                 0                  0                  0                  0                  
CONVERSATIONAL     0                  11                 0                  0                  0                  
AGENT_HANDOFF      0                  0                  11                 0                  0                  
FRUSTRATION        0                  0                  0                  8                  0                  
HISTORY_TRANSFORM  1                  0                  0                  0                  8                  
------------------------------------------------------------------------------------------------------------------
```

## Detailed Test Case Results
| ID | Language | Message | Expected | Predicted | Status | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| rt_01 | en | What is the refund policy of Aina AI? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 3084.42 ms |
| rt_02 | en | How much does the professional tier cost per month? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 351.9 ms |
| rt_03 | roman_urdu | Aina platform mein document upload karne ka tareeqa kya hai? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 404.6 ms |
| rt_04 | urdu | کیا واٹس ایپ انٹیگریشن سپورٹڈ ہے؟ | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 358.33 ms |
| rt_05 | en | Can you tell me about the team member limits on starter plan? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 355.55 ms |
| rt_06 | en | Hello, good morning! | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 403.59 ms |
| rt_07 | roman_urdu | Assalam o alaikum | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 3.2 ms |
| rt_08 | urdu | السلام علیکم، آپ کیسے ہیں؟ | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 693.75 ms |
| rt_09 | en | Thank you so much for your help! | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 457.9 ms |
| rt_10 | roman_urdu | Boht shukriya aap ka | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 401.36 ms |
| rt_11 | roman_urdu | Kya haal chaal hain? | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 388.13 ms |
| rt_12 | en | I need to speak with an agent right now | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 353.27 ms |
| rt_13 | roman_urdu | Mujhe kisi human se connect karo | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 361.72 ms |
| rt_14 | en | Transfer me to your customer care representative | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 381.16 ms |
| rt_15 | urdu | مجھے کسی انسان سے بات کرنی ہے | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 371.33 ms |
| rt_16 | en | This is totally useless, you don't understand anything! | FRUSTRATION | FRUSTRATION | ✅ PASS | 351.78 ms |
| rt_17 | roman_urdu | Bakwas service hai, bilkul samajh nahi aa raha tumhein | FRUSTRATION | FRUSTRATION | ✅ PASS | 413.01 ms |
| rt_18 | en | You are wasting my time, stupid bot | FRUSTRATION | FRUSTRATION | ✅ PASS | 407.95 ms |
| rt_19 | urdu | یہ بالکل فضول بوٹ ہے | FRUSTRATION | FRUSTRATION | ✅ PASS | 358.72 ms |
| rt_20 | en | Please translate the above answer into Roman Urdu | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 388.17 ms |
| rt_21 | roman_urdu | Is ko thora short aur concise kar do | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 387.74 ms |
| rt_22 | en | Make it in bullet points | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 374.24 ms |
| rt_23 | en | Summarize the previous response in 2 sentences | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 374.71 ms |
| rt_24 | urdu | اس کا خلاصہ لکھیں | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 354.26 ms |
| rt_25 | en | How does pgvector hybrid search work with reciprocal rank fusion? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 394.5 ms |
| rt_26 | roman_urdu | Hi, refund policy kya hai? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 342.71 ms |
| rt_27 | roman_urdu | Salam bhai, admission criteria kya hai? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 377.44 ms |
| rt_28 | en | Hey there, how can I change my email address? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 369.28 ms |
| rt_29 | en | AOA, what are the office timings for support? | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 496.28 ms |
| rt_30 | roman_urdu | Hi, isko short kar do | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 375.26 ms |
| rt_31 | roman_urdu | Salam, bullet points mein samjha do | HISTORY_TRANSFORM | RAG_LOOKUP | ❌ FAIL | 348.05 ms |
| rt_32 | en | Hello, can you rewrite this in Urdu script? | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 381.01 ms |
| rt_33 | roman_urdu | refnd polcy kya ha | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 422.98 ms |
| rt_34 | roman_urdu | admisn kse mile ga | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 344.68 ms |
| rt_35 | roman_urdu | paswrd reset kse krn | RAG_LOOKUP | RAG_LOOKUP | ✅ PASS | 382.07 ms |
| rt_36 | roman_urdu | shrt krdo isko | HISTORY_TRANSFORM | HISTORY_TRANSFORM | ✅ PASS | 380.79 ms |
| rt_37 | roman_urdu | Wah, kya zabardast bot hai bilkul jawab nahi diya | FRUSTRATION | FRUSTRATION | ✅ PASS | 357.08 ms |
| rt_38 | en | Great job, you completely failed to answer! | FRUSTRATION | FRUSTRATION | ✅ PASS | 367.65 ms |
| rt_39 | roman_urdu | Tumhari wajah se mera sara time waste ho gaya | FRUSTRATION | FRUSTRATION | ✅ PASS | 365.49 ms |
| rt_40 | en | Stop giving me automated useless bot answers | FRUSTRATION | FRUSTRATION | ✅ PASS | 349.12 ms |
| rt_41 | roman_urdu | Mujhe insan se baat karni hai, tumse nahi | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 423.12 ms |
| rt_42 | en | I want to speak with a real supervisor right now | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 356.9 ms |
| rt_43 | roman_urdu | Ye theek nahi laga mujhe | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 348.67 ms |
| rt_44 | roman_urdu | Ye theek nahi laga mujhe | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 544.38 ms |
| rt_45 | en | I am feeling quite confused and stressed about this | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 365.41 ms |
| rt_46 | en | I am feeling quite confused and stressed about this | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 382.27 ms |
| rt_47 | en | 👍 | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 359.96 ms |
| rt_48 | en | ok thanks | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 364.88 ms |
| rt_49 | roman_urdu | shukriya bhai | CONVERSATIONAL | CONVERSATIONAL | ✅ PASS | 0.12 ms |
| rt_50 | en | Connect me to customer support manager immediately | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 360.07 ms |
| rt_51 | roman_urdu | Admin se baat karao | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 346.83 ms |
| rt_52 | en | Can I speak with a real person right now? | AGENT_HANDOFF | AGENT_HANDOFF | ✅ PASS | 340.89 ms |
