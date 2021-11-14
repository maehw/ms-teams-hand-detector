import tkinter as tk
import tkinter.ttk as ttk
import serial.tools.list_ports
import mss

# GUI prototype (not in use yet)
window = tk.Tk()
window.title('Microsoft Teams Hand Detector')


cur_row = 0

lbl_det_status_descr = tk.Label(text='Detection status')
lbl_det_status_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

lbl_det_status = tk.Label(text='Detection not started')
lbl_det_status.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')

btn_det_startstop = tk.Button(text='Start detection')
btn_det_startstop.grid(row=cur_row, column=2, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_det_rate_descr = tk.Label(text='Detection rate')
lbl_det_rate_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

lbl_det_rate = tk.Label(text='0 fps')
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
display_id = 0
with mss.mss(display=':0') as sct:
    for display in sct.monitors:
        display_str = f"Display #{display_id} ({display['width']}x{display['height']} pixels)"
        combo_display['values'] = (*combo_display['values'], display_str)
        print(f"display_str = {display_str}, display = {display}")
        display_id += 1
combo_display['state'] = 'readonly'
combo_display.current(0)

btn_display_refresh = tk.Button(text='Refresh')
btn_display_refresh.grid(row=cur_row, column=2, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_serial_dev_descr = tk.Label(text='Serial device')
lbl_serial_dev_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

combo_serial_dev = ttk.Combobox()
combo_serial_dev.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
for dev in serial.tools.list_ports.comports():
    combo_serial_dev['values'] = (*combo_serial_dev['values'], dev)
combo_serial_dev['state'] = 'readonly'
combo_serial_dev.current(0)

btn_serial_dev_refresh = tk.Button(text='Refresh')
btn_serial_dev_refresh.grid(row=cur_row, column=2, padx='5', pady='5', sticky='w')


cur_row += 1

lbl_serial_speed_descr = tk.Label(text='Serial baudrate')
lbl_serial_speed_descr.grid(row=cur_row, column=0, padx='5', pady='5', sticky='w')

combo_serial_speed = ttk.Combobox()
combo_serial_speed.grid(row=cur_row, column=1, padx='5', pady='5', sticky='w')
baudrates = [9600, 19200, 38400, 57600, 115200, 230400]
for br in sorted(baudrates, reverse=True):
    combo_serial_speed['values'] = (*combo_serial_speed['values'], (br))
combo_serial_speed.current(0)

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


window.mainloop()
