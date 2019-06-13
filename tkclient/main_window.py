#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import ttk
import tkinter
import twainlib.wrapper
#import twainlib
#from twainlib.wrapper import Application

STATES = {1: "Pre-Session",
          2: "Source Manager Loaded",
          3: "Source Manager Opened",
          4: "Source Opened",
          5: "Source Enabled",
          6: "Transfer is Ready",
          7: "Transferring"}


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

        self.button_search_sources = ttk.Button(self.frame, text="Найти сканеры", command=self.search_sources)
        self.button_search_sources.grid(row=0, column=0)
        self.button_open_source = ttk.Button(self.frame, text="Открыть сканер", command=self.open_source)
        self.button_open_source.grid(row=0, column=1)
        #self.var_results = tkinter.StringVar()
        #self.label_results = ttk.Label(self.frame, textvariable=self.var_results, width=100)
        #self.label_results.grid(row=1, column=0, columnspan=1, sticky="ew")
        self.table_sources = ttk.Treeview(self.frame, columns=("model", "twain"),show="headings", selectmode="browse")
        self.table_sources.heading("model", text="Модель")
        self.table_sources.heading("twain", text="twain")
        self.table_sources.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.actions_frame = ttk.Frame()
        self.actions_frame.pack()
        self.var_status = tkinter.StringVar()
        self.label_status = ttk.Label(self.actions_frame, textvariable=self.var_status)
        self.label_status.grid(row=0, column=0)
        self.button12 = ttk.Button(self.actions_frame, text="1-->2 Load Source Manager")
        self.button12.grid(row=1, column=0)
        self.button21 = ttk.Button(self.actions_frame, text="2-->1 Unload Source Manager")
        self.button21.grid(row=1, column=1)
        self.button23 = ttk.Button(self.actions_frame, text="2-->3 Open Source Manager")
        self.button23.grid(row=2, column=0)
        self.button32 = ttk.Button(self.actions_frame, text="3-->2 Close Source Manager")
        self.button32.grid(row=2, column=1)
        self.button34 = ttk.Button(self.actions_frame, text="3-->4 Open Source")
        self.button34.grid(row=3, column=0)
        self.button43 = ttk.Button(self.actions_frame, text="4-->3 Close Source")
        self.button43.grid(row=3, column=1)
        self.root.mainloop()

    def refresh_table_sources(self):
        for row in self.table_sources.get_children():
            self.delete(row)
        #self.table_sources.insert('', 'end', iid=1, values=('Название1','1.0'))
        #self.table_sources.insert('', 'end', iid=2, values=('Название2', '2.0'))
        for source in self.sources:
            self.table_sources.insert('', 'end', iid=source[0], values=(source[1], source[2]))

    def search_sources(self):
        self.application = twainlib.wrapper.Application(MajorNum=0, MinorNum=1, Language=78, Country=7,
                              ProtocolMajor=1, ProtocolMinor=9, Manufacturer="Tsibizov Pavel", ProductName="pygmyscan")
        self.dsm = self.application.load_source_manager()
        x = 1
        #self.DSM = twainlib.wrapper.SourceManager(self.root)
        #self.DSM.set_app_info(MajorNum=0, MinorNum=1, Language=TWLG_RUSSIAN, Country=TWCY_RUSSIA,
        #                      ProtocolMajor=1, ProtocolMinor=9, Manufacturer="Tsibizov Pavel", ProductName="pygmyscan")
        #self.sources = self.DSM.get_sources()
        #self.refresh_table_sources()
        #results = ";".join(sources) if len(sources) != 0 else "ничего нет"
        #self.var_results.set(results)

    def open_source(self):
        selection = self.table_sources.selection()
        source_id = int(selection[0])
        self.DSM.open_source(source_id)


if __name__ == "__main__":
    MainWindow(1000, 500, '../logo.ico', '../logo.gif')
