from ast import parse
from datetime import datetime
import dis
from math import ceil, e
import math
import scipy
from particle_filter import Particle, Beacon, ParticleFilter
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import collections, patches

def get_dist_tof(tof): 
    return tof * 0.00029979245

def get_dist_rssi(rssi):
    return 0.02 * (10 ** ((108 - rssi) / 20))

def get_rssi_from_dist(dist):
    return 108 - 20 * math.log10(dist / 0.02)

def find_circle_intersections(x1, y1, r1, x2, y2, r2):
    # 距離を計算
    d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    # 交点が存在しない場合
    if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
        # print("intersection not found, d={}, r1={}, r2={}".format(d, r1, r2))
        return (0, 0)
    
    # 交点を計算
    a = (r1 ** 2 - r2 ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(r1 ** 2 - a ** 2)
    x0 = x1 + a * (x2 - x1) / d
    y0 = y1 + a * (y2 - y1) / d
    rx = -h * (y2 - y1) / d
    ry = h * (x2 - x1) / d
    
    intersection1 = (x0 + rx, y0 + ry)
    intersection2 = (x0 - rx, y0 - ry)
    
    # y座標が正の交点を返す
    if intersection1[1] >= 0 and intersection2[1] >= 0:
        return intersection1, intersection2
    elif intersection1[1] >= 0:
        return intersection1
    elif intersection2[1] >= 0:
        return intersection2
    else:
        return (0, 0)
    
time = 0.0

# パーティクルフィルタの初期化
n_particle = 1000
particle_initial_pos = (-6.6, 1.8)
beacon_initial_pos = [(-5, 0), (5, 0)]

particles = [Particle(particle_initial_pos, weight=1/n_particle) for p in range(n_particle)]
beacons = [Beacon(position= beacon_initial_pos[0]), Beacon(position=beacon_initial_pos[1])]
pfilter = ParticleFilter(particles)

# プロット軸設定
fig, ax = plt.subplots()
fig.set_size_inches(6, 8)
ax.grid()

plot_w = 15
plot_h = 25

ticks_x = np.linspace(-plot_w, plot_w, plot_w * 2 + 1)
ticks_y = np.linspace(-1, plot_h, plot_h + 2)
ax.set_xlim(-plot_w, plot_w)
ax.set_ylim(-1, plot_h)
ax.set_xticks(ticks_x)
ax.set_yticks(ticks_y)

# ビーコンをプロット
ax.scatter(beacon_initial_pos[0][0], beacon_initial_pos[0][1], c="orange", s=100)
ax.scatter(beacon_initial_pos[1][0], beacon_initial_pos[1][1], c="orange", s=100) 

course_w = 12
course_h = 19

line_1 = [particle_initial_pos, (particle_initial_pos[0] + course_w, particle_initial_pos[1])]
line_2 = [particle_initial_pos, (particle_initial_pos[0], particle_initial_pos[1] + course_h)]
line_3 = [(particle_initial_pos[0] + course_w, particle_initial_pos[1]), (particle_initial_pos[0] + course_w, particle_initial_pos[1] + course_h)]
line_4 = [(particle_initial_pos[0], particle_initial_pos[1] + course_h), (particle_initial_pos[0] + course_w, particle_initial_pos[1] + course_h)]

# error_circle = patches.Circle(xy=particle_initial_pos, radius=5, ec='r', fill=False)

collection_1_2 = collections.LineCollection([line_1, line_2, line_3, line_4], color="gray")
ax.add_collection(collection_1_2)
# ax.add_patch(error_circle)

scatter_particles = ax.scatter([p.position[0] for p in pfilter.particles], [p.position[1] for p in pfilter.particles], c="blue", s=5) 
scatter_tof_cross_point = ax.scatter(particle_initial_pos[0], particle_initial_pos[1], c="red", s=100)
scatter_rssi_cross_point = ax.scatter(particle_initial_pos[0], particle_initial_pos[1], c="purple", s=100)
scatter_pfilter_est_point = ax.scatter(particle_initial_pos[0], particle_initial_pos[1], c="green", s=100)

speed = 0.775
# 0.775

try:

    with open("0609_test_3/data.log", "r") as f:
        #ループ内変数
        idx = 0
        old_time = None
        new_time = None
        
        old_tof1 = 0
        old_tof2 = 0
            
        estimated_pos = particle_initial_pos
        initial_time = 0
        
        for row in f:
            
            # scatter.set_offsets([[p.position[0], p.position[1]] for p in pfilter.particles]) 
            
            # 観測
            tof1 = int(row.split(',')[3])
            tof2 = int(row.split(',')[4])
            rssi1 = int(row.split(',')[5])
            rssi2 = int(row.split(',')[6])
            d1 = get_dist_tof(tof1)
            d2 = get_dist_tof(tof2)
                
            x1 = beacons[0].position[0]
            x2 = beacons[1].position[0]
            
            y1 = beacons[0].position[1]
            y2 = beacons[1].position[1]
        
            if idx == 0:
                initial_time = int(row.split(',')[1])
            
            if idx > 0:
                
                # if idx > 334:
                #     while True:
                #         plt.pause(1)
                
                new_time = int(row.split(',')[1])
                diff = new_time - old_time
                delta = (diff / 1000)
                
                # print((new_time - initial_time) / 1000, find_circle_intersections(x1, y1, get_dist_rssi(rssi1), x2, y2, get_dist_rssi(rssi2)))
                
                # LPF 
                # y[n] = (1-a) * x[n] + a * y[n-1]
                const = 0.9
                tof1_filtered = (1 - const) * tof1 + (const * old_tof1)
                tof2_filtered = (1 - const) * tof2 + (const * old_tof2)
                
                tof_est_point = find_circle_intersections(x1, y1, get_dist_tof(tof1_filtered), x2, y2, get_dist_tof(tof2_filtered))
                rssi_est_point = find_circle_intersections(x1, y1, get_dist_rssi(rssi1), x2, y2, get_dist_rssi(rssi2))
                # tof_est_point = circles_cross_points(x1, y1, get_dist_tof(tof1_filtered), x2, y2, get_dist_tof(tof2_filtered))

                # 待つ
                plt.pause(delta / 5)
                # 指定秒数動かす
                pfilter.move_particle_random(speed_abs=speed, duration=delta)
                scatter_particles.set_offsets([[p.position[0], p.position[1]] for p in pfilter.particles])
                
                # # 理想位置
                # if idx <= 136:
                #     estimated_pos = (estimated_pos[0] + (-speed * delta), particle_initial_pos[1])
                #     error_circle.set_center(estimated_pos)
            
                # if idx > 203 and idx <= 334:
                #     estimated_pos = (estimated_pos[0] + (speed * delta), particle_initial_pos[1])
                #     error_circle.set_center(estimated_pos)
                
                # ToFによる三辺測量のプロット
                is_ovservation_succeed_tof = tof1 > 0 and tof2 > 0
                if is_ovservation_succeed_tof:
                    pfilter.observation_dual_tof_rssi(tof1_filtered, tof2_filtered, rssi1, rssi2, beacons[0], beacons[1])
                    scatter_tof_cross_point.set_visible(True)
                    scatter_tof_cross_point.set_offsets(([tof_est_point[0], tof_est_point[1]]))                 
                else:
                    scatter_tof_cross_point.set_visible(False)
                    
                # RSSIによる三辺測量のプロット
                is_ovservation_succeed_rssi = rssi1 > 0 and rssi2 > 0
                if is_ovservation_succeed_rssi:
                    scatter_rssi_cross_point.set_visible(True)
                    scatter_rssi_cross_point.set_offsets(([rssi_est_point[0], rssi_est_point[1]]))
                else:
                    scatter_rssi_cross_point.set_visible(False)
                                
                est, err = pfilter.estimate()
                error_result = np.linalg.norm(np.array(estimated_pos) - np.array(est))
                error_only_tof = ""
                
                # 誤差の計算
                error_only_tof = np.linalg.norm(np.array(tof_est_point) - np.array(estimated_pos))
                error_only_rssi = np.linalg.norm(np.array(rssi_est_point) - np.array(rssi_est_point))
                
                scatter_pfilter_est_point.set_offsets(est)

                old_tof1 = tof1_filtered
                old_tof2 = tof2_filtered
            else:
                new_time = int(row.split(',')[1])
                old_tof1 = tof1
                old_tof2 = tof2
            
            old_time = new_time

            idx += 1
except KeyboardInterrupt:
    pass