#!/usr/bin/python
# -*- coding: utf-8 -*-

import platform
import ctypes
from ctypes import *


def check_system():
    return platform.system()


def check_twain_dll():
    if check_system() == 'Windows':
        try:
            dll = None
            dll_name = 'twaindsm.dll'
            try:
                dll = ctypes.WinDLL(dll_name)
            except WindowsError:
                dll_name = 'twain_32.dll'
                dll = ctypes.WinDLL(dll_name)
            return dll_name
        except WindowsError as e:
            return 'ошибка'
    else:
        return 'Это не Windows'

