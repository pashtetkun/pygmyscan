#!/usr/bin/python
# -*- coding: utf-8 -*-

import platform
import ctypes
from ctypes import *
from ctypes import wintypes
from twainlib import *
from twainlib import _exc_mapping


def check_system():
    return platform.system()


def get_twain32_dll():
    if check_system() == 'Windows':
        try:
            dll_name = 'twain_32.dll'
            #dll_name = 'TWAINDSM.dll'
            dll = windll.LoadLibrary(dll_name)
            _GetProcAddress = windll.kernel32.GetProcAddress
            return dll_name, dll
        except WindowsError as e:
            return 'ошибка', None
    else:
        return 'Это не Windows', None


def func_address(dll_name, function_name):
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.GetProcAddress.restype = ctypes.c_void_p
    kernel32.GetProcAddress.argtypes = (wintypes.HMODULE, wintypes.LPCSTR)
    LoadLibAddy = kernel32.GetProcAddress(kernel32._handle, b'DSM_Entry')

    _GetModuleHandleA = kernel32.GetModuleHandleA
    _GetModuleHandleA.restype = POINTER(c_void_p)

    _GetProcAddress = kernel32.GetProcAddress
    _GetProcAddress.restype = c_void_p

    handle = _GetModuleHandleA(dll_name)
    if handle is None:
        print('Error getting handle')

    address = _GetProcAddress(handle, function_name)
    if address is None:
        print('Error getting address')

    windll.kernel32.CloseHandle(handle)
    return address


class DataSourceManager(object):
    def __init__(self,
                 parent_window=None,
                 MajorNum=1,
                 MinorNum=0,
                 Language=TWLG_RUSSIAN,
                 Country=TWCY_RUSSIA,
                 Info="",
                 ProductName="TWAIN Python Interface",
                 ProtocolMajor=TWON_PROTOCOLMAJOR,
                 ProtocolMinor=TWON_PROTOCOLMINOR,
                 SupportedGroups=DG_IMAGE | DG_CONTROL,
                 Manufacturer="Tsibizov Pavel",
                 ProductFamily="TWAIN Python Interface",
                 dsm_name=None):
        self._parent_window = parent_window
        twain_dll_info = get_twain32_dll()
        twain_dll = twain_dll_info[1]
        if not twain_dll:
            return

        try:
            #get function DSM_Entry()
            #self.dsm_entry = twain_dll['DSM_Entry']
            self.dsm_entry = twain_dll.DSM_Entry
            address = hex(c_void_p.from_buffer(self.dsm_entry).value)
            #address = func_address('twain_32.dll', 'DSM_Entry')
            #p = POINTER(self.dsm_entry)

            pass
        except AttributeError as e:
            pass

        self.dsm_entry.restype = c_uint16
        self.dsm_entry.argtypes = (POINTER(TW_IDENTITY),
                                POINTER(TW_IDENTITY),
                                c_uint32,
                                c_uint16,
                                c_uint16,
                                c_void_p)

        self._app_id = TW_IDENTITY(Version=TW_VERSION(MajorNum=MajorNum,
                                                      MinorNum=MinorNum,
                                                      Language=Language,
                                                      Country=Country,
                                                      Info=Info.encode('utf8')),
                                   ProtocolMajor=ProtocolMajor,
                                   ProtocolMinor=ProtocolMinor,
                                   SupportedGroups=SupportedGroups | DF_APP2,
                                   Manufacturer=Manufacturer.encode('utf8'),
                                   ProductFamily=ProductFamily.encode('utf8'),
                                   ProductName=ProductName.encode('utf8'))
        self._hwnd = parent_window.winfo_id()
        #open Data Source Manager(connection)
        returnCode = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_PARENT, MSG_OPENDSM, byref(c_void_p(self._hwnd)))
        if returnCode != TWRC_SUCCESS:
            return

        #search sources
        ds_id = TW_IDENTITY()
        rc = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_IDENTITY, MSG_GETFIRST, byref(ds_id))
        if rc == TWRC_FAILURE: #1 error
            status = TW_STATUS()
            self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_STATUS, MSG_GET, byref(status))
            if status.ConditionCode == TWCC_NODS: #no Sources found
                print('not sources!!!')
            return

        pass

    def _call(self, dest_id, dg, dat, msg, buf, expected_returns=()):
        rv = self.dsm_entry(self._app_id, dest_id, dg, dat, msg, buf)
        if rv == TWRC_SUCCESS or rv in expected_returns:
            return rv
        elif rv == TWRC_FAILURE:
            status = TW_STATUS()
            rv = self.dsm_entry(self._app_id,
                             dest_id,
                             DG_CONTROL,
                             DAT_STATUS,
                             MSG_GET,
                             byref(status))
            if rv != TWRC_SUCCESS:
                raise Exception('DG_CONTROL DAT_STATUS MSG_GET returned non success code, rv = %d' % rv)
            code = status.ConditionCode
            exc = _exc_mapping.get(code,
                                   excTWCC_UNKNOWN("ConditionCode = %d" % code))
            raise exc
        else:
            raise Exception('Unexpected result: %d' % rv)

    def get_source_list(self):
        names = []
        ds_id = TW_IDENTITY()
        try:
            rv = self._call(None,
                            DG_CONTROL,
                            DAT_IDENTITY,
                            MSG_GETFIRST,
                            byref(ds_id),
                            (TWRC_SUCCESS, TWRC_ENDOFLIST))
            pass
        except excTWCC_NODS:
            # there are no data sources
            return names

        while rv != TWRC_ENDOFLIST:
            names.append(self._decode(ds_id.ProductName))
            rv = self._call(None,
                            DG_CONTROL,
                            DAT_IDENTITY,
                            MSG_GETNEXT,
                            byref(ds_id),
                            (TWRC_SUCCESS, TWRC_ENDOFLIST))
        return names