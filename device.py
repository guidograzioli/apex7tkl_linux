import os
import sys
from time import sleep
import traceback
from cinematic import DefaultHardwareCinematic, cinematicManager, cinematicScene, cinematicTextStatic

os.environ['LIBUSB_DEBUG'] = 'debug'
import usb.core
from usb.core import USBError
import usb.util

from monitor import Monitor
import oled

import threading

DEFAULT_LEN = 642

TARGETS = [
    { "name": "apex7", "idVendor": 0x1038, "idProduct": 0x1612, "oledPreamble": [0x65] },
    { "name": "apex7tkl", "idVendor": 0x1038, "idProduct": 0x1618, "oledPreamble": [0x65] },
    { "name": "apex5", "idVendor": 0x1038, "idProduct": 0x161c, "oledPreamble": [0x65] },
    { "name": "apexpro", "idVendor": 0x1038, "idProduct": 0x1610, "oledPreamble": [0x61] }
]

def find_device():
    """Find the first matching keyboard device in the TARGETS list"""

    for target in TARGETS:
        try:
            dev = usb.core.find(idVendor = target['idVendor'], idProduct = target['idProduct'])
            if dev is not None:
                return target, dev
        except USBError as e:
            print(f"usb::find({target['name']}) failed: {e}")

    raise Exception("Cannot find a matching device")

def detach_kernel(dev):
    if dev.is_kernel_driver_active(1) == True:
        try:
            print("dev::detach_kernel_driver - interface 1")
            dev.detach_kernel_driver(1)
            return True
        except USBError as e:
            print("dev::detach_kernel_driver failed" + str(e))
    return False

def reattach_kernel(dev, was_detached):
    print("dev::dispose_resources")
    usb.util.dispose_resources(dev)
    if was_detached:
        try:
            print("dev::attach_kernel_driver - interface 1")
            dev.attach_kernel_driver(1)
        except USBError as e:
            print("dev::attach_kernel_driver failed" + str(e))

class Device():
    def __init__ (self):
        self.target = None
        self.handle = None
        self._was_detached = None
        self._paused = False
        self.lock = threading.Lock()

    def __enter__ (self):
        self.target, self.handle = find_device()
        self._was_detached = detach_kernel(self.handle)
        return self

    def __exit__ (self, type, value, tb):
        reattach_kernel(self.handle, self._was_detached)


    def pad(self, payload, maxlen=642):
        if len(payload) < maxlen:
            payload += [0x00] * (maxlen - len(payload))
        return payload

    def send(self, wValue = 0x300, reqType = 0x01, payload=None):
        if payload is None:
            raise Exception("payload cannot be null")
        # try:
        with self.lock:
            self.handle.ctrl_transfer(0x21,
                    0x09,
                    wValue,
                    reqType,
                    payload)
        # except usb.core.USBError as err:
        #     print(f"Error connecting to USB device: {err.strerror}")
        #     exit(-1)

    def send_colors(self, color_payload):
        self._paused = True
        report = [0x3a, 0x69] + color_payload
        report = self.pad(report, DEFAULT_LEN)
        self.send(0x300, 0x01, report)
        self._paused = False

    def set_config(self, config_id):
        report = [0x89] + [config_id]
        report = self.pad(report, 20)
        self.send(0x200, 0x01, report)

    def oled_blank(self, filename="./images/blank.png"):
        self.oled_image(filename)

    def oled_image(self, filename):
        imagedata = oled.image_to_payload(filename)
        if isinstance(imagedata, list):
            if isinstance(imagedata[0], int):
                report = self.target['oledPreamble'] + imagedata
                self.send(0x300, 0x01, report)
            elif isinstance(imagedata[0], list):
                while True:
                    for it in imagedata:
                        report = self.target['oledPreamble'] + it
                        sleep(0.1)
                        self.send(0x300, 0x01, report)

    def oled_text(self, text):
        imagedata = oled.text_payload(text)
        report = self.target['oledPreamble'] + imagedata
        self.send(0x300, 0x01, report)

    def oled_monitor(self):
        mon = Monitor()
        mng = DefaultHardwareCinematic(mon)
        while True:
            while mng.isEnded() == False:
                for _ in range(0, 3):
                    if not self._paused:
                        msg = mng.display()
                        # print("MSG START")
                        # print(msg)
                        # print("MSG END")
                        imagedata = oled.text_payload(msg)
                        report = self.target['oledPreamble'] + imagedata
                        self.send(0x300, 0x01, report)
                        sleep(0.3)
                mng.next()
            mng.restart()