import math
from collections import defaultdict

import rclpy
from rclpy.parameter import Parameter
from rclpy.node import Node

from osr_control.roboclaw import Roboclaw

from sensor_msgs.msg import JointState
from osr_interfaces.msg import Status


class RoboclawWrapper(Node):
    """Interface between the roboclaw motor drivers and the higher level rover code"""

    def __init__(self):
        super().__init__("roboclaw_wrapper")
        self.log = self.get_logger()
        self.log.info("Initializing motor controllers")

        # initialize attributes
        self.rc = None
        self.err = [None] * 3
        self.address = []
        self.current_enc_vals = None
        self.drive_cmd_buffer = None

        self.declare_parameters(
            namespace='',
            parameters=[
                ('baud_rate', Parameter.Type.INTEGER),
                ('device', Parameter.Type.STRING),
                ('addresses', Parameter.Type.INTEGER_ARRAY),
                # ('roboclaw_mapping', Parameter.Type.INTEGER_ARRAY),
                ('drive_acceleration_factor', Parameter.Type.DOUBLE),
                ('corner_acceleration_factor', Parameter.Type.DOUBLE),
                ('velocity_timeout', Parameter.Type.DOUBLE),
                ('roboclaw_mapping.front_right_mecanum_joint.address', Parameter.Type.INTEGER),
                ('roboclaw_mapping.front_right_mecanum_joint.channel', Parameter.Type.STRING),
                ('roboclaw_mapping.front_right_mecanum_joint.ticks_per_rev', Parameter.Type.INTEGER),
                ('roboclaw_mapping.front_right_mecanum_joint.gear_ratio', Parameter.Type.DOUBLE),
                ('roboclaw_mapping.front_left_mecanum_joint.address', Parameter.Type.INTEGER),
                ('roboclaw_mapping.front_left_mecanum_joint.channel', Parameter.Type.STRING),
                ('roboclaw_mapping.front_left_mecanum_joint.ticks_per_rev', Parameter.Type.INTEGER),
                ('roboclaw_mapping.front_left_mecanum_joint.gear_ratio', Parameter.Type.DOUBLE),
                ('roboclaw_mapping.rear_right_mecanum_joint.address', Parameter.Type.INTEGER),
                ('roboclaw_mapping.rear_right_mecanum_joint.channel', Parameter.Type.STRING),
                ('roboclaw_mapping.rear_right_mecanum_joint.ticks_per_rev', Parameter.Type.INTEGER),
                ('roboclaw_mapping.rear_right_mecanum_joint.gear_ratio', Parameter.Type.DOUBLE),
                ('roboclaw_mapping.rear_left_mecanum_joint.address', Parameter.Type.INTEGER),
                ('roboclaw_mapping.rear_left_mecanum_joint.channel', Parameter.Type.STRING),
                ('roboclaw_mapping.rear_left_mecanum_joint.ticks_per_rev', Parameter.Type.INTEGER),
                ('roboclaw_mapping.rear_left_mecanum_joint.gear_ratio', Parameter.Type.DOUBLE),
                ('roboclaw_mapping.small_package_sweeper_joint.address', Parameter.Type.INTEGER),
                ('roboclaw_mapping.small_package_sweeper_joint.channel', Parameter.Type.STRING),
                ('roboclaw_mapping.small_package_sweeper_joint.ticks_per_rev', Parameter.Type.INTEGER),
                ('roboclaw_mapping.small_package_sweeper_joint.gear_ratio', Parameter.Type.DOUBLE),
                ('roboclaw_mapping.small_package_grabber_roller_1_joint.address', Parameter.Type.INTEGER),
                ('roboclaw_mapping.small_package_grabber_roller_1_joint.channel', Parameter.Type.STRING),
                ('roboclaw_mapping.small_package_grabber_roller_1_joint.ticks_per_rev', Parameter.Type.INTEGER),
                ('roboclaw_mapping.small_package_grabber_roller_1_joint.gear_ratio', Parameter.Type.DOUBLE)
            ]
        )

        self.roboclaw_mapping = defaultdict(dict)
        self.roboclaw_mapping["front_right_mecanum_joint"]["address"] = self.get_parameter('roboclaw_mapping.front_right_mecanum_joint.address').get_parameter_value().integer_value
        self.roboclaw_mapping["front_left_mecanum_joint"]["address"] = self.get_parameter('roboclaw_mapping.front_left_mecanum_joint.address').get_parameter_value().integer_value
        self.roboclaw_mapping["rear_right_mecanum_joint"]["address"] = self.get_parameter('roboclaw_mapping.rear_right_mecanum_joint.address').get_parameter_value().integer_value
        self.roboclaw_mapping["rear_left_mecanum_joint"]["address"] = self.get_parameter('roboclaw_mapping.rear_left_mecanum_joint.address').get_parameter_value().integer_value
        self.roboclaw_mapping["small_package_sweeper_joint"]["address"] = self.get_parameter('roboclaw_mapping.small_package_sweeper_joint.address').get_parameter_value().integer_value
        self.roboclaw_mapping["small_package_grabber_roller_1_joint"]["address"] = self.get_parameter('roboclaw_mapping.small_package_grabber_roller_1_joint.address').get_parameter_value().integer_value
        self.roboclaw_mapping["front_right_mecanum_joint"]["channel"] = self.get_parameter('roboclaw_mapping.front_right_mecanum_joint.channel').get_parameter_value().string_value
        self.roboclaw_mapping["front_left_mecanum_joint"]["channel"] = self.get_parameter('roboclaw_mapping.front_left_mecanum_joint.channel').get_parameter_value().string_value
        self.roboclaw_mapping["rear_right_mecanum_joint"]["channel"] = self.get_parameter('roboclaw_mapping.rear_right_mecanum_joint.channel').get_parameter_value().string_value
        self.roboclaw_mapping["rear_left_mecanum_joint"]["channel"] = self.get_parameter('roboclaw_mapping.rear_left_mecanum_joint.channel').get_parameter_value().string_value
        self.roboclaw_mapping["small_package_sweeper_joint"]["channel"] = self.get_parameter('roboclaw_mapping.small_package_sweeper_joint.channel').get_parameter_value().string_value
        self.roboclaw_mapping["small_package_grabber_roller_1_joint"]["channel"] = self.get_parameter('roboclaw_mapping.small_package_grabber_roller_1_joint.channel').get_parameter_value().string_value
        self.roboclaw_mapping["front_right_mecanum_joint"]["ticks_per_rev"] = self.get_parameter('roboclaw_mapping.front_right_mecanum_joint.ticks_per_rev').get_parameter_value().integer_value
        self.roboclaw_mapping["front_left_mecanum_joint"]["ticks_per_rev"] = self.get_parameter('roboclaw_mapping.front_left_mecanum_joint.ticks_per_rev').get_parameter_value().integer_value
        self.roboclaw_mapping["rear_right_mecanum_joint"]["ticks_per_rev"] = self.get_parameter('roboclaw_mapping.rear_right_mecanum_joint.ticks_per_rev').get_parameter_value().integer_value
        self.roboclaw_mapping["rear_left_mecanum_joint"]["ticks_per_rev"] = self.get_parameter('roboclaw_mapping.rear_left_mecanum_joint.ticks_per_rev').get_parameter_value().integer_value
        self.roboclaw_mapping["small_package_sweeper_joint"]["ticks_per_rev"] = self.get_parameter('roboclaw_mapping.small_package_sweeper_joint.ticks_per_rev').get_parameter_value().integer_value
        self.roboclaw_mapping["small_package_grabber_roller_1_joint"]["ticks_per_rev"] = self.get_parameter('roboclaw_mapping.small_package_grabber_roller_1_joint.ticks_per_rev').get_parameter_value().integer_value
        self.roboclaw_mapping["front_right_mecanum_joint"]["gear_ratio"] = self.get_parameter('roboclaw_mapping.front_right_mecanum_joint.gear_ratio').get_parameter_value().double_value
        self.roboclaw_mapping["front_left_mecanum_joint"]["gear_ratio"] = self.get_parameter('roboclaw_mapping.front_left_mecanum_joint.gear_ratio').get_parameter_value().double_value
        self.roboclaw_mapping["rear_right_mecanum_joint"]["gear_ratio"] = self.get_parameter('roboclaw_mapping.rear_right_mecanum_joint.gear_ratio').get_parameter_value().double_value
        self.roboclaw_mapping["rear_left_mecanum_joint"]["gear_ratio"] = self.get_parameter('roboclaw_mapping.rear_left_mecanum_joint.gear_ratio').get_parameter_value().double_value
        self.roboclaw_mapping["small_package_sweeper_joint"]["gear_ratio"] = self.get_parameter('roboclaw_mapping.small_package_sweeper_joint.gear_ratio').get_parameter_value().double_value
        self.roboclaw_mapping["small_package_grabber_roller_1_joint"]["gear_ratio"] = self.get_parameter('roboclaw_mapping.small_package_grabber_roller_1_joint.gear_ratio').get_parameter_value().double_value

        self.encoder_limits = {}
        self.establish_roboclaw_connections()
        self.stop_motors()  # don't move at start
        self.setup_encoders()

        # save settings to non-volatile (permanent) memory
        for address in self.address:
            self.rc.WriteNVM(address)

        for address in self.address:
            self.rc.ReadNVM(address)

        # Even though the actual method takes longs (2*32-1), roboclaw blog says 2**15 is 100%
        accel_max = 2**15-1
        self.roboclaw_overflow = 10000
        # drive motor acceleration
        accel_max = 2**15-1
        accel_rate = self.get_parameter('drive_acceleration_factor').get_parameter_value().double_value
        self.drive_accel = int(accel_max * accel_rate)
        self.velocity_timeout = rclpy.duration.Duration(seconds=self.get_parameter('velocity_timeout').get_parameter_value().double_value, 
                                                        nanoseconds=0)
        self.time_last_cmd = self.get_clock().now()

        self.stop_motors()

        # set up publishers and subscribers
        # self.drive_cmd_sub = self.create_subscription(CommandDrive, "/cmd_drive", self.drive_cmd_cb, 1)
        self.drive_cmd_sub = self.create_subscription(JointState, "/drive_command", self.drive_cmd_cb, 1)
        self.enc_pub = self.create_publisher(JointState, "/drive_state", 1)
        self.status_pub = self.create_publisher(Status, "/status", 1)

        self.status = Status()
        fast_loop_rate = 0.125  # seconds
        slow_loop_rate = 3  # seconds
        # true if we're idling and started ramping down velocity to bring the motors to full stop
        self.idle_ramp = False
        # if we're idled
        self.idle = False
        self.fast_timer = self.create_timer(fast_loop_rate, self.fast_update)
        self.slow_timer = self.create_timer(slow_loop_rate, self.slow_update)

    def fast_update(self):
        """Read from and write to roboclaws"""
        # Check to see if there are commands in the buffer to send to the motor controller
        now = self.get_clock().now()
        if self.drive_cmd_buffer:
            self.send_drive_buffer_velocity(self.drive_cmd_buffer)
            self.drive_cmd_buffer = None
            self.idle_ramp = False
            self.idle = False
            self.time_last_cmd = now

        # read from roboclaws and publish
        try:
            self.read_encoder_values()
            self.enc_pub.publish(self.current_enc_vals)
        except AssertionError as read_exc:
            self.get_logger().warn("Failed to read encoder values")
            #self.get_logger().warn(read_exc.args)

        # # stop the motors if we haven't received a command in a while
        # if not self.idle and (now - self.time_last_cmd > self.velocity_timeout):
        #     # rather than a hard stop, send a ramped velocity command to 0
        #     if not self.idle_ramp:
        #         self.get_logger().debug("Idling: ramping down velocity to zero")
        #         self.idle_ramp = True
        #         drive_cmd_buffer = JointState()
        #         self.send_drive_buffer_velocity(drive_cmd_buffer)
        #     # if we've already ramped down, send a full stop to minimize
        #     # idle power consumption
        #     else:
        #         self.get_logger().debug("Idling: full stopping motors")
        #         self.stop_motors()
        #         self.idle = True
            
            # so that's there's a delay between ramping and full stop
            self.time_last_cmd = now

    def slow_update(self): #fine
        
        """Slower roboclaw read/write cycle"""
        self.status.battery = self.read_battery()
        self.status.temp = self.read_temperatures()
        self.status.current = self.read_currents()
        self.status.error_status = self.read_errors()
        self.status_pub.publish(self.status)

    def establish_roboclaw_connections(self):
        """
        Attempt connecting to the roboclaws

        :raises Exception: when connection to one or more of the roboclaws is unsuccessful
        """
        serial_port = self.get_parameter('device').get_parameter_value().string_value
        baud_rate = self.get_parameter('baud_rate').get_parameter_value().integer_value
        self.rc = Roboclaw(serial_port, baud_rate)
        self.rc.Open()
        self.address = self.get_parameter('addresses').get_parameter_value().integer_array_value

        # initialize connection status to successful
        all_connected = True
        for address in self.address:
            self.get_logger().debug("Attempting to talk to motor controller ''".format(address))
            version_response = self.rc.ReadVersion(address)
            connected = bool(version_response[0])
            if not connected:
                self.get_logger().error("Unable to connect to roboclaw at '{}'".format(address))
                all_connected = False
            else:
                self.get_logger().debug("Roboclaw version for address '{}': '{}'".format(address, version_response[1]))
        if all_connected:
            self.get_logger().info("Sucessfully connected to RoboClaw motor controllers")
        else:
            raise Exception("Unable to establish connection to one or more of the Roboclaw motor controllers")
        
        
        self.rc.SetM1VelocityPID(130, 1.33289, 0.24868, 0.0, 10000)
        self.rc.SetM2VelocityPID(130, 1.19756, 0.24062, 0.0, 10000)
        self.rc.SetM1VelocityPID(129, 0.98359, 0.24771, 0.0, 6083)
        self.rc.SetM2VelocityPID(129, 0.90848, 0.28011, 0.0, 8231)




    def setup_encoders(self):
        """Set up the encoders"""
        for motor_name, properties in self.roboclaw_mapping.items():
            self.encoder_limits[motor_name] = (None, None)
            self.rc.ResetEncoders(properties["address"])

    def read_encoder_values(self):
        """Query roboclaws and update current motors status in encoder ticks"""
        enc_msg = JointState()
        enc_msg.header.stamp = self.get_clock().now().to_msg()
        for motor_name, properties in self.roboclaw_mapping.items():
            enc_msg.name.append(motor_name)
            position = self.read_encoder_position(properties["address"], properties["channel"])
            velocity = self.read_encoder_velocity(properties["address"], properties["channel"])
            current = self.read_encoder_current(properties["address"], properties["channel"])
            enc_msg.position.append(self.tick2position(position,
                                                       self.encoder_limits[motor_name][0],
                                                       self.encoder_limits[motor_name][1],
                                                       properties['ticks_per_rev'],
                                                       properties['gear_ratio']))
            enc_msg.velocity.append(self.qpps2velocity(velocity,
                                                       properties['ticks_per_rev'],
                                                       properties['gear_ratio']))
            enc_msg.effort.append(current)

        self.current_enc_vals = enc_msg
        
    def drive_cmd_cb(self, cmd):
        """
        Takes the drive command and stores it in the buffer to be sent
        on the next iteration of the run() loop.
        """
        
        self.drive_cmd_buffer = cmd

    def send_drive_buffer_velocity(self, cmd):
        """
        Sends the drive command to the motor controller, closed loop velocity commands
        """
        # forloop that reads through joint states message and sends velocity commands to each motor
        for i in range(len(cmd.name)):
            # check if the motor is in the roboclaw mapping
            if cmd.name[i] in self.roboclaw_mapping:

                props = self.roboclaw_mapping[cmd.name[i]]
                if "mecanum" in cmd.name[i]:
                    vel_cmd = self.velocity2qpps(cmd.velocity[i], props["ticks_per_rev"], props["gear_ratio"])
                    print(f"{vel_cmd}")
                    self.send_velocity_cmd(props["address"], props["channel"], vel_cmd)
                else:
                    self.send_speed_cmd(props["address"], props["channel"], cmd.effort[i])
                

    

    def read_encoder_position(self, address, channel):
        """Wrapper around self.rc.ReadEncM1 and self.rcReadEncM2 to simplify code"""
        if channel == "M1":
            val = self.rc.ReadEncM1(address)
        elif channel == "M2":
            val = self.rc.ReadEncM2(address)
        else:
            raise AttributeError("Received unknown channel '{}'. Expected M1 or M2".format(channel))

        assert val[0] == 1
        return val[1]

    def read_encoder_limits(self, address, channel):
        """Wrapper around self.rc.ReadPositionPID and returns subset of the data

        :return: (enc_min, enc_max)
        """
        if channel == "M1":
            result = self.rc.ReadM1PositionPID(address)
        elif channel == "M2":
            result = self.rc.ReadM2PositionPID(address)
        else:
            raise AttributeError("Received unknown channel '{}'. Expected M1 or M2".format(channel))

        assert result[0] == 1
        return (result[-2], result[-1])
    
    def send_speed_cmd(self, address, channel, speed):
        target_speed = int(speed) #int(max(min(speed, 100), -100))
        if channel == "M1":
            if target_speed >= 0:
                self.rc.ForwardM1(address, abs(target_speed))
            else:
                self.rc.BackwardM1(address, abs(target_speed))
        elif channel == "M2":
            if target_speed >= 0:
                self.rc.ForwardM2(address, abs(target_speed))
            else:
                self.rc.BackwardM2(address, abs(target_speed))
        else:
            raise AttributeError("Received unknown channel '{}'. Expected M1 or M2".format(channel))

    def send_velocity_cmd(self, address, channel, target_qpps):
        """
        Wrapper around one of the send velocity commands

        :param address:
        :param channel:
        :param target_qpps: int
        """
        # clip values
        target_qpps = max(-self.roboclaw_overflow, min(self.roboclaw_overflow, target_qpps))
        if channel == "M1":
            return self.rc.SpeedAccelM1(address, self.drive_accel, target_qpps)
        elif channel == "M2":
            return self.rc.SpeedAccelM2(address, self.drive_accel, target_qpps)
        else:
            raise AttributeError("Received unknown channel '{}'. Expected M1 or M2".format(channel))

    def read_encoder_velocity(self, address, channel):
        """Wrapper around self.rc.ReadSpeedM1 and self.rcReadSpeedM2 to simplify code"""
        if channel == "M1":
            val = self.rc.ReadSpeedM1(address)
        elif channel == "M2":
            val = self.rc.ReadSpeedM2(address)
        else:
            raise AttributeError("Received unknown channel '{}'. Expected M1 or M2".format(channel))

        assert val[0] == 1
        return val[1]

    def read_encoder_current(self, address, channel):
        """Wrapper around self.rc.ReadCurrents to simplify code"""
        if channel == "M1":
            return self.rc.ReadCurrents(address)[0]
        elif channel == "M2":
            return self.rc.ReadCurrents(address)[1]
        else:
            raise AttributeError("Received unknown channel '{}'. Expected M1 or M2".format(channel))

    def tick2position(self, tick, enc_min, enc_max, ticks_per_rev, gear_ratio):
        """
        Convert the absolute position from ticks to radian relative to the middle position

        :param tick:
        :param enc_min:
        :param enc_max:
        :param ticks_per_rev:
        :return:
        """
        ticks_per_rad = ticks_per_rev / (2 * math.pi)
        if enc_min is None or enc_max is None:
            return tick / ticks_per_rad
        mid = enc_min + (enc_max - enc_min) / 2

        return (tick - mid) / ticks_per_rad * gear_ratio

    def position2tick(self, position, enc_min, enc_max, ticks_per_rev, gear_ratio):
        """
        Convert the absolute position from radian relative to the middle position to ticks

                Clip values that are outside the range [enc_min, enc_max]

        :param position:
        :param enc_min:
        :param enc_max:
        :param ticks_per_rev:
        :return:
        """
        ticks_per_rad = ticks_per_rev / (2 * math.pi)
        if enc_min is None or enc_max is None:
            return position * ticks_per_rad
        mid = enc_min + (enc_max - enc_min) / 2
        tick = int(mid + position * ticks_per_rad / gear_ratio)

        return max(enc_min, min(enc_max, tick))

    def qpps2velocity(self, qpps, ticks_per_rev, gear_ratio):
        """
        Convert the given quadrature pulses per second to radian/s

        :param qpps: int
        :param ticks_per_rev:
        :param gear_ratio:
        :return:
        """
        return qpps * 2 * math.pi / (gear_ratio * ticks_per_rev)

    def velocity2qpps(self, velocity, ticks_per_rev, gear_ratio):
        """
        Convert the given velocity to quadrature pulses per second

        :param velocity: rad/s
        :param ticks_per_rev:
        :param gear_ratio:
        :return: int
        """
        return int(velocity * gear_ratio * ticks_per_rev / (2 * math.pi))

    def read_battery(self):
        """Read battery voltage from one of the roboclaws as a proxy for all roboclaws"""
        # roboclaw reports value in 10ths of a Volt
        return self.rc.ReadMainBatteryVoltage(self.address[0])[1] / 10.0

    def read_temperatures(self):
        temp = [None] * 3
        for i in range(3):
            # reported by roboclaw in 10ths of a Celsius
            temp[i] = self.rc.ReadTemp(self.address[i])[1] / 10.0
        
        return temp

    def read_currents(self):
        currents = [None] * 6
        for i in range(3):
            currs = self.rc.ReadCurrents(self.address[i])
            # reported by roboclaw in 10ths of an Ampere
            currents[2*i] = currs[1] / 100.0
            currents[(2*i) + 1] = currs[2] / 100.0
        
        return currents

    def stop_motors(self):
        """Stops all motors on Rover"""
        for i in range(3):
            self.rc.ForwardM1(self.address[i], 0)
            self.rc.ForwardM2(self.address[i], 0)

    def read_errors(self):
        """Checks error status of each motor controller, returns 0 if no errors reported"""
        err = ['0'] * 3
        for i in range(len(self.address)):
            err_int = self.rc.ReadError(self.address[i])[1]

            if err_int != 0:
                # convert to hexadecimal and then to string for easy decoding
                err[i] = str(hex(err_int))

                err_string, has_error = self.decode_error(err_int)

                if(has_error):
                    self.log.error(f"Motor controller {self.address[i]} reported error code {err[i]} (hex: {hex(err_int)}),{err_string}")
                else:
                    self.log.warn(f"Motor controller {self.address[i]} reported warning code {err[i]} (hex: {hex(err_int)}), {err_string}")

        return err

    def decode_error(self, err_int):
        """ Decodes error codes according to RoboClaw user manual, pg. 73 """

        err_string = ""
        is_error = False

        if(err_int & 0x000001):
            err_string += "\nE-stop"
        if(err_int & 0x000002):
            err_string += "\nTemperature Error"
            is_error = True
        if(err_int & 0x000004):
            err_string += "\nTemperature 2 error"
            is_error = True
        if(err_int & 0x000008):
            err_string += "\nMain voltage High Error"
            is_error = True
        if(err_int & 0x000010):
            err_string += "\nLogic voltage High Error"
            is_error = True
        if(err_int & 0x000020):
            err_string += "\nLogic voltage Low Error"
            is_error = True
        if(err_int & 0x000040):
            err_string += "\nM1 Driver Fault"
            is_error = True
        if(err_int & 0x000080):
            err_string += "\nM2 Driver Fault"
            is_error = True
        if(err_int & 0x000100):
            err_string += "\nM1 Speed Error"
            is_error = True
        if(err_int & 0x000200):
            err_string += "\nM2 Speed Error"
            is_error = True
        if(err_int & 0x000400):
            err_string += "\nM1 Position Error"
            is_error = True
        if(err_int & 0x000800):
            err_string += "\nM2 Position Error"
            is_error = True
        if(err_int & 0x001000):
            err_string += "\nM1 Current Error"
            is_error = True
        if(err_int & 0x002000):
            err_string += "\nM2 Current Error"
            is_error = True

        if(err_int & 0x010000):
            err_string += "\nM1 Over-Current Warning"
        if(err_int & 0x020000):
            err_string += "\nM2 Over-Current Warning"
        if(err_int & 0x040000):
            err_string += "\nMain Voltage High Warning"
        if(err_int & 0x080000):
            err_string += "\nMain Voltage Low Warning" 
        if(err_int & 0x100000):
            err_string += "\nTemperature Warning"
        if(err_int & 0x200000):
            err_string += "\nTemperature 2 Warning"
        if(err_int & 0x400000):
            err_string += "\nS4 Signal Triggered"
        if(err_int & 0x800000):
            err_string += "\nS5 Signal Triggered"
        if(err_int & 0x01000000):
            err_string += "\nSpeed Error Limit Warning"
        if(err_int & 0x02000000):
            err_string += "\nPosition Error Limit Warning"

        return err_string, is_error


def main(args=None):
    rclpy.init(args=args)

    wrapper = RoboclawWrapper()

    rclpy.spin(wrapper)
    wrapper.stop_motors()
    wrapper.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
