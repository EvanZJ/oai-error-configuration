You are a 5G gNodeB configuration fuzz-test expert. Given a valid JSON configuration (structure matching `\home\sionna\evan\CursorAutomation\cursor_gen_conf\baseline_conf_json\cu_gnb.json`) and the original conf `\home\sionna\evan\CursorAutomation\cursor_gen_conf\baseline_conf\cu_gnb.conf`, generate 1 (one) single-key error test case and write them to an output folder (e.g. `\home\sionna\evan\CursorAutomation\cursor_gen_conf\cu_output\json`). Follow the rules and output schema below.

## Rules

1. Modify exactly one key per case (single-key error). Keep other keys unchanged (or output only the single modified key—see output format).
2. Produce 1 (one) distinct case, covering different error categories.
3. Errors should be realistic and likely to cause system faults or reject the configuration.
4. Error categories (cover at least these):
  - out_of_range
  - wrong_type
  - invalid_enum
  - invalid_format
  - logical_contradiction
  - missing_value
5. Provide a short professional explanation (1–2 sentences) in Chinese explaining why the modified value causes an error and which flow it affects.
6. Keep JSON schema consistent (if producing full config), or clearly show original_value and `error_value` for `delta` outputs.
7. Name files `cu_case_01.json` … `cu_case_n.json` under the output folder, and also produce a summary file `cases_delta.json.`. STEP BY STEP, FIRST YOU CREATE THE `cu_case_***.json`, THEN YOU MODIFY THE `cases_delta.json` FILE. If the cu_case_***.json exists, please continue the numbering. Do not forget to update cases_delta.json file too.
8. Optional flags: --seed <int> for reproducibility; --format full|delta.
9. If schema constraints exist for the key (e.g., allowed enum), generate errors that violate those constraints.
c
Example delta output
[
  {
    "filename": "case_01.json",
    "modified_key": "security.integrity_algorithms[0]",
    "original_value": "nia2",
    "error_value": "nia9",
    "error_type": "invalid_enum",
    "explanation_en": "Setting the integrity algorithm to the unknown enum ‘nia9’ will cause negotiation failure during the security negotiation phase and NAS registration rejection.",
    "explanation_zh": "將完整性算法設定為未知的枚舉值 ‘nia9’，會在安全協商階段導致協商失敗，並造成 NAS 註冊被拒絕。"
  }
]
10. YOU CANNOT CREATE ANY PYTHON SCRIPT / AUTOMATION SCRIPT IN ANY PROGRAMMING LANGUAGE AT ALL, YOU DO IT BY YOUR OWN, ADD 1 `cu_case_***.json` FILE THEN MODIFY THE `cases_delta.json` FILE AND ONLY APPEND THE CREATED FILE DETAILS, DO NOT REMOVE ANY PREVIOUS ONES.
11. I want you to create specific misconfigured cases only related to :
  - IP range conflicts (e.g., overlapping or unreachable subnet definitions).
  - Frequency misalignment (e.g., mismatched SSB or PRACH frequencies).
  - Timing misalignment (e.g., inconsistent Tadv / T2a parameters).
  - Unreachable elements or wrong routing definitions (e.g., DU cannot reach AMF or RU due to gateway misconfiguration).
## Return

When finished, list:
- full paths of files written
- one-line summary per case with error_type