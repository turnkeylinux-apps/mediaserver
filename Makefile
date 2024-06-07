WEBMIN_FW_TCP_INCOMING += 8096 8920 12322

NONFREE = yes

CREDIT_ANCHORTEXT = Mediaserver Appliance

include $(FAB_PATH)/common/mk/turnkey/fileserver.mk
include $(FAB_PATH)/common/mk/turnkey/php.mk
include $(FAB_PATH)/common/mk/turnkey.mk
