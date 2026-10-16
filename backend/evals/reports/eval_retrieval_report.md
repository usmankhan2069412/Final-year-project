# Component Evaluation Report: Hybrid Retrieval & RRF Fusion

* **Date:** 2026-10-04 19:40:44
* **Corpus Chunks Indexed:** 51
* **Total Benchmark Queries:** 51

## Strategy Ablation Comparison
| Retrieval Strategy | Hit Rate @ 1 | Hit Rate @ 3 | Hit Rate @ 5 | MRR @ 3 | Precision @ 3 | Recall @ 3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dense Only** | 82.4% | 100.0% | 100.0% | 0.9052 | 0.3791 | 98.0% |
| **Sparse Only** | 29.4% | 62.7% | 74.5% | 0.4281 | 0.2157 | 61.1% |
| **Hybrid RRF (Ours)** | 68.6% | 92.2% | 96.1% | 0.7941 | 0.3268 | 87.3% |

## Detailed Query Retrieval Results
| ID | Query Type | Query Text | Ground Truth | Top 3 Hybrid Retrieved | Hybrid Hit @ 3 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ret_iac_001 | sparse_keyword | "What is IAC's phone number?" | `['iac_005']` | `['iac_002', 'iac_029', 'iac_030']` | ❌ MISS |
| ret_iac_002 | sparse_keyword | "What is the total credit hours for Bachelor of Architecture?" | `['iac_041']` | `['iac_041', 'iac_032', 'iac_047']` | ✅ HIT |
| ret_iac_003 | semantic_dense | "How many schools does IAC have?" | `['iac_004']` | `['iac_004', 'iac_001', 'iac_008']` | ✅ HIT |
| ret_iac_004 | sparse_keyword | "What is the email address for IAC?" | `['iac_005']` | `['iac_008', 'iac_005', 'iac_001']` | ✅ HIT |
| ret_iac_005 | semantic_dense | "What is the duration of Bachelor of Interior Design?" | `['iac_043']` | `['iac_025', 'iac_043', 'iac_012']` | ✅ HIT |
| ret_iac_006 | sparse_keyword | "What is the address of IAC campus?" | `['iac_030']` | `['iac_029', 'iac_030', 'iac_001']` | ✅ HIT |
| ret_iac_007 | semantic_dense | "List Master's programs at IAC." | `['iac_026']` | `['iac_026', 'iac_009', 'iac_025']` | ✅ HIT |
| ret_iac_008 | sparse_keyword | "What short courses does School of Art offer?" | `['iac_017']` | `['iac_017', 'iac_016', 'iac_015']` | ✅ HIT |
| ret_iac_009 | semantic_dense | "What are SADU Bachelor's programs?" | `['iac_012']` | `['iac_012', 'iac_025', 'iac_013']` | ✅ HIT |
| ret_iac_010 | sparse_keyword | "What is the total credit hours for Bachelor of Film and Television?" | `['iac_049']` | `['iac_049', 'iac_025', 'iac_021']` | ✅ HIT |
| ret_iac_011 | semantic_dense | "Who is the Dean of SADU?" | `['iac_011']` | `['iac_011', 'iac_051', 'iac_004']` | ✅ HIT |
| ret_iac_012 | semantic_dense | "What is IAC's mission?" | `['iac_002']` | `['iac_002', 'iac_003', 'iac_029']` | ✅ HIT |
| ret_iac_013 | hybrid | "What partnerships does IAC have?" | `['iac_006']` | `['iac_006', 'iac_008', 'iac_001']` | ✅ HIT |
| ret_iac_014 | semantic_dense | "How can prospective students apply to IAC?" | `['iac_008']` | `['iac_008', 'iac_002', 'iac_003']` | ✅ HIT |
| ret_iac_015 | hybrid | "What sports and cultural events are offered at IAC?" | `['iac_007']` | `['iac_007', 'iac_008', 'iac_028']` | ✅ HIT |
| ret_iac_016 | semantic_dense | "What facilities are available for IAC students?" | `['iac_010']` | `['iac_008', 'iac_010', 'iac_002']` | ✅ HIT |
| ret_iac_017 | semantic_dense | "What programs are offered by School of Informatics and Robotics?" | `['iac_019']` | `['iac_018', 'iac_051', 'iac_004']` | ❌ MISS |
| ret_iac_018 | hybrid | "What is the fee for Bachelor of Architecture?" | `['iac_032']` | `['iac_032', 'iac_038', 'iac_034']` | ✅ HIT |
| ret_iac_019 | hybrid | "What is the total fee for BS Computer Science?" | `['iac_035']` | `['iac_040', 'iac_035', 'iac_037']` | ✅ HIT |
| ret_iac_020 | sparse_keyword | "What is the fee for Master of Architecture?" | `['iac_036']` | `['iac_036', 'iac_031', 'iac_032']` | ✅ HIT |
| ret_iac_021 | semantic_dense | "What are the short courses at SDCA?" | `['iac_022']` | `['iac_022', 'iac_020', 'iac_014']` | ✅ HIT |
| ret_iac_022 | semantic_dense | "Who leads the School of Art?" | `['iac_015']` | `['iac_015', 'iac_004', 'iac_020']` | ✅ HIT |
| ret_iac_023 | semantic_dense | "What are the Bachelor's programs in School of Culture and Languages?" | `['iac_024']` | `['iac_024', 'iac_025', 'iac_016']` | ✅ HIT |
| ret_iac_024 | hybrid | "What is the duration and credits for BS Tourism, Hospitality & Culinary Arts?" | `['iac_045']` | `['iac_045', 'iac_012', 'iac_025']` | ✅ HIT |
| ret_iac_025 | sparse_keyword | "What is the fee for ADP Construction Management?" | `['iac_037']` | `['iac_037', 'iac_032', 'iac_027']` | ✅ HIT |
| ret_iac_026 | semantic_dense | "What is the mission of IAC regarding arts and technology?" | `['iac_002']` | `['iac_002', 'iac_003', 'iac_001']` | ✅ HIT |
| ret_iac_027 | sparse_keyword | "What are the admission portal URLs for IAC?" | `['iac_008']` | `['iac_008', 'iac_010', 'iac_031']` | ✅ HIT |
| ret_iac_028 | hybrid | "What is the total tuition fee for Bachelor of Interior Design?" | `['iac_039']` | `['iac_039', 'iac_032', 'iac_034']` | ✅ HIT |
| ret_iac_029 | semantic_dense | "What are the graduate programs at SADU?" | `['iac_013']` | `['iac_011', 'iac_013', 'iac_026']` | ✅ HIT |
| ret_iac_030 | sparse_keyword | "What is the fee for Bachelor of Graphic Design?" | `['iac_034']` | `['iac_034', 'iac_016', 'iac_033']` | ✅ HIT |
| ret_iac_031 | roman_urdu_hybrid | "IAC mein kitne schools hain aur unke naam kya hain?" | `['iac_004']` | `['iac_004', 'iac_008', 'iac_005']` | ✅ HIT |
| ret_iac_032 | hybrid | "What is the total fee for Bachelor of Fashion Design and ADP Fashion Design?" | `['iac_037', 'iac_034']` | `['iac_034', 'iac_016', 'iac_025']` | ✅ HIT |
| ret_iac_033 | hybrid | "Where is IAC located and what is the phone number?" | `['iac_030', 'iac_005']` | `['iac_001', 'iac_008', 'iac_029']` | ❌ MISS |
| ret_iac_034 | hybrid | "How many credits does B.Arch have and what are the Semester 1 courses?" | `['iac_042', 'iac_041']` | `['iac_042', 'iac_038', 'iac_039']` | ✅ HIT |
| ret_iac_035 | hybrid | "What is the fee difference between BS Computer Science and BS Interaction Design?" | `['iac_035']` | `['iac_035', 'iac_025', 'iac_037']` | ✅ HIT |
| ret_iac_036 | roman_urdu_hybrid | "IAC ka chancellor kaun hai aur Act number kya hai?" | `['iac_029']` | `['iac_029', 'iac_001', 'iac_028']` | ✅ HIT |
| ret_iac_037 | hybrid | "What are the SADU diploma courses and their durations?" | `['iac_014']` | `['iac_014', 'iac_011', 'iac_013']` | ✅ HIT |
| ret_iac_038 | semantic_dense | "List all Associate Degree Programs across IAC." | `['iac_027']` | `['iac_009', 'iac_027', 'iac_025']` | ✅ HIT |
| ret_iac_039 | hybrid | "What is the total fee for Bachelor of Game Design and Bachelor of Animation Design?" | `['iac_033']` | `['iac_033', 'iac_025', 'iac_021']` | ✅ HIT |
| ret_iac_040 | hybrid | "What events are organized by IAC and who is the Chancellor?" | `['iac_029', 'iac_028']` | `['iac_028', 'iac_029', 'iac_002']` | ✅ HIT |
| ret_iac_041 | hybrid | "What is the fee structure for all SADU Bachelor's programs?" | `['iac_032']` | `['iac_012', 'iac_025', 'iac_031']` | ❌ MISS |
| ret_iac_042 | hybrid | "What are the short courses offered by School of Art and SDCA?" | `['iac_022', 'iac_017']` | `['iac_020', 'iac_015', 'iac_017']` | ✅ HIT |
| ret_iac_043 | hybrid | "What is the total credit hours for B.Arch, B.ID, and BS Construction Management?" | `['iac_043', 'iac_044', 'iac_041']` | `['iac_044', 'iac_041', 'iac_043']` | ✅ HIT |
| ret_iac_044 | roman_urdu_hybrid | "IAC mein PhD program hai? Agar nahi to kaunse levels offered hain?" | `['iac_009']` | `['iac_008', 'iac_002', 'iac_009']` | ✅ HIT |
| ret_iac_045 | hybrid | "What is the fee for Bachelor of Film & TV and ADP Film & TV?" | `['iac_033', 'iac_037']` | `['iac_021', 'iac_033', 'iac_031']` | ✅ HIT |
| ret_iac_046 | hybrid | "What is the total fee for Master in Interior Design and Master of Architecture?" | `['iac_036']` | `['iac_032', 'iac_036', 'iac_013']` | ✅ HIT |
| ret_iac_047 | hybrid | "What is the difference between SADU and SOA programs?" | `['iac_012', 'iac_016']` | `['iac_011', 'iac_013', 'iac_012']` | ✅ HIT |
| ret_iac_048 | roman_urdu_hybrid | "IAC ki website par kaunse social media links hain?" | `['iac_005']` | `['iac_005', 'iac_008', 'iac_029']` | ✅ HIT |
| ret_iac_049 | hybrid | "What is the total fee for Bachelor of Architecture including admission and security?" | `['iac_038']` | `['iac_038', 'iac_031', 'iac_032']` | ✅ HIT |
| ret_iac_050 | sparse_keyword | "What are the course codes for B.Arch Semester 1?" | `['iac_042']` | `['iac_042', 'iac_041', 'iac_032']` | ✅ HIT |
| ret_iac_051 | sparse_keyword | "What is Dr Shazia Saqib's designation at IAC?" | `['iac_051']` | `['iac_051', 'iac_018', 'iac_029']` | ✅ HIT |
