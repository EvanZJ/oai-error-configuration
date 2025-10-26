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
5. Keep JSON schema consistent (if producing full config) only with modified parameter from original cu_gnb.json file.
6. Name files `cu_case_01.json` … `cu_case_n.json` under the output folder.
7. Optional flags: --seed <int> for reproducibility; --format full|delta.
8. If schema constraints exist for the key (e.g., allowed enum), generate errors that violate those constraints.
9. YOU CANNOT CREATE ANY PYTHON SCRIPT / AUTOMATION SCRIPT IN ANY PROGRAMMING LANGUAGE AT ALL, YOU DO IT BY YOUR OWN, ADD 1 `cu_case_***.json` FILE WHICH CONSISTS OF THE BASELINE `cu_gnb.conf` FILE BUT ONE PARAM IS MODIFIED
10. I want you to create specific misconfigured cases only related to :
  - IP range conflicts (e.g., overlapping or unreachable subnet definitions).
  - Frequency misalignment (e.g., mismatched SSB or PRACH frequencies).
  - Timing misalignment (e.g., inconsistent Tadv / T2a parameters).
  - Unreachable elements or wrong routing definitions (e.g., DU cannot reach AMF or RU due to gateway misconfiguration).
## Return

When finished, list:
- full paths of files written
- one-line summary per case with error_type