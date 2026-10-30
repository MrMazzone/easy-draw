/////////////////////////
// Hi students,
// DO NOT MESS AROUND WITH THIS FILE
// Please :)
/////////////////////////

/////////////////////////
// Easy Draw for Java
// Version 1.0.0
// Created by Joe Mazzone
// Documentation: https://easy-draw.joemazzone.net/
/////////////////////////

/////////////////////////
// This class was developed for students to easily create basic Java
// GUIs by drawing graphics primitives.  It features drawing classes
// for many shapes, as well as event handling for basic animations and games.
//
// Your drawing is shown in a web browser.  Easy Draw writes an index.html
// file in the folder your program runs from and serves a live version of it
// while your program is running, so clicks and key presses reach your event handlers.
//
// Put EasyDraw.java in the same folder as your program and use it like this:
//
//     public class Main {
//         public static void main(String[] args) {
//             EasyDraw.loadCanvas();
//
//             EasyDraw.Rectangle square = new EasyDraw.Rectangle(100, 100, 200, 200);
//             square.setColor("red");
//             square.eventSetup("<Button-1>", event -> square.rotate(10));
//
//             EasyDraw.end();
//         }
//     }
//
// Requires Java 17 or newer.
/////////////////////////

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Easy Draw - Classes and methods to easily create drawings.
 *
 * Shapes: Rectangle, RegPolygon, Polygon, Line, Arc, Circle, Oval, Text, Image
 *
 * Methods: loadCanvas(), end(), setCanvasColor(), saveCanvas(), canvasEventSetup(),
 * openImage(), rgbConvert()
 */
public final class EasyDraw {

    public static final String VERSION = "1.0.0";
    public static final String HTML_FILE = "index.html";
    public static final int CANVAS_SIZE = 600;

    private EasyDraw() {
    }

    static {
        System.out.println("Welcome to Easy Draw! -- version " + VERSION + " -- https://easy-draw.joemazzone.net/");
    }

    /** Thrown when Easy Draw is not used properly. */
    public static class EasyDrawException extends RuntimeException {
        public EasyDrawException(String message) {
            super(message);
        }
    }

    /** The code that runs when an event happens. Usually written as a lambda: {@code event -> { ... }} */
    @FunctionalInterface
    public interface EventHandler {
        void handle(Event event);
    }

    // --- Internal state ---
    // Everything below is shared between your program and the little web server
    // that talks to the browser, so it is guarded by LOCK.

    private static final Object LOCK = new Object();
    private static final Object HANDLER_LOCK = new Object();   // Only one event handler runs at a time.
    private static final BlockingQueue<Boolean> DIRTY = new ArrayBlockingQueue<>(1);
    private static final String RUN_ID = String.valueOf(System.currentTimeMillis());
    private static final Map<Integer, Shape> SHAPES = new LinkedHashMap<>();     // drawing order, bottom to top
    private static final Map<Integer, String> IMAGES = new LinkedHashMap<>();    // image ID -> src
    private static final Map<String, ImageFile> IMAGE_CACHE = new LinkedHashMap<>();
    private static final List<Binding> CANVAS_EVENTS = new ArrayList<>();
    private static final Set<BlockingQueue<Object>> CLIENTS = new HashSet<>();    // one per browser tab
    private static final Map<Integer, Map<String, Object>> PENDING_SAVES = new LinkedHashMap<>();
    private static volatile boolean loaded = false;
    private static String background = "white";
    private static int nextId = 0;
    private static HttpServer server = null;
    private static int port = -1;
    private static Path outDir = Paths.get("").toAbsolutePath();
    private static BufferedReader input = null;

    // --- Canvas methods ---

    /**
     * Starts Easy Draw with a 600x600px canvas.
     * Must be called before creating drawing objects.
     */
    public static void loadCanvas() {
        loadCanvas("white", 8765, true);
    }

    /** Starts Easy Draw with a background color. */
    public static void loadCanvas(String background) {
        loadCanvas(background, 8765, true);
    }

    /**
     * Starts Easy Draw with a background color.
     * Use port to pick the local web server port and set openBrowser to false
     * if you want to open the page yourself.
     */
    public static void loadCanvas(String background, int port, boolean openBrowser) {
        synchronized (LOCK) {
            loaded = true;
            EasyDraw.background = checkColor(background == null ? "white" : background, "background");
            SHAPES.clear();
            CANVAS_EVENTS.clear();
        }
        startServer(port);
        writeHtml();
        Thread writer = new Thread(EasyDraw::writerLoop, "EasyDraw-writer");
        writer.setDaemon(true);
        writer.start();
        Runtime.getRuntime().addShutdownHook(new Thread(EasyDraw::writeHtml));
        System.out.println("Your drawing is saved to " + htmlPath());
        if (server != null) {
            System.out.println("Your live drawing is at " + liveUrl());
            if (openBrowser) {
                Thread opener = new Thread(EasyDraw::openBrowser, "EasyDraw-browser");
                opener.setDaemon(true);
                opener.start();
            }
        }
    }

    /** Used to set the background color of the drawing canvas. */
    public static void setCanvasColor(String color) {
        requireCanvas();
        synchronized (LOCK) {
            background = checkColor(color, "color");
            broadcast(map("type", "background", "background", cssColor(background)), true);
        }
    }

    /** Used to set the background color of the drawing canvas with RGB values. */
    public static void setCanvasColor(int red, int green, int blue) {
        setCanvasColor(rgbConvert(red, green, blue));
    }

    /**
     * Every Easy Draw program must end with this method call.
     * Keeps your program running so the browser can send it events.
     * Closing the browser tab (or pressing Ctrl+C) ends the program.
     */
    public static void end() {
        end(false);
    }

    /** Same as end(). Set printHtml to true to print the finished page's HTML code. */
    public static void end(boolean printHtml) {
        requireCanvas();
        writeHtml();
        if (printHtml) {
            synchronized (LOCK) {
                System.out.println(buildHtml(false));
            }
        }
        if (server == null) {
            return;
        }
        System.out.println("Close your Easy Draw browser tab or press Ctrl+C to stop your program.");
        boolean connectedBefore = false;
        long lastSeen = System.currentTimeMillis();
        while (true) {
            boolean connected;
            boolean saving;
            synchronized (LOCK) {
                connected = !CLIENTS.isEmpty();
                saving = !PENDING_SAVES.isEmpty();
            }
            long now = System.currentTimeMillis();
            if (connected) {
                connectedBefore = true;
                lastSeen = now;
            } else if (connectedBefore && !saving && now - lastSeen > 3000) {
                break;
            }
            sleep(200);
        }
        writeHtml();
    }

    /**
     * Saves the canvas as a PNG file. Asks for the file name in the terminal.
     * The picture is created by the browser, so the drawing must be open in a browser tab.
     */
    public static void saveCanvas() {
        requireCanvas();
        System.out.print("What would you like your picture's file name to be? ");
        try {
            if (input == null) {
                input = new BufferedReader(new InputStreamReader(System.in));
            }
            String name = input.readLine();
            saveCanvas(name == null ? "" : name);
        } catch (IOException error) {
            throw new EasyDrawException("Could not read the file name.");
        }
    }

    /**
     * Saves the canvas as a PNG file in the folder your program runs from.
     * The picture is created by the browser, so the drawing must be open in a browser tab.
     */
    public static void saveCanvas(String name) {
        requireCanvas();
        name = name.trim();
        if (name.toLowerCase(Locale.ROOT).endsWith(".png")) {
            name = name.substring(0, name.length() - 4);
        }
        if (name.isEmpty()) {
            return;
        }
        boolean waiting;
        synchronized (LOCK) {
            int token = newId();
            Map<String, Object> message = map("type", "save", "token", token, "name", name, "scene", snapshot());
            PENDING_SAVES.put(token, message);
            broadcast(message, false);
            waiting = CLIENTS.isEmpty();
        }
        if (waiting) {
            System.out.println("Saving " + name + ".png once your drawing is open in the browser...");
        }
    }

    /** Used to setup an event for the entire canvas and not just a drawing object. */
    public static void canvasEventSetup(String event, EventHandler handler) {
        requireCanvas();
        Map<String, Object> spec = parseEvent(event);
        checkHandler(handler);
        synchronized (LOCK) {
            CANVAS_EVENTS.add(new Binding(spec, handler));
            broadcast(map("type", "canvasEvents", "events", specs(CANVAS_EVENTS)), true);
        }
    }

    /** Used to convert an RGB color value to hex. */
    public static String rgbConvert(int red, int green, int blue) {
        for (int value : new int[] {red, green, blue}) {
            if (value < 0 || value > 255) {
                throw new EasyDrawException("RGB values must be positive numbers and cannot exceed 255.");
            }
        }
        return String.format("#%02x%02x%02x", red, green, blue);
    }

    /**
     * Used to open an image for Easy Draw to use.
     * filename can be a file in the folder your program runs from or a public image link
     * that starts with http:// or https://.
     */
    public static ImageFile openImage(String filename) {
        String key = isUrl(filename) ? filename.trim() : findFile(filename).toAbsolutePath().toString();
        synchronized (LOCK) {
            if (!IMAGE_CACHE.containsKey(key)) {
                ImageFile image = new ImageFile(isUrl(filename) ? key : filename);
                IMAGE_CACHE.put(key, image);
                IMAGES.put(image.id, image.src);
                broadcast(map("type", "image", "id", image.id, "src", image.src), true);
            }
            return IMAGE_CACHE.get(key);
        }
    }

    /** An image opened with openImage(). Give it to an Image object to draw it. */
    public static class ImageFile {
        private static final Map<String, String> TYPES = Map.of(
            ".png", "image/png", ".gif", "image/gif", ".jpg", "image/jpeg", ".jpeg", "image/jpeg",
            ".webp", "image/webp", ".bmp", "image/bmp", ".svg", "image/svg+xml");
        private static final int MAX_DOWNLOAD = 10 * 1024 * 1024;

        private final String filename;
        private final int id;
        private final String src;

        private ImageFile(String filename) {
            this.filename = filename;
            this.id = newId();
            if (isUrl(filename)) {
                // The browser loads internet images itself, straight from the link.
                this.src = filename.trim();
                return;
            }
            Path path = findFile(filename);
            String mime = TYPES.get(extension(path.toString()));
            if (mime == null) {
                throw new EasyDrawException("Easy Draw can open .png, .gif, .jpg, .webp, .bmp, and .svg images, not \"" + filename + "\".");
            }
            try {
                this.src = "data:" + mime + ";base64," + Base64.getEncoder().encodeToString(Files.readAllBytes(path));
            } catch (IOException error) {
                throw new EasyDrawException("Could not read the image file \"" + filename + "\".");
            }
        }

        /** The file name or link this image was opened from. */
        public String getFilename() {
            return filename;
        }

        /** Downloads an internet image, for saving PNGs when the image's site blocks the browser. */
        private static Object[] download(String url) {
            byte[] data;
            String contentType;
            try {
                HttpClient client = HttpClient.newBuilder()
                    .followRedirects(HttpClient.Redirect.NORMAL)
                    .connectTimeout(Duration.ofSeconds(15))
                    .build();
                HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                    .timeout(Duration.ofSeconds(15))
                    .header("User-Agent", "Mozilla/5.0 (Easy Draw for Java " + VERSION + ")")
                    .build();
                HttpResponse<InputStream> response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());
                try (InputStream body = response.body()) {
                    data = body.readNBytes(MAX_DOWNLOAD + 1);
                }
                if (response.statusCode() >= 400) {
                    throw new IOException("status " + response.statusCode());
                }
                contentType = response.headers().firstValue("Content-Type").orElse("")
                    .split(";")[0].trim().toLowerCase(Locale.ROOT);
            } catch (IOException | IllegalArgumentException error) {
                throw new EasyDrawException("Could not download the image at \"" + url + "\" (" + error.getMessage() + "). "
                    + "Check that the link is correct and opens the image in your browser.");
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
                throw new EasyDrawException("Downloading the image at \"" + url + "\" was interrupted.");
            }
            if (data.length > MAX_DOWNLOAD) {
                throw new EasyDrawException("The image at \"" + url + "\" is bigger than 10 MB. Try a smaller image.");
            }
            if (TYPES.containsValue(contentType)) {
                return new Object[] {data, contentType};
            }
            String sniffed = sniffImageType(data);
            if (sniffed != null) {
                return new Object[] {data, sniffed};
            }
            String fromExtension = TYPES.get(extension(URI.create(url).getPath()));
            if (fromExtension != null && !contentType.startsWith("text/")) {
                return new Object[] {data, fromExtension};
            }
            throw new EasyDrawException("The link \"" + url + "\" is not a .png, .gif, .jpg, .webp, .bmp, or .svg image. "
                + "Make sure you copy the image's address, not the web page's address.");
        }
    }

    /**
     * Information about an event. Easy Draw passes one to your event handler.
     *
     * x, y - The mouse position on the canvas, in pixels.
     * xRoot, yRoot - The mouse position on the screen, in pixels.
     * character - The character typed (keyboard events only).
     * keysym - The key symbol, like "a", "Up", or "space" (keyboard events only).
     * keycode - The key code (keyboard events only).
     * num - The mouse button number (mouse button events only).
     * delta - How far the mouse wheel moved (mouse wheel events only).
     * type - The event type, like "ButtonPress" or "KeyPress".
     */
    public static class Event {
        private static final Map<String, String> TYPE_NAMES = Map.ofEntries(
            Map.entry("down", "ButtonPress"), Map.entry("double", "ButtonPress"), Map.entry("triple", "ButtonPress"),
            Map.entry("up", "ButtonRelease"), Map.entry("move", "Motion"), Map.entry("keydown", "KeyPress"),
            Map.entry("keyup", "KeyRelease"), Map.entry("enter", "Enter"), Map.entry("leave", "Leave"),
            Map.entry("focusin", "FocusIn"), Map.entry("focusout", "FocusOut"), Map.entry("wheel", "MouseWheel"));

        public final String type;
        public final int x;
        public final int y;
        public final int xRoot;
        public final int yRoot;
        public final String character;
        public final String keysym;
        public final int keycode;
        public final int num;
        public final int delta;

        private Event(Map<String, Object> spec, Map<?, ?> data) {
            type = TYPE_NAMES.getOrDefault((String) spec.get("t"), "");
            x = intValue(data.get("x"));
            y = intValue(data.get("y"));
            xRoot = intValue(data.get("x_root"));
            yRoot = intValue(data.get("y_root"));
            character = data.get("char") instanceof String ? (String) data.get("char") : "";
            keysym = data.get("keysym") instanceof String ? (String) data.get("keysym") : "??";
            keycode = intValue(data.get("keycode"));
            num = intValue(data.get("num"));
            delta = intValue(data.get("delta"));
        }

        @Override
        public String toString() {
            return "<Event " + type + " x=" + x + " y=" + y + ">";
        }
    }

    // --- Drawing Shapes ---

    /**
     * The parent class of every Easy Draw drawing object.
     *
     * Methods
     * -------
     * toString() - Used to print information about an instance.
     * rotate() - Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
     * erase() - Used to removed the instance from the canvas.
     * eventSetup() - Used to bind an event and handler to the instance.
     * setVisible() / isVisible() - Show or hide the shape.
     */
    public abstract static class Shape {
        private final int id;
        private final String typeName;
        private final List<Binding> events = new ArrayList<>();
        private boolean ready = false;
        private boolean erased = false;
        private boolean visible = true;
        private double angle = 0;
        private String anchorMode = "center";
        private double offsetX = 0;
        private double offsetY = 0;

        Shape(String typeName) {
            requireCanvas();
            this.id = newId();
            this.typeName = typeName;
        }

        /** The kind of shape, like "Rectangle". */
        public String getType() {
            return typeName;
        }

        /** The shape's ID number. */
        public int getId() {
            return id;
        }

        public boolean isVisible() {
            return visible;
        }

        /** true = Shape can be seen. false = Shape cannot be seen. */
        public void setVisible(boolean visible) {
            this.visible = visible;
            changed();
        }

        /** How far the shape has been rotated, in degrees. */
        public double getAngle() {
            return angle;
        }

        /** Sets how far the shape is rotated, in degrees. */
        public void setAngle(double angle) {
            this.angle = angle;
            changed();
        }

        /** Used to rotate the shape by x degrees. Negative values rotate the opposite direction. */
        public void rotate(double angle) {
            rotateAround(angle, "center");
        }

        /** Used to removed the instance from the canvas. */
        public void erase() {
            synchronized (LOCK) {
                if (erased) {
                    return;
                }
                erased = true;
                ready = false;
                SHAPES.remove(id);
                broadcast(map("type", "erase", "id", id), true);
            }
        }

        /** Used to bind an event and handler to the instance. */
        public void eventSetup(String event, EventHandler handler) {
            Map<String, Object> spec = parseEvent(event);
            checkHandler(handler);
            synchronized (LOCK) {
                events.add(new Binding(spec, handler));
            }
            changed();
        }

        /** Used to print information about an instance. */
        @Override
        public String toString() {
            return "Object: " + getType() + "\t ID: " + id;
        }

        // Everything below is used internally by Easy Draw.

        /** Adds the finished shape to the canvas. */
        void show() {
            synchronized (LOCK) {
                ready = true;
                SHAPES.put(id, this);
                changed();
            }
        }

        void changed() {
            synchronized (LOCK) {
                if (ready && !erased) {
                    broadcast(map("type", "shape", "shape", toMap()), true);
                }
            }
        }

        abstract double[] center();

        double[] anchor(String mode) {
            return center();
        }

        void rotateAround(double degrees, String mode) {
            double[] anchor = anchor(mode);
            // Keep the new anchor point where it is on screen, then turn around it.
            double[] moved = transformPoint(anchor);
            offsetX = moved[0] - anchor[0];
            offsetY = moved[1] - anchor[1];
            anchorMode = mode;
            setAngle(angle + degrees);
        }

        /** Where a point of the shape ends up after rotation. */
        private double[] transformPoint(double[] point) {
            double[] anchor = anchor(anchorMode);
            double radians = Math.toRadians(angle);
            double dx = point[0] - anchor[0];
            double dy = point[1] - anchor[1];
            return new double[] {
                dx * Math.cos(radians) - dy * Math.sin(radians) + anchor[0] + offsetX,
                dx * Math.sin(radians) + dy * Math.cos(radians) + anchor[1] + offsetY,
            };
        }

        Map<String, Object> toMap() {
            Map<String, Object> shape = geometry();
            double[] anchor = anchor(anchorMode);
            shape.put("id", id);
            shape.put("visible", visible);
            shape.put("angle", round(angle));
            shape.put("anchor", roundList(anchor));
            shape.put("offset", roundList(new double[] {offsetX, offsetY}));
            shape.put("events", specs(events));
            return shape;
        }

        abstract Map<String, Object> geometry();
    }

    /** A shape with a color. */
    public abstract static class ColoredShape extends Shape {
        private String color = "black";

        ColoredShape(String typeName) {
            super(typeName);
        }

        public String getColor() {
            return color;
        }

        /** Color name, like "red", or hexadecimal color value, like "#FF0000". */
        public void setColor(String color) {
            this.color = checkColor(color, "color");
            changed();
        }

        /** RGB color value, like setColor(255, 0, 0). */
        public void setColor(int red, int green, int blue) {
            setColor(rgbConvert(red, green, blue));
        }
    }

    /** A shape with a color, a border, and dashes. */
    public abstract static class FilledShape extends ColoredShape {
        private String borderColor = null;
        private double borderWidth = 0;
        private double dashes = 0;

        FilledShape(String typeName) {
            super(typeName);
        }

        public String getBorderColor() {
            return borderColor;
        }

        /** Color of the border. Use null for no border. */
        public void setBorderColor(String borderColor) {
            this.borderColor = borderColor == null ? null : checkColor(borderColor, "borderColor");
            changed();
        }

        public void setBorderColor(int red, int green, int blue) {
            setBorderColor(rgbConvert(red, green, blue));
        }

        public double getBorderWidth() {
            return borderWidth;
        }

        /** Size of the border in pixels. */
        public void setBorderWidth(double borderWidth) {
            this.borderWidth = borderWidth;
            changed();
        }

        public double getDashes() {
            return dashes;
        }

        /** Size of the dashes for the border in pixels. Use 0 for a solid border. */
        public void setDashes(double dashes) {
            this.dashes = dashes;
            changed();
        }

        Map<String, Object> paint(Map<String, Object> shape) {
            shape.put("fill", cssColor(getColor()));
            shape.put("stroke", cssColor(borderColor));
            shape.put("strokeWidth", round(borderWidth(borderColor, borderWidth)));
            shape.put("dash", dashList(dashes));
            return shape;
        }
    }

    /**
     * Draws a rectangle from the top-left corner (x, y) with a given width and height.
     *
     * Use rotate(45, true) to turn it around its top-left corner instead of its center.
     */
    public static class Rectangle extends FilledShape {
        private double x;
        private double y;
        private double width;
        private double height;

        public Rectangle(double x, double y, double width, double height) {
            super("Rectangle");
            this.x = x;
            this.y = y;
            this.width = width;
            this.height = height;
            show();
        }

        public double getX() {
            return x;
        }

        public double getY() {
            return y;
        }

        /** Moves the rectangle's top-left corner. */
        public void setXY(double x, double y) {
            this.x = x;
            this.y = y;
            changed();
        }

        public void setX(double x) {
            setXY(x, y);
        }

        public void setY(double y) {
            setXY(x, y);
        }

        public double getWidth() {
            return width;
        }

        public void setWidth(double width) {
            this.width = width;
            changed();
        }

        public double getHeight() {
            return height;
        }

        public void setHeight(double height) {
            this.height = height;
            changed();
        }

        /**
         * Used to rotate the shape by x degrees. Negative values rotate the opposite direction.
         * Set fromTopLeft to true to rotate around the top-left corner instead of the center.
         */
        public void rotate(double angle, boolean fromTopLeft) {
            rotateAround(angle, fromTopLeft ? "top_left" : "center");
        }

        @Override
        double[] anchor(String mode) {
            return mode.equals("top_left") ? new double[] {x, y} : center();
        }

        @Override
        double[] center() {
            return new double[] {x + width / 2, y + height / 2};
        }

        @Override
        Map<String, Object> geometry() {
            return paint(map("kind", "polygon",
                "points", roundList(new double[] {x, y, x + width, y, x + width, y + height, x, y + height})));
        }
    }

    /** Draws a regular polygon, n sided shape with equal sides. */
    public static class RegPolygon extends FilledShape {
        private int nsides;
        private double centerX;
        private double centerY;
        private double radius;

        public RegPolygon(int nsides, double centerX, double centerY, double radius) {
            super("Regular Polygon");
            this.nsides = checkSides(nsides);
            this.centerX = centerX;
            this.centerY = centerY;
            this.radius = radius;
            show();
        }

        @Override
        public String getType() {
            return nsides + "-Sided Regular Polygon";
        }

        public int getNsides() {
            return nsides;
        }

        /** The number of sides the polygon has. */
        public void setNsides(int nsides) {
            this.nsides = checkSides(nsides);
            changed();
        }

        public double getCenterX() {
            return centerX;
        }

        public double getCenterY() {
            return centerY;
        }

        /** Moves the polygon's center. */
        public void setCenter(double centerX, double centerY) {
            this.centerX = centerX;
            this.centerY = centerY;
            changed();
        }

        public double getRadius() {
            return radius;
        }

        /** The distance in pixels from the center to any outer point. */
        public void setRadius(double radius) {
            this.radius = radius;
            changed();
        }

        @Override
        double[] center() {
            return new double[] {centerX, centerY};
        }

        @Override
        Map<String, Object> geometry() {
            double[] points = new double[nsides * 2];
            for (int i = 0; i < nsides; i++) {
                double angle = 2 * Math.PI * i / nsides;
                points[i * 2] = centerX + radius * Math.cos(angle);
                points[i * 2 + 1] = centerY + radius * Math.sin(angle);
            }
            return paint(map("kind", "polygon", "points", roundList(points)));
        }
    }

    /** Draws a polygon using a list of x y coordinates, like new Polygon(25, 25, 150, 25, 200, 200). */
    public static class Polygon extends FilledShape {
        private double[] points;

        public Polygon(double... points) {
            super("Polygon");
            this.points = checkPoints(points);
            show();
        }

        @Override
        public String getType() {
            return points.length / 2 + "-Sided Polygon";
        }

        public double[] getPoints() {
            return points.clone();
        }

        /** A list of x y coordinates identifying the points of the polygon. */
        public void setPoints(double... points) {
            this.points = checkPoints(points);
            changed();
        }

        @Override
        double[] center() {
            return averagePoint(points);
        }

        @Override
        Map<String, Object> geometry() {
            return paint(map("kind", "polygon", "points", roundList(points)));
        }
    }

    /**
     * Draws a line from (x1, y1) to (x2, y2), like new Line(100, 100, 200, 200).
     * Give more x y coordinates to draw a line through many points.
     */
    public static class Line extends ColoredShape {
        private double[] points;
        private double thickness = 5;
        private double dashes = 0;
        private boolean arrowStart = false;
        private boolean arrowEnd = false;
        private String style = "round";

        public Line(double... points) {
            super("Line");
            if (points == null || points.length < 4) {
                throw new EasyDrawException("You must give a line at least 2 points, like new Line(100, 100, 200, 200).");
            }
            this.points = checkPoints(points);
            show();
        }

        public double[] getPoints() {
            return points.clone();
        }

        /** A list of x y coordinates the line goes through. */
        public void setPoints(double... points) {
            this.points = checkPoints(points);
            changed();
        }

        /** Moves the start of the line. */
        public void setXY1(double x, double y) {
            points[0] = x;
            points[1] = y;
            changed();
        }

        /** Moves the end of the line. */
        public void setXY2(double x, double y) {
            points[points.length - 2] = x;
            points[points.length - 1] = y;
            changed();
        }

        public double getThickness() {
            return thickness;
        }

        /** The width of the line in pixels. */
        public void setThickness(double thickness) {
            this.thickness = thickness;
            changed();
        }

        public double getDashes() {
            return dashes;
        }

        /** Size of the dashes in pixels. Use 0 for a solid line. */
        public void setDashes(double dashes) {
            this.dashes = dashes;
            changed();
        }

        public boolean getArrowStart() {
            return arrowStart;
        }

        /** Add an arrow to the start of the line. */
        public void setArrowStart(boolean arrowStart) {
            this.arrowStart = arrowStart;
            changed();
        }

        public boolean getArrowEnd() {
            return arrowEnd;
        }

        /** Add an arrow to the end of the line. */
        public void setArrowEnd(boolean arrowEnd) {
            this.arrowEnd = arrowEnd;
            changed();
        }

        public String getStyle() {
            return style;
        }

        /** "round" (the default) or "cut" for square line ends. */
        public void setStyle(String style) {
            this.style = checkStyle(style, "Line", "round", "cut");
            changed();
        }

        @Override
        double[] center() {
            return averagePoint(points);
        }

        @Override
        Map<String, Object> geometry() {
            return map("kind", "line", "points", roundList(points), "color", cssColor(getColor()),
                "width", round(thickness), "dash", dashList(dashes), "arrowStart", arrowStart,
                "arrowEnd", arrowEnd, "style", style);
        }
    }

    /** Draws a circle with a center coordinate and a radius. */
    public static class Circle extends FilledShape {
        private double centerX;
        private double centerY;
        private double radius;

        public Circle(double centerX, double centerY, double radius) {
            super("Circle");
            this.centerX = centerX;
            this.centerY = centerY;
            this.radius = radius;
            show();
        }

        public double getCenterX() {
            return centerX;
        }

        public double getCenterY() {
            return centerY;
        }

        /** Moves the circle's center. */
        public void setCenter(double centerX, double centerY) {
            this.centerX = centerX;
            this.centerY = centerY;
            changed();
        }

        public double getRadius() {
            return radius;
        }

        /** The measurement in pixels from the center of the circle to the edge. */
        public void setRadius(double radius) {
            this.radius = radius;
            changed();
        }

        @Override
        double[] center() {
            return new double[] {centerX, centerY};
        }

        @Override
        Map<String, Object> geometry() {
            return paint(map("kind", "ellipse", "cx", round(centerX), "cy", round(centerY),
                "rx", round(radius), "ry", round(radius)));
        }
    }

    /** Draws an oval with a center coordinate, a width, and a height. */
    public static class Oval extends FilledShape {
        private double centerX;
        private double centerY;
        private double width;
        private double height;

        public Oval(double centerX, double centerY, double width, double height) {
            super("Oval");
            this.centerX = centerX;
            this.centerY = centerY;
            this.width = width;
            this.height = height;
            show();
        }

        public double getCenterX() {
            return centerX;
        }

        public double getCenterY() {
            return centerY;
        }

        /** Moves the oval's center. */
        public void setCenter(double centerX, double centerY) {
            this.centerX = centerX;
            this.centerY = centerY;
            changed();
        }

        public double getWidth() {
            return width;
        }

        public void setWidth(double width) {
            this.width = width;
            changed();
        }

        public double getHeight() {
            return height;
        }

        public void setHeight(double height) {
            this.height = height;
            changed();
        }

        @Override
        double[] center() {
            return new double[] {centerX, centerY};
        }

        @Override
        Map<String, Object> geometry() {
            return paint(map("kind", "ellipse", "cx", round(centerX), "cy", round(centerY),
                "rx", round(width / 2), "ry", round(height / 2)));
        }
    }

    /**
     * Draws a arc using a slice of an oval. sweepAngle is how much of the arc to show, in degrees.
     * The arc comes in three styles: "pieslice" (the default), "chord", and "arc".
     */
    public static class Arc extends FilledShape {
        private double centerX;
        private double centerY;
        private double width;
        private double height;
        private double sweepAngle;
        private String style = "pieslice";

        public Arc(double centerX, double centerY, double width, double height, double sweepAngle) {
            super("Arc");
            this.centerX = centerX;
            this.centerY = centerY;
            this.width = width;
            this.height = height;
            this.sweepAngle = sweepAngle;
            show();
        }

        public double getCenterX() {
            return centerX;
        }

        public double getCenterY() {
            return centerY;
        }

        /** Moves the center of the oval used to create the arc. */
        public void setCenter(double centerX, double centerY) {
            this.centerX = centerX;
            this.centerY = centerY;
            changed();
        }

        public double getWidth() {
            return width;
        }

        public void setWidth(double width) {
            this.width = width;
            changed();
        }

        public double getHeight() {
            return height;
        }

        public void setHeight(double height) {
            this.height = height;
            changed();
        }

        public double getSweepAngle() {
            return sweepAngle;
        }

        /** The amount of the arc to show. From 0 to the angle in degrees identified. */
        public void setSweepAngle(double sweepAngle) {
            this.sweepAngle = sweepAngle;
            changed();
        }

        public String getStyle() {
            return style;
        }

        /** "pieslice", "chord", or "arc". The "arc" style only draws the outline. */
        public void setStyle(String style) {
            this.style = checkStyle(style, "Arc", "pieslice", "chord", "arc");
            changed();
        }

        @Override
        double[] center() {
            return new double[] {centerX, centerY};
        }

        @Override
        Map<String, Object> geometry() {
            // Without a border color, the arc's outline uses its color (the "arc" style is only an outline).
            String strokeColor = getBorderColor() == null ? getColor() : getBorderColor();
            String fill;
            double strokeWidth;
            if (style.equals("arc")) {
                fill = "none";
                strokeWidth = Math.max(getBorderWidth(), 1);
            } else {
                fill = cssColor(getColor());
                strokeWidth = borderWidth(getBorderColor(), getBorderWidth());
            }
            return map("kind", "arc", "style", style, "cx", round(centerX), "cy", round(centerY),
                "rx", round(width / 2), "ry", round(height / 2), "start", 0, "extent", round(sweepAngle),
                "fill", fill, "stroke", cssColor(strokeColor), "strokeWidth", round(strokeWidth),
                "dash", dashList(getDashes()));
        }
    }

    // --- Text and Images ---

    /** Draws text from a center coordinate. */
    public static class Text extends ColoredShape {
        private double centerX;
        private double centerY;
        private String text;
        private String font = "Arial";
        private double size = 16;
        private boolean bold = false;
        private boolean italic = false;
        private boolean underline = false;
        private boolean strikethrough = false;

        public Text(double centerX, double centerY, String text) {
            super("Text");
            this.centerX = centerX;
            this.centerY = centerY;
            this.text = text == null ? "" : text;
            show();
        }

        public double getCenterX() {
            return centerX;
        }

        public double getCenterY() {
            return centerY;
        }

        /** Moves the center of the text. */
        public void setCenter(double centerX, double centerY) {
            this.centerX = centerX;
            this.centerY = centerY;
            changed();
        }

        public String getText() {
            return text;
        }

        /** The text you want to display. */
        public void setText(String text) {
            this.text = text == null ? "" : text;
            changed();
        }

        public String getFont() {
            return font;
        }

        /** The font family used for the text. Font must be installed on the computer to be used. */
        public void setFont(String font) {
            this.font = font;
            changed();
        }

        public double getSize() {
            return size;
        }

        /** The font size of the text. */
        public void setSize(double size) {
            this.size = size;
            changed();
        }

        public boolean isBold() {
            return bold;
        }

        public void setBold(boolean bold) {
            this.bold = bold;
            changed();
        }

        public boolean isItalic() {
            return italic;
        }

        public void setItalic(boolean italic) {
            this.italic = italic;
            changed();
        }

        public boolean isUnderline() {
            return underline;
        }

        public void setUnderline(boolean underline) {
            this.underline = underline;
            changed();
        }

        public boolean isStrikethrough() {
            return strikethrough;
        }

        public void setStrikethrough(boolean strikethrough) {
            this.strikethrough = strikethrough;
            changed();
        }

        @Override
        double[] center() {
            return new double[] {centerX, centerY};
        }

        @Override
        Map<String, Object> geometry() {
            return map("kind", "text", "x", round(centerX), "y", round(centerY), "text", text,
                "color", cssColor(getColor()), "font", font, "size", round(size), "bold", bold,
                "italic", italic, "underline", underline, "strike", strikethrough);
        }
    }

    /** Draws an image from an image file or a public image link. */
    public static class Image extends Shape {
        private double centerX;
        private double centerY;
        private ImageFile image;

        public Image(double centerX, double centerY, ImageFile image) {
            super("Image");
            this.centerX = centerX;
            this.centerY = centerY;
            this.image = checkImage(image);
            show();
        }

        /** Draws an image straight from a file name or a public image link. */
        public Image(double centerX, double centerY, String filename) {
            this(centerX, centerY, openImage(filename));
        }

        public double getCenterX() {
            return centerX;
        }

        public double getCenterY() {
            return centerY;
        }

        /** Moves the center of the image. */
        public void setCenter(double centerX, double centerY) {
            this.centerX = centerX;
            this.centerY = centerY;
            changed();
        }

        public ImageFile getImage() {
            return image;
        }

        /** Changes the picture. */
        public void setImage(ImageFile image) {
            this.image = checkImage(image);
            changed();
        }

        /** Changes the picture to a file name or a public image link. */
        public void setImage(String filename) {
            setImage(openImage(filename));
        }

        @Override
        double[] center() {
            return new double[] {centerX, centerY};
        }

        @Override
        Map<String, Object> geometry() {
            return map("kind", "image", "x", round(centerX), "y", round(centerY), "img", image.id);
        }

        private static ImageFile checkImage(ImageFile image) {
            if (image == null) {
                throw new EasyDrawException("image must be made with EasyDraw.openImage(\"file_name.png\").");
            }
            return image;
        }
    }

    // --- Internal helpers ---

    private static final class Binding {
        final Map<String, Object> spec;
        final EventHandler handler;

        Binding(Map<String, Object> spec, EventHandler handler) {
            this.spec = spec;
            this.handler = handler;
        }
    }

    private static void requireCanvas() {
        if (!loaded) {
            throw new EasyDrawException("You must call EasyDraw.loadCanvas() at the start of your program, before drawing anything.");
        }
    }

    private static int newId() {
        synchronized (LOCK) {
            return ++nextId;
        }
    }

    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
        }
    }

    private static int intValue(Object value) {
        return value instanceof Number ? ((Number) value).intValue() : 0;
    }

    private static String checkColor(String color, String name) {
        if (color == null) {
            throw new EasyDrawException(name + " must be a color name, a hex value like \"#FF0000\", or RGB values like (255, 0, 0).");
        }
        return color;
    }

    private static void checkHandler(EventHandler handler) {
        if (handler == null) {
            throw new EasyDrawException("The event handler is missing. Use a lambda like eventSetup(\"<Button-1>\", event -> { ... }).");
        }
    }

    private static int checkSides(int nsides) {
        if (nsides < 3) {
            throw new EasyDrawException("nsides must be a whole number that is 3 or more.");
        }
        return nsides;
    }

    private static double[] checkPoints(double[] points) {
        if (points == null || points.length % 2 != 0) {
            throw new EasyDrawException("The points list must have an even number of values as it should contain xy coordinate pairs.");
        }
        if (points.length < 4) {
            throw new EasyDrawException("The points list needs at least 2 points (4 numbers).");
        }
        return points.clone();
    }

    private static String checkStyle(String style, String shape, String... styles) {
        String lower = style == null ? "" : style.toLowerCase(Locale.ROOT);
        if (!Arrays.asList(styles).contains(lower)) {
            throw new EasyDrawException(shape + " only supports these styles: " + String.join(", ", styles));
        }
        return lower;
    }

    private static final Pattern GRAY = Pattern.compile("gr[ae]y(\\d{1,3})");

    /** Turns a Tkinter style color into a color the browser understands. */
    private static String cssColor(String color) {
        if (color == null || color.isEmpty()) {
            return "none";
        }
        color = color.trim();
        if (color.startsWith("#")) {
            String digits = color.substring(1);
            if (digits.length() == 9 || digits.length() == 12) {
                int size = digits.length() / 3;
                StringBuilder hex = new StringBuilder("#");
                for (int i = 0; i < 3; i++) {
                    hex.append(digits, i * size, i * size + 2);
                }
                return hex.toString();
            }
            return color;
        }
        String name = color.replace(" ", "").toLowerCase(Locale.ROOT);
        Matcher gray = GRAY.matcher(name);
        if (gray.matches() && Integer.parseInt(gray.group(1)) <= 100) {
            int level = (int) Math.round(Integer.parseInt(gray.group(1)) * 2.55);
            return String.format("#%02x%02x%02x", level, level, level);
        }
        return name;
    }

    private static double borderWidth(String borderColor, double borderWidth) {
        if (borderColor == null || borderColor.isEmpty()) {
            return 0;
        }
        return Math.max(borderWidth, 1);
    }

    private static List<Object> dashList(double dashes) {
        return dashes > 0 ? List.of(round(dashes), round(dashes)) : null;
    }

    private static Number round(double value) {
        double rounded = Math.round(value * 1000) / 1000.0;
        if (rounded == Math.rint(rounded) && Math.abs(rounded) < 1e15) {
            return (long) rounded;
        }
        return rounded;
    }

    private static List<Object> roundList(double[] values) {
        List<Object> list = new ArrayList<>();
        for (double value : values) {
            list.add(round(value));
        }
        return list;
    }

    private static double[] averagePoint(double[] points) {
        double x = 0;
        double y = 0;
        for (int i = 0; i < points.length; i += 2) {
            x += points[i];
            y += points[i + 1];
        }
        int count = points.length / 2;
        return new double[] {x / count, y / count};
    }

    private static String extension(String path) {
        int slash = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
        int dot = path.lastIndexOf('.');
        return dot > slash ? path.substring(dot).toLowerCase(Locale.ROOT) : "";
    }

    /** Guesses an image's type from its first bytes, for servers that do not say. */
    private static String sniffImageType(byte[] data) {
        if (startsWith(data, new byte[] {(byte) 0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'})) {
            return "image/png";
        }
        if (startsWith(data, "GIF87a".getBytes(StandardCharsets.US_ASCII))
                || startsWith(data, "GIF89a".getBytes(StandardCharsets.US_ASCII))) {
            return "image/gif";
        }
        if (startsWith(data, new byte[] {(byte) 0xff, (byte) 0xd8, (byte) 0xff})) {
            return "image/jpeg";
        }
        if (data.length >= 12 && new String(data, 0, 4, StandardCharsets.US_ASCII).equals("RIFF")
                && new String(data, 8, 4, StandardCharsets.US_ASCII).equals("WEBP")) {
            return "image/webp";
        }
        if (startsWith(data, "BM".getBytes(StandardCharsets.US_ASCII))) {
            return "image/bmp";
        }
        String start = new String(data, 0, Math.min(data.length, 1024), StandardCharsets.ISO_8859_1);
        if (start.toLowerCase(Locale.ROOT).contains("<svg")) {
            return "image/svg+xml";
        }
        return null;
    }

    private static boolean startsWith(byte[] data, byte[] prefix) {
        if (data.length < prefix.length) {
            return false;
        }
        for (int i = 0; i < prefix.length; i++) {
            if (data[i] != prefix[i]) {
                return false;
            }
        }
        return true;
    }

    private static boolean isUrl(String filename) {
        if (filename == null) {
            return false;
        }
        String lower = filename.trim().toLowerCase(Locale.ROOT);
        return lower.startsWith("http://") || lower.startsWith("https://");
    }

    private static Path findFile(String filename) {
        if (filename != null) {
            Path path = outDir.resolve(filename);
            if (Files.isRegularFile(path)) {
                return path;
            }
        }
        throw new EasyDrawException("Could not find the file \"" + filename + "\". "
            + "Make sure it is in the same folder you run your program from.");
    }

    // --- Events ---

    private static final Map<String, String> EVENT_TYPES = Map.ofEntries(
        Map.entry("Button", "down"), Map.entry("ButtonPress", "down"), Map.entry("ButtonRelease", "up"),
        Map.entry("Motion", "move"), Map.entry("Key", "keydown"), Map.entry("KeyPress", "keydown"),
        Map.entry("KeyRelease", "keyup"), Map.entry("Enter", "enter"), Map.entry("Leave", "leave"),
        Map.entry("FocusIn", "focusin"), Map.entry("FocusOut", "focusout"), Map.entry("MouseWheel", "wheel"));
    private static final Map<String, String> MODIFIERS = Map.of(
        "Shift", "Shift", "Control", "Control", "Alt", "Alt", "Option", "Alt", "Meta", "Meta", "Command", "Meta");
    // Browser key names -> Tkinter style key symbols
    private static final Map<String, String> KEY_KEYSYMS = Map.ofEntries(
        Map.entry("ArrowUp", "Up"), Map.entry("ArrowDown", "Down"), Map.entry("ArrowLeft", "Left"),
        Map.entry("ArrowRight", "Right"), Map.entry("Enter", "Return"), Map.entry("Escape", "Escape"),
        Map.entry("Backspace", "BackSpace"), Map.entry("Tab", "Tab"), Map.entry("Delete", "Delete"),
        Map.entry("Home", "Home"), Map.entry("End", "End"), Map.entry("PageUp", "Prior"),
        Map.entry("PageDown", "Next"), Map.entry("Insert", "Insert"), Map.entry("CapsLock", "Caps_Lock"));
    // Typed characters -> Tkinter style key symbols
    private static final Map<String, String> CHAR_KEYSYMS = Map.ofEntries(
        Map.entry(" ", "space"), Map.entry("!", "exclam"), Map.entry("\"", "quotedbl"), Map.entry("#", "numbersign"),
        Map.entry("$", "dollar"), Map.entry("%", "percent"), Map.entry("&", "ampersand"), Map.entry("'", "apostrophe"),
        Map.entry("(", "parenleft"), Map.entry(")", "parenright"), Map.entry("*", "asterisk"), Map.entry("+", "plus"),
        Map.entry(",", "comma"), Map.entry("-", "minus"), Map.entry(".", "period"), Map.entry("/", "slash"),
        Map.entry(":", "colon"), Map.entry(";", "semicolon"), Map.entry("<", "less"), Map.entry("=", "equal"),
        Map.entry(">", "greater"), Map.entry("?", "question"), Map.entry("@", "at"), Map.entry("[", "bracketleft"),
        Map.entry("\\", "backslash"), Map.entry("]", "bracketright"), Map.entry("^", "asciicircum"),
        Map.entry("_", "underscore"), Map.entry("`", "grave"), Map.entry("{", "braceleft"), Map.entry("|", "bar"),
        Map.entry("}", "braceright"), Map.entry("~", "asciitilde"));
    private static final Map<String, String> KEYSYM_ALIASES = Map.of(
        "Page_Up", "Prior", "Page_Down", "Next", "Enter", "Return", "Esc", "Escape");
    private static final Set<String> KNOWN_KEYSYMS = new HashSet<>();

    static {
        KNOWN_KEYSYMS.addAll(KEY_KEYSYMS.values());
        KNOWN_KEYSYMS.addAll(CHAR_KEYSYMS.values());
        for (String key : new String[] {"Shift", "Control", "Alt", "Meta"}) {
            KNOWN_KEYSYMS.add(key + "_L");
            KNOWN_KEYSYMS.add(key + "_R");
        }
        for (int n = 1; n <= 24; n++) {
            KNOWN_KEYSYMS.add("F" + n);
        }
    }

    private static Map<String, Object> spec(String kind, int button, int drag, String key, List<String> modifiers) {
        return map("t", kind, "b", button, "drag", drag, "k", key, "m", modifiers);
    }

    /** Turns an event string like "<Button-1>" into something the browser can match. */
    private static Map<String, Object> parseEvent(String sequence) {
        EasyDrawException error = new EasyDrawException("\"" + sequence + "\" is not an event Easy Draw understands. "
            + "Try something like \"<Button-1>\", \"<Key>\", or \"<Up>\".");
        if (sequence == null || sequence.isEmpty()) {
            throw error;
        }
        if (!(sequence.startsWith("<") && sequence.endsWith(">") && sequence.length() > 1)) {
            if (sequence.length() == 1) {
                return spec("keydown", 0, 0, CHAR_KEYSYMS.getOrDefault(sequence, sequence), List.of());
            }
            throw error;
        }
        String[] tokens = sequence.substring(1, sequence.length() - 1).split("-", -1);
        for (String token : tokens) {
            if (token.isEmpty()) {
                throw error;
            }
        }
        List<String> modifiers = new ArrayList<>();
        int clicks = 1;
        int drag = 0;
        int i = 0;
        while (i < tokens.length - 1) {
            String token = tokens[i];
            if (MODIFIERS.containsKey(token)) {
                modifiers.add(MODIFIERS.get(token));
            } else if (token.equals("Double")) {
                clicks = 2;
            } else if (token.equals("Triple")) {
                clicks = 3;
            } else if (token.matches("(B|Button)[1-3]")) {
                drag = token.charAt(token.length() - 1) - '0';
            } else {
                break;
            }
            i++;
        }
        String[] rest = Arrays.copyOfRange(tokens, i, tokens.length);
        if (rest.length > 2) {
            throw error;
        }
        String kind;
        String detail;
        if (EVENT_TYPES.containsKey(rest[0])) {
            kind = EVENT_TYPES.get(rest[0]);
            detail = rest.length == 2 ? rest[1] : null;
        } else if (rest.length == 1) {
            detail = rest[0];
            kind = detail.matches("\\d+") ? "down" : "keydown";
        } else {
            throw error;
        }
        int button = 0;
        String key = null;
        if (kind.equals("down") || kind.equals("up")) {
            if (detail != null) {
                if (!detail.matches("[1-5]")) {
                    throw error;
                }
                button = Integer.parseInt(detail);
            }
            if (clicks > 1) {
                if (!kind.equals("down")) {
                    throw error;
                }
                kind = clicks == 2 ? "double" : "triple";
            }
        } else if (kind.equals("keydown") || kind.equals("keyup")) {
            if (detail != null) {
                key = CHAR_KEYSYMS.getOrDefault(detail, KEYSYM_ALIASES.getOrDefault(detail, detail));
                if (key.length() != 1 && !KNOWN_KEYSYMS.contains(key)) {
                    throw error;
                }
            }
        } else if (detail != null) {
            throw error;
        }
        return spec(kind, button, drag, key, modifiers);
    }

    private static List<Object> specs(List<Binding> bindings) {
        List<Object> list = new ArrayList<>();
        for (Binding binding : bindings) {
            list.add(binding.spec);
        }
        return list;
    }

    /** Runs the event handler the browser asked for. */
    private static void dispatch(Map<?, ?> body) {
        if (!RUN_ID.equals(body.get("run")) || !(body.get("index") instanceof Number)) {
            return;
        }
        Object target = body.get("target");
        int index = ((Number) body.get("index")).intValue();
        Binding binding;
        synchronized (LOCK) {
            List<Binding> bindings;
            if (target == null) {
                bindings = CANVAS_EVENTS;
            } else {
                Shape shape = target instanceof Number ? SHAPES.get(((Number) target).intValue()) : null;
                if (shape == null) {
                    return;
                }
                bindings = shape.events;
            }
            if (index < 0 || index >= bindings.size()) {
                return;
            }
            binding = bindings.get(index);
        }
        Object data = body.get("event");
        Event event = new Event(binding.spec, data instanceof Map ? (Map<?, ?>) data : Map.of());
        synchronized (HANDLER_LOCK) {
            try {
                binding.handler.handle(event);
            } catch (RuntimeException error) {
                error.printStackTrace();
            }
        }
    }

    // --- Talking to the browser ---

    private static Map<String, Object> map(Object... keysAndValues) {
        Map<String, Object> map = new LinkedHashMap<>();
        for (int i = 0; i < keysAndValues.length; i += 2) {
            map.put((String) keysAndValues[i], keysAndValues[i + 1]);
        }
        return map;
    }

    private static Map<String, Object> snapshot() {
        synchronized (LOCK) {
            List<Object> shapes = new ArrayList<>();
            for (Shape shape : SHAPES.values()) {
                shapes.add(shape.toMap());
            }
            Map<String, Object> images = new LinkedHashMap<>();
            for (Map.Entry<Integer, String> image : IMAGES.entrySet()) {
                images.put(String.valueOf(image.getKey()), image.getValue());
            }
            return map("run", RUN_ID, "background", cssColor(background), "shapes", shapes,
                "images", images, "canvasEvents", specs(CANVAS_EVENTS));
        }
    }

    private static void broadcast(Object message, boolean dirty) {
        synchronized (LOCK) {
            for (BlockingQueue<Object> client : CLIENTS) {
                client.add(message);
            }
        }
        if (dirty) {
            DIRTY.offer(true);
        }
    }

    private static BlockingQueue<Object> addClient() {
        BlockingQueue<Object> client = new LinkedBlockingQueue<>();
        synchronized (LOCK) {
            client.add(map("type", "scene", "scene", snapshot()));
            client.addAll(PENDING_SAVES.values());
            CLIENTS.add(client);
        }
        return client;
    }

    private static void receiveSave(Map<?, ?> body) {
        Map<String, Object> message;
        synchronized (LOCK) {
            Object token = body.get("token");
            message = token instanceof Number ? PENDING_SAVES.remove(((Number) token).intValue()) : null;
        }
        Object data = body.get("data");
        if (message == null || !(data instanceof String) || !((String) data).contains(",")) {
            return;
        }
        Path path = outDir.resolve(message.get("name") + ".png");
        try {
            Files.write(path, Base64.getDecoder().decode(((String) data).split(",", 2)[1]));
            System.out.println("Saved " + path);
        } catch (IOException | IllegalArgumentException error) {
            System.out.println("Easy Draw could not save " + path + ": " + error.getMessage());
        }
    }

    private static void startServer(int startPort) {
        if (server != null) {
            return;
        }
        for (int attempt = 0; attempt < 20 && server == null; attempt++) {
            try {
                server = HttpServer.create(new InetSocketAddress("127.0.0.1", startPort + attempt), 0);
            } catch (IOException error) {
                server = null;
            }
        }
        if (server == null) {
            System.out.println("Easy Draw could not start its web server, so events will not work. "
                + "Your drawing will still be saved to " + HTML_FILE + ".");
            return;
        }
        port = server.getAddress().getPort();
        server.setExecutor(Executors.newCachedThreadPool(task -> {
            Thread thread = new Thread(task, "EasyDraw-server");
            thread.setDaemon(true);
            return thread;
        }));
        server.createContext("/", EasyDraw::handleRequest);
        // Threads copy daemon-ness from the thread that starts them, so start the server
        // from a daemon thread. That way it never keeps your program from ending.
        Thread starter = new Thread(server::start);
        starter.setDaemon(true);
        starter.start();
        try {
            starter.join();
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
        }
    }

    private static void handleRequest(HttpExchange exchange) throws IOException {
        try {
            String method = exchange.getRequestMethod();
            String path = exchange.getRequestURI().getPath();
            cors(exchange.getResponseHeaders());
            if (method.equals("OPTIONS")) {
                empty(exchange, 204);
            } else if (method.equals("GET") && (path.equals("/") || path.equals("/index.html"))) {
                String html;
                synchronized (LOCK) {
                    html = buildHtml(true);
                }
                exchange.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
                exchange.getResponseHeaders().set("Cache-Control", "no-store");
                send(exchange, 200, html.getBytes(StandardCharsets.UTF_8));
            } else if (method.equals("GET") && path.equals("/events")) {
                stream(exchange);
            } else if (method.equals("GET") && path.equals("/image")) {
                sendImage(exchange);
            } else if (method.equals("POST") && (path.equals("/event") || path.equals("/save"))) {
                Object body;
                try (InputStream in = exchange.getRequestBody()) {
                    body = Json.parse(new String(in.readAllBytes(), StandardCharsets.UTF_8));
                } catch (RuntimeException error) {
                    empty(exchange, 400);
                    return;
                }
                if (body instanceof Map) {
                    if (path.equals("/event")) {
                        dispatch((Map<?, ?>) body);
                    } else {
                        receiveSave((Map<?, ?>) body);
                    }
                }
                empty(exchange, 204);
            } else {
                empty(exchange, 404);
            }
        } finally {
            exchange.close();
        }
    }

    private static void cors(Headers headers) {
        headers.set("Access-Control-Allow-Origin", "*");
        headers.set("Access-Control-Allow-Headers", "Content-Type");
        headers.set("Access-Control-Allow-Private-Network", "true");
    }

    private static void empty(HttpExchange exchange, int status) throws IOException {
        exchange.sendResponseHeaders(status, -1);
    }

    private static void send(HttpExchange exchange, int status, byte[] body) throws IOException {
        exchange.sendResponseHeaders(status, body.length);
        try (OutputStream out = exchange.getResponseBody()) {
            out.write(body);
        }
    }

    /** Server-sent events: pushes drawing changes to the browser as they happen. */
    private static void stream(HttpExchange exchange) throws IOException {
        exchange.getResponseHeaders().set("Content-Type", "text/event-stream");
        exchange.getResponseHeaders().set("Cache-Control", "no-store");
        exchange.sendResponseHeaders(200, 0);
        BlockingQueue<Object> client = addClient();
        try (OutputStream out = exchange.getResponseBody()) {
            out.write("retry: 1000\n\n".getBytes(StandardCharsets.UTF_8));
            out.flush();
            while (true) {
                Object first = client.poll(1, TimeUnit.SECONDS);
                if (first == null) {
                    out.write(": ping\n\n".getBytes(StandardCharsets.UTF_8));
                    out.flush();
                    continue;
                }
                List<Object> messages = new ArrayList<>();
                messages.add(first);
                client.drainTo(messages);
                out.write(("data: " + Json.write(messages) + "\n\n").getBytes(StandardCharsets.UTF_8));
                out.flush();
            }
        } catch (IOException | InterruptedException error) {
            // The browser tab closed.
        } finally {
            synchronized (LOCK) {
                CLIENTS.remove(client);
            }
        }
    }

    /** Downloads an internet image for the browser when the image's site will not share it with the page. */
    private static void sendImage(HttpExchange exchange) throws IOException {
        String src = null;
        String query = exchange.getRequestURI().getRawQuery();
        if (query != null) {
            for (String part : query.split("&")) {
                if (part.startsWith("id=")) {
                    try {
                        int imageId = Integer.parseInt(URLDecoder.decode(part.substring(3), StandardCharsets.UTF_8));
                        synchronized (LOCK) {
                            src = IMAGES.get(imageId);
                        }
                    } catch (NumberFormatException error) {
                        src = null;
                    }
                }
            }
        }
        if (src == null || !isUrl(src)) {
            empty(exchange, 404);
            return;
        }
        Object[] download;
        try {
            download = ImageFile.download(src);
        } catch (EasyDrawException error) {
            System.out.println(error.getMessage());
            empty(exchange, 502);
            return;
        }
        exchange.getResponseHeaders().set("Content-Type", (String) download[1]);
        send(exchange, 200, (byte[]) download[0]);
    }

    private static String liveUrl() {
        return "http://localhost:" + port + "/";
    }

    private static void openBrowser() {
        // Give a tab left open from an earlier run a moment to reconnect first.
        sleep(1500);
        synchronized (LOCK) {
            if (!CLIENTS.isEmpty()) {
                return;
            }
        }
        String url = liveUrl();
        String os = System.getProperty("os.name", "").toLowerCase(Locale.ROOT);
        List<String[]> commands = new ArrayList<>();
        if (os.contains("win")) {
            commands.add(new String[] {"rundll32", "url.dll,FileProtocolHandler", url});
        } else if (os.contains("mac")) {
            commands.add(new String[] {"open", url});
        } else {
            commands.add(new String[] {"xdg-open", url});
            commands.add(new String[] {"wslview", url});
            commands.add(new String[] {"cmd.exe", "/c", "start", url});
        }
        for (String[] command : commands) {
            try {
                Process process = new ProcessBuilder(command)
                    .redirectOutput(ProcessBuilder.Redirect.DISCARD)
                    .redirectError(ProcessBuilder.Redirect.DISCARD)
                    .start();
                if (process.waitFor() == 0) {
                    return;
                }
            } catch (IOException error) {
                // Try the next way of opening a browser.
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
                return;
            }
        }
    }

    private static Path htmlPath() {
        return outDir.resolve(HTML_FILE);
    }

    private static void writeHtml() {
        if (!loaded) {
            return;
        }
        String html;
        synchronized (LOCK) {
            html = buildHtml(false);
        }
        Path path = htmlPath();
        Path temp = outDir.resolve(HTML_FILE + ".tmp");
        try {
            Files.writeString(temp, html, StandardCharsets.UTF_8);
            Files.move(temp, path, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException error) {
            System.out.println("Easy Draw could not write " + path + ": " + error.getMessage());
        }
    }

    private static void writerLoop() {
        while (true) {
            try {
                DIRTY.take();
            } catch (InterruptedException error) {
                return;
            }
            sleep(500);
            DIRTY.clear();
            writeHtml();
        }
    }

    private static String buildHtml(boolean live) {
        Object serverUrl;
        if (live) {
            serverUrl = "";
        } else if (server != null) {
            serverUrl = "http://localhost:" + port;
        } else {
            serverUrl = null;
        }
        Map<String, Object> data = map(
            "config", map("server", serverUrl, "keys", KEY_KEYSYMS, "chars", CHAR_KEYSYMS, "version", VERSION),
            "scene", snapshot());
        return HTML_TEMPLATE.replace("__EASY_DRAW_DATA__", Json.write(data).replace("</", "<\\/"));
    }

    /** A tiny JSON reader and writer, so Easy Draw does not need any libraries. */
    private static final class Json {
        static String write(Object value) {
            StringBuilder out = new StringBuilder();
            write(out, value);
            return out.toString();
        }

        private static void write(StringBuilder out, Object value) {
            if (value == null) {
                out.append("null");
            } else if (value instanceof String) {
                writeString(out, (String) value);
            } else if (value instanceof Boolean || value instanceof Integer || value instanceof Long) {
                out.append(value);
            } else if (value instanceof Number) {
                double number = ((Number) value).doubleValue();
                out.append(Double.isFinite(number) ? String.valueOf(number) : "null");
            } else if (value instanceof Map) {
                out.append('{');
                boolean first = true;
                for (Map.Entry<?, ?> entry : ((Map<?, ?>) value).entrySet()) {
                    if (!first) {
                        out.append(',');
                    }
                    first = false;
                    writeString(out, String.valueOf(entry.getKey()));
                    out.append(':');
                    write(out, entry.getValue());
                }
                out.append('}');
            } else if (value instanceof Collection) {
                out.append('[');
                boolean first = true;
                for (Object item : (Collection<?>) value) {
                    if (!first) {
                        out.append(',');
                    }
                    first = false;
                    write(out, item);
                }
                out.append(']');
            } else {
                writeString(out, value.toString());
            }
        }

        private static void writeString(StringBuilder out, String text) {
            out.append('"');
            for (int i = 0; i < text.length(); i++) {
                char c = text.charAt(i);
                switch (c) {
                    case '"': out.append("\\\""); break;
                    case '\\': out.append("\\\\"); break;
                    case '\n': out.append("\\n"); break;
                    case '\r': out.append("\\r"); break;
                    case '\t': out.append("\\t"); break;
                    case '\b': out.append("\\b"); break;
                    case '\f': out.append("\\f"); break;
                    default:
                        if (c < 0x20 || c == 0x2028 || c == 0x2029) {
                            out.append(String.format("\\u%04x", (int) c));
                        } else {
                            out.append(c);
                        }
                }
            }
            out.append('"');
        }

        static Object parse(String text) {
            Json parser = new Json(text);
            parser.skipSpace();
            Object value = parser.value();
            parser.skipSpace();
            if (parser.pos != text.length()) {
                throw new IllegalArgumentException("Extra text after JSON");
            }
            return value;
        }

        private final String text;
        private int pos = 0;

        private Json(String text) {
            this.text = text;
        }

        private void skipSpace() {
            while (pos < text.length() && Character.isWhitespace(text.charAt(pos))) {
                pos++;
            }
        }

        private char next() {
            if (pos >= text.length()) {
                throw new IllegalArgumentException("Unexpected end of JSON");
            }
            return text.charAt(pos++);
        }

        private void expect(String word) {
            if (!text.startsWith(word, pos)) {
                throw new IllegalArgumentException("Bad JSON at " + pos);
            }
            pos += word.length();
        }

        private Object value() {
            skipSpace();
            char c = text.charAt(pos);
            if (c == '{') {
                pos++;
                Map<String, Object> map = new LinkedHashMap<>();
                skipSpace();
                if (text.charAt(pos) == '}') {
                    pos++;
                    return map;
                }
                while (true) {
                    skipSpace();
                    Object key = value();
                    if (!(key instanceof String)) {
                        throw new IllegalArgumentException("Bad JSON key at " + pos);
                    }
                    skipSpace();
                    expect(":");
                    map.put((String) key, value());
                    skipSpace();
                    char end = next();
                    if (end == '}') {
                        return map;
                    }
                    if (end != ',') {
                        throw new IllegalArgumentException("Bad JSON at " + pos);
                    }
                }
            }
            if (c == '[') {
                pos++;
                List<Object> list = new ArrayList<>();
                skipSpace();
                if (text.charAt(pos) == ']') {
                    pos++;
                    return list;
                }
                while (true) {
                    list.add(value());
                    skipSpace();
                    char end = next();
                    if (end == ']') {
                        return list;
                    }
                    if (end != ',') {
                        throw new IllegalArgumentException("Bad JSON at " + pos);
                    }
                }
            }
            if (c == '"') {
                pos++;
                StringBuilder out = new StringBuilder();
                while (true) {
                    char ch = next();
                    if (ch == '"') {
                        return out.toString();
                    }
                    if (ch != '\\') {
                        out.append(ch);
                        continue;
                    }
                    char escape = next();
                    switch (escape) {
                        case 'n': out.append('\n'); break;
                        case 'r': out.append('\r'); break;
                        case 't': out.append('\t'); break;
                        case 'b': out.append('\b'); break;
                        case 'f': out.append('\f'); break;
                        case 'u':
                            out.append((char) Integer.parseInt(text.substring(pos, pos + 4), 16));
                            pos += 4;
                            break;
                        default: out.append(escape);
                    }
                }
            }
            if (text.startsWith("true", pos)) {
                pos += 4;
                return true;
            }
            if (text.startsWith("false", pos)) {
                pos += 5;
                return false;
            }
            if (text.startsWith("null", pos)) {
                pos += 4;
                return null;
            }
            int start = pos;
            while (pos < text.length() && "+-0123456789.eE".indexOf(text.charAt(pos)) >= 0) {
                pos++;
            }
            return Double.parseDouble(text.substring(start, pos));
        }
    }

    // The page below is the same one easy_draw.py makes. Keep the two in sync.
    private static final String HTML_TEMPLATE = """
<!DOCTYPE html>
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
    const lines = String(s.text).split("\\n");
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
    return { Enter: "\\r", Tab: "\\t", Backspace: "\\b", Escape: "\\x1b" }[e.key] || "";
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
    if (count && !e.ctrlKey && !e.metaKey && !/^F\\d+$/.test(e.key)) e.preventDefault();
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

  function blobToDataURL(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  async function fetchDataURL(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(response.status);
    return blobToDataURL(await response.blob());
  }

  // A saved picture can only include internet images that are copied into it first.
  async function inlineImage(id, src) {
    if (src.startsWith("data:")) return src;
    try { return await fetchDataURL(src); } catch (err) { /* The site does not share the image with pages. */ }
    if (live) {
      try { return await fetchDataURL(CFG.server + "/image?id=" + id); } catch (err) { /* Python could not get it either. */ }
    }
    return null;
  }

  async function toPNG(s) {
    const images = {};
    const missing = [];
    await Promise.all(Object.keys(s.images).map(async (id) => {
      await loadImage(id, s.images[id]);
      images[id] = await inlineImage(id, s.images[id]);
      if (!images[id] && s.shapes.some((shape) => shape.kind === "image" && shape.img == id)) missing.push(s.images[id]);
    }));
    if (missing.length) console.warn("Easy Draw could not include these images in the saved picture:", missing);
    const svg = el("svg", { width: 600, height: 600, viewBox: "0 0 600 600" });
    svg.append(el("rect", { width: 600, height: 600, fill: s.background }));
    for (const shape of s.shapes) svg.append(build(shape, images));
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
    name = name.trim().replace(/\\.png$/i, "") + ".png";
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
""";
}

/*
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
*/
