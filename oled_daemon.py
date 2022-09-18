#!/usr/bin/env python
import device
import keys
import colors

import dbus
import dbus.service  # yes, you need to import this as well

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

UID = 'org.guido.apex7tklp.Daemon'
UID_PATH = '/org/guido/apex7tklp/Daemon'

class ApexDaemon(dbus.service.Object):

    def __init__(self, bus_name):
        self._device = device.Device()
        self.monitor_running = False
        super().__init__(
            bus_name, UID_PATH
        )
        self._monitor()


    def _monitor(self):
        with self._device as dev:
            dev.oled_monitor()
        self.monitor_running = True


    @dbus.service.method(
        dbus_interface=UID, out_signature='i'
    )
    def start_monitor(self) -> int:
        daemon = Thread(target=self._monitor, daemon=True, name='MonitorThread')
        daemon.start()
        return 0

        
    @dbus.service.method(
        dbus_interface=UID, in_signature='s'
    )
    def set_colors(self, colordef):
        print(colordef)
        l = colordef.split(',')
        print(l)
        defs = {}

        while len(l) > 0:
            key_target = l.pop(0).split(",")
            col = l.pop(0)

            for tgt in key_target:
                if tgt == '--':
                    # special: applies color to all yet unused colors
                    for keycode in keys.others(defs.keys()):
                        defs[keycode] = colors.get(col)
                for keycode in keys.get(tgt):
                    if keycode is None:
                        continue
                    defs[keycode] = colors.get(col)

        if len(defs) == 0:
            raise Exception("could not determine any color definitions")

        COLOR_PAYLOAD = []
        for keycode, color in defs.items():
            COLOR_PAYLOAD += [keycode]
            COLOR_PAYLOAD += color

        with self._device as dev:
            dev.send_colors(COLOR_PAYLOAD)


def main():
    DBusGMainLoop(set_as_default=True)
    try:
        bus_name = dbus.service.BusName(
            UID, bus=dbus.SessionBus(), do_not_queue=True
        )
    except dbus.exceptions.NameExistsException:
        print(f'Service with id {UID} is already running')
        exit(1)
    loop = GLib.MainLoop()
    daemon = ApexDaemon(bus_name)
    try:
        loop.run()
    except KeyboardInterrupt:
        print('KeyboardInterrupt received')
    except Exception as e:
        print('Unhandled exception: `{}`'.format(str(e)))
    finally:
        loop.quit()


if __name__ == '__main__':
    main()
