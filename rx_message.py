from protocol.requests.hd_get_setup_config_msg import HDGetSetupConfigMessage
from protocol.requests.hd_get_status_msg import HDGetStatusMessage
from protocol.requests.hd_get_warning_config_msg import HDGetWarningConfigMessage
from protocol.requests.hd_get_warning_msg import HDGetWarningMessage
from protocol.requests.hd_remove_all_warnings_except_default_msg import HDRemoveAllWarningsExceptDefaultMessage
from protocol.requests.hd_remove_all_warnings_msg import HDRemoveAllWarningsMessage
from protocol.requests.hd_remove_warning_msg import HDRemoveWarningMessage
from protocol.requests.hd_set_power_msg import HDSetPowerMessage
from protocol.requests.hd_set_warning_msg import HDSetWarningMessage
from protocol.requests.hd_set_warning_to_default_msg import HDSetWarningToDefaultMessage
from protocol.requests.hd_setup_msg import HDSetupMessage
from protocol.responses.hd_get_status_response import HDGetStatusResponse
from protocol.responses.hd_get_warning_config_response import HDGetWarningConfigResponse


class IRXMessage(object):
    def is_module_in_error(self):
        pass

    def on_setup_message(self, message: HDSetupMessage):
        pass

    def on_set_warning_msg(self, message: HDSetWarningMessage):
        pass

    def on_remove_warning_msg(self, message: HDRemoveWarningMessage):
        pass

    def on_remove_all_warnings_msg(self):
        pass

    def on_remove_all_warnings_except_defaults_msg(self):
        pass

    def on_set_warning_to_default_msg(self, message: HDSetWarningToDefaultMessage):
        pass

    def on_set_power_msg(self, message: HDSetPowerMessage):
        pass

    def on_get_warning_msg(self):
        pass

    def on_get_is_system_status_ok(self):
        pass

    def on_get_warning_config_msg(self, message: HDGetWarningConfigMessage) -> HDGetWarningConfigResponse:
        pass

    def on_get_setup_config_msg(self):
        pass

    def on_get_status_msg(self) -> HDGetStatusResponse:
        pass
