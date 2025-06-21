LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_BASE_PRODUCT),neo_custom)

wcnss_ini := $(TARGET_OUT_VENDOR)/firmware/wlan/qca_cld/$(TARGET_WLAN_CHIP)/WCNSS_qcom_cfg.ini
$(call symlink-file,,/vendor/etc/wifi/$(TARGET_WLAN_CHIP)/WCNSS_qcom_cfg.ini, $(wcnss_ini))

include $(CLEAR_VARS)
LOCAL_MODULE := wcnss_qcom_cfg_ini_symlink
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_CLASS := DATA
LOCAL_SRC_FILES := WCNSS_qcom_cfg_kiwi_v2_neo_custom.ini
LOCAL_ADDITIONAL_DEPENDENCIES := $(wcnss_ini)
include $(BUILD_PREBUILT)
ALL_DEFAULT_INSTALLED_MODULES += $(wcnss_ini)
endif
