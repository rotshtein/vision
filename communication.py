"""
Created on Aug 14, 2018

@author: ziv
"""
import binascii
from datetime import datetime

import serial

from messages_receiver_handler import MessagesReceiverHandler
from protocol.bytes_converter import IBytesConverter
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


class Communication(HDThread):
    def __init__(self, thread_name, logging, messages_receiver_handler, port=PORT, baudrate=BAUD_RATE):
        super().__init__(thread_name, logging, 0)
        self.logging.info("{} - Init.".format(thread_name))
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
            self.logging.info(
                "{} - Initialized Serial port: port={} baudrate={}".format(thread_name, self.port, self.baudrate))
            # send bringup to ST slave
            # self.ser.write(bytearray([PREAMBLE_PREFIX, PREAMBLE_PREFIX, PREAMBLE_PREFIX, PREAMBLE_PREFIX]))
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
                msg_header, length, opcode = self.handle_message_header()

                # continue reading message - minus 3 bytes: preamble + length + opcode
                msg_body = self.ser.read(length - 3)
                self.logging.info(
                    "{} - read message body length={}. message: {}".format(self.thread_name, length - 3,
                                                                           binascii.hexlify(msg_body)))

                # validate CRC - if error throw exception
                self.validate_crc(msg_header + msg_body, length)

                response = self.handle_message_body(msg_body, opcode)

                # send reply message
                msg = self.ser.write(response)
                iteration_time = datetime.now() - start_time
                self.logging.debug("{} - End. Total Duration={}".format(self.thread_name, iteration_time))
            except Exception as e:
                self.logging.error(
                    "{} - Error in serial - flushing input buffer. {}".format(self.thread_name, e.__str__()))
                self.ser.reset_input_buffer()

    def validate_crc(self, msg_concat, length):
        calculated_checksum = self.messages_receiver_handler.calc_checksum(msg_concat[:-1])
        received_checksum = msg_concat[length - 1]
        if calculated_checksum != int.to_bytes(received_checksum, 1, byteorder=IBytesConverter.LITTLE_ENDIAN):
            raise Exception(
                "{} - Checksum failed. Calculated:{}. Received:{}.".format(self.thread_name, calculated_checksum,
                                                                           received_checksum))

    def read_header(self):
        msg = self.ser.read(3)
        # msg_in_hex = hex(int.from_bytes(msg, byteorder=IBytesConverter.BIG_ENDIAN))
        self.logging.info("{} - read message header 3 bytes: {}".format(self.thread_name, binascii.hexlify(msg)))
        return msg

    def handle_message_header(self):
        # read first 3 bytes - msg[0]=preamble; msg[1]=length; msg[2]=opcode
        msg_header = self.read_header()
        # read preamble
        if msg_header[0] != PREAMBLE_PREFIX:
            error_msg = "{} - error reading Preamble. Expected=0xAA. Received={}".format(self.thread_name,
                                                                                         binascii.hexlify(
                                                                                             msg_header[0]))
            self.logging.error(error_msg)
            raise Exception(error_msg)
        # length = total length of message including preamble, length , opcode and checksum
        length = msg_header[1]
        # read opcode
        opcode = msg_header[2]
        return msg_header, length, opcode

    def handle_message_body(self, msg_body, opcode):

        response = None
        # handle message
        try:
            if opcode == OPCODE_SETUP_MSG:
                self.messages_receiver_handler.handle_setup_msg(msg_body)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_SET_WARNING_MSG:
                self.messages_receiver_handler.handle_set_warning_msg(msg_body)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_REMOVE_WARNING_MSG:
                self.messages_receiver_handler.handle_remove_warning_msg(msg_body)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_REMOVE_ALL_WARNINGS_MSG:
                self.messages_receiver_handler.handle_remove_all_warnings_msg()
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_REMOVE_ALL_WARNINGS_EXCEPT_DEFAULT_MSG:
                self.messages_receiver_handler.handle_remove_all_warnings_except_defaults_msg()
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_SET_WARNING_TO_DEFAULT_MSG:
                self.messages_receiver_handler.handle_set_warning_to_default_msg(msg_body)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)
            elif opcode == OPCODE_SET_POWER_MSG:
                self.messages_receiver_handler.handle_set_power_msg(msg_body)
                response = self.messages_receiver_handler.build_response_message(OPCODE_ACK_RESPONSE)

            # RESPONSE DIFFERENT FROM ACK
            elif opcode == OPCODE_GET_WARNING_MSG:  # check if there is error in modules - if so throw exception
                warning_response = self.messages_receiver_handler.handle_get_warning_msg()
                response = self.messages_receiver_handler.build_response_message(OPCODE_GET_WARNING_RESPONSE,
                                                                                 warning_response.to_bytes())
            elif opcode == OPCODE_GET_WARNING_CONFIG_MSG:
                warning_response = self.messages_receiver_handler.handle_get_warning_config_msg(msg_body)
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
            self.logging.info("{} - Error in handle_message_body - {}".format(self.thread_name, e.__str__()))
            response = self.messages_receiver_handler.build_response_message(OPCODE_NACK_RESPONSE)

        self.logging.info(
            "{} - Send Response message. message: {}".format(self.thread_name, binascii.hexlify(response)))
        return response
