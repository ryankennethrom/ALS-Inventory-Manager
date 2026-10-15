import tkinter as tk

class TitledGridsBuilder():
    def __init__(self, frame):
        self.sections = []
        self.available_row = 0
        self.frame = frame
    
    def add_section_bottom(self, content, heading=None, space_ratio=100):
        self.sections.append([{"frame": content, "heading": heading}]) 
        return self

    def fill_rest_with_last_section(self, enabled=True):
        self.fill_rest_with_last_section = enabled
        return self

    def add_rightmost_of_bottom_section(self, content, heading, space_ratio):
        self.sections[-1].append({"frame": content, "heading": heading})
        return self

    def build(self):
        row_position = 0
        last_frame_row = None
        for row in range(len(self.sections)):
            for col in range(len(self.sections[0])):
                if self.sections[row][col]["heading"]:
                    header = tk.Label(
                        self.frame,
                        text=self.sections[row][col]["heading"],
                        font=("Segoe UI", 14, "bold")
                    )
                    header.grid(row=row_position, column=col, columnspan=2, sticky="w", padx=10, pady=(20, 0))
                self.sections[row][col]["frame"].grid(row=row_position+1, column=col, columnspan=2, sticky="nsew", padx=10, pady=(5, 20))

                frame_row = row_position + 1
                last_frame_row = frame_row
            row_position += 2

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        if self.fill_rest_with_last_section:
            # only the final section expands
            for i in range(row_position + 1):
                self.frame.grid_rowconfigure(i, weight=0)

            if last_frame_row is not None:
                self.frame.grid_rowconfigure(last_frame_row, weight=1)
        else: 
            for i in range(row_position+1):
                self.frame.grid_rowconfigure(i, weight=1)

        return self

    def build_old(self):
        row_position = 0

        last_frame_row = None

        for row in range(len(self.sections)):
            for col in range(len(self.sections[0])):
                header = tk.Label(
                    self.frame,
                    text=self.sections[row][col]["heading"],
                    font=("Segoe UI", 14, "bold")
                )

                header.grid(
                row=row_position,
                column=col,
                columnspan=2,
                sticky="w",
                padx=10,
                pady=(20, 0)
                )

                frame_row = row_position + 1

                self.sections[row][col]["frame"].grid(
                row=frame_row,
                column=col,
                columnspan=2,
                sticky="nsew",
                padx=10,
                pady=(5, 20)
                )

                last_frame_row = frame_row

            row_position += 2

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        if self.fill_rest_with_last_section:
            # only the final section expands
            for i in range(row_position + 1):
                self.frame.grid_rowconfigure(i, weight=0)

            if last_frame_row is not None:
                self.frame.grid_rowconfigure(last_frame_row, weight=1)
        else:
            # current behavior
            for i in range(row_position + 1):
                self.frame.grid_rowconfigure(i, weight=1)

        return self
