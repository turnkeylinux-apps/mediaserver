WEBMIN_FW_TCP_INCOMING = 22 80 135 139 443 445 8096 8920 12321 12322
WEBMIN_FW_UDP_INCOMING = 137 138

NONFREE = yes

CREDIT_ANCHORTEXT = Mediaserver Appliance

include $(FAB_PATH)/common/mk/turnkey/fileserver.mk
include $(FAB_PATH)/common/mk/turnkey/php.mk
include $(FAB_PATH)/common/mk/turnkey.mk
