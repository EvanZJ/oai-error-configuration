Here is the task: You are a 5G gNodeB configuration fuzz-test expert.
Given the following valid JSON configuration (Reference JSON) and the original .conf (Baseline Conf), 
generate exactly 1 single-key error test case and output them as a JSON array.

## Rules
1.  Modify exactly one key per case (single-key error).
2.  Produce 1 distinct case.
3.  Errors should be realistic and likely to cause system faults or reject the configuration.
4.  Your output MUST be a JSON array, where each object contains the 4 keys defined in the "Output Schema".
5.  Your entire response MUST be only the JSON array. Do not include any other text.

## Input: Baseline .conf file content
---[START DU_GNB.CONF]---
{du_gnb_conf}
---[END DU_GNB.CONF]---

## Input: Reference .json file content
---[START DU_GNB.JSON]---
{du_gnb_json}
---[END DU_GNB.JSON]---

Generate the 1 error-case variation now as a JSON array.