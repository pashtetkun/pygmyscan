#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import ttk
import tkinter
import twainlib.data_source_manager as dsm


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
        self.button_search_sources.grid(row=0, column=0, sticky="ew")
        self.var_results = tkinter.StringVar()
        self.label_results = ttk.Label(self.frame, textvariable=self.var_results, width=100)
        self.label_results.grid(row=1, column=0, columnspan=1, sticky="ew")

        self.root.mainloop()

    def search_sources(self):
        SM = dsm.DataSourceManager(self.root)
        sources = SM.get_sources()
        results = ";".join(sources) if len(sources) != 0 else "ничего нет"
        self.var_results.set(results)



if __name__ == "__main__":
    MainWindow(1000, 500, '../logo.ico', '../logo.gif')
