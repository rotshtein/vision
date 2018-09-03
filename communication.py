"""
Created on Aug 14, 2018

@author: ziv
"""
import binascii
from datetime import datetime
import serial

from messages_receiver_handler import MessagesReceiverHandler
from protocol.bytes_converter import IBytesConverter
from protocol.responses.hd_get_warning_response import HDGetWarningResponse
from utils.hd_threading import HDThread


PREAMBLE_PREFIX = 0xAA
OPCODE_SETUP_MSG = 0xB1
OPCODE_SET_WARNING_MSG = 0xB2
OPCODE_REMOVE_WARNING_MSG = 0xB3
OPCODE_REMOVE_ALL_WARNINGS_MSG = 0xB4
OPCODE_REMOVE_ALL_WARNINGS_EXCEPT_DEFAULT_MSG = 0xB5
OPCODE_SET_WARNING_TO_DEFAULT_MSG = 0xB6
OPCODE_SET_POWER_MSG = 0xB7

OPCODE_GET_WARNING_MSG = 0xB8
OPCODE_GET_WARNING_CONFIG_MSG = 0xB9
OPCODE_GET_SETUP_CONFIG_MSG = 0xBA
OPCODE_GET_STATUS_MSG = 0xBB

OPCODE_GET_WARNING_RESPONSE = 0xC1
OPCODE_GET_WARNING_CONFIG_RESPONSE = 0xC2
OPCODE_GET_SETUP_CONFIG_RESPONSE = 0xC3
OPCODE_GET_STATUS_RESPONSE = 0xC4

OPCODE_ACK_RESPONSE = 0xD1
OPCODE_NACK_RESPONSE = 0xD2

BAUD_RATE = 115200
PORT = '/dev/ttyAMA0'  # COM1 / ttyUSB0 for USB port / ttyS0 for IO


# ROBOT_STOP_MESSAGE_HEX = "\xAA\x09\x1E\x15\x0F\xAA\x00\xFF\x61"
# ROBOT_STATUS_MESSAGE_HEX = "\xAA\x09\x1E\x16\x0F\xA7\x00\x04\x5E"

class Communication(HDThread):
    def __init__(self, thread_name, logging, messages_receiver_handler, port=PORT, baudrate=BAUD_RATE):
        super().__init__(thread_name, logging, 0)
        self.logging.info("{} - Init.".format(thread_name, 0))
        self.messages_receiver_handler = messages_receiver_handler  # type: MessagesReceiverHandler
        self.port = port if port is not None else PORT
        self.baudrate = int(baudrate) if baudrate is not None else BAUD_RATE
        self.ser = None
        try:
            self.ser = serial.Serial(  # ttyUSB0 for USB port / ttyS0 for IO
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
            )
            self.logging.info("{} - Initialized Serial port: port={} baudrate={}".format(thread_name, self.port, self.baudrate))
        except Exception as e:
            self.logging.info("{} - Initializing Serial port failed. {}".format(thread_name, e.__str__()))
            self.exit_thread()

    def _run(self) -> None:
        self._communication()

    def _communication(self):
        self.logging.debug("{} - Start.".format(self.thread_name))
        start_time = datetime.now()

        # read message
        if self.ser is not None:
            try:
                length, opcode = self.handle_message_header()
                response = self.handle_message_body(length, opcode)

                # send reply message
                msg = self.ser.write(response)
                # msg_encoded = msg.encode("hex")
                # self.logging.info("DNN - Received Ack Message from Robot: " + msg_encoded)
                iteration_time = datetime.now() - start_time
                self.logging.debug("{} - End. Total Duration={}".format(self.thread_name, iteration_time))
            except:
                self.ser.flushInput()

    def read_header(self):
        msg = self.ser.read(3)
        # msg_in_hex = hex(int.from_bytes(msg, byteorder=IBytesConverter.BIG_ENDIAN))
        self.logging.info("{} - read message header 3 bytes: {}".format(self.thread_name, binascii.hexlify(msg)))
        return msg

    def handle_message_header(self):
        # read first 3 bytes - msg[0]=preamble; msg[1]=length; msg[2]=opcode
        msg = self.read_header()
        # read preamble
        if msg[0] != PREAMBLE_PREFIX:
            self.logging.error("{} - error reading Preamble. Expected=0xAA. Received={}".format(self.thread_name, binascii.hexlify(msg[0])))
            return
        # read length
        length = msg[1]
        # read opcode
        opcode = msg[2]
        return length, opcode

    def handle_message_body(self, length, opcode):
        # continue reading message - minus 3 bytes: preamble + length + opcode
        msg = self.ser.read(length - 3)
        self.logging.info("{} - read message body length={}. message: {}".format(self.thread_name, length - 3, binascii.hexlify(msg)))
        response = None
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
                self.messages_receiver_handler.handle_remove_all_warnings_msg()
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_REMOVE_ALL_WARNINGS_EXCEPT_DEFAULT_MSG:
                self.messages_receiver_handler.handle_remove_all_warnings_except_defaults_msg()
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_SET_WARNING_TO_DEFAULT_MSG:
                self.messages_receiver_handler.handle_set_warning_to_default_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_SET_POWER_MSG:
                self.messages_receiver_handler.handle_set_power_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)

            # RESPONSE DIFFERENT FROM ACK
            elif opcode == OPCODE_GET_WARNING_MSG:  # check if there is error in modules - if so throw exception
                warning_response = self.messages_receiver_handler.handle_get_warning_msg()
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_WARNING_RESPONSE,
                                                                                 warning_response.to_bytes())
            elif opcode == OPCODE_GET_WARNING_CONFIG_MSG:
                warning_response = self.messages_receiver_handler.handle_get_warning_config_msg(msg)
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_WARNING_CONFIG_RESPONSE,
                                                                                 warning_response.to_bytes())
            elif opcode == OPCODE_GET_SETUP_CONFIG_MSG:
                warning_response = self.messages_receiver_handler.handle_get_setup_config_msg()
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_SETUP_CONFIG_RESPONSE,
                                                                                 warning_response.to_bytes())
            elif opcode == OPCODE_GET_STATUS_MSG:
                warning_response = self.messages_receiver_handler.handle_get_status_msg()
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_STATUS_RESPONSE,
                                                                                 warning_response.to_bytes())

        except Exception as e:
            print("{} - Error in handle_message_body - {}".format(self.thread_name, e.__str__()))
            response = self.messages_receiver_handler.build_response_message(OPCODE_NACK_RESPONSE)

        self.logging.info("{} - Send Response message. message: {}".format(self.thread_name, binascii.hexlify(response)))
        return response
