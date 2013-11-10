#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Instanciation de la fenêtre principale.
"""

import sys
import os
import time

from ast import literal_eval as litval

import wx
import wx.lib.agw.aui as aui
import wx.lib.dialogs
from wx.lib.wordwrap import wordwrap
#from wx.lib.buttons import ThemedGenBitmapToggleButton as togbutbmp

from  phpyclilib import editors as eds
from  phpyclilib import searchctrl as scf
from  phpyclilib import consolephp as clp
from  phpyclilib import userprefs as ups
from  phpyclilib import loadjson as ljs


class PhPyCli(wx.Frame):
    """Initialisation de la fenêtre principale.
    Le module editors instancie un nouvel éditeur comme page du NoteBook AUI.
    Le module searchctrl instancie un champ de recherche dans la barre d'outil.
    Le module console instancie une fenêtre avec une console (wxprocess)
    Le module userprefs charge les variables choisies par l'utilisateur
    """
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.userdatas = ljs.loadJson('/datas/user_prefs.json')
        self.toggleprefs = True
        self.getPrefs = None

        self.process = None
        self.startproc = 0
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_END_PROCESS, self.OnProcessEnded)

        self.timer = None
        self.Bind(wx.EVT_TIMER, self.gaugeAnimate)

        self.toggleconsole = True

        self.session = {'curf': {'id': None, 'path': None, 'saved': False, 'toggle': False}, 'editors': {}}

        self.viewport = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER|wx.SP_LIVE_UPDATE)

        self.viewport_input = wx.Panel(self.viewport, -1)
        self.textctrl_input = aui.AuiNotebook(self)

        self.viewport_output = wx.Panel(self.viewport, -1)
        self.textctrl_output = wx.TextCtrl(self.viewport_output, -1, "", style=wx.TE_MULTILINE)

        # Menu Bar

        # Menu Fichier
        self.main_window_menubar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.newfitem = self.file_menu.Append(wx.ID_NEW, 'Nouveau', 'Ouvrir un nouveau fichier')
        self.dirfitem = self.file_menu.Append(wx.ID_OPEN, 'Ouvrir', 'Ouvrir un fichier')
        self.file_menu.AppendSeparator()
        self.savefitem = self.file_menu.Append(wx.ID_SAVE, 'Sauvegarder', 'Sauvegarder le fichier courant')
        self.savefasitem = self.file_menu.Append(wx.ID_SAVEAS, 'Sauvegarder sous...', 'Sauvegarder le fichier courant sous...')
        self.execfitem = self.file_menu.Append(wx.ID_ANY, 'Exécuter\tCtrl+E', 'Exécuter le fichier courant')
        self.file_menu.AppendSeparator()
        self.quititem = self.file_menu.Append(wx.ID_EXIT, 'Quitter', 'Fermer l\'application')
        self.main_window_menubar.Append(self.file_menu, "&Fichier")

        # Menu Edition
        self.menuedition = wx.Menu()
        self.prefsitem = self.menuedition.Append(wx.ID_ANY, "Préréfences", "Gérer les préférences de l'application")
        self.main_window_menubar.Append(self.menuedition, "&Edition")

        # Menu Aide
        self.menuhelp = wx.Menu()
        self.helpitem = self.menuhelp.Append(wx.ID_HELP, "Aide", "Afficher l'aide")
        self.menuhelp.AppendSeparator()
        self.aboutitem = self.menuhelp.Append(wx.ID_ABOUT, "A propos", "A propos de PhPyCli")
        self.main_window_menubar.Append(self.menuhelp, "&Aide")
        # fin menu aide

        self.SetMenuBar(self.main_window_menubar)
        # Menu Bar end

        # Status Bar
        self.main_window_statusbar = self.CreateStatusBar(3, 0)

        # Tool Bar
        self.toolbar = wx.ToolBar(self, -1)
        self.SetToolBar(self.toolbar)
        tsize = (24,24)
        new_bmp =  wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, tsize)
        open_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize)
        save_bmp =  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tsize)
        saveas_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, tsize)
        exec_bmp = wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_TOOLBAR, tsize)
        #inter_bmp = wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_TOOLBAR, tsize)
        quit_bmp = wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR, tsize)
        clear_bmp = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR, tsize)

        self.toolbar.AddLabelTool(10, "Nouveau", new_bmp, shortHelp="Nouveau", longHelp="Créer un nouveau fichier")
        self.toolbar.AddLabelTool(20, "Ouvrir", open_bmp, shortHelp="Ouvrir", longHelp="Ouvrir un fichier")
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(30, "Sauvegarder", save_bmp, shortHelp="Sauvegarder", longHelp="Sauvegarder le fichier <CTRL+S>")
        self.toolbar.AddLabelTool(40, "Sauvegarder sous", saveas_bmp, shortHelp="Sauvegarder sous", longHelp="")
        self.toolbar.AddLabelTool(50, "Exécuter", exec_bmp, shortHelp="Exécuter", longHelp="Exécuter le fichier en cours <CTRL+E>")
        self.toolbar.EnableTool(50, False)
        self.toolbar.AddLabelTool(70, "Vider", clear_bmp, shortHelp="Vider l'output", longHelp="Vider le champ de sortie")
        self.toolbar.AddSeparator()
        self.interphp = wx.BitmapButton(self.toolbar, -1, wx.Bitmap(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + "/img/console.png", wx.BITMAP_TYPE_ANY))
        #self.interphp = togbutbmp(self.toolbar, -1, wx.Bitmap(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + "/img/console.png", wx.BITMAP_TYPE_ANY))
        #self.interphp.SetSize(self.interphp.GetBestSize())
        self.toolbar.AddControl(self.interphp)
        self.toolbar.AddSeparator()
        self.search = scf.SearchFunx(self.toolbar)
        self.toolbar.AddControl(self.search)
        #self.modlabel = wx.StaticText(self.toolbar, -1, " Mode:", (15, 10))
        #self.toolbar.AddControl(self.modlabel)
        mods = ['php.net', 'local', 'autre']
        self.modchoice = wx.Choice(self.toolbar, -1, (100, 50), choices = mods)
        self.toolbar.AddControl(self.modchoice)
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(60, "Quitter", quit_bmp, shortHelp="Quitter", longHelp="Quitter PhPyCli")
        # Tool Bar end

        #Add default page editor, after generation of the toolbar
        self.addEds(e = None, pth = None)

        #Menubar bindings
        #menu file
        self.Bind(wx.EVT_MENU, self.addEds, self.newfitem)
        self.Bind(wx.EVT_MENU, self.openFile, self.dirfitem)
        self.Bind(wx.EVT_MENU, self.saveFile, self.savefitem)
        self.Bind(wx.EVT_MENU, self.saveFileAs, self.savefasitem)
        self.Bind(wx.EVT_MENU, self.execCurf, self.execfitem)
        self.Bind(wx.EVT_MENU, self.onCloseApp, self.quititem)
        #menu edition
        self.Bind(wx.EVT_MENU, self.onPrefs, self.prefsitem)
        #menu help
        self.Bind(wx.EVT_MENU, self.onHelp, self.helpitem)
        self.Bind(wx.EVT_MENU, self.onAbout, self.aboutitem)

        #Toolbar bindings
        self.Bind(wx.EVT_TOOL, lambda pth: self.addEds(pth, None), id=10)
        self.Bind(wx.EVT_TOOL, self.openFile, id=20)
        self.Bind(wx.EVT_TOOL, self.saveFile, id=30)
        self.Bind(wx.EVT_TOOL, self.saveFileAs, id=40)
        self.Bind(wx.EVT_TOOL, self.execCurf, id=50)
        self.Bind(wx.EVT_CHOICE, self.onModChoice, self.modchoice)
        self.Bind(wx.EVT_BUTTON, self.openConsole, self.interphp)
        self.Bind(wx.EVT_TOOL, self.onCloseApp, id=60)
        self.Bind(wx.EVT_TOOL, self.onClearOutput, id=70)

        self.textctrl_input.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.onChangeEd)
        self.textctrl_input.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE,  self.onCloseEd)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("PhPyCli")
        self.SetSize((800, 600))
        favicon = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + '/img/favicon.ico'
        _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(wx.Bitmap(favicon, wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.SetSize((800, 600))
        self.modchoice.SetSelection(int(self.userdatas['search'][0]))
        self.textctrl_output.SetBackgroundColour(litval(self.userdatas['colors'][1]))
        self.textctrl_output.SetForegroundColour(litval(self.userdatas['colors'][0]))
        # statusbar fields
        self.main_window_statusbar.SetStatusWidths([100, -2, -1])
        main_window_statusbar_fields = ["", "", ""]
        for i in range(len(main_window_statusbar_fields)):
            self.main_window_statusbar.SetStatusText(main_window_statusbar_fields[i], i)
        self.progbar = wx.Gauge(self.main_window_statusbar, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        rect = self.main_window_statusbar.GetFieldRect(0)
        self.progbar.SetPosition((rect.x+2, rect.y+2))
        self.progbar.SetSize((rect.width-4, rect.height-4))
        #self.progbar.SetValue(10)

    def __do_layout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        viewport_sizer_output = wx.BoxSizer(wx.HORIZONTAL)
        viewport_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        viewport_input_sizer.Add(self.textctrl_input, 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.viewport_input.SetSizer(viewport_input_sizer)
        viewport_sizer_output.Add(self.textctrl_output, 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.viewport_output.SetSizer(viewport_sizer_output)
        self.viewport.SplitVertically(self.viewport_input, self.viewport_output)
        main_sizer.Add(self.viewport, 5, wx.ALL|wx.EXPAND, 0)
        self.SetSizer(main_sizer)
        self.Layout()
        self.Centre()

    def onModChoice(self, e):
        ch = e.GetString()
        if ch == 'php.net':
            self.userdatas['search'][0] = 0
            self.userdatas['search'][1] = ""
        elif ch == 'local':
            self.userdatas['search'][0] = 1
            self.userdatas['search'][1] = ""
        else:
            self.userdatas['search'][0] = 2
            tmp = self.userdatas['search'][1]
            self.userdatas['search'][1] = tmp

    def gaugeAnimate(self, e):
        self.progbar.Pulse()

    def __del__(self):
        self.timer.Stop()
        if self.process is not None:
            self.process.Detach()
            self.process.CloseOutput()
            self.process = None

    def __output_stdoe(self, i):
        tcs = self.textctrl_output
        e = tcs.GetLastPosition()
        l = len(i)
        s = e - l
        tcs.SetStyle(s, e, wx.TextAttr(litval(self.userdatas['colors'][2]), wx.NullColour))

    def OnIdle(self, evt):
        if self.process is not None:
            self.search.Enable(False)
            self.timer = wx.Timer(self)
            self.timer.Start(100)
            self.toolbar.EnableTool(50, False)
            stream = self.process.GetInputStream()
            estream = self.process.GetErrorStream()

            if stream.CanRead():
                text = stream.read()
                self.textctrl_output.AppendText(text)
            if estream.CanRead():
                etext = estream.read()
                self.textctrl_output.AppendText(etext)
                self.__output_stdoe(str(etext))

    def OnProcessEnded(self, evt):
        self.timer.Stop()
        procdur = time.time() - self.startproc
        self.main_window_statusbar.SetStatusText(str(procdur), 2)
        stream = self.process.GetInputStream()
        estream = self.process.GetErrorStream()

        if stream.CanRead():
            text = stream.read()
            self.textctrl_output.AppendText(text)
        if estream.CanRead():
            etext = estream.read()
            self.textctrl_output.AppendText(etext)
            self.__output_stdoe(str(etext))

        self.process.Destroy()
        self.process = None

        self.toolbar.EnableTool(50, True)
        self.progbar.SetValue(0)
        self.search.Enable(True)

    def addEds(self, e, pth):
        newed = eds.AddEditor(self, -1)
        self.textctrl_input.AddPage(newed, "*new file")

        x = self.textctrl_input.GetPageCount()
        self.textctrl_input.SetSelection(x-1)
        y = self.textctrl_input.GetCurrentPage().GetId()

        if pth is None:
            self.session['curf'] = {'id': newed, 'path': None, 'saved': False, 'toggle': False}
            self.session['editors'][y] = self.session['curf']
            newed.SetText("<?php\n/* New file */\n\n?>\n")
            newed.SetSTCFocus(True)
            newed.SetSelection(21,21)
            #newed.SetCurrentPos(21)
            self.toolbar.EnableTool(30, True)
            self.toolbar.EnableTool(40, True)
            self.toolbar.EnableTool(50, False)
        else:
            try:
                c = open(pth, 'r').read()
                self.session['curf'] = {'id': newed, 'path': pth, 'saved': True, 'toggle': False}
                self.session['editors'][y] = self.session['curf']
                newed.SetText(c)
                self.toolbar.EnableTool(30, False)
                self.toolbar.EnableTool(40, True)
                self.toolbar.EnableTool(50, True)
                self.SetTitle("PhPyCli ~ %s" % self.session['curf']['path'])
                cured = self.textctrl_input.GetCurrentPage()
                curedi = self.textctrl_input.GetPageIndex(cured)
                self.textctrl_input.SetPageText(curedi, os.path.basename(self.session['curf']['path']))
                self.main_window_statusbar.SetStatusText("Fichier ouvert %s" % os.path.basename(self.session['curf']['path']), 1)
            except IOError:
                dlg = wx.MessageDialog(self, 'Ce fichier n\'est pas accessible en lecture!', 'Message', wx.OK|wx.ICON_EXCLAMATION)
                """
                if dlg.ShowModal() == wx.ID_OK:
                    self.openFile()
                """
                dlg.Destroy()

    def openFile(self, e):
        dlg = wx.FileDialog(self, message="Choisissez un fichier", defaultDir="", defaultFile="", wildcard="Fichier PHP (*.php)|*.php", style=wx.OPEN|wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            p = dlg.GetPath()
            self.addEds(0, p)
            '''
            x = self.textctrl_input.GetPageCount()
            if x == 2:
                self.textctrl_input.RemovePage(0)
            '''
        else:
            e.Skip()

    def saveFile(self, e):
        if self.session['curf']['saved']:
            fp = file(self.session['curf']['path'], 'w')
            if fp:
                fp.write(self.session['curf']['id'].GetText())
                fp.close()
                self.session['curf']['toggle'] = True
                self.toolbar.EnableTool(30, False)
                self.toolbar.EnableTool(50, True)
                self.SetTitle("PhPyCli ~ %s" % self.session['curf']['path'])
                cured = self.textctrl_input.GetCurrentPage()
                curedi = self.textctrl_input.GetPageIndex(cured)
                self.textctrl_input.SetPageText(curedi, os.path.basename(self.session['curf']['path']))
                self.main_window_statusbar.SetStatusText("Sauvegardé: %s" % str(os.path.basename(self.session['curf']['path'])), 1)
            else:
                wx.MessageBox('L\'emplacement n\'est pas accessible en écriture!', 'Erreur', wx.OK|wx.ICON_ERROR)
        else:
            self.saveFileAs(self)

    def saveFileAs(self, e):
        dlg = wx.FileDialog(self, message="Sauver le fichier sous ...", defaultDir="", defaultFile="new_file.php", wildcard="Fichier PHP (*.php)|*.php", style=wx.SAVE)
        #dlg.SetFilterIndex(2)
        if dlg.ShowModal() == wx.ID_OK:
            pth = dlg.GetPath()

            fp = file(pth, 'w')
            if fp:
                fp.write(self.session['curf']['id'].GetText())
                fp.close()
                self.session['curf']['path'] = pth
                self.session['curf']['saved'] = True
                self.session['curf']['toggle'] = True
                self.toolbar.EnableTool(30, False)
                self.toolbar.EnableTool(50, True)
                self.SetTitle("PhPyCli ~ %s" % self.session['curf']['path'])
                cured = self.textctrl_input.GetCurrentPage()
                curedi = self.textctrl_input.GetPageIndex(cured)
                self.textctrl_input.SetPageText(curedi, os.path.basename(self.session['curf']['path']))
                self.main_window_statusbar.SetStatusText("Fichier sauvé sous %s" % str(self.session['curf']['path']), 1)
            else:
                fp.close()
                wx.MessageBox('L\'emplacement n\'est pas accessible en écriture!', 'Erreur', wx.OK|wx.ICON_ERROR)

    def execCurf(self, e):
        self.startproc = time.time()
        if self.session['curf']['toggle'] is not True:
            self.saveFile(True)
        self.process = wx.Process(self)
        self.process.Redirect();
        cmd = 'php -f %s' % str(self.session['curf']['path'])
        pid = wx.Execute(cmd, wx.EXEC_ASYNC, self.process)

    def onChangeEd(self, e):
        y = self.textctrl_input.GetCurrentPage().GetId()
        self.session['curf'] = self.session['editors'][y]

        p = '* new file'
        if self.session['curf']['path'] is not None:
            p = self.session['curf']['path']
        if self.session['curf']['toggle']:
            self.toolbar.EnableTool(50, True)

        self.SetTitle("PhPyCli ~ %s" % p)
        self.main_window_statusbar.SetStatusText("Fichier en cours: %s" %  os.path.basename(p), 1)
        self.main_window_statusbar.SetStatusText("", 2)

    def onCloseEd(self, e):
        y = self.textctrl_input.GetCurrentPage().GetId()
        self.session['editors'].pop(y)

        x = self.textctrl_input.GetPageCount()
        if x == 1:
            self.toolbar.EnableTool(30, False)
            self.toolbar.EnableTool(40, False)
            self.toolbar.EnableTool(50, False)

    def openConsole(self, e):
        newconsole = clp.ConsolePhp(self, -1, "")

    def onCloseApp(self, e):
        self.Close()

    def onPrefs(self, e):
        if self.toggleprefs:
            self.toggleprefs = False
            self.getPrefs = ups.UserPrefs(self, -1, "")
        else:
            self.getPrefs.closePrefs(True)
            self.toggleprefs = True


    def onHelp(self, e):
        rp = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + '/datas/help.txt'
        f = open(rp)
        h = f.read()
        f.close()
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, h, "PhPyCli ~ Aide")
        dlg.ShowModal()

    def onAbout(self, e):
        info = wx.AboutDialogInfo()
        info.Name = "PhPyCli"
        info.Version = "Alpha"
        info.Copyright = "(C) OpenSource4Christ"
        info.Description = wordwrap(
            "PhpPyCli est une application open source pour écrire et tester du code php. "
            "Plus d'info dans l'aide...",
            350, wx.ClientDC(self))
        info.WebSite = ("http://steph-hen.github.io/phpycli", "Page de PhPycli sur github")
        info.Developers = ["Stephane"]

        rp = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + '/datas/licence.txt'
        f = open(rp, 'r')
        licence = f.read()
        f.close()

        info.License = wordwrap(licence, 500, wx.ClientDC(self))

        wx.AboutBox(info)

    def onClearOutput(self, e):
        self.textctrl_output.SetValue('')


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    main_window = PhPyCli(None, -1, "")
    app.SetTopWindow(main_window)
    main_window.Show()
    app.MainLoop()
