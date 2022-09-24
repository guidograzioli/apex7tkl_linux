
class cinematicTextStatic:
    def __init__(self, text: str, step: int, max: int):
        self.txt = text
        self.offset = 0
        self.step = step
        self.max = max

    def isEnded(self) -> bool:
        return self.step == self.offset

    def restart(self):
        self.offset = 0

    def next(self):
        if (self.isEnded() == False):
            self.offset += 1

    def display(self) -> str:
        txt = (" " * self.max + self.txt + " " * self.max)
        pos = int(float(len(txt) / 2) - float(self.max / 2))
        return txt[pos:pos + self.max]

class cinematicTextDynamic:
    def __init__(self, text: str, max: int, c: int):
        self.txt = text
        self.offset = 0
        self.max = max
        self.char = chr(c)

    def isEnded(self) -> bool:
        return (self.max + len(self.txt)) == self.offset

    def restart(self):
        self.offset = 0

    def next(self):
        if (self.isEnded() == False):
            self.offset += 1

    def display(self) -> str:
        return (self.char * self.max + self.txt + self.char * self.max)[self.offset:self.offset + self.max]


class cinematicManager:
    def __init__(self, rendered):
        self.func = rendered
        self.list = [ cinematicTextStatic(x, 21, 21) if len(x) < 22 else cinematicTextDynamic(x, 21, ord(' ')) for x in self.func() ]

    def isEnded(self) -> bool:
        for it in self.list:
            if it.isEnded() == False:
                return False
        return True

    def restart(self):
        print("mgr RESTART")
        self.list = [ cinematicTextStatic(x, 21, 21) if len(x) < 22 else cinematicTextDynamic(x, 21, ord(' ')) for x in self.func() ]
        for it in self.list:
            it.restart()

    def next(self):
        for it in self.list:
            if (it.isEnded() == False):
                it.next()

    def display(self) -> str:
        data = []
        for it in self.list:
            data += [it.display()]
        return "\n".join(data).strip()

class cinematicScene:
    def __init__(self):
        self.list = []

    def isEnded(self) -> bool:
        for it in self.list:
            if it.isEnded() == False:
                return False
        return True

    def restart(self):
        for it in self.list:
            it.restart()

    def next(self):
        for it in self.list:
            if (it.isEnded() == False):
                it.next()
                return

    def display(self) -> str:
        for it in self.list:
            if (it.isEnded() == False):
                return it.display()
        return self.list[-1].display()

def DefaultHardwareCinematic(mon) -> cinematicScene:

    mng = cinematicScene()
    scnMem = cinematicManager(mon.memory)
    scnCpu = cinematicManager(mon.cpu)
    scnSens = cinematicManager(mon.sensors)
    scnMedia = cinematicManager(mon.media)
    mng.list = [
        scnCpu,
        scnMem,
        scnSens,
        scnMedia
    ]
    return mng