#!/usr/bin/python3
import pycodestyle


def separator():
    print("-"*80)


if __name__ == '__main__':
    # perform checks with pycodestyle
    files = ['check_code.py', 'ms_teams_hand_detector.py']
    for file in files:
        fchecker = pycodestyle.Checker(file, show_source=True)
        num_errors = fchecker.check_all(expected=["E501"])  # allow long lines
        print(f"Found {num_errors} errors (and warnings) in file '{file}'")
        separator()
