I want you to modify cases_delta.json (create it if it isn't made yet) and add each case file based on {modified_cu_path} file and {modified_du_path}.

Example delta output
[
  {
    "filename": "case_01.json",
    "cu": {
        "modified_key": "security.integrity_algorithms[0]",
        "original_value": "nia2",
        "error_value": "nia9",
        "error_type": "invalid_enum",
        "explanation": "Setting the integrity algorithm to the unknown enum ‘nia9’ will cause negotiation failure during the security negotiation phase and NAS registration rejection.",
    },
    "du": {
        "modified_key": "security.integrity_algorithms[0]",
        "original_value": "nia2",
        "error_value": "nia9",
        "error_type": "invalid_enum",
        "explanation": "Setting the integrity algorithm to the unknown enum ‘nia9’ will cause negotiation failure during the security negotiation phase and NAS registration rejection.",
    },
  }
]
