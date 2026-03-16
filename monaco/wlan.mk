WLAN_CHIPSET := qca_cld3

# WLAN wear specific defconfig
WLAN_PROFILE := wear

#WPA
WPA := wpa_cli

WLAN_MODULES_VENDOR += $(WLAN_CHIPSET)_wlan.ko
WLAN_MODULES_VENDOR += wifilearner
WLAN_MODULES_VENDOR += init.vendor.wlan.rc
WLAN_MODULES_VENDOR += wificfrtool
WLAN_MODULES_VENDOR += ctrlapp_dut
ifneq ($(wildcard $(QCPATH)/wlan/oem/oem-ss),)
WLAN_MODULES_VENDOR += libwpa_drv_oem
endif
ifneq ($(wildcard $(QCPATH)/wlan/oem/oem-hmd),)
WLAN_MODULES_VENDOR += libwpa_drv_oem_hmd
endif
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
WLAN_MODULES_VENDOR += android.hardware.wifi-service
WLAN_MODULES_VENDOR += $(WPA)

#Enable rc file from wpa_supplicant
WIFI_HIDL_UNIFIED_SUPPLICANT_SERVICE_RC_ENTRY ?= true

ifneq ($(TARGET_SUPPORTS_WEARABLES),true)
#Enable WIFI AWARE FEATURE
WIFI_HIDL_FEATURE_AWARE := true
endif

ifeq ($(BOARD_WLAN_DIR),)
    BOARD_WLAN_DIR := device/qcom/wlan
endif

PRODUCT_COPY_FILES += \
	$(BOARD_WLAN_DIR)/monaco/WCNSS_qcom_cfg.ini:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/WCNSS_qcom_cfg.ini \
	$(BOARD_WLAN_DIR)/monaco/wpa_supplicant_overlay.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/wpa_supplicant_overlay.conf \
	$(BOARD_WLAN_DIR)/monaco/p2p_supplicant_overlay.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/p2p_supplicant_overlay.conf \
	$(BOARD_WLAN_DIR)/monaco/icm.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/icm.conf

ifneq ($(TARGET_SUPPORTS_WEARABLES),true)
PRODUCT_COPY_FILES += \
	frameworks/native/data/etc/android.hardware.wifi.aware.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.aware.xml \
	frameworks/native/data/etc/android.hardware.wifi.rtt.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.rtt.xml
endif

PRODUCT_PACKAGES += icnss2.ko
PRODUCT_PACKAGES += wlan_firmware_service.ko
PRODUCT_PACKAGES += cnss_prealloc.ko
PRODUCT_PACKAGES += cnss_utils.ko
PRODUCT_PACKAGES += cnss_nl.ko

PRODUCT_SOONG_NAMESPACES += \
    hardware/qcom/wlan \
    hardware/qcom/wlan/qcwcn

WLAN_PLATFORM_KBUILD_OPTIONS := CONFIG_CNSS_OUT_OF_TREE=y CONFIG_ICNSS2=m \
				CONFIG_ICNSS2_QMI=y CONFIG_CNSS_QMI_SVC=m \
				CONFIG_ICNSS2_DEBUG=y CONFIG_CNSS_GENL=m \
				CONFIG_WCNSS_MEM_PRE_ALLOC=m CONFIG_CNSS_UTILS=m \
				KERNEL_SUPPORTS_NESTED_COMPOSITES=n \
				CONFIG_SLATE_MODULE_ENABLED=y

PRODUCT_PACKAGES += WifiResTarget

PRODUCT_PACKAGES +=$(WLAN_MODULES_VENDOR)

# WLAN specific aosp flag
TARGET_USES_AOSP_FOR_WLAN := false

# WLAN specific memory flag
WLAN_TARGET_MONACO_HAS_LOW_RAM := true

# Enable STA + SAP Concurrency.
WIFI_HIDL_FEATURE_DUAL_INTERFACE := true

# Enable SAP + SAP Feature.
QC_WIFI_HIDL_FEATURE_DUAL_AP := true

#Enable cal delete feature
TARGET_CAL_DATA_CLEAR := true

#Disable Perf tuner in cnss-daemon
TARGET_USES_NO_CNSS_DP := true

# Enable vendor properties.
PRODUCT_PROPERTY_OVERRIDES += \
	wifi.aware.interface=wifi-aware0
