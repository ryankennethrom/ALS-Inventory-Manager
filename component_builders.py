# Under construction

import tkinter as tk
from tkinter import ttk

class TitledGridsBuilder():
    def __init__(self, frame):
        self.sections = []
        self.frame = frame

    def insert_section(self, content, position, heading):
        if position[0] > len(self.sections) or position[1] > len(position[1]) or position[0] < 0 or position[1] < 0:
            raise Exception("Section position out of bounds")
        return self
    
    def add_section_bottom(self, content, heading):
        self.sections.append([{"frame": content, "heading": heading}])
        return self


    def build(self):
        row_position = 0
        for row in range(len(self.sections)):
            for col in range(len(self.sections[1])):
                header = tk.Label(
                    self.frame,
                    text=self.sections[row][col]["heading"],
                    font=("Segoe UI", 14, "bold")
                )
                header.grid(row=row_position, column=col, columnspan=2, sticky="w", padx=10, pady=(20, 0))
                self.sections[row][col]["frame"].grid(row=row_position+1, column=col, columnspan=2, sticky="nsew", padx=10, pady=(5, 20))
            row_position += 2

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        for i in range(row_position+1):
            self.frame.grid_rowconfigure(i, weight=1)

        return self

class TabBuilder():
    def __init__(self, nav_context):
        self.nav_context = nav_context
        self.notebook = ttk.Frame(self.nav_context["notebook"])
        self.titled_grids_builder = TitledGridsBuilder(self.frame)

    def add_section_bottom(self, content, heading):
        self.titled_grids_builder.add_section_bottom(content, heading)
        return self

    def build(self):
        self.titled_grids_builder.build()
        return self
