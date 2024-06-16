
import copy
from math import cos, exp, floor, pi, sin, sqrt
import math
import random
import numpy as np

class Particle:
    def __init__(self, position=(0.0, 0.0), weight=0.0, timeslot=0):
        self.position = position
        self.weight = weight
        self.timeslot = timeslot

class Beacon:
    def __init__(self, position=(0.0, 0.0)):
        self.position = position

    def get_estimated_tof(self, particle: Particle):
        distance = np.linalg.norm(np.array(particle.position) - np.array(self.position))
        return floor(distance * 10 ** 12 / 299792458)
    
    def get_estimated_rssi(self,  particle: Particle):
        distance = np.linalg.norm(np.array(particle.position) - np.array(self.position))
        return 108 - 20 * math.log10(distance / 0.02)

class ParticleFilter:
    def __init__(self, particles):
        self.particles = particles
        self.random_vectors = [random.uniform(0, 2 * pi) for _ in particles]

    # 尤度計算
    def _calculate_likelihood(self, tof, particle: Particle, beacon: Beacon):
        sigma = 5000
        # ビーコンとパーティクルの座標から, 予測ToFを求める
        ideal_tof = beacon.get_estimated_tof(particle)
        # print(ideal_tof, tof)
        # 予測ToFを中心としたガウス分布から, 実際のToFがどれだけ離れているかを求める
        likelihood = (1 / sqrt(2 * pi * (sigma ** 2))) * exp( -((tof - ideal_tof) ** 2) / (2 * (sigma ** 2)))
        # print(likelihood)
        particle.weight = particle.weight * likelihood

    def _calc_ess(self):
        return 1. / np.sum(np.square([p.weight for p in self.particles]))
        
    # リサンプリング
    def _resample(self):
        ws = np.cumsum([p.weight for p in self.particles])
        if ws[-1] < 1e-100: ws=[w+1e-100 for w in ws]
        
        step = ws[-1]/len(self.particles)
        r = np.random.uniform(0.0, step)
        cur_pos = 0
        ps = []
        
        while(len(ps) < len(self.particles)):
            if r < ws[cur_pos]:
                ps.append(self.particles[cur_pos])
                r += step
            else:
                cur_pos += 1

        self.particles = [copy.deepcopy(p) for p in ps]
        for p in self.particles: 
            p.weight = 1.0/len(self.particles)

    # 与えられた速度ベクトルに従って移動
    def move_particle(self, speed, duration, error):
        for particle in self.particles:
            particle.position = (particle.position[0] + speed[0] * duration + np.random.normal(0, error),
                                 particle.position[1] + speed[1] * duration + np.random.normal(0, error))

    # 速度情報をもとに, ランダムな方向に移動
    def move_particle_random(self, speed_abs, duration):

        idx = 0
        for index, particle in enumerate(self.particles):
            
            # ランダムな角度の生成（0から2π）
            random_angle = random.uniform(0, 2 * pi)
            
            error = 0.2
            random_speed = random.uniform(speed_abs - error, speed_abs + error)
            
            # 4方向に絞る
            directions = [0, pi / 2, pi, 3 * pi / 2]  # 0度、90度、180度、270度
            # directions = [0, pi / 4, pi / 2, 3 * pi / 4, pi, 5 * pi / 4, 3 * pi / 2, 7 * pi / 4]
            rounded_angle = min(directions, key=lambda x: abs(x - self.random_vectors[idx]))
            
            # particle.position = (particle.position[0] + random_speed * cos(self.random_vectors[index]) * duration ,
            #                      particle.position[1] + random_speed * sin(self.random_vectors[index]) * duration ) 
            particle.position = (particle.position[0] + speed_abs * cos(rounded_angle) * duration ,
                                 particle.position[1] + speed_abs * sin(rounded_angle) * duration ) 
            idx += 1
        
    # 観測
    def observation(self, tof, beacon):
        # 尤度計算 
        for particle in self.particles:
            self._calculate_likelihood(tof, particle, beacon)
        # 正規化
        weights = [p.weight for p in self.particles]
        weight_sum = np.sum(weights)
        normalized_weights = weights / weight_sum
        for idx, particle in enumerate(self.particles):
            particle.weight = normalized_weights[idx]

        # リサンプリング
        self._resample()
        
    def normalize(self):
        weights = [p.weight for p in self.particles]
        weight_sum = np.sum(weights)
        normalized_weights = weights / weight_sum
        for idx, particle in enumerate(self.particles):
            particle.weight = normalized_weights[idx]
            
    def calc_likelyhood_gaussian(self, sigma, observed, ideal):
        return (1 / sqrt(2 * pi * (sigma ** 2))) * exp( -((ideal - observed) ** 2) / (2 * (sigma ** 2)))
        
    def observation_dual(self, tof1, tof2, beacon1: Beacon, beacon2: Beacon):
        sigma = 3000
        for particle in self.particles:
            # ビーコンとパーティクルの座標から, 予測ToFを求める
            ideal_tof_1 = beacon1.get_estimated_tof(particle)
            ideal_tof_2 = beacon2.get_estimated_tof(particle)
            if abs(ideal_tof_1 - tof1)  > sigma:
                # 捨てる
                pass
            # 予測ToFを中心としたガウス分布から, 実際のToFがどれだけ離れているかを求める
            likelihood_1 = self.calc_likelyhood_gaussian(sigma, tof1, ideal_tof_1)
            likelihood_2 = self.calc_likelyhood_gaussian(sigma, tof2, ideal_tof_2)
            particle.weight = likelihood_1 * likelihood_2 
        #正規化
        self.normalize()
        # リサンプリング
        ess = self._calc_ess()
        if ess < len(self.particles) / 2:
            self._resample()
            self.random_vectors = [random.uniform(0, 2 * pi) for _ in self.particles]
            
    def observation_dual_tof_rssi(self, tof1, tof2, rssi1, rssi2, beacon1: Beacon, beacon2: Beacon):
        
        sigma_tof = 3000
        sigma_rssi = 1
        
        for particle in self.particles:
            # ビーコンとパーティクルの座標から, 予測ToFを求める
            ideal_tof_1 = beacon1.get_estimated_tof(particle)
            ideal_tof_2 = beacon2.get_estimated_tof(particle)
            ideal_rssi_1 = beacon1.get_estimated_rssi(particle)
            ideal_rssi_2 = beacon2.get_estimated_rssi(particle)
            
            if abs(ideal_tof_1 - tof1)  > sigma_tof:
                # 捨てる
                pass
            
            # 値が小さくなりすぎるので定数倍する
            factor = 10 ** 5
            # 予測ToFを中心としたガウス分布から, 実際のToFがどれだけ離れているかを求める
            likelihood_1_tof =  self.calc_likelyhood_gaussian(sigma_tof, tof1, ideal_tof_1) * factor
            likelihood_2_tof =  self.calc_likelyhood_gaussian(sigma_tof, tof2, ideal_tof_2) * factor 
            likelihood_1_rssi = self.calc_likelyhood_gaussian(sigma_rssi, rssi1, ideal_rssi_1) * factor
            likelihood_2_rssi = self.calc_likelyhood_gaussian(sigma_rssi, rssi2, ideal_rssi_2) * factor
            particle.weight = likelihood_1_tof * likelihood_2_tof
            # particle.weight = likelihood_1_tof * likelihood_2_tof * likelihood_1_rssi * likelihood_2_rssi
        
        #正規化
        self.normalize()
        # リサンプリング
        ess = self._calc_ess()
        if ess < len(self.particles) / 2:
            self._resample()
            self.random_vectors = [random.uniform(0, 2 * pi) for _ in self.particles]
            
    def estimate(self):
        """ 重みの付いた粒子の平均と共分散行列を返す。 """
        
        weights = np.array([p.weight for p in self.particles])
        particles = np.array(self.particles)
        
        w = weights.reshape(len(particles), 1)
        pos = [p.position for p in self.particles]
        mean = np.sum(pos * w, axis=0)
        var  = np.sum((pos - mean)**2 * w, axis=0)
        return mean, var