#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import ttk
import tkinter
import twainlib


class MainWindow:
    def __init__(self, width, height, icon_path, logo_path):
        self.root = tkinter.Tk()

        #self.style = ttk.Style()
        #self.themes = self.style.theme_names()

        #self.root.set_theme("vista")
        self.root.title("pygmyscanner")
        self.hs = self.root.winfo_screenheight()
        self.ws = self.root.winfo_screenwidth()
        self.root.geometry('%dx%d+%d+%d' % (width, height, (self.ws-width)//2, (self.hs-height)//2))
        self.root.resizable(width=False, height=False)
        #self.root.iconbitmap(icon_path)

        self.frame = ttk.Frame()
        self.frame.pack()

        self.button_check_system = ttk.Button(self.frame, text="Проверить ОС", command=self.check_system)
        self.button_check_system.grid(row=0, column=0, sticky="ew")
        self.var_system = tkinter.StringVar()
        self.label_system = ttk.Label(self.frame, textvariable=self.var_system, width=100)
        self.label_system.grid(row=0, column=1, columnspan=1, sticky="ew")

        self.button_check_twain_dll = ttk.Button(self.frame, text="Проверить twain.dll", command=self.check_twain_dll)
        self.button_check_twain_dll.grid(row=1, column=0, sticky="ew")
        self.var_twain_dll = tkinter.StringVar()
        self.label_twain_dll = ttk.Label(self.frame, textvariable=self.var_twain_dll, width=100)
        self.label_twain_dll.grid(row=1, column=1, columnspan=1, sticky="ew")

        self.root.mainloop()

    def check_system(self):
        system = twainlib.check_system()
        if not system:
            system = 'Не определена'
        self.var_system.set(system)

    def check_twain_dll(self):
        dll_name = twainlib.check_twain_dll()
        if not dll_name:
            dll_name = 'Не определена'
        self.var_twain_dll.set(dll_name)


if __name__ == "__main__":
    MainWindow(1000, 500, '../logo.ico', '../logo.gif')