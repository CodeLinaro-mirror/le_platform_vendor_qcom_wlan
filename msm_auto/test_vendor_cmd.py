# Copyright (c) 2021 The Linux Foundation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#     * Neither the name of The Linux Foundation nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import subprocess
import time
import hostapd
import hwsim_utils
from wpasupplicant import WpaSupplicant
from p2p_utils import *
from log_verify import LogVerify
from ini import Ini
from load_unload import reload_driver
import logging
import whunt_daemon_util
from utils import HwsimSkip
logger = logging.getLogger()

VENDOR_CMD_TOOL = '/vendor/whunt/bin/vendor_cmd_tool'
VENDOR_CMD_XML = '/vendor/whunt/test_case/config/vendor_cmd.xml '
EOK = 0
EALREADY = -114
EBUSY = -16
EINVAL = -22
EOPNOTSUPP = -95
ETMO = -110
ENOTSUPP = -524

def connect_sta_sap(dev, apdev):
    params = { "ssid":"WHUNT_OPEN" }
    hapd = hostapd.add_ap(apdev[0], params)
    dev[0].connect("WHUNT_OPEN", key_mgmt="NONE")
    ev = hapd.wait_event([ "AP-STA-CONNECTED" ], timeout=5)
    if ev is None:
        raise Exception("No connection event received from hostapd")
    hwsim_utils.test_connectivity(dev[0], hapd)

def vendor_cmd_execute(dev, cmd_params, cmd_name, expected_result = EOK):
    cmd = "%s -f %s %s" % (VENDOR_CMD_TOOL, VENDOR_CMD_XML, cmd_params,)
    ret, buf = dev[0].cmd_execute(cmd.split(" "))
    if buf.find('error_handler received') > 0:
        error_handler = buf.split("\n")[1]
        errno = int(error_handler.split(":")[1])
    else:
        errno = EOK
    if ret:
        raise Exception("%s vendor command not working: ret = %d" % (cmd_name, ret))
    if errno == EOPNOTSUPP:
        raise HwsimSkip("%s vendor command is not supported" % cmd_name)
    if errno != expected_result:
        raise Exception("%s vendor command failed: expected = %d, actual = %d" % (cmd_name, expected_result, errno))

def test_get_chain_rssi(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_GET_CHAIN_RSSI vendor command """
    """ Date: 3/6/2019 """
    cmd = '-i wlan0 --START_CMD --GET_CHAIN_RSSI --MAC_ADDR "000af58989ff" --END_CMD'
    
    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd, "GET_CHAIN_RSSI", ETMO)
    
def test_wifi_logger_start(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_WIFI_LOGGER_START """
    """ Date: 3/6/2019 """
    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")

    with Ini("wlan") as ini:
       ini.change_ini("gEnablePacketLog", 1, load=True)
       for i in range(6):
           cmd = '-i wlan0 --START_CMD --WIFI_LOGGER_START --RING_ID ' + str(i) + ' --VBV_LVL 0 --IS_IW_CMD 1 --END_CMD'

           log.start_monitoring()

           vendor_cmd_execute(dev, cmd, "WIFI_LOGGER_START")
           subprocess.call("adb shell iw wlan0 link > /dev/null".split())
           subprocess.call("adb shell iw wlan0 link > /dev/null".split())

           if i == 0:
               continue

           count = 0
           res = []
           count, res = log.find_string("SIR_HAL_START_STOP_LOGGING")
           if count == 0:
                raise Exception("QCA_NL80211_VENDOR_SUBCMD_WIFI_LOGGER_START not working")

def test_dcc_clear_stats(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_DCC_CLEAR_STATS vendor command """
    """ Date: 3/6/2019 """
    connect_sta_sap(dev, apdev)

    cmd = '-i wlan0 --START_CMD --DCC_CLEAR_STATS --BITMAP 1 --END_CMD'

    vendor_cmd_execute(dev, cmd, "DCC_CLEAR_STATS")

def test_wifi_test_config(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_WIFI_TEST_CONFIGURATION vendor command """
    """ Date: 3/12/2019 """

    connect_sta_sap(dev, apdev)

    # Sending all the config items with enabled.
    cmd = '-i wlan0 --START_CMD --WIFI_CONFIG --WMM_ENABLE 1 --ACCEPT_ADDBA_REQ 1 --SEND_ADDBA_REQ 1 --HE_FRAGMENTATION 1 --HE_MCS 1 --WEP_TKIP_IN_HE 1 --ADD_DEL_BA_SESSION 1 --ADDBA_BUFF_SIZE 1 --BA_TID 1 --ENABLE_NO_ACK 1 --NO_ACK_AC 1 --HE_LTF 1 --ENABLE_TX_BEAMFORMEE 1 --HE_TX_BEAMFORMEE_NSTS 1 --HE_MU_EDCA_AC 1 --HE_MAC_PADDING_DUR 1 --OVERRIDE_MU_EDCA 1 --HE_OM_CTRL_SUPP 1 --HE_OM_CTRL_BW 1 --HE_OM_CTRL_NSS 1 --HE_TX_SUPPDU 1 --HE_ACTION_TX_TB_PPDU 1 --HE_HTC_HE_SUPP 1 --END_CMD'
    vendor_cmd_execute(dev, cmd, "WIFI_CONFIG")
    time.sleep(1)

    # Sending all the config items with disabled.
    cmd = '-i wlan0 --START_CMD --WIFI_CONFIG --WMM_ENABLE 0 --ACCEPT_ADDBA_REQ 0 --SEND_ADDBA_REQ 0 --HE_FRAGMENTATION 0 --HE_MCS 0 --WEP_TKIP_IN_HE 0 --ADD_DEL_BA_SESSION 2 --ADDBA_BUFF_SIZE 0 --BA_TID 0 --ENABLE_NO_ACK 1 --NO_ACK_AC 0 --HE_LTF 0 --ENABLE_TX_BEAMFORMEE 0 --HE_TX_BEAMFORMEE_NSTS 0 --HE_MU_EDCA_AC 0 --HE_MAC_PADDING_DUR 0 --OVERRIDE_MU_EDCA 0 --HE_OM_CTRL_SUPP 0 --HE_OM_CTRL_BW 0 --HE_OM_CTRL_NSS 0 --HE_TX_SUPPDU 0 --HE_ACTION_TX_TB_PPDU 0 --HE_HTC_HE_SUPP 0 --END_CMD'
    vendor_cmd_execute(dev, cmd, "WIFI_CONFIG")

def test_reset_passpoint_list(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_EXTSCAN_PNO_RESET_PASSPOINT_LIST vendor command """
    """ Date: 3/13/2019 """

    connect_sta_sap(dev, apdev)

    cmd = '-i wlan0 --START_CMD --EXTSCAN_PNO_RESET_PASSPOINT_LIST --CONFIG_PARAM_REQUEST_ID 1 --END_CMD'
    vendor_cmd_execute(dev, cmd, "EXTSCAN_PNO_RESET_PASSPOINT_LIST")

def test_reset_significant_change(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_EXTSCAN_RESET_SIGNIFICANT_CHANGE vendor command """
    """ Date: 3/14/2019 """

    connect_sta_sap(dev, apdev)

    cmd = '-i wlan0 --START_CMD --EXTSCAN_PNO_RESET_SIGNIFICANT_CHANGE --CONFIG_PARAM_REQUEST_ID 1 --END_CMD'
    vendor_cmd_execute(dev, cmd, "EXTSCAN_RESET_SIGNIFICANT_CHANGE")

def test_config_tdls_trigger_mode(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_CONFIGURE_TDLS """
    """ Date: 3/9/2019 """
    connect_sta_sap(dev, apdev)
    cmd = '-i wlan0 --START_CMD --CONFIG_TDLS_MODE --MODE 1 --TX_STATS 0 --TX_THRESHOLD 0 --DISC_PERIOD 0 --MAX_DISC_ATTEMPT 0 --IDLE_TIMEOUT 0 --IDLE_PACKET_THRE 0 --SETUP_RSSI_THRE 0 --TEARDOWN_RSSI_THRE 0 --END_CMD'
    vendor_cmd_execute(dev, cmd, "CONFIG_TDLS_MODE")

def test_scanning_mac_oui(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_SCANNING_MAC_OUI """
    """ Date: 3/27/2019 """
    dev[0].scan()
    cmd = '-i wlan0 --START_CMD --SCANNING_MAC_OUI --OUI AACCBB --END_CMD'
    vendor_cmd_execute(dev, cmd, "SCANNING_MAC_OUI")

def test_get_tdls_cap(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_TDLS_GET_CAPABILITIES """
    """ Date: 3/18/2019 """
    connect_sta_sap(dev, apdev)
    cmd = '-i wlan0 --START_CMD --TDLS_GET_CAP --END_CMD'
    vendor_cmd_execute(dev, cmd, "TDLS_GET_CAP")

def test_set_trace_level(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_SET_TRACE_LEVEL vendor command """
    """ Date: 3/26/2019 """
    cmd = '-i wlan0 --START_CMD --SET_TRACE_LEVEL --TRACE_LEVEL_PARAM --NESTED_AUTO --MODULE_ID 51 --TRACE_MASK 1  --END_ATTR  --END_ATTR  --END_CMD'
    cmd_restore = '-i wlan0 --START_CMD --SET_TRACE_LEVEL --TRACE_LEVEL_PARAM --NESTED_AUTO --MODULE_ID 51 --TRACE_MASK 2047  --END_ATTR  --END_ATTR  --END_CMD'

    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd, "SET_TRACE_LEVEL")

    # Restore the trace level so that it won't affect other test cases
    vendor_cmd_execute(dev, cmd_restore, "SET_TRACE_LEVEL")

def test_ll_stats(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_LL_STATS_SET and QCA_NL80211_VENDOR_SUBCMD_LL_STATS_CLEAR vendor command """
    """ Date: 3/26/2019 """
    cmd1 = '-i wlan0 --START_CMD --SET_LL_STATS --SET_CONFIG_MPDU_SIZE_THRESHOLD 30 --SET_CONFIG_AGGRESSIVE_STATS_GATHERING 40 --END_CMD'
    cmd2 = '-i wlan0 --START_CMD --LLSTATS_GET  --REQ_ID 1 --REQ_MASK 7 --REQ_INFO "INFO" --END_CMD'
    cmd3 = '-i wlan0 --START_CMD --CLEAR_LL_STATS --LL_STATS_CLR_CONFIG_REQ_MASK 3 --LL_STATS_CLR_CONFIG_STOP_REQ 4 --END_CMD'
    with Ini("wlan") as ini:
        ini.change_ini("enable_qmi_stats", 0, load=True)
        connect_sta_sap(dev, apdev)

        vendor_cmd_execute(dev, cmd1, "SET_LL_STATS")
        time.sleep(1)

        vendor_cmd_execute(dev, cmd2, "LLSTATS_GET", ETMO)
        time.sleep(1)

        vendor_cmd_execute(dev, cmd3, "CLEAR_LL_STATS")
        time.sleep(1)

def test_get_logger_feature_set(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_GET_LOGGER_FEATURE_SET vendor command """
    """ Date: 3/28/2019 """
    cmd = '-i wlan0 --START_CMD --GET_LOGGER_FEATURE_SET --END_CMD'

    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd, "GET_LOGGER_FEATURE_SET")

def test_get_bus_size(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_GET_BUS_SIZE vendor command """
    """ Date: 4/15/2019 """
    cmd = '-i wlan0 --START_CMD --GET_BUS_SIZE --DRV_INFO_BUS_SIZE 1 --END_CMD'
    
    connect_sta_sap(dev, apdev)
	
    vendor_cmd_execute(dev, cmd, "GET_BUS_SIZE")

def test_set_band(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_SETBAND vendor command """
    """ Date: 4/15/2019 """
    cmd = '-i wlan0 --START_CMD --SETBAND --SETBAND_VALUE 1 --END_CMD'
    cmd_auto = '-i wlan0 --START_CMD --SETBAND --SETBAND_VALUE 0 --END_CMD'
    
    connect_sta_sap(dev, apdev)
	
    vendor_cmd_execute(dev, cmd, "SETBAND")
    time.sleep(1)

    # Restore the band so that it won't affect other test cases
    dev[0].request("REMOVE_NETWORK all")
    vendor_cmd_execute(dev, cmd_auto, "SETBAND")
    time.sleep(1)

def test_set_fast_roaming_enable_disable(dev, apdev):
    """ The test case is to enable fast roaming followed by disabling it. Set
	fast roaming enable/disable indication comes to host via
	QCA_NL80211_VENDOR_SUBCMD_ROAMING vendor command and attribute
	QCA_WLAN_VENDOR_ATTR_ROAMING_POLICY """
    """ Date: 05/05/2021 """
    cmd_enable = '-i wlan0 --START_CMD --ROAMING --ROAMING_POLICY 1 --END_CMD'
    cmd_disable = '-i wlan0 --START_CMD --ROAMING --ROAMING_POLICY 0 --END_CMD'

    connect_sta_sap(dev, apdev)

    # Enable
    vendor_cmd_execute(dev, cmd_enable, "ROAMING")
    time.sleep(1)

    # Disabe success
    vendor_cmd_execute(dev, cmd_disable, "ROAMING")
    time.sleep(1)
    # Disable again, will not send command to FW
    vendor_cmd_execute(dev, cmd_disable, "ROAMING", EALREADY)
    time.sleep(1)
    reload_driver("wlan0", "set_fast_roaming_enable_disable")

def test_set_fast_roaming_disabe_fail(dev, apdev):
    """ Test case to validate the scenario in which roam disable attempt, using
	vendor command QCA_NL80211_VENDOR_SUB_CMD_ROAMING, fails in FW """
    """ Date: 05/05/2021 """
    cmd_enable = '-i wlan0 --START_CMD --ROAMING --ROAMING_POLICY 1 --END_CMD'
    cmd_disable = '-i wlan0 --START_CMD --ROAMING --ROAMING_POLICY 0 --END_CMD'

    connect_sta_sap(dev, apdev)

    # Enable
    vendor_cmd_execute(dev, cmd_enable, "ROAMING")
    time.sleep(1)

    # Disabe fail
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_set_fast_roaming_fail.xml")
    try:
        vendor_cmd_execute(dev, cmd_disable, "ROAMING", EBUSY)
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")
        reload_driver("wlan0", "set_fast_roaming_disabe_fail")

def test_set_fast_roaming_disabe_timeout(dev, apdev):
    """ Test case to validate the scenario in which FW does not send a response
	for fast roaming disable command to HOST """
    """ Date: 05/05/2021 """
    cmd_enable = '-i wlan0 --START_CMD --ROAMING --ROAMING_POLICY 1 --END_CMD'
    cmd_disable = '-i wlan0 --START_CMD --ROAMING --ROAMING_POLICY 0 --END_CMD'

    connect_sta_sap(dev, apdev)

    # Enable
    vendor_cmd_execute(dev, cmd_enable, "ROAMING")
    time.sleep(1)

    # Disabe timeout
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_set_fast_roaming_timeout.xml")
    try:
        vendor_cmd_execute(dev, cmd_disable, "ROAMING", ETMO)
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")
        reload_driver("wlan0", "set_fast_roaming_disabe_timeout")

def test_stats_ext(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_STATS_EXT vendor command """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --STATS_EXT --DATA ABCD --END_CMD'

    connect_sta_sap(dev, apdev)

    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_stats_ext.xml")
    try:
        vendor_cmd_execute(dev, cmd, "STATS_EXT")
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

def test_extscan_stop(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_EXTSCAN_STOP vendor command """
    """ Date: 5/29/2019 """
    cmd_start = '-i wlan0 --START_CMD --EXTSCAN_START --REQUEST_ID 1234 --BASE_PERIOD 100 --MAX_AP_PER_SCAN 5 --REPORT_THRESHOLD_PERCENT 75 --REPORT_THRESHOLD_NUM_SCANS 5 --NUM_BUCKETS 1 --BUCKET_SPEC --NESTED_AUTO --SPEC_INDEX 0 --BAND 1 --PERIOD 5000 --REPORT_EVENTS 0 --NUM_CHANNEL_SPECS 1 --MAX_PERIOD 5000 --EXPONENT 2 --STEP_COUNT 5 --CHANNEL_SPEC --NESTED_AUTO --CHANNEL 2412 --DWELL_TIME 1000 --PASSIVE 1 --END_ATTR --END_ATTR --END_ATTR --END_ATTR --END_CMD'
    cmd_stop = '-i wlan0 --START_CMD --EXTSCAN_STOP --REQUEST_ID 1234 --END_CMD'

    connect_sta_sap(dev, apdev)

    # Stop timeout
    vendor_cmd_execute(dev, cmd_stop, "EXTSCAN_STOP", ETMO)
    time.sleep(1)

    # Stop fail
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_extscan_stop_fail.xml")
    try:
        vendor_cmd_execute(dev, cmd_stop, "EXTSCAN_STOP", EINVAL)
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

    # Stop after started
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_extscan.xml")
    log.start_monitoring()
    try:
        vendor_cmd_execute(dev, cmd_start, "EXTSCAN_START")
        vendor_cmd_execute(dev, cmd_stop, "EXTSCAN_STOP")
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

def test_extscan_reset_bssid_hotlist(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_EXTSCAN_RESET_BSSID_HOTLIST vendor command """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --EXTSCAN_RESET_BSSID_HOTLIST --CONFIG_PARAM_REQUEST_ID 1234 --END_CMD'

    connect_sta_sap(dev, apdev)

    # command timeout
    vendor_cmd_execute(dev, cmd, "EXTSCAN_RESET_BSSID_HOTLIST", ETMO)
    time.sleep(1)

    # command fail
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_extscan_reset_bssid_hotlist_fail.xml")
    try:
        vendor_cmd_execute(dev, cmd, "EXTSCAN_RESET_BSSID_HOTLIST", EINVAL)
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

    # command success
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_extscan.xml")
    try:
        vendor_cmd_execute(dev, cmd, "EXTSCAN_RESET_BSSID_HOTLIST")
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

def test_extscan_set_significant_change(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_EXTSCAN_SET_SIGNIFICANT_CHANGE vendor command """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --EXTSCAN_SET_SIGNIFICANT_CHANGE --CONFIG_PARAM_REQUEST_ID 1234 --CONFIG_PARAM_RSSI_SAMPLE_SIZE 5 --CONFIG_PARAM_LOST_AP_SAMPLE_SIZE 5 --CONFIG_PARAM_MIN_BREACHING 1 --CONFIG_PARAM_NUM_AP 1 --CONFIG_PARAM_AP_THRESHOLD_PARAM --NESTED_AUTO --AP_THRESHOLD_PARAM_BSSID "000af58989ff" --AP_THRESHOLD_PARAM_RSSI_LOW 24 --AP_THRESHOLD_PARAM_RSSI_HIGH 70 --END_ATTR --END_ATTR --END_CMD'
    cmd_invalid = '-i wlan0 --START_CMD --EXTSCAN_SET_SIGNIFICANT_CHANGE --CONFIG_PARAM_REQUEST_ID 1234 --CONFIG_PARAM_RSSI_SAMPLE_SIZE 5 --CONFIG_PARAM_LOST_AP_SAMPLE_SIZE 5 --CONFIG_PARAM_MIN_BREACHING 1 --CONFIG_PARAM_NUM_AP 128 --CONFIG_PARAM_AP_THRESHOLD_PARAM --NESTED_AUTO --AP_THRESHOLD_PARAM_BSSID "000af58989ff" --AP_THRESHOLD_PARAM_RSSI_LOW 24 --AP_THRESHOLD_PARAM_RSSI_HIGH 70 --END_ATTR --END_ATTR --END_CMD'

    connect_sta_sap(dev, apdev)

    # invalid command
    vendor_cmd_execute(dev, cmd_invalid, "EXTSCAN_SET_SIGNIFICANT_CHANGE", EINVAL)
    time.sleep(1)

    # command timeout
    vendor_cmd_execute(dev, cmd, "EXTSCAN_SET_SIGNIFICANT_CHANGE", ETMO)
    time.sleep(1)

    # command fail
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_extscan_set_significant_change_fail.xml")
    try:
        vendor_cmd_execute(dev, cmd, "EXTSCAN_SET_SIGNIFICANT_CHANGE", EINVAL)
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

    # command success
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_extscan.xml")
    try:
        vendor_cmd_execute(dev, cmd, "EXTSCAN_SET_SIGNIFICANT_CHANGE")
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

def test_no_dfs_flag(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_NO_DFS_FLAG vendor command """
    """ Date: 5/29/2019 """
    cmd_dfs = '-i wlan0 --START_CMD --NO_DFS_FLAG --SET_NO_DFS_FLAG 0 --END_CMD'
    cmd_no_dfs = '-i wlan0 --START_CMD --NO_DFS_FLAG --SET_NO_DFS_FLAG 1 --END_CMD'
    cmd_invalid = '-i wlan0 --START_CMD --NO_DFS_FLAG --SET_NO_DFS_FLAG 2 --END_CMD'

    params = { "ssid": "WHUNT_OPEN",
               "country_code": "CN",
               "ieee80211n" : "1",
               "hw_mode" : "a",
               "channel": "52"}
    hapd = hostapd.add_ap(apdev[0], params, timeout=120)
    bssid = hapd.own_addr()

    dev[0].request("DRIVER COUNTRY FR")

    # invalid command
    vendor_cmd_execute(dev, cmd_invalid, "NO_DFS_FLAG", EINVAL)
    time.sleep(1)

    # enable dfs scan
    vendor_cmd_execute(dev, cmd_dfs, "NO_DFS_FLAG")
    time.sleep(1)

    dev[0].flush_scan_cache()
    dev[0].scan_for_bss(bssid, freq="5260")

    # disable dfs scan
    vendor_cmd_execute(dev, cmd_no_dfs, "NO_DFS_FLAG")
    time.sleep(1)

    dev[0].flush_scan_cache()
    dev[0].scan(freq="5260", no_wait=True)
    ev = dev[0].wait_event(["CTRL-EVENT-SCAN-FAILED"], timeout=10)
    if ev is None:
        raise Exception("NO_DFS_FLAG vendor command not working")

def test_get_wifi_info(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_GET_WIFI_INFO vendor command """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --GET_WIFI_INFO --DRIVER_VERSION 1 --FIRMWARE_VERSION 1 --RADIO_INDEX 0 --END_CMD'

    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd, "GET_WIFI_INFO")

def test_roam_ssid_white_list(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_ROAM vendor command with subcmd QCA_WLAN_VENDOR_ATTR_ROAM_SUBCMD_SSID_WHITE_LIST """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 1 --ROAMING_REQ_ID 1 --WHITE_LIST_SSID_NUM_NETWORKS 1 --WHITE_LIST_SSID_LIST --NESTED_AUTO --WHITE_LIST_SSID "WHUNT_WHITE_LIST_SSID" --END_ATTR --END_ATTR --END_CMD'
    cmd_null = 'adb shell /vendor/whunt/bin/vendor_cmd_tool -f /vendor/whunt/test_case/config/vendor_cmd.xml -i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 1 --ROAMING_REQ_ID 1 --WHITE_LIST_SSID_NUM_NETWORKS 1 --WHITE_LIST_SSID_LIST --NESTED_AUTO --WHITE_LIST_SSID "" --END_ATTR --END_ATTR --END_CMD'
    cmd_too_many = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 1 --ROAMING_REQ_ID 1 --WHITE_LIST_SSID_NUM_NETWORKS 5 --WHITE_LIST_SSID_LIST --NESTED_AUTO --WHITE_LIST_SSID "1234" --END_ATTR --END_ATTR --END_CMD'
    cmd_too_long = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 1 --ROAMING_REQ_ID 1 --WHITE_LIST_SSID_NUM_NETWORKS 1 --WHITE_LIST_SSID_LIST --NESTED_AUTO --WHITE_LIST_SSID "123456789012345678901234567890123" --END_ATTR --END_ATTR --END_CMD'

    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")

    log.start_monitoring()
    vendor_cmd_execute(dev, cmd, "ROAM")
    time.sleep(1)

    count, res = log.find_string("hdd_set_ext_roam_params")
    if count == 0:
        raise Exception("ROAM vendor command not working")

    if not [s for s in res if "Cmd Type: 1" in s]:
        raise Exception("ROAM vendor command not working")

    count1, res = log.find_string("Whitelist: WHUNT_WHITE_LIST_SSID")
    count2, res = log.find_string("WHUNT_WHITE_LIST_SSID")
    if count1 == 0 and count2 == 0:
        raise Exception("ROAM vendor command not working")

    count, res = log.find_string("WMI_ROAM_PER_CONFIG_CMDID")
    if count == 0:
        raise Exception("ROAM vendor command not working")

    log.start_monitoring()
    buf = subprocess.check_output(cmd_null.split(" "))
    time.sleep(1)

    count1, res = log.find_string("wlan_hdd_cfg80211_set_ext_roam_params")
    count2, res = log.find_string("hdd_set_ext_roam_params")
    if count1 == 0 and count2 == 0:
        raise Exception("ROAM vendor command not working")

    vendor_cmd_execute(dev, cmd_too_many, "ROAM", EINVAL)
    time.sleep(1)

    vendor_cmd_execute(dev, cmd_too_long, "ROAM", EINVAL)
    time.sleep(1)

def test_roam_set_extscan_params(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_ROAM vendor command with subcmd QCA_WLAN_VENDOR_ATTR_ROAM_SUBCMD_SET_EXTSCAN_ROAM_PARAMS """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 2 --ROAMING_REQ_ID 1 --A_BAND_BOOST_THRESHOLD 1 --A_BAND_PENALTY_THRESHOLD 1 --A_BAND_BOOST_FACTOR 1 --A_BAND_PENALTY_FACTOR 1 --A_BAND_MAX_BOOST 1 --LAZY_ROAM_HISTERESYS 1 --ALERT_ROAM_RSSI_TRIGGER 1 --END_CMD'

    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")

    log.start_monitoring()
    vendor_cmd_execute(dev, cmd, "ROAM")
    time.sleep(1)

    count, res = log.find_string("hdd_set_ext_roam_params")
    if count == 0:
        raise Exception("ROAM vendor command not working")

    if not [s for s in res if "Cmd Type: 2" in s]:
        raise Exception("ROAM vendor command not working")

    count, res = log.find_string("WMI_ROAM_PER_CONFIG_CMDID")
    if count == 0:
        raise Exception("ROAM vendor command not working")

def test_roam_set_lazy_roam(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_ROAM vendor command with subcmd QCA_WLAN_VENDOR_ATTR_ROAM_SUBCMD_SET_LAZY_ROAM """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 3 --ROAMING_REQ_ID 1 --SET_LAZY_ROAM_ENABLE 45 --END_CMD'

    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")

    log.start_monitoring()
    vendor_cmd_execute(dev, cmd, "ROAM")
    time.sleep(1)

    count, res = log.find_string("hdd_set_ext_roam_params")
    if count == 0:
        raise Exception("ROAM vendor command not working")

    if not [s for s in res if "Cmd Type: 3" in s]:
        raise Exception("ROAM vendor command not working")

    count, res = log.find_string("WMI_ROAM_PER_CONFIG_CMDID")
    if count == 0:
        raise Exception("ROAM vendor command not working")

def test_roam_set_bssid_prefs(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_ROAM vendor command with subcmd QCA_WLAN_VENDOR_ATTR_ROAM_SUBCMD_SET_BSSID_PREFS """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 4 --ROAMING_REQ_ID 1 --SET_LAZY_ROAM_NUM_BSSID 1 --SET_BSSID_PREFS --NESTED_AUTO --SET_LAZY_ROAM_BSSID "000af58989ff" --SET_LAZY_ROAM_RSSI_MODIFIER 60 --END_ATTR --END_ATTR --END_CMD'
    cmd_too_many = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 4 --ROAMING_REQ_ID 1 --SET_LAZY_ROAM_NUM_BSSID 17 --SET_BSSID_PREFS --NESTED_AUTO --SET_LAZY_ROAM_BSSID "000af58989ff" --SET_LAZY_ROAM_RSSI_MODIFIER 60 --END_ATTR --END_ATTR --END_CMD'

    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")

    log.start_monitoring()
    vendor_cmd_execute(dev, cmd, "ROAM")
    time.sleep(1)

    count, res = log.find_string("hdd_set_ext_roam_params")
    if count == 0:
        raise Exception("ROAM vendor command not working")

    if not [s for s in res if "Cmd Type: 4" in s]:
        raise Exception("ROAM vendor command not working")

    count, res = log.find_string("WMI_ROAM_PER_CONFIG_CMDID")
    if count == 0:
        raise Exception("ROAM vendor command not working")

    vendor_cmd_execute(dev, cmd_too_many, "ROAM", EINVAL)

def test_roam_set_blacklist_bssid(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_ROAM vendor command with subcmd QCA_WLAN_VENDOR_ATTR_ROAM_SUBCMD_SET_BLACKLIST_BSSID """
    """ Date: 5/29/2019 """
    cmd = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 6 --ROAMING_REQ_ID 1 --SET_BSSID_PARAMS_NUM_BSSID 1 --SET_BSSID_PARAMS --NESTED_AUTO --SET_BSSID_PARAMS_BSSID "000af58989ff" --END_ATTR --END_ATTR --END_CMD'
    cmd_too_many = '-i wlan0 --START_CMD --ROAM --ROAMING_SUBCMD 6 --ROAMING_REQ_ID 1 --SET_BSSID_PARAMS_NUM_BSSID 17 --SET_BSSID_PARAMS --NESTED_AUTO --SET_BSSID_PARAMS_BSSID "000af58989ff" --END_ATTR --END_ATTR --END_CMD'

    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")

    log.start_monitoring()
    vendor_cmd_execute(dev, cmd, "ROAM")
    time.sleep(1)

    count, res = log.find_string("hdd_set_ext_roam_params")
    if count == 0:
        raise Exception("ROAM vendor command not working")

    if not [s for s in res if "Cmd Type: 6" in s]:
        raise Exception("ROAM vendor command not working")

    count, res = log.find_string("WMI_ROAM_PER_CONFIG_CMDID")
    if count == 0:
        raise Exception("ROAM vendor command not working")

    vendor_cmd_execute(dev, cmd_too_many, "ROAM", EINVAL)
    time.sleep(1)

def test_offloaded_packets(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_OFFLOADED_PACKETS vendor command """
    """ Date: 5/29/2019 """
    cmd_add = '-i wlan0 --START_CMD --OFFLOADED_PACKETS --SENDING_CONTROL 1 --REQUEST_ID 1 --IP_PACKET_DATA DEADBEEF --SRC_MAC_ADDR "000af58989ff" --DST_MAC_ADDR "ffffffffffff" --PERIOD 1000 --END_CMD'
    cmd_add_invalid_src_addr = '-i wlan0 --START_CMD --OFFLOADED_PACKETS --SENDING_CONTROL 1 --REQUEST_ID 1 --IP_PACKET_DATA DEADBEEF --SRC_MAC_ADDR "000adeadbeef" --DST_MAC_ADDR "ffffffffffff" --PERIOD 1000 --END_CMD'
    cmd_del = '-i wlan0 --START_CMD --OFFLOADED_PACKETS --SENDING_CONTROL 2 --REQUEST_ID 1 --END_CMD'
    cmd_del_invalid_request = '-i wlan0 --START_CMD --OFFLOADED_PACKETS --SENDING_CONTROL 2 --REQUEST_ID 2 --END_CMD'
    cmd_invalid = '-i wlan0 --START_CMD --OFFLOADED_PACKETS --SENDING_CONTROL 3 --REQUEST_ID 2 --END_CMD'

    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd_add, "OFFLOADED_PACKETS")
    time.sleep(1)

    vendor_cmd_execute(dev, cmd_add_invalid_src_addr, "OFFLOADED_PACKETS", EINVAL)
    time.sleep(1)

    vendor_cmd_execute(dev, cmd_del, "OFFLOADED_PACKETS")
    time.sleep(1)

    vendor_cmd_execute(dev, cmd_del_invalid_request, "OFFLOADED_PACKETS", EINVAL)
    time.sleep(1)

    vendor_cmd_execute(dev, cmd_invalid, "OFFLOADED_PACKETS", EINVAL)
    time.sleep(1)

def test_nd_offload(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_ND_OFFLOAD vendor command """
    """ Date: 5/29/2019 """
    cmd_enable = '-i wlan0 --START_CMD --ND_OFFLOAD --ND_OFFLOAD_FLAG 1 --END_CMD'
    cmd_disable = '-i wlan0 --START_CMD --ND_OFFLOAD --ND_OFFLOAD_FLAG 0 --END_CMD'

    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd_enable, "ND_OFFLOAD")
    time.sleep(1)

    vendor_cmd_execute(dev, cmd_disable, "ND_OFFLOAD")
    time.sleep(1)

def test_packet_filter_legacy(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_PACKET_FILTER vendor command """
    """ Date: 5/29/2019 """
    cmd_set = '-i wlan0 --START_CMD --PACKET_FILTER --SET_RESET_PACKET_FILTER 1 --PACKET_FILTER_SIZE 4 --PACKET_FILTER_PROGRAM DEADBEEF --PACKET_FILTER_ID 1 --PACKET_FILTER_CURRENT_OFFSET 0 --END_CMD'
    cmd_reset = '-i wlan0 --START_CMD --PACKET_FILTER --SET_RESET_PACKET_FILTER 1 --PACKET_FILTER_SIZE 0 --END_CMD'
    cmd_get = '-i wlan0 --START_CMD --PACKET_FILTER --SET_RESET_PACKET_FILTER 2 --END_CMD'
    cmd_invalid_mode = '-i wlan2 --START_CMD --PACKET_FILTER --SET_RESET_PACKET_FILTER 1 --END_CMD'

    dev[0].scan()

    # Not connected
    vendor_cmd_execute(dev, cmd_set, "PACKET_FILTER", ENOTSUPP)
    time.sleep(1)

    # Set success
    connect_sta_sap(dev, apdev)
    vendor_cmd_execute(dev, cmd_set, "PACKET_FILTER")
    time.sleep(1)

    # Set for SAP
    vendor_cmd_execute(dev, cmd_invalid_mode, "PACKET_FILTER", ENOTSUPP)
    time.sleep(1)

    # Get timeout
    vendor_cmd_execute(dev, cmd_get, "PACKET_FILTER", ETMO)
    time.sleep(1)

    # Get success
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_packet_filter.xml")
    try:
        vendor_cmd_execute(dev, cmd_get, "PACKET_FILTER")
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

    # Reset
    vendor_cmd_execute(dev, cmd_reset, "PACKET_FILTER")
    time.sleep(1)

def test_packet_filter_apf_30(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_PACKET_FILTER vendor command """
    """ Date: 5/29/2019 """
    cmd_write = '-i wlan0 --START_CMD --PACKET_FILTER --SET_RESET_PACKET_FILTER 3 --PACKET_FILTER_PROGRAM DEADBEEF --PACKET_FILTER_PROG_LENGTH 4 --PACKET_FILTER_CURRENT_OFFSET 0 --END_CMD'
    cmd_read = '-i wlan0 --START_CMD --PACKET_FILTER --SET_RESET_PACKET_FILTER 4 --PACKET_FILTER_SIZE 4 --PACKET_FILTER_CURRENT_OFFSET 0 --END_CMD'
    cmd_enable = '-i wlan0 --START_CMD --PACKET_FILTER --SET_RESET_PACKET_FILTER 5 --END_CMD'
    cmd_disable = '-i wlan0 --START_CMD --PACKET_FILTER --SET_RESET_PACKET_FILTER 6 --END_CMD'

    connect_sta_sap(dev, apdev)

    # Disable
    vendor_cmd_execute(dev, cmd_disable, "PACKET_FILTER")
    time.sleep(1)

    # Enable
    vendor_cmd_execute(dev, cmd_enable, "PACKET_FILTER")
    time.sleep(1)

    # Write when enabled, fail
    vendor_cmd_execute(dev, cmd_write, "PACKET_FILTER", EINVAL)
    time.sleep(1)

    # Read when enabled, fail
    vendor_cmd_execute(dev, cmd_read, "PACKET_FILTER", EINVAL)
    time.sleep(1)

    vendor_cmd_execute(dev, cmd_disable, "PACKET_FILTER")
    time.sleep(1)

    # Write when disabled, success
    vendor_cmd_execute(dev, cmd_write, "PACKET_FILTER")
    time.sleep(1)

    # Read when disabled, timeout
    vendor_cmd_execute(dev, cmd_read, "PACKET_FILTER", ETMO)
    time.sleep(1)

    # Read when disabled, success
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_packet_filter.xml")
    try:
        vendor_cmd_execute(dev, cmd_read, "PACKET_FILTER")
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

def test_scan_followed_by_start_beacon_reporting(dev, apdev):
    """ Test case for scan followed by QCA_NL80211_VENDOR_SUBCMD_BEACON_REPORTING vendor command """
    """ Date: 12/27/2019 """
    """ Simulated CR: 2578642 """
    cmd = '-i wlan0 --START_CMD --BEACON_REPORTING  --BEACON_REPORTING_OP_TYPE 0 --BEACON_REPORTING_ACTIVE_REPORTING 1 --END_CMD'
    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")
    log.start_monitoring()

    try:
        dev[0].scan(no_wait=True)
        vendor_cmd_execute(dev, cmd, "BEACON_REPORTING", EBUSY)
        time.sleep(.1)
        res = []
        count, res = log.find_string("__wlan_hdd_cfg80211_bcn_rcv_op")
        if count == 0:
            raise Exception("BEACON REPORTING START vendor command not working")
        if not [s for s in res if "Scan in progress" in s]:
            raise Exception("BEACON REPORTING START did not get aborted")
    finally:
        dev[0].request("DISCONNECT")
        dev[0].wait_disconnected()

def test_start_beacon_reporting(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_BEACON_REPORTING vendor command """
    """ Date: 06/06/2019 """
    cmd = '-i wlan0 --START_CMD --BEACON_REPORTING  --BEACON_REPORTING_OP_TYPE 0 --BEACON_REPORTING_ACTIVE_REPORTING 1 --END_CMD'
    whunt_daemon_util.wcd_cli_load_test('0','beacon_reporting.xml')
    connect_sta_sap(dev, apdev)
    whunt_daemon_util.wcd_cli_set_cfg('log_level', '4')
    log = LogVerify("DRIVER", "wlan0")
    log.start_monitoring()
    try:
        vendor_cmd_execute(dev, cmd, "BEACON_REPORTING")
        time.sleep(.1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test('0')
    count, res = log.find_string("Setting vdev")
    if count == 0:
        raise Exception("Send WMI command WMI_VDEV_SET_PARAM_CMDID Failed")
    if not [s for s in res if "value = 2147483649" in s]:
        raise Exception("BEACON REPORTING START vendor command not working")

def test_stop_beacon_reporting(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_BEACON_REPORTING vendor command """
    """ Date: 06/06/2019 """
    cmd1 = '-i wlan0 --START_CMD --BEACON_REPORTING  --BEACON_REPORTING_OP_TYPE 0 --BEACON_REPORTING_ACTIVE_REPORTING 1 --END_CMD'
    cmd2 = '-i wlan0 --START_CMD --BEACON_REPORTING  --BEACON_REPORTING_OP_TYPE 1 --END_CMD'
    whunt_daemon_util.wcd_cli_set_cfg('log_level', '4')
    whunt_daemon_util.wcd_cli_load_test('0','beacon_reporting.xml')
    connect_sta_sap(dev, apdev)
    log1 = LogVerify("DRIVER", "wlan0")
    log1.start_monitoring()
    try:
        vendor_cmd_execute(dev, cmd1, "BEACON_REPORTING")
        time.sleep(.1)
        res1 = []
        count1, res1 = log1.find_string("Setting vdev")
        if count1 == 0:
            raise Exception("Send WMI command WMI_VDEV_SET_PARAM_CMDID Failed")
        if not [s for s in res1 if "value = 2147483649" in s]:
            raise Exception("BEACON REPORTING START vendor command not working")
        log1.start_monitoring()
        vendor_cmd_execute(dev, cmd2, "BEACON_REPORTING")
        time.sleep(.1)
        res2 = []
    finally:
        whunt_daemon_util.wcd_cli_unload_test('0')
    count2, res2 = log1.find_string("ucfg_scan_unregister_event_handler")
    if count2 == 0:
        raise Exception("BEACON REPORTING STOP vendor command not working")
    if not [s for s in res2 if "removed" in s]:
        raise Exception("BEACON REPORTING STOP vendor command not working")

    reload_driver("wlan0", "stop_beacon_reporting")

def test_start_beacon_reporting_followed_by_scan(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_BEACON_REPORTING vendor command followed by scan """
    """ Date: 06/06/2019 """
    cmd = '-i wlan0 --START_CMD --BEACON_REPORTING  --BEACON_REPORTING_OP_TYPE 0 --BEACON_REPORTING_ACTIVE_REPORTING 1 --END_CMD'
    whunt_daemon_util.wcd_cli_set_cfg('log_level', '4')
    whunt_daemon_util.wcd_cli_load_test('0','beacon_reporting.xml')
    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")
    log.start_monitoring()
    try:
        vendor_cmd_execute(dev, cmd, "BEACON_REPORTING")
        time.sleep(.1)
        res1 = []
        count1, res1 = log.find_string("Setting vdev")
        if count1 == 0:
            raise Exception("Send WMI command WMI_VDEV_SET_PARAM_CMDID Failed")
        if not [s for s in res1 if "value = 2147483649" in s]:
            raise Exception("BEACON REPORTING START vendor command not working")
        dev[0].scan(no_wait=True)
    finally:
        whunt_daemon_util.wcd_cli_unload_test('0')
    res2 = []
    count2, res2 = log.find_string("WMI_START_SCAN_CMDID")
    if count2 == 0:
        raise Exception("BEACON_REPORTING_OP_PAUSE vendor event not working")
    reload_driver("wlan0", "start_beacon_reporting_followed_by_scan")

def test_start_beacon_reporting_followed_by_disconnect(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_BEACON_REPORTING vendor command followed by disconnection """
    """ Date: 06/06/2019 """
    cmd = '-i wlan0 --START_CMD --BEACON_REPORTING  --BEACON_REPORTING_OP_TYPE 0 --BEACON_REPORTING_ACTIVE_REPORTING 1 --END_CMD'
    whunt_daemon_util.wcd_cli_set_cfg('log_level', '4')
    whunt_daemon_util.wcd_cli_load_test('0','beacon_reporting.xml')
    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")
    log.start_monitoring()
    try:
        vendor_cmd_execute(dev, cmd, "BEACON_REPORTING")
        time.sleep(.1)
        res1 = []
        count1, res1 = log.find_string("Setting vdev")
        if count1 == 0:
            raise Exception("Send WMI command WMI_VDEV_SET_PARAM_CMDID Failed")
        if not [s for s in res1 if "value = 2147483649" in s]:
            raise Exception("BEACON REPORTING START vendor command not working")

        dev[0].request("DISCONNECT")
        ev = dev[0].wait_event(["CTRL-EVENT-DISCONNECTED"], timeout=20)
        if ev is None:
            raise Exception("No disconnection event received")
    finally:
        whunt_daemon_util.wcd_cli_unload_test('0')
    count2, res2 = log.find_string("hdd_dis_connect_handler")
    count3, res3 = log.find_string("__hdd_cm_disconnect_handler_post_user_update")
    if count2 == 0 and count3 == 0:
        raise Exception("BEACON_REPORTING_OP_PAUSE vendor event not working")
    reload_driver("wlan0", "start_beacon_reporting_followed_by_disconnect")

def test_start_beacon_reporting_followed_by_p2p_scan(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_BEACON_REPORTING vendor command followed by p2p scan """
    """ Date: 12/27/2019 """
    """ Simulated CR: 2582389 """

    cmd = '-i wlan0 --START_CMD --BEACON_REPORTING  --BEACON_REPORTING_OP_TYPE 0 --BEACON_REPORTING_ACTIVE_REPORTING 1 --END_CMD'
    whunt_daemon_util.wcd_cli_set_cfg('log_level', '4')
    whunt_daemon_util.wcd_cli_load_test('0','beacon_reporting.xml')
    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")
    log.start_monitoring()

    try:
        vendor_cmd_execute(dev, cmd, "BEACON_REPORTING")
        time.sleep(0.1)
        dev[1].p2p_find(social=True)
        time.sleep(0.1)

        res = False
        for i in range(10):
            count1, srt1 = log.find_string("ucfg_scan_register_event_handler")
            if count1:
                res = True
                break
            time.sleep(.1)
        if not res:
            raise Exception("BEACON REPORTING START vendor command not working")

        res2 = False
        for i in range(10):
            count2, str2 = log.find_string("sme_scan_event_handler")
            if not [s for s in str2 if "Send" in s]:
                time.sleep(.1)
            else:
                res2 = True
                break
        if not res2:
            raise Exception("BEACON_REPORTING_OP_PAUSE vendor event not working")

    finally:
        dev[0].request("DISCONNECT")
        dev[0].wait_disconnected()
        whunt_daemon_util.wcd_cli_unload_test('0')

def test_sta_connect_roam_policy(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_STA_CONNECT_ROAM_POLICY vendor command """
    """ Date: 06/06/2019 """
    cmd = '-i wlan0 --START_CMD --STA_CONNECT_ROAM_POLICY  --STA_DFS_MODE 1 --STA_SKIP_UNSAFE_CHANNEL 1 --END_CMD'
    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")
    log.start_monitoring()
    vendor_cmd_execute(dev, cmd, "STA_CONNECT_ROAM_POLICY")
    time.sleep(.1)
    dev[0].scan(no_wait=True)
    res = []
    count, res = log.find_string("wlan_cm_roam_cmd_allowed")
    res2 = []
    count2, res2 = log.find_string("cm_roam_cmd_allowed")
    if count == 0 and count2 == 0:
        raise Exception("Error while updating sta-roam policy")

    reason1 = True
    if not [s for s in res if "Reason" in s and "35" in s]:
        reason1 = False

    reason2 = True
    if not [s for s in res2 if "Reason" in s and "35" in s]:
        reason2 = False

    if reason1 == False and reason2 == False:
            raise Exception("Fail to send roam scan offload with reason REASON_ROAM_SCAN_STA_ROAM_POLICY_CHANGED")

    reload_driver("wlan0", "sta_connect_roam_policy")

def test_ocb_set_config(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_OCB_SET_CONFIG vendor command """
    """ Date: 06/06/2019 """
    cmd = '-i wlanocb0 --START_CMD --OCB_SET_CONFIG --CHANNEL_COUNT 1 --SCHEDULE_SIZE 1 --CHANNEL_ARRAY E41600000A0000000000000000000102030102030102034000000040000000 --SCHEDULE_ARRAY 01020304 --NDL_CHANNEL_ARRAY 01020304 --NDL_ACTIVE_STATE_ARRAY 01020304 --FLAGS 0 --END_CMD'

    ini = Ini("wlan")
    ini.change_ini("gDot11PMode", 1, load=True)

    dev[0].cmd_execute(['ifconfig', 'wlanocb0', 'up'])
    time.sleep(1)

    try:
        vendor_cmd_execute(dev, cmd, "OCB_SET_CONFIG")
        time.sleep(1)
    finally:
        dev[0].cmd_execute(['ifconfig', 'wlanocb0', 'down'])
        time.sleep(1)
        ini.restore_ini()
        time.sleep(1)

def test_ocb_set_utc_time(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_OCB_SET_UTC_TIME vendor command """
    """ Date: 06/06/2019 """
    cmd = '-i wlanocb0 --START_CMD --OCB_SET_UTC_TIME --UTC_TIME_VALUE 0102030405060708090A --UTC_TIME_ERROR 0102030405 --END_CMD'

    ini = Ini("wlan")
    ini.change_ini("gDot11PMode", 1, load=True)

    dev[0].cmd_execute(['ifconfig', 'wlanocb0', 'up'])
    time.sleep(1)

    try:
        vendor_cmd_execute(dev, cmd, "OCB_SET_UTC_TIME")
        time.sleep(1)
    finally:
        dev[0].cmd_execute(['ifconfig', 'wlanocb0', 'down'])
        time.sleep(1)
        ini.restore_ini()
        time.sleep(1)

def test_ocb_timing_advert(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_OCB_START_TIMING_ADVERT and QCA_NL80211_VENDOR_SUBCMD_OCB_STOP_TIMING_ADVERT vendor command """
    """ Date: 06/06/2019 """
    cmd_start = '-i wlanocb0 --START_CMD --OCB_START_TIMING_ADVERT --CHANNEL_FREQ 5860 --REPEAT_RATE 5 --END_CMD'
    cmd_stop = '-i wlanocb0 --START_CMD --OCB_STOP_TIMING_ADVERT --CHANNEL_FREQ 5860 --END_CMD'

    ini = Ini("wlan")
    ini.change_ini("gDot11PMode", 1, load=True)

    dev[0].cmd_execute(['ifconfig', 'wlanocb0', 'up'])
    time.sleep(1)

    try:
        vendor_cmd_execute(dev, cmd_start, "OCB_START_TIMING_ADVERT")
        time.sleep(1)

        vendor_cmd_execute(dev, cmd_stop, "OCB_START_TIMING_ADVERT")
        time.sleep(1)
    finally:
        dev[0].cmd_execute(['ifconfig', 'wlanocb0', 'down'])
        time.sleep(1)
        ini.restore_ini()
        time.sleep(1)

def test_set_sap_config(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_SET_SAP_CONFIG vendor command """
    """ Date: 06/06/2019 """
    cmd = '-i wlan2 --START_CMD --SET_SAP_CONFIG --SAP_CONFIG_CHANNEL 6 --MANDATORY_FREQUENCY_LIST 6C090000 --END_CMD'
    cmd_invalid_channel = '-i wlan2 --START_CMD --SET_SAP_CONFIG --SAP_CONFIG_CHANNEL 0 --END_CMD'
    cmd_invalid_freq = '-i wlan2 --START_CMD --SET_SAP_CONFIG --MANDATORY_FREQUENCY_LIST FFFFFFFF --END_CMD'
    cmd_invalid_freq_len = '-i wlan2 --START_CMD --SET_SAP_CONFIG --MANDATORY_FREQUENCY_LIST ABCD --END_CMD'

    params = { "ssid": "WHUNT_OPEN",
               "ieee80211n" : "1",
               "hw_mode" : "g",
               "channel": "1"}
    hapd = hostapd.add_ap(apdev[0], params)
    log = LogVerify("DRIVER", "wlan2")

    # SAP started
    log.start_monitoring()
    vendor_cmd_execute(dev, cmd, "SET_SAP_CONFIG")
    time.sleep(1)

    count, res = log.find_string("hdd_restart_sap")
    if count == 0:
        raise Exception("SET_SAP_CONFIG vendor command not working")

    count, res = log.find_string("policy_mgr_set_sap_mandatory_channels")
    if count == 0:
        raise Exception("SET_SAP_CONFIG vendor command not working")

    # Invalid channel
    vendor_cmd_execute(dev, cmd_invalid_channel, "SET_SAP_CONFIG", ENOTSUPP)
    time.sleep(1)

    # Invalid Frequency
    vendor_cmd_execute(dev, cmd_invalid_freq, "SET_SAP_CONFIG", EINVAL)
    time.sleep(1)

    # Invalid Frequency Length
    vendor_cmd_execute(dev, cmd_invalid_freq_len, "SET_SAP_CONFIG", EINVAL)
    time.sleep(1)

    hapd.disable()

    # SAP not started
    vendor_cmd_execute(dev, cmd, "SET_SAP_CONFIG", EINVAL)
    time.sleep(1)

def test_wisa(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_WISA vendor command """
    """ Date: 06/06/2019 """
    cmd = '-i wlan0 --START_CMD --WISA --WISA_MODE 1 --END_CMD'

    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd, "WISA")
    time.sleep(1)

def test_ll_stats_ext(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_LL_STATS_EXT vendor command """
    """ Date: 06/06/2019 """
    cmd_period = '-i wlan0 --START_CMD --LL_STATS_EXT --CFG_PERIOD 1 --END_CMD'
    cmd_threshold = '-i wlan0 --START_CMD --LL_STATS_EXT --CFG_THRESHOLD 100 --GLOBAL 100 --TX_BITMAP 7 --RX_BITMAP 7 --CCA_BSS_BITMAP 7 --SIGNAL_BITMAP 7 --TX_MSDU 100 --TX_MPDU 100 --TX_PPDU 100 --TX_BYTES 100 --TX_DROP 100 --TX_DROP_BYTES 100 --TX_RETRY 100 --TX_NO_ACK 100 --TX_NO_BACK 100 --TX_AGGR 100 --TX_SUCC_MCS 100 --TX_FAIL_MCS 100 --TX_DELAY 100 --RX_MPDU 100 --RX_MPDU_BYTES 100 --RX_PPDU 100 --RX_PPDU_BYTES 100 --RX_MPDU_LOST 100 --RX_MPDU_RETRY 100 --RX_MPDU_DUP 100 --RX_MPDU_DISCARD 100 --RX_MCS 100 --RX_AGGR 100 --PEER_PS_TIMES 100 --PEER_PS_DURATION 100 --RX_PROBE_REQ 100 --RX_MGMT 100 --IDLE_TIME 100 --TX_TIME 100 --RX_BUSY 100 --RX_BAD 100 --TX_BAD 100 --NO_AVAIL 100 --IN_BSS_TIME 100 --OUT_BSS_TIME 100 --ANT_SNR 50 --ANT_NF 20 --END_CMD'
    cmd_threshold_disable = '-i wlan0 --START_CMD --LL_STATS_EXT --END_CMD'

    connect_sta_sap(dev, apdev)

    # Set period
    vendor_cmd_execute(dev, cmd_period, "LL_STATS_EXT")
    time.sleep(1)

    # Set threshold
    vendor_cmd_execute(dev, cmd_threshold, "LL_STATS_EXT")
    time.sleep(1)

    # Disable threshold
    vendor_cmd_execute(dev, cmd_threshold_disable, "LL_STATS_EXT")
    time.sleep(1)

def test_sar_set(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_SET_SAR_LIMITS vendor command """
    """ Date: 06/14/2019 """

    connect_sta_sap(dev, apdev)
    cmd = '-i wlan0 --START_CMD --SAR_SET --ENABLE 1 --NUM_SPECS 1 --SAR_SPEC --NESTED_AUTO --BAND 0 --CHAIN 0 --MOD 0 --POW 1 --POW_IDX 1 --END_ATTR --END_ATTR --END_CMD'

    vendor_cmd_execute(dev, cmd, "SAR_SET")

def test_get_supported_features(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_GET_SUPPORTED_FEATURES vendor command """
    """ Date: 06/17/2019 """
    cmd = '-i wlan0 --START_CMD --GET_SUPPORTED_FEATURES --END_CMD'
    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd, "GET_SUPPORTED_FEATURES")

def test_extscan_set_passpoint_list(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_EXTSCAN_PNO_SET_PASSPOINT_LIST vendor command """
    """ Date: 06/21/2019 """
    cmd = "-i wlan0 --START_CMD --EXTSCAN_PNO_SET_PASSPOINT_LIST --PNO_PASSPOINT_LIST_PARAM_NUM 1 --PASSPOINT_LIST_PARAM_NETWORK_ARRAY --NESTED_AUTO --PNO_PASSPOINT_NETWORK_PARAM_ID 1 --PNO_PASSPOINT_NETWORK_PARAM_REALM google.com --PASSPOINT_NETWORK_PARAM_ROAM_CNSRTM_ID 0x1234 --PNO_PASSPOINT_NETWORK_PARAM_ROAM_PLMN 0x1234 --END_ATTR --END_ATTR --END_CMD"
    
    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd, "EXTSCAN_PNO_SET_PASSPOINT_LIST")
    
def test_gw_param_config(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_GW_PARAM_CONFIG vendor command """
    """ Date 6/25/2019 """
    cmd = '-i wlan0 --START_CMD --GW_PARAM_CONFIG --PARAM_MAC_ADDR "000af58989ff" --PARAM_IPV4_ADDR AACCBBDD --PARAM_IPV6_ADDR AABBCCDDEEFFAABBCCDDAABBCCDDFFEE --END_CMD'
    connect_sta_sap(dev, apdev)

    vendor_cmd_execute(dev, cmd, "GW_PARAM_CONFIG")

def test_nud_stats_set(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_NUD_STATS_SET vendor command """
    """ Date 6/25/2019 """
    cmd_enable = '-i wlan0 --START_CMD --NUD_STATS_SET --STATS_SET_START 1 --STATS_GW_IPV4 3232235777 --STATS_SET_DATA_PKT_INFO --NESTED_AUTO --STATS_PKT_INFO_TYPE 255 --STATS_DNS_DOMAIN_NAME "www.google.com" --STATS_SRC_PORT 256 --STATS_DEST_PORT 36115 --STATS_DEST_IPV4 3232235777 --STATS_DEST_IPV6 0 --END_ATTR --END_ATTR --END_CMD'

    cmd_disable = '-i wlan0 --START_CMD --NUD_STATS_SET --STATS_SET_DATA_PKT_INFO --NESTED_AUTO --STATS_PKT_INFO_TYPE 255 --END_ATTR --END_ATTR --END_CMD'

    cmd_gw_enable = '-i wlan0 --START_CMD --NUD_STATS_SET --STATS_SET_START 1 --STATS_GW_IPV4 3232235777 --END_CMD'

    cmd_gw_disable = '-i wlan0 --START_CMD --NUD_STATS_SET --STATS_GW_IPV4 3232235777 --END_CMD'

    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")

    # Enable data packet stats
    log.start_monitoring()
    vendor_cmd_execute(dev, cmd_enable, "NUD_STATS_SET")
    time.sleep(1)

    count, res = log.find_string("STATS_SET_START Received flag 1!")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    count, res = log.find_string("Connectivity Stats:")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    count, res = log.find_string("WMI_VDEV_SET_ARP_STAT_CMDID")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    # Disable data packet stats
    log.start_monitoring()
    vendor_cmd_execute(dev, cmd_disable, "NUD_STATS_SET")
    time.sleep(1)

    count, res = log.find_string("STATS_SET_START Received flag 0!")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    count, res = log.find_string("Connectivity Stats:")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    count, res = log.find_string("WMI_VDEV_SET_ARP_STAT_CMDID")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    # Enable GW packet stats
    log.start_monitoring()
    vendor_cmd_execute(dev, cmd_gw_enable, "NUD_STATS_SET")
    time.sleep(1)

    count, res = log.find_string("STATS_SET_START Received flag 1!")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    count, res = log.find_string("Connectivity Stats:")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    count, res = log.find_string("WMI_VDEV_SET_ARP_STAT_CMDID")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    # Disable GW packet stats
    log.start_monitoring()
    vendor_cmd_execute(dev, cmd_gw_disable, "NUD_STATS_SET")
    time.sleep(1)

    count, res = log.find_string("STATS_SET_START Received flag 0!")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    count, res = log.find_string("Connectivity Stats:")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

    count, res = log.find_string("WMI_VDEV_SET_ARP_STAT_CMDID")
    if count == 0:
        raise Exception("NUD_STATS_SET vendor command not working")

def test_nud_stats_get(dev, apdev):
    """ Test case for QCA_NL80211_VENDOR_SUBCMD_NUD_STATS_GET vendor command """
    """ Date 7/12/2019 """
    cmd = '-i wlan0 --START_CMD --NUD_STATS_GET --END_CMD'

    whunt_daemon_util.wcd_cli_load_test('0','get_nud_stats.xml')
    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")

    # Enable data packet stats
    log.start_monitoring()
    try:
        vendor_cmd_execute(dev, cmd, "NUD_STATS_GET")
        time.sleep(1)
    finally:
        whunt_daemon_util.wcd_cli_unload_test('0')

    count, res = log.find_string("WMI_VDEV_GET_ARP_STAT_CMDID")
    if count == 0:
        raise Exception("NUD_STATS_GET vendor command not working")

    count, res = log.find_string("hdd_get_nud_stats_cb")
    if count == 0:
        raise Exception("NUD_STATS_GET vendor command not working")

    count, res = log.find_string("rsp->arp_req_enqueue")
    if count == 0:
        raise Exception("NUD_STATS_GET vendor command not working")

    count, res = log.find_string("rsp->ba_session_establishment_status")
    if count == 0:
        raise Exception("NUD_STATS_GET vendor command not working")

def test_disconnect_ies_set(dev, apdev):
    """ Test case for @QCA_NL80211_VENDOR_SUBCMD_SET_WIFI_CONFIGURATION: vendor command with DISCONNECT_IES attribute"""
    """ Date: 06/28/2019 """

    params = { "ssid":"WHUNT_OPEN" }
    hapd = hostapd.add_ap(apdev[0], params)
    dev[0].connect("WHUNT_OPEN", key_mgmt="NONE")
    ev = hapd.wait_event([ "AP-STA-CONNECTED" ], timeout=5)
    if ev is None:
        raise Exception("No connection event received from hostapd")
    hwsim_utils.test_connectivity(dev[0], hapd)

    log = LogVerify("DRIVER", "wlan0")
    log.start_monitoring()
    cmd = '-i wlan0 --START_CMD --SET_WIFI_CONFIG --CONFIG_DISCONNECT_IES dd090000F0220301020100 --END_CMD'

    vendor_cmd_execute(dev, cmd, "SET_WIFI_CONFIG")
    count = 0
    time.sleep(1)
    count, res = log.find_string("mlme_set_self_disconnect_ies")
    if count == 0:
        raise Exception("SET_WIFI_CONFIGURATION with DISCONNECT_IES attribute is not working")

    log.start_monitoring()
    dev[0].request("DISCONNECT")
    dev[0].wait_disconnected()
    count, res = log.find_string("lim_append_ies_to_frame")
    if count == 0:
        raise Exception("Not able to send disconnect IEs to AP")
    dev[0].request("RECONNECT")
    ev = hapd.wait_event([ "AP-STA-CONNECTED" ], timeout=5)
    if ev is None:
        raise Exception("No connection event received from hostapd")

    log.start_monitoring()
    dev[0].request("DISCONNECT")
    dev[0].wait_disconnected()
    count, res = log.find_string("lim_append_ies_to_frame")
    if count != 0:
        raise Exception("IEs are one time usable; We are not supposed to send disconnect IEs to AP again")
    dev[0].request("RECONNECT")
    ev = hapd.wait_event([ "AP-STA-CONNECTED" ], timeout=5)
    if ev is None:
        raise Exception("No connection event received from hostapd")

def test_send_ani_level_cmd(dev, apdev):
    """ Test case for wpa_cli DRIVER GET_ANI_LEVEL <num of freqs> <freq list> """
    """ Date: 01/13/2020 """

    connect_sta_sap(dev, apdev)
    log = LogVerify("DRIVER", "wlan0")
    whunt_daemon_util.wcd_cli_set_cfg('log_level', '4')

    #Invalid cases
    log.start_monitoring()
    dev[0].request("DRIVER GET_ANI_LEVEL 2 2412")
    dev[0].request("DRIVER GET_ANI_LEVEL 30 1000 1000")
    dev[0].request("DRIVER GET_ANI_LEVEL 0")
    dev[0].request("DRIVER GET_ANI_LEVEL 1")
    dev[0].request("DRIVER GET_ANI_LEVEL 1 abcd")
    dev[0].request("DRIVER GET_ANI_LEVEL 1 2412 2412")
    count, res = log.find_string("WMI_GET_CHANNEL_ANI_CMDID")
    if count != 0:
        raise Exception("Invalid command being processed")

    #Valid case - No response from FW
    log.start_monitoring()
    dev[0].request("DRIVER GET_ANI_LEVEL 2 2412 5180")
    count, res = log.find_string("WMI_GET_CHANNEL_ANI_CMDID")
    if count == 0:
        raise Exception("Command not sent to the FW")
    count, res = log.find_string("Unable to retrieve ani level")
    if count == 0:
        raise Exception("Error in response path")


    #Valid case - Response from FW
    whunt_daemon_util.wcd_cli_load_test(core_id="0", test_xml="vendor_cmd_get_ani_level.xml")
    try:
        log.start_monitoring()
        dev[0].request("DRIVER GET_ANI_LEVEL 2 2412 5180")
        count, res = log.find_string("WMI_GET_CHANNEL_ANI_CMDID")
        if count == 0:
            raise Exception("Command not sent to the FW")
        count, res = log.find_string("Unable to retrieve ani level")
        if count != 0:
            raise Exception("No Response from FW")

    finally:
        whunt_daemon_util.wcd_cli_unload_test(core_id="0")

def test_chan_list0(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ end > start case testing """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 2437 --FREQ_END 2412 --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list1(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ corner case overlap testing 1 """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 5785 --FREQ_END 5796 --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list2(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ whether same band case testing """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 2412 --FREQ_END 5745 --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list3(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ Date: 7/05/2021 """
    """ 2.4g case testing """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 2412 --FREQ_END 2417 --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list4(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ Date: 7/05/2021 """
    """ 5g inside case testing """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 5755 --FREQ_END 5775 --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list5(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ Date: 7/05/2021 """
    """ corner case 5170-5190 testing 2"""
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 5180 --FREQ_END 5180 --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list6(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ missing END """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 2437 --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list7(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ missing START """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_END 2437 --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list8(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ bigger than 2.4g max freq """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 2462 --FREQ_END 2489 --END_ATTR --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list9(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ no valid center freq """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 5746 --FREQ_END 5746 --END_ATTR --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list10(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ clean avoid freq list """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --AVOID_FREQUENCY_EXT --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list11(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ multi avoid freq range list """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --AVOID_FREQUENCY_EXT --FREQ_RANGE --NESTED_AUTO --FREQ_START 2412 --FREQ_END 2417 --END_ATTR --NESTED_AUTO --FREQ_START 2452 --FREQ_END 2452 --END_ATTR --NESTED_AUTO --FREQ_START 5380 --FREQ_END 5540 --END_ATTR --NESTED_AUTO --FREQ_START 5180 --FREQ_END 5180 --END_ATTR --NESTED_AUTO --FREQ_START 5805 --FREQ_END 5805 --END_ATTR --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)

def test_chan_list12(dev, apdev):
    """ QCA_NL80211_VENDOR_SUBCMD_AVOID_FREQUENCY_EXT """
    """ multi avoid freq range list """
    cmd = '-i wlan0 --START_CMD --AVOID_FREQUENCY_EXT --AVOID_FREQUENCY_EXT --NESTED_AUTO --FREQ_START 2462 --FREQ_END 2462 --END_ATTR --END_ATTR --END_ATTR --END_CMD'
    vendor_cmd_execute(dev, cmd, "AVOID_FREQUENCY_EXT")
    time.sleep(1)
