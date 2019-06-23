#!/usr/bin/python
# -*- coding: utf-8 -*-

import platform
import ctypes
from ctypes import *
from ctypes import wintypes
from twainlib.constants import *
#from pywin32 import GetFileVersionInfo, LOWORD, HIWORD
#from win32.win32api import GetFileVersionInfo
#from win32.win32api import
import os


class Application():
    def __init__(self, parent_window=None, send_message_callback = None):
        self._tw_app = None
        self.dll = None
        self.dsm_entry = None
        self._parent_window = parent_window
        self._hwnd = parent_window.winfo_id()
        self.send_message_callback = send_message_callback
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
        self._tw_app = TW_IDENTITY(Version=TW_VERSION(MajorNum=MajorNum,
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
        if self.send_message_callback:
            self.send_message_callback.__call__("Data Source Manager starts loading")
        try:
            self.dll = windll.LoadLibrary('twain_32.dll')
            self.dsm_version = self.get_file_version('twain_32.dll', "FileVersion")
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
            self.source_manager = SourceManager(self)
            if self.send_message_callback:
                self.send_message_callback.__call__("Data Source Manager (%s) is loaded" % self.source_manager.version)
            return self.source_manager
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))
            return None

    def unload_source_manager(self):
        '''
        2 --> 1
        :return:
        '''
        version = self.source_manager.version
        if self.send_message_callback:
            self.send_message_callback.__call__("Data Source Manager (%s) starts unloading" % version)
        try:
            del self.dll
            self.source_manager = None
            if self.send_message_callback:
                self.send_message_callback("Data Source Manager (%s) is unloaded" % version)
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))

    # returns the requested version information from the given file
    #
    # `language` should be an 8-character string combining both the language and
    # codepage (such as "040904b0"); if None, the first language in the translation
    # table is used instead
    #
    def get_file_version(self, filename, what, language=None):
        # VerQueryValue() returns an array of that for VarFileInfo\Translation
        #
        class LANGANDCODEPAGE(Structure):
            _fields_ = [
                ("wLanguage", c_uint16),
                ("wCodePage", c_uint16)]

        wstr_file = wstring_at(filename)

        # getting the size in bytes of the file version info buffer
        size = windll.version.GetFileVersionInfoSizeW(wstr_file, None)
        if size == 0:
            raise WinError()

        buffer = create_string_buffer(size)

        # getting the file version info data
        if windll.version.GetFileVersionInfoW(wstr_file, None, size, buffer) == 0:
            raise WinError()

        # VerQueryValue() wants a pointer to a void* and DWORD; used both for
        # getting the default language (if necessary) and getting the actual data
        # below
        value = c_void_p(0)
        value_size = c_uint(0)

        if language is None:
            # file version information can contain much more than the version
            # number (copyright, application name, etc.) and these are all
            # translatable
            #
            # the following arbitrarily gets the first language and codepage from
            # the list
            ret = windll.version.VerQueryValueW(
                buffer, wstring_at(r"\VarFileInfo\Translation"),
                byref(value), byref(value_size))

            if ret == 0:
                raise WinError()

            # value points to a byte inside buffer, value_size is the size in bytes
            # of that particular section

            # casting the void* to a LANGANDCODEPAGE*
            lcp = cast(value, POINTER(LANGANDCODEPAGE))

            # formatting language and codepage to something like "040904b0"
            language = "{0:04x}{1:04x}".format(
                lcp.contents.wLanguage, lcp.contents.wCodePage)

        # getting the actual data
        res = windll.version.VerQueryValueW(
            buffer, wstring_at("\\StringFileInfo\\" + language + "\\" + what),
            byref(value), byref(value_size))

        if res == 0:
            raise WinError()

        # value points to a string of value_size characters, minus one for the
        # terminating null
        version = wstring_at(value.value, value_size.value - 1)
        version = version.replace(",",".")
        return version


class SourceManager():
    """
        This object represents Data Source Manager
    """
    def __init__(self, application):

        self._tw_app = application._tw_app
        self.dsm_entry = application.dsm_entry
        self.version = application.dsm_version
        self._hwnd = application._hwnd
        self.send_message_callback = application.send_message_callback
        self.tw_sources_dict = {}
        self.tw_current_source = None
        self.sources_info = []

    def open(self):
        '''
        2 -> 3 Open Source Manager
        :return:
        '''
        if self.send_message_callback:
            self.send_message_callback.__call__("Data Source Manager (%s) starts opening" % self.version)
        try:
            rc = self.dsm_entry(self._tw_app, None, DG_CONTROL, DAT_PARENT, MSG_OPENDSM,
                                    byref(c_void_p(self._hwnd)))
            if rc == TWRC_SUCCESS:
                if self.send_message_callback:
                    self.send_message_callback("(TWRC_SUCCESS=0) Data Source Manager (%s) is opened" % self.version)
            else:
                if self.send_message_callback:
                    self.send_message_callback("(TWRC=%d) Data Source Manager (%s) is not opened" % (rc, self.version))

        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))

    def close(self):
        '''
        3 -> 2 Close Source Manager
        :return:
        '''
        if self.send_message_callback:
            self.send_message_callback.__call__("Data Source Manager (%s) starts closing" % self.version)
        try:
            rc = self.dsm_entry(self._tw_app, None, DG_CONTROL, DAT_PARENT, MSG_CLOSEDSM,
                                    byref(c_void_p(self._hwnd)))
            if rc == TWRC_SUCCESS:
                if self.send_message_callback:
                    self.send_message_callback("(TWRC_SUCCESS=0) Data Source Manager (%s) is closed" % (self.version))
            else:
                if self.send_message_callback:
                    self.send_message_callback("(TWRC=%d) Data Source Manager (%s) is not closed" % (rc, self.version))
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))

    def get_sources(self):
        '''
        3
        :return:
        '''
        try:
            if self.send_message_callback:
                self.send_message_callback.__call__("Sources starts search")
            tw_source = TW_IDENTITY()
            rc = self.dsm_entry(self._tw_app, None, DG_CONTROL, DAT_IDENTITY, MSG_GETFIRST, byref(tw_source))
            if rc == TWRC_SUCCESS:
                if self.send_message_callback:
                    self.send_message_callback.__call__("(TWRC_SUCCESS=0) first source is searched")
            if rc == TWRC_FAILURE:  # 1 error
                cc = self.get_failure_condition_code(None)
                if cc == TWCC_NODS:  # no Sources found
                    if self.send_message_callback:
                        self.send_message_callback.__call__("(TWRC_FAILURE=1, TWCC_NODS=3) sources is not found")
                return []
            source_info = SourceInfo(
                        tw_source.Id,
                        tw_source.ProductName.decode("utf-8"),
                        str(tw_source.ProtocolMajor)+"."+str(tw_source.ProtocolMinor))
            self.sources_info.append(source_info)
            self.tw_sources_dict[tw_source.Id] = tw_source

            while True:
                tw_source = TW_IDENTITY()
                rc = self.dsm_entry(self._tw_app, None, DG_CONTROL, DAT_IDENTITY, MSG_GETNEXT, byref(tw_source))
                if rc == TWRC_SUCCESS:
                    if self.send_message_callback:
                        self.send_message_callback.__call__("(TWRC_SUCCESS=0) next source is searched")
                elif rc == TWRC_ENDOFLIST:
                    if self.send_message_callback:
                        self.send_message_callback.__call__("(TWRC_ENDOFLIST=7) no more sources for search")
                    break
                else:
                    if self.send_message_callback:
                        self.send_message_callback.__call__("(TWRC=%d) next source is not searched" % rc)
                source_info = SourceInfo(
                    tw_source.Id,
                    tw_source.ProductName.decode("utf-8"),
                    str(tw_source.ProtocolMajor) + "." + str(tw_source.ProtocolMinor))
                self.sources_info.append(source_info)
                self.tw_sources_dict[tw_source.Id] = tw_source

            if self.send_message_callback:
                self.send_message_callback.__call__("Sources are searched")
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))

        return self.sources_info

    def open_source(self, source_id):
        '''
        3 --> 4 open Source
        :param source_id:
        :return: Source
        '''
        try:
            tw_source = self.tw_sources_dict[source_id]
            if self.send_message_callback:
                self.send_message_callback.__call__("Source (%s) starts opening" % tw_source.ProductName.decode("utf-8"))
            rc = self.dsm_entry(self._tw_app, None, DG_CONTROL, DAT_IDENTITY, MSG_OPENDS, byref(tw_source))
            if rc == TWRC_SUCCESS:
                self.tw_current_source = tw_source
                if self.send_message_callback:
                    self.send_message_callback.__call__("Source (%s) is opened" % tw_source.ProductName.decode("utf-8"))
                return Source(self)
            else:
                if self.send_message_callback:
                    self.send_message_callback.__call__("(TWRC=%d) Source (%s) is opened" % (rc, tw_source.ProductName.decode("utf-8")))
                return None
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))
            return None

    def close_source(self, source_id):
        '''
        4 --> 3 close Source
        :param source_id:
        :return:
        '''
        try:
            tw_source = self.tw_sources_dict[source_id]
            if self.send_message_callback:
                self.send_message_callback.__call__("Source (%s) starts closing" % tw_source.ProductName.decode("utf-8"))
            rc = self.dsm_entry(self._tw_app, None, DG_CONTROL, DAT_IDENTITY, MSG_CLOSEDS, byref(tw_source))
            if rc == TWRC_SUCCESS:
                if self.send_message_callback:
                    self.send_message_callback.__call__("Source (%s) is closed" % tw_source.ProductName.decode("utf-8"))
                self.tw_current_source = None
            else:
                if self.send_message_callback:
                    self.send_message_callback.__call__("(TWRC=%d) Source (%s) is not closed" % (rc, tw_source.ProductName.decode("utf-8")))
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))

    def get_failure_condition_code(self, tw_source):
        status = TW_STATUS()
        self.dsm_entry(self._tw_app, tw_source, DG_CONTROL, DAT_STATUS, MSG_GET, byref(status))
        return status.ConditionCode


class SourceInfo():
    def __init__(self, id, name, twain):
        self.id = id
        self.name = name
        self.twain = twain


class Source():
    def __init__(self, source_manager):
        self._tw_app = source_manager._tw_app
        self.dsm_entry = source_manager.dsm_entry
        self._hwnd = source_manager._hwnd
        self.send_message_callback = source_manager.send_message_callback
        self.tw_source = source_manager.tw_current_source
        self.save_to = None
        self.filename = None

    def get_id(self):
        return self.tw_source.Id

    def get_name(self):
        return self.tw_source.ProductName.decode("utf-8")

    def get_twain(self):
        return str(self.tw_source.ProtocolMajor)+"."+str(self.tw_source.ProtocolMinor)

    def enable(self):
        '''
        4 --> 5 enable Source
        :return:
        '''
        if self.send_message_callback:
            self.send_message_callback.__call__("Source (%s) starts enabling" % self.get_name())
        try:
            ui = TW_USERINTERFACE(ShowUI=False, ModalUI=False, hParent=self._hwnd)
            rc = self.dsm_entry(self._tw_app, self.tw_source, DG_CONTROL, DAT_USERINTERFACE, MSG_ENABLEDS, byref(ui))
            if rc == TWRC_SUCCESS:
                if self.send_message_callback:
                    self.send_message_callback("(TWRC_SUCCESS=0) Source (%s) is enabled" % self.get_name())
            else:
                if self.send_message_callback:
                    self.send_message_callback("(TWRC=%d) Source (%s) is not enabled" % (rc, self.get_name()))
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))

    def disable(self):
        '''
        5 --> 4 disable Source
        :return:
        '''
        if self.send_message_callback:
            self.send_message_callback.__call__("Source (%s) starts disabling" % self.get_name())
        try:
            ui = TW_USERINTERFACE(ShowUI=False, ModalUI=False, hParent=self._hwnd)
            rc = self.dsm_entry(self._tw_app, self.tw_source, DG_CONTROL, DAT_USERINTERFACE, MSG_DISABLEDS, byref(ui))
            if rc == TWRC_SUCCESS:
                if self.send_message_callback:
                    self.send_message_callback.__call__("Source (%s) is disabled" % self.get_name())
                return
            if rc == TWRC_FAILURE:
                cc = self.get_failure_condition_code()
                if self.send_message_callback:
                    self.send_message_callback.__call__("(TWRC_FAILURE=1, TWCC=%d) Source (%s) is not disabled" % (cc, self.get_name()))
                if cc == TWCC_SEQERROR:
                    pass
            pass
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))

    def get_failure_condition_code(self):
        status = TW_STATUS()
        self.dsm_entry(self._tw_app, self.tw_source, DG_CONTROL, DAT_STATUS, MSG_GET, byref(status))
        return status.ConditionCode

    def scan(self, save_to, filename):
        if self.send_message_callback:
            self.send_message_callback.__call__("Source (%s) starts scanning" % self.tw_source.ProductName.decode("utf-8"))
        self.save_to = save_to
        self.filename = filename
        self.enable()
        self.app_event_loop(self.get_image)
        if self.send_message_callback:
            self.send_message_callback.__call__("Source (%s) ends scanning" % self.tw_source.ProductName.decode("utf-8"))

    def _process_event(self, msg_ref):
        if self.send_message_callback:
            self.send_message_callback.__call__("..Event starts processing")
        event = TW_EVENT(cast(msg_ref, c_void_p), 0)
        rc = self.dsm_entry(self._tw_app,
                            self.tw_source,
                            DG_CONTROL,
                            DAT_EVENT,
                            MSG_PROCESSEVENT,
                            byref(event))
        code = ''
        if event.TWMessage == MSG_XFERREADY:
            self._state = 'ready'
            code = "TWRC_DSEVENT=4, MSG_XFERREADY=257"
        else:
            code = "TWRC=%d, MSG=%d" % ((rc, event.TWMessage))
        if self.send_message_callback:
            self.send_message_callback.__call__("..(%s) Event is processed" % code)
        return rc, event.TWMessage

    def app_event_loop(self, callback=None):
        if self.send_message_callback:
            self.send_message_callback.__call__("Starts application loop")
        done = False
        msg = MSG()
        while not done:
            if not _GetMessage(byref(msg), 0, 0, 0):
                break
            if self.send_message_callback:
                self.send_message_callback.__call__("..Message is getted")
            rc, event = self._process_event(byref(msg))
            if callback:
                callback(event)
            if event in (MSG_XFERREADY, MSG_CLOSEDSREQ):#data is ready for transfer, source UI was disabled
                done = True
            if rc == TWRC_NOTDSEVENT: # this not Source event
                _TranslateMessage(byref(msg))
                _DispatchMessage(byref(msg))
        if self.send_message_callback:
            self.send_message_callback.__call__("Ends application loop")

    def get_image(self, event):
        if event == MSG_XFERREADY: #data is ready for transfer
            if self.send_message_callback:
                self.send_message_callback("..Data is ready for transfer")
            try:
                rv, handle = self.get_native_image()
                image = _Image(handle)
                filename = self.filename + ".bmp"
                image.save(os.path.join(self.save_to, filename))
                if self.send_message_callback:
                    self.send_message_callback("..Image is saved")
            except Exception as e:
                if self.send_message_callback:
                    self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))

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
        if self.send_message_callback:
            self.send_message_callback("..Image starts getting in native mode")
        try:
            hbitmap = c_void_p()
            rv = self.dsm_entry(self._tw_app, self.tw_source, DG_IMAGE,
                                DAT_IMAGENATIVEXFER,
                                MSG_GET,
                                byref(hbitmap))
            #rv, hbitmap = self._get_native_image()
            #more = self._end_xfer()
            if rv == TWRC_CANCEL:
                raise excDSTransferCancelled
            return rv, hbitmap
        except Exception as e:
            if self.send_message_callback:
                self.send_message_callback.__call__("APPLICATION EXCEPTION: " + str(e))


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