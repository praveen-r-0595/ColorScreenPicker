import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import ImageGrab, ImageColor, ImageDraw, ImageTk, Image
from tkinter import colorchooser
from colormath2.color_objects import sRGBColor, LCHabColor, BaseRGBColor
from colormath2.color_conversions import convert_color

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
        self.current_active_picker = None

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
        """
        Zoom in and out on the image underneath the mouse
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

        rgbR100 = round((rgbColorValue[0]*1)/255, 2)
        rgbG100 = round((rgbColorValue[1]*1)/255, 2)
        rgbB100 = round((rgbColorValue[2]*1)/255, 2)
        rgb100 = (rgbR100, rgbG100, rgbB100)

        rgb_color = sRGBColor(rgbR100, rgbG100, rgbB100, is_upscaled=False)

        print('rgbColorValue', rgb100)
        lch_color = convert_color(rgb_color, through_rgb_type=sRGBColor, target_cs=LCHabColor, target_illuminant="e")

        match self.current_active_picker:
            case 'mainPicker':
                mainRGBRedValue.set(str(rgbColorValue[0]))
                mainRGBGreenValue.set(str(rgbColorValue[1]))
                mainRGBBlueValue.set(str(rgbColorValue[2]))

                mainLCHLightnessValue.set(str(round(lch_color.lch_l,2)))
                mainLCHChromeValue.set(str(round(lch_color.lch_c,2)))
                mainLCHHueValue.set(str(round(lch_color.lch_h,2)))

                mainHexCodeValue.set(str(hx))

                selectedColorWidget.configure(bg=mainHexCodeValue.get())

            case "cc1Picker":
                cc1mainRGBRedValue.set(str(rgbColorValue[0]))
                cc1mainRGBGreenValue.set(str(rgbColorValue[1]))
                cc1mainRGBBlueValue.set(str(rgbColorValue[2]))

                cc1mainLCHLightnessValue.set(str(round(lch_color.lch_l, 2)))
                cc1mainLCHChromeValue.set(str(round(lch_color.lch_c, 2)))
                cc1mainLCHHueValue.set(str(round(lch_color.lch_h, 2)))

                cc1mainHexCodeValue.set(str(hx))

            case "cc2Picker":
                cc2mainRGBRedValue.set(str(rgbColorValue[0]))
                cc2mainRGBGreenValue.set(str(rgbColorValue[1]))
                cc2mainRGBBlueValue.set(str(rgbColorValue[2]))

                cc2mainLCHLightnessValue.set(str(round(lch_color.lch_l, 2)))
                cc2mainLCHChromeValue.set(str(round(lch_color.lch_c, 2)))
                cc2mainLCHHueValue.set(str(round(lch_color.lch_h, 2)))

                cc2mainHexCodeValue.set(str(hx))

            case _:
                pass


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

    def show(self, stringActivePicker):
        """Show the toplevel window"""
        self.current_active_picker = stringActivePicker
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

def srgb_to_linear(c):
    """Converts an sRGB component (0-1) to linear RGB."""
    if c <= 0.03928:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4

def get_luminance(rgb):
    """Calculates the relative luminance for an RGB color (0-255)."""
    r, g, b = [c / 255.0 for c in rgb]  # Normalize to 0-1
    r_linear = srgb_to_linear(r)
    g_linear = srgb_to_linear(g)
    b_linear = srgb_to_linear(b)
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear

def get_contrast_ratio(rgb1, rgb2):
    """Calculates the contrast ratio between two RGB colors (0-255)."""
    l1 = get_luminance(rgb1)
    l2 = get_luminance(rgb2)

    # Ensure L1 is the lighter color's luminance
    if l1 < l2:
        l1, l2 = l2, l1

    return (l1 + 0.05) / (l2 + 0.05)

def calculate_and_show_contrast_ratio():
    """Calculates the contrast ratio between two RGB colors (0-255)."""
    if (cc1mainRGBRedValue.get() != None) and (cc2mainRGBRedValue.get() != None):
        rgb1 = (float(cc1mainRGBRedValue.get()),float(cc1mainRGBGreenValue.get()) ,float(cc1mainRGBBlueValue.get()))
        rgb2 = (float(cc2mainRGBRedValue.get()),float(cc2mainRGBGreenValue.get()) ,float(cc2mainRGBBlueValue.get()))

        contrast_ratio_value = get_contrast_ratio(rgb1, rgb2)
        print(contrast_ratio_value)

        contrastRatioValue.set(str(contrast_ratio_value))

        if(contrast_ratio_value > 2):
            contrastPassFailWidget.configure(background='#1e7800')
            contrastPassFailWidget.configure(foreground='#ffffff')
            contrastPassFailWidget.configure(text="PASS")
        else:
            contrastPassFailWidget.configure(background='#ad0a02')
            contrastPassFailWidget.configure(foreground='#ffffff')
            contrastPassFailWidget.configure(text="FAIL")


def choose_color(stringActivePicker):
    picker = ColorDropperDialog()
    picker.show(stringActivePicker)
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

def make_frame_6x6_grid(frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)
    frame.columnconfigure(3, weight=1)
    frame.columnconfigure(4, weight=1)
    frame.columnconfigure(5, weight=1)

    frame.rowconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)
    frame.rowconfigure(2, weight=1)
    frame.rowconfigure(3, weight=1)
    frame.rowconfigure(4, weight=1)
    frame.rowconfigure(5, weight=1)

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

contrastRatioValue = ttk.StringVar()

#endregion

#region UI Setup

mainContainer = ttk.Notebook(window)
mainContainer.pack(fill="both", expand=True, padx=5, pady=5)

colorSelectorWindow = ttk.Frame(mainContainer)
make_frame_5x5_grid(colorSelectorWindow)

contrastCheckerWindow = ttk.Frame(mainContainer)
make_frame_6x6_grid(contrastCheckerWindow)

mainContainer.add(colorSelectorWindow, text='  Color Picker  ', padding=5)
mainContainer.add(contrastCheckerWindow, text='Contrast Checker', padding=0)

pickColorButton = ttk.Button(colorSelectorWindow,text="Activate Color Picker", command=lambda : choose_color("mainPicker"))
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
LightnessLabel.grid(column=1, row=2, sticky="nsew", padx=5, pady=5, columnspan=5)
chromaLabel = ttk.LabelFrame(colorSelectorWindow, text="Chroma")
#chromaLabel.grid(column=2, row=2, sticky="nsew", padx=5, pady=5)
hueLabel = ttk.LabelFrame(colorSelectorWindow, text="Hue")
#hueLabel.grid(column=3, row=2, sticky="nsew", padx=5, pady=5)

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

ccTopPanel = ttk.Frame(contrastCheckerWindow)
ccTopPanel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5, columnspan=6, rowspan=1)
ccRightPanel = ttk.Frame(contrastCheckerWindow)
ccRightPanel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5, columnspan=3, rowspan=4)
ccLeftPanel = ttk.Frame(contrastCheckerWindow)
ccLeftPanel.grid(row=1, column=3, sticky="nsew", padx=5, pady=5, columnspan=3, rowspan=4)
ccBottomPanel = ttk.Frame(contrastCheckerWindow)
ccBottomPanel.grid(row=5, column=0, sticky="nsew", padx=5, pady=5, columnspan=6, rowspan=1)

make_frame_6x6_grid(ccTopPanel)
make_frame_6x6_grid(ccRightPanel)
make_frame_6x6_grid(ccLeftPanel)
make_frame_6x6_grid(ccBottomPanel)

cc1redLabel = ttk.LabelFrame(ccRightPanel, text="Color 1 Red")
cc1redLabel.grid(column=0, row=0, sticky="nsew", padx=2, pady=2, columnspan=6)
cc1greenLabel = ttk.LabelFrame(ccRightPanel, text="Color 1 Green")
cc1greenLabel.grid(column=0, row=1, sticky="nsew", padx=2, pady=2, columnspan=6)
cc1blueLabel = ttk.LabelFrame(ccRightPanel, text="Color 1 Blue")
cc1blueLabel.grid(column=0, row=2, sticky="nsew", padx=2, pady=2, columnspan=6)
cc1LightnessLabel = ttk.LabelFrame(ccRightPanel, text="Color 1 Lightness")
cc1LightnessLabel.grid(column=0, row=3, sticky="nsew", padx=2, pady=2, columnspan=6)
cc1mainHexLabel = ttk.LabelFrame(ccRightPanel, text="Color 1 Hex Code")
cc1mainHexLabel.grid(column=0, row=4, sticky="nsew", padx=2, pady=2, columnspan=6)

cc1rgbRedValueWidget = ttk.Entry(cc1redLabel, textvariable=cc1mainRGBRedValue)
cc1rgbRedValueWidget.pack(expand=True, fill="both")
cc1rgbGreenValueWidget = ttk.Entry(cc1greenLabel, textvariable=cc1mainRGBGreenValue)
cc1rgbGreenValueWidget.pack(expand=True, fill="both")
cc1rgbBlueValueWidget = ttk.Entry(cc1blueLabel, textvariable=cc1mainRGBBlueValue)
cc1rgbBlueValueWidget.pack(expand=True, fill="both")
cc1LightnessValueWidget = ttk.Entry(cc1LightnessLabel, textvariable=cc1mainLCHLightnessValue)
cc1LightnessValueWidget.pack(expand=True, fill="both")
cc1mainHexValueWidget = ttk.Entry(cc1mainHexLabel, textvariable=cc1mainHexCodeValue)
cc1mainHexValueWidget.pack(expand=True, fill="both")

cc2redLabel = ttk.LabelFrame(ccLeftPanel, text="Color 2 Red")
cc2redLabel.grid(column=0, row=0, sticky="nsew", padx=2, pady=2, columnspan=6)
cc2greenLabel = ttk.LabelFrame(ccLeftPanel, text="Color 2 Green")
cc2greenLabel.grid(column=0, row=1, sticky="nsew", padx=2, pady=2, columnspan=6)
cc2blueLabel = ttk.LabelFrame(ccLeftPanel, text="Color 2 Blue")
cc2blueLabel.grid(column=0, row=2, sticky="nsew", padx=2, pady=2, columnspan=6)
cc2LightnessLabel = ttk.LabelFrame(ccLeftPanel, text="Color 2 Lightness")
cc2LightnessLabel.grid(column=0, row=3, sticky="nsew", padx=2, pady=2, columnspan=6)
cc2mainHexLabel = ttk.LabelFrame(ccLeftPanel, text="Color 2 Hex Code")
cc2mainHexLabel.grid(column=0, row=4, sticky="nsew", padx=2, pady=2, columnspan=6)

cc2rgbRedValueWidget = ttk.Entry(cc2redLabel, textvariable=cc2mainRGBRedValue)
cc2rgbRedValueWidget.pack(expand=True, fill="both")
cc2rgbGreenValueWidget = ttk.Entry(cc2greenLabel, textvariable=cc2mainRGBGreenValue)
cc2rgbGreenValueWidget.pack(expand=True, fill="both")
cc2rgbBlueValueWidget = ttk.Entry(cc2blueLabel, textvariable=cc2mainRGBBlueValue)
cc2rgbBlueValueWidget.pack(expand=True, fill="both")
cc2LightnessValueWidget = ttk.Entry(cc2LightnessLabel, textvariable=cc2mainLCHLightnessValue)
cc2LightnessValueWidget.pack(expand=True, fill="both")
cc2mainHexValueWidget = ttk.Entry(cc2mainHexLabel, textvariable=cc2mainHexCodeValue)
cc2mainHexValueWidget.pack(expand=True, fill="both")

cc1ColorPickerButton = ttk.Button(ccTopPanel, text="Color 1 Picker", command=lambda : choose_color("cc1Picker"))
cc1ColorPickerButton.grid(column=0, row=0, sticky="nsew", padx=5, pady=5, columnspan=3, rowspan=6)

cc2pickColorButton = ttk.Button(ccTopPanel, text="Color 2 Picker", command=lambda : choose_color("cc2Picker"))
cc2pickColorButton.grid(column=3, row=0, sticky="nsew", padx=5, pady=5, columnspan=3, rowspan=6)

contrastCheckButton = ttk.Button(ccBottomPanel, text="Contrast Ratio", command=calculate_and_show_contrast_ratio)
contrastCheckButton.grid(column=0, row=0, sticky="nsew", padx=5, pady=5, columnspan=3, rowspan=6)

contrastRatioValueWidget = ttk.Entry(ccBottomPanel, textvariable=contrastRatioValue)
contrastRatioValueWidget.grid(column=3, row=0, sticky="nsew", padx=5, pady=5, columnspan=1, rowspan=6)

contrastPassFailWidget = tk.Button(ccBottomPanel, text="Status")
contrastPassFailWidget.grid(column=4, row=0, sticky="nsew", padx=5, pady=5, columnspan=3, rowspan=6)
contrastPassFailWidget.configure(state=tk.DISABLED)
contrastPassFailWidget.configure(background="#ffffff")

#endregion

# Start the event loop
if __name__ == "__main__":
    window.mainloop()
