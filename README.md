# Easy Draw - Python Module

Full Documentation - https://easy-draw.joemazzone.net/

# Setup

It's easy!  Just download ```easy_draw.py``` and include it in your project directory. 

[Download!](https://github.com/MrMazzone/easy-draw/releases/download/v2.0.0/easy_draw.py)

Currently, the module is not on PyPI so it is not pip installable. Thus, you must download the ```easy_draw.py``` file.

Easy Draw only uses the Python standard library, so there is nothing else to install.

# Seeing Your Drawing

When your program runs, Easy Draw:

1. Writes your drawing to an ```index.html``` file in the same folder as your program.
2. Opens the live drawing in your web browser (http://localhost:8765/).

While your program is running, clicks, mouse movement, and key presses in the browser are sent to your event handlers. Open ```index.html``` any time to see your drawing again. Run your program again and the page goes live again.

Close the browser tab (or press Ctrl+C) to stop your program.

To print the finished page's HTML code, use ```easy_draw.end(print_html=True)```.

Options for ```load_canvas()```:

- ```port``` - The port for the live drawing. Default is ```8765```.
- ```open_browser``` - Set to ```False``` if you want to open the page yourself.

# What's New in 2.0

- Drawings show in the browser instead of a Tkinter window.
- ```Oval``` objects now rotate properly.
- ```Rectangle``` can rotate around its top-left corner: ```rect.rotate(45, from_top_left=True)```
- Every drawing object shares a ```Shape``` parent class.
- Properties can be changed directly: ```circle.radius = 50``` works like ```circle.set_property(radius = 50)```.
- ```Image``` objects can rotate.
- ```open_image()``` works with public image links: ```easy_draw.open_image("https://example.com/cat.png")```. The browser loads the image straight from the link, so viewing the drawing needs an internet connection.
- ```.rotate()``` turns every object clockwise, including ```Arc``` and ```Text```, which used to turn counterclockwise.
- Animations made with ```time.sleep()``` loops now show while they run.

# Java Version

```EasyDraw.java``` does the same thing for Java (Java 17 or newer). [Download it](https://github.com/MrMazzone/easy-draw/releases/download/v2.0.0/EasyDraw.java) and put it in the same folder as your program:

```java
public class Main {
    public static void main(String[] args) {
        EasyDraw.loadCanvas();

        EasyDraw.Rectangle square = new EasyDraw.Rectangle(100, 100, 200, 200);
        square.setColor("red");
        square.eventSetup("<Button-1>", event -> square.rotate(10));

        EasyDraw.end();
    }
}
```

Compile and run it with ```javac *.java``` and ```java Main```.

How it differs from the Python version:

- Shapes are made with ```new EasyDraw.ShapeName(...)``` and the required values in order, like ```new EasyDraw.Circle(centerX, centerY, radius)```.
- Optional properties use setters and getters, like ```setColor("red")```, ```setColor(255, 0, 0)```, ```setBorderWidth(5)```, and ```getRadius()```. Coordinates use methods like ```setCenter(x, y)``` and ```setXY(x, y)```.
- ```Polygon``` and ```Line``` take their points as numbers: ```new EasyDraw.Line(100, 100, 200, 200)```.
- Event handlers are lambdas: ```shape.eventSetup("<Button-1>", event -> { ... })```. The event strings are the same as Python's. The typed character is ```event.character```.
- ```setDashes(0)``` and ```setBorderColor(null)``` remove dashes and borders.
- Drawing errors throw an ```EasyDraw.EasyDrawException```.
- Files like images and ```index.html``` use the folder you run your program from.

# Desktop Version

The original Tkinter window version is still available as ```easy_draw_desktop.py```. It needs Tkinter and Pillow. Use it with ```import easy_draw_desktop as easy_draw```.

# What is Easy Draw?

Easy Draw is a easy to use Python module that allows you to create simple graphics primitives (rectangles, circles, polygons, etc.) with just Python function calls.

It is designed to be used with students that only know how to make function calls with Python code. 

After learning more about Python (conditionals, iteration, and functions definitions), students can use Easy Draw to make simple animations and games!

# About the Project
Easy Draw was created by [Joe Mazzone](https://www.linkedin.com/in/joe-mazzone/), Computer and Software Engineering instructor at William M. Davies, Jr. Career and Technical High School in Lincoln, Rhode Island. 

The project was created to introduce Davies' students to GUI development early in an introductory Python course.  GUIs are how students interact with software.  Let's get them to build GUIs earlier and generate more interest in Computer Science and programming!

Looking for a simple way to create an app with Python?  Check out the Easy App project: https://easy-app.joemazzone.net/

For more information about Davies Career and Technical High School, visit https://www.daviestech.org/
