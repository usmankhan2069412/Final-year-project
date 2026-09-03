# Component Evaluation Report: Grounded Generator & Faithfulness

* **Date:** 2026-09-03 17:31:34
* **Total Samples:** 4
* **Faithfulness Score (Groundedness):** 100.00%
* **Answer Relevance Score:** 97.50%
* **Persona Tone Adherence:** 97.50%
* **Average Latency:** 2480.67 ms

## Detailed Generation Results
| ID | Language | Question | Faithfulness | Relevance | Persona | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| gen_01 | en | "What is your refund policy?" | 1.00 | 1.00 | 1.00 | 4185.54 ms |
| gen_02 | roman_urdu | "Starter plan ki price aur bot limit kya hai?" | 1.00 | 1.00 | 0.90 | 2242.04 ms |
| gen_03 | en | "How do you prevent data leaks between different customer organizations?" | 1.00 | 1.00 | 1.00 | 1767.74 ms |
| gen_04 | urdu | "واٹس ایپ کنیکٹ کرنے کے لیے کیا درکار ہے؟" | 1.00 | 0.90 | 1.00 | 1727.37 ms |

## Sample Answers & Judge Breakdown

### Test Case [gen_01]: What is your refund policy?
* **Generated Answer:** Our refund policy is as follows:

- Customers can request a full refund within 14 days of purchase.
- The total API requests must be below 100 for the refund to be applicable.
- For Enterprise plans, custom terms apply as per the Service Level Agreement (SLA).

If you have any further questions, feel free to ask!
* **Faithfulness:** `1.00` — _The generated answer accurately reflects the refund policy stated in the context without introducing any unsupported claims._
* **Relevance:** `1.00` — _The answer directly addresses the user's question about the refund policy clearly and concisely, providing specific details about the conditions for refunds._
* **Persona:** `1.00` — _The answer is professional, helpful, and concise, aligning perfectly with the persona traits of Aina Support._
---

### Test Case [gen_02]: Starter plan ki price aur bot limit kya hai?
* **Generated Answer:** Starter plan ki price $15 per month hai aur is mein aapko 3 chatbots aur 500 documents ki limit milti hai.
* **Faithfulness:** `1.00` — _The generated answer accurately reflects the information provided in the context regarding the price and limits of the Starter plan._
* **Relevance:** `1.00` — _The answer directly addresses the user's question by providing the price of the starter plan and the limits on chatbots and documents clearly and concisely._
* **Persona:** `0.90` — _The answer provides information in a friendly manner, but it lacks a more empathetic tone that aligns with the persona traits._
---

### Test Case [gen_03]: How do you prevent data leaks between different customer organizations?
* **Generated Answer:** To prevent data leaks between different customer organizations, we implement the following measures:

- **PostgreSQL Row-Level Security (RLS)**: All database tables enforce RLS tied to the organization ID (org_id). This ensures that users can only access data that belongs to their specific organization.

- **Multi-Tenant Vector Searches**: These searches are strictly filtered by both chatbot ID and org_id, which helps to further isolate data access between different customers.

These security measures are designed to maintain data integrity and confidentiality across different organizations.
* **Faithfulness:** `1.00` — _All claims in the generated answer are directly supported by the context provided. The answer accurately describes the use of PostgreSQL Row-Level Security and multi-tenant vector searches as measures to prevent data leaks, which are explicitly mentioned in the context._
* **Relevance:** `1.00` — _The answer directly addresses the user's question by providing specific measures implemented to prevent data leaks between different customer organizations, clearly explaining how each measure contributes to data security._
* **Persona:** `1.00` — _The answer aligns perfectly with the persona of Aina Security Bot, demonstrating technical knowledge and precision in describing security measures._
---

### Test Case [gen_04]: واٹس ایپ کنیکٹ کرنے کے لیے کیا درکار ہے؟
* **Generated Answer:** واٹس ایپ کنیکٹ کرنے کے لیے آپ کو درج ذیل چیزیں درکار ہیں:

- **واٹس ایپ ٹوکن**: یہ آپ کو چینل سیٹنگز میں درج کرنا ہوگا۔
- **فون نمبر آئی ڈی**: یہ بھی چینل سیٹنگز میں شامل کرنا ضروری ہے۔

اگر آپ کو مزید مدد کی ضرورت ہو تو براہ کرم بتائیں!
* **Faithfulness:** `1.00` — _The generated answer accurately reflects the requirements for connecting WhatsApp as stated in the context, with no unsupported claims._
* **Relevance:** `0.90` — _The answer directly addresses the user's question by listing the necessary items to connect WhatsApp. It is clear and concise, though it could be slightly more specific about what a 'واٹس ایپ ٹوکن' and 'فون نمبر آئی ڈی' are._
* **Persona:** `1.00` — _The response is polite and helpful, providing clear instructions for connecting WhatsApp, which aligns with the persona traits of Aina Helper._
---
