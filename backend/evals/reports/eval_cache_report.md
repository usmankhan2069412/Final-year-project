# Component Evaluation Report: Semantic Cache & Threshold Optimization (w/ Guardrails)

* **Date:** 2026-09-04 16:06:06
* **Total Test Pairs:** 36
* **Configured Threshold:** 0.65
* **Optimal Guarded Threshold:** 0.6 (Accuracy: 88.89%)

## Threshold Sweep Comparison (Baseline vs Guardrails)
| Threshold | TP (Hits) | FP (Traps) | Precision % | Recall % | Guarded Accuracy % | Raw Accuracy % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0.6** | 14 | 0 | 100.0% | 77.78% | **88.89%** | 52.78% |
| **0.65** | 12 | 0 | 100.0% | 66.67% | **83.33%** | 52.78% |
| **0.7** | 8 | 0 | 100.0% | 44.44% | **72.22%** | 47.22% |
| **0.75** | 4 | 0 | 100.0% | 22.22% | **61.11%** | 38.89% |
| **0.8** | 1 | 0 | 100.0% | 5.56% | **52.78%** | 33.33% |
| **0.85** | 1 | 0 | 100.0% | 5.56% | **52.78%** | 33.33% |

## Category Performance Breakdown (@ Threshold 0.65)
| Category | Total Pairs | Raw Acc % | Guarded Acc % | Traps Intercepted |
| :--- | :--- | :--- | :--- | :--- |
| `action_antonym` | 4 | 75.0% | **100.0%** | 1 |
| `direct_paraphrase` | 3 | 100.0% | **100.0%** | 0 |
| `entity_swap` | 4 | 25.0% | **100.0%** | 3 |
| `error_code_trap` | 1 | 0.0% | **100.0%** | 1 |
| `granularity_mismatch` | 1 | 100.0% | **100.0%** | 0 |
| `length_verbosity_mismatch` | 1 | 0.0% | **0.0%** | 0 |
| `multilingual_roman_urdu` | 4 | 50.0% | **50.0%** | 0 |
| `multilingual_urdu` | 2 | 50.0% | **50.0%** | 0 |
| `negation_trap` | 3 | 0.0% | **100.0%** | 3 |
| `numerical_quota_shift` | 3 | 0.0% | **100.0%** | 3 |
| `phrasing_variation` | 3 | 100.0% | **100.0%** | 0 |
| `synonym_substitution` | 4 | 75.0% | **75.0%** | 0 |
| `syntactic_inversion` | 2 | 50.0% | **50.0%** | 0 |
| `typo_and_casing_noise` | 1 | 100.0% | **100.0%** | 0 |

## Detailed Query Pair Results
| ID | Category | Expected | Cosine Sim | Guardrail Status | Final Outcome | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| c_01 | `direct_paraphrase` | **HIT** | `0.7745` | ✓ Compatible | HIT ✅ PASS | Direct semantic paraphrase |
| c_02 | `synonym_substitution` | **HIT** | `0.6835` | ✓ Compatible | HIT ✅ PASS | Synonym paraphrase |
| c_03 | `phrasing_variation` | **HIT** | `0.7375` | ✓ Compatible | HIT ✅ PASS | Phrasing variation |
| c_04 | `action_antonym` | **MISS** | `0.6374` | 🛡️ Blocked (Action antonym mismatch: 'upgrade' vs 'cancel') | MISS ✅ PASS | False positive trap: Upgrade vs Cancel |
| c_05 | `action_antonym` | **MISS** | `0.5685` | 🛡️ Blocked (Action antonym mismatch: 'upload' vs 'delete') | MISS ✅ PASS | False positive trap: Upload vs Delete |
| c_06 | `entity_swap` | **MISS** | `0.5284` | 🛡️ Blocked (Entity substitution mismatch: {'gpt-4o'} vs {'claude-3.5-sonnet'}) | MISS ✅ PASS | False positive trap: Different entity |
| c_07 | `multilingual_roman_urdu` | **HIT** | `0.7358` | ✓ Compatible | HIT ✅ PASS | Roman Urdu paraphrase |
| c_08 | `syntactic_inversion` | **HIT** | `0.6061` | ✓ Compatible | MISS ❌ FAIL | Inquiry vs Setup question |
| c_09 | `negation_trap` | **MISS** | `0.8625` | 🛡️ Blocked (Polarity mismatch: 'enable' vs 'disable') | MISS ✅ PASS | Negation trap: Enable vs Disable 2FA |
| c_10 | `negation_trap` | **MISS** | `0.9348` | 🛡️ Blocked (Polarity mismatch: 'with' vs 'without') | MISS ✅ PASS | Negation trap: With vs Without credit card |
| c_11 | `negation_trap` | **MISS** | `0.8695` | 🛡️ Blocked (Polarity mismatch: 'turn on' vs 'turn off') | MISS ✅ PASS | Negation trap: Turn on vs Turn off auto-renew |
| c_12 | `entity_swap` | **MISS** | `0.7928` | 🛡️ Blocked (Entity substitution mismatch: {'slack'} vs {'discord'}) | MISS ✅ PASS | Entity swap: Slack vs Discord integration |
| c_13 | `entity_swap` | **MISS** | `0.6576` | 🛡️ Blocked (Entity substitution mismatch: {'admin'} vs {'viewer'}) | MISS ✅ PASS | Entity swap: Admin vs Viewer RBAC permissions |
| c_14 | `entity_swap` | **MISS** | `0.7328` | 🛡️ Blocked (Entity substitution mismatch: {'jazzcash'} vs {'easypaisa'}) | MISS ✅ PASS | Entity swap: JazzCash vs EasyPaisa payment gateway |
| c_15 | `numerical_quota_shift` | **MISS** | `0.8622` | 🛡️ Blocked (Entity substitution mismatch: {'starter'} vs {'enterprise'}) | MISS ✅ PASS | Quota shift: Starter (3 bots) vs Enterprise limits |
| c_16 | `numerical_quota_shift` | **MISS** | `0.9122` | 🛡️ Blocked (Numeric parameter mismatch: {'7'} vs {'90'}) | MISS ✅ PASS | Parameter shift: 7-day vs 90-day analytics window |
| c_17 | `numerical_quota_shift` | **MISS** | `0.9641` | 🛡️ Blocked (Numeric parameter mismatch: {'500'} vs {'50000'}) | MISS ✅ PASS | Quota shift: Tier document threshold 500 vs 50,000 |
| c_18 | `action_antonym` | **MISS** | `0.6191` | 🛡️ Blocked (Action antonym mismatch: 'register' vs 'remove') | MISS ✅ PASS | Action antonym: Register vs Delete webhook |
| c_19 | `action_antonym` | **MISS** | `0.9371` | 🛡️ Blocked (Polarity mismatch: 'mute' vs 'unmute') | MISS ✅ PASS | Action antonym: Mute vs Unmute notifications |
| c_20 | `granularity_mismatch` | **MISS** | `0.4218` | ✓ Compatible | MISS ✅ PASS | Granularity mismatch: High-level overview vs exact chunk parameters |
| c_21 | `multilingual_roman_urdu` | **HIT** | `0.5937` | ✓ Compatible | MISS ❌ FAIL | Cross-lingual paraphrase: English vs Roman Urdu account deletion |
| c_22 | `error_code_trap` | **MISS** | `0.6647` | 🛡️ Blocked (Numeric parameter mismatch: {'401'} vs {'429'}) | MISS ✅ PASS | Technical error trap: 401 Auth failure vs 429 Rate limiting |
| c_23 | `synonym_substitution` | **HIT** | `0.5240` | ✓ Compatible | MISS ❌ FAIL | Synonym substitution: Update credit card vs enter new payment method |
| c_24 | `multilingual_roman_urdu` | **MISS** | `0.5884` | 🛡️ Blocked (Action antonym mismatch: 'update' vs 'delete') | MISS ✅ PASS | Roman Urdu trap: Update bot persona vs Permanently delete bot |
| c_25 | `multilingual_urdu` | **MISS** | `0.5407` | 🛡️ Blocked (Entity substitution mismatch: {'واٹس ایپ'} vs {'ٹیلی گرام'}) | MISS ✅ PASS | Urdu script entity trap: WhatsApp vs Telegram channel connection |
| c_26 | `direct_paraphrase` | **HIT** | `0.7678` | ✓ Compatible | HIT ✅ PASS | Direct paraphrase: On-premise self-hosted vs own private infrastructure |
| c_27 | `direct_paraphrase` | **HIT** | `0.6554` | ✓ Compatible | HIT ✅ PASS | Semantic paraphrase: Reset password vs Recover forgotten login |
| c_28 | `synonym_substitution` | **HIT** | `0.7049` | ✓ Compatible | HIT ✅ PASS | Synonym substitution: Invoices & usage vs receipts & consumption |
| c_29 | `syntactic_inversion` | **HIT** | `0.7209` | ✓ Compatible | HIT ✅ PASS | Syntactic complexity: Multi-admin permissions inquiry |
| c_30 | `length_verbosity_mismatch` | **HIT** | `0.4410` | ✓ Compatible | MISS ❌ FAIL | Verbosity mismatch: Ultra-concise keyword vs verbose polite question |
| c_31 | `phrasing_variation` | **HIT** | `0.6688` | ✓ Compatible | HIT ✅ PASS | Phrasing variation: Supported file formats with parenthetical examples |
| c_32 | `phrasing_variation` | **HIT** | `0.7845` | ✓ Compatible | HIT ✅ PASS | Configuration paraphrase: Adjust temperature & system prompt |
| c_33 | `typo_and_casing_noise` | **HIT** | `0.8820` | ✓ Compatible | HIT ✅ PASS | Typo & casing noise: Lowercase and misspelled words ('genrate', 'secert') |
| c_34 | `synonym_substitution` | **HIT** | `0.6739` | ✓ Compatible | HIT ✅ PASS | Colloquial paraphrase: Pro tier free trial vs try before charged |
| c_35 | `multilingual_roman_urdu` | **HIT** | `0.6146` | ✓ Compatible | MISS ❌ FAIL | Roman Urdu paraphrase: Naya bot create vs Fresh bot banane ka tarika |
| c_36 | `multilingual_urdu` | **HIT** | `0.3088` | ✓ Compatible | MISS ❌ FAIL | Urdu script paraphrase: Refund terms & conditions vs How to file refund request |
