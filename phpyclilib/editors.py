#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Ajout dynamique d'editeurs.
"""

import sys
import os
import json
import re

import  wx
import  wx.stc  as  stc

from loadjson import loadJson


class AddEditor(stc.StyledTextCtrl):
    """Objet Editeur.
    Les éditeurs sont enfants de la classe stc.StyledTextCtrl.
    Ils sont ajoutés au NoteBook AUI de la fenêtre principale
    """
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        self.prnt = parent
        self.toggleAutocomp = True
        self.charr = []
        self.phpf = []
        self.chkbaksp = False
        self.ptn = re.compile(r'.*([a-zA-Z0-9]+\w*)$')
        self.ptab = re.compile(r'^(\t+)')

        self.phpfunxlist = loadJson('/datas/funx_php.json')

        #Editor
        self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
        self.SetEdgeColumn(78)
        self.SetWrapMode(1)
        self.SetWrapVisualFlags(1)

        #ZOOM & autres
        self.CmdKeyAssign(ord('B'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord('N'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)
        self.CmdKeyAssign(ord('W'), stc.STC_SCMOD_CTRL, stc.STC_CMD_WORDRIGHT)
        self.CmdKeyAssign(ord('W'), stc.STC_SCMOD_CTRL | stc.STC_SCMOD_SHIFT, stc.STC_CMD_WORDLEFT)

        #FOLDING & Margin
        #self.SetKeyWords(4, " ".join(PHPKEYWORDS))
        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetProperty("fold", "1")
        self.SetProperty("fold.html", "1")
        self.SetMargins(2,2)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(1, 15)
        self.SetMarginWidth(2, 12)

        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,   stc.STC_MARK_BOXMINUS,        "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,       stc.STC_MARK_BOXPLUS,          "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,             "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,   stc.STC_MARK_LCORNER,          "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,         "white", "#808080")

        #INDENTATION
        self.SetIndent(4)
        self.SetIndentationGuides(True)
        self.SetBackSpaceUnIndents(True)
        self.SetTabIndents(True)
        self.SetTabWidth(4)
        self.SetUseTabs(True)
        self.SetHighlightGuide(0)

        #HIGHLIGHT & others
        self.SetStyleBits(7)
        self.SetViewWhiteSpace(False)
        self.SetCaretWidth(1)
        #self.SetControlCharSymbol(0)
        self.SetCaretLineVisible(True)
        self.SetCaretLineBack(wx.Colour(250, 254, 255))
        self.SetCaretForeground("#1A1A1A")

        self.SetLexer(stc.STC_LEX_HTML)
        lx = '/datas/lex_php.json'
        f = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + lx
        fo = open(f, 'r')
        fr = fo.read()
        fo.close()
        datas = json.loads(fr)

        for i in datas['styles']:
            self.StyleSetSpec(eval(i['id']), str(i['val']))

        for i in datas['keywords']:
            self.SetKeyWords(int(i['index']), str(i['value']))

        self.Bind(stc.EVT_STC_UPDATEUI, self.uiupdate)
        self.Bind(wx.EVT_KEY_DOWN, self.kpressed)
        self.Bind(stc.EVT_STC_CHARADDED, self.charadded)
        self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.stc.EVT_STC_AUTOCOMP_SELECTION, self.autocomp)

    def OnMarginClick(self, evt):
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)

    def FoldAll(self):
        lineCount = self.GetLineCount()
        expanding = True

        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1

    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1

        return line
        #self.AutoCompSetDropRestOfWord(True)

    def autocomp(self, e):
        self.toggleAutocomp = False
        o = e.GetText()
        x = len(o)
        y = len(self.charr)

        a = self.GetCurrentPos()
        b = a - y
        self.SetTargetStart(b)
        self.SetTargetEnd(a)
        self.ReplaceTarget(o)
        self.SetSelectionStart(a+x-y)
        self.SetSelectionEnd(a+x-y)
        self.toggleAutocomp = True
        if self.AutoCompActive():
            self.AutoCompCancel()

    def uiupdate(self, e):
        ''' Actions lors de la mise à jour du champ inputctrl '''
        # Gestion de la marge de gauche pour s'adapter en fonction de la numérotation
        nmb = self.GetLineCount()
        if nmb > 9 and nmb < 100:
            self.SetMarginWidth(1, 20)
        elif nmb > 99 and nmb < 1000:
            self.SetMarginWidth(1, 27)
        elif nmb > 999 and nmb < 10000:
            self.SetMarginWidth(1, 35)
        else:
            self.SetMarginWidth(1, 15)

        # Autocompletion
        if self.toggleAutocomp:
            k = self.GetCurrentPos()
            c = ''
            fp = ''
            lp = k
            self.phpf = []
            if k > 0:
                c = self.GetCharAt(k - 1)
                if self.chkbaksp:
                    if len(self.charr) > 1:
                        self.charr.pop()
                    elif len(self.charr) == 1:
                        self.charr = []
                        self.phpf = []
                    self.chkbaksp = False
                elif c != 32 and c != 10 and c != 8:
                    self.charr.append(chr(c))
                else:
                    self.charr = []
                if len(self.charr) > 3:
                    x = "".join(self.charr)
                    m = re.match(self.ptn, x)
                    if m:
                        y = self.phpfunxlist[x[0]]
                        for i in y:
                            n = re.match(x, i)
                            if n:
                                self.phpf.append(i)

                        self.AutoCompShow(0, " ".join(self.phpf))
                        self.AutoCompSelect(x)
            e.Skip()

    '''
    def kpressed(self, e):
        # Fenêtre de recherche rapide de fonctions (Ctrl + Espace)
        k = e.GetKeyCode()
        if k == 8:
            self.chkbaksp = True
        elif k == 32 and e.CmdDown():
            s = ''
            cs = self.GetSelectedText()
            if cs:
                s = cs
            shSel = InsertFunx(self.prnt, -1, s)
        elif k == ord("E") and e.CmdDown():
            self.prnt.execcurf(e)

        self.prnt.toolbar.EnableTool(30, True)
        self.prnt.ppc_sess['curf']['toggle'] = False
        self.prnt.SetTitle("PhPyCli ~ *%s" % self.prnt.ppc_sess['curf']['path'])
        #self.prnt.statusbar.SetStatusText("Input", 0)

        e.Skip()
    '''

    def charadded(self, e): # Inutilisée...
        k = e.Key
        x = 0
        if k == ord('\n'):
            #cur_pos = self.GetCurrentPos()
            #cur_line = self.GetCurLine()
            cur_line_order = self.GetCurrentLine()
            prev_line = cur_line_order - 1
            m = re.search(self.ptab, self.GetLine(prev_line))
            if m:
                x = len(m.group(0))

            if self.GetLine(prev_line)[-2] == '{':
                x = x + 1
            #if cur_line[] == '}':
            if x > 0:
                for i in range(x):
                    self.AddText("\t")
        elif k == 125:
            print k
            cur_line_order = self.GetCurrentLine()
            prev_line = cur_line_order - 1
            m = re.search(self.ptab, self.GetLine(cur_line_order))
            if m:
                x = len(m.group(0))
            if x > 0:
                y = self.GetCurLine()
                #y[0].replace('\t', '')

                a = self.PositionFromLine(cur_line_order)
                b = self.GetCurrentPos()
                self.SetTargetStart(a)
                self.SetTargetEnd(a+1)
                #self.AddText("}")
                #self.SetSelectionStart(a)
                #self.SetSelectionEnd(a)
                nbt = ''
                if x > 0:
                    for i in range(x):
                        nbt += "\t"
                self.ReplaceTarget('%s\n' % nbt)
                #self.SetCurrentPos(prev_line)

        e.Skip()

    def kpressed(self, e):
        k = e.GetKeyCode()
        if k == ord("E") and e.CmdDown():
            self.prnt.execCurf(e)
        if k == ord("S") and e.CmdDown():
            self.prnt.saveFile(e)
        if k == ord("I") and e.CmdDown():
            self.prnt.onClearOutput(e)

        self.prnt.toolbar.EnableTool(30, True)
        self.prnt.session['curf']['toggle'] = False

        if self.prnt.session['curf']['path'] is not None:
            self.prnt.SetTitle("PhPyCli ~ *%s" % self.prnt.session['curf']['path'])
            cured = self.prnt.textctrl_input.GetCurrentPage()
            curedi = self.prnt.textctrl_input.GetPageIndex(cured)
            self.prnt.textctrl_input.SetPageText(curedi, "* %s" %  os.path.basename(self.prnt.session['curf']['path']))
            #self.prnt.statusbar.SetStatusText("Input", 0)
        e.Skip()
