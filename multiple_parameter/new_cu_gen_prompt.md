You are a senior OpenAirInterface (OAI) gNB system engineer with deep knowledge of
configuration parsing, protocol stack interactions, and runtime state machines.

The OAI gNB source code is located at the following path:

~/evan/CursorAutomation/openairinterface5g

The baseline gNB configuration file is located at the following path:

/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/cu_gnb.conf

The reference structured configuration (JSON format) is located at the following path:

/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf_json/cu_gnb.json


You must base your reasoning on:
- The provided baseline configuration files
- The reference JSON structure
- Your engineering understanding of the OAI gNB architecture as implemented under the above path
  (including CU/DU, RRC, NGAP, F1AP, MAC, and PHY layers)

You are NOT allowed to assume any external codebase beyond this directory.

---

## Input Files

Baseline configuration (.conf):
---[START {COMPONENT}.CONF]---
{cu_gnb_conf}
---[END {COMPONENT}.CONF]---

Reference configuration (.json):
---[START {COMPONENT}.JSON]---
{cu_gnb_json}
---[END {COMPONENT}.JSON]---

---

## Task Objective

Generate exactly **100** configuration mutation cases.

Each case must satisfy ALL of the following:
1. The configuration remains **syntactically valid** and can pass OAI config parsing.
2. The modification introduces a **logical or semantic error** that will only surface at runtime.
3. The error must realistically lead to:
   - protocol handshake failure,
   - state machine inconsistency,
   - or resource allocation conflict in the OAI gNB stack.

---

## Error Generation Strategies

### 1. Logical Mutation
Create contradictions between parameters that are individually valid but mutually inconsistent
(e.g., timing relations, bandwidth vs numerology, feature enable flags vs missing dependencies).

### 2. Deep Runtime Disruption
Modify parameters that:
- Do not trigger parser errors
- But break assumptions in RRC / NGAP / F1AP procedures
- Or cause MAC/PHY scheduling and resource mapping failures

### 3. Knowledge Correlation (MANDATORY)
For every mutation, explicitly associate it with:
- A specific protocol layer or subsystem
- A known class of runtime logic (state transition, capability validation, scheduler assumption, etc.)

You must NOT fabricate non-existent modules or files.
All correlations must be consistent with common OAI gNB implementation patterns.

---

## Coverage Constraints (MUST FOLLOW)

- Generate exactly 100 cases (no more, no less).
- Do NOT modify the same configuration key more than **3 times**.
- Ensure all error categories below are covered.
- Ensure mutations span **multiple protocol layers** (not PHY-only or RRC-only).

---

## Error Categories (each case must belong to one)

- out of range
- wrong type
- invalid enum
- invalid format
- logical contradiction
- missing value

---

## Output Format (STRICT)

The output must be a valid JSON array and saved as `output.json`
under:

C:\Users\bmwlab\Desktop\option\output

Each element must strictly follow this schema:

[
  {
    "filename": "{component}_case_001.json",
    "modified_key": "path.to.the.key",
    "original_value": "val",
    "error_value": "err_val",
    "error_type": "logical contradiction",
    "affected_module": "RRC / NGAP / F1AP / MAC / PHY",
    "impact_description": "Concise engineering explanation of the expected runtime failure"
  }
]

---

## Final Rules (CRITICAL)

- You MUST generate exactly 100 cases.
- You MUST provide a plausible engineering rationale for every case.
- You MUST NOT invent arbitrary source files or logic unrelated to the OAI gNB stack.
- Diversity and realism are more important than extremity of errors.
