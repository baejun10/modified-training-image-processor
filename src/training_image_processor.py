from pygame.rect import Rect
from pygame_gui.elements.ui_image import UIImage
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.windows.ui_file_dialog import UIFileDialog
import pygame_gui
import pygame
import pygame.locals
import pygame as pg
from tkinter import *
from tkinter import messagebox
import os
import shutil
import time

pygame.init()
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


class SelectionBox:
    def __init__(self):
        self.location = [0, 0]
        self.size = image_res

    def draw(self):
        s = self.size/2
        rect1 = Rect(
            (self.location[0]-s, self.location[1]-s), (self.size, self.size))
        rect2 = Rect(
            (self.location[0]-s-1, self.location[1]-s-1), (self.size+2, self.size+2))
        black = (0, 0, 0)
        white = (255, 255, 255)
        pygame.draw.rect(screen, black, rect1, width=1)
        pygame.draw.rect(screen, white, rect2, width=1)

    def clamp(self, rect: Rect):
        s = self.size/32
        max_s = self.size/2
        if rect.bottom > rect.right:
            min_x = rect.left + s
            max_x = rect.right - s
            min_y = rect.top + max_s
            max_y = rect.bottom - max_s
        else:
            min_x = rect.left + max_s
            max_x = rect.right - max_s
            min_y = rect.top + s
            max_y = rect.bottom - s
        self.location[0] = clamp(self.location[0], min_x, max_x)
        self.location[1] = clamp(self.location[1], min_y, max_y)

    def image_rect(self):
        s = self.size/2
        rect = Rect(
            (self.location[0]-s, self.location[1]-s), (self.size, self.size))
        rect.move_ip(0, -ui_bar_height)
        scale = image.get_size()[0]/scaled_image.get_size()[0]
        rect = Rect((rect.left*scale, rect.top*scale),
                    (rect.width*scale, rect.height*scale))
        return rect


class InputBox:

    def __init__(self, x, y, w, h, text=''):
        self.TEXT_COLOR_ACTIVE = 'grey'
        self.TEXT_COLOR_INACTIVE = 'grey50'
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text_color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        self.text_color = self.TEXT_COLOR_ACTIVE if self.active else self.TEXT_COLOR_INACTIVE
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    print(self.text)
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
        self.txt_surface = FONT.render(self.text, True, self.text_color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+1))
        # Blit the rect.
        pg.draw.rect(screen, self.color, self.rect, 2)


def ProcessedImage():
    rect = selection_box.image_rect()
    pimage = pygame.Surface((rect.width, rect.height))
    global image
    pimage.blit(image, (0, 0), area=rect)
    pimage = pygame.transform.smoothscale(pimage, (image_res, image_res))
    return pimage

# add image repeat feature when press ctrl


def ClickImage(repeat=False):
    processed_image = ProcessedImage()
    output_path = os.path.join(open_folder, 'outputs')
    originals_path = os.path.join(open_folder, 'originals')

    try:
        os.mkdir(output_path)
    except FileExistsError:
        pass
    try:
        os.mkdir(originals_path)
    except FileExistsError:
        pass

    #output_name = os.path.join(output_path, files[0])
    # change output file name from filename to image_namebox
    t_len = len(image_namebox.text)

    # cut extension name like .png
    for i in range(0, t_len):
        if (image_namebox.text[i] == '.'):
            image_namebox.text = image_namebox.text[0:i-1]

    output_name = os.path.join(output_path, image_namebox.text+'.png')
    if not os.path.exists(output_name):
        pygame.image.save(processed_image, output_name)
    else:
        saved = False
        suffix = 1
        while not saved:
            output_name_new = os.path.join(
                output_path, image_namebox.text + '_' + str(suffix) + '.png')
            if not os.path.exists(output_name_new):
                pygame.image.save(processed_image, output_name_new)
                print(output_name_new)
                saved = True
                break
            suffix += 1
    save_notifier.notify_saving()
    # skip move, pop and load image to repeat
    if (not repeat):
        shutil.move(os.path.join(open_folder, files[0]), os.path.join(
            originals_path, files[0]))
        files.pop(0)
        LoadImage()


class ScrollHandler:
    def __init__(self):
        self.frames_scrolled = 0
        self.y = 0
        self.rate = 0

    def start_frame(self):
        if self.y == 0:
            self.rate = 0
            self.frames_scrolled = 0
        self.y = 0

    def scroll(self, scroll_y):
        if scroll_y > 0:
            scroll_y += 1
        elif scroll_y < 0:
            scroll_y -= 1
        self.y = scroll_y
        self.frames_scrolled += 1.5
        # print(scroll_y)
        self.rate += pow(self.frames_scrolled, 2) * scroll_y * (1/3)
        return self.rate


def clamp(x, _min, _max):
    return max(min(x, _max), _min)


class Save_Notifier:
    def __init__(self) -> None:
        self.color = pg.Color('green4')
        self.notify_rect = image_rect
        self.notify_rect.width = 3
        self.notify_duration_sec = 0.25
        self.stime = 0
        self.on = False

    def notify_saving(self):
        self.stime = time.time()
        self.on = True
        self.color = pg.Color('yellow3')

    def notify_default(self):
        if self.on:
            time_delta = time.time() - self.stime
            if (time_delta > self.notify_duration_sec):
                self.color = pg.Color('green4')
                self.stime = 0
                self.on = False

    def draw_notify(self):
        pg.draw.rect(screen, self.color, self.notify_rect, 5)

    def scale_notify(self, image_rect):
        self.notify_rect = image_rect
        pg.Rect.inflate_ip(self.notify_rect, 5, 5)


# Initialize program
pygame.init()
#FONT = pg.font.Font(None, 25)
FONT = pygame.font.SysFont('Arial', 17)
COLOR_INACTIVE = pg.Color('grey25')
COLOR_ACTIVE = pg.Color('white')

if not pygame.image.get_extended():
    print("Warning: You are using a version of pygame with limited image format support.")
originals_path = ""
project_folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
icon = pygame.image.load(os.path.join(
    project_folder, "assets", "emblem-photos-symbolic.svg"))
pygame.display.set_icon(icon)
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
screen_center = [pygame.Surface.get_width(
    screen) // 2, pygame.Surface.get_height(screen) // 2]
pygame.display.set_caption('Training Image Processor')
manager = pygame_gui.UIManager((800, 600))
clock = pygame.time.Clock()
files = []
image = None
scaled_image = None
global image_res
image_res = 768
scroll_handler = ScrollHandler()
ui_row_height = 25
ui_bar_height = 50
img_x = 15  # img x coordinate

# Initialize UI elements
button_rect = Rect(0, 0, 150, ui_bar_height)
button_rect.topright = (0, 0)
open_folder_label = pygame_gui.elements.ui_label.UILabel(Rect(150, 0, 800 - 150, ui_row_height),
                                                         "", manager)

folder_selection_button = UIButton(relative_rect=Rect(0, 0, 150, ui_row_height),
                                   manager=manager, text='Open Folder')

clockwise_button = UIButton(
    Rect(0, ui_row_height, ui_row_height, ui_row_height), text='', manager=manager)
clockwise_icon = pygame.image.load(os.path.join(
    project_folder, 'assets', 'object-rotate-right-symbolic.svg'))
clockwise_button_image = UIImage(Rect(
    0, ui_row_height, ui_row_height, ui_row_height).inflate(-8, -8), clockwise_icon, manager)

cclockwise_button = UIButton(Rect(
    ui_row_height, ui_row_height, ui_row_height, ui_row_height), text='', manager=manager)
cclockwise_icon = pygame.image.load(os.path.join(
    project_folder, 'assets', 'object-rotate-left-symbolic.svg'))
cclockwise_button_image = UIImage(Rect(
    ui_row_height, ui_row_height, ui_row_height, ui_row_height).inflate(-8, -8), cclockwise_icon, manager)

fliph_button = UIButton(Rect(ui_row_height*2, ui_row_height,
                        ui_row_height, ui_row_height), text='', manager=manager)
fliph_icon = pygame.image.load(os.path.join(
    project_folder, 'assets', 'object-flip-horizontal-symbolic.svg'))
fliph_button_image = UIImage(Rect(ui_row_height*2, ui_row_height,
                             ui_row_height, ui_row_height).inflate(-8, -8), fliph_icon, manager)

flipv_button = UIButton(Rect(ui_row_height*3, ui_row_height,
                        ui_row_height, ui_row_height), text='', manager=manager)
flipv_icon = pygame.image.load(os.path.join(
    project_folder, 'assets', 'object-flip-vertical-symbolic.svg'))
flipv_button_image = UIImage(Rect(ui_row_height*3, ui_row_height,
                             ui_row_height, ui_row_height).inflate(-8, -8), flipv_icon, manager)

next_button = UIButton(Rect(ui_row_height*4, ui_row_height,
                       ui_row_height, ui_row_height), text='', manager=manager)
next_icon = pygame.image.load(os.path.join(
    project_folder, 'assets', 'go-next-symbolic.svg'))
next_button_image = UIImage(Rect(ui_row_height*4, ui_row_height,
                            ui_row_height, ui_row_height).inflate(-8, -8), next_icon, manager)

image_namebox = InputBox(ui_row_height*6, ui_row_height, 140, 25, 'filename')
#image_resbox = InputBox(ui_row_height*9, ui_row_height, 65, 25, '512')
image_rect = Rect(img_x, ui_bar_height, 800, 600-ui_bar_height)
image_button = UIButton(image_rect, '', manager)
placeholder_image = pygame.Surface((1, 1))
placeholder_image.fill((0, 0, 0))
image_element = UIImage(image_rect, placeholder_image, manager)

repeat = False
selection_box = SelectionBox()
save_notifier = Save_Notifier()


def FolderSelection():
    dialog = UIFileDialog(rect=Rect(0, 0, 600, 400), manager=manager,
                          allow_picking_directories=True,
                          allow_existing_files_only=False,
                          visible=0)
    dialog.resizable = True
    dialog.set_display_title("Open a Directory")
    dialog.enable_close_button = False
    dialog.ok_button.enable()
    bsize = (25, 25)
    dialog.parent_directory_button.set_dimensions(bsize)
    dialog.home_button.set_dimensions(bsize)
    dialog.refresh_button.set_dimensions(bsize)
    dialog.delete_button.kill()
    dialog.rebuild()
    return dialog


def ScaleImage():
    w, h = pygame.display.get_surface().get_size()
    h -= ui_bar_height
    iw, ih = image.get_size()
    scale = min(w/iw, h/ih)
    scaled_size = (iw*scale, ih*scale)
    global scaled_image
    scaled_image = pygame.transform.smoothscale(image, scaled_size)
    image_element.set_image(scaled_image)
    image_rect = Rect((img_x, ui_bar_height), scaled_size)
    image_button.set_dimensions(image_rect.size)
    image_element.set_dimensions(image_rect.size)
    save_notifier.scale_notify(image_rect)


def LoadImage():
    loaded = False
    while not loaded:
        if files:
            try:
                global image
                image = pygame.image.load(os.path.join(
                    open_folder, files[0])).convert().convert_alpha()
                ScaleImage()
                selection_box.size = min(scaled_image.get_size())
                loaded = True
                image_button.show()
            except pygame.error as e:
                if str(e) != "Unsupported image format":
                    raise Exception().with_traceback(e.__traceback__)
                files.pop(0)
        else:
            image = None
            image_element.set_image(placeholder_image)
            image_button.hide()
            Tk().wm_withdraw()
            messagebox.showinfo('End of image', 'OK')
            break


def Draw():
    manager.update(time_delta)
    screen.fill((0, 0, 0))
    image_namebox.update()
    # image filename box is under of the folder window
    save_notifier.notify_default()
    image_namebox.draw(screen)
    manager.draw_ui(screen)
    if image:
        selection_box.draw()
        save_notifier.draw_notify()
    pygame.display.update()


def ScreenCenter():
    screen_center = [pygame.Surface.get_width(
        screen) // 2, pygame.Surface.get_height(screen) // 2]


folder_selection = FolderSelection()
open_folder = ""


# Main loop
while True:
    time_delta = clock.tick(60) / 1000.0
    scroll_handler.start_frame()
    ScreenCenter()
    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()
        elif event.type == pygame.VIDEORESIZE:
            # Resize UI Elements
            w, h = pygame.display.get_surface().get_size()
            open_folder_label.set_dimensions((w-150, ui_row_height))
            if image:
                ScaleImage()
            screen.fill((0, 0, 0))

            # Update Manager
            manager.set_window_resolution((w, h))

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == folder_selection_button:
                folder_selection.show()
            elif event.ui_element == folder_selection.ok_button:
                open_folder_label.set_text(
                    folder_selection.current_directory_path)
                open_folder = folder_selection.current_directory_path
                files = [f for f in os.listdir(open_folder) if os.path.isfile(
                    os.path.join(open_folder, f))]
                print(files)
                folder_selection.hide()
                LoadImage()
            elif event.ui_element == folder_selection.parent_directory_button:
                folder_selection.ok_button.enable()
            elif event.ui_element == folder_selection.home_button:
                folder_selection.ok_button.enable()
            elif event.ui_element == folder_selection.close_window_button or \
                    event.ui_element == folder_selection.cancel_button:
                folder_selection = FolderSelection()
            elif event.ui_element == clockwise_button:
                if image:
                    image = pygame.transform.rotate(image, -90)
                    ScaleImage()
            elif event.ui_element == cclockwise_button:
                if image:
                    image = pygame.transform.rotate(image, 90)
                    ScaleImage()
            elif event.ui_element == fliph_button:
                if image:
                    image = pygame.transform.flip(image, True, False)
                    ScaleImage()
            elif event.ui_element == flipv_button:
                if image:
                    image = pygame.transform.flip(image, False, True)
                    ScaleImage()
            elif event.ui_element == image_button:
                # print('click')
                repeat = False
                all_keys = pygame.key.get_pressed()
                # repeat when press ctrl or r key
                if all_keys[pygame.K_LCTRL] or all_keys[pygame.K_r]:
                    repeat = True
                if files and image:
                    ClickImage(repeat)
            elif event.ui_element == next_button:
                if files:
                    files.pop(0)
                    LoadImage()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if files:
                if repeat:  # if repeated image mv to original folder
                    originals_path = os.path.join(open_folder, 'originals')
                    shutil.move(os.path.join(open_folder, files[0]), os.path.join(
                        originals_path, files[0]))
                    repeat = False
                files.pop(0)
                LoadImage()
        elif event.type == pygame.MOUSEMOTION:
            if image and len(files) > 0:
                selection_box.location[0] = event.pos[0]
                selection_box.location[1] = event.pos[1]
                image_rect = Rect((img_x, ui_bar_height),
                                  scaled_image.get_size())
                selection_box.clamp(image_rect)

        elif event.type == pygame.MOUSEWHEEL:
            if image:
                pos = pygame.mouse.get_pos()
                w, h = scaled_image.get_size()
                scale = image.get_size()[0]/scaled_image.get_size()[0]
                min_box_size = image_res/scale
                selection_box.size = clamp(
                    selection_box.size + scroll_handler.scroll(event.y), min_box_size, max(w, h))
                selection_box.location[0] = pos[0]
                selection_box.location[1] = pos[1]
                image_rect = Rect((img_x, ui_bar_height), (w, h))
                selection_box.clamp(image_rect)
        image_namebox.handle_event(event)
        manager.process_events(event)

    Draw()
