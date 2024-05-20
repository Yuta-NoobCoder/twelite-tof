import time
import keyboard
calibration_flg = True
def end_calibration(): 
    global calibration_flg
    calibration_flg = False

keyboard.on_press_key('enter', lambda _: end_calibration())

while calibration_flg:
    print(calibration_flg)
    
    time.sleep(1)
    