from re import T
import numpy as np
from serial import Serial, SerialTimeoutException
import argparse
import os
import time
from particle_filter import Particle, Beacon, ParticleFilter
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import collections
import keyboard

# 実行例
# python .\log_plot_dual_beacon.py --p1 COM3 --p2 COM4 --dir rouka_test_sync --n 200

# パーティクルフィルタの初期化
n_particle = 1000
particles = [Particle((5 + 4.8, 6.6)) for p in range(n_particle)]
beacons = [Beacon(position= (-5, 0)), Beacon(position=(5, 0))]
pfilter = ParticleFilter(particles)

fig, ax = plt.subplots()
fig.set_size_inches(12,6)
ax.grid()

# プロット軸設定
ticks_x = np.linspace(-20, 20, 41)
ticks_y = np.linspace(-10, 20, 31)
ax.set_xlim(-20, 20)
ax.set_ylim(-10, 20)
ax.set_xticks(ticks_x)
ax.set_yticks(ticks_y)

# ビーコンをプロット
ax.scatter(-5, 0, c="red", s=100)
ax.scatter(5, 0, c="red", s=100) 

line_1 = [(9.8, 3.5), (9.8 - 20, 3.5)]
line_2 = [(9.8 - 20, 3.5), (9.8 - 20, 3.5 + 3.5)]
line_3 = [(9.8 - 20, 3.5 + 3.5), (9.8, 3.5 + 3.5)]
line_4 = [(9.8, 3.5 + 3.5), (9.8, 3.5 + 3.5 + 3.5)]
line_5 = [(9.8, 3.5 + 3.5 + 3.5), (9.8 - 20, 3.5 + 3.5 + 3.5)]
# line_2 = [(1, 7), (3, 6)]
collection_1_2 = collections.LineCollection([line_1, line_2, line_3, line_4, line_5], color="green")
ax.add_collection(collection_1_2)

def get_dist_tof(tof): 
    return tof * 0.00029979245

def circles_cross_points(x1, y1, r1, x2, y2, r2):
    rr0 = (x2 - x1)**2 + (y2 - y1)**2
    xd = x2 - x1
    yd = y2 - y1
    rr1 = r1**2; rr2 = r2**2
    cv = (rr0 + rr1 - rr2)
    sv = (4*rr0*rr1 - cv**2)**.5
    return (
        (x1 + (cv*xd - sv*yd)/(2.*rr0), y1 + (cv*yd + sv*xd)/(2.*rr0)),
        (x1 + (cv*xd + sv*yd)/(2.*rr0), y1 + (cv*yd - sv*xd)/(2.*rr0)),
    )

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
timespan_ms = 200

half_timespan_ms = timespan_ms / 2

ser_1 = Serial(port=args.p1, baudrate=115200)
ser_2 = Serial(port=args.p2, baudrate=115200)

# パーティクルフィルタの初期化
n_particle = 500
particles = [Particle(position=(5 + 4.8, 6.6),weight=1/n_particle) for p in range(n_particle)]
beacons = [Beacon(position= (-5, 0)), Beacon(position=(5, 0))]
pfilter = ParticleFilter(particles)

x1 = beacons[0].position[0]
x2 = beacons[1].position[0]
y1 = beacons[0].position[1]
y2 = beacons[1].position[1]

scatter_particles = ax.scatter([p.position[0] for p in pfilter.particles],[p.position[1] for p in pfilter.particles], c="blue", s=10)
scatter_estimate_pos = ax.scatter(9.8, 6.6, c="red", s=30)
scatter_estimate_pos_lpf = ax.scatter(9.8, 6.6, c="orange", s=30)

calibration_flg = True
def end_calibration(): 
    global calibration_flg
    calibration_flg = False
keyboard.on_press_key('enter', lambda _: end_calibration())

# 最初はキャリブレーション
print("#----------------------------------------#")
print("#-----キャリブレーションを開始します------#")
print("#--------Enterキーを押下して終了----------#")
print("#----------------------------------------#")

values_beacon_1 = []
values_beacon_2 = []

with open(args.dir + "/offset.log", 'w') as offset_file:
    while calibration_flg:
        try:
            plt.pause(timespan_ms / 1000)
            # beacon 1
            ser_1.write(b'm')
            value_beacon_1 = 0
            raw_beacon_1 = ser_1.readline()
            if raw_beacon_1.strip() != b'':
                value_beacon_1 = int(raw_beacon_1.strip())
                values_beacon_1.append(value_beacon_1)
            ser_1.flush()
            # beacon 2
            ser_2.write(b'm')
            value_beacon_2 = 0
            raw_beacon_2 = ser_2.readline()
            if raw_beacon_2.strip() != b'':
                value_beacon_2 = int(raw_beacon_2.strip())     
                values_beacon_2.append(value_beacon_2)
            ser_2.flush()
            
            print(value_beacon_1, value_beacon_2)
            offset_file.write(f"{value_beacon_1},{value_beacon_2}\n")
            
            est_pos = circles_cross_points(x1, y1, get_dist_tof(value_beacon_1), x2, y2, get_dist_tof(value_beacon_2))
            
            is_cross_point_valid = (type(est_pos[0][0]) is not complex) and (type(est_pos[0][1]) is not complex)
            is_ovservation_succeed = value_beacon_1 > 10000 and value_beacon_2 > 10000
            
            if is_ovservation_succeed and is_cross_point_valid:
                scatter_estimate_pos.set_offsets([est_pos[0][0],est_pos[0][1]])
            else:
                scatter_estimate_pos.set_offsets((0,0))
            
        except ValueError as ve:
            print(ve)
    

# 計測開始
print("#---------------------------#")
print("#------計測を開始します------#")
print("#---------------------------#")
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
                plt.pause(timespan_ms / 1000)
                
                # ビーコン1 計測
                timestamp_beacon1_start = getTimeMs()                
                ser_1.write(b'm')
                value_beacon_1 = 0
                raw_beacon_1 = ser_1.readline()
                if raw_beacon_1.strip() != b'':
                    value_beacon_1 = int(raw_beacon_1.strip())
                ser_1.flush()
                timestamp_beacon1_end = getTimeMs()
                
                #ビーコン2 計測
                timestamp_beacon2_start = getTimeMs()
                ser_2.write(b'm')
                value_beacon_2 = 0
                raw_beacon_2 = ser_2.readline()
                if raw_beacon_2.strip() != b'':
                    value_beacon_2 = int(raw_beacon_2.strip())                    
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
            
            output = "{},{},{},{},{}".format(cnt, timestamp_beacon1_start, elapsed_time_ms, value_beacon_1, value_beacon_2)
            log_file.write(output + "\n")
            print(output)

            # 計測終了
            # フィルタ処理とプロット
            scatter_particles.set_offsets([[p.position[0], p.position[1]] for p in pfilter.particles])
        
            # 観測
            d1 = get_dist_tof(value_beacon_1)
            d2 = get_dist_tof(value_beacon_2)
        
            if cnt > 0:
            
                new_time = timestamp_beacon1_start
                diff = new_time - old_time
                delta = (diff / 1000)    
            
                # LPF 
                # y[n] = (1-a) * x[n] + a * y[n-1]
                const = 0.9
                tof1_filtered = (1 - const) * value_beacon_1 + (const * old_tof1)
                tof2_filtered = (1 - const) * value_beacon_2 + (const * old_tof2)

                # 三点測量による予測点のプロット
                # 生データ
                est_pos = circles_cross_points(x1, y1, d1, x2, y2, d2)
                scatter_estimate_pos.set_offsets([est_pos[0][0],est_pos[0][1]])
                # LPF
                est_pos_lpf = circles_cross_points(x1, y1, d1, x2, y2, d2)
                scatter_estimate_pos_lpf.set_offsets([est_pos_lpf[0][0],est_pos_lpf[0][1]])
                
                # パーティクルフィルタ:
                # 予測: 指定秒数動かす
                pfilter.move_particle_random(speed_abs=1, duration=delta)
                
                # 観測
                # 両ビーコンのデータがなければスキップ
                if value_beacon_1 > 0 and value_beacon_2 > 0:
                    pfilter.observation_dual(tof1_filtered, tof2_filtered, beacons[0], beacons[1])
                    old_tof1 = tof1_filtered
                    old_tof2 = tof2_filtered
            else:
                new_time = timestamp_beacon1_start
                old_tof1 = value_beacon_1
                old_tof2 = value_beacon_2
    
            old_time = new_time
            cnt+=1
            elapsed_time_ms += (timestamp_end - timestamp_start)
            
            if cnt == args.n:
                break
        
        except KeyboardInterrupt:
            ser_1.close()
            ser_2.close()
            break
        
    print("#---------------------------#")
    print("#------計測を終了します------#")
    print("#---------------------------#")