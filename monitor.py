import psutil
import sensors
import humanize

from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier
from dasbus.loop import EventLoop

from threading import Thread
from time import sleep


class Monitor:

    def __init__(self):
        self.ram_total = 1
        self.ram_available = 1
        self.swap_percent = 0
        self.cpu_percent = 0
        self.cpu_count = 1
        self.loadavg = [0,0,0]
        self.temp = [0,0]
        self.media_title = ""
        self.media_artist = ""
        self.daemon = Thread(target=self.update, daemon=True, name='Background')
        self.daemon.start()
        self.dbusdaemon = Thread(target=self.dbuslisten, daemon=True, name='DBus listener')
        self.dbusdaemon.start()
        self.updated = False


    def __repr__(self):
        return """*********************************
                   RAM total:    %s
                   RAM available:%s
                   SWAP percent: %s
                   CPU percent:  %s
                   LOADAVG:      %s
                   Sensors:      %s
                   MEDIA title:  %s
                   MEDIA artist: %s
        """ % (self.ram_total, self.ram_available, self.swap_percent, self.cpu_percent, self.loadavg, ",".join(self.temp), self.media_title, self.media_artist)


    def callback(self, interface:str, properties_changed, Properties_invalid):
        # print("CALLBACK")
        if 'Metadata' in properties_changed:
            metadata = properties_changed['Metadata']
            self.media_artist = ','.join(metadata['xesam:artist'])
            self.media_title = metadata['xesam:title']
            self.media_title += " ("+metadata['xesam:album']+")"
            # print("%s %s" % (self.media_artist, self.media_title))


    def dbuslisten(self):
        self.proxy = SessionMessageBus().get_proxy("org.mpris.MediaPlayer2.playerctld", "/org/mpris/MediaPlayer2")
        self.proxy.PropertiesChanged.connect(self.callback)
        loop = EventLoop()
        loop.run()


    def update(self):
        while True:
            #print("UPDATE")
            self.ram_total = psutil.virtual_memory().total
            self.ram_available = psutil.virtual_memory().available
            self.swap_percent = psutil.swap_memory().percent
            self.cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_count = psutil.cpu_count()
            self.loadavg = psutil.getloadavg()
            self.temp = []
            sensors.init()
            try: 
                for chip in sensors.iter_detected_chips():
                    features = chip.adapter_name + '::'
                    for feature in chip:
                        if feature.type == 2:
                            features += ' %s:%.1f°C ' % (feature.label.replace(' ','_'), feature.get_value())
                    self.temp.append(features)
            finally:
                sensors.cleanup()
            self.updated = True
            #print(repr(self))
            sleep(3)

    def memory(self):
        while not self.updated:
            pass
        return [ "Memory           Free", 
                 "Ram  %4s%%%11s" % (format((self.ram_total - self.ram_available) * 100 / self.ram_total, ".1f"), humanize.naturalsize(self.ram_available, gnu=True)), 
                 "Swap %4s%%%11s" % (format(self.swap_percent, ".1f"), '') ]

    def cpu(self):
        while not self.updated:
            pass
        return [ "Load Average",
                 "CPU      1m   5m  15m",
                 "%5s %5s%5s%5s" % (format(self.cpu_percent, ".1f")+"%", format(self.loadavg[0], ".1f"), format(self.loadavg[1], ".1f"), format(self.loadavg[2], ".1f")) ]

    def sensors(self):
        while not self.updated:
            pass
        return [ "Sensors", self.temp[0] if len(self.temp) > 0 else '', self.temp[1] if len(self.temp) > 1 else '' ]

    
    def media(self):
        while not self.updated:
            pass
        return [ "Mediaplayer", self.media_title, self.media_artist ]
