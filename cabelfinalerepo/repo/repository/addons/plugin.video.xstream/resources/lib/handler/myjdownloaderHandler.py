from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib.tools import logger
import myjdapi


class cMyJDownloaderHandler:

    def sendToMyJDownloader(self, sUrl, sMovieTitle):
        if self.__checkConfig() == False:
            cGui().showError('MyJDownloader', 'Settings ueberpruefen', 5)
            return False

        jd = myjdapi.Myjdapi()
        if jd.connect(self.__getUser(), self.__getPass()) == False:
            cGui().showError('MyJDownloader', 'Keine Verbindung zu MY.JDownloader', 5)
            return False

        if jd.update_devices() == False:
            cGui().showError('MyJDownloader', 'Konnte Geraete Liste nicht laden', 5)
            return False

        device = jd.get_device(self.__getDevice())
        if device.linkgrabber.add_links([{"autostart": False, "links": sUrl, "packageName": sMovieTitle}])['id'] > 0:
            cGui().showInfo('MyJDownloader', 'Link gesendet', 5)
            return True
        return False

    def __checkConfig(self):
        logger.info('check MYJD Addon setings')
        if cConfig().getSetting('myjd_enabled') == 'true':
            return True
        return False

    def __getDevice(self):
        return cConfig().getSetting('myjd_device')

    def __getUser(self):
        return cConfig().getSetting('myjd_user')

    def __getPass(self):
        return cConfig().getSetting('myjd_pass')
