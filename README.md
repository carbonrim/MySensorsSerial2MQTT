# MySensorsSerial2MQTT
This is simple bridge between [MySensors serial gateway](https://www.mysensors.org/build/serial_gateway) and the MQTT bus.

To use it, connect the serial gateway to the host and then run:

    ./serial2mqtt.py --device /dev/ttyDevice

where `/dev/ttyDevice` is the path to the serial device (e.g. `/dev/ttyUSB0` for Arduino Uno serial gateway).

# Running as a service

1. Clone this repository to preferred location, for example `/opt` directory
   ```
   cd /opt
   git clone https://github.com/mikozak/MySensorsSerial2MQTT.git
   ```

2. Create python virtual environment for running service (this is optional step, however I recommend it)
   ```
   cd MySensorsSerial2MQTT/
   python3 -m venv .
   ```

3. Install dependencies
   ```
   bin/python3 -m pip install -r requirements.txt
   ```

4. Check whether everything works as expected (choose valid serial device, for example `/dev/ttyUSB0`)
   ```
   bin/python3 serial2mqtt.py --device /dev/ttyUSB0 --log-debug
   ```

5. Create system user which will be used to run as service process (for the purpose of this instruction 
   user named *mysensors* will be used)

   If you are installing on Raspberry Pi you probably want to add newly created user to *dialout*
   group in order to allow access to `/dev/tty*` devices.

   ```
   sudo useradd -r mysensors -Gdialout
   ```

6. Edit `myserial2mqtt@.service` and make sure path in `WorkingDirectory` and `ExecStart` are valid (and absolute!)
   You can add additional command line options. The list of all options is as follows:
   * `--broker-host` MQTT server host (default: `localhost`) [optional]
   * `--broker-port` MQTT server port (default: `1883`) [optional]
   * `--mqtt-publish-topic` MQTT topic used when publishing messages from serial device (default: `mysensors-out`) [optional]
   * `--mqtt-subscribe-topic` MQTT topic to subscribe for message that should be written to serial device (default: `mysensors-in`) [optional]
   * `--baudrate` serial device baudrate (default: `38400`) [optional]
   * `--log-debug` enable debug logging (disabled by default) [optional]
   * `--log-info` enable info logging (disabled by default) [optional]
   * `--username` MQTT user [optional]
   * `--password` MQTT password [optional]
   * `--device` path to serial device [required]

7. Install service
   ```
   sudo cp myserial2mqtt@.service /etc/systemd/system/
   ```

8. Run service for `ttyUSB0` device (remember to replace it to you device)
   ```
   sudo systemctl start myserial2mqtt@ttyUSB0
   ```

   If you want to start the service automatically after system starts just enable it
   ```
   sudo systemctl enable myserial2mqtt@ttyUSB0
   ```
