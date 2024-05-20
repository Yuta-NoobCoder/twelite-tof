import numpy as np
from serial import Serial, SerialTimeoutException
import argparse
import os
import time

# 実行例s
# python .\plot_sync.py --p1 COM3 --p2 COM4 --dir rouka_test_sync --n 200

def getTimeMs():
    return int(time.time() * 1000)

# コマンドライン引数
parser = argparse.ArgumentParser()
parser.add_argument("--p1", required=True)         # COMポート番号(ビーコン1)
parser.add_argument("--p2", required=True)         # COMポート番号(ビーコン2)
parser.add_argument("--dir", required=True)        # 出力ディレクトリ名
parser.add_argument("--n", type=int)               # プロット数
args = parser.parse_args()

try:
    os.mkdir(args.dir)
except FileExistsError:
    pass

log_file_path = args.dir + "/data.log"	 # ログファイル名

cnt = 0
elapsed_time_ms = 0
timespan_ms = 500

half_timespan_ms = timespan_ms / 2

ser_1 = Serial(port=args.p1, baudrate=115200, timeout= half_timespan_ms / 1000)
ser_2 = Serial(port=args.p2, baudrate=115200,  timeout= half_timespan_ms / 1000)

with open(log_file_path, 'w') as file:
    while True:
        try:
            
            timestamp_start = getTimeMs()

            try:
                # ビーコン1 計測
                timestamp_beacon1_start = getTimeMs()
                
                ser_1.write(b'm')
                value_beacon_1 = int(ser_1.readline())
                ser_1.flush()
                
                timestamp_beacon1_end = getTimeMs()
                
                #ビーコン2 計測
                timestamp_beacon2_start = getTimeMs()
                
                ser_2.write(b'm')
                value_beacon_2 = int(ser_2.readline())
                ser_2.flush()
                
                timestamp_beacon2_end = getTimeMs()
                
            except SerialTimeoutException:
                pass
            
            timestamp_end = getTimeMs()
            diff = timespan_ms - (timestamp_end - timestamp_start)
            if diff > 0:
                time.sleep(diff / 1000)
                timestamp_end = getTimeMs()
            
            file.write("{},{},{},{},{}\n".format(cnt, timestamp_beacon1_start, elapsed_time_ms, value_beacon_1, value_beacon_2))
            print("{},{},{},{},{}".format(cnt, timestamp_beacon1_start, elapsed_time_ms, value_beacon_1, value_beacon_2))
            
            cnt+=1
            elapsed_time_ms += (timestamp_end - timestamp_start)
            
            if cnt == args.n:
                break

        except ValueError:
            pass # 数値以外の行は無
        except KeyboardInterrupt:
            ser_1.close()
            ser_2.close()
            break