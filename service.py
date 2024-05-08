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
    tempo_enabled_warning_emitted = False

    def __init__(self):
        super().__init__()
        self.overlay = OverlayText(font="font30_title")
        self.speed_saved = "1.25"
        self.timer_speed = None
        self.timer_label = None
        self.tempo_enabled = False

    def __del__(self):
        self.clean()
        del self.overlay

    @staticmethod
    def speed_get():
        ps = xbmc.getInfoLabel("Player.PlaySpeed")
        return ps if ps != "0.00" else None

    @staticmethod
    def speed_set(speed):
        xbmc.executebuiltin(f"PlayerControl(Tempo({speed}))")

    def onPlayBackStarted(self):
        # self.tempo_enabled = False
        self.stop_timers()

    def onAVStarted(self):
        if not self.tempo_enabled:
            self.tempo_enabled = xbmc.getCondVisibility("Player.TempoEnabled")
            if not self.tempo_enabled and not KodiPlayer.tempo_enabled_warning_emitted:
                KodiPlayer.tempo_enabled_warning_emitted = True
                xbmc.log(f"{xbmcaddon.Addon().getAddonInfo('id')}: changing speed not possible (is 'Sync playback to display' enabled?)", xbmc.LOGWARNING)

        if xbmc.getCondVisibility("!Window.IsVisible(videoosd)"):
            self.overlay.text = f"[{xbmc.getInfoLabel('VideoPlayer.PlaylistPosition')}/{xbmc.getInfoLabel('VideoPlayer.PlaylistLength')}] {xbmc.getInfoLabel('Player.Filename')}"
            self.overlay.visible = True
            self.timer_label_start()
        else:
            self.overlay.visible = False

        if not self.tempo_enabled:
            return
        self.timer_speed_start()

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

    def timer_speed_cb(self):
        ps = KodiPlayer.speed_get()
        if not ps:
            self.timer_speed_start()
            return

        if ps == KodiPlayer.SPEED_NORMAL:
            KodiPlayer.speed_set(self.speed_saved)
        self.timer_speed = None

    def timer_speed_start(self):
        self.timer_speed = threading.Timer(3.0, self.timer_speed_cb)
        self.timer_speed.start()

    def timer_speed_stop(self):
        if self.timer_speed is None:
            return
        self.timer_speed.cancel()
        self.timer_speed = None

    def timer_label_cb(self):
        self.overlay.visible = False
        self.timer_label = None

    def timer_label_start(self):
        self.timer_label = threading.Timer(3.0, self.timer_label_cb)
        self.timer_label.start()

    def timer_label_stop(self):
        if self.timer_label is None:
            return
        self.timer_label.cancel()
        self.timer_label = None

    def stop_timers(self):
        self.timer_speed_stop()
        self.timer_label_stop()

    def clean(self):
        self.stop_timers()
        self.overlay.visible = False


class KodiMonitor(xbmc.Monitor):
    ADDON_ID = xbmcaddon.Addon().getAddonInfo("id")

    def __init__(self):
        super().__init__()
        self.player = KodiPlayer()

    def __del__(self):
        del self.player

    def cancel_player_timer(self):
        self.player.timer_speed_stop()
        xbmcgui.Dialog().notification(xbmcaddon.Addon().getAddonInfo("name"), "Delayed speed setting cancelled", time=1000, sound=False)

    def onNotification(self, sender, method, data):
        if sender != KodiMonitor.ADDON_ID or not self.player.tempo_enabled:
            return

        try:
            if method == "Other.toggle_speed":
                ps = KodiPlayer.speed_get()
                if ps == KodiPlayer.SPEED_NORMAL:
                    if self.player.timer_speed is None:
                        KodiPlayer.speed_set(self.player.speed_saved)
                        return
                    self.cancel_player_timer()
                elif ps:
                    current_time = self.player.getTime()
                    KodiPlayer.speed_set(KodiPlayer.SPEED_NORMAL)
                    xbmc.sleep(100)
                    self.player.seekTime(current_time)
                elif self.player.timer_speed is not None:
                    self.cancel_player_timer()
            elif method == "Other.add_speed":
                KodiPlayer.speed_set(float(KodiPlayer.speed_get()) + float(data))
        except:
            pass


if __name__ == "__main__":
    monitor = KodiMonitor()
    monitor.waitForAbort()

    del monitor
