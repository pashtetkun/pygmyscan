#!/usr/bin/python
# -*- coding: utf-8 -*-

import platform
import ctypes
from ctypes import *
from ctypes import wintypes
from twainlib.constants import *


class Application():
    def __init__(self, parent_window=None):
        self._app_id = None
        self.dll = None
        self.dsm_entry = None
        self._parent_window = parent_window
        self._hwnd = parent_window.winfo_id()
        self.set_app_info()
        self.source_manager = None

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
        :return: Source Manager
        '''
        try:
            self.dll = windll.LoadLibrary('twain_32.dll')
            #_GetProcAddress = windll.kernel32.GetProcAddress
            self.dsm_entry = self.dll.DSM_Entry
            address = hex(c_void_p.from_buffer(self.dsm_entry).value)
            # address = func_address('twain_32.dll', 'DSM_Entry')
            # p = POINTER(self.dsm_entry)
            # x = byref(self.dsm_entry)
            self.dsm_entry.restype = c_uint16
            self.dsm_entry.argtypes = (POINTER(TW_IDENTITY),
                                       POINTER(TW_IDENTITY),
                                       c_uint32,
                                       c_uint16,
                                       c_uint16,
                                       c_void_p)
            #return self.dsm_entry
            self.source_manager = SourceManager(self)
            return self.source_manager
        except Exception as e:
            return None

    def unload_source_manager(self):
        '''
        2 --> 1
        :return:
        '''
        try:
            del self.dll
            self.source_manager = None
        except Exception as e:
            print(e)


class SourceManager():
    """
        This object represents Data Source Manager
    """
    def __init__(self, application):

        self._app_id = application._app_id
        self.dsm_entry = application.dsm_entry
        self._hwnd = application._hwnd
        self.sources_dict = {}
        self.opened_source = None

    def open(self):
        '''
        2 -> 3 Open Source Manager
        :return:
        '''
        returnCode = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_PARENT, MSG_OPENDSM,
                                    byref(c_void_p(self._hwnd)))
        if returnCode != TWRC_SUCCESS:
            return

    def close(self):
        '''
        3 -> 2 Close Source Manager
        :return:
        '''
        returnCode = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_PARENT, MSG_CLOSEDSM,
                                    byref(c_void_p(self._hwnd)))
        if returnCode != TWRC_SUCCESS:
            return

    def get_sources(self):
        '''
        3
        :return:
        '''
        sources = []
        source_info = TW_IDENTITY()
        rc = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_IDENTITY, MSG_GETFIRST, byref(source_info))
        if rc == TWRC_FAILURE:  # 1 error
            cc = self.get_failure_condition_code(None)
            if cc == TWCC_NODS:  # no Sources found
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
        '''
        3 --> 4 open Source
        :param source_id:
        :return: Source
        '''
        source_info = self.sources_dict[source_id]
        rc = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_IDENTITY, MSG_OPENDS, byref(source_info))
        if rc != TWRC_SUCCESS:
            return
        self.opened_source = source_info
        return Source(self)
        #get_image
        #self.xfer_image_natively()

    def close_source(self, source_id):
        '''
        4 --> 3 close Source
        :param source_id:
        :return:
        '''
        source_info = self.sources_dict[source_id]
        rc = self.dsm_entry(self._app_id, None, DG_CONTROL, DAT_IDENTITY, MSG_CLOSEDS, byref(source_info))
        if rc != TWRC_SUCCESS:
            return
        self.opened_source = None

    def get_failure_condition_code(self, source):
        status = TW_STATUS()
        self.dsm_entry(self._app_id, source, DG_CONTROL, DAT_STATUS, MSG_GET, byref(status))
        return status.ConditionCode


class Source():
    def __init__(self, source_manager):
        self._app_id = source_manager._app_id
        self.dsm_entry = source_manager.dsm_entry
        self._hwnd = source_manager._hwnd
        self._source_id = source_manager.opened_source

    def enable(self):
        '''
        4 --> 5 enable Source
        :return:
        '''
        ui = TW_USERINTERFACE(ShowUI=False, ModalUI=False, hParent=self._hwnd)
        rc = self.dsm_entry(self._app_id, self._source_id, DG_CONTROL, DAT_USERINTERFACE, MSG_ENABLEDS, byref(ui))
        if rc != TWRC_SUCCESS:
            return

    def disable(self):
        '''
        5 --> 4 disable Source
        :return:
        '''
        ui = TW_USERINTERFACE(ShowUI=False, ModalUI=False, hParent=self._hwnd)
        rc = self.dsm_entry(self._app_id, self._source_id, DG_CONTROL, DAT_USERINTERFACE, MSG_DISABLEDS, byref(ui))
        if rc == TWRC_SUCCESS:
            return
        if rc == TWRC_FAILURE:
            cc = self.get_failure_condition_code()
            if cc == TWCC_SEQERROR:
                pass
        pass

    def get_failure_condition_code(self):
        status = TW_STATUS()
        self.dsm_entry(self._app_id, self._source_id, DG_CONTROL, DAT_STATUS, MSG_GET, byref(status))
        return status.ConditionCode

    def _process_event(self, msg_ref):
        event = TW_EVENT(cast(msg_ref, c_void_p), 0)
        rv = self.dsm_entry(self._app_id,
                            self._source_id,
                            DG_CONTROL,
                            DAT_EVENT,
                            MSG_PROCESSEVENT,
                            byref(event))
        if event.TWMessage == MSG_XFERREADY:
            self._state = 'ready'
        return rv, event.TWMessage

    def _modal_loop(self, callback=None):
        done = False
        msg = MSG()
        while not done:
            if not _GetMessage(byref(msg), 0, 0, 0):
                break
            rc, event = self._process_event(byref(msg))
            #if callback:
            self.callback(event)
            if event in (MSG_XFERREADY, MSG_CLOSEDSREQ):
                done = True
            if rc == TWRC_NOTDSEVENT:
                #_TranslateMessage(byref(msg))
                #_DispatchMessage(byref(msg))
                x = 1

    def callback(self, event):
        if event == MSG_XFERREADY:
            rv, handle = self.get_native_image()
            image = _Image(handle)
            image.save("C:/1/test2.bmp")

    def get_native_image(self):
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
        rv = self.dsm_entry(self._app_id, self._source_id, DG_IMAGE,
                        DAT_IMAGENATIVEXFER,
                        MSG_GET,
                        byref(hbitmap))
        #rv, hbitmap = self._get_native_image()
        #more = self._end_xfer()
        if rv == TWRC_CANCEL:
            raise excDSTransferCancelled
        return rv, hbitmap


def _win_check(result, func, args):
    if func is _GlobalFree:
        if result:
            raise WinError()
        return None
    elif func is _GlobalUnlock:
        if not result and GetLastError() != 0:
            raise WinError()
        return result
    elif func is _GetMessage:
        if result == -1:
            raise WinError()
        return result
    elif func is _TranslateMessage or func is _DispatchMessage:
        return result
    else:
        if not result:
            raise WinError()
        return result


_GetMessage = windll.user32.GetMessageW
_TranslateMessage = windll.user32.TranslateMessage
_TranslateMessage.errcheck = _win_check
_DispatchMessage = windll.user32.DispatchMessageW
_DispatchMessage.errcheck = _win_check

_GlobalLock = windll.kernel32.GlobalLock
_GlobalLock.argtypes = [ctypes.c_void_p]
_GlobalLock.restype = ctypes.c_void_p
_GlobalLock.errcheck = _win_check
_GlobalUnlock = windll.kernel32.GlobalUnlock
_GlobalUnlock.argtypes = [ctypes.c_void_p]
_GlobalUnlock.errcheck = _win_check
_GlobalAlloc = windll.kernel32.GlobalAlloc
_GlobalAlloc.restype = ctypes.c_void_p
_GlobalAlloc.errcheck = _win_check
_GlobalFree = windll.kernel32.GlobalFree
_GlobalFree.argtypes = [ctypes.c_void_p]
_GlobalFree.errcheck = _win_check
_GlobalSize = windll.kernel32.GlobalSize
_GlobalSize.argtypes = [ctypes.c_void_p]
_GlobalSize.restype = ctypes.c_size_t
_GlobalSize.errcheck = _win_check


class _Image(object):
    def __init__(self, handle):
        self._handle = handle

        self._free = _GlobalFree
        self._lock = _GlobalLock
        self._unlock = _GlobalUnlock

    def __del__(self):
        self.close()

    def close(self):
        """Releases memory of image"""
        self._free(self._handle)
        self._handle = None

    def save(self, filepath):
        """Saves in-memory image to BMP file"""
        _dib_write(self._handle, filepath, self._lock, self._unlock)


class BITMAPINFOHEADER(Structure):
    _pack_ = 4
    _fields_ = [('biSize', c_uint32),
                ('biWidth', c_long),
                ('biHeight', c_long),
                ('biPlanes', c_uint16),
                ('biBitCount', c_uint16),
                ('biCompression', c_uint32),
                ('biSizeImage', c_uint32),
                ('biXPelsPerMeter', c_long),
                ('biYPelsPerMeter', c_long),
                ('biClrUsed', c_uint32),
                ('biClrImportant', c_uint32)]


def _dib_write(handle, path, lock, unlock):
    file_header_size = 14
    ptr = lock(handle)
    try:
        char_ptr = cast(ptr, POINTER(c_char))
        bih = cast(ptr, POINTER(BITMAPINFOHEADER)).contents
        if bih.biCompression != 0:
            msg = 'Cannot handle compressed image. Compression Format %d' % bih.biCompression
            raise excImageFormat(msg)
        bits_offset = file_header_size + bih.biSize + bih.biClrUsed * 4
        if bih.biSizeImage == 0:
            row_bytes = (((bih.biWidth * bih.biBitCount) + 31) & ~31) // 8
            bih.biSizeImage = row_bytes * bih.biHeight
        dib_size = bih.biSize + bih.biClrUsed * 4 + bih.biSizeImage
        file_size = dib_size + file_header_size

        def _write_bmp(f):
            import struct
            f.write(b'BM')
            f.write(struct.pack('LHHL', file_size, 0, 0, bits_offset))
            for i in range(dib_size):
                f.write(char_ptr[i])

        if path:
            f = open(path, 'wb')
            try:
                _write_bmp(f)
            finally:
                f.close()
        else:
            import io
            f = io.BytesIO()
            try:
                _write_bmp(f)
                return f.getvalue()
            finally:
                f.close()
    finally:
        unlock(handle)