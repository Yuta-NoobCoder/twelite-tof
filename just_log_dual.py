import time
from serial import Serial, SerialTimeoutException
import argparse
import os

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
timespan_ms = 50

half_timespan_ms = timespan_ms / 2

ser_1 = Serial(port=args.p1, baudrate=115200)
ser_2 = Serial(port=args.p2, baudrate=115200)


def getTimeMs():
    return int(time.time() * 1000)

with open(log_file_path, 'w') as log_file:
    
    old_time = None
    new_time = None
    old_tof1 = 0
    old_tof2 = 0
    
    while True:
        
        # 計測
        try:
            timestamp_start = getTimeMs()
            try:
                # ビーコン1 計測
                timestamp_beacon1_start = getTimeMs()                
                ser_1.write(b'm')
                value_beacon_1_tof = 0
                value_beacon_1_rssi_local = 0
                value_beacon_1_rssi_remote = 0
                raw_beacon_1 = ser_1.readline().strip()
                if raw_beacon_1 != b'' and raw_beacon_1 != b'-1':
                    # print(raw_beacon_1)
                    value_beacon_1_tof = int(raw_beacon_1.decode(encoding='utf-8').split(",")[0])
                    value_beacon_1_rssi_local = int(raw_beacon_1.decode(encoding='utf-8').split(",")[1])
                    value_beacon_1_rssi_remote = int(raw_beacon_1.decode(encoding='utf-8').split(",")[1])
                ser_1.flush()
                timestamp_beacon1_end = getTimeMs()
                
                #ビーコン2 計測
                timestamp_beacon2_start = getTimeMs()
                ser_2.write(b'm')
                value_beacon_2_tof = 0
                value_beacon_2_rssi_local = 0
                value_beacon_2_rssi_remote = 0
                raw_beacon_2 = ser_2.readline().strip()
                if raw_beacon_2 != b'' and raw_beacon_2 != b'-1':
                    # print(raw_beacon_2)
                    value_beacon_2_tof = int(raw_beacon_2.decode(encoding='utf-8').split(",")[0])
                    value_beacon_2_rssi_local = int(raw_beacon_2.decode(encoding='utf-8').split(",")[1])
                    value_beacon_2_rssi_remote = int(raw_beacon_1.decode(encoding='utf-8').split(",")[1])     
                ser_2.flush()
                timestamp_beacon2_end = getTimeMs()
                
            except SerialTimeoutException:
                print("serial timed out.")
            except ValueError as ve:
                print(ve)
            
            timestamp_end = getTimeMs()
            diff = timespan_ms - (timestamp_end - timestamp_start)
            if diff > 0:
                time.sleep(diff / 1000)
                timestamp_end = getTimeMs()
            
            output = "{},{},{},{},{},{},{},{},{}".format(cnt, timestamp_beacon1_start, elapsed_time_ms, value_beacon_1_tof, value_beacon_2_tof, value_beacon_1_rssi_local, value_beacon_2_rssi_local, value_beacon_1_rssi_remote, value_beacon_2_rssi_remote)
            log_file.write(output + "\n")
            print(output)

            new_time = timestamp_beacon1_start
            old_tof1 = value_beacon_1_tof
            old_tof2 = value_beacon_2_tof
    
            old_time = new_time
            cnt+=1
            elapsed_time_ms += (timestamp_end - timestamp_start)
            
            if cnt == args.n:
                break
        
        except KeyboardInterrupt:
            ser_1.close()
            ser_2.close()
            break
        