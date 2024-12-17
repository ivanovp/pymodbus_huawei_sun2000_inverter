#!/usr/bin/env /home/pi/pymodbus/bin/python3
#                     ^
#                     |
#                     `--- change to your username
#
# Install venv:
# sudo apt install python3-venv
#
# Creating venv:
# python3 -m venv ~/pymodbus
# cd ~/pymodbus/bin
# ./pip3 install -v "pymodbus==3.7.4"
# ./pip3 install pyserial
# ./pip3 install paho-mqtt
#
# Copyright (C) Peter Ivanov <ivanovp@gmail.com>, 2024
# License: GPLv3
#
# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
import sys
import time
import pymodbus.client as ModbusClient
from pymodbus import (
    ExceptionResponse,
    FramerType,
    ModbusException,
    pymodbus_apply_logging_config,
)
from paho.mqtt.enums import MQTTProtocolVersion
import paho.mqtt.publish as publish

modbus_slave_id = 1
mqtt_host = "127.0.0.1"
mqtt_port = 1883
mqtt_topic = "/sensors/huawei_sun2000_inverter/"

# Convert Modbus register to string
def regs2str(regs):
    s = ""
    for r in regs:
        a = chr(r & 0xFF)
        b = chr((r >> 8) & 0xFF)
        if a == '\x00':
            a = ' '
        if b == '\x00':
            b = ' '
        s += "%c%c" % (b, a)
    return s.rstrip()

# Read registers from Modbus slave
def readregs(client, address, count=1):
    try:
        holding_regs = client.read_holding_registers(address, count=count, slave=modbus_slave_id)
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
    if holding_regs.isError():
        print(f"Received Modbus library error({holding_regs})")
    elif isinstance(holding_regs, ExceptionResponse):
        print(f"Received Modbus library exception ({holding_regs})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
    else:
        return (holding_regs.registers)

# Convert two unsigned 16-bit register to one unsigned 32-bit value
def u16_to_u32(regs):
    u32 = None
    if len(regs) >= 2:
        u32 = (regs[1] + (regs[0] << 16))
    return u32

# Convert two unsigned 16-bit register to one signed 32-bit value
def u16_to_i32(regs):
    i32 = None
    if len(regs) >= 2:
        i32 = (regs[1] + (regs[0] << 16))
        if i32 & (1 << 31):
            i32 = (1 << 32) - i32
            i32 *= -1
    return i32

# Get states, voltages, currents, etc. from Huawei SUN 2000 inverter via modbus
def fetch_data():
    d = {}

    regs = readregs(client, 30000, 15)
    d['model'] = regs2str (regs)

    regs = readregs(client, 30015, 10)
    d['serial_number'] = regs2str (regs)

    regs = readregs(client, 30025, 10)
    d['part_number'] = regs2str (regs)

    regs = readregs(client, 30070, 13)
    d['model_id'] = regs[0]
    d['pv_string_num'] = regs[1]
    d['mpp_tracker_num'] = regs[2]
    d['rated_power_W'] = u16_to_u32(regs[3:])
    d['rated_active_power_W'] = u16_to_u32(regs[5:])
    d['maximum_apperent_power_VA'] = u16_to_u32(regs[7:])
    d['maximum_reactive_power_to_grid_var'] = u16_to_i32(regs[9:])
    d['maximum_reactive_power_from_grid_var'] = u16_to_i32(regs[11:])

    regs = readregs(client, 32000, 5)
    d['state1'] = regs[0]
    d['state1_str'] = []
    r = regs[0]
    if r & 1:
        d['state1_str'].append("standby")
    if r & 2:
        d['state1_str'].append("grid-connected")
    if r & 4:
        d['state1_str'].append("grid-connected normally")
    if r & 8:
        d['state1_str'].append("grid connection with derating due to power rationing")
    if r & 16:
        d['state1_str'].append("grid connection with derating due to internal causes of the solar inverter")
    if r & 32:
        d['state1_str'].append("normal stop")
    if r & 64:
        d['state1_str'].append("stop due to faults")
    if r & 128:
        d['state1_str'].append("stop due to power rationing")
    if r & 256:
        d['state1_str'].append("shutdown")
    if r & 512:
        d['state1_str'].append("spot check")
    d['state1_str'] = ", ".join(d['state1_str'])
    d['state2'] = regs[2]
    d['state2_str'] = []
    r = regs[2]
    if r & 1:
        d['state2_str'].append("locking status: unlocked")
    else:
        d['state2_str'].append("locking status: locked")
    if r & 2:
        d['state2_str'].append("PV connection status: connected")
    else:
        d['state2_str'].append("PV connection status: disconnected")
    if r & 4:
        d['state2_str'].append("DSP data collection: yes")
    else:
        d['state2_str'].append("DSP data collection: no")
    d['state2_str'] = ", ".join(d['state2_str'])
    d['state3'] = u16_to_u32(regs[3:])
    d['state3_str'] = []
    r = u16_to_u32(regs[3:])
    if r & 1:
        d['state3_str'].append("on-grid")
    else:
        d['state3_str'].append("off-grid")
    if r & 2:
        d['state3_str'].append("off-grid switch: enable")
    else:
        d['state3_str'].append("off-grid switch: disable")
    d['state3_str'] = ", ".join(d['state3_str'])

    regs = readregs(client, 32008, 3)
    d['alarm1'] = regs[0]
    d['alarm2'] = regs[1]
    d['alarm3'] = regs[2]

    regs = readregs(client, 32016, d['pv_string_num'] * 2)
    for i in range(d['pv_string_num']):
        d['pv%i_voltage_V' % i] = regs[i * 2] / 10.0
        d['pv%i_current_A' % i] = regs[i * 2 + 1] / 100.0

    regs = readregs(client, 32064, 2)
    d['input_power_kW'] = u16_to_i32(regs) / 10.0

    regs = readregs(client, 32066, 10)
    d['line_AB_voltage_V'] = regs[0] / 10.0
    d['line_BC_voltage_V'] = regs[1] / 10.0
    d['line_CA_voltage_V'] = regs[2] / 10.0
    d['phase_A_voltage_V'] = regs[3] / 10.0
    d['phase_B_voltage_V'] = regs[4] / 10.0
    d['phase_C_voltage_V'] = regs[5] / 10.0

    regs = readregs(client, 32078, 11)
    d['peak_active_power_of_current_day_kW'] = u16_to_u32(regs) / 1000.0
    d['active_power_kW'] = u16_to_i32(regs[2:]) / 1000.0
    d['reactive_power_kvar'] = u16_to_i32(regs[4:]) / 1000.0

    regs = readregs(client, 32087, 1)
    d['internal_temperature_C'] = regs[0] / 10.0

    regs = readregs(client, 32089, 6)
    device_status_str = "Unknown"
    d['device_status'] = regs[0]
    r = regs[0]
    if (r == 0x0000):
        device_status_str = "Standby: initializing"
    elif (r == 0x0001):
        device_status_str = "Standby: detecting insulation resistance"
    elif (r == 0x0002):
        device_status_str = "Standby: detecting irradiation"
    elif (r == 0x0003):
        device_status_str = "Standby: drid detecting"
    elif (r == 0x0100):
        device_status_str = "Starting"
    elif (r == 0x0200):
        device_status_str = "On-grid (Off-grid mode: running)"
    elif (r == 0x0201):
        device_status_str = "Grid connection: power limited (Off-grid mode: running: power limited)"
    elif (r == 0x0202):
        device_status_str = "Grid connection: self- derating (Off-grid mode: running: self- derating)"
    elif (r == 0x0203):
        device_status_str = "Off-grid Running"
    elif (r == 0x0300):
        device_status_str = "Shutdown: fault"
    elif (r == 0x0301):
        device_status_str = "Shutdown: command"
    elif (r == 0x0302):
        device_status_str = "Shutdown: OVGR"
    elif (r == 0x0303):
        device_status_str = "Shutdown: communication disconnected"
    elif (r == 0x0304):
        device_status_str = "Shutdown: power limited"
    elif (r == 0x0305):
        device_status_str = "Shutdown: manual startup required"
    elif (r == 0x0306):
        device_status_str = "Shutdown: DC switches disconnected"
    elif (r == 0x0307):
        device_status_str = "Shutdown: rapid cutoff"
    elif (r == 0x0308):
        device_status_str = "Shutdown: input underpower"
    elif (r == 0x0401):
        device_status_str = "Grid scheduling: cosφ-P curve"
    elif (r == 0x0402):
        device_status_str = "Grid scheduling: Q-U curve"
    elif (r == 0x0403):
        device_status_str = "Grid scheduling: PF-U curve"
    elif (r == 0x0404):
        device_status_str = "Grid scheduling: dry contact"
    elif (r == 0x0405):
        device_status_str = "Grid scheduling: Q-P curve"
    elif (r == 0x0500):
        device_status_str = "Spot-check ready"
    elif (r == 0x0501):
        device_status_str = "Spot-checking"
    elif (r == 0x0600):
        device_status_str = "Inspecting"
    elif (r == 0x0700):
        device_status_str = "AFCI self check"
    elif (r == 0x0800):
        device_status_str = "I-V scanning"
    elif (r == 0x0900):
        device_status_str = "DC input detection"
    elif (r == 0x0A00):
        device_status_str = "Running: off-grid charging"
    elif (r == 0xA000):
        device_status_str = "Standby: no irradiation"
    d['device_status_str'] = device_status_str
    d['fault_code'] = regs[1]
    d['startup_time_sec'] = u16_to_u32(regs[2:])
    d['shutdown_time_sec'] = u16_to_u32(regs[4:])

    regs = readregs(client, 32106, 2)
    d['accumulated_energy_yield_kWh'] = u16_to_u32(regs) / 100.0

    regs = readregs(client, 32114, 2)
    d['daily_energy_yield_kWh'] = u16_to_u32(regs) / 100.0

    regs = readregs(client, 43006, 2)
    d['time_zone'] = regs[0]
    d['time_source'] = regs[1]

    return d

# Print states, voltages, currents, etc. of Huawei SUN 2000 inverter
def print_data(d):
    print("Model:", d['model'])
    print("Model ID:", d['model_id'])
    #print("Serial number:", d['serial_number'])
    print("Part number:", d['part_number'])
    #print("State 1:", d['state1'], "=", ", ".join(d['state1_str']))
    #print("State 2:", d['state2'], "=", ", ".join(d['state2_str']))
    #print("State 3:", d['state3'], "=", ", ".join(d['state3_str']))
    print("State 1:", d['state1'], "=", d['state1_str'])
    print("State 2:", d['state2'], "=", d['state2_str'])
    print("State 3:", d['state3'], "=", d['state3_str'])
    print("Number of PV strings:", d['pv_string_num'])
    print("Number of MPP trackers:", d['mpp_tracker_num'])
    print("Rated power (Pn):", d['rated_power_W'], "W")
    print("Maximum active power (Pmax):", d['rated_active_power_W'], "W")
    print("Maximum apparent power (Smax):", d['maximum_apperent_power_VA'], "VA")
    print("Maximum reactive power to grid (Qmax):", d['maximum_reactive_power_to_grid_var'], "var")
    print("Maximum reactive power from grid (Qmax):", d['maximum_reactive_power_from_grid_var'], "var")
    for i in range(d['pv_string_num']):
        print("PV %i voltage: %.1f V" % (i, d['pv%i_voltage_V' % i]))
        print("PV %i current: %.2f A" % (i, d['pv%i_current_A' % i]))
    print("Input power: %.3f kW" % d['input_power_kW'])
    print("Power grid line AB voltage: %.3f V" % d['line_AB_voltage_V'])
    print("Power grid line BC voltage: %.3f V" % d['line_BC_voltage_V'])
    print("Power grid line CA voltage: %.3f V" % d['line_CA_voltage_V'])
    print("Power grid phase A voltage: %.3f V" % d['phase_A_voltage_V'])
    print("Power grid phase B voltage: %.3f V" % d['phase_B_voltage_V'])
    print("Power grid phase C voltage: %.3f V" % d['phase_C_voltage_V'])
    print("Peak active power of current day: %.4f kW" % d['peak_active_power_of_current_day_kW'])
    print("Active power: %.4f kW" % d['active_power_kW'])
    print("Reactive power: %.4f kvar" % d['reactive_power_kvar'])
    print("Internal temperature: %.1f Celsius" % d['internal_temperature_C'])
    print("Device status: 0x%X %s" % (d['device_status'], d['device_status_str']))
    print("Fault code: 0x%X" % (d['fault_code']))
    print("Startup time: %i sec" % (d['startup_time_sec']))
    print("Shutdown time: %i sec" % (d['shutdown_time_sec']))
    print("Time zone: %i" % d['time_zone'])
    print("Time source: %i" % d['time_source'])

# Publish states, voltages, currents, etc. of Huawei SUN 2000 inverter via MQTT
def publish_data(d):
    msgs = []
    for k in d.keys():
        msg = { 'topic': mqtt_topic + k, 'payload': d[k]}
        msgs.append(msg)
    publish.multiple(msgs, hostname=mqtt_host, port=mqtt_port, protocol=MQTTProtocolVersion.MQTTv5)

if __name__ == "__main__":
    # activate debugging
#    pymodbus_apply_logging_config("DEBUG")

    client = ModbusClient.ModbusSerialClient(
        port='/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0',
        timeout=1,
        retries=3,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
    )

    client.connect()

    d = fetch_data()

    client.close()

    quiet = False
    publish = False
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == '-q':
                quiet = True
            if arg == '-m'
                publish = True
    if not quiet:
        print_data(d)
    if publish:
        publish_data(d)


