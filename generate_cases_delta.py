import json
import random

cu_mods = [
    {"key": "Num_Threads_PUSCH", "original": 8, "error": -1, "type": "out of range", "exp": "Negative thread count causes allocation error in PUSCH processing module"},
    {"key": "Num_Threads_PUSCH", "original": 8, "error": 0, "type": "out of range", "exp": "Zero threads causes deadlock in PUSCH processing"},
    {"key": "Num_Threads_PUSCH", "original": 8, "error": "eight", "type": "wrong type", "exp": "String instead of number causes type error in thread configuration"},
    {"key": "gNBs.gNB_ID", "original": "0xe00", "error": "0xg00", "type": "invalid format", "exp": "Invalid hex format causes parsing error in gNB ID validation"},
    {"key": "gNBs.gNB_ID", "original": "0xe00", "error": 123, "type": "wrong type", "exp": "Number instead of string causes type mismatch in ID field"},
    {"key": "gNBs.gNB_ID", "original": "0xe00", "error": "", "type": "invalid format", "exp": "Empty string causes ID validation failure in RRC"},
    {"key": "gNBs.tracking_area_code", "original": 1, "error": -1, "type": "out of range", "exp": "Negative TAC causes RRC connection failure"},
    {"key": "gNBs.tracking_area_code", "original": 1, "error": 65536, "type": "out of range", "exp": "TAC out of valid range (0-65535) causes NGAP error"},
    {"key": "gNBs.tracking_area_code", "original": 1, "error": "one", "type": "wrong type", "exp": "String instead of number causes type error in TAC"},
    {"key": "gNBs.plmn_list.mcc", "original": 1, "error": 1000, "type": "out of range", "exp": "MCC out of range (000-999) causes PLMN mismatch in NGAP"},
    {"key": "gNBs.plmn_list.mcc", "original": 1, "error": -1, "type": "out of range", "exp": "Negative MCC causes validation error"},
    {"key": "gNBs.plmn_list.mcc", "original": 1, "error": "001", "type": "wrong type", "exp": "String instead of number causes type mismatch"},
    {"key": "gNBs.plmn_list.mnc", "original": 1, "error": 1000, "type": "out of range", "exp": "MNC out of range causes PLMN mismatch"},
    {"key": "gNBs.plmn_list.mnc", "original": 1, "error": -1, "type": "out of range", "exp": "Negative MNC causes validation error"},
    {"key": "gNBs.plmn_list.mnc", "original": 1, "error": "01", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs.nr_cellid", "original": 1, "error": -1, "type": "out of range", "exp": "Negative cell ID causes cell configuration error in RRC"},
    {"key": "gNBs.nr_cellid", "original": 1, "error": 1000000, "type": "out of range", "exp": "Cell ID out of range causes ID collision"},
    {"key": "gNBs.nr_cellid", "original": 1, "error": "cell1", "type": "wrong type", "exp": "String instead of number causes type mismatch"},
    {"key": "gNBs.local_s_portc", "original": 501, "error": -1, "type": "out of range", "exp": "Negative port causes socket binding failure"},
    {"key": "gNBs.local_s_portc", "original": 501, "error": 99999, "type": "out of range", "exp": "Port out of range causes network error"},
    {"key": "gNBs.local_s_portc", "original": 501, "error": "port501", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs.SCTP.SCTP_INSTREAMS", "original": 2, "error": 0, "type": "out of range", "exp": "Zero streams causes SCTP association failure"},
    {"key": "gNBs.SCTP.SCTP_INSTREAMS", "original": 2, "error": 100, "type": "out of range", "exp": "Too many streams causes resource exhaustion"},
    {"key": "gNBs.SCTP.SCTP_INSTREAMS", "original": 2, "error": "two", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs.amf_ip_address.ipv4", "original": "192.168.70.132", "error": "999.999.999.999", "type": "invalid format", "exp": "Invalid IP format causes AMF connection failure"},
    {"key": "gNBs.amf_ip_address.ipv4", "original": "192.168.70.132", "error": "192.168.70", "type": "invalid format", "exp": "Incomplete IP causes parsing error"},
    {"key": "gNBs.amf_ip_address.ipv4", "original": "192.168.70.132", "error": 19216870132, "type": "wrong type", "exp": "Number instead of string causes type mismatch"},
    {"key": "security.ciphering_algorithms", "original": ["nea3", "nea2", "nea1", "nea0"], "error": "nea3", "type": "wrong type", "exp": "String instead of array causes security configuration error"},
    {"key": "security.ciphering_algorithms", "original": ["nea3", "nea2", "nea1", "nea0"], "error": ["invalid"], "type": "invalid enum", "exp": "Invalid ciphering algorithm causes ciphering failure"},
    {"key": "security.ciphering_algorithms", "original": ["nea3", "nea2", "nea1", "nea0"], "error": [], "type": "missing value", "exp": "Empty array causes no ciphering available"},
    {"key": "log_config.global_log_level", "original": "info", "error": "invalid_level", "type": "invalid enum", "exp": "Invalid log level causes logging module crash"},
    {"key": "log_config.global_log_level", "original": "info", "error": 1, "type": "wrong type", "exp": "Number instead of string causes type error"},
    {"key": "log_config.global_log_level", "original": "info", "error": "", "type": "invalid format", "exp": "Empty log level causes default failure"},
    {"key": "gNBs.tr_s_preference", "original": "f1", "error": "invalid_pref", "type": "invalid enum", "exp": "Invalid transport preference causes F1 interface error"},
    {"key": "gNBs.tr_s_preference", "original": "f1", "error": 1, "type": "wrong type", "exp": "Number instead of string causes type mismatch"},
    {"key": "gNBs.tr_s_preference", "original": "f1", "error": None, "type": "missing value", "exp": "Missing preference causes configuration error"},
    {"key": "gNBs.local_s_address", "original": "127.0.0.5", "error": "invalid.ip", "type": "invalid format", "exp": "Invalid IP causes network interface error"},
    {"key": "gNBs.local_s_address", "original": "127.0.0.5", "error": "127.0.0.5.1", "type": "invalid format", "exp": "Malformed IP causes parsing error"},
    {"key": "gNBs.local_s_address", "original": "127.0.0.5", "error": 127005, "type": "wrong type", "exp": "Number instead of string causes type error"},
    {"key": "gNBs.plmn_list.mnc_length", "original": 2, "error": 3, "type": "logical contradiction", "exp": "MNC length 3 contradicts MNC 1 (should be 2) causes PLMN validation error"},
    {"key": "gNBs.plmn_list.mnc_length", "original": 2, "error": 1, "type": "logical contradiction", "exp": "MNC length 1 contradicts MNC 1 (should be 2) causes inconsistency"},
    {"key": "gNBs.plmn_list.mnc_length", "original": 2, "error": "two", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs.NETWORK_INTERFACES.GNB_PORT_FOR_S1U", "original": 2152, "error": None, "type": "missing value", "exp": "Missing port value causes NGU interface failure"},
    {"key": "gNBs.NETWORK_INTERFACES.GNB_PORT_FOR_S1U", "original": 2152, "error": -1, "type": "out of range", "exp": "Negative port causes binding error"},
    {"key": "gNBs.NETWORK_INTERFACES.GNB_PORT_FOR_S1U", "original": 2152, "error": "port", "type": "wrong type", "exp": "String instead of number causes type error"},
]

du_mods = [
    {"key": "gNBs[0].gNB_ID", "original": "0xe00", "error": "invalid", "type": "invalid format", "exp": "Invalid gNB ID format causes parsing error in DU"},
    {"key": "gNBs[0].gNB_ID", "original": "0xe00", "error": 3584, "type": "wrong type", "exp": "Number instead of string causes type mismatch"},
    {"key": "gNBs[0].gNB_ID", "original": "0xe00", "error": "", "type": "invalid format", "exp": "Empty ID causes validation failure"},
    {"key": "gNBs[0].tracking_area_code", "original": 1, "error": -1, "type": "out of range", "exp": "Negative TAC causes RRC error in DU"},
    {"key": "gNBs[0].tracking_area_code", "original": 1, "error": 65536, "type": "out of range", "exp": "TAC out of range causes NGAP mismatch"},
    {"key": "gNBs[0].tracking_area_code", "original": 1, "error": "tac", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].plmn_list[0].mcc", "original": 1, "error": 1000, "type": "out of range", "exp": "MCC out of range causes PLMN error"},
    {"key": "gNBs[0].plmn_list[0].mcc", "original": 1, "error": -1, "type": "out of range", "exp": "Negative MCC causes validation error"},
    {"key": "gNBs[0].plmn_list[0].mcc", "original": 1, "error": "mcc", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].plmn_list[0].mnc", "original": 1, "error": 1000, "type": "out of range", "exp": "MNC out of range causes PLMN mismatch"},
    {"key": "gNBs[0].plmn_list[0].mnc", "original": 1, "error": -1, "type": "out of range", "exp": "Negative MNC causes validation error"},
    {"key": "gNBs[0].plmn_list[0].mnc", "original": 1, "error": "mnc", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].nr_cellid", "original": 1, "error": -1, "type": "out of range", "exp": "Negative cell ID causes cell config error"},
    {"key": "gNBs[0].nr_cellid", "original": 1, "error": 1000000, "type": "out of range", "exp": "Cell ID out of range causes collision"},
    {"key": "gNBs[0].nr_cellid", "original": 1, "error": "cell", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].pdsch_AntennaPorts_XP", "original": 2, "error": 0, "type": "out of range", "exp": "Zero antenna ports causes PDSCH failure"},
    {"key": "gNBs[0].pdsch_AntennaPorts_XP", "original": 2, "error": 10, "type": "out of range", "exp": "Too many ports causes resource error"},
    {"key": "gNBs[0].pdsch_AntennaPorts_XP", "original": 2, "error": "two", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].servingCellConfigCommon[0].physCellId", "original": 0, "error": -1, "type": "out of range", "exp": "Negative physCellId causes cell identity error"},
    {"key": "gNBs[0].servingCellConfigCommon[0].physCellId", "original": 0, "error": 1008, "type": "out of range", "exp": "physCellId out of range (0-1007)"},
    {"key": "gNBs[0].servingCellConfigCommon[0].physCellId", "original": 0, "error": "zero", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].servingCellConfigCommon[0].absoluteFrequencySSB", "original": 641280, "error": 0, "type": "out of range", "exp": "Zero frequency causes SSB config error"},
    {"key": "gNBs[0].servingCellConfigCommon[0].absoluteFrequencySSB", "original": 641280, "error": 10000000, "type": "out of range", "exp": "Frequency out of range causes PHY error"},
    {"key": "gNBs[0].servingCellConfigCommon[0].absoluteFrequencySSB", "original": 641280, "error": "freq", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].SCTP.SCTP_INSTREAMS", "original": 2, "error": 0, "type": "out of range", "exp": "Zero streams causes SCTP failure"},
    {"key": "gNBs[0].SCTP.SCTP_INSTREAMS", "original": 2, "error": 100, "type": "out of range", "exp": "Too many streams causes resource exhaustion"},
    {"key": "gNBs[0].SCTP.SCTP_INSTREAMS", "original": 2, "error": "streams", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].num_cc", "original": 1, "error": 0, "type": "out of range", "exp": "Zero component carriers causes config error"},
    {"key": "gNBs[0].num_cc", "original": 1, "error": 10, "type": "out of range", "exp": "Too many carriers causes resource error"},
    {"key": "gNBs[0].num_cc", "original": 1, "error": "one", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "MACRLCs[0].num_cc", "original": 1, "error": "string", "type": "wrong type", "exp": "Wrong type for num_cc causes MACRLC error"},
    {"key": "MACRLCs[0].num_cc", "original": 1, "error": 0, "type": "out of range", "exp": "Zero num_cc causes MACRLC failure"},
    {"key": "MACRLCs[0].num_cc", "original": 1, "error": None, "type": "missing value", "exp": "Missing num_cc causes configuration error"},
    {"key": "L1s[0].prach_dtx_threshold", "original": 120, "error": -100, "type": "out of range", "exp": "Negative threshold causes PRACH error"},
    {"key": "L1s[0].prach_dtx_threshold", "original": 120, "error": 1000, "type": "out of range", "exp": "Threshold out of range causes DTX failure"},
    {"key": "L1s[0].prach_dtx_threshold", "original": 120, "error": "thresh", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "RUs[0].nb_tx", "original": 4, "error": 0, "type": "out of range", "exp": "Zero TX antennas causes RU config error"},
    {"key": "RUs[0].nb_tx", "original": 4, "error": 100, "type": "out of range", "exp": "Too many TX antennas causes resource error"},
    {"key": "RUs[0].nb_tx", "original": 4, "error": "four", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "RUs[0].max_pdschReferenceSignalPower", "original": -27, "error": 1000, "type": "out of range", "exp": "Power out of range causes PHY error"},
    {"key": "RUs[0].max_pdschReferenceSignalPower", "original": -27, "error": -1000, "type": "out of range", "exp": "Negative power out of range"},
    {"key": "RUs[0].max_pdschReferenceSignalPower", "original": -27, "error": "power", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "rfsimulator.serveraddr", "original": "server", "error": "", "type": "invalid format", "exp": "Empty server address causes RF simulator failure"},
    {"key": "rfsimulator.serveraddr", "original": "server", "error": "invalid@addr", "type": "invalid format", "exp": "Invalid address format causes connection error"},
    {"key": "rfsimulator.serveraddr", "original": "server", "error": 123, "type": "wrong type", "exp": "Number instead of string causes type error"},
    {"key": "log_config.global_log_level", "original": "info", "error": "invalid", "type": "invalid enum", "exp": "Invalid log level causes logging crash"},
    {"key": "log_config.global_log_level", "original": "info", "error": 2, "type": "wrong type", "exp": "Number instead of string causes type error"},
    {"key": "log_config.global_log_level", "original": "info", "error": None, "type": "missing value", "exp": "Missing log level causes default failure"},
    {"key": "fhi_72.dpdk_devices", "original": ["0000:ca:02.0", "0000:ca:02.1"], "error": {}, "type": "wrong type", "exp": "Object instead of array causes DPDK error"},
    {"key": "fhi_72.dpdk_devices", "original": ["0000:ca:02.0", "0000:ca:02.1"], "error": ["invalid"], "type": "invalid format", "exp": "Invalid device format causes DPDK failure"},
    {"key": "fhi_72.dpdk_devices", "original": ["0000:ca:02.0", "0000:ca:02.1"], "error": [], "type": "missing value", "exp": "Empty devices causes no DPDK interfaces"},
    {"key": "gNBs[0].servingCellConfigCommon[0].dl_subcarrierSpacing", "original": 1, "error": 10, "type": "invalid enum", "exp": "Invalid subcarrier spacing causes PHY config error"},
    {"key": "gNBs[0].servingCellConfigCommon[0].dl_subcarrierSpacing", "original": 1, "error": 0, "type": "out of range", "exp": "Zero spacing causes timing error"},
    {"key": "gNBs[0].servingCellConfigCommon[0].dl_subcarrierSpacing", "original": 1, "error": "spacing", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].do_CSIRS", "original": 1, "error": None, "type": "missing value", "exp": "Missing CSIRS flag causes CSI-RS configuration error"},
    {"key": "gNBs[0].do_CSIRS", "original": 1, "error": 2, "type": "invalid enum", "exp": "Invalid CSIRS value causes flag error"},
    {"key": "gNBs[0].do_CSIRS", "original": 1, "error": "yes", "type": "wrong type", "exp": "String instead of number causes type error"},
    {"key": "gNBs[0].gNB_DU_ID", "original": "0xe00", "error": "not_hex", "type": "invalid format", "exp": "Invalid DU ID format causes ID mismatch"},
    {"key": "gNBs[0].gNB_DU_ID", "original": "0xe00", "error": 3584, "type": "wrong type", "exp": "Number instead of string causes type error"},
    {"key": "gNBs[0].gNB_DU_ID", "original": "0xe00", "error": None, "type": "missing value", "exp": "Missing DU ID causes configuration error"},
]

cu_counts = {}
du_counts = {}
cases = []

for i in range(1, 101):
    available_cu = [m for m in cu_mods if cu_counts.get(m['key'], 0) < 3]
    if not available_cu:
        cu_mod = random.choice(cu_mods)
    else:
        cu_mod = random.choice(available_cu)
    cu_counts[cu_mod['key']] = cu_counts.get(cu_mod['key'], 0) + 1

    available_du = [m for m in du_mods if du_counts.get(m['key'], 0) < 3]
    if not available_du:
        du_mod = random.choice(du_mods)
    else:
        du_mod = random.choice(available_du)
    du_counts[du_mod['key']] = du_counts.get(du_mod['key'], 0) + 1

    case = {
        "filename": f"case_{i:03d}.json",
        "cu": {
            "modified_key": cu_mod['key'],
            "original_value": cu_mod['original'],
            "error_value": cu_mod['error'],
            "error_type": cu_mod['type'],
            "explanation": cu_mod['exp']
        },
        "du": {
            "modified_key": du_mod['key'],
            "original_value": du_mod['original'],
            "error_value": du_mod['error'],
            "error_type": du_mod['type'],
            "explanation": du_mod['exp']
        }
    }
    cases.append(case)

with open('cases_delta.json', 'w') as f:
    json.dump(cases, f, indent=2)