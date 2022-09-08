
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import sys
import glob
import shutil
import re
import os

try:  # Python 3
    from urllib.parse import quote_plus
    import zipfile
except ImportError:  # Python 2
    from urllib import quote_plus
    from resources.libs import zipfile

from resources.libs.common.config import CONFIG
from resources.libs import db
from resources.libs.common import logging
from resources.libs.common import tools


def cleanup_backup():
    folder = glob.glob(os.path.join(CONFIG.MYBUILDS, "*"))
    logging.log(folder)
    list = []
    filelist = []

    dialog = xbmcgui.Dialog()

    if len(folder) == 0:
        logging.log_notify(CONFIG.ADDONTITLE,
                           "[COLOR {0}]Backup Location: Empty[/COLOR]".format(CONFIG.COLOR2))
        return
    for item in sorted(folder, key=os.path.getmtime):
        filelist.append(item)
        base = item.replace(CONFIG.MYBUILDS, '')
        if os.path.isdir(item):
            list.append('/{0}/'.format(base))
        elif os.path.isfile(item):
            list.append(base)
    list = ['[COLORred]Backup Ordner komplett bereinigen![/COLOR]'] + list
    selected = dialog.select("{0}".format(CONFIG.ADDONTITLE),
                             list)

    if selected == -1:
        logging.log_notify(CONFIG.ADDONTITLE,
                           "[COLOR {0}]Clean Up Cancelled![/COLOR]".format(CONFIG.COLOR2))
    elif selected == 0:
        if dialog.yesno(CONFIG.ADDONTITLE, "[COLOR {0}]Willst du den kompletten Backup Ordner bereinigen?[/COLOR]".format(CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.MYBUILDS),
                        yeslabel="[COLORlime]Ja[/COLOR]",
                        nolabel="[COLORred]Nein[/COLOR]"):
            clearedfiles, clearedfolders = tools.clean_house(CONFIG.MYBUILDS)
            logging.log_notify(CONFIG.ADDONTITLE,
                               "[COLOR {0}]Removed Files: [COLOR {1}]{2}[/COLOR] / Folders:[/COLOR] [COLOR {3}]{4}[/COLOR]".format(
                                   CONFIG.COLOR2, CONFIG.COLOR1, clearedfiles, CONFIG.COLOR1, clearedfolders))
        else:
            logging.log_notify(CONFIG.ADDONTITLE,
                               "[COLOR {0}]Clean Up Cancelled![/COLOR]".format(CONFIG.COLOR2))
    else:
        path = filelist[selected - 1]
        passed = False

        if dialog.yesno(CONFIG.ADDONTITLE, "[COLOR {0}]Willst du [COLOR {1}]{2}[/COLOR] aus deinem Backup Ordner löschen?[/COLOR]".format(CONFIG.COLOR2, CONFIG.COLOR1, list[selected]) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, path),
                        yeslabel="[COLORlime]Ja[/COLOR]",
                        nolabel="[COLORred]Nein[/COLOR]"):
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    passed = True
                except:
                    logging.log("Unable to remove: {0}".format(path))
            else:
                tools.clean_house(path)
                try:
                    shutil.rmtree(path)
                    passed = True
                except Exception as e:
                    logging.log("Error removing {0}: {1}".format(path, e))
            if passed:
                logging.log_notify(CONFIG.ADDONTITLE,
                                   "[COLOR {0}]{1} Removed![/COLOR]".format(CONFIG.COLOR2, list[selected]))
            else:
                logging.log_notify(CONFIG.ADDONTITLE,
                                   "[COLOR {0}]Error Removing {1}![/COLOR]".format(CONFIG.COLOR2, list[selected]))
        else:
            logging.log_notify(CONFIG.ADDONTITLE,
                               "[COLOR {0}]Clean Up Cancelled![/COLOR]".format(CONFIG.COLOR2))


class Backup:
    def __init__(self):
        tools.ensure_folders()

        self.dialog = xbmcgui.Dialog()
        self.progress_dialog = xbmcgui.DialogProgress()

    def backup_addon_pack(self, name=""):
        if self.dialog.yesno(CONFIG.ADDONTITLE,
                             "[COLOR {0}]Willst du ein Addon Backup erstellen?[/COLOR]".format(CONFIG.COLOR2),
                             nolabel="[COLORred]Nein[/COLOR]",
                             yeslabel="[COLORlime]Ja[/COLOR]"):
            if name == "":
                name = tools.get_keyboard("", "Bitte gib einen Namen für das Backup ein!")
                if not name:
                    return False
                name = quote_plus(name)
            name = '{0}.zip'.format(name)
            tempzipname = ''
            zipname = os.path.join(CONFIG.MYBUILDS, name)
            try:
                zipf = zipfile.ZipFile(xbmcvfs.translatePath(zipname), mode='w', allowZip64=True)
            except:
                try:
                    tempzipname = os.path.join(CONFIG.PACKAGES, '{0}.zip'.format(name))
                    zipf = zipfile.ZipFile(tempzipname, mode='w', allowZip64=True)
                except:
                    logging.log("Unable to create {0}.zip".format(name), level=xbmc.LOGERROR)
                    if self.dialog.yesno(CONFIG.ADDONTITLE,
                                         "[COLOR {0}]In den aktuellen Backup Ordner kann nicht geschrieben werden, willst du einen anderen wählen?[/COLOR]".format(CONFIG.COLOR2),
                                         yeslabel="[COLORlime]Ja[/COLOR]",
                                         nolabel="[COLORred]Nein[/COLOR]"):
                        CONFIG.open_settings()
                        return
                    else:
                        return
            fold = glob.glob(os.path.join(CONFIG.ADDONS, '*/'))
            addonnames = []
            addonfolds = []
            for folder in sorted(fold, key=lambda x: x):
                foldername = os.path.split(folder[:-1])[1]
                if foldername in CONFIG.EXCLUDES:
                    continue
                elif foldername in CONFIG.DEFAULTPLUGINS:
                    continue
                elif foldername == 'packages':
                    continue
                xml = os.path.join(folder, 'addon.xml')
                if os.path.exists(xml):
                    match = tools.parse_dom(tools.read_from_file(xml), 'addon', ret='name')
                    if len(match) > 0:
                        addonnames.append(match[0])
                        addonfolds.append(foldername)
                    else:
                        addonnames.append(foldername)
                        addonfolds.append(foldername)

            selected = self.dialog.multiselect(
                "Wähle Addons für das Backup aus.".format(CONFIG.ADDONTITLE), addonnames)
            if selected is None:
                selected = []

            logging.log(selected)
            self.progress_dialog.create(CONFIG.ADDONTITLE, '[COLOR {0}]Erstelle Backup:[/B][/COLOR]'.format(CONFIG.COLOR2) + '\n' + 'Bitte warten...')
            if len(selected) > 0:
                added = []
                for item in selected:
                    added.append(addonfolds[item])
                    self.progress_dialog.update(0, '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, addonfolds[item]))
                    for base, dirs, files in os.walk(os.path.join(CONFIG.ADDONS, addonfolds[item])):
                        files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                        for file in files:
                            if file.endswith('.pyo'):
                                continue
                            self.progress_dialog.update(0, '\n' +"[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, addonfolds[item]) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, file))
                            fn = os.path.join(base, file)
                            zipf.write(fn, fn[len(CONFIG.ADDONS):], zipfile.ZIP_DEFLATED)
                    dep = os.path.join(CONFIG.ADDONS, addonfolds[item], 'addon.xml')
                    if os.path.exists(dep):
                        match = tools.parse_dom(tools.read_from_file(dep), 'import', ret='addon')
                        for depends in match:
                            if 'xbmc.python' in depends:
                                continue
                            if depends in added:
                                continue
                            self.progress_dialog.update(0, '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, depends))
                            for base, dirs, files in os.walk(os.path.join(CONFIG.ADDONS, depends)):
                                files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                                for file in files:
                                    if file.endswith('.pyo'):
                                        continue
                                    self.progress_dialog.update(0, '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, depends) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, file))
                                    fn = os.path.join(base, file)
                                    zipf.write(fn, fn[len(CONFIG.ADDONS):], zipfile.ZIP_DEFLATED)
                                    added.append(depends)
            self.dialog.ok(CONFIG.ADDONTITLE,"[COLOR {0}]{1}[/COLOR] [COLOR {2}]Backup erstellt:[/COLOR]".format(CONFIG.COLOR1, name, CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, zipname))

    def backup_build(self, name=""):
        if self.dialog.yesno(CONFIG.ADDONTITLE,
                             "[COLOR {0}]Willst du ein Build Backup erstellen?[/COLOR]".format(CONFIG.COLOR2), nolabel="[COLORred]Nein[/COLOR]", yeslabel="[COLORlime]Ja[/COLOR]"):
            if name == "":
                name = tools.get_keyboard("", "Bitte gib einen Namen für das Backup ein!")
                if not name:
                    return False
                name = name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?',
                                                                                                         '').replace(
                    '"', '').replace('<', '').replace('>', '').replace('|', '')
            name = quote_plus(name)
            tempzipname = ''
            zipname = os.path.join(CONFIG.MYBUILDS, '{0}.zip'.format(name))
            for_progress = 0
            ITEM = []
            exclude_dirs = CONFIG.EXCLUDE_DIRS

            if not self.dialog.yesno(CONFIG.ADDONTITLE, "Willst du die Addon Daten mit hinzufügen?".format(CONFIG.COLOR2) + '\n' + "Diese enthalten alle Addon-Einstellungen einschließlich Passwörter, aber auch wichtige Informationen wie z.B. Skin-Shortcuts.[CR]Wir empfehlen das Backup anschließend manuell zu überprüfen und evtl. empfindliche Daten zu löschen.".format(CONFIG.COLOR1, CONFIG.COLOR1) + '\n' + " ".format(CONFIG.COLOR1, CONFIG.ADDON_ID), yeslabel='[COLORlime]Ja[/COLOR]',nolabel='[COLORred]Nein[/COLOR]'):
                exclude_dirs.append('addon_data')

            tools.convert_special(CONFIG.HOME, True)
            extractsize = 0
            try:
                zipf = zipfile.ZipFile(xbmcvfs.translatePath(zipname), mode='w', allowZip64=True)
            except:
                try:
                    tempzipname = os.path.join(CONFIG.PACKAGES, '{0}.zip'.format(name))
                    zipf = zipfile.ZipFile(tempzipname, mode='w', allowZip64=True)
                except:
                    logging.log("Unable to create {0}.zip".format(name), level=xbmc.LOGERROR)
                    if self.dialog.yesno(CONFIG.ADDONTITLE,
                                         "[COLOR {0}]In den aktuellen Backup Ordner kann nicht geschrieben werden, willst du einen anderen wählen?[/COLOR]".format(CONFIG.COLOR2),
                                         yeslabel="[COLORlime]Ja[/COLOR]",
                                         nolabel="[COLORred]Nein[/COLOR]"):
                        CONFIG.open_settings()
                        return
                    else:
                        return
            self.progress_dialog.create(CONFIG.ADDONTITLE + "[COLOR {0}][/COLOR]".format(CONFIG.COLOR2) + '\n' + "[COLOR {0}]".format(CONFIG.COLOR2) + '\n' + "Bitte warten...[/COLOR]")

            for base, dirs, files in os.walk(CONFIG.HOME):
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                for file in files:
                    ITEM.append(file)

            N_ITEM = len(ITEM)
            picture = []
            music = []
            video = []
            programs = []
            repos = []
            scripts = []
            skins = []
            fold = glob.glob(os.path.join(CONFIG.ADDONS, '*/'))
            idlist = []

            binaries = []
            binidlist = []

            for folder in sorted(fold, key=lambda x: x):
                foldername = os.path.split(folder[:-1])[1]
                if foldername == 'packages':
                    continue

                binaryid, binaryname = db.find_binary_addons(addon=foldername)

                if binaryid:
                    binaries.append(binaryname)
                    binidlist.append(binaryid)

                xml = os.path.join(folder, 'addon.xml')
                if os.path.exists(xml):
                    a = tools.read_from_file(xml)
                    prov = re.compile("<provides>(.+?)</provides>").findall(a)
                    match = tools.parse_dom(prov, 'addon', ret='id')

                    addid = foldername if len(match) == 0 else match[0]
                    if addid in idlist:
                        continue
                    idlist.append(addid)
                    try:
                        add = xbmcaddon.Addon(id=addid)
                        aname = add.getAddonInfo('name')
                        aname = aname.replace('[', '<').replace(']', '>')
                        aname = str(re.sub('<[^<]+?>', '', aname)).lstrip()
                    except:
                        aname = foldername
                    if len(prov) == 0:
                        if foldername.startswith('skin'):
                            skins.append(aname)
                        elif foldername.startswith('repo'):
                            repos.append(aname)
                        else:
                            scripts.append(aname)
                        continue
                    if not (prov[0]).find('executable') == -1:
                        programs.append(aname)
                    if not (prov[0]).find('video') == -1:
                        video.append(aname)
                    if not (prov[0]).find('audio') == -1:
                        music.append(aname)
                    if not (prov[0]).find('image') == -1:
                        picture.append(aname)
            db.fix_metas()

            binarytxt = self._backup_binaries(binidlist)

            for base, dirs, files in os.walk(CONFIG.HOME):
                dirs[:] = [d for d in dirs if os.path.join(base, d) not in exclude_dirs]
                files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                for file in files:
                    try:
                        for_progress += 1
                        progress = tools.percentage(for_progress, N_ITEM)
                        self.progress_dialog.update(int(progress), '[COLOR {0}]Erstelle Backup: [COLOR {1}]{2}[/COLOR] / [COLOR {3}]{4}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, for_progress, CONFIG.COLOR1, N_ITEM) + '\n' + '[COLOR {0}]{1}[/COLOR]'.format(CONFIG.COLOR1, file))
                        fn = os.path.join(base, file)
                        if file in CONFIG.LOGFILES:
                            logging.log("[Back Up] Type = build: Ignore {0} - Log File".format(file))
                            continue
                        elif os.path.join(base, file) in CONFIG.EXCLUDE_FILES:
                            logging.log("[Back Up] Type = build: Ignore {0} - Excluded File".format(file))
                            continue
                        elif os.path.join('addons', 'packages') in fn:
                            logging.log("[Back Up] Type = build: Ignore {0} - Packages Folder".format(file))
                            continue
                        elif file.startswith('._') or file.lower().startswith('.ds_store'):
                            logging.log("[Back Up] Type = build: Ignore {0} - OSX metadata file".format(file))
                            continue
                        elif file.endswith('.pyo'):
                            continue
                        elif file.lower().endswith('.db') and 'database' in base:
                            temp = file.replace('.db', '')
                            temp = ''.join([i for i in temp if not i.isdigit()])
                            if temp in CONFIG.DB_FILES:
                                if not file == db.latest_db(temp):
                                    logging.log("[Back Up] Type = build: Ignore {0} - DB File".format(file))
                                    continue

                        skipbinary = False
                        if len(binidlist) > 0:
                            for id in binidlist:
                                id = os.path.join(CONFIG.ADDONS, id)
                                if id in fn:
                                    skipbinary = True

                        if skipbinary:
                            logging.log("[Back Up] Type = build: Ignore {0} - Binary Add-on".format(file))
                            continue

                        try:
                            zipf.write(fn, fn[len(CONFIG.HOME):], zipfile.ZIP_DEFLATED)
                            extractsize += os.path.getsize(fn)
                        except Exception as e:
                            logging.log("[Back Up] Type = build: Unable to backup {0}".format(file))
                            logging.log("{0} / {1}".format(Exception, e))
                        if self.progress_dialog.iscanceled():
                            self.progress_dialog.close()
                            logging.log_notify(CONFIG.ADDONTITLE,
                                               "[COLOR {0}]Backup Cancelled[/COLOR]".format(CONFIG.COLOR2))
                            sys.exit()
                    except Exception as e:
                        logging.log("[Back Up] Type = build: Unable to backup {0}".format(file))
                        logging.log("Build Backup Error: {0}".format(str(e)))

            if 'addon_data' in exclude_dirs:
                match = glob.glob(os.path.join(CONFIG.ADDON_DATA, 'skin.*', ''))
                for fold in match:
                    fd = os.path.split(fold[:-1])[1]
                    if fd not in ['skin.confluence', 'skin.estuary', 'skin.estouchy']:
                        for base, dirs, files in os.walk(os.path.join(CONFIG.ADDON_DATA, fold)):
                            files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                            for file in files:
                                fn = os.path.join(base, file)
                                zipf.write(fn, fn[len(CONFIG.HOME):], zipfile.ZIP_DEFLATED)
                                extractsize += os.path.getsize(fn)
                        xml = os.path.join(CONFIG.ADDONS, fd, 'addon.xml')
                        if os.path.exists(xml):
                            matchxml = tools.parse_dom(tools.read_from_file(xml), 'import', ret='addon')
                            if 'script.skinshortcuts' in matchxml:
                                for base, dirs, files in os.walk(
                                        os.path.join(CONFIG.ADDON_DATA, 'script.skinshortcuts')):
                                    files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                                    for file in files:
                                        fn = os.path.join(base, file)
                                        zipf.write(fn, fn[len(CONFIG.HOME):], zipfile.ZIP_DEFLATED)
                                        extractsize += os.path.getsize(fn)
            zipf.close()
            xbmc.sleep(500)
            self.progress_dialog.close()

            backup('gui', name)

            if not tempzipname == '':
                success = xbmcvfs.rename(tempzipname, zipname)
                if success == 0:
                    xbmcvfs.copy(tempzipname, zipname)
                    xbmcvfs.delete(tempzipname)

            if binarytxt is not None:
                bintxtpath = os.path.join(CONFIG.USERDATA, binarytxt)
                xbmcvfs.delete(bintxtpath)

            self._backup_info(name, extractsize, programs, video, music, picture, repos, scripts, binaries)

            if len(binaries) > 0:
                self.dialog.ok(CONFIG.ADDONTITLE,
                               "[COLOR {0}]Die folgenden Addons wurden vom Backup ausgeschlossen, da sie plattformspezifisch sind:[/COLOR]".format(CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, ', '.join(binaries)))

            self.dialog.ok(CONFIG.ADDONTITLE, "[COLOR {0}]{1}[/COLOR] [COLOR {2}]Backup abgeschlossen:[/COLOR]".format(CONFIG.COLOR1, name, CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, zipname))

    def _backup_info(self, name, extractsize, programs, video, music, picture, repos, scripts, binaries):
        backup_path = CONFIG.MYBUILDS
        zipname = name + '.zip'
        txtname = name + '.txt'
        backup_zip = os.path.join(backup_path, zipname)
        temp_txt = os.path.join(CONFIG.PACKAGES, txtname)
        info_txt = os.path.join(backup_path, txtname)
        
        _skin_root = xbmcvfs.translatePath('special://skin/')
        _skin_id = os.path.basename(os.path.normpath(_skin_root))
        _skin = xbmcaddon.Addon(_skin_id)
        _skin_name = xbmcvfs.translatePath(_skin.getAddonInfo('name'))

        with open(temp_txt, 'w') as f:
            f.write('name="{0}"\n'.format(name))
            f.write('extracted="{0}"\n'.format(extractsize))
            f.write('zipsize="{0}"\n'.format(os.path.getsize(backup_zip)))
            f.write('skin="{0}"\n'.format(_skin_name))
            f.write('created="{0}"\n'.format(tools.get_date(formatted=True)))
            f.write('programs="{0}"\n'.format(', '.join(programs)) if len(programs) > 0 else 'programs="none"\n')
            f.write('video="{0}"\n'.format(', '.join(video)) if len(video) > 0 else 'video="none"\n')
            f.write('music="{0}"\n'.format(', '.join(music)) if len(music) > 0 else 'music="none"\n')
            f.write('picture="{0}"\n'.format(', '.join(picture)) if len(picture) > 0 else 'picture="none"\n')
            f.write('repos="{0}"\n'.format(', '.join(repos)) if len(repos) > 0 else 'repos="none"\n')
            f.write('scripts="{0}"\n'.format(', '.join(scripts)) if len(scripts) > 0 else 'scripts="none"\n')
            f.write('binaries="{0}"\n'.format(', '.join(binaries)) if len(binaries) > 0 else 'binaries="none"\n')
            
        xbmcvfs.copy(temp_txt, info_txt)
        xbmcvfs.delete(temp_txt)

    def _backup_binaries(self, ids):
        txtname = None

        if len(ids) > 0:
            path = CONFIG.USERDATA
            txtname = 'build_binaries.txt'
            txt_path = os.path.join(path, txtname)

            with open(txt_path, 'w') as f:
                for id in ids:
                    if ids.index(id) == len(ids) - 1:
                        f.write(id)
                    else:
                        f.write(id + ',')

        return txtname

    def backup_gui(self, name=""):
        if name == "":
            guiname = tools.get_keyboard("", "Bitte gib einen Namen für das GuiFix Backup ein!")
            if not guiname:
                return False
            tools.convert_special(CONFIG.USERDATA, True)
            tools.ascii_check(CONFIG.USERDATA, True)
        else:
            guiname = name
        guiname = quote_plus(guiname)
        tempguizipname = ''
        guizipname = os.path.join(CONFIG.MYBUILDS, '{0}_guisettings.zip'.format(guiname))
        if os.path.exists(CONFIG.GUISETTINGS):
            try:
                zipf = zipfile.ZipFile(guizipname, mode='w', allowZip64=True)
            except:
                try:
                    tempguizipname = os.path.join(CONFIG.PACKAGES, '{0}_guisettings.zip'.format(guiname))
                    zipf = zipfile.ZipFile(tempguizipname, mode='w', allowZip64=True)
                except:
                    logging.log("Unable to create {0}_guisettings.zip".format(guiname), level=xbmc.LOGERROR)
                    if self.dialog.yesno(CONFIG.ADDONTITLE, "[COLOR {0}In den aktuellen Backup Ordner kann nicht geschrieben werden, willst du einen anderen wählen?[/COLOR]".format(CONFIG.COLOR2),
                                         yeslabel="[COLORlime]Ja[/COLOR]",
                                         nolabel="[COLORred]Nein[/COLOR]"):
                        CONFIG.open_settings()
                        return
                    else:
                        return
            try:
                zipf.write(CONFIG.GUISETTINGS, 'guisettings.xml', zipfile.ZIP_DEFLATED)
                zipf.write(CONFIG.PROFILES, 'profiles.xml', zipfile.ZIP_DEFLATED)
                match = glob.glob(os.path.join(CONFIG.ADDON_DATA, 'skin.*', ''))
                for fold in match:
                    fd = os.path.split(fold[:-1])[1]
                    if fd not in ['skin.confluence', 'skin.estuary', 'skin.estouchy']:
                        if self.dialog.yesno(CONFIG.ADDONTITLE, "[COLOR {0}]Willst du den folgenden Skin zum GuiFix Backup hinzufügen?[/COLOR]".format(CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, fd),
                                             yeslabel="[COLORlime]Ja[/COLOR]",
                                             nolabel="[COLORred]Nein[/COLOR]"):
                            for base, dirs, files in os.walk(os.path.join(CONFIG.ADDON_DATA, fold)):
                                files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                                for file in files:
                                    fn = os.path.join(base, file)
                                    zipf.write(fn, fn[len(CONFIG.USERDATA):], zipfile.ZIP_DEFLATED)
                            xml = os.path.join(CONFIG.ADDONS, fd, 'addon.xml')
                            if os.path.exists(xml):
                                matchxml = tools.parse_dom(tools.read_from_file(xml), 'import', ret='addon')
                                if 'script.skinshortcuts' in matchxml:
                                    for base, dirs, files in os.walk(
                                            os.path.join(CONFIG.ADDON_DATA, 'script.skinshortcuts')):
                                        files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                                        for file in files:
                                            fn = os.path.join(base, file)
                                            zipf.write(fn, fn[len(CONFIG.USERDATA):], zipfile.ZIP_DEFLATED)
                        else:
                            logging.log("[Back Up] Type = guifix: {0} ignored".format(fold))
            except Exception as e:
                logging.log("[Back Up] Type = guifix: {0}".format(e))
                pass
            zipf.close()
            if not tempguizipname == '':
                success = xbmcvfs.rename(tempguizipname, guizipname)
                if success == 0:
                    xbmcvfs.copy(tempguizipname, guizipname)
                    xbmcvfs.delete(tempguizipname)
        else:
            logging.log("[Back Up] Type = guifix: guisettings.xml not found")
        if name == "":
            self.dialog.ok(CONFIG.ADDONTITLE, "[COLOR {0}]GuiFix Backup abgeschlossen:[/COLOR]".format(CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, guizipname))

    def backup_theme(self, name=""):
        if not self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2), "[COLOR {0}]Willst du ein Theme Backup erstellen?[/COLOR]".format(CONFIG.COLOR2),
                                 yeslabel="[COLORlime]Ja[/COLOR]",
                                 nolabel="[COLORred]Nein[/COLOR]"):
            logging.log_notify("Theme Backup", "Cancelled!")
            return False
        if name == "":
            themename = tools.get_keyboard("", "Bitte gib einen Namen für das Theme Backup ein!")
            if not themename:
                return False
        else:
            themename = name
        themename = quote_plus(themename)
        tempzipname = ''
        zipname = os.path.join(CONFIG.MYBUILDS, '{0}.zip'.format(themename))
        try:
            zipf = zipfile.ZipFile(zipname, mode='w', allowZip64=True)
        except:
            try:
                tempzipname = os.path.join(CONFIG.PACKAGES, '{0}.zip'.format(themename))
                zipf = zipfile.ZipFile(tempzipname, mode='w', allowZip64=True)
            except:
                logging.log("Unable to create {0}.zip".format(themename), level=xbmc.LOGERROR)
                if self.dialog.yesno(CONFIG.ADDONTITLE, "[COLOR {0}]In den aktuellen Backup Ordner kann nicht geschrieben werden, willst du einen anderen wählen?[/COLOR]".format(CONFIG.COLOR2),
                                     yeslabel="[COLORlime]Ja[/COLOR]",
                                     nolabel="[COLORred]Nein[/COLOR]"):
                    CONFIG.open_settings()
                    return
                else:
                    return
        tools.convert_special(CONFIG.USERDATA, True)
        tools.ascii_check(CONFIG.USERDATA, True)
        try:
            if not CONFIG.SKIN not in ['skin.confluence', 'skin.estuary', 'skin.estouchy']:
                skinfold = os.path.join(CONFIG.SKIN, 'media')
                match2 = glob.glob(os.path.join(skinfold, '*.xbt'))
                if len(match2) > 1:
                    if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2) + '\n' + "[COLOR {0}]Willst du die Textures.xbt auswählen?[/COLOR]".format(CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.SKIN),
                                         yeslabel="[COLORlime]Ja[/COLOR]",
                                         nolabel="[COLORred]Nein[/COLOR]"):
                        for xbt in match2:
                            if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2), "[COLOR {0}]Willst du die Texture Datei [COLOR {1}]{2}[/COLOR] hinzufügen?".format(CONFIG.COLOR1, CONFIG.COLOR2, xbt.replace(skinfold, "")[1:]) + '\n' + "from [COLOR {0}]{1}[/COLOR][/COLOR]".format(CONFIG.COLOR1, CONFIG.SKIN),
                                    yeslabel="[COLORlime]Ja[/COLOR]",
                                    nolabel="[COLORred]Nein[/COLOR]"):
                                fn = xbt
                                fn2 = fn.replace(CONFIG.HOME, "")
                                zipf.write(fn, fn2, zipfile.ZIP_DEFLATED)
                else:
                    for xbt in match2:
                        if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2), "[COLOR {0}]Willst du die Texture Datei [COLOR {1}]{2}[/COLOR] hinzufügen?".format(CONFIG.COLOR2, CONFIG.COLOR1, xbt.replace(skinfold, "")[1:]) + '\n' + "from [COLOR {0}]{1}[/COLOR][/COLOR]".format(CONFIG.COLOR1, CONFIG.SKIN),
                                yeslabel="[COLORlime]Ja[/COLOR]",
                                nolabel="[COLORred]Nein[/COLOR]"):
                            fn = xbt
                            fn2 = fn.replace(CONFIG.HOME, "")
                            zipf.write(fn, fn2, zipfile.ZIP_DEFLATED)
                ad_skin = os.path.join(CONFIG.ADDON_DATA, CONFIG.SKIN, 'settings.xml')
                if os.path.exists(ad_skin):
                    if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2), "[COLOR {0}]Willst du die [COLOR {1}]settings.xml[/COLOR] aus [COLOR {2}]/addon_data/[/COLOR] hinzufügen?".format(
                                             CONFIG.COLOR2, CONFIG.COLOR1, CONFIG.COLOR1) + '\n'+ "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.SKIN),
                                         yeslabel="[COLORlime]Ja[/COLOR]",
                                         nolabel="[COLORred]Nein[/COLOR][/B]"):
                        ad_skin2 = ad_skin.replace(CONFIG.HOME, "")
                        zipf.write(ad_skin, ad_skin2, zipfile.ZIP_DEFLATED)
                match = tools.parse_dom(tools.read_from_file(os.path.join(CONFIG.SKIN, 'addon.xml')), 'import',
                                        ret='addon')
                if 'script.skinshortcuts' in match:
                    if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2), "[COLOR {0}Willst du die [COLOR {1}]settings.xml[/COLOR] für [COLOR {2}]script.skinshortcuts[/COLOR] hinzufügen?".format(CONFIG.COLOR2, CONFIG.COLOR1, CONFIG.COLOR1),
                                         yeslabel="[COLORlime]Ja[/COLOR]",
                                         nolabel="[COLORred]Nein[/COLOR]"):
                        for base, dirs, files in os.walk(os.path.join(CONFIG.ADDON_DATA, 'script.skinshortcuts')):
                            files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                            for file in files:
                                fn = os.path.join(base, file)
                                zipf.write(fn, fn[len(CONFIG.HOME):], zipfile.ZIP_DEFLATED)
            if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2),
                                 "[COLOR {0}]Willst du einen [COLOR {1}]Backgrounds[/COLOR] Ordner hinzufügen?[/COLOR]".format(
                                     CONFIG.COLOR2, CONFIG.COLOR1),
                                 yeslabel="[COLORlime]Ja[/COLOR]",
                                 nolabel="[COLORred]Nein[/COLOR]"):
                fn = self.dialog.browse(0, 'Wähle den Backgrounds Ordner aus.', 'files', '', True, False, CONFIG.HOME,
                                        False)
                if not fn == CONFIG.HOME:
                    for base, dirs, files in os.walk(fn):
                        dirs[:] = [d for d in dirs if os.path.join(base, d) not in CONFIG.EXCLUDE_DIRS]
                        files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                        for file in files:
                            try:
                                fn2 = os.path.join(base, file)
                                zipf.write(fn2, fn2[len(CONFIG.HOME):], zipfile.ZIP_DEFLATED)
                            except Exception as e:
                                logging.log("[Back Up] Type = theme: Unable to backup {0}".format(file))
                                logging.log("Backup Error: {0}".format(str(e)))
                text = db.latest_db('Textures')
                if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2),
                                     "[COLOR {0}]Willst du [COLOR {1}]{2}[/COLOR] hinzufügen?[/COLOR]".format(
                                         CONFIG.COLOR2, CONFIG.COLOR1, text),
                                     yeslabel="[COLORlime]Ja[/COLOR]",
                                     nolabel="[COLORred]Nein[/COLOR]"):
                    zipf.write(os.path.join(CONFIG.DATABASE, text), '/userdata/Database/{0}'.format(text),
                               zipfile.ZIP_DEFLATED)
            if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2),
                                 "[COLOR {0}]Willst du irgendwelche Addons hinzufügen?[/COLOR]".format(CONFIG.COLOR2),
                                 yeslabel="[COLORlime]Ja[/COLOR]",
                                 nolabel="[COLORred]Nein[/COLOR]"):
                fold = glob.glob(os.path.join(CONFIG.ADDONS, '*/'))
                addonnames = []
                addonfolds = []
                for folder in sorted(fold, key=lambda x: x):
                    foldername = os.path.split(folder[:-1])[1]
                    if foldername in CONFIG.EXCLUDES:
                        continue
                    elif foldername in CONFIG.DEFAULTPLUGINS:
                        continue
                    elif foldername == 'packages':
                        continue
                    xml = os.path.join(folder, 'addon.xml')
                    if os.path.exists(xml):
                        match = tools.parse_dom(tools.read_from_file(xml), 'addon', ret='name')
                        if len(match) > 0:
                            addonnames.append(match[0])
                            addonfolds.append(foldername)
                        else:
                            addonnames.append(foldername)
                            addonfolds.append(foldername)
                selected = self.dialog.multiselect(
                    "Wähle die Addons aus..".format(CONFIG.ADDONTITLE), addonnames)
                if selected is None:
                    selected = []
                if len(selected) > 0:
                    added = []
                    for item in selected:
                        added.append(addonfolds[item])
                        for base, dirs, files in os.walk(os.path.join(CONFIG.ADDONS, addonfolds[item])):
                            files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                            for file in files:
                                if file.endswith('.pyo'):
                                    continue
                                fn = os.path.join(base, file)
                                zipf.write(fn, fn[len(CONFIG.HOME):], zipfile.ZIP_DEFLATED)
                        dep = os.path.join(CONFIG.ADDONS, addonfolds[item], 'addon.xml')
                        if os.path.exists(dep):
                            match = tools.parse_dom(tools.read_from_file(dep), 'import', ret='addon')
                            for depends in match:
                                if 'xbmc.python' in depends:
                                    continue
                                if depends in added:
                                    continue
                                for base, dirs, files in os.walk(os.path.join(CONFIG.ADDONS, depends)):
                                    files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                                    for file in files:
                                        if file.endswith('.pyo'):
                                            continue
                                        fn = os.path.join(base, file)
                                        zipf.write(fn, fn[len(CONFIG.HOME):], zipfile.ZIP_DEFLATED)
                                        added.append(depends)
            if self.dialog.yesno(CONFIG.ADDONTITLE + '[COLOR {0}]: Theme Backup[/COLOR]'.format(CONFIG.COLOR2),
                                 "[COLOR {0}]Willst du die [COLOR {1}]guisettings.xml[/COLOR] hinzufügen?[/COLOR]".format(
                                     CONFIG.COLOR2, CONFIG.COLOR1),
                                 yeslabel="[COLORlime]Ja[/COLOR]",
                                 nolabel="[COLORred]Nein[/COLOR]"):
                zipf.write(CONFIG.GUISETTINGS, '/userdata/guisettings.xml', zipfile.ZIP_DEFLATED)
        except Exception as e:
            zipf.close()
            logging.log("[Back Up] Type = theme: {0}".format(str(e)))
            self.dialog.ok(CONFIG.ADDONTITLE,
                           "[COLOR {0}]{1}[/COLOR][COLOR {2}] Theme Backup fehlgeschlagen:[/COLOR]".format(CONFIG.COLOR1, themename, CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, str(e)))
            if not tempzipname == '':
                try:
                    os.remove(tempzipname)
                except Exception as e:
                    logging.log(str(e))
            else:
                try:
                    os.remove(zipname)
                except Exception as e:
                    logging.log(str(e))
            return
        zipf.close()
        if not tempzipname == '':
            success = xbmcvfs.rename(tempzipname, zipname)
            if success == 0:
                xbmcvfs.copy(tempzipname, zipname)
                xbmcvfs.delete(tempzipname)
        self.dialog.ok(CONFIG.ADDONTITLE, "[COLOR {0}]{1}[/COLOR][COLOR {2}] Theme Backup abgeschlossen:[/COLOR]".format(CONFIG.COLOR1, themename, CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, zipname))

    def backup_addon_data(self, name=""):
        if self.dialog.yesno(CONFIG.ADDONTITLE,
                             "[COLOR {0}]Willst du ein Addon Daten Backup erstellen?[/COLOR]".format(
                                 CONFIG.COLOR2),
                             nolabel="[COLORred]Nein[/COLOR]",
                             yeslabel="[COLORlime]Ja[/COLOR]"):
            if name == "":
                name = tools.get_keyboard("", "Bitte gib einen Namen für das Addon Daten Backup ein!")
                if not name:
                    return False
                name = quote_plus(name)
            name = '{0}_addondata.zip'.format(name)
            tempzipname = ''
            zipname = os.path.join(CONFIG.MYBUILDS, name)
            try:
                zipf = zipfile.ZipFile(xbmcvfs.translatePath(zipname), mode='w', allowZip64=True)
            except:
                try:
                    tempzipname = os.path.join(CONFIG.PACKAGES, '{0}.zip'.format(name))
                    zipf = zipfile.ZipFile(tempzipname, mode='w', allowZip64=True)
                except:
                    logging.log("Unable to create {0}_addondata.zip".format(name), level=xbmc.LOGERROR)
                    if self.dialog.yesno(CONFIG.ADDONTITLE,
                                         "[COLOR {0}]In den aktuellen Backup Ordner kann nicht geschrieben werden, willst du einen anderen wählen?[/COLOR]".format(
                                             CONFIG.COLOR2),
                                         yeslabel="[COLORlime]Ja[/COLOR]",
                                         nolabel="[COLORred]Nein[/COLOR]"):
                        CONFIG.open_settings()
                        return
                    else:
                        return
            for_progress = 0
            ITEM = []
            tools.convert_special(CONFIG.ADDON_DATA, True)
            tools.ascii_check(CONFIG.ADDON_DATA, True)
            self.progress_dialog.create(CONFIG.ADDONTITLE + "[COLOR {0}][/COLOR]".format(CONFIG.COLOR2), "[COLOR {0}]".format(CONFIG.COLOR2) + '\n' + "Bitte warten...[/COLOR]")
            for base, dirs, files in os.walk(CONFIG.ADDON_DATA):
                dirs[:] = [d for d in dirs if os.path.join(base, d) not in CONFIG.EXCLUDE_DIRS]
                files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                for file in files:
                    ITEM.append(file)
            N_ITEM = len(ITEM)

            bad_files = [
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.exodusredux', 'cache.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.exodusredux', 'cache.meta.5.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.exodusredux', 'cache.providers.13.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.thecrew', 'cache.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.thecrew', 'cache.meta.5.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.thecrew', 'cache.providers.13.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.scrubsv2', 'cache.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.scrubsv2', 'cache.meta.5.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.scrubsv2', 'cache.providers.13.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.venom', 'cache.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.venom', 'cache.meta.5.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.venom', 'cache.providers.13.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.numbersbynumbers', 'cache.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.numbersbynumbers', 'cache.meta.5.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.numbersbynumbers', 'cache.providers.13.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.gaia', 'cache.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.gaia', 'meta.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.seren', 'cache.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'plugin.video.seren', 'torrentScrape.db')),
                (os.path.join(CONFIG.ADDON_DATA, 'script.module.simplecache', 'simplecache.db'))]

            for base, dirs, files in os.walk(CONFIG.ADDON_DATA):
                dirs[:] = [d for d in dirs if os.path.join(base, d) not in CONFIG.EXCLUDE_DIRS]
                files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
                for file in files:
                    try:
                        for_progress += 1
                        progress = tools.percentage(for_progress, N_ITEM)
                        self.progress_dialog.update(int(progress), '[COLOR {0}]Erstelle Backup: [COLOR{1}]{2}[/COLOR] / [COLOR{3}]{4}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, for_progress, CONFIG.COLOR1, N_ITEM) + '\n' + '[COLOR {0}]{1}[/COLOR]'.format(CONFIG.COLOR1, file))
                        fn = os.path.join(base, file)
                        if file in CONFIG.LOGFILES:
                            logging.log("[Back Up] Type = addon_data: Ignore {0} - Log Files".format(file))
                            continue
                        elif os.path.join(base, file) in bad_files:
                            logging.log("[Back Up] Type = addon_data: Ignore {0} - Cache Files".format(file))
                            continue
                        elif os.path.join('addons', 'packages') in fn:
                            logging.log("[Back Up] Type = addon_data: Ignore {0} - Packages Folder".format(file))
                            continue
                        elif file.endswith('.csv'):
                            logging.log("[Back Up] Type = addon_data: Ignore {0} - CSV File".format(file))
                            continue
                        elif file.endswith('.db') and 'Database' in base:
                            temp = file.replace('.db', '')
                            temp = ''.join([i for i in temp if not i.isdigit()])
                            if temp in CONFIG.DB_FILES:
                                if not file == db.latest_db(temp):
                                    logging.log("[Back Up] Type = addon_data: Ignore {0} - Database Files".format(file))
                                    continue
                        try:
                            zipf.write(fn, fn[len(CONFIG.ADDON_DATA):], zipfile.ZIP_DEFLATED)
                        except Exception as e:
                            logging.log("[Back Up] Type = addon_data: Unable to backup {0}".format(file))
                            logging.log("Backup Error: {0}".format(str(e)))
                    except Exception as e:
                        logging.log("[Back Up] Type = addon_data: Unable to backup {0}".format(file))
                        logging.log("Backup Error: {0}".format(str(e)))
            zipf.close()
            if not tempzipname == '':
                success = xbmcvfs.rename(tempzipname, zipname)
                if success == 0:
                    xbmcvfs.copy(tempzipname, zipname)
                    xbmcvfs.delete(tempzipname)
            self.progress_dialog.close()
            self.dialog.ok(CONFIG.ADDONTITLE, "[COLOR {0}]{1}[/COLOR] [COLOR {2}] Backup abgeschlossen:[/COLOR]".format(CONFIG.COLOR1, name, CONFIG.COLOR2) + '\n' + "[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, zipname))


def backup(action, name=''):
    cls = Backup()

    if action == "addonpack":
        cls.backup_addon_pack(name)
    elif action == "build":
        cls.backup_build(name)
    elif action == "gui":
        cls.backup_gui(name)
    elif action == "theme":
        cls.backup_theme(name)
    elif action == "addondata":
        cls.backup_addon_data(name)

################################################################################
#  Copyright (C) 2019 drinfernoo / Modified & translated by SGK 2021           #
#                                                                              #
#  This Program is free software; you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by        #
#  the Free Software Foundation; either version 2, or (at your option)         #
#  any later version.                                                          #
#                                                                              #
#  This Program is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with XBMC; see the file COPYING.  If not, write to                    #
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.       #
#  http://www.gnu.org/copyleft/gpl.html                                        #
################################################################################