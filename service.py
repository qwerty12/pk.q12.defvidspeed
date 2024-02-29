import xbmc
import threading


NORMAL_SPEED = "1.00"
saved_speed = "1.25"

def setSpeed(speed):
    xbmc.executebuiltin(f"PlayerControl(Tempo({speed}))")

def getPlaybackSpeed():
    return xbmc.getInfoLabel("Player.PlaySpeed")

class KodiPlayer(xbmc.Player):
    
    def __init__(self):
        xbmc.Player.__init__(self)
        self.seek_timer = None

    def onAVStarted(self, *args, **kwargs):
        self.stop_seek_timer()
        self.seek_timer = threading.Timer(3.0, self.execute_builtin)
        self.seek_timer.start()

    def onPlayBackEnded(self):
        self.stop_seek_timer()

    def onPlayBackError(self):
        self.stop_seek_timer()

    def onPlayBackSpeedChanged(self, speed):
        if speed != 1:
            return

        ps = getPlaybackSpeed()
        if ps and ps != NORMAL_SPEED:
            global saved_speed
            saved_speed = ps

    def onPlayBackStopped(self):
        self.stop_seek_timer()

    def execute_builtin(self):
        try:
            setSpeed(saved_speed)
        except:
            pass
        self.seek_timer = None

    def stop_seek_timer(self):
        if self.seek_timer:
            try:
                self.seek_timer.cancel()
            except:
                pass
            self.seek_timer = None


class KodiMonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)

    def onNotification(self, sender, method, data):
        if sender == "pk.q12.defvidspeed":
            if method == "Other.toggle_speed":
                try:
                    if getPlaybackSpeed() == NORMAL_SPEED:
                        setSpeed(saved_speed)
                    else:
                        current_time = xbmc.Player().getTime()
                        setSpeed(NORMAL_SPEED)
                        xbmc.sleep(100)
                        xbmc.Player().seekTime(current_time)
                except:
                    pass


if __name__ == '__main__':
    monitor = KodiMonitor()
    player = KodiPlayer()
    
    while not monitor.abortRequested():
        if monitor.waitForAbort():
            break
