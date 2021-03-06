import argparse
import cv2
import numpy as np
import time
import mss
import serial
from datetime import datetime

if __name__ == "__main__":
    serial_tx_errors = 0

    # configure your messages to be sent on a
    # - first hand detected and
    # - last hand lowered events,
    # where the following symbols are used:
    # - 'P' to PLAY the hand raised sound,
    # - 'S' to move the SERVO motor to the hand raised position,
    # - 'A' to play the hand raised ANIMATION,
    # - 'p' to PLAY the hand lowered sound,
    # - 's' to move the SERVO motor to the hand lowered position,
    # - 'a' to play the hand lowered ANIMATION
    serial_msg_on_raise = b'PAS\x0d'
    serial_msg_on_lowered = b'pas\x0d'
    serial_msg_on_init = serial_msg_on_lowered

    debug = True  # set to false to have a very quiet mode

    parser = argparse.ArgumentParser(description='%(prog)s')

    parser.add_argument('-p', action="store", default=None, required=False,
                        dest='serport',
                        help="serial device port name (e.g. '/dev/cu.usbmodem14202' or 'COM1')")

    parser.add_argument('-t', action="store", default=4.2e6, required=False,
                        dest='threshold',
                        help="threshold value for detection of the hand symbol (e.g. '4.2e6')")

    parser.add_argument('-m', action="store", default=0, required=False,
                        dest='monitor_number',
                        help="monitor number (e.g. '0')")

    parser.add_argument('-r', action="store", default="the-hand.png", required=False,
                        dest='resource_path',
                        help="resource path to hand image (e.g. 'the-hand.png')")

    args = parser.parse_args()
    args.threshold = float(args.threshold)
    args.monitor_number = int(args.monitor_number)

    if debug:
        print(f"serport = {args.serport}")
        print(f"threshold = {args.threshold}")
        print(f"monitor_number = {args.monitor_number}")
        print(f"resource_path = {args.resource_path}")

    serial_baudrate = 115200

    ser = args.serport
    if ser:
        ser = serial.Serial(ser, serial_baudrate, timeout=3)

    if debug:
        print(f"ser = {ser}")

    # try to send initialization message via serial
    if ser:
        ser.write(serial_msg_on_init)

    template = cv2.imread(args.resource_path)
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    template = cv2.Canny(template, 50, 200)
    w, h = template.shape[::-1]

    last_detection = False

    with mss.mss(display=':0') as sct:
        monitors = sct.monitors

        # list monitors
        if debug:
            mon_num = 0
            for mon in monitors:
                print(f"monitor #{mon_num} = {mon}")
                mon_num = mon_num + 1

        while True:
            last_time = time.time()

            img = sct.grab(monitors[args.monitor_number])
            img = np.array(img)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edged = cv2.Canny(gray, 50, 200)

            result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
            (_, detection_max_val, _, detection_max_loc) = cv2.minMaxLoc(result)

            loc = np.where(result >= args.threshold)
            detection = len(loc[0]) > 0

            if debug:
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")

                fps = 1 / (time.time() - last_time)
                print(f"[{current_time}] detection: {detection}, fps: {fps:.1f}, "
                      f"maxval: {detection_max_val:.0f}, maxloc: {detection_max_loc}, tx errors: {serial_tx_errors}")

            if detection != last_detection:
                if detection:
                    if debug:
                        print(f"[{current_time}] event: hand raised!")
                    serial_str = serial_msg_on_raise
                else:
                    if debug:
                        print(f"[{current_time}] event: hand lowered!")
                    serial_str = serial_msg_on_lowered

                # try to send via serial
                try:
                    if ser:
                        print(f"[{current_time}] sending message via serial: {serial_str}")
                        ser.write(serial_str)
                except SerialException as e:
                    serial_tx_errors = serial_tx_errors + 1
                    if e.errno == 13:  # write failed: [Errno 6] Device not configured
                        # retry once, may work or may fail; might want to re-open the serial
                        if ser:
                            print(f"[{current_time}] resending message via serial: {serial_str}")
                            ser.write(serial_str)
                    else:  # do not catch every exception
                        raise e

            # store for next iteration
            last_detection = detection
