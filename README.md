# README

The Python script in this repository tries to detect a raised hand in Microsoft Teams meetings, outputs the detection results to the console and send a string to a serial device. It's originally meant for meetings that are "hybrid" - some people take part in presence, some only digitally/online (better wording is welcome; native speakers are welcome to suggest something else).

The detection is based on computer vision (OpenCV) pattern matching using a reference symbol.

In my case I've used a micro:bit to receive and react on the serial data. Both `.hex` files contained in this repository can be flashed on a micro:bit v2. The micro:bit will play an animation and make a sound when a hand has been raised. The source can be accessed under https://makecode.microbit.org/_gk0CmXCuh3of.
If you also want to move a servo (e.g. to move a cardboard hand) dependent on whether a hand has been raised or lowered use the following code: https://makecode.microbit.org/_ewy3tvETmETp.

![Blocks shown in Microsoft MakeCode for micro:bit](microbit-ide.png)

It should be easy to implement own actions/reactions to raised/lowered hands (the edge detection is already in use).

# How To

## Prerequisites

Take a screenshot of the raised hand symbol that is shown in Microsoft Teams in the participants list on the right hand side. Then cut it (about 32 x 32 pixels) and place it in the same folder as the Python script. Call the image file `the-hand.png` (or specify a different name). It is not part of this repository due to copyright uncertainties. Also it may be subject to change in future releases of Microsoft Teams.

Call the script using Python 3:

The following parameter is required if you want to send messages via serial:

* `-p`: the port of the virtual serial import

Optional arguments are:

* `-t`: the threshold used in the computer vision pattern matching for detecting the hand (`4.2e6` did the trick for me, but you may add some `print` log-debugging to find the threshold value that suits you)
* `-m`: the monitor number (defaults to `0`)
* `-r`: the name of the image resource (defaults to `the-hand.png`)

### Example calls

Only output to console (only if `debug = True`):

```
python3 ms_teams_hand_detector.py
```

Output to console and send messages via serial:

```
python3 ms_teams_hand_detector.py -p /dev/cu.usbmodem14202
```

Additionally set a custom threshold value:

```
python3 ms_teams_hand_detector.py -p COM5 -t 23.5e4
```

Additionally select another monitor/display and define the hand symbol image resource:

```
python3 ms_teams_hand_detector.py -p COM5 -t 4.2e6 -m 1 -r the-hand-modified.png
```

# Dependencies

Some Python modules are required for taking screenshots and using computer vision to detect the hand (see the `import` statements at the top of the Python script, some more may be require bot not listed here):

```
pip install argparse
pip install opencv-python
pip install mss
pip instll pyserial
```

# Building a standalone version

The aim is to get an executable version without any implicit Python runtime dependency.

```
pip install pyinstaller
pyinstaller ms_teams_hand_detector.py
```

*Documentation of this section is WIP, help to contribute*

# TODOs/Ideas

- [x] Add support for controlling a servo motor from the micro:bit (should be easy, but the hardware I currently have at hand won't play)
- [ ] Automatic build of standalone application and test on different platforms (Windows, Linux, Mac OS)

*(This section may be migrated to https://github.com/maehw/ms-teams-hand-detector/issues.)*

# Contributing

Feel free to contribute. ;) Any issues and merge requests are welcome.

It would be great if you could run `check_code.py` on your code before you send a merge request.
