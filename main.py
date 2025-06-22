import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import ImageGrab, ImageColor, ImageDraw, ImageTk, Image
from tkinter import colorchooser
from colormath.color_objects import sRGBColor, LCHabColor
from colormath.color_conversions import convert_color

from ttkbootstrap import colorutils, utility
import ctypes

# Make the application DPI-aware for better scaling on high-resolution displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except AttributeError:
    pass  # Not all Windows versions support this, or it might not be Windows

# Create the app's main window
class ColorDropperDialog:
    def __init__(self):
        global rgbColor, hslColor, hexColor, selectedColorWidget

        self.toplevel = None
        self.result = ttk.Variable()

    def build_screenshot_canvas(self):
        """Build the screenshot canvas"""
        self.screenshot_canvas = ttk.Canvas(self.toplevel, cursor='tcross', autostyle=False)
        self.screenshot_data = ImageGrab.grab()
        self.screenshot_image = ImageTk.PhotoImage(self.screenshot_data)
        self.screenshot_canvas.create_image(0, 0, image=self.screenshot_image, anchor=NW)
        self.screenshot_canvas.pack(fill=BOTH, expand=YES)

    def build_zoom_toplevel(self, master):
        """Build the toplevel widget that shows the zoomed version of
        the pixels underneath the mouse cursor."""
        zBoxheight = utility.scale_size(self.toplevel, 100)
        zBoxwidth = utility.scale_size(self.toplevel, 100)
        text_xoffset = utility.scale_size(self.toplevel, 50)
        text_yoffset = utility.scale_size(self.toplevel, 50)
        toplevel = ttk.Toplevel(master)
        toplevel.transient(master)
        if self.toplevel.winsys == 'x11':
            toplevel.attributes('-type', 'tooltip')
        else:
            toplevel.overrideredirect(True)

        toplevel.geometry(f'{zBoxwidth}x{zBoxheight}')
        toplevel.lift()

        self.zoom_canvas = ttk.Canvas(toplevel, borderwidth=1, height=self.zoom_height, width=self.zoom_width)
        self.zoom_canvas.create_image(0, 0, tags=['image'], anchor=NW)
        self.zoom_canvas.create_text(text_xoffset, text_yoffset, text="+", fill="white", tags=['indicator'])
        self.zoom_canvas.pack(fill="both", expand=True)
        self.zoom_toplevel = toplevel
        self.zoom_toplevel.place_window_center()

    def on_mouse_wheel(self, event: tk.Event):
        """Zoom in and out on the image underneath the mouse
        TODO Cross platform testing needed
        """
        if self.toplevel.winsys.lower() == 'win32':
            delta = -int(event.delta / 120)
        elif self.toplevel.winsys.lower() == 'aqua':
            delta = -event.delta
        elif event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        self.zoom_level += delta
        self.on_mouse_motion()

    def on_left_click(self, _):
        """Capture the color underneath the mouse cursor and destroy
        the toplevel widget"""
        # add logic here to capture the image color
        hx, rgbColorValue = self.get_hover_color()

        rgb_color = sRGBColor(rgbColorValue[0], rgbColorValue[1], rgbColorValue[2], is_upscaled=True)
        lch_color = convert_color(rgb_color, LCHabColor)

        mainRGBRedValue.set(str(rgb_color.rgb_r*255))
        mainRGBGreenValue.set(str(rgb_color.rgb_g*255))
        mainRGBBlueValue.set(str(rgb_color.rgb_b*255))

        mainLCHLightnessValue.set(str(lch_color.lch_l))
        mainLCHChromeValue.set(str(lch_color.lch_c))
        mainLCHHueValue.set(str(lch_color.lch_h))

        mainHexCodeValue.set(str(hx))

        selectedColorWidget.configure(bg=mainHexCodeValue.get())
        self.toplevel.destroy()
        self.zoom_toplevel.destroy()
        self.toplevel.grab_release()

        return rgbColorValue

    def on_right_click(self, _):
        """Close the color dropper without saving any color information"""
        self.zoom_toplevel.destroy()
        self.toplevel.grab_release()
        self.toplevel.destroy()

    def on_mouse_motion(self, event=None):
        """Callback for mouse motion"""
        if event is None:
            x, y = self.toplevel.winfo_pointerxy()
        else:
            x = event.x
            y = event.y
        # move snip window
        self.zoom_toplevel.geometry(f'+{x+self.zoom_xoffset}+{y+self.zoom_yoffset}')
        # update the snip image
        bbox = (x-self.zoom_level, y-self.zoom_level, x+self.zoom_level+1, y+self.zoom_level+1)
        size = (self.zoom_width, self.zoom_height)
        self.zoom_data = self.screenshot_data.crop(bbox).resize(size, Image.BOX)
        self.zoom_image = ImageTk.PhotoImage(self.zoom_data)
        self.zoom_canvas.itemconfig('image', image=self.zoom_image)
        hover_color, rgbColorValue = self.get_hover_color()
        contrast_color = colorutils.contrast_color(hover_color, 'hex')
        self.zoom_canvas.itemconfig('indicator', fill=contrast_color)

    def get_hover_color(self):
        """Get the color hovered over by the mouse cursor."""
        x1, y1, x2, y2 = self.zoom_canvas.bbox('indicator')
        x = x1 + (x2-x1)//2
        y = y1 + (y2-y2)//2
        r, g, b = self.zoom_data.getpixel((x, y))
        hx = colorutils.color_to_hex((r, g, b))
        rgbValue = [r, g, b]
        return hx, rgbValue

    def show(self):
        """Show the toplevel window"""
        self.toplevel = ttk.Toplevel(alpha=1)
        self.toplevel.wm_attributes('-fullscreen', True)
        self.build_screenshot_canvas()

        # event binding
        self.toplevel.bind("<Motion>", self.on_mouse_motion, "+")
        self.toplevel.bind("<Button-1>", self.on_left_click, "+")
        self.toplevel.bind("<Button-3>", self.on_right_click, "+")

        if self.toplevel.winsys.lower() == 'x11':
            self.toplevel.bind("<Button-4>", self.on_mouse_wheel, "+")
            self.toplevel.bind("<Button-5>", self.on_mouse_wheel, "+")
        else:
            self.toplevel.bind("<MouseWheel>", self.on_mouse_wheel, "+")

        # initial snip setup
        self.zoom_level = 2
        self.zoom_toplevel = None
        self.zoom_data = None
        self.zoom_image = None
        self.zoom_height = utility.scale_size(self.toplevel, 100)
        self.zoom_width = utility.scale_size(self.toplevel, 100)
        self.zoom_xoffset = utility.scale_size(self.toplevel, 10)
        self.zoom_yoffset = utility.scale_size(self.toplevel, 10)

        self.build_zoom_toplevel(self.toplevel)
        self.toplevel.grab_set()
        self.toplevel.lift('.')
        self.zoom_toplevel.lift(self.toplevel)

        self.on_mouse_motion()

#region Support Functions
def choose_color():
    picker = ColorDropperDialog()
    picker.show()
    del picker

def make_frame_5x5_grid(frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)
    frame.columnconfigure(3, weight=1)
    frame.columnconfigure(4, weight=1)

    frame.rowconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)
    frame.rowconfigure(2, weight=1)
    frame.rowconfigure(3, weight=1)
    frame.rowconfigure(4, weight=1)

def handle_window_close():
    global isOpen
    isOpen = False

def start_drag(event):
    # Store the initial position of the mouse relative to the window
    event.widget.offset_x = event.x
    event.widget.offset_y = event.y

def move_window(event):
    # Calculate new window position based on mouse movement and initial offset
    new_x = event.x_root - event.widget.offset_x
    new_y = event.y_root - event.widget.offset_y
    window.geometry(f'+{new_x}+{new_y}')

def choose_color_dialog():
    selectedColor = colorchooser.askcolor()
    rgbColorValue = selectedColor[0]
    rgb_color = sRGBColor(rgbColorValue[0], rgbColorValue[1], rgbColorValue[2], is_upscaled=True)
    lch_color = convert_color(rgb_color, LCHabColor)

    mainRGBRedValue.set(str(rgbColorValue[0]))
    mainRGBGreenValue.set(str(rgbColorValue[1]))
    mainRGBBlueValue.set(str(rgbColorValue[2]))

    mainLCHLightnessValue.set(str(lch_color.lch_l))
    mainLCHChromeValue.set(str(lch_color.lch_c))
    mainLCHHueValue.set(str(lch_color.lch_h))

    mainHexCodeValue.set(str(selectedColor[1]))

    selectedColorWidget.configure(bg=selectedColor[1])

#endregion

#region Window Setup and Initiation
isOpen = True

window = ttk.Window(themename='darkly')
window.title("Onscreen Color Selector")
window.geometry("400x400")
window.resizable(False, False)
window.attributes('-topmost', True)
window.iconbitmap('colorpicker.ico')

window.overrideredirect(False)
window.place_window_center()

#endregion

#region Color Value Variables

mainRGBRedValue = ttk.StringVar()
mainRGBGreenValue = ttk.StringVar()
mainRGBBlueValue = ttk.StringVar()
mainLCHLightnessValue = ttk.StringVar()
mainLCHChromeValue = ttk.StringVar()
mainLCHHueValue = ttk.StringVar()
mainHexCodeValue = ttk.StringVar()

cc1mainRGBRedValue = ttk.StringVar()
cc1mainRGBGreenValue = ttk.StringVar()
cc1mainRGBBlueValue = ttk.StringVar()
cc1mainLCHLightnessValue = ttk.StringVar()
cc1mainLCHChromeValue = ttk.StringVar()
cc1mainLCHHueValue = ttk.StringVar()
cc1mainHexCodeValue = ttk.StringVar()

cc2mainRGBRedValue = ttk.StringVar()
cc2mainRGBGreenValue = ttk.StringVar()
cc2mainRGBBlueValue = ttk.StringVar()
cc2mainLCHLightnessValue = ttk.StringVar()
cc2mainLCHChromeValue = ttk.StringVar()
cc2mainLCHHueValue = ttk.StringVar()
cc2mainHexCodeValue = ttk.StringVar()

#endregion

#region UI Setup

mainContainer = ttk.Notebook(window)
mainContainer.pack(fill="both", expand=True, padx=5, pady=5)

colorSelectorWindow = ttk.Frame(mainContainer)
make_frame_5x5_grid(colorSelectorWindow)

contrastCheckerWindow = ttk.Frame(mainContainer)
make_frame_5x5_grid(contrastCheckerWindow)

mainContainer.add(colorSelectorWindow, text='  Color Picker  ', padding=5)
mainContainer.add(contrastCheckerWindow, text='Contrast Checker', padding=5)

pickColorButton = ttk.Button(colorSelectorWindow,text="Activate Color Picker", command=choose_color)
pickColorButton.grid(column=0, row=0, sticky="nsew", columnspan=5, rowspan=1, padx=5, pady=5)

redLabel = ttk.LabelFrame(colorSelectorWindow, text="Red")
redLabel.grid(column=1, row=1, sticky="nsew", padx=5, pady=5)
greenLabel = ttk.LabelFrame(colorSelectorWindow, text="Green")
greenLabel.grid(column=2, row=1, sticky="nsew", padx=5, pady=5)
blueLabel = ttk.LabelFrame(colorSelectorWindow, text="Blue")
blueLabel.grid(column=3, row=1, sticky="nsew", padx=5, pady=5)

rgbRedValueWidget = ttk.Entry(redLabel, textvariable=mainRGBRedValue)
rgbRedValueWidget.pack(expand=True, fill="both")
rgbGreenValueWidget = ttk.Entry(greenLabel, textvariable=mainRGBGreenValue)
rgbGreenValueWidget.pack(expand=True, fill="both")
rgbBlueValueWidget = ttk.Entry(blueLabel, textvariable=mainRGBBlueValue)
rgbBlueValueWidget.pack(expand=True, fill="both")

LightnessLabel = ttk.LabelFrame(colorSelectorWindow, text="Lightness")
LightnessLabel.grid(column=1, row=2, sticky="nsew", padx=5, pady=5)
chromaLabel = ttk.LabelFrame(colorSelectorWindow, text="Chroma")
chromaLabel.grid(column=2, row=2, sticky="nsew", padx=5, pady=5)
hueLabel = ttk.LabelFrame(colorSelectorWindow, text="Hue")
hueLabel.grid(column=3, row=2, sticky="nsew", padx=5, pady=5)

lchLightValueWidget = ttk.Entry(LightnessLabel, textvariable=mainLCHLightnessValue)
lchLightValueWidget.pack(expand=True, fill="both")
lchChromaValueWidget = ttk.Entry(chromaLabel, textvariable=mainLCHChromeValue)
lchChromaValueWidget.pack(expand=True, fill="both")
lchHueValueWidget = ttk.Entry(hueLabel, textvariable=mainLCHHueValue)
lchHueValueWidget.pack(expand=True, fill="both")

hexLabel = ttk.LabelFrame(colorSelectorWindow, text="Hex Code")
hexLabel.grid(column=1, row=3, sticky="nsew", columnspan=3, rowspan=1, padx=5, pady=5)

hexValueWidget = ttk.Entry(hexLabel, textvariable=mainHexCodeValue)
hexValueWidget.pack(expand=True, fill="both")

selectedColorWidget = tk.Button(colorSelectorWindow, command=choose_color_dialog, borderwidth=20)
selectedColorWidget.grid(column=0, row=5, sticky="nsew", columnspan=5, padx=5, pady=5)
selectedColorWidget.configure(bg="#ffffff")

#endregion

# Start the event loop
if __name__ == "__main__":
    window.mainloop()
