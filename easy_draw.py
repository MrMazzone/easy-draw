#######################
# Hi students,
# DO NOT MESS AROUND WITH THIS FILE
# Please 😁
#######################

#######################
# Easy Draw Module
# Version 2.0.0
# Created by Joe Mazzone
# Documentation: https://easy-draw.joemazzone.net/
#######################

#######################
# This module was developed for students to easily create basic Python
# GUIs by drawing graphics primitives.  It features drawing functions
# for many shapes, as well as event handling for basic animations and games.
#
# Your drawing is shown in a web browser.  Easy Draw writes an index.html
# file next to your program and serves a live version of it while your
# program is running, so clicks and key presses reach your event handlers.
#
# Looking for the old Tkinter window version?  Use easy_draw_desktop.py.
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

import atexit
import base64
import json
import math
import os
import queue
import re
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "2.0.0"
HTML_FILE = "index.html"
CANVAS_SIZE = 600


class EasyDrawError(Exception):
    """Raised for error caused by not properly using Easy Draw."""
    def __init__(self, message="Seems you did something you shouldn't with Easy Draw..."):
        self.message = message
        super().__init__(self.message)


print("Welcome to Easy Draw! -- version " + VERSION + " -- https://easy-draw.joemazzone.net/")

POINTS_LIST_ERROR = EasyDrawError(
    message="The points_list must have an even number of values as it should contain xy coordinate pairs.")
LINE_COORDINATES_ERROR = EasyDrawError(
    message="You must use xy1 and xy2 OR a points_list to create a line.")
LINE_STYLE_ERROR = EasyDrawError(
    message="Line only supports \"round\" and \"cut\" as a style")

# --- Internal state ---
# Everything below is shared between your program and the little web server
# that talks to the browser, so it is guarded by _SCENE_LOCK.

_SCENE_LOCK = threading.RLock()
_HANDLER_LOCK = threading.RLock()   # Only one event handler runs at a time, like Tkinter.
_STOP = threading.Event()
_DIRTY = threading.Event()
_LOADED = False
_RUN_ID = str(int(time.time() * 1000))
_BACKGROUND = "white"
_SHAPES = {}            # ID -> shape, in drawing order (bottom to top)
_IMAGES = {}            # image ID -> data URI
_IMAGE_CACHE = {}       # absolute path -> ImageFile
_CANVAS_EVENTS = []     # (event spec, handler)
_CLIENTS = set()        # one queue per connected browser tab
_PENDING_SAVES = {}     # token -> save message
_NEXT_ID = 0
_SERVER = None
_PORT = None
_OUT_DIR = os.getcwd()


# --- Canvas functions ---

def load_canvas(background="white", *, port=8765, open_browser=True):
    """
    Starts Easy Draw with a 600x600px canvas.
    Must be called before instantiating drawing objects.

    Your drawing is written to index.html next to your program and opened in
    your web browser.  Use port to pick the local web server port and set
    open_browser=False if you want to open the page yourself.
    """
    global _LOADED, _BACKGROUND, _OUT_DIR
    with _SCENE_LOCK:
        _LOADED = True
        _BACKGROUND = _check_color("white" if background is None else background, "background")
        _SHAPES.clear()
        _CANVAS_EVENTS.clear()
        _OUT_DIR = _program_dir()
    _start_server(port)
    _write_html()
    threading.Thread(target=_writer_loop, daemon=True).start()
    print("Your drawing is saved to " + _html_path())
    if _SERVER is not None:
        print("Your live drawing is at " + _live_url())
        if open_browser:
            threading.Thread(target=_open_browser, daemon=True).start()


def set_canvas_color(color):
    """Used to set the background color of the drawing canvas."""
    global _BACKGROUND
    _require_canvas()
    with _SCENE_LOCK:
        _BACKGROUND = _check_color(color, "color")
        _broadcast({"type": "background", "background": _css_color(_BACKGROUND)})


def end(print_html=False):
    """
    Every Easy Draw program must end with this function call.
    Keeps your program running so the browser can send it events.
    Closing the browser tab (or pressing Ctrl+C) ends the program.
    Set print_html=True to print the finished page's HTML code.
    """
    _require_canvas()
    _write_html()
    if print_html:
        with _SCENE_LOCK:
            print(_build_html(live=False))
    if _SERVER is None:
        return
    print("Close your Easy Draw browser tab or press Ctrl+C to stop your program.")
    connected_before = False
    last_seen = time.time()
    try:
        while not _STOP.is_set():
            with _SCENE_LOCK:
                connected = len(_CLIENTS) > 0
                saving = len(_PENDING_SAVES) > 0
            now = time.time()
            if connected:
                connected_before = True
                last_seen = now
            elif connected_before and not saving and now - last_seen > 3:
                break
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    _write_html()


def save_canvas(name=None):
    """
    Saves the canvas as a PNG file next to your program.
    The picture is created by the browser, so the drawing must be open in a browser tab.
    """
    _require_canvas()
    if name is None:
        name = input("What would you like your picture's file name to be? ")
    name = str(name).strip()
    if name.lower().endswith(".png"):
        name = name[:-4]
    if name == "":
        return
    with _SCENE_LOCK:
        token = _new_id()
        message = {"type": "save", "token": token, "name": name, "scene": _snapshot()}
        _PENDING_SAVES[token] = message
        _broadcast(message, dirty=False)
        waiting = len(_CLIENTS) == 0
    if waiting:
        print("Saving " + name + ".png once your drawing is open in the browser...")


def canvas_event_setup(event, handler):
    """Used to setup an event for the entire canvas and not just a drawing object."""
    _require_canvas()
    spec = _parse_event(event)
    _check_handler(handler)
    with _SCENE_LOCK:
        _CANVAS_EVENTS.append((spec, handler))
        _broadcast({"type": "canvasEvents", "events": [s for s, _ in _CANVAS_EVENTS]})


def rgb_convert(rgb):
    """Used to convert an RGB color value to hex."""
    if len(rgb) != 3:
        raise EasyDrawError(message="RGB colors must have 3 values.")
    for value in rgb:
        if not _is_number(value) or value < 0 or value > 255:
            raise EasyDrawError(message="RGB values must be positive numbers and cannot exceed 255.")
    return "#%02x%02x%02x" % tuple(int(round(value)) for value in rgb)


class ImageFile:
    """An image file opened with open_image(). Give it to an Image object to draw it."""
    _TYPES = {
        ".png": "image/png", ".gif": "image/gif", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".bmp": "image/bmp", ".svg": "image/svg+xml",
    }

    def __init__(self, filename):
        path = _find_file(filename)
        extension = os.path.splitext(path)[1].lower()
        if extension not in self._TYPES:
            raise EasyDrawError("Easy Draw can open .png, .gif, .jpg, .webp, .bmp, and .svg images, not \"" + filename + "\".")
        with open(path, "rb") as file:
            data = base64.b64encode(file.read()).decode("ascii")
        self.filename = filename
        self.ID = _new_id()
        self._src = "data:" + self._TYPES[extension] + ";base64," + data


def open_image(filename):
    """Used to open an image file for Easy Draw to use."""
    path = os.path.abspath(_find_file(filename))
    with _SCENE_LOCK:
        if path not in _IMAGE_CACHE:
            image = ImageFile(filename)
            _IMAGE_CACHE[path] = image
            _IMAGES[image.ID] = image._src
            _broadcast({"type": "image", "id": image.ID, "src": image._src})
        return _IMAGE_CACHE[path]


class Event:
    """
    Information about an event. Easy Draw passes one to your event handler.

    Properties
    ----------
    x, y - The mouse position on the canvas, in pixels.
    x_root, y_root - The mouse position on the screen, in pixels.
    char - The character typed (keyboard events only), as a string.
    keysym - The key symbol, like "a", "Up", or "space" (keyboard events only).
    keycode - The key code (keyboard events only).
    num - The mouse button number (mouse button events only).
    delta - How far the mouse wheel moved (mouse wheel events only).
    type - The event type, like "ButtonPress" or "KeyPress".
    """
    _TYPE_NAMES = {
        "down": "ButtonPress", "double": "ButtonPress", "triple": "ButtonPress", "up": "ButtonRelease",
        "move": "Motion", "keydown": "KeyPress", "keyup": "KeyRelease", "enter": "Enter", "leave": "Leave",
        "focusin": "FocusIn", "focusout": "FocusOut", "wheel": "MouseWheel",
    }

    def __init__(self, spec, data):
        self.type = self._TYPE_NAMES.get(spec["t"], "")
        self.x = int(data.get("x", 0))
        self.y = int(data.get("y", 0))
        self.x_root = int(data.get("x_root", 0))
        self.y_root = int(data.get("y_root", 0))
        self.char = str(data.get("char", ""))
        self.keysym = str(data.get("keysym", "??"))
        self.keycode = data.get("keycode", "??")
        self.num = data.get("num", "??")
        self.delta = int(data.get("delta", 0))

    def __repr__(self):
        return "<Event " + self.type + " x=" + str(self.x) + " y=" + str(self.y) + ">"


# --- Drawing Shapes ---

class Shape:
    """
    The parent class of every Easy Draw drawing object.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance.
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas.
    .event_setup() - Used to bind an event and handler to the instance.

    Properties can also be changed directly, like shape.color = "red".
    """
    _PROPERTIES = ("visible", "angle")
    _STYLES = ()

    def __init__(self, type_name):
        _require_canvas()
        object.__setattr__(self, "_ready", False)
        object.__setattr__(self, "_erased", False)
        object.__setattr__(self, "_events", [])
        object.__setattr__(self, "_anchor_mode", "center")
        object.__setattr__(self, "_offset", (0, 0))
        object.__setattr__(self, "ID", _new_id())
        object.__setattr__(self, "type", type_name)
        self.angle = 0

    def __setattr__(self, name, value):
        if name in self._PROPERTIES:
            value = self._clean(name, value)
        object.__setattr__(self, name, value)
        if name in self._PROPERTIES:
            self._redraw()

    def to_string(self):
        """Used to print information about an instance."""
        return "Object: " + self.type + "\t ID: " + str(self.ID)

    def set_property(self, **properties):
        """Used to change one of the property values of an instance."""
        settable = self._settable()
        for name in properties:
            if name not in settable:
                raise EasyDrawError(self.type + " does not have a property called \"" + name + "\". "
                                    + "Properties you can set: " + ", ".join(settable))
        ready = self._ready
        object.__setattr__(self, "_ready", False)
        try:
            for name, value in properties.items():
                setattr(self, name, value)
        finally:
            object.__setattr__(self, "_ready", ready)
        self._redraw()

    def rotate(self, angle):
        """Used to rotate the shape by x degrees. Negative values rotate the opposite direction."""
        self._rotate(angle, "center")

    def erase(self):
        """Used to removed the instance from the canvas."""
        with _SCENE_LOCK:
            if self._erased:
                return
            object.__setattr__(self, "_erased", True)
            object.__setattr__(self, "_ready", False)
            _SHAPES.pop(self.ID, None)
            _broadcast({"type": "erase", "id": self.ID})

    def event_setup(self, event, handler):
        """Used to bind an event and handler to the instance."""
        spec = _parse_event(event)
        _check_handler(handler)
        self._events.append((spec, handler))
        self._redraw()

    # Everything below is used internally by Easy Draw.

    def _settable(self):
        return self._PROPERTIES

    def _show(self):
        """Adds the finished shape to the canvas."""
        with _SCENE_LOCK:
            object.__setattr__(self, "_ready", True)
            _SHAPES[self.ID] = self
            self._redraw()

    def _redraw(self):
        if self._ready and not self._erased:
            with _SCENE_LOCK:
                _broadcast({"type": "shape", "shape": self._to_dict()})

    def _center(self):
        raise NotImplementedError

    def _anchor(self, mode):
        return self._center()

    def _rotate(self, angle, mode):
        _check_number(angle, "angle")
        anchor = self._anchor(mode)
        # Keep the new anchor point where it is on screen, then turn around it.
        x, y = self._transform_point(anchor)
        object.__setattr__(self, "_offset", (x - anchor[0], y - anchor[1]))
        object.__setattr__(self, "_anchor_mode", mode)
        self.angle = self.angle + angle

    def _transform_point(self, point):
        """Where a point of the shape ends up after rotation."""
        ax, ay = self._anchor(self._anchor_mode)
        radians = math.radians(self.angle)
        dx = point[0] - ax
        dy = point[1] - ay
        return (dx * math.cos(radians) - dy * math.sin(radians) + ax + self._offset[0],
                dx * math.sin(radians) + dy * math.cos(radians) + ay + self._offset[1])

    def _to_dict(self):
        shape = self._geometry()
        shape.update({
            "id": self.ID,
            "visible": self.visible,
            "angle": _round(self.angle),
            "anchor": [_round(v) for v in self._anchor(self._anchor_mode)],
            "offset": [_round(v) for v in self._offset],
            "events": [spec for spec, _ in self._events],
        })
        return shape

    def _geometry(self):
        raise NotImplementedError

    def _paint(self):
        """Fill and border for shapes that have color, border_color, border_width, and dashes."""
        return {
            "fill": _css_color(self.color),
            "stroke": _css_color(self.border_color),
            "strokeWidth": _border_width(self.border_color, self.border_width),
            "dash": _dash_list(self.dashes),
        }

    def _clean(self, name, value):
        """Checks and tidies a property value before it is stored."""
        if name in ("color", "border_color"):
            if value is None and name == "border_color":
                return None
            return _check_color(value, name)
        if name == "dashes":
            if value is None:
                return None
            if _is_number(value):
                return (value, value)
            if isinstance(value, (tuple, list)) and all(_is_number(v) for v in value):
                return tuple(value)
            raise EasyDrawError("dashes must be a number, like dashes = 25.")
        if name in ("xy", "center_xy"):
            return _check_point(value, name)
        if name == "points_list":
            return _check_points(value)
        if name == "nsides":
            if not isinstance(value, int) or isinstance(value, bool) or value < 3:
                raise EasyDrawError("nsides must be a whole number that is 3 or more.")
            return value
        if name == "style":
            style = str(value).lower()
            if style not in self._STYLES:
                if self._STYLES == ("round", "cut"):
                    raise LINE_STYLE_ERROR
                raise EasyDrawError(self.type + " only supports these styles: " + ", ".join(self._STYLES))
            return style
        if name in ("visible", "bold", "italic", "underline", "strikethrough", "arrow_start", "arrow_end"):
            return bool(value)
        if name in ("text", "font"):
            return str(value)
        if name == "image":
            if isinstance(value, ImageFile):
                return value
            if isinstance(value, str):
                return open_image(value)
            raise EasyDrawError("image must be made with easy_draw.open_image(\"file_name.png\").")
        _check_number(value, name)
        return value


class Rectangle(Shape):
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
                Use .rotate(45, from_top_left=True) to turn it around its top-left corner instead of its center.
    .erase() - Used to removed the instance from the canvas.
    .event_setup() - Used to bind an event and handler to the instance.
    """
    _PROPERTIES = ("xy", "width", "height", "color", "border_color", "border_width", "dashes", "visible", "angle")

    def __init__(self, xy, width, height, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
        super().__init__("Rectangle")
        self.xy = xy
        self.width = width
        self.height = height
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.visible = visible
        self._show()

    def rotate(self, angle, from_top_left=False):
        """
        Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
        Set from_top_left=True to rotate around the top-left corner instead of the center.
        """
        self._rotate(angle, "top_left" if from_top_left else "center")

    def _anchor(self, mode):
        if mode == "top_left":
            return self.xy
        return self._center()

    def _center(self):
        return (self.xy[0] + self.width / 2, self.xy[1] + self.height / 2)

    def _geometry(self):
        x, y = self.xy
        shape = {"kind": "polygon", "points": _round_list([x, y, x + self.width, y,
                                                           x + self.width, y + self.height, x, y + self.height])}
        shape.update(self._paint())
        return shape


class RegPolygon(Shape):
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
    _PROPERTIES = ("nsides", "center_xy", "radius", "color", "border_color", "border_width", "dashes", "visible", "angle")

    def __init__(self, nsides, center_xy, radius, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
        super().__init__("Regular Polygon")
        self.nsides = nsides
        self.center_xy = center_xy
        self.radius = radius
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.visible = visible
        self._show()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "nsides":
            object.__setattr__(self, "type", str(self.nsides) + "-Sided Regular Polygon")

    def _center(self):
        return self.center_xy

    def _geometry(self):
        points = []
        for i in range(self.nsides):
            angle = 2 * math.pi * i / self.nsides
            points.append(self.center_xy[0] + self.radius * math.cos(angle))
            points.append(self.center_xy[1] + self.radius * math.sin(angle))
        shape = {"kind": "polygon", "points": _round_list(points)}
        shape.update(self._paint())
        return shape


class Polygon(Shape):
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
    _PROPERTIES = ("points_list", "color", "border_color", "border_width", "dashes", "visible", "angle")

    def __init__(self, points_list, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
        super().__init__("Polygon")
        self.points_list = points_list
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.visible = visible
        self._show()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "points_list":
            object.__setattr__(self, "nsides", len(self.points_list) // 2)
            object.__setattr__(self, "type", str(self.nsides) + "-Sided Polygon")

    def _center(self):
        return _average_point(self.points_list)

    def _geometry(self):
        shape = {"kind": "polygon", "points": _round_list(self.points_list)}
        shape.update(self._paint())
        return shape


class Line(Shape):
    """
    Draws a line using a starting xy coordinate and ending xy coordinate.

    Properties
    ----------
    xy1 - REQUIRED - The starting xy coordinate of the line as a tuple.
    xy2 - REQUIRED - The ending xy coordinate of the line as a tuple.
    points_list - Use instead of xy1 and xy2 to draw a line through many points.
    color - Default is black. RGB tuple color value, hexadecimal color value, or string containing color name can be used.
    thickness - Default is 5px. The width of the line.
    dashes - Default is None. Size of the dashes for the border in pixels.
    arrow_start - Default is False. Add an arrow to the start of the line.
    arrow_end - Default is False. Add an arrow to the end of the line.
    style - Default is "round". Use "cut" for square line ends.
    visible - Default is True. True = Shape can be seen. False = Shape cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance.
    .rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas.
    .event_setup() - Used to bind an event and handler to the instance.
    """
    _PROPERTIES = ("points_list", "color", "thickness", "dashes", "arrow_start", "arrow_end", "style", "visible", "angle")
    _STYLES = ("round", "cut")

    def __init__(self, xy1=None, xy2=None, *, points_list=None, color="black", thickness=5,
                 dashes=None, arrow_start=False, arrow_end=False, style="round", visible=True):
        super().__init__("Line")
        if points_list is None:
            if xy1 is None or xy2 is None:
                raise LINE_COORDINATES_ERROR
            points_list = list(_check_point(xy1, "xy1")) + list(_check_point(xy2, "xy2"))
        self.points_list = points_list
        self.color = color
        self.thickness = thickness
        self.dashes = dashes
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end
        self.style = style
        self.visible = visible
        self._show()

    @property
    def xy1(self):
        return tuple(self.points_list[0:2])

    @xy1.setter
    def xy1(self, value):
        self.points_list = list(_check_point(value, "xy1")) + self.points_list[2:]

    @property
    def xy2(self):
        return tuple(self.points_list[-2:])

    @xy2.setter
    def xy2(self, value):
        self.points_list = self.points_list[:-2] + list(_check_point(value, "xy2"))

    def _settable(self):
        return ("xy1", "xy2") + self._PROPERTIES

    def _center(self):
        return _average_point(self.points_list)

    def _geometry(self):
        return {
            "kind": "line",
            "points": _round_list(self.points_list),
            "color": _css_color(self.color),
            "width": self.thickness,
            "dash": _dash_list(self.dashes),
            "arrowStart": self.arrow_start,
            "arrowEnd": self.arrow_end,
            "style": self.style,
        }


class Circle(Shape):
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
    _PROPERTIES = ("center_xy", "radius", "color", "border_color", "border_width", "dashes", "visible", "angle")

    def __init__(self, center_xy, radius, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
        super().__init__("Circle")
        self.center_xy = center_xy
        self.radius = radius
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.visible = visible
        self._show()

    def _center(self):
        return self.center_xy

    def _geometry(self):
        shape = {"kind": "ellipse", "cx": _round(self.center_xy[0]), "cy": _round(self.center_xy[1]),
                 "rx": _round(self.radius), "ry": _round(self.radius)}
        shape.update(self._paint())
        return shape


class Oval(Shape):
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
    _PROPERTIES = ("center_xy", "width", "height", "color", "border_color", "border_width", "dashes", "visible", "angle")

    def __init__(self, center_xy, width, height, *, color="black", border_color=None, border_width=0, dashes=None, visible=True):
        super().__init__("Oval")
        self.center_xy = center_xy
        self.width = width
        self.height = height
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.visible = visible
        self._show()

    def _center(self):
        return self.center_xy

    def _geometry(self):
        shape = {"kind": "ellipse", "cx": _round(self.center_xy[0]), "cy": _round(self.center_xy[1]),
                 "rx": _round(self.width / 2), "ry": _round(self.height / 2)}
        shape.update(self._paint())
        return shape


class Arc(Shape):
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
    _PROPERTIES = ("center_xy", "width", "height", "sweep_angle", "color", "border_color", "border_width",
                   "dashes", "style", "visible", "angle")
    _STYLES = ("pieslice", "chord", "arc")

    def __init__(self, center_xy, width, height, sweep_angle, *,
                 color="black", border_color=None, border_width=0, dashes=None, style="pieslice", visible=True):
        super().__init__("Arc")
        self.center_xy = center_xy
        self.width = width
        self.height = height
        self.sweep_angle = sweep_angle
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.dashes = dashes
        self.style = style
        self.visible = visible
        self._show()

    def _center(self):
        return self.center_xy

    def _geometry(self):
        # Without a border_color, the arc's outline uses its color (the "arc" style is only an outline).
        stroke_color = self.color if self.border_color is None else self.border_color
        if self.style == "arc":
            fill = "none"
            stroke_width = max(self.border_width, 1)
        else:
            fill = _css_color(self.color)
            stroke_width = _border_width(self.border_color, self.border_width)
        return {
            "kind": "arc", "style": self.style,
            "cx": _round(self.center_xy[0]), "cy": _round(self.center_xy[1]),
            "rx": _round(self.width / 2), "ry": _round(self.height / 2),
            "start": 0, "extent": _round(self.sweep_angle),
            "fill": fill, "stroke": _css_color(stroke_color), "strokeWidth": stroke_width,
            "dash": _dash_list(self.dashes),
        }


# --- Text and Images ---

class Text(Shape):
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
    _PROPERTIES = ("center_xy", "text", "color", "font", "size", "bold", "italic", "underline",
                   "strikethrough", "visible", "angle")

    def __init__(self, center_xy, text="", *, color="black", font="Arial", size=16,
                 bold=False, italic=False, underline=False, strikethrough=False, visible=True):
        super().__init__("Text")
        self.center_xy = center_xy
        self.text = text
        self.color = color
        self.font = font
        self.size = size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strikethrough = strikethrough
        self.visible = visible
        self._show()

    def _center(self):
        return self.center_xy

    def _geometry(self):
        return {
            "kind": "text", "x": _round(self.center_xy[0]), "y": _round(self.center_xy[1]),
            "text": self.text, "color": _css_color(self.color), "font": self.font, "size": self.size,
            "bold": self.bold, "italic": self.italic, "underline": self.underline, "strike": self.strikethrough,
        }


class Image(Shape):
    """
    Draws an image from an image file.

    Properties
    ----------
    center_xy - REQUIRED - The center coordinate (x, y) of where to draw the image.
    image - REQUIRED - The image file to draw. Use the open_image() function to create the image object.
    visible - Default is True. True = Image can be seen. False = Image cannot be seen.

    Methods
    -------
    .to_string() - Used to print information about an instance.
    .set_property() - Used to change one of the property values of an instance.
    .rotate() - Used to rotate the image by x degrees. Negative values rotate the opposite direction.
    .erase() - Used to removed the instance from the canvas.
    .event_setup() - Used to bind an event and handler to the instance.
    """
    _PROPERTIES = ("center_xy", "image", "visible", "angle")

    def __init__(self, center_xy, image, *, visible=True):
        super().__init__("Image")
        self.center_xy = center_xy
        self.image = image
        self.visible = visible
        self._show()

    def _center(self):
        return self.center_xy

    def _geometry(self):
        return {"kind": "image", "x": _round(self.center_xy[0]), "y": _round(self.center_xy[1]), "img": self.image.ID}


# --- Internal helpers ---

def _require_canvas():
    if not _LOADED:
        raise EasyDrawError("You must call easy_draw.load_canvas() at the start of your program, before drawing anything.")


def _new_id():
    global _NEXT_ID
    with _SCENE_LOCK:
        _NEXT_ID += 1
        return _NEXT_ID


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_number(value, name):
    if not _is_number(value):
        raise EasyDrawError(name + " must be a number, not " + repr(value) + ".")
    return value


def _check_point(value, name):
    if not isinstance(value, (tuple, list)) or len(value) != 2 or not all(_is_number(v) for v in value):
        raise EasyDrawError(name + " must be an (x, y) coordinate, like " + name + " = (100, 200).")
    return tuple(value)


def _check_points(value):
    if not isinstance(value, (tuple, list)):
        raise EasyDrawError("points_list must be a list of numbers, like [50, 210, 180, 250, 300, 210].")
    points = []
    for item in value:
        if isinstance(item, (tuple, list)):
            points.extend(_check_point(item, "Each point"))
        elif _is_number(item):
            points.append(item)
        else:
            raise EasyDrawError("points_list must be a list of numbers, like [50, 210, 180, 250, 300, 210].")
    if len(points) % 2 != 0:
        raise POINTS_LIST_ERROR
    if len(points) < 4:
        raise EasyDrawError("points_list needs at least 2 points (4 numbers).")
    return points


def _check_color(value, name):
    if isinstance(value, (tuple, list)):
        return rgb_convert(value)
    if not isinstance(value, str):
        raise EasyDrawError(name + " must be a color name, a hex value like \"#FF0000\", or an RGB tuple like (255, 0, 0).")
    return value


def _check_handler(handler):
    if not callable(handler):
        raise EasyDrawError("The event handler must be the name of a function without parentheses, "
                            "like event_setup(\"<Button-1>\", my_function).")


def _css_color(color):
    """Turns a Tkinter style color into a color the browser understands."""
    if color is None or color == "":
        return "none"
    color = color.strip()
    if color.startswith("#"):
        digits = color[1:]
        if len(digits) in (9, 12):
            size = len(digits) // 3
            return "#" + "".join(digits[i * size:i * size + 2] for i in range(3))
        return color
    name = color.replace(" ", "").lower()
    gray = re.fullmatch(r"gr[ae]y(\d{1,3})", name)
    if gray and int(gray.group(1)) <= 100:
        return "#%02x%02x%02x" % ((round(int(gray.group(1)) * 2.55),) * 3)
    return name


def _border_width(border_color, border_width):
    if border_color is None or border_color == "":
        return 0
    return max(border_width, 1)


def _dash_list(dashes):
    return None if dashes is None else list(dashes)


def _round(value):
    value = round(value, 3)
    return int(value) if value == int(value) else value


def _round_list(values):
    return [_round(v) for v in values]


def _average_point(points):
    xs = points[0::2]
    ys = points[1::2]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _program_dir():
    main = sys.modules.get("__main__")
    path = getattr(main, "__file__", None)
    if path:
        return os.path.dirname(os.path.abspath(path))
    return os.getcwd()


def _find_file(filename):
    for folder in (os.getcwd(), _program_dir()):
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            return path
    raise EasyDrawError("Could not find the file \"" + str(filename) + "\". "
                        "Make sure it is in the same folder as your program.")


# --- Events ---

_EVENT_TYPES = {
    "Button": "down", "ButtonPress": "down", "ButtonRelease": "up", "Motion": "move",
    "Key": "keydown", "KeyPress": "keydown", "KeyRelease": "keyup",
    "Enter": "enter", "Leave": "leave", "FocusIn": "focusin", "FocusOut": "focusout",
    "MouseWheel": "wheel",
}
_MODIFIERS = {"Shift": "Shift", "Control": "Control", "Alt": "Alt", "Option": "Alt", "Meta": "Meta", "Command": "Meta"}
# Browser key names -> Tkinter key symbols
_KEY_KEYSYMS = {
    "ArrowUp": "Up", "ArrowDown": "Down", "ArrowLeft": "Left", "ArrowRight": "Right",
    "Enter": "Return", "Escape": "Escape", "Backspace": "BackSpace", "Tab": "Tab", "Delete": "Delete",
    "Home": "Home", "End": "End", "PageUp": "Prior", "PageDown": "Next", "Insert": "Insert",
    "CapsLock": "Caps_Lock",
}
# Typed characters -> Tkinter key symbols
_CHAR_KEYSYMS = {
    " ": "space", "!": "exclam", "\"": "quotedbl", "#": "numbersign", "$": "dollar", "%": "percent",
    "&": "ampersand", "'": "apostrophe", "(": "parenleft", ")": "parenright", "*": "asterisk", "+": "plus",
    ",": "comma", "-": "minus", ".": "period", "/": "slash", ":": "colon", ";": "semicolon", "<": "less",
    "=": "equal", ">": "greater", "?": "question", "@": "at", "[": "bracketleft", "\\": "backslash",
    "]": "bracketright", "^": "asciicircum", "_": "underscore", "`": "grave", "{": "braceleft", "|": "bar",
    "}": "braceright", "~": "asciitilde",
}
_KEYSYM_ALIASES = {"Page_Up": "Prior", "Page_Down": "Next", "Enter": "Return", "Esc": "Escape"}
_KNOWN_KEYSYMS = (set(_KEY_KEYSYMS.values()) | set(_CHAR_KEYSYMS.values())
                  | {side for key in ("Shift", "Control", "Alt", "Meta") for side in (key + "_L", key + "_R")}
                  | {"F" + str(n) for n in range(1, 25)})


def _parse_event(sequence):
    """Turns a Tkinter event string like "<Button-1>" into something the browser can match."""
    error = EasyDrawError("\"" + str(sequence) + "\" is not an event Easy Draw understands. "
                          "Try something like \"<Button-1>\", \"<Key>\", or \"<Up>\".")
    if not isinstance(sequence, str) or sequence == "":
        raise error
    if not (sequence.startswith("<") and sequence.endswith(">")):
        if len(sequence) == 1:
            return {"t": "keydown", "b": 0, "drag": 0, "k": _CHAR_KEYSYMS.get(sequence, sequence), "m": []}
        raise error
    tokens = sequence[1:-1].split("-")
    if "" in tokens:
        raise error
    modifiers = []
    clicks = 1
    drag = 0
    i = 0
    while i < len(tokens) - 1:
        token = tokens[i]
        if token in _MODIFIERS:
            modifiers.append(_MODIFIERS[token])
        elif token == "Double":
            clicks = 2
        elif token == "Triple":
            clicks = 3
        elif re.fullmatch(r"(B|Button)[1-3]", token):
            drag = int(token[-1])
        else:
            break
        i += 1
    rest = tokens[i:]
    if len(rest) > 2:
        raise error
    if rest[0] in _EVENT_TYPES:
        kind = _EVENT_TYPES[rest[0]]
        detail = rest[1] if len(rest) == 2 else None
    elif len(rest) == 1:
        detail = rest[0]
        kind = "down" if detail.isdigit() else "keydown"
    else:
        raise error
    spec = {"t": kind, "b": 0, "drag": drag, "k": None, "m": modifiers}
    if kind in ("down", "up"):
        if detail is not None:
            if not detail.isdigit() or not 1 <= int(detail) <= 5:
                raise error
            spec["b"] = int(detail)
        if clicks > 1:
            if kind != "down":
                raise error
            spec["t"] = "double" if clicks == 2 else "triple"
    elif kind in ("keydown", "keyup"):
        if detail is not None:
            keysym = _CHAR_KEYSYMS.get(detail, _KEYSYM_ALIASES.get(detail, detail))
            if len(keysym) != 1 and keysym not in _KNOWN_KEYSYMS:
                raise error
            spec["k"] = keysym
    elif detail is not None:
        raise error
    return spec


def _dispatch(body):
    """Runs the event handler the browser asked for."""
    if body.get("run") != _RUN_ID:
        return
    target = body.get("target")
    index = body.get("index")
    with _SCENE_LOCK:
        if target is None:
            bindings = _CANVAS_EVENTS
        else:
            shape = _SHAPES.get(target)
            if shape is None:
                return
            bindings = shape._events
        if not isinstance(index, int) or not 0 <= index < len(bindings):
            return
        spec, handler = bindings[index]
    event = Event(spec, body.get("event") or {})
    with _HANDLER_LOCK:
        try:
            handler(event)
        except SystemExit:
            _STOP.set()
        except Exception:
            traceback.print_exc()


# --- Talking to the browser ---

def _snapshot():
    return {
        "run": _RUN_ID,
        "background": _css_color(_BACKGROUND),
        "shapes": [shape._to_dict() for shape in _SHAPES.values()],
        "images": dict(_IMAGES),
        "canvasEvents": [spec for spec, _ in _CANVAS_EVENTS],
    }


def _broadcast(message, dirty=True):
    with _SCENE_LOCK:
        for client in _CLIENTS:
            client.put(message)
    if dirty:
        _DIRTY.set()


def _add_client():
    client = queue.Queue()
    with _SCENE_LOCK:
        client.put({"type": "scene", "scene": _snapshot()})
        for message in _PENDING_SAVES.values():
            client.put(message)
        _CLIENTS.add(client)
    return client


def _remove_client(client):
    with _SCENE_LOCK:
        _CLIENTS.discard(client)


def _receive_save(body):
    with _SCENE_LOCK:
        message = _PENDING_SAVES.pop(body.get("token"), None)
    data = str(body.get("data", ""))
    if message is None or "," not in data:
        return
    path = os.path.join(_OUT_DIR, message["name"] + ".png")
    with open(path, "wb") as file:
        file.write(base64.b64decode(data.split(",", 1)[1]))
    print("Saved " + path)


class _RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _empty(self, status):
        self.send_response(status)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_OPTIONS(self):
        self._empty(204)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            body = _build_html(live=True).encode("utf-8")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/events":
            self._stream()
        else:
            self._empty(404)

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self._empty(400)
            return
        if path == "/event":
            _dispatch(body)
        elif path == "/save":
            _receive_save(body)
        else:
            self._empty(404)
            return
        self._empty(204)

    def _stream(self):
        """Server-sent events: pushes drawing changes to the browser as they happen."""
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        client = _add_client()
        try:
            self.wfile.write(b"retry: 1000\n\n")
            while True:
                try:
                    messages = [client.get(timeout=1)]
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                while True:
                    try:
                        messages.append(client.get_nowait())
                    except queue.Empty:
                        break
                self.wfile.write(b"data: " + json.dumps(messages).encode("utf-8") + b"\n\n")
                self.wfile.flush()
        except OSError:
            pass
        finally:
            _remove_client(client)


def _start_server(port):
    global _SERVER, _PORT
    if _SERVER is not None:
        return
    for attempt in range(20):
        try:
            _SERVER = ThreadingHTTPServer(("127.0.0.1", port + attempt), _RequestHandler)
            break
        except OSError:
            continue
    if _SERVER is None:
        print("Easy Draw could not start its web server, so events will not work. "
              "Your drawing will still be saved to " + HTML_FILE + ".")
        return
    _SERVER.daemon_threads = True
    _PORT = _SERVER.server_address[1]
    threading.Thread(target=_SERVER.serve_forever, daemon=True).start()


def _live_url():
    return "http://localhost:" + str(_PORT) + "/"


def _open_browser():
    # Give a tab left open from an earlier run a moment to reconnect first.
    time.sleep(1.5)
    with _SCENE_LOCK:
        if _CLIENTS:
            return
    try:
        webbrowser.open(_live_url())
    except Exception:
        pass


def _html_path():
    return os.path.join(_OUT_DIR, HTML_FILE)


def _write_html():
    if not _LOADED:
        return
    with _SCENE_LOCK:
        html = _build_html(live=False)
    path = _html_path()
    temp = path + ".tmp"
    try:
        with open(temp, "w", encoding="utf-8") as file:
            file.write(html)
        os.replace(temp, path)
    except OSError as error:
        print("Easy Draw could not write " + path + ": " + str(error))


def _writer_loop():
    while True:
        _DIRTY.wait()
        time.sleep(0.5)
        _DIRTY.clear()
        _write_html()


atexit.register(_write_html)


def _build_html(live):
    if live:
        server = ""
    elif _PORT is not None:
        server = "http://localhost:" + str(_PORT)
    else:
        server = None
    data = {
        "config": {"server": server, "keys": _KEY_KEYSYMS, "chars": _CHAR_KEYSYMS, "version": VERSION},
        "scene": _snapshot(),
    }
    return _HTML_TEMPLATE.replace("__EASY_DRAW_DATA__", json.dumps(data).replace("</", "<\\/"))


_HTML_TEMPLATE = r'''<!DOCTYPE html>
<!-- Made with Easy Draw - https://easy-draw.joemazzone.net/ -->
<!-- This file is rewritten every time your program runs. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Easy Draw</title>
<style>
  :root { --blue: #07649E; --red: #E32636; --ink: #1d2733; --muted: #6b7785; --paper: #f4f6f8; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; background: var(--paper); color: var(--ink);
         font: 14px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
         display: flex; flex-direction: column; align-items: center; }
  .wrap { width: 100%; max-width: 700px; padding: 16px; }
  header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
  .brand { font-weight: 700; font-size: 18px; color: var(--blue); margin-right: auto; }
  button { font: inherit; font-weight: 700; color: #fff; background: var(--blue); border: 0;
           border-radius: 6px; padding: 7px 14px; cursor: pointer; }
  button:hover { filter: brightness(1.1); }
  button.on { background: var(--red); }
  .status { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px;
            background: #e3e7eb; color: var(--muted); }
  .status.live { background: #dff3e4; color: #1e7b3a; }
  #color-info { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; padding: 8px 12px;
                background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.12); }
  #color-info[hidden] { display: none; }
  #color-swatch { width: 28px; height: 28px; border-radius: 6px; border: 1px solid rgba(0,0,0,.2); }
  #color-info code { font-size: 14px; user-select: all; }
  #color-input { position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none; }
  #board { display: block; width: 100%; height: auto; touch-action: none; user-select: none; }
  #board .canvas { cursor: crosshair; }
  #board .label { font: 10px Arial, sans-serif; fill: var(--blue); }
  .hidden { display: none; }
  footer { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; color: var(--muted); }
  #coords { font: 700 15px Arial, sans-serif; color: var(--blue); }
  footer a { color: var(--muted); }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">Easy Draw</div>
    <button id="color-btn" type="button">Color Picker</button>
    <button id="grid-btn" type="button">Grid</button>
    <button id="save-btn" type="button">Save Canvas</button>
    <span id="status" class="status" title="Run your Python program to interact with the drawing.">Offline</span>
  </header>
  <div id="color-info" hidden>
    <div id="color-swatch"></div>
    <div>The color you chose is: <code id="color-hex"></code> &nbsp; <code id="color-rgb"></code></div>
  </div>
  <input id="color-input" type="color" value="#07649e" tabindex="-1">
  <svg id="board" viewBox="-36 -20 644 628" xmlns="http://www.w3.org/2000/svg">
    <defs><clipPath id="canvas-clip"><rect width="600" height="600"/></clipPath></defs>
    <g id="labels" class="hidden"></g>
    <g class="canvas" clip-path="url(#canvas-clip)">
      <rect id="background" width="600" height="600" fill="white"/>
      <g id="shapes"></g>
      <g id="grid" class="hidden" pointer-events="none"></g>
    </g>
    <rect x="-1" y="-1" width="602" height="602" fill="none" stroke="#9aa5b1" stroke-width="2" pointer-events="none"/>
  </svg>
  <footer>
    <a href="https://easy-draw.joemazzone.net/" target="_blank" rel="noopener">easy-draw.joemazzone.net</a>
    <span id="coords">(0, 0)</span>
  </footer>
</div>
<script type="application/json" id="easy-draw-data">__EASY_DRAW_DATA__</script>
<script>
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const DATA = JSON.parse(document.getElementById("easy-draw-data").textContent);
  const CFG = DATA.config;
  const $ = (id) => document.getElementById(id);
  const board = $("board"), shapesLayer = $("shapes"), background = $("background");

  let scene = null;          // current drawing
  const nodes = new Map();   // shape id -> SVG element
  const imageSizes = {};     // image id -> [width, height]
  const imageLoads = {};     // image id -> Promise
  let live = false;

  function el(tag, attrs) {
    const node = document.createElementNS(NS, tag);
    for (const key in attrs) {
      if (attrs[key] !== null && attrs[key] !== undefined) node.setAttribute(key, attrs[key]);
    }
    return node;
  }

  // ---------- Drawing ----------

  function strokeAttrs(s) {
    const on = s.stroke && s.stroke !== "none" && s.strokeWidth > 0;
    return {
      stroke: on ? s.stroke : "none",
      "stroke-width": on ? s.strokeWidth : null,
      "stroke-dasharray": on && s.dash ? s.dash.join(" ") : null,
    };
  }

  function arcPath(s) {
    const { cx, cy, rx, ry, start, extent } = s;
    if (extent === 0 || rx <= 0 || ry <= 0) return null;
    if (Math.abs(extent) >= 360) {
      return `M ${cx - rx} ${cy} A ${rx} ${ry} 0 1 0 ${cx + rx} ${cy} A ${rx} ${ry} 0 1 0 ${cx - rx} ${cy} Z`;
    }
    // Like Tkinter: angles start at 3 o'clock and positive sweeps go counterclockwise.
    const at = (deg) => [cx + rx * Math.cos(deg * Math.PI / 180), cy - ry * Math.sin(deg * Math.PI / 180)];
    const [x1, y1] = at(start), [x2, y2] = at(start + extent);
    const large = Math.abs(extent) > 180 ? 1 : 0, sweep = extent > 0 ? 0 : 1;
    const curve = `A ${rx} ${ry} 0 ${large} ${sweep} ${x2} ${y2}`;
    if (s.style === "pieslice") return `M ${cx} ${cy} L ${x1} ${y1} ${curve} Z`;
    if (s.style === "chord") return `M ${x1} ${y1} ${curve} Z`;
    return `M ${x1} ${y1} ${curve}`;
  }

  function arrowHead(tip, from, size) {
    // Returns [arrow polygon points, where the line should stop].
    const dx = tip[0] - from[0], dy = tip[1] - from[1];
    const len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len;
    const back = Math.min(size, len);
    const base = [tip[0] - ux * back, tip[1] - uy * back];
    const half = size * 0.45;
    const pts = [tip, [base[0] - uy * half, base[1] + ux * half], [base[0] + uy * half, base[1] - ux * half]];
    return [pts.map((p) => p.join(",")).join(" "), base];
  }

  function buildLine(s, g) {
    const pts = [];
    for (let i = 0; i + 1 < s.points.length; i += 2) pts.push([s.points[i], s.points[i + 1]]);
    if (pts.length < 2) return;
    const size = Math.max(10, s.width * 3);
    const heads = [];
    if (s.arrowEnd) {
      const [poly, base] = arrowHead(pts[pts.length - 1], pts[pts.length - 2], size);
      heads.push(poly); pts[pts.length - 1] = base;
    }
    if (s.arrowStart) {
      const [poly, base] = arrowHead(pts[0], pts[1], size);
      heads.push(poly); pts[0] = base;
    }
    const round = s.style !== "cut";
    g.append(el("polyline", {
      points: pts.map((p) => p.join(",")).join(" "), fill: "none", stroke: s.color, "stroke-width": s.width,
      "stroke-linecap": round ? "round" : "butt", "stroke-linejoin": round ? "round" : "bevel",
      "stroke-dasharray": s.dash ? s.dash.join(" ") : null,
    }));
    for (const poly of heads) g.append(el("polygon", { points: poly, fill: s.color }));
  }

  function buildText(s, g) {
    const decorations = [s.underline && "underline", s.strike && "line-through"].filter(Boolean).join(" ");
    const text = el("text", {
      x: s.x, y: s.y, fill: s.color, "font-family": s.font,
      "font-size": s.size < 0 ? -s.size + "px" : s.size + "pt",
      "font-weight": s.bold ? "bold" : null, "font-style": s.italic ? "italic" : null,
      "text-decoration": decorations || null, "text-anchor": "middle", "dominant-baseline": "central",
      style: "white-space: pre",
    });
    const lines = String(s.text).split("\n");
    if (lines.length === 1) {
      text.textContent = lines[0];
    } else {
      lines.forEach((line, i) => {
        const span = el("tspan", { x: s.x, dy: i === 0 ? -(lines.length - 1) * 0.6 + "em" : "1.2em" });
        span.textContent = line;
        text.append(span);
      });
    }
    g.append(text);
  }

  function build(s, images) {
    const transform = [];
    if (s.offset[0] || s.offset[1]) transform.push(`translate(${s.offset[0]} ${s.offset[1]})`);
    if (s.angle) transform.push(`rotate(${s.angle} ${s.anchor[0]} ${s.anchor[1]})`);
    const g = el("g", { "data-id": s.id, transform: transform.join(" ") || null, display: s.visible ? null : "none" });
    if (s.kind === "polygon") {
      const points = [];
      for (let i = 0; i + 1 < s.points.length; i += 2) points.push(s.points[i] + "," + s.points[i + 1]);
      g.append(el("polygon", Object.assign({ points: points.join(" "), fill: s.fill }, strokeAttrs(s))));
    } else if (s.kind === "ellipse") {
      g.append(el("ellipse", Object.assign({ cx: s.cx, cy: s.cy, rx: s.rx, ry: s.ry, fill: s.fill }, strokeAttrs(s))));
    } else if (s.kind === "arc") {
      const d = arcPath(s);
      if (d) g.append(el("path", Object.assign({ d: d, fill: s.fill }, strokeAttrs(s))));
    } else if (s.kind === "line") {
      buildLine(s, g);
    } else if (s.kind === "text") {
      buildText(s, g);
    } else if (s.kind === "image") {
      const size = imageSizes[s.img], src = images[s.img];
      if (size && src) {
        g.append(el("image", { href: src, x: s.x - size[0] / 2, y: s.y - size[1] / 2, width: size[0], height: size[1] }));
      }
    }
    return g;
  }

  function loadImage(id, src) {
    if (!imageLoads[id]) {
      imageLoads[id] = new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          imageSizes[id] = [img.naturalWidth || 150, img.naturalHeight || 150];
          if (scene) for (const s of scene.shapes.values()) if (s.kind === "image" && s.img == id) draw(s);
          resolve();
        };
        img.onerror = () => resolve();
        img.src = src;
      });
    }
    return imageLoads[id];
  }

  function draw(s) {
    const node = build(s, scene.images);
    const old = nodes.get(s.id);
    if (old) {
      old.replaceWith(node);
    } else {
      // Shapes stay in the order they were made, like layers.
      let before = null;
      for (const [id, other] of nodes) if (id > s.id && (!before || id < Number(before.dataset.id))) before = other;
      shapesLayer.insertBefore(node, before);
    }
    nodes.set(s.id, node);
  }

  function setScene(s) {
    scene = { run: s.run, background: s.background, images: s.images || {}, canvasEvents: s.canvasEvents || [], shapes: new Map() };
    nodes.clear();
    shapesLayer.replaceChildren();
    background.setAttribute("fill", scene.background);
    for (const id in scene.images) loadImage(id, scene.images[id]);
    for (const shape of s.shapes) { scene.shapes.set(shape.id, shape); draw(shape); }
  }

  function handle(msg) {
    if (msg.type === "scene") {
      setScene(msg.scene);
    } else if (msg.type === "shape") {
      scene.shapes.set(msg.shape.id, msg.shape);
      draw(msg.shape);
    } else if (msg.type === "erase") {
      scene.shapes.delete(msg.id);
      const node = nodes.get(msg.id);
      if (node) node.remove();
      nodes.delete(msg.id);
    } else if (msg.type === "background") {
      scene.background = msg.background;
      background.setAttribute("fill", msg.background);
    } else if (msg.type === "canvasEvents") {
      scene.canvasEvents = msg.events;
    } else if (msg.type === "image") {
      scene.images[msg.id] = msg.src;
      loadImage(msg.id, msg.src);
    } else if (msg.type === "save") {
      toPNG(msg.scene).then((data) => post("/save", { token: msg.token, data: data }));
    }
  }

  // ---------- Talking to Python ----------

  function post(path, body) {
    return fetch(CFG.server + path, { method: "POST", headers: { "Content-Type": "text/plain" }, body: JSON.stringify(body) });
  }

  const outbox = [];
  let sending = false;

  function send(item) {
    if (!live) return;
    const last = outbox[outbox.length - 1];
    // Only the newest mouse movement matters if Python is still busy.
    if (item.coalesce && last && last.coalesce && last.target === item.target && last.index === item.index) {
      outbox[outbox.length - 1] = item;
    } else {
      outbox.push(item);
    }
    pump();
  }

  async function pump() {
    if (sending) return;
    sending = true;
    while (outbox.length) {
      const item = outbox.shift();
      try {
        await post("/event", { run: scene.run, target: item.target, index: item.index, event: item.ev });
      } catch (err) { /* Python stopped; the status pill will show it. */ }
    }
    sending = false;
  }

  function setLive(on) {
    live = on;
    const status = $("status");
    status.textContent = on ? "Live" : "Offline";
    status.classList.toggle("live", on);
    status.title = on ? "Connected to your Python program." : "Run your Python program to interact with the drawing.";
  }

  function connect() {
    if (CFG.server === null || !window.EventSource) return;
    const source = new EventSource(CFG.server + "/events");
    source.onopen = () => setLive(true);
    source.onerror = () => setLive(false);
    source.onmessage = (m) => { for (const msg of JSON.parse(m.data)) handle(msg); };
  }

  // ---------- Events ----------

  const BUTTON_MASK = { 1: 1, 2: 4, 3: 2 };
  let hoverId = null, pressId = null, pressed = false, inCanvas = false;
  let lastPoint = { x: 0, y: 0 };
  const clicks = { count: 0, time: 0, x: 0, y: 0, num: 0 };

  function bindings(target) {
    if (target === null) return scene.canvasEvents;
    const s = scene.shapes.get(target);
    return s ? s.events : [];
  }

  function targetsFor(id) { return id === null ? [null] : [id, null]; }

  function modsOk(spec, e) {
    return spec.m.every((m) => ({ Shift: e.shiftKey, Control: e.ctrlKey, Alt: e.altKey, Meta: e.metaKey })[m]);
  }

  function fire(targets, test, ev, coalesce) {
    let count = 0;
    for (const target of targets) {
      bindings(target).forEach((spec, index) => {
        if (test(spec)) { send({ target, index, ev, coalesce }); count++; }
      });
    }
    return count;
  }

  function canvasPoint(e) {
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(shapesLayer.getScreenCTM().inverse());
    return { x: Math.round(p.x), y: Math.round(p.y) };
  }

  function inside(p) { return p.x >= 0 && p.y >= 0 && p.x <= 600 && p.y <= 600; }

  function shapeAt(e) {
    const hit = document.elementFromPoint(e.clientX, e.clientY);
    const g = hit && hit.closest ? hit.closest("[data-id]") : null;
    return g ? Number(g.dataset.id) : null;
  }

  function mouseEvent(e, p, extra) {
    return Object.assign({ x: p.x, y: p.y, x_root: Math.round(e.screenX), y_root: Math.round(e.screenY) }, extra);
  }

  function updateHover(e, p) {
    const nowInside = inside(p);
    const id = nowInside ? shapeAt(e) : null;
    const ev = mouseEvent(e, p, {});
    if (id !== hoverId) {
      if (hoverId !== null) fire([hoverId], (s) => s.t === "leave", ev);
      if (id !== null) fire([id], (s) => s.t === "enter", ev);
      hoverId = id;
    }
    if (nowInside !== inCanvas) {
      fire([null], (s) => s.t === (nowInside ? "enter" : "leave"), ev);
      inCanvas = nowInside;
    }
  }

  board.addEventListener("pointerdown", (e) => {
    const p = canvasPoint(e);
    if (!inside(p) || !scene) return;
    e.preventDefault();
    board.setPointerCapture(e.pointerId);
    const num = e.button + 1, now = performance.now();
    const again = num === clicks.num && now - clicks.time < 400 && Math.abs(p.x - clicks.x) < 5 && Math.abs(p.y - clicks.y) < 5;
    Object.assign(clicks, { count: again ? clicks.count + 1 : 1, time: now, x: p.x, y: p.y, num: num });
    pressed = true;
    pressId = shapeAt(e);
    const ev = mouseEvent(e, p, { num: num });
    const buttonOk = (s) => (s.b === 0 || s.b === num) && modsOk(s, e);
    for (const target of targetsFor(pressId)) {
      // A double click runs the "<Double-Button-1>" handler instead of "<Button-1>" when there is one.
      const list = bindings(target);
      let kind = "down";
      if (clicks.count >= 3 && list.some((s) => s.t === "triple" && buttonOk(s))) kind = "triple";
      else if (clicks.count >= 2 && list.some((s) => s.t === "double" && buttonOk(s))) kind = "double";
      fire([target], (s) => s.t === kind && buttonOk(s), ev);
    }
  });

  board.addEventListener("pointermove", (e) => {
    if (!scene) return;
    const p = canvasPoint(e);
    lastPoint = p;
    if (inside(p)) $("coords").textContent = `(${p.x}, ${p.y})`;
    if (!pressed) updateHover(e, p);
    if (!pressed && !inside(p)) return;
    const target = pressed ? pressId : hoverId;
    fire(targetsFor(target), (s) => s.t === "move" && (!s.drag || (e.buttons & BUTTON_MASK[s.drag])) && modsOk(s, e),
         mouseEvent(e, p, {}), true);
  });

  board.addEventListener("pointerup", (e) => {
    if (!pressed || !scene) return;
    const p = canvasPoint(e), num = e.button + 1;
    fire(targetsFor(pressId), (s) => s.t === "up" && (s.b === 0 || s.b === num) && modsOk(s, e), mouseEvent(e, p, { num: num }));
    pressed = false;
    pressId = null;
    updateHover(e, p);
  });

  board.addEventListener("pointercancel", () => { pressed = false; pressId = null; });

  board.addEventListener("pointerleave", (e) => { if (!pressed && scene) updateHover(e, { x: -1, y: -1 }); });

  board.addEventListener("wheel", (e) => {
    const p = canvasPoint(e);
    if (!inside(p) || !scene) return;
    const count = fire(targetsFor(shapeAt(e)), (s) => s.t === "wheel" && modsOk(s, e),
                       mouseEvent(e, p, { delta: Math.round(-e.deltaY) }));
    if (count) e.preventDefault();
  }, { passive: false });

  board.addEventListener("contextmenu", (e) => e.preventDefault());

  function keysym(e) {
    if (CFG.keys[e.key]) return CFG.keys[e.key];
    if (["Shift", "Control", "Alt", "Meta"].includes(e.key)) return e.key + (e.code.endsWith("Right") ? "_R" : "_L");
    if (e.key.length === 1) return CFG.chars[e.key] || e.key;
    return e.key;
  }

  function keyChar(e) {
    if (e.key.length === 1) return e.key;
    return { Enter: "\r", Tab: "\t", Backspace: "\b", Escape: "\x1b" }[e.key] || "";
  }

  function onKey(e, kind) {
    if (!scene || e.target.closest && e.target.closest("input, textarea")) return;
    const sym = keysym(e);
    const ev = { x: lastPoint.x, y: lastPoint.y, char: keyChar(e), keysym: sym, keycode: e.keyCode };
    const targets = [];
    for (const [id, s] of scene.shapes) if (s.events.some((spec) => spec.t === kind)) targets.push(id);
    targets.push(null);
    let count = 0;
    for (const target of targets) {
      // Like Tkinter, a handler for a specific key wins over a handler for every key.
      const exact = (s) => s.t === kind && s.k === sym && modsOk(s, e);
      const any = (s) => s.t === kind && s.k === null && modsOk(s, e);
      count += fire([target], bindings(target).some(exact) ? exact : any, ev);
    }
    if (count && !e.ctrlKey && !e.metaKey && !/^F\d+$/.test(e.key)) e.preventDefault();
  }

  window.addEventListener("keydown", (e) => onKey(e, "keydown"));
  window.addEventListener("keyup", (e) => onKey(e, "keyup"));
  window.addEventListener("focus", () => scene && fire([null], (s) => s.t === "focusin", lastPoint));
  window.addEventListener("blur", () => scene && fire([null], (s) => s.t === "focusout", lastPoint));

  // ---------- Toolbar ----------

  (function makeGrid() {
    const grid = $("grid"), labels = $("labels");
    for (let i = 50; i < 600; i += 50) {
      grid.append(el("line", { x1: 0, y1: i, x2: 600, y2: i, stroke: "#C2CCD0", "stroke-width": 1 }));
      grid.append(el("line", { x1: i, y1: 0, x2: i, y2: 600, stroke: "#C2CCD0", "stroke-width": 1 }));
    }
    for (let i = 0; i <= 600; i += 50) {
      const top = el("text", { x: i, y: -7, "text-anchor": "middle", class: "label" });
      top.textContent = i;
      const left = el("text", { x: -6, y: i, "text-anchor": "end", "dominant-baseline": "central", class: "label" });
      left.textContent = i;
      labels.append(top, left);
    }
  })();

  $("grid-btn").addEventListener("click", (e) => {
    const on = e.currentTarget.classList.toggle("on");
    $("grid").classList.toggle("hidden", !on);
    $("labels").classList.toggle("hidden", !on);
  });

  $("color-btn").addEventListener("click", () => $("color-input").click());
  $("color-input").addEventListener("input", (e) => {
    const hex = e.target.value.toUpperCase();
    const rgb = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
    $("color-swatch").style.background = hex;
    $("color-hex").textContent = hex;
    $("color-rgb").textContent = `RGB (${rgb.join(", ")})`;
    $("color-info").hidden = false;
  });

  async function toPNG(s) {
    await Promise.all(Object.keys(s.images).map((id) => loadImage(id, s.images[id])));
    const svg = el("svg", { width: 600, height: 600, viewBox: "0 0 600 600" });
    svg.append(el("rect", { width: 600, height: 600, fill: s.background }));
    for (const shape of s.shapes) svg.append(build(shape, s.images));
    const img = new Image();
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(svg));
    await img.decode();
    const canvas = document.createElement("canvas");
    canvas.width = 600;
    canvas.height = 600;
    canvas.getContext("2d").drawImage(img, 0, 0);
    return canvas.toDataURL("image/png");
  }

  $("save-btn").addEventListener("click", async () => {
    let name = prompt("What would you like your picture's file name to be?");
    if (!name || !name.trim()) return;
    name = name.trim().replace(/\.png$/i, "") + ".png";
    const link = document.createElement("a");
    link.download = name;
    link.href = await toPNG({ background: scene.background, shapes: [...scene.shapes.values()], images: scene.images });
    link.click();
  });

  setScene(DATA.scene);
  connect();
})();
</script>
</body>
</html>
'''


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
