#######################
# Hi students,
# DO NOT MESS AROUND WITH THIS FILE
# Please 😁
#######################

#######################
# Easy Draw Module
# Version 1.0.9
# Created by Joe Mazzone
# Documentation: https://easy-draw.joemazzone.net/
#######################

#######################
# This module was developed for students to easily create basic Python 
# GUIs by drawing graphics primitives.  It features drawing functions 
# for many shapes, as well as event handling for basic animations and games.
#######################

# Easy Draw Docstring
"""
Easy Draw module - Objects and function to easily create drawings.
    Objects:
        - Rectangle
        - RegPolygon
        - Polygon
        - Line
        - Arc
        - Circle
        - Oval
        - Text
        - Image
    Functions:
        - load_canvas()
        - end()
        - set_canvas_color()
        - save_canvas()
        - canvas_event_setup()
        - open_image()
        - rgb_convert()
"""

import tkinter as tk
import tkinter.colorchooser, tkinter.messagebox, tkinter.simpledialog
from PIL import ImageGrab
import math
import time


class __EasyDrawError(Exception):
    """Raised for error caused by not properly using Easy Draw."""
    def __init__(self, message="Seems you did something you shouldn't with Easy Draw..."):
        self.message = message
        super().__init__(self.message)


print("Welcome to Easy Draw! -- version 1.0.9 -- https://easy-draw.joemazzone.net/")
WINDOW = None
CANVAS = None
GRID_LINES = []
grid_on = False
POINTS_LIST_ERROR = __EasyDrawError(
    message="The points_list must have an even number of values as it should contain xy coordinate pairs.")


def load_canvas(background=None):
    """
    Opens Easy Draw window with a 600x600px canvas.
    Must be called before instantiating drawing objects.
    """
    global WINDOW
    global CANVAS
    global GRID_LINES
    global grid_on
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
            tkinter.messagebox.showinfo("Your Color", 
                                        "The color you chose is: " + "\n\n" + color[1] + "\n\n" + "RBG (" + str(int(color[0][0])) 
                                        + ", " + str(int(color[0][1])) + ", " + str(int(color[0][2])) + ")")
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
        global grid_on
        if grid_on:
            grid_on = False
            grid_button["text"] = "Grid"
            grid_button["bg"] = "#07649E"
            for line in GRID_LINES:
                CANVAS.itemconfig(line, state = tk.HIDDEN)
            for label in x_labels:
                label.configure(fg = WINDOW.cget("background"))
            for label in y_labels:
                label.configure(fg = WINDOW.cget("background"))
        else:
            grid_on = True
            grid_button["text"] = "Grid"
            grid_button["bg"] = "#E32636"
            for line in GRID_LINES:
                CANVAS.itemconfig(line, state = tk.DISABLED)
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
        y_labels.append(tk.Label(text = "      " + str(i), fg = window_bg, font=("Arial", 8), padx=0, pady=0))
    count = 1
    for label in x_labels:
        label.grid(column=count, row=2, sticky="sw")
        count += 1
    count = 3
    for label in y_labels:
        label.grid(column=0, row=count, sticky="ne")
        count += 1
    spacer1 = tk.Label(text = " ", font=("Arial", 2))
    spacer1.grid(column=15, row=3, sticky="w", padx=6)


def set_canvas_color(color):
    """Used to set the background color of the drawing canvas."""
    global CANVAS
    if type(color) is tuple:
        color = rgb_convert(color)
    CANVAS.configure(bg = color)


def end():
    """
    Every Easy Draw program must end with this function call.
    Sets up event loop and other important aspects of Easy Draw.
    """
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
    """Should only be used internally! Grabs canvas image."""
    global WINDOW
    global CANVAS
    global grid_on
    x = WINDOW.winfo_rootx() + CANVAS.winfo_x()
    y = WINDOW.winfo_rooty() + CANVAS.winfo_y()
    x1 = x + CANVAS.winfo_width()
    y1 = y + CANVAS.winfo_height()
    ImageGrab.grab().crop((x,y,x1,y1)).save(filename + ".png")
    if grid_on:
        for line in GRID_LINES:
            CANVAS.itemconfig(line, state = tk.NORMAL)


def save_canvas(name = None):
    """Used to save the canvas without pressing the save button."""
    global WINDOW
    global CANVAS
    global GRID_LINES
    for line in GRID_LINES:
        CANVAS.itemconfig(line, state = tk.HIDDEN)
    if name is None:
        name = tkinter.simpledialog.askstring("Save File", "What would you like your picture's file name to be?", parent=WINDOW)
    if (not name is None) and (name != ""):
        print("Saving " + name + ".png ", end="")
        for i in range(5):
            time.sleep(0.25)
            print(".", end="")
        print("")
        WINDOW.after(250, __screenshot__(name))
    

def canvas_event_setup(event, handler):
    """Used to setup an event for the entire canvas and not just a drawing object."""
    global CANVAS
    CANVAS.bind_all(event, handler)


def rgb_convert(rgb):
    """Used to convert an RGB color value to hex."""
    if len(rgb) != 3:
        raise __EasyDrawError(message = "RGB colors must have 3 values.")
    elif (rgb[0] >= 0 and rgb[0] <= 255) and (rgb[1] >= 0 and rgb[1] <= 255) and (rgb[2] >= 0 and rgb[2] <= 255):
        return '#%02x%02x%02x' % rgb
    else:
        raise __EasyDrawError(message = "RGB values must be positive numbers and cannot exceed 255.")


# --- Drawing Shapes ---

class Rectangle:
    """
    Draws a rectangle from the top-left corner (x, y) with a given width and height.

    Properties
    ----------
    xy - REQUIRED - The x and y coordinate of the rectangle's top-left corner as a tuple.
    width - REQUIRED - The width of the rectangle in pixels.
    height - REQUIRED - The height of the rectangle in pixels.
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used. 
    border_color - Default is None. Color of the border.
    border_width - Default is 0px. Size of the border in pixels. 
    dashes - Default is None. Size of the dashes for the border in pixels.
    visible - Default is True. True = Shape can be seen. False = Shape cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """
    def __init__(self, xy, width, height, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
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
        self.visible = visible
        self.event_list = []
        self.handle_list = []
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, *, xy=None, width=None, height=None, color=None, border_color=None, border_width=None, dashes=None, visible=None):
        """Used to change one of the property values of an instance."""
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
        if not visible is None:
            self.visible = visible
        self.rotate(0)

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
        global CANVAS
        global WINDOW
        self.angle += angle
        shape_points = [
            self.xy[0], self.xy[1],
            self.xy[0] + self.width, self.xy[1],
            self.xy[0] + self.width, self.xy[1] + self.height,
            self.xy[0], self.xy[1] + self.height
        ]
        new_angle = math.radians(self.angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])
    
    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)
        self.event_list.append(event)
        self.handle_list.append(handler)


class RegPolygon:
    """
    Draws a regular polygon, n sided shape with equal sides.

    Properties
    ----------
    nsides - REQUIRED - The number of sides the polygon has.
    center_xy - REQUIRED - The x and y coordinate of the polygon's center as a tuple.
    radius - REQUIRED - The distance in pixels from the center to any outer point.
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used. 
    border_color - Default is None. Color of the border.
    border_width - Default is 0px. Size of the border in pixels. 
    dashes - Default is None. Size of the dashes for the border in pixels.
    visible - Default is True. True = Shape can be seen. False = Shape cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """
    def __init__(self, nsides, center_xy, radius, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
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
        self.visible = visible
        self.event_list = []
        self.handle_list = []
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
    
    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, *, nsides=None, center_xy=None, radius=None, color=None, border_color=None, border_width=None, dashes=None, visible=None):
        """Used to change one of the property values of an instance."""
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
        if not visible is None:
            self.visible = visible
        self.rotate(0)

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
        global CANVAS
        global WINDOW
        self.angle += angle
        draw_angle = 0
        angle_increment = 2*math.pi / self.nsides
        shape_points = []
        for i in range(self.nsides):
            x = self.center_xy[0] + self.radius * math.cos(draw_angle)
            shape_points.append(x)
            y = self.center_xy[1] + self.radius * math.sin(draw_angle)
            shape_points.append(y)
            draw_angle += angle_increment
        new_angle = math.radians(self.angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])
    
    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)
        self.event_list.append(event)
        self.handle_list.append(handler)


class Polygon:
    """
    Draws a polygon using a list of points.

    Properties
    ----------
    points_list - REQUIRED - A list of x y coordinates identifying the points of the polygon. List must have an even number of values.
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used. 
    border_color - Default is None. Color of the border.
    border_width - Default is 0px. Size of the border in pixels. 
    dashes - Default is None. Size of the dashes for the border in pixels.
    visible - Default is True. True = Shape can be seen. False = Shape cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """
    def __init__(self, points_list, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
        global CANVAS
        global POINTS_LIST_ERROR
        if len(points_list) % 2 != 0:
            raise POINTS_LIST_ERROR
        self.points_list = points_list
        self.nsides = len(points_list)
        self.type = str(self.nsides) + "-Sided Polygon"
        self.angle = 0
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.visible = visible
        self.event_list = []
        self.handle_list = []
        if type(self.color) is tuple:
            self.color = rgb_convert(self.color)
        if type(self.border_color) is tuple:
            self.border_color = rgb_convert(self.border_color)
        if not self.dashes is None and not type(self.dashes) is tuple:
            self.dashes = (self.dashes, self.dashes)
        self.ID = CANVAS.create_polygon(self.points_list, fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes)
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
    
    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, *, points_list=None, color=None, border_color=None, border_width=None, dashes=None, visible=None):
        """Used to change one of the property values of an instance."""
        global CANVAS
        global POINTS_LIST_ERROR
        if not points_list is None:
            if len(points_list) % 2 != 0:
                raise POINTS_LIST_ERROR
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
        if not visible is None:
            self.visible = visible
        self.rotate(0)

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
        global CANVAS
        global WINDOW
        self.angle += angle
        new_angle = math.radians(self.angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
        shape_points = self.points_list
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])
    
    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)
        self.event_list.append(event)
        self.handle_list.append(handler)


class Line:
    """
    Draws a line using a starting xy coordinate and ending xy coordinate.

    Properties
    ----------
    xy1 - REQUIRED - The starting xy coordinate of the line as a tuple.
    xy2 - REQUIRED - The ending xy coordinate of the line as a tuple.
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used. 
    thickness - Default is 5px. The width of the line.
    dashes - Default is None. Size of the dashes for the border in pixels.
    arrow_start - Default is False. Add an arrow to the start of the line.
    arrow_end - Default is False. Add an arrow to the end of the line.
    visible - Default is True. True = Shape can be seen. False = Shape cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """
    def __init__(self, xy1, xy2, *, color="black", thickness=5, dashes=None, arrow_start=False, arrow_end=False, visible=True):
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
        self.visible = visible
        self.event_list = []
        self.handle_list = []
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
    
    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, *, xy1=None, xy2=None, color=None, thickness=None, dashes=None, arrow_start=None, arrow_end=None, visible=None):
        """Used to change one of the property values of an instance."""
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
        if not visible is None:
            self.visible = visible
        self.rotate(0)

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
        global CANVAS
        global WINDOW
        self.angle += angle
        new_angle = math.radians(self.angle)
        cos_val = math.cos(new_angle)
        sin_val = math.sin(new_angle)
        x1, y1 = self.xy1
        x2, y2 = self.xy2
        shape_points = (x1, y1, x2, y2)
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])
    
    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)
        self.event_list.append(event)
        self.handle_list.append(handler)


class Circle:
    """
    Draws a circle with a center coordinate and a radius.

    Properties
    ----------
    center_xy - REQUIRED - The center coordinate (x, y) of the circle.
    radius - REQUIRED - The measurement in pixels from the center of the circle to the edge.
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used. 
    border_color - Default is None. Color of the border.
    border_width - Default is 0px. Size of the border in pixels. 
    dashes - Default is None. Size of the dashes for the border in pixels.
    visible - Default is True. True = Shape can be seen. False = Shape cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """
    def __init__(self, center_xy, radius, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
        global CANVAS
        self.type = "Circle"
        self.angle = 0
        self.center_xy = center_xy
        self.radius = radius
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.visible = visible
        self.event_list = []
        self.handle_list = []
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, *, center_xy=None, radius=None, color=None, border_color=None, border_width=None, dashes=None, visible=None):
        """Used to change one of the property values of an instance."""
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
        if not visible is None:
            self.visible = visible
        self.rotate(0)

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
        global CANVAS
        global WINDOW
        center_x, center_y = self.center_xy
        x1 = center_x - self.radius
        y1 = center_y - self.radius
        x2 = center_x + self.radius
        y2 = center_y + self.radius
        self.angle += angle
        new_angle = math.radians(self.angle)
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])

    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)
        self.event_list.append(event)
        self.handle_list.append(handler)


class Oval:
    """
    Draws an oval with a center coordinate, a width, and a height.

    Properties
    ----------
    center_xy - REQUIRED - The center coordinate (x, y) of the oval.
    width - REQUIRED - The measurement in pixels of the left edge to the right edge of the oval.
    height - REQUIRED - The measurement in pixels of the top edge to the bottom edge of the oval.
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used. 
    border_color - Default is None. Color of the border.
    border_width - Default is 0px. Size of the border in pixels. 
    dashes - Default is None. Size of the dashes for the border in pixels.
    visible - Default is True. True = Shape can be seen. False = Shape cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """
    def __init__(self, center_xy, width, height, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
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
        self.visible = visible
        self.event_list = []
        self.handle_list = []
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, *, center_xy=None, width=None, height=None, color=None, border_color=None, border_width=None, dashes=None, visible=None):
        """Used to change one of the property values of an instance."""
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
        if not visible is None:
            self.visible = visible
        self.rotate(0)

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
        global CANVAS
        global WINDOW
        center_x, center_y = self.center_xy
        x1 = center_x - (self.width / 2)
        y1 = center_y - (self.height / 2)
        x2 = center_x + (self.width / 2) 
        y2 = center_y + (self.height / 2)
        self.angle += angle
        new_angle = math.radians(self.angle)
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])
    
    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)        

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)
        self.event_list.append(event)
        self.handle_list.append(handler)


class Arc:
    """
    Draws a arc using a slice of a circle. 

    Properties
    ----------
    center_xy - REQUIRED - The center coordinate (x, y) of the circle used to create the arc.
    width - REQUIRED - The width of the circle used to create the arc.
    height - REQUIRED - The height of the circle used to create the arc.
    sweep_angle - REQUIRED - The amount of the arc to show. From 0 to the angle in degrees identified. 
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used. 
    border_color - Default is None. Color of the border.
    border_width - Default is 0px. Size of the border in pixels. 
    dashes - Default is None. Size of the dashes for the border in pixels.
    style - Default is "pieslice". The arc comes in three styles choices: "pieslice", "chord", and "arc"
    visible - Default is True. True = Shape can be seen. False = Shape cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """

    def __init__(self, center_xy, width, height, sweep_angle, *,
                 color="black", border_color=None, border_width=0, dashes=None, style="pieslice", visible=True):
        global CANVAS
        self.type = "Arc"
        self.start_angle = 0
        self.center_xy = center_xy
        self.width = width
        self.height = height
        self.sweep_angle = sweep_angle
        self.color = color
        if border_color is None:
            self.border_color = self.color
            self.has_border = False
        else:
            self.border_color = border_color
            self.has_border = True
        self.border_width = border_width
        self.dashes = dashes
        self.style = style
        self.visible = visible
        self.event_list = []
        self.handle_list = []
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
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color,
                                        outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.CHORD)
        elif self.style.lower() == "arc":
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle,
                                        fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.ARC)
        else:
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color,
                                        outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.PIESLICE)
        if self.visible:
            CANVAS.itemconfig(self.ID, state=tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state=tk.HIDDEN)

    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)

    def set_property(self, *, center_xy=None, width=None, height=None, sweep_angle=None, color=None, border_color=None, border_width=None, dashes=None, style=None, visible=None):
        """Used to change one of the property values of an instance."""
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
            if not self.has_border:
                self.border_color = self.color
        if not border_color is None:
            self.has_border = True
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
        if not visible is None:
            self.visible = visible
        self.rotate(0)

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
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
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color,
                                        outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.CHORD)
        elif self.style.lower() == "arc":
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle,
                                        fill=self.color, outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.ARC)
        else:
            self.ID = CANVAS.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=self.sweep_angle, fill=self.color,
                                        outline=self.border_color, width=self.border_width, dash=self.dashes, style=tk.PIESLICE)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        if self.visible:
            CANVAS.itemconfig(self.ID, state=tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state=tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])

    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)
        self.event_list.append(event)
        self.handle_list.append(handler)


# --- Text and Images ---

class Text:
    """
    Draws text from a center coordinate.

    Properties
    ----------
    center_xy - REQUIRED - The center coordinate (x, y) of where to draw the text.
    text - Default is ""/empty string. The text you want to display.
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used. 
    font - Default is Arial. The font family used for the text. Font must be installed on machine to be used. 
    size - Default is 16. The font size of the text.
    bold - Default is False. When set to True, it bolds the text.
    italic - Default is False. When set to True, it italicizes the text.
    underline - Default is False. When set to True, it underlines the text.
    strikethrough - Default is False. When set to True, it strikes-out the text.
    visible - Default is True. True = Text can be seen. False = Text cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """
    def __init__(self, center_xy, text="", *, color="black", font="Arial", size=16, 
                bold=False, italic=False, underline=False, strikethrough=False, visible=True):
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
        self.visible = visible
        self.event_list = []
        self.handle_list = []
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)
    
    def set_property(self, *, center_xy=None, text=None, color=None, font=None, size=None, bold=None, italic=None, underline=None, strikethrough=None, visible=None):
        """Used to change one of the property values of an instance."""
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
        if not visible is None:
            self.visible = visible
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
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
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)
        for i in range(len(self.event_list)):
            CANVAS.tag_bind(self.ID, self.event_list[i], self.handle_list[i])

    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


def open_image(filename):
    """Used to open an image file for Easy Draw to use."""
    img_file = tk.PhotoImage(file=filename)
    return img_file


class Image:
    """
    Draws an image from an image file.

    Properties
    ----------
    center_xy - REQUIRED - The center coordinate (x, y) of where to draw the image.
    image - REQUIRED - The image file to draw. Must use the open_image() function to create the required image object.
    visible - Default is True. True = Image can be seen. False = Image cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance. 
    .erase() - Used to removed the instance from the canvas. 
    .event_setup() - Used to bind an event and handler to the instance.
    """
    def __init__(self, center_xy, image, *, visible=True):
        global CANVAS
        self.type = "Image"
        self.angle = 0
        self.center_xy = center_xy
        self.image = image
        self.visible = visible
        x, y = self.center_xy
        self.ID = CANVAS.create_image(x, y, image=self.image)
    
    def set_property(self, *, center_xy=None, image=None, visible=None):
        """Used to change one of the property values of an instance."""
        global CANVAS
        if not center_xy is None:
            self.center_xy = center_xy
        if not image is None:
            self.image = image
        if not visible is None:
            self.visible = visible
        old_id = self.ID
        x, y = self.center_xy
        self.ID = CANVAS.create_image(x, y, image=self.image)
        CANVAS.tag_lower(self.ID, old_id)
        CANVAS.delete(old_id)
        if self.visible:
            CANVAS.itemconfig(self.ID, state = tk.NORMAL)
        else:
            CANVAS.itemconfig(self.ID, state = tk.HIDDEN)

    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)

    def erase(self):
        """Used to removed the instance from the canvas."""
        CANVAS.delete(self.ID)

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        global CANVAS
        CANVAS.tag_bind(self.ID, event, handler)


# TkDocs https://tkdocs.com/shipman/

"""
MIT License
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
