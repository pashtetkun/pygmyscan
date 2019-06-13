#!/usr/bin/python
# -*- coding: utf-8 -*-

import platform
import ctypes
from ctypes import *
from ctypes import wintypes
from twainlib.constants import *


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
        print('Error getting address1')

    windll.kernel32.CloseHandle(handle)
    return address


class Application():
    def __init__(self,
                 MajorNum=1,
                 MinorNum=0,
                 Language=TWLG_USA,
                 Country=TWCY_USA,
                 Info="",
                 ProductName="TWAIN Python Interface",
                 ProtocolMajor=TWON_PROTOCOLMAJOR,
                 ProtocolMinor=TWON_PROTOCOLMINOR,
                 SupportedGroups=DG_IMAGE | DG_CONTROL,
                 Manufacturer="Tsibizov Pavel",
                 ProductFamily="TWAIN Python Interface"):
        self._app_id = TW_IDENTITY(Version=TW_VERSION(MajorNum=MajorNum,
                                                      MinorNum=MinorNum,
                                                      Language=Language,
                                                      Country=Country,
                                                      Info=Info.encode('utf8')),
                                   ProtocolMajor=ProtocolMajor,
                                   ProtocolMinor=ProtocolMinor,
                                   SupportedGroups=SupportedGroups,
                                   Manufacturer=Manufacturer.encode('utf8'),
                                   ProductFamily=ProductFamily.encode('utf8'),
                                   ProductName=ProductName.encode('utf8'))

    def load_source_manager(self):
        '''
        1 -> 2
        :return: DSM_Entry
        '''
        try:
            dll = windll.LoadLibrary('twain_32.dll')
            #_GetProcAddress = windll.kernel32.GetProcAddress
            dsm_entry = dll.DSM_Entry
            address = hex(c_void_p.from_buffer(dsm_entry).value)
            # address = func_address('twain_32.dll', 'DSM_Entry')
            # p = POINTER(self.dsm_entry)
            x = byref(dsm_entry)
            return dsm_entry
        except Exception as e:
            return None


class SourceManager():
    """
        This object represents Data Source Manager
    """
    def __init__(self,
                 parent_window=None,
                 dll_name=None):
        self._parent_window = parent_window
        twain_dll_info = get_twain32_dll()
        twain_dll = twain_dll_info[1]
        if not twain_dll:
            return

        self.dsm_entry = None
        self._app_id = None
        self._hwnd = None
        self.sources_dict = {}
        self.opened_source = None

        try:
            #get function DSM_Entry()
            #self.dsm_entry = twain_dll['DSM_Entry']
            self.dsm_entry = twain_dll.DSM_Entry
            address = hex(c_void_p.from_buffer(self.dsm_entry).value)
            #address = func_address('twain_32.dll', 'DSM_Entry')
            #p = POINTER(self.dsm_entry)
            x = byref(self.dsm_entry)

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
        self._hwnd = parent_window.winfo_id()

    def set_app_info(self,
                     MajorNum=1,
                     MinorNum=0,
                     Language=TWLG_USA,
                     Country=TWCY_USA,
                     Info="",
                     ProductName="TWAIN Python Interface",
                     ProtocolMajor=TWON_PROTOCOLMAJOR,
                     ProtocolMinor=TWON_PROTOCOLMINOR,
                     SupportedGroups=DG_IMAGE | DG_CONTROL,
                     Manufacturer="Kevin Gill",
                     ProductFamily="TWAIN Python Interface"):
        self._app_id = TW_IDENTITY(Version=TW_VERSION(MajorNum=MajorNum,
                                                      MinorNum=MinorNum,
                                                      Language=Language,
                                                      Country=Country,
                                                      Info=Info.encode('utf8')),
                                   ProtocolMajor=ProtocolMajor,
                                   ProtocolMinor=ProtocolMinor,
                                   SupportedGroups=SupportedGroups,
                                   Manufacturer=Manufacturer.encode('utf8'),
                                   ProductFamily=ProductFamily.encode('utf8'),
                                   ProductName=ProductName.encode('utf8'))

    def load_dsm(self, dll_name=None):
        '''
        1 -> 2
        :return: DSM_Entry
        '''
        twain_dll_info = get_twain32_dll()
        twain_dll = twain_dll_info[1]
        if not twain_dll:
            return

    def get_sources(self):
        # open Data Source Manager(connection)
        returnCode = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_PARENT, MSG_OPENDSM,
                                    byref(c_void_p(self._hwnd)))
        if returnCode != TWRC_SUCCESS:
            return

        # search sources
        sources = []
        source_info = TW_IDENTITY()
        rc = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_IDENTITY, MSG_GETFIRST, byref(source_info))
        if rc == TWRC_FAILURE:  # 1 error
            status = TW_STATUS()
            self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_STATUS, MSG_GET, byref(status))
            if status.ConditionCode == TWCC_NODS:  # no Sources found
                print('not sources!!!')
            return sources
        sources.append((source_info.Id,
                       source_info.ProductName.decode("utf-8"),
                       str(source_info.ProtocolMajor)+"."+str(source_info.ProtocolMinor)))
        self.sources_dict[source_info.Id] = source_info

        while 1:
            source_info = TW_IDENTITY()
            rc = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_IDENTITY, MSG_GETNEXT, byref(source_info))
            if rc == TWRC_ENDOFLIST:
                break
            sources.append((source_info.Id,
                           source_info.ProductName.decode("utf-8"),
                           str(source_info.ProtocolMajor) + "." + str(source_info.ProtocolMinor)))
            self.sources_dict[source_info.Id] = source_info

        return sources

    def open_source(self, source_id):
        source_info = self.sources_dict[source_id]
        rc = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_IDENTITY, MSG_OPENDS, byref(source_info))
        if rc != TWRC_SUCCESS:
            return
        self.opened_source = source_info

        #get_image
        self.xfer_image_natively()

    def xfer_image_natively(self):
        """Perform a 'Native' form transfer of the image.

        When successful, this routine returns two values,
        an image handle and a count of the number of images
        remaining in the source.

        If remaining number of images is zero Source will
        transition to state 5, otherwise it stays in state 6
        in which case you should call
        :meth:`xfer_image_natively` again.

        Valid states: 6
        """
        hbitmap = c_void_p()
        rv = self.dsm_entry(self._app_id, self.opened_source, DG_IMAGE,
                        DAT_IMAGENATIVEXFER,
                        MSG_GET,
                        byref(hbitmap))
        #rv, hbitmap = self._get_native_image()
        #more = self._end_xfer()
        if rv == TWRC_CANCEL:
            raise excDSTransferCancelled
        #return hbitmap.value, more

    def close_source(self, source_id):
        pass