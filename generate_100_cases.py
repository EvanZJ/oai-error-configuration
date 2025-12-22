import json

cu_keys = [
    {"key": "gNBs.gNB_ID", "original": "0xe00", "type": "hex"},
    {"key": "gNBs.local_s_portc", "original": 501, "type": "int"},
    {"key": "gNBs.amf_ip_address.ipv4", "original": "192.168.70.132", "type": "ip"},
    {"key": "security.ciphering_algorithms", "original": ["nea3", "nea2", "nea1", "nea0"], "type": "array"},
    {"key": "log_config.global_log_level", "original": "info", "type": "enum"},
    {"key": "gNBs.tr_s_preference", "original": "f1", "type": "enum"},
    {"key": "gNBs.SCTP.SCTP_INSTREAMS", "original": 2, "type": "int"},
    {"key": "gNBs.NETWORK_INTERFACES.GNB_PORT_FOR_S1U", "original": 2152, "type": "int"},
    {"key": "gNBs.plmn_list.mcc", "original": 1, "type": "int"},
    {"key": "Num_Threads_PUSCH", "original": 8, "type": "int"}
]

du_keys = [
    {"key": "gNBs[0].gNB_ID", "original": "0xe00", "type": "hex"},
    {"key": "gNBs[0].local_n_portc", "original": 500, "type": "int"},
    {"key": "gNBs[0].servingCellConfigCommon[0].physCellId", "original": 0, "type": "int"},
    {"key": "gNBs[0].pdsch_AntennaPorts_XP", "original": 2, "type": "int"},
    {"key": "log_config.global_log_level", "original": "info", "type": "enum"},
    {"key": "gNBs[0].tr_s_preference", "original": "local_L1", "type": "enum"},
    {"key": "gNBs[0].SCTP.SCTP_INSTREAMS", "original": 2, "type": "int"},
    {"key": "RUs[0].nb_tx", "original": 4, "type": "int"},
    {"key": "gNBs[0].plmn_list[0].mcc", "original": 1, "type": "int"},
    {"key": "MACRLCs[0].num_cc", "original": 1, "type": "int"}
]

error_types = [
    {"name": "invalid_type", "desc": "Invalid data type"},
    {"name": "out_of_range_negative", "desc": "Out of range negative value"},
    {"name": "null_value", "desc": "Null value"},
    {"name": "empty_string", "desc": "Empty string"},
    {"name": "invalid_enum", "desc": "Invalid enumeration value"},
    {"name": "invalid_ip", "desc": "Invalid IP address format"},
    {"name": "too_large", "desc": "Value too large"},
    {"name": "zero_value", "desc": "Zero value where positive required"},
    {"name": "wrong_array", "desc": "Wrong array type"},
    {"name": "invalid_hex", "desc": "Invalid hexadecimal format"}
]

def get_error_value(original, typ, error_name):
    if error_name == "invalid_type":
        if typ in ["int", "hex"]:
            return "invalid_string"
        elif typ == "string":
            return 12345
        elif typ == "array":
            return "not_an_array"
        elif typ == "enum":
            return 999
        elif typ == "ip":
            return 12345
    elif error_name == "out_of_range_negative":
        if typ in ["int"]:
            return -1
        else:
            return original  # or skip, but for now
    elif error_name == "null_value":
        return None
    elif error_name == "empty_string":
        return ""
    elif error_name == "invalid_enum":
        return "invalid_enum_value"
    elif error_name == "invalid_ip":
        return "999.999.999.999"
    elif error_name == "too_large":
        if typ in ["int"]:
            return 999999999
        else:
            return original
    elif error_name == "zero_value":
        return 0
    elif error_name == "wrong_array":
        if typ == "array":
            return "string_instead_of_array"
        else:
            return []
    elif error_name == "invalid_hex":
        return "0xgggg"
    return original

cases = []
for i in range(1, 101):
    cu_idx = (i-1) % 10
    du_idx = ((i-1) // 10) % 10
    error_idx = ((i-1) // 10) % 10
    
    cu = cu_keys[cu_idx]
    du = du_keys[du_idx]
    error = error_types[error_idx]
    
    cu_error_value = get_error_value(cu["original"], cu["type"], error["name"])
    du_error_value = get_error_value(du["original"], du["type"], error["name"])
    
    case = {
        "filename": f"case_{i:03d}.json",
        "cu": {
            "modified_key": cu["key"],
            "original_value": cu["original"],
            "error_value": cu_error_value,
            "error_type": error["name"],
            "explanation": f"Setting {error['desc']} for {cu['key']} causes runtime failure in CU module"
        },
        "du": {
            "modified_key": du["key"],
            "original_value": du["original"],
            "error_value": du_error_value,
            "error_type": error["name"],
            "explanation": f"Setting {error['desc']} for {du['key']} causes runtime failure in DU module"
        }
    }
    cases.append(case)

print(json.dumps(cases, indent=2))