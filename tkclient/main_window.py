#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import ttk
import tkinter
import twainlib.wrapper
#import twainlib
#from twainlib.wrapper import Application
from datetime import datetime
import tkinter.scrolledtext as tkscrolled

STATES = {1: "1: Pre-Session",
          2: "2: Source Manager Loaded",
          3: "3: Source Manager Opened",
          4: "4: Source Opened",
          5: "5: Source Enabled",
          6: "6: Transfer is Ready",
          7: "7: Transferring"}


class MainWindow:
    def __init__(self, width, height, icon_path, logo_path):
        self.root = tkinter.Tk()

        self.style = ttk.Style()
        #self.themes = self.style.theme_names()
        #self.root.set_theme("vista")
        self.style.configure('Actions.TButton', anchor="w")

        self.root.title("pygmyscanner debug tool (development)")
        self.hs = self.root.winfo_screenheight()
        self.ws = self.root.winfo_screenwidth()
        self.root.geometry('%dx%d+%d+%d' % (width, height, (self.ws-width)//2, (self.hs-height)//2))
        self.root.resizable(width=False, height=False)
        #self.root.iconbitmap(icon_path)

        self.application = twainlib.wrapper.Application(self.root)
        self.source_manager = None
        self.sources = []
        self.source = None
        self.opened_source = None

        self.top_frame = ttk.Frame(self.root)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="w")
        self.var_tw_status = tkinter.StringVar()
        self.tw_status = ttk.Label(self.top_frame, textvariable=self.var_tw_status, anchor="w", relief="sunken",
                                   width=50)
        self.tw_status.grid(row=0, column=0, sticky="w")
        self.var_dsm_status = tkinter.StringVar()
        self.dsm_status = ttk.Label(self.top_frame, textvariable=self.var_dsm_status, relief="sunken", width=40)
        self.dsm_status.grid(row=0, column=1, sticky="w")
        self.var_source_status = tkinter.StringVar()
        self.source_status = ttk.Label(self.top_frame, textvariable=self.var_source_status, relief="sunken", width=30)
        self.source_status.grid(row=0, column=2, sticky="w")
        self.top_frame.columnconfigure(0, pad=10, minsize=300)
        self.top_frame.columnconfigure(1, pad=10, minsize=300)
        self.top_frame.columnconfigure(2, pad=10, minsize=300)

        self.left_frame = ttk.Frame(self.root)
        self.left_frame.grid(row=1, column=0, sticky="w")
        self.button12 = ttk.Button(self.left_frame, text="1-->2 Load Source Manager", style='Actions.TButton',
                                   command=self.load_source_manager)
        self.button12.grid(row=0, column=0, sticky="ew")
        self.button21 = ttk.Button(self.left_frame, text="2-->1 Unload Source Manager", style='Actions.TButton',
                                   command=self.unload_source_manager)
        self.button21.grid(row=0, column=1, sticky="ew")
        self.button23 = ttk.Button(self.left_frame, text="2-->3 Open Source Manager", style='Actions.TButton',
                                   command=self.open_source_manager)
        self.button23.grid(row=1, column=0, sticky="ew")
        self.button32 = ttk.Button(self.left_frame, text="3-->2 Close Source Manager", style='Actions.TButton',
                                   command=self.close_source_manager)
        self.button32.grid(row=1, column=1, sticky="ew")
        self.button3 = ttk.Button(self.left_frame, text="3: Get Sources", style='Actions.TButton',
                                  command=self.get_sources)
        self.button3.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.button34 = ttk.Button(self.left_frame, text="3-->4 Open Source", style='Actions.TButton',
                                   command=self.open_source)
        self.button34.grid(row=3, column=0, sticky="ew")
        self.button43 = ttk.Button(self.left_frame, text="4-->3 Close Source", style='Actions.TButton',
                                   command=self.close_source)
        self.button43.grid(row=3, column=1, sticky="ew")
        self.button4 = ttk.Button(self.left_frame, text="4: Negotiate Capabilities", style='Actions.TButton')
        self.button4.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.button45 = ttk.Button(self.left_frame, text="4-->5 Enable Source", style='Actions.TButton',
                                   command=self.enable_source)
        self.button45.grid(row=5, column=0, sticky="ew")
        self.button54 = ttk.Button(self.left_frame, text="5-->4 Event: Disable Source", style='Actions.TButton',
                                   command=self.disable_source)
        self.button54.grid(row=5, column=1, sticky="ew")
        self.button56 = ttk.Button(self.left_frame, text="5-->6 Event: Transfer Ready", style='Actions.TButton')
        self.button56.grid(row=6, column=0, sticky="ew")
        self.button65 = ttk.Button(self.left_frame, text="6-->5 Event: No more image for transfer",
                                   style='Actions.TButton')
        self.button65.grid(row=6, column=1, sticky="ew")
        self.button67 = ttk.Button(self.left_frame, text="6-->7 Initiate Transfer", style='Actions.TButton')
        self.button67.grid(row=7, column=0, sticky="ew")
        self.button76 = ttk.Button(self.left_frame, text="7-->6 End of Transfer", style='Actions.TButton')
        self.button76.grid(row=7, column=1, sticky="ew")

        self.right_frame = ttk.Frame(self.root)
        self.right_frame.grid(row=1, column=1, sticky="w")

        self.table_sources = ttk.Treeview(self.right_frame, columns=("model", "twain"),show="headings",
                                          selectmode="browse")
        self.table_sources.heading("model", text="Модель")
        self.table_sources.heading("twain", text="twain")
        self.table_sources.column("model", width=300)
        self.table_sources.column("twain", width=50)
        self.table_sources.grid(row=0, column=0, sticky="ew")
        self.table_sources.grid_remove()

        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.text_area = tkscrolled.ScrolledText(self.bottom_frame, height=15, wrap='word')
        self.text_area.pack(fill=tkinter.BOTH)

        self.set_statuses(1)

        self.root.rowconfigure(0, pad=10)
        self.root.rowconfigure(1, pad=10)
        self.root.rowconfigure(2, pad=10)
        #self.root.columnconfigure(0, minsize=10)
        #self.root.columnconfigure(1, minsize=300)
        self.root.mainloop()

    def set_statuses(self, num):
        self.button12["state"] = "disabled"
        self.button21["state"] = "disabled"
        self.button23["state"] = "disabled"
        self.button32["state"] = "disabled"
        self.button3["state"] = "disabled"
        self.button34["state"] = "disabled"
        self.button43["state"] = "disabled"
        self.button4["state"] = "disabled"
        self.button45["state"] = "disabled"
        self.button54["state"] = "disabled"
        self.button56["state"] = "disabled"
        self.button65["state"] = "disabled"
        self.button67["state"] = "disabled"
        self.button76["state"] = "disabled"
        if num == 1:
            self.button12["state"] = "enable"
        if num == 2:
            self.button21["state"] = "enable"
            self.button23["state"] = "enable"
        if num == 3:
            self.button32["state"] = "enable"
            self.button3["state"] = "enable"
            self.button34["state"] = "enable"
        if num == 4:
            self.button43["state"] = "enable"
            #self.button4["state"] = "enable"
            self.button45["state"] = "enable"
        if num == 5:
            #self.button54["state"] = "enable"
            #self.button56["state"] = "enable"
            pass
        if num == 6:
            #self.button65["state"] = "enable"
            #self.button67["state"] = "enable"
            pass
        if num == 7:
            #self.button76["state"] = "enable"
            pass

        if num == 1:
            self.var_dsm_status.set("")
            self.var_source_status.set("")
        if num == 2:
            self.var_dsm_status.set("Data Source Manager (%s) is loaded" % self.source_manager.version)
            self.var_source_status.set("")
        if num == 3:
            self.var_dsm_status.set("Data Source Manager (%s) is opened" % self.source_manager.version)
            self.var_source_status.set("")
        if num == 4:
            self.var_source_status.set("Source is opened")
        if num == 5:
            self.var_source_status.set("Source is enabled")
        self.var_tw_status.set("TWAIN Session Status - " + STATES.get(num))

    def load_source_manager(self):
        self.source_manager = self.application.load_source_manager()
        self.set_statuses(2)
        self.insert_text("Data Source Manager (%s) is loaded" % self.source_manager.version)

    def unload_source_manager(self):
        self.application.unload_source_manager()
        self.set_statuses(1)
        self.insert_text("Data Source Manager (%s) is unloaded" % self.source_manager.version)

    def open_source_manager(self):
        self.source_manager.open()
        self.set_statuses(3)
        self.insert_text("Data Source Manager (%s) is opened" % self.source_manager.version)

    def close_source_manager(self):
        self.source_manager.close()
        self.set_statuses(2)
        self.insert_text("Data Source Manager (%s) is closed" % self.source_manager.version)

    def get_sources(self):
        self.table_sources.grid()
        self.sources = self.source_manager.get_sources()
        for row in self.table_sources.get_children():
            self.table_sources.delete(row)
        for source in self.sources:
            self.table_sources.insert('', 'end', iid=source[0], values=(source[1], source[2]))
        self.insert_text("Sources are searched")

    def open_source(self):
        selection = self.table_sources.selection()
        if not selection:
            self.insert_text("Source is not selected")
            return
        source_id = int(selection[0])
        self.source = self.source_manager.open_source(source_id)
        self.opened_source = source_id
        self.set_statuses(4)
        self.insert_text("Source is opened")

    def close_source(self):
        self.source_manager.close_source(self.opened_source)
        self.opened_source = None
        self.source = None
        self.set_statuses(3)
        self.insert_text("Source is closed")

    def enable_source(self):
        self.source.enable()
        self.insert_text("Source is enabled")
        self.source._modal_loop()
        self.insert_text("Start loop")
        self.set_statuses(5)

    def disable_source(self):
        self.source.disable()
        self.set_statuses(4)
        self.insert_text("Source is disabled")

    def insert_text(self, text):
        var_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S ')
        self.text_area.insert(tkinter.END, var_datetime + text+"\n")
        self.text_area.see(tkinter.END)


if __name__ == "__main__":
    MainWindow(1000, 500, '../logo.ico', '../logo.gif')
