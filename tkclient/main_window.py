#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import ttk
import tkinter
import twainlib.wrapper
#import twainlib
#from twainlib.wrapper import Application

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

        self.root.title("pygmyscanner")
        self.hs = self.root.winfo_screenheight()
        self.ws = self.root.winfo_screenwidth()
        self.root.geometry('%dx%d+%d+%d' % (width, height, (self.ws-width)//2, (self.hs-height)//2))
        self.root.resizable(width=False, height=False)
        #self.root.iconbitmap(icon_path)

        self.application = None
        self.source_manager = None
        self.sources = []
        self.opened_source = None

        self.frame = ttk.Frame()
        self.frame.pack(side=tkinter.RIGHT, anchor="n")

        self.table_sources = ttk.Treeview(self.frame, columns=("model", "twain"),show="headings", selectmode="browse")
        self.table_sources.heading("model", text="Модель")
        self.table_sources.heading("twain", text="twain")
        self.table_sources.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.actions_frame = ttk.Frame()
        self.actions_frame.pack(side=tkinter.LEFT, anchor="n")
        self.var_status = tkinter.StringVar()
        self.label_status = ttk.Label(self.actions_frame, textvariable=self.var_status)
        self.label_status.grid(row=0, column=0)
        self.button12 = ttk.Button(self.actions_frame, text="1-->2 Load Source Manager", style='Actions.TButton',
                                   command=self.load_source_manager)
        self.button12.grid(row=1, column=0, sticky="ew")
        self.button21 = ttk.Button(self.actions_frame, text="2-->1 Unload Source Manager", style='Actions.TButton',
                                    command = self.unload_source_manager)
        self.button21.grid(row=1, column=1, sticky="ew")
        self.button23 = ttk.Button(self.actions_frame, text="2-->3 Open Source Manager", style='Actions.TButton',
                                   command=self.open_source_manager)
        self.button23.grid(row=2, column=0, sticky="ew")
        self.button32 = ttk.Button(self.actions_frame, text="3-->2 Close Source Manager", style='Actions.TButton',
                                   command=self.close_source_manager)
        self.button32.grid(row=2, column=1, sticky="ew")
        self.button3 = ttk.Button(self.actions_frame, text="3: Select Source", style='Actions.TButton',
                                   command=self.select_source)
        self.button3.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.button34 = ttk.Button(self.actions_frame, text="3-->4 Open Source", style='Actions.TButton',
                                   command=self.open_source)
        self.button34.grid(row=4, column=0, sticky="ew")
        self.button43 = ttk.Button(self.actions_frame, text="4-->3 Close Source", style='Actions.TButton',
                                   command=self.close_source)
        self.button43.grid(row=4, column=1, sticky="ew")
        self.button4 = ttk.Button(self.actions_frame, text="4: Negotiate Capabilities", style='Actions.TButton')
        self.button4.grid(row=5, column=0, columnspan=2, sticky="ew")
        self.button45 = ttk.Button(self.actions_frame, text="4-->5 Enable Source", style='Actions.TButton',
                                   command=self.enable_source)
        self.button45.grid(row=6, column=0, sticky="ew")
        self.button54 = ttk.Button(self.actions_frame, text="5-->4 Event: Disable Source", style='Actions.TButton',
                                   command=self.disable_source)
        self.button54.grid(row=6, column=1, sticky="ew")
        self.button56 = ttk.Button(self.actions_frame, text="5-->6 Event: Transfer Ready", style='Actions.TButton')
        self.button56.grid(row=7, column=0, sticky="ew")
        self.button65 = ttk.Button(self.actions_frame, text="6-->5 Event: No more image for transfer", style='Actions.TButton')
        self.button65.grid(row=7, column=1, sticky="ew")
        self.button67 = ttk.Button(self.actions_frame, text="6-->7 Initiate Transfer", style='Actions.TButton')
        self.button67.grid(row=8, column=0, sticky="ew")
        self.button76 = ttk.Button(self.actions_frame, text="7-->6 End of Transfer", style='Actions.TButton')
        self.button76.grid(row=8, column=1, sticky="ew")

        self.set_status(1)
        self.root.mainloop()

    def set_status(self, num):
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
            self.button4["state"] = "enable"
            self.button45["state"] = "enable"
        if num == 5:
            self.button54["state"] = "enable"
            self.button56["state"] = "enable"
        if num == 6:
            self.button65["state"] = "enable"
            self.button67["state"] = "enable"
        if num == 7:
            self.button76["state"] = "enable"

        self.var_status.set(STATES.get(num))

    def load_source_manager(self):
        self.application = twainlib.wrapper.Application(self.root)
        self.source_manager = self.application.load_source_manager()
        self.set_status(2)

    def unload_source_manager(self):
        self.application.unload_source_manager()
        self.set_status(1)

    def open_source_manager(self):
        self.source_manager.open()
        self.set_status(3)

    def close_source_manager(self):
        self.source_manager.close()
        self.set_status(2)

    def select_source(self):
        self.sources = self.source_manager.get_sources()
        for row in self.table_sources.get_children():
            self.table_sources.delete(row)
        for source in self.sources:
            self.table_sources.insert('', 'end', iid=source[0], values=(source[1], source[2]))

    def open_source(self):
        selection = self.table_sources.selection()
        if not selection:
            return
        source_id = int(selection[0])
        self.source_manager.open_source(source_id)
        self.opened_source = source_id
        self.set_status(4)

    def close_source(self):
        self.source_manager.close_source(self.opened_source)
        self.opened_source = None
        self.set_status(3)

    def enable_source(self):
        self.source_manager.enable_source()
        self.set_status(5)

    def disable_source(self):
        self.source_manager.disable_source()
        self.set_status(4)

if __name__ == "__main__":
    MainWindow(1000, 500, '../logo.ico', '../logo.gif')
