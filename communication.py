"""
Created on Aug 14, 2018

@author: ziv
"""
from datetime import datetime
import serial

from messages_receiver_handler import MessagesReceiverHandler
from protocol.responses.hd_get_warning_response import HDGetWarningResponse
from utils.hd_threading import HDThread

PREAMBLE_PREFIX = b'xAA'
OPCODE_SETUP_MSG = b'0xB1'
OPCODE_SET_WARNING_MSG = b'0xB2'
OPCODE_REMOVE_WARNING_MSG = b'xB3'
OPCODE_REMOVE_ALL_WARNINGS_MSG = b'xB4'
OPCODE_REMOVE_ALL_WARNINGS_EXCEPT_DEFAULT_MSG = b'xB5'
OPCODE_SET_WARNING_TO_DEFAULT_MSG = b'0xB6'
OPCODE_SET_POWER_MSG = b'xB7'

OPCODE_GET_WARNING_MSG = b'0xB8'
OPCODE_GET_WARNING_CONFIG_MSG = b'0xB9'
OPCODE_GET_SETUP_CONFIG_MSG = b'0xBA'
OPCODE_GET_STATUS_MSG = b'0xBB'

OPCODE_GET_WARNING_RESPONSE = b'xC1'
OPCODE_GET_WARNING_CONFIG_RESPONSE = b'xC2'
OPCODE_GET_SETUP_CONFIG_RESPONSE = b'xC3'
OPCODE_GET_STATUS_RESPONSE = b'xC4'

OPCODE_ACK_RESPONSE = b'xD1'
OPCODE_NACK_RESPONSE = b'xD2'

BAUD_RATE = 19200


# ROBOT_STOP_MESSAGE_HEX = "\xAA\x09\x1E\x15\x0F\xAA\x00\xFF\x61"
# ROBOT_STATUS_MESSAGE_HEX = "\xAA\x09\x1E\x16\x0F\xA7\x00\x04\x5E"

class Communication(HDThread):
    def __init__(self, thread_name, logging, messages_receiver_handler):
        super().__init__(thread_name, logging)
        self.logging.info("{} - Init. fps={}".format(thread_name, 0))
        self.messages_receiver_handler = messages_receiver_handler  # type: MessagesReceiverHandler
        self.ser = serial.Serial(  # ttyUSB0 for USB port / ttyS0 for IO
            port='/dev/ttyUSB0',
            baudrate=BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )

    def _run(self) -> None:
        self._communication()

    def _communication(self):
        self.logging.info("Communication - Start ")
        process_start = datetime.now()

        # read message
        length, opcode = self.handle_message_header()
        response = self.handle_message_body(length, opcode)

        # send reply message
        msg = self.ser.write(response)

        msg_encoded = msg.encode("hex")
        self.logging.info("DNN - Received Ack Message from Robot: " + msg_encoded)
        self.logging.info("Communication - End. Duration=" + str(datetime.now() - process_start))

    def read_header(self):
        self.logging.info("Communication - blocked for read(3)")
        msg = self.ser.read(3)
        msg_in_hex = hex(int.from_bytes(msg, byteorder='little'))
        self.logging.info("Communication - received message - read 3 bytes: {}".format(msg_in_hex))
        return msg_in_hex

    def handle_message_header(self):
        # read first 3 bytes - msg[0]=preamble; msg[1]=length; msg[2]=opcode
        msg_in_hex = self.read_header()
        # read preamble
        if msg_in_hex[0] != PREAMBLE_PREFIX:
            self.logging.error("Communication error reading Preamble. Expected=0xAA. Received={}".format(msg_in_hex[0]))
            return
        # read length
        length = int.from_bytes(msg_in_hex[1], byteorder='little')
        # read opcode
        opcode = int.from_bytes(msg_in_hex[2], byteorder='little')
        return length, opcode

    def handle_message_body(self, length, opcode):
        # continue reading message - minus 3 bytes: preamble + length + opcode
        msg = self.ser.read(length - 3)

        # handle message
        try:
            if opcode == OPCODE_SETUP_MSG:
                self.messages_receiver_handler.handle_setup_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_SET_WARNING_MSG:
                self.messages_receiver_handler.handle_set_warning_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_REMOVE_WARNING_MSG:
                self.messages_receiver_handler.handle_remove_warning_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_REMOVE_ALL_WARNINGS_MSG:
                self.messages_receiver_handler.handle_remove_all_warnings_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_REMOVE_ALL_WARNINGS_EXCEPT_DEFAULT_MSG:
                self.messages_receiver_handler.handle_remove_all_warnings_except_defaults_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_SET_WARNING_TO_DEFAULT_MSG:
                self.messages_receiver_handler.handle_set_warning_to_default_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_SET_POWER_MSG:
                self.messages_receiver_handler.handle_set_power_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)

            # RESPONSE DIFFERENT FROM ACK
            elif opcode == OPCODE_GET_WARNING_MSG:
                warning_response = self.messages_receiver_handler.handle_get_warning_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_WARNING_RESPONSE,
                                                                                 warning_response.to_bytes())
            elif opcode == OPCODE_GET_WARNING_CONFIG_MSG:
                warning_response = self.messages_receiver_handler.handle_get_warning_config_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_WARNING_CONFIG_RESPONSE,
                                                                                 warning_response.to_bytes())
            elif opcode == OPCODE_GET_SETUP_CONFIG_MSG:
                warning_response = self.messages_receiver_handler.handle_get_setup_config_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_SETUP_CONFIG_RESPONSE,
                                                                                 warning_response.to_bytes())
            elif opcode == OPCODE_GET_STATUS_MSG:
                warning_response = self.messages_receiver_handler.handle_get_status_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_STATUS_RESPONSE,
                                                                                 warning_response.to_bytes())

        except:
            response = self.messages_receiver_handler.build_response_message(OPCODE_NACK_RESPONSE)

        return response
