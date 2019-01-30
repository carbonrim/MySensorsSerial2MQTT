#!/usr/bin/python3

from collections import namedtuple
from serial.threaded import ReaderThread, LineReader
import argparse
import logging
import paho.mqtt.client as mqtt
import serial
import sys
import time

class MySerialReader(LineReader):
    TERMINATOR = b'\n'
    SerialMessage = namedtuple('SerialMessage', 'nodeid sensorid command ack type payload')

    def __init__(self, mqttPublishTopic, mqttClient):
        self.log = logging.getLogger(self.__class__.__name__)
        super(MySerialReader, self).__init__()
        self._mqttPublishTopic = mqttPublishTopic
        self._mqttClient = mqttClient

    def is_gateway_message(self, serialMessage):
        return serialMessage.nodeid == '0'

    def handle_line(self, line):
        self.log.debug(line)
        try:
            msg = self.SerialMessage(*line.split(';', 6))
            if self.is_gateway_message(msg):
                return
        except TypeError as parseError:
            self.log.warning('Can\'t parse serial message: "%s". Reason: %s', line, parseError)
            return
        mqttPublishTopic = "/".join([self._mqttPublishTopic, msg.nodeid, msg.sensorid, msg.command, msg.ack])
        self.log.info('MQTT publishing topic="%s" payload="%s"', mqttPublishTopic, msg.payload)
        self._mqttClient.publish(mqttPublishTopic, msg.payload)

class Serial2MQTT:
    def __init__(self, device, baudrate, host, port, publishTopic, subscribeTopic, username=None, password=None):
        self.log = logging.getLogger(self.__class__.__name__)
        self._mqttPublishTopic = publishTopic
        self._mqttSubscribeTopic = subscribeTopic
        self._mqttClient = mqtt.Client()
        self._mqttClient.on_connect = self._mqtt_on_connect
        self._mqttClient.on_message = self._mqtt_on_message
        if username is not None:
            self._mqttClient.username_pw_set(username, password)
        self._mqttClient.connect_async(host, port)
        ser = serial.Serial(args.device, baudrate, timeout=1)
        self._serialClient = ReaderThread(ser, lambda: MySerialReader(self._mqttPublishTopic, self._mqttClient))
        self._serialProtocol = None

    def _mqtt_on_connect(self, client, userdata, flags, rc):
        self.log.info("Connected with result code=%s: %s ", rc, mqtt.connack_string(rc))
        self._mqttClient.subscribe(self._mqttSubscribeTopic + "/#")

    def _mqtt_on_message(self, client, obj, msg):
        payload = msg.payload.decode("utf-8")
        self.log.info('Received topic: %s. payload: %s', msg.topic, payload)
        fields = msg.topic.split('/')
        data = ";".join(fields[1:] + [payload])
        self.log.info('Writing msg: %s', data)
        self._serialProtocol.write_line(data)

    def run(self):
        self._serialClient.start()
        _, self._serialProtocol = self._serialClient.connect()
        self._mqttClient.loop_start()

    def stop(self):
        self._mqttClient.loop_stop()
        self._serialClient.stop()

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--broker-host', default='localhost')
parser.add_argument('--mqtt-publish-topic', default='mysensors-out')
parser.add_argument('--mqtt-subscribe-topic', default='mysensors-in')
parser.add_argument('--broker-port', type=int, default=1883)
parser.add_argument('--baudrate', type=int, default=38400)
parser.add_argument('--debug', action='store_true', default=False)
parser.add_argument('--username')
parser.add_argument('--password')
parser.add_argument('--device', required=True)
args = parser.parse_args()

# configure logging
logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)
log = logging.getLogger(sys.modules['__main__'].__file__)

# start serial2mqtt conversion
serial2Mqtt = Serial2MQTT(args.device, args.baudrate, args.broker_host, args.broker_port, args.mqtt_publish_topic, args.mqtt_subscribe_topic, args.username, args.password)
serial2Mqtt.run()

try:
    while True:
        time.sleep(100)
except:
    log.info('Stopping...')
    serial2Mqtt.stop()

