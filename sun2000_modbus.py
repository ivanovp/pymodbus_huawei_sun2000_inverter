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
# ./pip3 install pymodbus
# ./pip3 install pyserial
#
# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
import time
import pymodbus.client as ModbusClient
from pymodbus import (
    ExceptionResponse,
    FramerType,
    ModbusException,
    pymodbus_apply_logging_config,
)

def regs2str(regs):
    s = ""
    for r in regs:
        a = chr(r & 0xFF)
        b = chr((r >> 8) & 0xFF)
        s += "%c%c" % (b, a)
    return s

def readregs(address,count=1):
    try:
        holding_regs = client.read_holding_registers(address, count, slave=1)
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
    if holding_regs.isError():
        print(f"Received Modbus library error({holding_regs})")
    elif isinstance(holding_regs, ExceptionResponse):
        print(f"Received Modbus library exception ({holding_regs})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
    else:
        return (holding_regs.registers)

if __name__ == "__main__":
    # activate debugging
#    pymodbus_apply_logging_config("DEBUG")

    client = ModbusClient.ModbusSerialClient(
        port='/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0',
#        framer=framer,
        timeout=1,
        retries=3,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        #handle_local_echo=False,
    )
    
    print ("connecting")
    client.connect()

    regs = readregs(30000, 15)
    print("Model:", regs2str (regs))

    #regs = readregs(30015, 10)
    #print("Serial number:", regs2str (regs))
    
    regs = readregs(30025, 10)
    print("Part number:", regs2str (regs))
    
    regs = readregs(30070, 2)
    print("Model ID:", regs[0])
    print("Number of PV strings:", regs[1])
    
    regs = readregs(32000, 1)
    print("State 1:", regs[0])
    
    regs = readregs(32016, 4)
    print("PV 1 voltage: %.1f V" % (regs[0] / 10.0))
    print("PV 1 current: %.2f A" % (regs[1] / 100.0))
    print("PV 2 voltage: %.1f V" % (regs[2] / 10.0))
    print("PV 2 current: %.2f A" % (regs[3] / 100.0))
    
    regs = readregs(32064, 2)
    print("Input power: %.3f kW" % (regs[0] / 10.0))
    
    regs = readregs(32066, 10)
    print("Power grid line AB voltage: %.3f V" % (regs[0] / 10.0))
    print("Power grid line BC voltage: %.3f V" % (regs[1] / 10.0))
    print("Power grid line CA voltage: %.3f V" % (regs[2] / 10.0))
    print("Power grid phase A voltage: %.3f V" % (regs[3] / 10.0))
    print("Power grid phase B voltage: %.3f V" % (regs[4] / 10.0))
    print("Power grid phase C voltage: %.3f V" % (regs[5] / 10.0))
    
    regs = readregs(32078, 2)
    print("Peak active power of current day: %.4f kW" % ((regs[1] + (regs[0] << 16)) / 1000.0))

    regs = readregs(32087, 1)
    print("Internal temperature: %.1f Celsius" % (regs[0] / 10.0))
    
    regs = readregs(32089, 1)
    status_str = "Unknown"
    r = regs[0]
    if (r == 0x0000):
        status_str = "Standby: initializing"
    elif (r == 0x0001):
        status_str = "Standby: detecting insulation resistance"
    elif (r == 0x0002):
        status_str = "Standby: detecting irradiation"
    elif (r == 0x0003):
        status_str = "Standby: drid detecting"
    elif (r == 0x0100):
        status_str = "Starting"
    elif (r == 0x0200):
        status_str = "On-grid (Off-grid mode: running)"
    elif (r == 0x0201):
        status_str = "Grid connection: power limited (Off-grid mode: running: power limited)"
    elif (r == 0x0202):
        status_str = "Grid connection: self- derating (Off-grid mode: running: self- derating)"
    elif (r == 0x0203):
        status_str = "Off-grid Running"
    elif (r == 0x0300):
        status_str = "Shutdown: fault"
    elif (r == 0x0301):
        status_str = "Shutdown: command"
    elif (r == 0x0302):
        status_str = "Shutdown: OVGR"
    elif (r == 0x0303):
        status_str = "Shutdown: communication disconnected"
    elif (r == 0x0304):
        status_str = "Shutdown: power limited"
    elif (r == 0x0305):
        status_str = "Shutdown: manual startup required"
    elif (r == 0x0306):
        status_str = "Shutdown: DC switches disconnected"
    elif (r == 0x0307):
        status_str = "Shutdown: rapid cutoff"
    elif (r == 0x0308):
        status_str = "Shutdown: input underpower"
    elif (r == 0x0401):
        status_str = "Grid scheduling: cosφ-P curve"
    elif (r == 0x0402):
        status_str = "Grid scheduling: Q-U curve"
    elif (r == 0x0403):
        status_str = "Grid scheduling: PF-U curve"
    elif (r == 0x0404):
        status_str = "Grid scheduling: dry contact"
    elif (r == 0x0405):
        status_str = "Grid scheduling: Q-P curve"
    elif (r == 0x0500):
        status_str = "Spot-check ready"
    elif (r == 0x0501):
        status_str = "Spot-checking"
    elif (r == 0x0600):
        status_str = "Inspecting"
    elif (r == 0x0700):
        status_str = "AFCI self check"
    elif (r == 0x0800):
        status_str = "I-V scanning"
    elif (r == 0x0900):
        status_str = "DC input detection"
    elif (r == 0x0A00):
        status_str = "Running: off-grid charging"
    elif (r == 0xA000):
        status_str = "Standby: no irradiation"

    print("Device status: 0x%X %s" % (regs[0], status_str))
    
    regs = readregs(43006, 2)
    print("Time zone: %i" % (regs[0]))
    print("Time source: %i" % (regs[1]))

    print ("close connection")
    client.close()


