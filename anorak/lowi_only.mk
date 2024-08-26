LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

GNSS_CFLAGS := \
    -Werror \
    -Wformat \
    -Wformat-extra-args \
    -Wunused-label \
    -Wunused-variable \
    -Wunused-function \
    -Wimplicit-fallthrough \
    -Wno-unused-parameter \
    -Wno-error=unused-parameter \
    -Wno-error=macro-redefined \
    -Wno-error=reorder \
    -Wno-error=missing-braces \
    -Wno-error=self-assign \
    -Wno-error=enum-conversion \
    -Wno-error=logical-op-parentheses \
    -Wno-error=null-arithmetic \
    -Wno-error=null-conversion \
    -Wno-error=parentheses-equality \
    -Wno-error=undefined-bool-conversion \
    -Wno-error=tautological-compare \
    -Wno-error=switch

LOWI_GPS_DIR:=$(LOCAL_PATH)/../../../../vendor/qcom/proprietary/gps-noship
LOWI_GPS_BUILD_DIR:=$(LOWI_GPS_DIR)/build

include $(LOWI_GPS_BUILD_DIR)/gnss_common_path.in
include $(LOWI_GPS_DIR)/*/lowi/Android.mk
