from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Point, GraphicException
from random import random
from math import sqrt
import time

Window.fullscreen = True
# Window.borderless = True
Window.left = 2000

def calculate_points(x1, y1, x2, y2, steps=5):
    dx = x2 - x1
    dy = y2 - y1
    dist = sqrt(dx * dx + dy * dy)
    if dist < steps:
        return
    o = []
    m = dist / steps
    for i in range(1, int(m)):
        mi = i / m
        lastx = x1 + dx * mi
        lasty = y1 + dy * mi
        o.extend([lastx, lasty])

    return o

class FingerTracker(FloatLayout):

    def __init__(self, **kwargs):
        super(FingerTracker, self).__init__(**kwargs)

        print ("Start: ", Clock.get_boottime())

        self.filename = "output_" + time.strftime('%Y-%m-%d_%H.%M.%S', time.localtime(time.time())) + '.txt'

        self.starttime = -1
        self.real_dims = (13.375, 10.625) # dimensions of touchscreen in inches

        # touch positions defined from the bottom left corner of screen
        self.all_touches = {} # touch position in inches
        self.all_touches_pix = {} # raw touch position in pixels
        self.all_touches_norm = {} # normalized touch position from 0 to 1

        Clock.schedule_once(self.flash, 0) # call after the next frame
        Clock.schedule_once(self.unflash, 3)

        Clock.schedule_interval(self.update, 1.0 / 60) # update at 60 hz

    # flash touchscreen red for synchronization with computer vision code
    def flash(self, dt):
        self.flasher = Rectangle(pos=(0, 0), size=self.size)
        with self.canvas:
            Color(1, 0, 0, 1, mode="rgba")
        self.canvas.add(self.flasher)
        self.starttime = Clock.get_boottime()

    # end flash
    def unflash(self, dt):
        self.canvas.remove(self.flasher)

    def update(self, dt):
        if self.starttime >= 0:
            clock_time = str(Clock.get_boottime() - self.starttime)

            # CODE TO SAVE TO FILE -- UNCOMMENT ONE (NORM WHEN IN DOUBT) OR CHANGE FILENAMES
            # with open('output.txt', 'a') as f:
            #     f.write(clock_time + "\t" + str(self.all_touches) + "\n")

            # with open('output_pix.txt', 'a') as f:
            #     f.write(clock_time + "\t" + str(self.all_touches_pix) + "\n")

            with open(self.filename, 'a') as f:
                f.write(clock_time + "\t" + str(self.all_touches_norm) + "\n")
            print(self.all_touches_norm)

            # print(clock_time + "\t" + str(self.all_touches_pix) )

    def on_touch_down(self, touch):
        win = self.get_parent_window()

        # create new touch event
        ud = touch.ud
        ud['group'] = g = str(touch.uid)
        pointsize = 5

        # update touch positions
        self.all_touches_pix[touch.uid] = (touch.x, touch.y)
        self.all_touches[touch.uid] = (touch.x * self.real_dims[0] / self.width, touch.y * self.real_dims[1] / self.height)
        self.all_touches_norm[touch.uid] = (touch.x / self.width, touch.y / self.height)

        # store pressure and scale point if touch contains this information
        if 'pressure' in touch.profile:
            ud['pressure'] = touch.pressure
            pointsize = self.normalize_pressure(touch.pressure)

        # pick a new color for new touch
        ud['color'] = random()

        # draw vertical/horizontal lines that intersect with touch location
        with self.canvas:
            Color(ud['color'], 1, 1, mode='hsv', group=g)
            ud['lines'] = [
                Rectangle(pos=(touch.x, 0), size=(1, win.height), group=g),
                Rectangle(pos=(0, touch.y), size=(win.width, 1), group=g),
                Point(points=(touch.x, touch.y), source='particle.png',
                      pointsize=pointsize, group=g)]

        ud['label'] = Label(size_hint=(None, None))
        self.update_touch_label(ud['label'], touch)
        self.add_widget(ud['label'])
        touch.grab(self)

        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        ud = touch.ud

        # update positions associated with touch ids assigned on touchdown
        self.all_touches_pix[touch.uid] = (touch.x, touch.y)
        self.all_touches[touch.uid] = (touch.x * self.real_dims[0] / self.width, touch.y * self.real_dims[1] / self.height)
        self.all_touches_norm[touch.uid] = (touch.x / self.width, touch.y / self.height)

        # update line marker locations
        ud['lines'][0].pos = touch.x, 0
        ud['lines'][1].pos = 0, touch.y

        index = -1

        # calculate location of new points
        while True:
            try:
                points = ud['lines'][index].points
                oldx, oldy = points[-2], points[-1]
                break
            except IndexError:
                index -= 1

        points = calculate_points(oldx, oldy, touch.x, touch.y)

        if points:
            try:
                lp = ud['lines'][-1].add_point
                for idx in range(0, len(points), 2):
                    lp(points[idx], points[idx + 1])
            except GraphicException:
                pass

        ud['label'].pos = touch.pos
        
        t = int(time.time())
        if t not in ud:
            ud[t] = 1
        else:
            ud[t] += 1
        self.update_touch_label(ud['label'], touch)

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        
        # remove touch ids
        self.all_touches_pix.pop(touch.uid)
        self.all_touches.pop(touch.uid)
        self.all_touches_norm.pop(touch.uid)

        touch.ungrab(self)
        ud = touch.ud
        self.canvas.remove_group(ud['group'])
        self.remove_widget(ud['label'])

    def update_touch_label(self, label, touch):
        label.text = 'ID: %s\nPos: (%d, %d)\nClass: %s' % (
            touch.id, touch.x, touch.y, touch.__class__.__name__)
        label.texture_update()
        label.pos = touch.pos
        # print(touch.pos)
        # with open('output6.txt', 'a') as f:
        #     f.write(str(touch.pos) + "\n")
        label.size = label.texture_size[0] + 20, label.texture_size[1] + 20

class BrailleApp(App):
    title = 'Braille Finger Tracker'

    def build(self):
        return FingerTracker()

    def on_pause(self):
        return True


if __name__ == '__main__':
    BrailleApp().run()