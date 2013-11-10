#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Instanciation d'une pseudo console avec wxprocess
"""

import sys
import os
import re

import wx


class ConsolePhp(wx.Frame):
    def __init__(self, *args, **kwds):
        """C'est une docstr.
        Hé voui.
        """
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.process = None
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_END_PROCESS, self.OnProcessEnded)

        self.ptncmd = re.compile(r'.*(php --rf [a-zA-Z0-9]+)$')

        self.prompt = wx.StaticText(self, -1, 'Commande:')
        self.cmd = wx.ComboBox(self, -1, choices=["php -a", "php --rf"], style=wx.CB_DROPDOWN)
        self.exBtn = wx.Button(self, -1, 'Exécuter')

        self.out = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)

        self.inp = wx.TextCtrl(self, -1, '', style=wx.TE_PROCESS_ENTER)
        self.sndBtn = wx.Button(self, -1, 'Envoyer')
        self.termBtn = wx.Button(self, -1, 'Fermer')
        self.clearBtn = wx.Button(self, -1, 'Vider')
        self.inp.Enable(False)
        self.sndBtn.Enable(False)
        self.termBtn.Enable(False)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("PhPyCli Console Php")
        favicon = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + '/img/favicon.ico'
        _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(wx.Bitmap(favicon, wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.out.SetMinSize((500, 200))
        self.cmd.SetSelection(0)

    def __do_layout(self):
        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box1.Add(self.prompt, 0, wx.ALIGN_CENTER)
        box1.Add(self.cmd, 1, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, 5)
        box1.Add(self.exBtn, 0)

        self.Bind(wx.EVT_BUTTON, self.OnExecuteBtn, self.exBtn)
        self.Bind(wx.EVT_BUTTON, self.OnSendText, self.sndBtn)
        self.Bind(wx.EVT_BUTTON, self.OnCloseStream, self.termBtn)
        self.Bind(wx.EVT_BUTTON, self.clearOut, self.clearBtn)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSendText, self.inp)

        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(self.inp, 1, wx.ALIGN_CENTER)
        box2.Add(self.sndBtn, 0, wx.LEFT, 5)
        box2.Add(self.termBtn, 0, wx.LEFT, 5)
        box2.Add(self.clearBtn, 0, wx.LEFT, 5)

        console_sizer = wx.BoxSizer(wx.VERTICAL)
        console_sizer.Add(box1, 0, wx.EXPAND|wx.ALL, 10)
        console_sizer.Add(self.out, 1, wx.EXPAND|wx.ALL, 10)
        console_sizer.Add(box2, 0, wx.EXPAND|wx.ALL, 10)

        self.SetSizer(console_sizer)
        console_sizer.Fit(self)
        self.Layout()
        self.Centre()
        self.Show()

    def __del__(self):
        if self.process is not None:
            self.process.Detach()
            self.process.CloseOutput()
            self.process = None


    def OnExecuteBtn(self, e):
        cmd = self.cmd.GetValue()
        chk = False

        if cmd == "php -a":
            chk = True
        else:
            m = re.search(self.ptncmd, cmd)
            if m > 0:
                chk = True
            else:
                m2 = re.search(r'^php --rf$', cmd)
                if m2 > 0:
                    dlg = wx.MessageDialog(self, 'Avec l\'option --rf la commande doit contenir un argument (php --rf <name> (fonctions uniquement))!', 'PhPy', wx.OK|wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                else:
                    chk = True

        if chk:
            self.process = wx.Process(self)
            self.process.Redirect();
            pid = wx.Execute(cmd, wx.EXEC_ASYNC, self.process)

            self.inp.Enable(True)
            self.sndBtn.Enable(True)
            self.termBtn.Enable(True)
            self.cmd.Enable(False)
            self.exBtn.Enable(False)
            self.inp.SetFocus()

    def OnSendText(self, e):
        text = self.inp.GetValue()
        self.inp.SetValue('')
        self.process.GetOutputStream().write(text + '\n')
        self.inp.SetFocus()


    def OnCloseStream(self, evt):
        #print "b4 CloseOutput"
        self.process.CloseOutput()
        #print "after CloseOutput"

    def __output_stdoe(self, i):
        tcs = self.out
        e = tcs.GetLastPosition()
        l = len(i)
        s = e - l
        tcs.SetStyle(s, e, wx.TextAttr((255, 0, 0), wx.NullColour))

    def OnIdle(self, e):
        if self.process is not None:
            stream = self.process.GetInputStream()

            if stream.CanRead():
                text = stream.read()
                self.out.AppendText(text)

            estream = self.process.GetErrorStream()

            if estream.CanRead():
                etext = estream.read()
                self.out.AppendText(etext)
                self.__output_stdoe(str(etext))

    def OnProcessEnded(self, e):
        stream = self.process.GetInputStream()

        if stream.CanRead():
            text = stream.read()
            self.out.AppendText(text)

        self.process.Destroy()
        self.process = None
        self.inp.Enable(False)
        self.sndBtn.Enable(False)
        self.termBtn.Enable(False)
        self.cmd.Enable(True)
        self.exBtn.Enable(True)

    def clearOut(self, e):
        self.out.SetValue('')

    def closeConsole(self):
        self.Close()
