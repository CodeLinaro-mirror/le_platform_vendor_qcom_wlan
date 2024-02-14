TARGET_WLAN_CHIP := adrastea

WLAN_CHIPSET := qca_cld3

# Force chip-specific DLKM name
TARGET_MULTI_WLAN := true

ifneq ($(TARGET_WLAN_CHIP),)
	WLAN_MODULES_VENDOR += $(foreach chip, $(TARGET_WLAN_CHIP), $(WLAN_CHIPSET)_$(chip).ko)
else
	WLAN_MODULES_VENDOR += $(WLAN_CHIPSET)_wlan.ko
endif

#WPA
WPA := wpa_cli
WLAN_MODULES_VENDOR := $(WPA)

WLAN_MODULES_VENDOR += wifilearner
#WLAN_MODULES_VENDOR += qsh_wifi_test
WLAN_MODULES_VENDOR += init.vendor.wlan.rc
WLAN_MODULES_VENDOR += wificfrtool
WLAN_MODULES_VENDOR += ctrlapp_dut
WLAN_MODULES_VENDOR += libwpa_drv_oem
WLAN_MODULES_VENDOR += libwpa_drv_oem_hmd
WLAN_MODULES_VENDOR += libtcmd
WLAN_MODULES_VENDOR += libtestcmd6174
WLAN_MODULES_VENDOR += libtlvutil
WLAN_MODULES_VENDOR += libtlv2
WLAN_MODULES_VENDOR += libdpp_manager
WLAN_MODULES_VENDOR += dppdaemon
WLAN_MODULES_VENDOR += wifimyftm
WLAN_MODULES_VENDOR += myftm
WLAN_MODULES_VENDOR += ftmdaemon
WLAN_MODULES_VENDOR += wdsdaemon
WLAN_MODULES_VENDOR += athdiag
WLAN_MODULES_VENDOR += cnss_diag
WLAN_MODULES_VENDOR += vendor_cmd_tool
WLAN_MODULES_VENDOR += hal_proxy_daemon
WLAN_MODULES_VENDOR += spectraltool
WLAN_MODULES_VENDOR += sigma_dut
WLAN_MODULES_VENDOR += e_loop
WLAN_MODULES_VENDOR += cnss-daemon
WLAN_MODULES_VENDOR += cnss_cli
WLAN_MODULES_VENDOR += pktlogconf
WLAN_MODULES_VENDOR += libcld80211
WLAN_MODULES_VENDOR += libwifi-hal-ctrl
WLAN_MODULES_VENDOR += libwifi-hal-qcom
WLAN_MODULES_VENDOR += libwifi-hal
WLAN_MODULES_VENDOR += lib_driver_cmd_qcwcn
WLAN_MODULES_VENDOR += libwpa_client
WLAN_MODULES_VENDOR += wpa_supplicant
WLAN_MODULES_VENDOR += hostapd
WLAN_MODULES_VENDOR += hostapd_cli
WLAN_MODULES_VENDOR += hs20-osu-client

#Enable WIFI AWARE FEATURE
WIFI_HIDL_FEATURE_AWARE := true

# Copy chip specific INI files if TARGET_WLAN_CHIP is defined
ifneq ($(TARGET_WLAN_CHIP),)
	PRODUCT_COPY_FILES += \
			      $(foreach chip, $(TARGET_WLAN_CHIP), \
			      device/qcom/wlan/pitti/WCNSS_qcom_cfg_$(chip).ini:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/$(chip)/WCNSS_qcom_cfg.ini)
else
	PRODUCT_COPY_FILES += \
			      device/qcom/wlan/pitti/WCNSS_qcom_cfg.ini:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/WCNSS_qcom_cfg.ini

endif

PRODUCT_COPY_FILES += \
				device/qcom/wlan/pitti/wpa_supplicant_overlay.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/wpa_supplicant_overlay.conf \
				device/qcom/wlan/pitti/p2p_supplicant_overlay.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/p2p_supplicant_overlay.conf \
				device/qcom/wlan/pitti/icm.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/icm.conf \
                                frameworks/native/data/etc/android.hardware.wifi.aware.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.aware.xml \
                                frameworks/native/data/etc/android.hardware.wifi.rtt.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.rtt.xml \
                                frameworks/native/data/etc/android.hardware.wifi.passpoint.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.passpoint.xml

# Enable STA + SAP Concurrency.
WIFI_HIDL_FEATURE_DUAL_INTERFACE := true

# Enable SAP + SAP Feature.
QC_WIFI_HIDL_FEATURE_DUAL_AP := true

# Enable vendor properties.
PRODUCT_PROPERTY_OVERRIDES += \
	wifi.aware.interface=wifi-aware0

# Enable STA + STA Feature.
QC_WIFI_HIDL_FEATURE_DUAL_STA := true

#Disable cnss-daemon QMI communication with FW
TARGET_USES_NO_FW_QMI_CLIENT := true

#Disable DMS MAC address feature in cnss-daemon
TARGET_USES_NO_DMS_QMI_CLIENT := true

#Disable subnet detection
TARGET_USES_NO_SUBNET_DETECTION := true

WLAN_MODULES_VENDOR += icnss2.ko
WLAN_MODULES_VENDOR += wlan_firmware_service.ko
WLAN_MODULES_VENDOR += cnss_nl.ko
WLAN_MODULES_VENDOR += cnss_prealloc.ko
WLAN_MODULES_VENDOR += cnss_utils.ko

PRODUCT_PACKAGES += $(WLAN_MODULES_VENDOR)
