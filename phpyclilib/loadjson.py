#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Petite fonction pour charger le contenu de différents fichiers json
"""

import sys
import os
import json

def loadJson(path):
    f = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]))) + path
    fo = open(f, 'r')
    fr = fo.read()
    datas = json.loads(fr)
    fo.close()

    return datas

