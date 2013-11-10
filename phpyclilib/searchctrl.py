#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cette class instancie un objet wx.SearchCtrl.
C'est un champ de recherche qui se place dans la barre d'outil.
"""

import sys
import os
import re
import json
import webbrowser
import shlex
from subprocess import check_output as chkout

import  wx


class SearchFunx(wx.SearchCtrl):
    maxSearches = 15
    def __init__(self, parent, id=-1, value="", pos=wx.DefaultPosition, size=(150,-1), style= wx.TE_PROCESS_ENTER):
        wx.SearchCtrl.__init__(self, parent, id, value, pos, size, style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuItem, id=1, id2=self.maxSearches)
        self.Bind(wx.EVT_TEXT, self.OnText)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.clear_input)
        self.searches = []
        self.ShowCancelButton(True)

        self.prnt = parent

        self.ptnurl = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

        self.SetDescriptiveText("Hello")

        self.toggleOnText = True

    def OnText(self, e):
        txt = self.GetValue()
        e.Skip()

    def clear_input(self, e):
        self.SetValue("")
        e.Skip()

    def doSearch(self, text):
        try:
            searchopt = int(self.prnt.GetParent().userdatas['search'][0])
            if searchopt == 0:
                url = "http://php.net/results.php?q=%s&l=fr&p=all" % text
                webbrowser.open_new_tab(url)
            elif searchopt == 1:
                searchlocal = chkout(['php', '--rf', str(text)])
                tcs = self.prnt.GetParent().textctrl_output
                tcs.AppendText(searchlocal)
                e = tcs.GetLastPosition()
                l = len(searchlocal)
                s = e - l
                tcs.SetStyle(s, e, wx.TextAttr((0,0,0), (255,255,255)))
            elif searchopt == 2:
                datasearchcmd = self.prnt.GetParent().userdatas['search'][1]
                if datasearchcmd == "":
                    dlg = wx.MessageDialog(self, 'Aucune valeur n\' été définie pour ce mode! Voulez-vous la définir?', 'PhPy', wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
                    if dlg.ShowModal() == wx.ID_OK:
                        self.prnt.GetParent().onPrefs(True)
                    dlg.Destroy()
                else:
                    url = datasearchcmd.replace("<name>", str(text))
                    testcmd = re.match(self.ptnurl, url)
                    if testcmd > 0:
                        webbrowser.open_new_tab(url)
                    else:
                        ncmd = datasearchcmd.replace("<name>", str(text))
                        execcmd = chkout(shlex.split(ncmd))
                        self.prnt.GetParent().textctrl_output.AppendText(execcmd)
                        e = self.prnt.GetParent().textctrl_output.GetLastPosition()
                        l = len(execcmd)
                        s = e - l
                        self.prnt.GetParent().textctrl_output.SetStyle(s, e, wx.TextAttr((0,0,0), (255,255,255)))
        except OSError as err:
            wx.MessageBox('Impossible d\'ouvrir un navigateur... Infos erreur:\n\Numéro: %s\Fichier: %s\Message %s' % (err.erno, err.filename, err.strerror), 'Erreur', wx.OK|wx.ICON_ERROR)

    def OnTextEntered(self, e):
        text = self.GetValue()
        if text != "":
            self.searches.append(text)
            self.SetMenu(self.MakeMenu())
        testsearch = self.doSearch(text)

    def OnMenuItem(self, e):
        text = self.searches[e.GetId()-1]
        pos = self.prnt.GetParent().session['curf']['id'].GetCurrentPos()
        self.prnt.GetParent().session['curf']['id'].InsertText(pos, text)

    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, "Recherches:")
        item.Enable(False)
        for idx, txt in enumerate(self.searches):
            menu.Append(1+idx, txt)
        return menu

