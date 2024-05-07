import os
import threading
import xbmc
import xbmcaddon
import xbmcgui


class OverlayText:
    # https://github.com/elgatito/plugin.video.elementum/blob/master/resources/site-packages/elementum/overlay.py
    def __init__(self, *args, **kwargs):
        self.window = xbmcgui.Window(12005) # WINDOW_FULLSCREEN_VIDEO
        w = self.window.getWidth() # not screen resolution
        h = 0
        x = 20
        y = 80
        _text = ""
        self._label = xbmcgui.ControlLabel(x, y, w, h, _text, *args, **kwargs)
        self._shadow = xbmcgui.ControlLabel(x + 1, y + 1, w, h, _text, textColor="0xD0000000", *args, **kwargs)
        self._background = xbmcgui.ControlImage(x, y, w, h, os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "img", "black.png"), colorDiffuse="0xD0000000")
        self.window.addControls([self._background, self._shadow, self._label])

    def __del__(self):
        self.window.removeControls([self._background, self._shadow, self._label])
        del self._background
        del self._shadow
        del self._label

    @property
    def visible(self):
        return self._label.isVisible()
    
    @visible.setter
    def visible(self, show):
        if self.visible == show:
            return
        self._background.setVisible(show)
        self._shadow.setVisible(show)
        self._label.setVisible(show)

    @property
    def text(self):
        return self._label.getLabel()

    @text.setter
    def text(self, text):
        self._label.setLabel(text)
        self._shadow.setLabel(text)


class KodiPlayer(xbmc.Player):
    SPEED_NORMAL = "1.00"

    def __init__(self):
        super().__init__()
        self.speed_saved = "1.25"
        self.overlay = OverlayText(font="font30_title")
        self.timers = [None] * 2
        self.tempo_enabled = False
        self.tempo_enabled_warning_emitted = False

    def __del__(self):
        self.clean()
        del self.overlay

    @staticmethod
    def speed_get():
        return xbmc.getInfoLabel("Player.PlaySpeed")

    @staticmethod
    def speed_set(speed):
        xbmc.executebuiltin(f"PlayerControl(Tempo({speed}))")

    def onPlayBackStarted(self):
        self.stop_timers()
        self.overlay.visible = False

    def onAVStarted(self):
        if not self.tempo_enabled:
            self.tempo_enabled = xbmc.getCondVisibility("Player.TempoEnabled")
            if not self.tempo_enabled and not self.tempo_enabled_warning_emitted:
                self.tempo_enabled_warning_emitted = True
                xbmc.log("defvidspeed: changing speed not possible (is \"Sync playback to display\" enabled?)", xbmc.LOGWARNING)
        if xbmc.getCondVisibility("!Window.IsVisible(videoosd)"):
            self.overlay.text = f"[{xbmc.getInfoLabel('VideoPlayer.PlaylistPosition')}/{xbmc.getInfoLabel('VideoPlayer.PlaylistLength')}] {xbmc.getInfoLabel('Player.Filename')}"
            self.overlay.visible = True
            self.start_label_timer()
        if self.tempo_enabled:
            self.start_speed_timer()

    def onPlayBackEnded(self):
        self.clean()

    def onPlayBackError(self):
        self.clean()

    def onPlayBackSpeedChanged(self, speed):
        if speed != 1 or not self.tempo_enabled:
            return

        ps = KodiPlayer.speed_get()
        if ps and ps != KodiPlayer.SPEED_NORMAL:
            self.speed_saved = ps

    def onPlayBackStopped(self):
        self.clean()

    def speed_timer_callback(self):
        if xbmc.getCondVisibility("Player.Paused"):
            self.start_speed_timer()
            return

        if KodiPlayer.speed_get() == KodiPlayer.SPEED_NORMAL:
            KodiPlayer.speed_set(self.speed_saved)
        self.stop_speed_timer(True)

    def label_timer_callback(self):
        self.overlay.visible = False
        self.timers[1] = None

    def start_speed_timer(self):
        self.timers[0] = threading.Timer(3.0, self.speed_timer_callback)
        self.timers[0].start()

    def stop_speed_timer(self, skip_cancel=False):
        if self.timers[0] is None:
            return
        if not skip_cancel:
            self.timers[0].cancel()
        self.timers[0] = None

    def start_label_timer(self):
        self.timers[1] = threading.Timer(3.0, self.label_timer_callback)
        self.timers[1].start()

    def stop_timers(self):
        self.stop_speed_timer()
        for i in range(1, len(self.timers)):
            if not self.timers[i]:
                continue
            self.timers[i].cancel()
            self.timers[i] = None

    def clean(self):
        self.stop_timers()
        self.overlay.visible = False


class KodiMonitor(xbmc.Monitor):

    def __init__(self):
        super().__init__()
        self.player = KodiPlayer()

    def __del__(self):
        del self.player

    def onNotification(self, sender, method, data):
        if not self.player.tempo_enabled or sender != "pk.q12.defvidspeed":
            return

        try:
            if method == "Other.toggle_speed":
                if KodiPlayer.speed_get() == KodiPlayer.SPEED_NORMAL:
                    KodiPlayer.speed_set(self.player.speed_saved)
                else:
                    current_time = self.player.getTime()
                    self.player.stop_speed_timer()
                    KodiPlayer.speed_set(KodiPlayer.SPEED_NORMAL)
                    xbmc.sleep(100)
                    self.player.seekTime(current_time)
            elif method == "Other.add_speed":
                KodiPlayer.speed_set(float(KodiPlayer.speed_get()) + float(data))
        except:
            pass


if __name__ == "__main__":
    monitor = KodiMonitor()
    monitor.waitForAbort()

    del monitor
