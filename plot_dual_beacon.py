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
    
time = 0.0

# パーティクルフィルタの初期化
n_particle = 1000
particle_initial_pos = (9.8, 6.6)
beacon_initial_pos = [(-5, 0), (5, 0)]

particles = [Particle(particle_initial_pos, weight=1/n_particle) for p in range(n_particle)]
beacons = [Beacon(position= beacon_initial_pos[0]), Beacon(position=beacon_initial_pos[1])]
pfilter = ParticleFilter(particles)


fig, ax = plt.subplots()
fig.set_size_inches(16, 5.2)
ax.grid()

# プロット軸設定
ticks_x = np.linspace(-20, 20, 41)
ticks_y = np.linspace(0, 13, 14)
ax.set_xlim(-20, 20)
ax.set_ylim(0, 13)
ax.set_xticks(ticks_x)
ax.set_yticks(ticks_y)

# ビーコンをプロット
ax.scatter(beacon_initial_pos[0][0], beacon_initial_pos[0][1], c="orange", s=100)
ax.scatter(beacon_initial_pos[1][0], beacon_initial_pos[1][1], c="orange", s=100) 

# line_1 = [(9.8, 3.5), (9.8 - 20, 3.5)]
# line_2 = [(9.8 - 20, 3.5), (9.8 - 20, 3.5 + 3.5)]
line_3 = [(9.8 - 20, 6.6), (9.8, 6.6)]
# line_4 = [(9.8, 3.5 + 3.5), (9.8, 3.5 + 3.5 + 3.5)]
# line_5 = [(9.8, 3.5 + 3.5 + 3.5), (9.8 - 20, 3.5 + 3.5 + 3.5)]

error_circle = patches.Circle(xy=particle_initial_pos, radius=5, ec='r', fill=False)

collection_1_2 = collections.LineCollection([line_3], color="green")
ax.add_collection(collection_1_2)
ax.add_patch(error_circle)

scatter_particles = ax.scatter([p.position[0] for p in pfilter.particles], [p.position[1] for p in pfilter.particles], c="blue", s=5) 
scatter_tof_cross_point = ax.scatter(9.8,6.6, c="red", s=100)
scatter_pfilter_est_point = ax.scatter(9.8,6.6, c="green", s=100)

speed = 0.53

try:

    with open("0131_take6/data.log", "r") as f:
        idx = 0
        old_time = None
        new_time = None
        
        old_tof1 = 0
        old_tof2 = 0
            
        estimated_pos = particle_initial_pos
        
        for row in f:
            
            # scatter.set_offsets([[p.position[0], p.position[1]] for p in pfilter.particles]) 
            
            # 観測
            tof1 = int(row.split(',')[3]) + 5000
            tof2 = int(row.split(',')[4]) + 7000
            d1 = get_dist_tof(tof1)
            d2 = get_dist_tof(tof2)
                
            x1 = beacons[0].position[0]
            x2 = beacons[1].position[0]
            
            y1 = beacons[0].position[1]
            y2 = beacons[1].position[1]
            if idx == 0:
                plt.pause(10)
            
            if idx > 0:
                
                if idx > 334:
                    while True:
                        plt.pause(1)
                
                new_time = int(row.split(',')[1])
                diff = new_time - old_time
                delta = (diff / 1000)
                
                # LPF 
                # y[n] = (1-a) * x[n] + a * y[n-1]
                const = 0.9
                tof1_filtered = (1 - const) * tof1 + (const * old_tof1)
                tof2_filtered = (1 - const) * tof2 + (const * old_tof2)
                
                tof_est_point = circles_cross_points(x1, y1, get_dist_tof(tof1_filtered), x2, y2, get_dist_tof(tof2_filtered))

                # 待つ
                plt.pause(delta/10)
                # 指定秒数動かす
                pfilter.move_particle_random(speed_abs=speed, duration=delta)
                scatter_particles.set_offsets([[p.position[0], p.position[1]] for p in pfilter.particles])
                
                # 理想位置
                if idx <= 136:
                    estimated_pos = (estimated_pos[0] + (-speed * delta), particle_initial_pos[1])
                    error_circle.set_center(estimated_pos)
            
                if idx > 203 and idx <= 334:
                    estimated_pos = (estimated_pos[0] + (speed * delta), particle_initial_pos[1])
                    error_circle.set_center(estimated_pos)
                              
                is_ovservation_succeed = tof1 > 5000 and tof2 > 7000
                is_cross_point_valid = (type(tof_est_point[0][0]) is not complex) and (type(tof_est_point[0][1]) is not complex)
                
                if is_ovservation_succeed and is_cross_point_valid:
                    pfilter.observation_dual(tof1_filtered, tof2_filtered, beacons[0], beacons[1])                 
                    scatter_tof_cross_point.set_visible(True)
                    scatter_tof_cross_point.set_offsets(([tof_est_point[0][0],tof_est_point[0][1]]))
                else:
                    scatter_tof_cross_point.set_visible(False)
                
                est, err = pfilter.estimate()
                error_result = np.linalg.norm(np.array(estimated_pos) - np.array(est))
                error_only_tof = ""
                if is_cross_point_valid:
                    error_only_tof = np.linalg.norm(np.array(tof_est_point[0]) - np.array(estimated_pos))
                scatter_pfilter_est_point.set_offsets(est)
                print(error_result, error_only_tof)

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