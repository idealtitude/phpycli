#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gestions des préférences utilisateurs
"""

import sys
import os
import json

from ast import literal_eval as litval

import wx
import  wx.lib.colourselect as  csel
import wx.richtext as rt

from loadjson import loadJson


class UserPrefs(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)

        self.myprefs = loadJson('/datas/user_prefs.json')
        self.prnt = parent

        self.search_radiobox = wx.RadioBox(self, -1, "Sources pour la recherche", choices=["php.net", "local", "autre"], majorDimension=0, style=wx.RA_SPECIFY_ROWS)
        self.altsearch = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER)
        self.defopts = wx.StaticText(self, -1, "php.net: requête doc en ligne, local: commande php option --rf, autre: opération customisée")
        self.rtc = rt.RichTextCtrl(self, -1, size=(-1, 60), style=wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER);
        self.searchopts_sizer_staticbox = wx.StaticBox(self, -1, "Options du champ de recherche")

        self.colorpickers = wx.FlexGridSizer(1, 2)
        self.buttonRefs = []
        butsize = (30, 30)
        buttonData = [
            ("Couleur du texte", litval(self.myprefs['colors'][0]), butsize, ""),
            ("Couleur de fond", litval(self.myprefs['colors'][1]),   butsize, ""),
            ("Couleur des erreurs", litval(self.myprefs['colors'][2]), butsize, "")
            ]

        self.outcolors_sizer_staticbox = wx.StaticBox(self, -1, "Couleurs du champ de sortie")
        self.hr = wx.StaticLine(self, -1)
        self.valid_but = wx.Button(self, -1, "Valider")
        self.reset_but = wx.Button(self, -1, "Reset")
        self.cancel_but = wx.Button(self, -1, "Fermer")
        for name, color, size, label in buttonData:
            b = csel.ColourSelect(self, -1, label, color, size = size)

            b.Bind(csel.EVT_COLOURSELECT, self.onColorSel)
            self.buttonRefs.append((name, b))  # store reference to button

            self.colorpickers.AddMany([
                (wx.StaticText(self, -1, name), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
                (b, 0, wx.ALL, 3),
                ])

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_RADIOBOX, self.onRadioBox, self.search_radiobox)
        self.Bind(wx.EVT_TEXT_ENTER, self.altsearchEnter, self.altsearch)
        self.Bind(wx.EVT_BUTTON, self.onValidPrefs, self.valid_but)
        self.Bind(wx.EVT_BUTTON, self.resetPrefs, self.reset_but)
        self.Bind(wx.EVT_BUTTON, self.closePrefs, self.cancel_but)

    def __set_properties(self):
        self.SetTitle("PhPyCli Préferences")
        favicon = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + '/img/favicon.ico'
        _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(wx.Bitmap(favicon, wx.BITMAP_TYPE_ANY))

        getsearch = int(self.myprefs['search'][0])
        self.search_radiobox.SetSelection(getsearch)
        if getsearch == 2:
            self.altsearch.SetValue(str(self.myprefs['search'][1]))
            self.altsearch.Enable(True)
        else:
            self.altsearch.Enable(False)

        self.altsearch.SetMinSize((450, 31))
        helppath = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + '/datas/help_prefs.xml'
        self.rtc.LoadFile(helppath, 1)

    def __do_layout(self):
        helppath = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + '/datas/help_prefs.xml'
        #self.rtc.Freeze()
        #self.rtc.WriteText('')
        #self.rtc.Thaw()
        rt.RichTextBuffer.AddHandler(rt.RichTextXMLHandler())
        self.rtc.LoadFile(helppath, 2)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        valid_sizer = wx.BoxSizer(wx.VERTICAL)
        buts_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.outcolors_sizer_staticbox.Lower()
        outcolors_sizer = wx.StaticBoxSizer(self.outcolors_sizer_staticbox, wx.HORIZONTAL)
        self.searchopts_sizer_staticbox.Lower()
        searchopts_sizer = wx.StaticBoxSizer(self.searchopts_sizer_staticbox, wx.VERTICAL)
        searchopts_sizer.Add(self.defopts, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        searchopts_sizer.Add(self.search_radiobox, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        searchopts_sizer.Add(self.altsearch, 0, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        searchopts_sizer.Add(self.rtc, 0, wx.ALL|wx.EXPAND, 5)
        main_sizer.Add(searchopts_sizer, 0, wx.ALL|wx.EXPAND, 5)
        outcolors_sizer.Add(self.colorpickers, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        main_sizer.Add(outcolors_sizer, 0, wx.ALL|wx.EXPAND, 5)
        valid_sizer.Add(self.hr, 0, wx.ALL|wx.EXPAND, 5)
        buts_sizer.Add(self.valid_but, 1, wx.ALL|wx.ADJUST_MINSIZE, 5)
        buts_sizer.Add(self.reset_but, 1, wx.ALL|wx.ADJUST_MINSIZE, 5)
        buts_sizer.Add(self.cancel_but, 1, wx.ALL|wx.ADJUST_MINSIZE, 5)
        valid_sizer.Add(buts_sizer, 1, wx.EXPAND, 0)
        main_sizer.Add(valid_sizer, 1, wx.EXPAND, 0)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()
        self.Centre()
        self.Show()

    def onRadioBox(self, e):
        if e.GetInt() == 2:
            self.altsearch.Enable(True)
        else:
            self.altsearch.Enable(False)


    def altsearchEnter(self, e):
        print "Event handler `altsearchEnter' not implemented!"
        e.Skip()

    def onColorSel(self, e):
        print("Colour selected: %s" % str(e.GetValue()))

    def onValidPrefs(self, e):
        search = self.search_radiobox.GetSelection()
        newprefs = {'search' : [str(search), ''], 'colors' : []}

        if search == 2:
            newprefs['search'][1] = str(self.altsearch.GetValue())

        colors = []
        for i in self.buttonRefs:
            newprefs['colors'].append(str(i[1].GetValue()))

        dlg = wx.MessageDialog(self, 'Enregistrer les modifications?', 'PhPy', wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
        #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
        if dlg.ShowModal() == wx.ID_OK:
            newsstr = json.dumps(newprefs)
            p = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + '/datas/user_prefs.json'
            f = open(p, 'w')
            f.write(newsstr)
            f.close()

            dlg2 = wx.MessageDialog(self, 'Les préférences ont bien été enregistrées!', 'PhPy', wx.OK|wx.ICON_INFORMATION)
            dlg2.ShowModal()
            dlg2.Destroy()

            #self.Close()

        dlg.Destroy()

    def __del__(self):
        self.prnt.toggleprefs = True

    def resetPrefs(self, e):
        #self.buttonRefs[0][1].SetForegroundColour(wx.Colour(0, 0, 0))
        e.Skip()
        pass

    def closePrefs(self, e):
        self.prnt.toggleprefs = True
        self.Close()

