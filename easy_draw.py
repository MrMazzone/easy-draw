#######################
# Hi students,
# DO NOT MESS AROUND WITH THIS FILE
# Please 😁
#######################

#######################
# Easy Draw Module
# Version 1.0.2
# Created by Joe Mazzone
# Documentation: https://daviestech.gitbook.io/easy-draw/
#######################

#######################
# This module was developed for students to easily create basic Python GUIs by drawing graphics primitives.
# It features drawing functions for many shapes, as well as event handling for basic animations and games.
#######################

import tkinter as tk
import tkinter.colorchooser, tkinter.messagebox, tkinter.simpledialog
from PIL import ImageGrab
import math
import time


class __EasyDrawError(Exception):
    """ Raised for error caused by not properly using the module """
    def __init__(self, message="Seems you did something you shouldn't with Easy Draw..."):
        self.message = message
        super().__init__(self.message)


print("Welcome to Easy Draw! -- version 1.0.2 -- https://daviestech.gitbook.io/easy-draw/")
WINDOW = None
CANVAS = None
GRID_LINES = []
GRID_ON = False


def load_canvas(background=None):
    '''Opens Easy Draw window with a 600x600 canvas.'''
    global WINDOW
    global CANVAS
    global GRID_LINES
    global GRID_ON
    WINDOW = tk.Tk()
    WINDOW.title("Easy Draw")
    WINDOW.resizable(False, False)
    y_labels = []
    x_labels = []
    WINDOW.columnconfigure(1, minsize=40)
    for i in range(2, 13):
        WINDOW.columnconfigure(i, minsize=50)
    WINDOW.rowconfigure(3, minsize=40)      
    for i in range(4, 15):
        WINDOW.rowconfigure(i, minsize=50)              
    colorDialog = tkinter.colorchooser.Chooser(WINDOW)
    def openColorDialog():
        color = colorDialog.show()
        if not color[1] is None:
            tkinter.messagebox.showinfo("Your Color", "The color you chose is: " + "\n\n" + color[1] + "\n\n" + "RBG (" + str(int(color[0][0])) + ", " + str(int(color[0][1])) + ", " + str(int(color[0][2])) + ")")
    color_button = tk.Button(
        text = "Color Picker",
        font = ("Arial", 12, "bold"),
        bg = "#07649E",
        fg = "#FFFFFF",
        command = openColorDialog
    )
    color_button.grid(column=1, row=1, columnspan=4, padx=5, pady=5)
    def toggle_grid():
        global GRID_LINES
        global GRID_ON
        if GRID_ON:
            GRID_ON = False
            grid_button["text"] = "Grid"
            grid_button["bg"] = "#07649E"
            for line in GRID_LINES:
                CANVAS.itemconfig(line, state = tk.HIDDEN)
            for label in x_labels:
                label.configure(fg = WINDOW.cget("background"))
            for label in y_labels:
                label.configure(fg = WINDOW.cget("background"))
        else:
            GRID_ON = True
            grid_button["text"] = "Grid"
            grid_button["bg"] = "#E32636"
            for line in GRID_LINES:
                CANVAS.itemconfig(line, state = tk.NORMAL)
            for label in x_labels:
                label.configure(fg = "#07649E")
            for label in y_labels:
                label.configure(fg = "#07649E")
    grid_button = tk.Button(
        text="Grid",
        font=("Arial", 12, "bold"),
        bg = "#07649E",
        fg = "#FFFFFF",
        command=toggle_grid
    )
    grid_button.grid(column=5, row=1, columnspan=4, padx=5, pady=5)
    CANVAS = tk.Canvas(width = 595, height = 595, bg=background, bd=2, cursor="crosshair", relief="ridge")
    CANVAS.grid(column=1, row=3, columnspan=13, rowspan=13, padx=5, sticky="nw")
    save_button = tk.Button(
        text="Save Canvas",
        font=("Arial", 12, "bold"),
        bg = "#07649E",
        fg = "#FFFFFF",
        command=save_canvas
    )
    save_button.grid(column=9, row=1, columnspan=4, padx=5, pady=5)
    # Display Coordinates
    def mousePosition(event):
        xy_label["text"] = "  x  ,  y  \n(" + str(event.x) + ", " + str(event.y) + ")"
    CANVAS.bind("<Motion>", mousePosition)
    xy_label = tk.Label(
        text = "  x  ,  y  \n(0, 0)",
        fg = "#07649E",
        font=("Arial", 12, "bold")
    )
    xy_label.grid(column=8, row=16, columnspan=6, sticky="ne", padx=5, pady=5)
    window_bg = WINDOW.cget("background")
    for i in range(0, 601, 50):
        x_labels.append(tk.Label(text = str(i), fg = window_bg, font=("Arial", 8), padx=0, pady=0))
        y_labels.append(tk.Label(text = str(i), fg = window_bg, font=("Arial", 8), padx=0, pady=0))
    count = 1
    for label in x_labels:
        label.grid(column=count, row=2, sticky="sw")
        count += 1
    count = 3
    for label in y_labels:
        label.grid(column=0, row=count, sticky="ne")
        count += 1
    spacer1 = tk.Label(text = " ")
    spacer1.grid(column=15, row=3, sticky="w", padx=6)
    spacer2 = tk.Label(text = "   ", font=("Arial", 4))
    spacer2.grid(column=1, row=0)


def set_canvas_color(color):
    global CANVAS
    if type(color) is tuple:
        color = rgb_convert(color)
    CANVAS.configure(bg = color)


def end():
    global CANVAS
    global WINDOW
    global GRID_LINES
    # Create Grid Lines
    for i in range(50, 600, 50):
        GRID_LINES.append(CANVAS.create_line(0, i, 610, i, fill="#C2CCD0", width=1))
    for i in range(50, 600, 50):
        GRID_LINES.append(CANVAS.create_line(i, 0, i, 610, fill="#C2CCD0", width=1))
    for line in GRID_LINES:
        CANVAS.itemconfig(line, state = tk.HIDDEN)
    WINDOW.mainloop()


def __screenshot__(filename):
    global WINDOW
    global CANVAS
    x = WINDOW.winfo_rootx() + CANVAS.winfo_x()
    y = WINDOW.winfo_rooty() + CANVAS.winfo_y()
    x1 = x + CANVAS.winfo_width()
    y1 = y + CANVAS.winfo_height()
    ImageGrab.grab().crop((x,y,x1,y1)).save(filename + ".png")
    if GRID_ON:
        for line in GRID_LINES:
            CANVAS.itemconfig(line, state = tk.NORMAL)


def save_canvas():
    global WINDOW
    global CANVAS
    global GRID_LINES
    global GRID_ON
    for line in GRID_LINES:
        CANVAS.itemconfig(line, state = tk.HIDDEN)
    name = tkinter.simpledialog.askstring("Save File", "What would you like your picture's file name to be?", parent=WINDOW)
    if (not name is None) and (name != ""):
        print("Saving " + name + ".png ", end="")
        for i in range(5):
            time.sleep(0.25)
            print(".", end="")
        print("")
        WINDOW.after(250, __screenshot__(name))
    

def canvas_event_setup(event, handler):
    global CANVAS
    CANVAS.bind_all(event, handler)


def rgb_convert(rgb):
    return '#%02x%02x%02x' % rgb


# --- Drawing Shapes ---

class Rectangle:
    def __init__(self, xy, width, height, color="black", border_color=None, border_width=0, dashes=None):
        global CANVAS
        self.type = "Rectangle"
        self.angle = 0
        self.xy = xy
        self.width = width
        self.height = height
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        points = [
            self.xy[0], self.xy[1],
            self.xy[0] + self.width, self.xy[1],
            self.xy[0] + self.width, self.xy[1] + self.height,
            self.xy[0], self.xy[1] + self.height
        ]
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        if type(self.border_color) is tuple:
            self.border_color = rgb_convert(self.border_color)
        if not self.dashes is None and not type(self.dashes) is tuple:
            self.dashes = (self.dashes, self.dashes)
        self.ID = CANVAS.create_polygon(points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)

    def to_string(self):
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, xy=None, width=None, height=None, color=None, border_color=None, border_width=None, dashes=None):
        global CANVAS
        if not xy is None:
            self.xy = xy
        if not width is None:
            self.width = width
        if not height is None:
            self.height = height
        if not color is None:
            self.color = color
            if type(self.color) is tuple:
                self.color = rgb_convert(self.color)
        if not border_color is None:
            self.border_color = border_color
            if type(self.border_color) is tuple:
                self.border_color = rgb_convert(self.border_color)
        if not border_width is None:
            self.border_width = border_width
        if not dashes is None:
            self.dashes = dashes
            if not type(self.dashes) is tuple:
                self.dashes = (self.dashes, self.dashes)
        points = [
            self.xy[0], self.xy[1],
            self.xy[0] + self.width, self.xy[1],
            self.xy[0] + self.width, self.xy[1] + self.height,
            self.xy[0], self.xy[1] + self.height
        ]
        old_id = self.ID
        self.ID = CANVAS.create_polygon(points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        self.rotate(self.angle)

    def rotate(self, angle):
        global CANVAS
        global WINDOW
        self.angle += angle
        new_angle = math.radians(angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
        shape_points = CANVAS.coords(self.ID)
        count = 0
        point = []
        points = []
        for coord in shape_points:
            point.append(coord)
            if count % 2 == 1:
                points.append(list(point))
                point.clear()
            count += 1
        all_x = []
        all_y = []
        count = 0
        for coord in shape_points:
            if count % 2 == 0:
                all_x.append(coord)
            else:
                all_y.append(coord)
            count += 1
        center_x = sum(all_x) / len(all_x)
        center_y = sum(all_y) / len(all_y)
        new_points = []
        for x_old, y_old in points:
            x_old -= center_x
            y_old -= center_y
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append([x_new + center_x, y_new + center_y])
        old_id = self.ID
        self.ID = CANVAS.create_polygon(new_points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
    
    def erase(self):
        CANVAS.delete(self.ID)
    
    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


class RegPolygon:
    def __init__(self, nsides, center_xy, radius, color="black", border_color=None, border_width=0, dashes=None):
        global CANVAS
        self.nsides = nsides
        self.type = str(self.nsides) + "-Sided Regular Polygon"
        self.angle = 0
        self.center_xy = center_xy
        self.radius = radius
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        angle = 0
        angle_increment = 2*math.pi / self.nsides
        points = []
        for i in range(self.nsides):
            x = self.center_xy[0] + self.radius * math.cos(angle)
            points.append(x)
            y = self.center_xy[1] + self.radius * math.sin(angle)
            points.append(y)
            angle += angle_increment
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        if type(self.border_color) is tuple:
            self.border_color = rgb_convert(self.border_color)
        if not self.dashes is None and not type(self.dashes) is tuple:
            self.dashes = (self.dashes, self.dashes)
        self.ID = CANVAS.create_polygon(points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
    
    def to_string(self):
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, nsides=None, center_xy=None, radius=None, color=None, border_color=None, border_width=None, dashes=None):
        global CANVAS
        if not nsides is None:
            self.nsides = nsides
            self.type = str(self.nsides) + "-Sided Regular Polygon"
        if not center_xy is None:
            self.center_xy = center_xy
        if not radius is None:
            self.radius = radius
        if not color is None:
            self.color = color
            if type(self.color) is tuple:
                self.color = rgb_convert(self.color)
        if not border_color is None:
            self.border_color = border_color
            if type(self.border_color) is tuple:
                self.border_color = rgb_convert(self.border_color)
        if not border_width is None:
            self.border_width = border_width
        if not dashes is None:
            self.dashes = dashes
            if not type(self.dashes) is tuple:
                self.dashes = (self.dashes, self.dashes)
        angle = 0
        angle_increment = 2*math.pi / self.nsides
        points = []
        for i in range(self.nsides):
            x = self.center_xy[0] + self.radius * math.cos(angle)
            points.append(x)
            y = self.center_xy[1] + self.radius * math.sin(angle)
            points.append(y)
            angle += angle_increment
        old_id = self.ID
        self.ID = CANVAS.create_polygon(points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        self.rotate(self.angle)

    def rotate(self, angle):
        global CANVAS
        global WINDOW
        self.angle += angle
        new_angle = math.radians(angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
        shape_points = CANVAS.coords(self.ID)
        count = 0
        point = []
        points = []
        for coord in shape_points:
            point.append(coord)
            if count % 2 == 1:
                points.append(list(point))
                point.clear()
            count += 1
        all_x = []
        all_y = []
        count = 0
        for coord in shape_points:
            if count % 2 == 0:
                all_x.append(coord)
            else:
                all_y.append(coord)
            count += 1
        center_x = sum(all_x) / len(all_x)
        center_y = sum(all_y) / len(all_y)
        new_points = []
        for x_old, y_old in points:
            x_old -= center_x
            y_old -= center_y
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append([x_new + center_x, y_new + center_y])
        old_id = self.ID
        self.ID = CANVAS.create_polygon(new_points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
    
    def erase(self):
        CANVAS.delete(self.ID)
    
    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


class Polygon:
    def __init__(self, points_list, color="black", border_color=None, border_width=0, dashes=None):
        global CANVAS
        self.nsides = len(points_list)
        self.type = str(self.nsides) + "-Sided Polygon"
        self.angle = 0
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        if type(self.border_color) is tuple:
            self.border_color = rgb_convert(self.border_color)
        if not self.dashes is None and not type(self.dashes) is tuple:
            self.dashes = (self.dashes, self.dashes)
        self.ID = CANVAS.create_polygon(points_list, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
    
    def to_string(self):
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, points_list=None, color=None, border_color=None, border_width=None, dashes=None):
        global CANVAS
        if not points_list is None:
            self.points_list = points_list
            self.nsides = len(self.points_list)
            self.type = str(self.nsides) + "-Sided Polygon"
        if not color is None:
            self.color = color
            if type(self.color) is tuple:
                self.color = rgb_convert(self.color)
        if not border_color is None:
            self.border_color = border_color
            if type(self.border_color) is tuple:
                self.border_color = rgb_convert(self.border_color)
        if not border_width is None:
            self.border_width = border_width
        if not dashes is None:
            self.dashes = dashes
            if not type(self.dashes) is tuple:
                self.dashes = (self.dashes, self.dashes)
        old_id = self.ID
        self.ID = CANVAS.create_polygon(points_list, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        self.rotate(self.angle)

    def rotate(self, angle):
        global CANVAS
        global WINDOW
        self.angle += angle
        new_angle = math.radians(angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
        shape_points = CANVAS.coords(self.ID)
        count = 0
        point = []
        points = []
        for coord in shape_points:
            point.append(coord)
            if count % 2 == 1:
                points.append(list(point))
                point.clear()
            count += 1
        all_x = []
        all_y = []
        count = 0
        for coord in shape_points:
            if count % 2 == 0:
                all_x.append(coord)
            else:
                all_y.append(coord)
            count += 1
        center_x = sum(all_x) / len(all_x)
        center_y = sum(all_y) / len(all_y)
        new_points = []
        for x_old, y_old in points:
            x_old -= center_x
            y_old -= center_y
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append([x_new + center_x, y_new + center_y])
        old_id = self.ID
        self.ID = CANVAS.create_polygon(new_points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
    
    def erase(self):
        CANVAS.delete(self.ID)

    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


class Line:
    def __init__(self, xy1, xy2, color="black", thickness=5, dashes=None, arrow_start=False, arrow_end=False):
        global CANVAS
        self.type = "Line"
        self.angle = 0
        self.xy1 = xy1
        self.xy2 = xy2
        self.color = color
        self.thickness = thickness
        self.dashes = dashes
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end
        x1, y1 = self.xy1
        x2, y2 = self.xy2
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        if not self.dashes is None and not type(self.dashes) is tuple:
            self.dashes = (self.dashes, self.dashes)
        if self.arrow_start and self.arrow_end:
            self.ID = CANVAS.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.BOTH)
        elif self.arrow_start:
            self.ID = CANVAS.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.FIRST)
        elif self.arrow_end:
            self.ID = CANVAS.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.LAST)
        else:
            self.ID = CANVAS.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness, dash=self.dashes)
    
    def to_string(self):
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, xy1=None, xy2=None, color=None, thickness=None, dashes=None, arrow_start=None, arrow_end=None):
        global CANVAS
        if not xy1 is None:
            self.xy1 = xy1
        if not xy2 is None:
            self.xy2 = xy2
        if not color is None:
            self.color = color
            if type(self.color) is tuple:
                self.color = rgb_convert(self.color)
        if not thickness is None:
            self.thickness = thickness
        if not dashes is None:
            self.dashes = dashes
            if not type(self.dashes) is tuple:
                self.dashes = (self.dashes, self.dashes)
        if not arrow_start is None:
            self.arrow_start = arrow_start
        if not arrow_end is None:
            self.arrow_end = arrow_end
        x1, y1 = self.xy1
        x2, y2 = self.xy2
        old_id = self.ID
        if self.arrow_start and self.arrow_end:
            self.ID = CANVAS.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.BOTH)
        elif self.arrow_start:
            self.ID = CANVAS.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.FIRST)
        elif self.arrow_end:
            self.ID = CANVAS.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.LAST)
        else:
            self.ID = CANVAS.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        self.rotate(self.angle)
        

    def rotate(self, angle):
        global CANVAS
        global WINDOW
        self.angle += angle
        new_angle = math.radians(angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
        shape_points = CANVAS.coords(self.ID)
        count = 0
        point = []
        points = []
        for coord in shape_points:
            point.append(coord)
            if count % 2 == 1:
                points.append(list(point))
                point.clear()
            count += 1
        all_x = []
        all_y = []
        count = 0
        for coord in shape_points:
            if count % 2 == 0:
                all_x.append(coord)
            else:
                all_y.append(coord)
            count += 1
        center_x = sum(all_x) / len(all_x)
        center_y = sum(all_y) / len(all_y)
        new_points = []
        for x_old, y_old in points:
            x_old -= center_x
            y_old -= center_y
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append([x_new + center_x, y_new + center_y])
        old_id = self.ID
        if self.arrow_start and self.arrow_end:
            self.ID = CANVAS.create_line(new_points, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.BOTH)
        elif self.arrow_start:
            self.ID = CANVAS.create_line(new_points, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.FIRST)
        elif self.arrow_end:
            self.ID = CANVAS.create_line(new_points, fill=self.color, width=self.thickness, dash=self.dashes, arrow=tk.LAST)
        else:
            self.ID = CANVAS.create_line(new_points, fill=self.color, width=self.thickness, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
    
    def erase(self):
        CANVAS.delete(self.ID)

    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


class Arc:
    def __init__(self, center_xy, width, height, sweep_angle, color="black", border_color=None, border_width=0, dashes=None, style="pieslice"):
        global CANVAS
        self.type = "Arc"
        self.start_angle = 0
        self.center_xy = center_xy
        self.width = width
        self.height = height
        self.sweep_angle = sweep_angle
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.style = style
        center_x, center_y = self.center_xy
        x1 = center_x - (self.width / 2)
        y1 = center_y - (self.height / 2)
        x2 = center_x + (self.width / 2) 
        y2 = center_y + (self.height / 2)
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        if type(self.border_color) is tuple:
            self.border_color = rgb_convert(self.border_color)
        if not self.dashes is None and not type(self.dashes) is tuple:
            self.dashes = (self.dashes, self.dashes)
        if self.style.lower() == "chord":
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.CHORD)
        elif self.style.lower() == "arc":
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.ARC)
        else:
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.PIESLICE)
    
    def to_string(self):
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, center_xy=None, width=None, height=None, sweep_angle=None, color=None, border_color=None, border_width=None, dashes=None, style=None):
        global CANVAS
        if not center_xy is None:
            self.center_xy = center_xy
        if not width is None:
            self.width = width
        if not height is None:
            self.height = height
        if not sweep_angle is None:
            self.sweep_angle = sweep_angle
        if not color is None:
            self.color = color
            if type(self.color) is tuple:
                self.color = rgb_convert(self.color)
        if not border_color is None:
            self.border_color = border_color
            if type(self.border_color) is tuple:
                self.border_color = rgb_convert(self.border_color)
        if not border_width is None:
            self.border_width = border_width
        if not dashes is None:
            self.dashes = dashes
            if not type(self.dashes) is tuple:
                self.dashes = (self.dashes, self.dashes)
        if not style is None:
            self.style = style
        center_x, center_y = self.center_xy
        x1 = center_x - (self.width / 2)
        y1 = center_y - (self.height / 2)
        x2 = center_x + (self.width / 2) 
        y2 = center_y + (self.height / 2)
        old_id = self.ID
        if self.style.lower() == "chord":
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.CHORD)
        elif self.style.lower() == "arc":
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.ARC)
        else:
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.PIESLICE)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        self.rotate(self.start_angle)

    def rotate(self, angle):
        global CANVAS
        global WINDOW
        self.start_angle += angle
        center_x, center_y = self.center_xy
        x1 = center_x - (self.width / 2)
        y1 = center_y - (self.height / 2)
        x2 = center_x + (self.width / 2) 
        y2 = center_y + (self.height / 2)
        old_id = self.ID
        if self.style.lower() == "chord":
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.CHORD)
        elif self.style.lower() == "arc":
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.ARC)
        else:
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.PIESLICE)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
    
    def erase(self):
        CANVAS.delete(self.ID)

    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


class Circle:
    def __init__(self, center_xy, radius, color="black", border_color=None, border_width=0, dashes=None):
        global CANVAS
        self.type = "Circle"
        self.angle = 0
        self.center_xy = center_xy
        self.radius = radius
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        center_x, center_y = self.center_xy
        x1 = center_x - self.radius
        y1 = center_y - self.radius
        x2 = center_x + self.radius
        y2 = center_y + self.radius
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        if type(self.border_color) is tuple:
            self.border_color = rgb_convert(self.border_color)
        if not self.dashes is None and not type(self.dashes) is tuple:
            self.dashes = (self.dashes, self.dashes)
        self.ID = CANVAS.create_oval(x1, y1, x2, y2, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)

    def to_string(self):
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, center_xy=None, radius=None, color=None, border_color=None, border_width=None, dashes=None):
        global CANVAS
        if not center_xy is None:
            self.center_xy = center_xy
        if not radius is None:
            self.radius = radius
        if not color is None:
            self.color = color
            if type(self.color) is tuple:
                self.color = rgb_convert(self.color)
        if not border_color is None:
            self.border_color = border_color
            if type(self.border_color) is tuple:
                self.border_color = rgb_convert(self.border_color)
        if not border_width is None:
            self.border_width = border_width
        if not dashes is None:
            self.dashes = dashes
            if not type(self.dashes) is tuple:
                self.dashes = (self.dashes, self.dashes)
        center_x, center_y = self.center_xy
        x1 = center_x - self.radius
        y1 = center_y - self.radius
        x2 = center_x + self.radius
        y2 = center_y + self.radius
        old_id = self.ID
        self.ID = CANVAS.create_oval(x1, y1, x2, y2, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        self.rotate(self.angle)

    def rotate(self, angle):
        global CANVAS
        global WINDOW
        center_x, center_y = self.center_xy
        x1 = center_x - self.radius
        y1 = center_y - self.radius
        x2 = center_x + self.radius
        y2 = center_y + self.radius
        self.angle += angle
        new_angle = math.radians(angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
        shape_points = [x1, y1, x2, y2]
        count = 0
        point = []
        points = []
        for coord in shape_points:
            point.append(coord)
            if count % 2 == 1:
                points.append(list(point))
                point.clear()
            count += 1
        all_x = []
        all_y = []
        count = 0
        for coord in shape_points:
            if count % 2 == 0:
                all_x.append(coord)
            else:
                all_y.append(coord)
            count += 1
        center_x = sum(all_x) / len(all_x)
        center_y = sum(all_y) / len(all_y)
        new_points = []
        for x_old, y_old in points:
            x_old -= center_x
            y_old -= center_y
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append([x_new + center_x, y_new + center_y])
        old_id = self.ID
        self.ID = CANVAS.create_oval(new_points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)

    def erase(self):
        CANVAS.delete(self.ID)

    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


class Oval:
    def __init__(self, center_xy, width, height, color="black", border_color=None, border_width=0, dashes=None):
        global CANVAS
        self.type = "Oval"
        self.angle = 0
        self.center_xy = center_xy
        self.width = width
        self.height = height
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        center_x, center_y = self.center_xy
        x1 = center_x - (self.width / 2)
        y1 = center_y - (self.height / 2)
        x2 = center_x + (self.width / 2) 
        y2 = center_y + (self.height / 2)
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        if type(self.border_color) is tuple:
            self.border_color = rgb_convert(self.border_color)
        if not self.dashes is None and not type(self.dashes) is tuple:
            self.dashes = (self.dashes, self.dashes)
        self.ID = CANVAS.create_oval(x1, y1, x2, y2, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)

    def to_string(self):
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, center_xy=None, width=None, height=None, color=None, border_color=None, border_width=None, dashes=None):
        global CANVAS
        if not center_xy is None:
            self.center_xy = center_xy
        if not width is None:
            self.width = width
        if not height is None:
            self.height = height
        if not color is None:
            self.color = color
            if type(self.color) is tuple:
                self.color = rgb_convert(self.color)
        if not border_color is None:
            self.border_color = border_color
            if type(self.border_color) is tuple:
                self.border_color = rgb_convert(self.border_color)
        if not border_width is None:
            self.border_width = border_width
        if not dashes is None:
            self.dashes = dashes
            if not type(self.dashes) is tuple:
                self.dashes = (self.dashes, self.dashes)
        center_x, center_y = self.center_xy
        x1 = center_x - (self.width / 2)
        y1 = center_y - (self.height / 2)
        x2 = center_x + (self.width / 2) 
        y2 = center_y + (self.height / 2)
        old_id = self.ID
        self.ID = CANVAS.create_oval(x1, y1, x2, y2, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        self.rotate(self.angle)

    def rotate(self, angle):
        global CANVAS
        global WINDOW
        center_x, center_y = self.center_xy
        x1 = center_x - (self.width / 2)
        y1 = center_y - (self.height / 2)
        x2 = center_x + (self.width / 2) 
        y2 = center_y + (self.height / 2)
        self.angle += angle
        new_angle = math.radians(angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
        shape_points = [x1, y1, x2, y2]
        count = 0
        point = []
        points = []
        for coord in shape_points:
            point.append(coord)
            if count % 2 == 1:
                points.append(list(point))
                point.clear()
            count += 1
        all_x = []
        all_y = []
        count = 0
        for coord in shape_points:
            if count % 2 == 0:
                all_x.append(coord)
            else:
                all_y.append(coord)
            count += 1
        center_x = sum(all_x) / len(all_x)
        center_y = sum(all_y) / len(all_y)
        new_points = []
        for x_old, y_old in points:
            x_old -= center_x
            y_old -= center_y
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append([x_new + center_x, y_new + center_y])
        old_id = self.ID
        self.ID = CANVAS.create_oval(new_points, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
    
    def erase(self):
        CANVAS.delete(self.ID)
    
    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


# --- Text and Images ---

class Text:
    def __init__(self, center_xy, text="", color="black", font="Arial", size=16, bold=False, italic=False, underline=False, strikethrough=False):
        global CANVAS
        self.type = "Text"
        self.angle = 0
        self.center_xy = center_xy
        self.text = text
        self.color = color
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        self.font = font
        self.size = size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strikethrough = strikethrough
        style = ""
        if self.bold:
            style += "bold "
        if self.italic:
            style += "italic "
        if self.underline:
            style += "underline "
        if self.strikethrough:
            style += "overstrike "
        font_info = (self.font, self.size, style)
        x, y = self.center_xy
        self.ID = CANVAS.create_text(x, y, text=self.text, fill=self.color, font=font_info, angle=self.angle)

    def to_string(self):
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, center_xy=None, text=None, color=None, font=None, size=None, bold=None, italic=None, underline=None, strikethrough=None):
        global CANVAS
        if not center_xy is None:
            self.center_xy = center_xy
        if not text is None:
            self.text = text
        if not color is None:
            self.color = color
        if not font is None:
            self.font = font
        if not size is None:
            self.size = size
        if not bold is None:
            self.bold = bold
        if not italic is None:
            self.italic = italic
        if not underline is None:
            self.underline = underline
        if not strikethrough is None:
            self.strikethrough = strikethrough
        x, y = self.center_xy
        old_id = self.ID
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        style = ""
        if self.bold:
            style += "bold "
        if self.italic:
            style += "italic "
        if self.underline:
            style += "underline "
        if self.strikethrough:
            style += "overstrike "
        font_info = (self.font, self.size, style)
        self.ID = CANVAS.create_text(x, y, text=self.text, fill=self.color, font=font_info, angle=self.angle)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)


    def rotate(self, angle):
        global CANVAS
        global WINDOW
        self.angle += angle
        x, y = self.center_xy
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        style = ""
        if self.bold:
            style += "bold "
        if self.italic:
            style += "italic "
        if self.underline:
            style += "underline "
        if self.strikethrough:
            style += "overstrike "
        font_info = (self.font, self.size, style)
        old_id = self.ID
        self.ID = CANVAS.create_text(x, y, text=self.text, fill=self.color, font=font_info, angle=self.angle)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)

    def erase(self):
        CANVAS.delete(self.ID)
    
    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


def open_image(filename):
    img_file = tk.PhotoImage(file=filename)
    return img_file


class Image:
    def __init__(self, center_xy, image):
        global CANVAS
        self.type = "Image"
        self.angle = 0
        self.center_xy = center_xy
        self.image = image
        x, y = self.center_xy
        self.ID = CANVAS.create_image(x, y, image=self.image)
    
    def erase(self):
        CANVAS.delete(self.ID)
    
    def visible(self, value):
        if value:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def event_setup(self, event, handler):
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


# TkDocs https://tkdocs.com/shipman/

"""
Copyright (c) 2021 Joe Mazzone

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""