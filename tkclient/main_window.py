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

        self.root.mainloop()

    def refresh_table_sources(self):
        for row in self.table_sources.get_children():
            self.delete(row)
        #self.table_sources.insert('', 'end', iid=1, values=('Название1','1.0'))
        #self.table_sources.insert('', 'end', iid=2, values=('Название2', '2.0'))
        for source in self.sources:
            self.table_sources.insert('', 'end', iid=source[0], values=(source[1], source[2]))

    def search_sources(self):
        self.DSM = dsm.DataSourceManager(self.root)
        self.sources = self.DSM.get_sources()
        self.refresh_table_sources()
        #results = ";".join(sources) if len(sources) != 0 else "ничего нет"
        #self.var_results.set(results)

    def open_source(self):
        selection = self.table_sources.selection()
        source_id = int(selection[0])
        self.DSM.open_source(source_id)



if __name__ == "__main__":
    MainWindow(1000, 500, '../logo.ico', '../logo.gif')
