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
lbl_det_max_resetval = '-'
btn_det_startstop_start = 'Start'
btn_det_startstop_stop = 'Stop'
display_prefix = 'Display #'
combo_serial_dev_none = 'Do not use serial device'
raised_hand_detected_text = 'Raised hand detected'
raised_hand_not_detected_text = 'Raised hand not detected'
detection_not_started_text = 'Detection not started'
template_img_filename = 'the-hand.png'
serial_msg_on_raised_default = 'PAS\\r'
serial_msg_on_lowered_default = 'pas\\r'
processing_interval_msecs = 200  # also acts as rate limiter (max. 1000/processing_interval_msecs detections per second)
baudrates = sorted([9600, 19200, 38400, 57600, 115200, 230400], reverse=True)
baudrate_default = 115200
ser = None
selected_display_num = 0
detection_threshold = float('inf')
last_detection_result = None

last_time = time.time()
template_img = cv2.imread(template_img_filename)
template_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
template_img = cv2.Canny(template_img, 50, 200)
template_img_w, template_img_h = template_img.shape[::-1]


def refresh_serial_dev_list():
    """rebuild list of serial devices"""
    combo_serial_dev['values'] = []
    for dev in serial.tools.list_ports.comports():
        combo_serial_dev['values'] = (*combo_serial_dev['values'], dev)
    combo_serial_dev['values'] = (combo_serial_dev_none, *combo_serial_dev['values'])
    combo_serial_dev['state'] = 'readonly'
    combo_serial_dev.current(0)


def refresh_display_list():
    """rebuild list of displays"""
    combo_display['values'] = []
    display_id = 0
    with mss.mss(display=':0') as sct:
        for display in sct.monitors:
            display_str = f"{display_prefix}{display_id} ({display['width']}x{display['height']} pixels)"
            combo_display['values'] = (*combo_display['values'], display_str)
            display_id += 1
    combo_display['state'] = 'readonly'
    combo_display.current(0)


def startstop_detection():
    """start or stop the detection"""
    global ser
    global selected_display_num
    global detection_threshold
    global last_detection_result
    global serial_msg_on_raised
    global serial_msg_on_lowered
    if btn_det_startstop['text'] == btn_det_startstop_start:
        # start
        btn_det_startstop['text'] = btn_det_startstop_stop
        ctrl_state = tk.DISABLED
        # get the display number
        selected_display = combo_display.get()
        selected_display = selected_display[len(display_prefix):]
        selected_display_num = int(selected_display.split()[0])
        # get the detection threshold
        detection_threshold = float(ent_det_thres.get())
        # extract serial device name and baudrate from dropdown menu and
        # create Serial object if valid
        serial_dev_selected = combo_serial_dev.get()
        if serial_dev_selected == combo_serial_dev_none:
            ser = None
        else:
            serial_dev_selected = serial_dev_selected.split(' ', 1)[0]
            serial_baudrate = combo_serial_speed.get()
            ser = serial.Serial(serial_dev_selected, serial_baudrate, timeout=3)
        # save messages to be sent via serial
        serial_msg_on_raised = ent_msg_raised.get().replace('\\r', '\r').replace('\\n', '\n').encode()
        serial_msg_on_lowered = ent_msg_lowered.get().replace('\\r', '\r').replace('\\n', '\n').encode()
    else:
        # stop: reset some of the GUI elements
        btn_det_startstop['text'] = btn_det_startstop_start
        lbl_det_rate['text'] = lbl_det_rate_resetval
        lbl_det_max['text'] = lbl_det_max_resetval
        lbl_det_status['text'] = detection_not_started_text
        last_detection_result = None
        ctrl_state = tk.NORMAL
        # close serial device if Serial object is valid
        if ser:
            ser.close()
    # change state of GUI control elements (activate/deactivate)
    ent_det_thres['state'] = ctrl_state
    combo_display['state'] = ctrl_state
    btn_display_refresh['state'] = ctrl_state
    combo_serial_dev['state'] = ctrl_state
    btn_serial_dev_refresh['state'] = ctrl_state
    combo_serial_speed['state'] = ctrl_state
    ent_msg_raised['state'] = ctrl_state
    ent_msg_lowered['state'] = ctrl_state


def worker():
    """perform the detection (core)"""
    global last_time
    global template_img
    global selected_display_num
    global detection_threshold
    global last_detection_result
    global ser
    global serial_msg_on_raised
    global serial_msg_on_lowered
    # do the real work if detection is activated
    if btn_det_startstop['text'] == btn_det_startstop_stop:
        sct = mss.mss(display=':0')
        img = sct.grab(sct.monitors[selected_display_num])
        img = np.array(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(gray, 50, 200)

        result = cv2.matchTemplate(edged, template_img, cv2.TM_CCOEFF)
        (_, detection_max_val, _, detection_max_loc) = cv2.minMaxLoc(result)
        lbl_det_max['text'] = f"{detection_max_val:.2e} @ pos. {detection_max_loc}"

        loc = np.where(result >= detection_threshold)
        detection_result = len(loc[0]) > 0

        if detection_result:
            lbl_det_status['text'] = raised_hand_detected_text
        else:
            lbl_det_status['text'] = raised_hand_not_detected_text
        # edge detection
        if last_detection_result != detection_result:
            if detection_result:
                serial_str = serial_msg_on_raised
            else:
                serial_str = serial_msg_on_lowered

            # try to send via serial
            try:
                if ser:
                    ser.write(serial_str)
            except serial.SerialException as e:
                if e.errno == 13:  # write failed: [Errno 6] Device not configured
                    # retry once, may work or may fail; might want to re-open the serial
                    if ser:
                        ser.write(serial_str)
                else:  # do not catch every exception
                    raise e
        # store current detection result for next run (for edge detection)
        last_detection_result = detection_result

        # calculate detection rate
        this_time = time.time()
        detections_per_sec = 1 / (this_time - last_time)
        lbl_det_rate['text'] = f"{detections_per_sec:.2f}"
        last_time = this_time

    window.after(processing_interval_msecs, worker)  # reschedule


# build up the GUI
# (first the window, then all elements for every row of the grid)
window = tk.Tk()
window.title('Microsoft Teams Hand Detector')

cur_row = 0

lbl_det_status_descr = tk.Label(text='Detection status')
lbl_det_status_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

lbl_det_status = tk.Label(text=detection_not_started_text)
lbl_det_status.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')

btn_det_startstop = tk.Button(text=btn_det_startstop_start, command=startstop_detection)
btn_det_startstop.grid(row=cur_row, column=2, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_det_rate_descr = tk.Label(text='Detection refresh rate (1/s)')
lbl_det_rate_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

lbl_det_rate = tk.Label(text=lbl_det_rate_resetval)
lbl_det_rate.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_det_max_descr = tk.Label(text='Detection max. value')
lbl_det_max_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

lbl_det_max = tk.Label(text=lbl_det_max_resetval)
lbl_det_max.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_det_thres_descr = tk.Label(text='Detection threshold')
lbl_det_thres_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

ent_det_thres = tk.Entry()
ent_det_thres.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
ent_det_thres.insert(0, '4.2e6')


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
for br in baudrates:
    combo_serial_speed['values'] = (*combo_serial_speed['values'], (br))
combo_serial_speed.current(baudrates.index(baudrate_default))

cur_row += 1

lbl_msg_raised_descr = tk.Label(text='Msg. on hand raised event')
lbl_msg_raised_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

ent_msg_raised = tk.Entry()
ent_msg_raised.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
ent_msg_raised.insert(0, serial_msg_on_raised_default)


cur_row += 1

lbl_msg_lowered_descr = tk.Label(text='Msg. on hand lowered event')
lbl_msg_lowered_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

ent_msg_lowered = tk.Entry()
ent_msg_lowered.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
ent_msg_lowered.insert(0, serial_msg_on_lowered_default)


# call functions to fill lists initially
refresh_serial_dev_list()
refresh_display_list()

# kick off the GUI
window.after(processing_interval_msecs, worker)
window.mainloop()
