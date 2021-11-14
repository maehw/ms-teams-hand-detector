#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
import serial.tools.list_ports
import mss
import cv2
import time
import numpy as np
from datetime import datetime


lbl_det_rate_resetval = '-'
btn_det_startstop_start = 'Start detection'
btn_det_startstop_stop = 'Stop detection'
processing_interval_msecs = 500  # also acts as rate limiter
combo_serial_dev_none = 'Do not use serial device'
template_img = cv2.imread("the-hand.png")  # FIXME
template_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
template_img = cv2.Canny(template_img, 50, 200)
template_img_w, template_img_h = template_img.shape[::-1]
raised_hand_detected_text = 'Raised hand detected'
raised_hand_not_detected_text = 'Raised hand not detected'

ser = None
last_time = time.time()



def refresh_serial_dev_list():
    combo_serial_dev['values'] = []
    for dev in serial.tools.list_ports.comports():
        combo_serial_dev['values'] = (*combo_serial_dev['values'], dev)
    combo_serial_dev['values'] = (combo_serial_dev_none, *combo_serial_dev['values'])
    combo_serial_dev['state'] = 'readonly'
    combo_serial_dev.current(0)

def refresh_display_list():
    combo_display['values'] = []
    display_id = 0
    with mss.mss(display=':0') as sct:
        for display in sct.monitors:
            display_str = f"Display #{display_id} ({display['width']}x{display['height']} pixels)"
            combo_display['values'] = (*combo_display['values'], display_str)
            # print(f"display_str = {display_str}, display = {display}")
            display_id += 1
    combo_display['state'] = 'readonly'
    combo_display.current(0)

def startstop_detection():
    global ser
    if btn_det_startstop['text'] == btn_det_startstop_start:
        # start
        btn_det_startstop['text'] = btn_det_startstop_stop
        ctrl_state = tk.DISABLED

        serial_dev_selected = combo_serial_dev.get()
        if serial_dev_selected == combo_serial_dev_none:
            ser = None
        else:
            serial_dev_selected = serial_dev_selected.split(' ', 1)[0]
            # print(f"serial dev={serial_dev_selected}")
            serial_baudrate = combo_serial_speed.get()
            ser = serial.Serial(serial_dev_selected, serial_baudrate, timeout=3)
            if ser:
                print("opened serial device")
    else:
        # stop
        btn_det_startstop['text'] = btn_det_startstop_start
        lbl_det_rate['text'] = lbl_det_rate_resetval
        ctrl_state = tk.NORMAL
        if ser:
            ser.close()
            print("closed serial device")
    lbl_det_thres['state'] = ctrl_state
    combo_display['state'] = ctrl_state
    btn_display_refresh['state'] = ctrl_state
    combo_serial_dev['state'] = ctrl_state
    btn_serial_dev_refresh['state'] = ctrl_state
    combo_serial_speed['state'] = ctrl_state
    ent_msg_raised['state'] = ctrl_state
    ent_msg_lowered['state'] = ctrl_state

def worker():
    global last_time
    global template_img
    # do the real work
    if btn_det_startstop['text'] == btn_det_startstop_stop:
        lbl_det_rate['text'] = 'started'

        sct = mss.mss(display=':0')
        monitors = sct.monitors

        img = sct.grab(monitors[0])  # FIXME
        img = np.array(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(gray, 50, 200)

        result = cv2.matchTemplate(edged, template_img, cv2.TM_CCOEFF)
        (_, detection_max_val, _, detection_max_loc) = cv2.minMaxLoc(result)

        loc = np.where(result >= 4.2e6)  # FIXME
        detection_result = len(loc[0]) > 0

        if detection_result:
            lbl_det_status['text'] = raised_hand_detected_text
        else:
            lbl_det_status['text'] = raised_hand_not_detected_text

        this_time = time.time()
        fps = 1 / (this_time - last_time)
        # print(f"fps = {fps:.2f}")
        lbl_det_rate['text'] = f"{fps:.2f}"
        last_time = this_time

    window.after(processing_interval_msecs, worker)  # reschedule


# GUI prototype (not in use yet)
window = tk.Tk()
window.title('Microsoft Teams Hand Detector')


cur_row = 0

lbl_det_status_descr = tk.Label(text='Detection status')
lbl_det_status_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

lbl_det_status = tk.Label(text='Detection not started')
lbl_det_status.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')

btn_det_startstop = tk.Button(text=btn_det_startstop_start, command=startstop_detection)
btn_det_startstop.grid(row=cur_row, column=2, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_det_rate_descr = tk.Label(text='Detection refresh rate (1/s)')
lbl_det_rate_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

lbl_det_rate = tk.Label(text=lbl_det_rate_resetval)
lbl_det_rate.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_det_thres_descr = tk.Label(text='Detection threshold')
lbl_det_thres_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

lbl_det_thres = tk.Entry()
lbl_det_thres.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
lbl_det_thres.insert(0, '4.2e6')


cur_row += 1

lbl_display_descr = tk.Label(text='Display')
lbl_display_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

combo_display = ttk.Combobox()
combo_display.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')

btn_display_refresh = tk.Button(text='Refresh', command=refresh_display_list)
btn_display_refresh.grid(row=cur_row, column=2, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_serial_dev_descr = tk.Label(text='Serial device')
lbl_serial_dev_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

combo_serial_dev = ttk.Combobox()
combo_serial_dev.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')

btn_serial_dev_refresh = tk.Button(text='Refresh', command=refresh_serial_dev_list)
btn_serial_dev_refresh.grid(row=cur_row, column=2, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_serial_speed_descr = tk.Label(text='Serial baudrate')
lbl_serial_speed_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

combo_serial_speed = ttk.Combobox()
combo_serial_speed.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
baudrates = sorted([9600, 19200, 38400, 57600, 115200, 230400], reverse=True)
baudrate_default = 115200
for br in baudrates:
    combo_serial_speed['values'] = (*combo_serial_speed['values'], (br))
combo_serial_speed.current(baudrates.index(baudrate_default))

cur_row += 1

lbl_msg_raised_descr = tk.Label(text='Msg. on hand raised event')
lbl_msg_raised_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

ent_msg_raised = tk.Entry()
ent_msg_raised.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
ent_msg_raised.insert(0, 'PAS\\r')


cur_row += 1

lbl_msg_lowered_descr = tk.Label(text='Msg. on hand lowered event')
lbl_msg_lowered_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

ent_msg_lowered = tk.Entry()
ent_msg_lowered.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
ent_msg_lowered.insert(0, 'pas\\r')


# call functions to fill lists initially
refresh_serial_dev_list()
refresh_display_list()

window.after(processing_interval_msecs, worker)
window.mainloop()
