import xbmc
import threading


class KodiPlayer(xbmc.Player):
    
    def __init__(self):
        xbmc.Player.__init__(self)
        self.seek_timer = None

    def onAVStarted(self, *args, **kwargs):
        self.stop_seek_timer()
        self.seek_timer = threading.Timer(1.0, self.execute_builtin)
        self.seek_timer.start()

    def onPlayBackEnded(self):
        self.stop_seek_timer()

    def onPlayBackError(self):
        self.stop_seek_timer()

    def onPlayBackStopped(self):
        self.stop_seek_timer()

    def execute_builtin(self):
        try:
            xbmc.executebuiltin("PlayerControl(Tempo(1.25))")
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
                    if xbmc.getInfoLabel("Player.PlaySpeed") == "1.25":
                        current_time = xbmc.Player().getTime()
                        xbmc.executebuiltin("PlayerControl(Tempo(1.00))")
                        xbmc.sleep(100)
                        xbmc.Player().seekTime(current_time)
                    else:
                        xbmc.executebuiltin("PlayerControl(Tempo(1.25))")
                except:
                    pass


if __name__ == '__main__':
    monitor = KodiMonitor()
    player = KodiPlayer()
    
    while not monitor.abortRequested():
        if monitor.waitForAbort():
            break
