from protocol.bytes_converter import IBytesConverter
from protocol.requests.hd_get_warning_config_msg import HDGetWarningConfigMessage
from protocol.requests.hd_remove_warning_msg import HDRemoveWarningMessage
from protocol.requests.hd_set_power_msg import HDSetPowerMessage
from protocol.requests.hd_set_warning_msg import HDSetWarningMessage
from protocol.requests.hd_set_warning_to_default_msg import HDSetWarningToDefaultMessage
from protocol.requests.hd_setup_msg import HDSetupMessage
from protocol.responses.hd_get_setup_config_response import HDGetSetupConfigResponse
from protocol.responses.hd_get_status_response import HDGetStatusResponse
from protocol.responses.hd_get_warning_config_response import HDGetWarningConfigResponse
from protocol.responses.hd_get_warning_response import HDGetWarningResponse
from rx_message import IRXMessage
from utils import buzzer

PREAMBLE_PREFIX = 0xAA

MSG_FIXED_LENGTH_WITHOUT_DATA = 4


class MessagesReceiverHandler(object):
    """
    This class is used for handling send/receive messages between the HD to the Robot
    """

    def __init__(self, activate_buzzer=False) -> None:
        super().__init__()
        self.rx_listeners = []
        self.activate_buzzer = activate_buzzer

    def add_rx_listeners(self, rx_listener: IRXMessage):
        self.rx_listeners.append(rx_listener)

    def handle_setup_msg(self, message):
        message_from_bytes = HDSetupMessage.from_bytes(message)
        self.activate_buzzer = message_from_bytes.activate_buzzer
        for rx_listener in self.rx_listeners:
            rx_listener.on_setup_message(message_from_bytes)

    def handle_set_warning_msg(self, message):
        message_from_bytes = HDSetWarningMessage.from_bytes(message)
        for rx_listener in self.rx_listeners:
            rx_listener.on_set_warning_msg(message_from_bytes)

    def handle_remove_warning_msg(self, message):
        message_from_bytes = HDRemoveWarningMessage.from_bytes(message)
        for rx_listener in self.rx_listeners:
            rx_listener.on_remove_warning_msg(message_from_bytes)

    def handle_remove_all_warnings_msg(self):
        for rx_listener in self.rx_listeners:
            rx_listener.on_remove_all_warnings_msg()

    def handle_remove_all_warnings_except_defaults_msg(self):
        for rx_listener in self.rx_listeners:
            rx_listener.on_remove_all_warnings_except_defaults_msg()

    def handle_set_warning_to_default_msg(self, message):
        message_from_bytes = HDSetWarningToDefaultMessage.from_bytes(message)
        for rx_listener in self.rx_listeners:
            rx_listener.on_set_warning_to_default_msg(message_from_bytes)

    def handle_set_power_msg(self, message):
        message_from_bytes = HDSetPowerMessage.from_bytes(message)
        for rx_listener in self.rx_listeners:
            rx_listener.on_set_power_msg(message_from_bytes)

    def handle_get_warning_msg(self) -> HDGetWarningResponse:
        # compose the responses from HD and from vision.
        # Both implement the same message but each will update only its relevant fields.
        # non relevant fields will be None!
        response = HDGetWarningResponse()
        for rx_listener in self.rx_listeners:
            data = rx_listener.on_get_warning_msg()  # type: HDGetWarningResponse
            if data is None:
                continue
            if data.visibility_light_level is not None:
                response.visibility_light_level = data.visibility_light_level
            if data.is_obstructed is not None:
                response.is_obstructed = data.is_obstructed
            if data.warnings is not None:
                response.warnings = data.warnings
                # operate the buzzer
                if self.activate_buzzer and response.warnings.count(True) != 0:
                    buzzer.buzz()

            # check if there are any errors in all other models - if so throw exception
            if rx_listener.is_module_in_error():
                rx_listener.in_error = False
                raise Exception("{} in Error. Send Nack".format(rx_listener.thread_name))

        return response

    def handle_get_warning_config_msg(self, message):
        message_from_bytes = HDGetWarningConfigMessage.from_bytes(message)
        response = HDGetWarningConfigResponse()
        for rx_listener in self.rx_listeners:
            data = rx_listener.on_get_warning_config_msg(message_from_bytes)
            if data is not None:
                response = data
        return response

    def handle_get_setup_config_msg(self):
        # compose the responses from HD and from vision.
        # Both implement the same message but each will update only its relevant fields.
        # non relevant fields will be None!
        response = HDGetSetupConfigResponse()
        response.activate_buzzer = self.activate_buzzer
        for rx_listener in self.rx_listeners:
            data = rx_listener.on_get_setup_config_msg()
            if data is None:
                continue
            if data.rotate_image_cycle is not None:
                response.rotate_image_cycle = data.rotate_image_cycle
            if data.obstruction_threshold is not None:
                response.obstruction_threshold = data.obstruction_threshold
            if data.no_visibility_threshold is not None:
                response.no_visibility_threshold = data.no_visibility_threshold
            if data.medium_visibility_threshold is not None:
                response.medium_visibility_threshold = data.medium_visibility_threshold
            if data.full_visibility_threshold is not None:
                response.full_visibility_threshold = data.full_visibility_threshold
            if data.minimum_obstruction_hits is not None:
                response.minimum_obstruction_hits = data.minimum_obstruction_hits
            if data.maximum_obstruction_hits is not None:
                response.maximum_obstruction_hits = data.maximum_obstruction_hits
            if data.logging_debug is not None:
                response.logging_debug = data.logging_debug
            if data.show_images is not None:
                response.show_images = data.show_images
            if data.save_images_to_disk is not None:
                response.save_images_to_disk = data.save_images_to_disk
            if data.draw_polygons is not None:
                response.draw_polygons = data.draw_polygons
            if data.rotate_degree is not None:
                response.rotate_degree = data.rotate_degree
        return response

    def handle_get_status_msg(self):
        response = HDGetStatusResponse()
        for rx_listener in self.rx_listeners:
            data = rx_listener.on_get_status_msg()
            if data is not None:
                response = data
        return response

    def build_response_message(self, opcode, data=None):
        data_length = 0 if data is None else data.__len__()
        total_msg_length = data_length + MSG_FIXED_LENGTH_WITHOUT_DATA
        res_message_bytes_array = bytearray([PREAMBLE_PREFIX, total_msg_length, opcode])
        if data is not None:
            res_message_bytes_array += data
        checksum = self.calc_checksum(res_message_bytes_array)
        res_message_bytes_array = res_message_bytes_array + checksum
        return res_message_bytes_array

    def calc_checksum(self, data):
        crc = 0
        for i in range(len(data)):
            crc += data[i]
            i += 1
        _crc = ~crc % 256
        return int.to_bytes(_crc, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
