import numpy as np
import matplotlib.pyplot as plt
import serial
import argparse
import os

# コマンドライン引数
parser = argparse.ArgumentParser()
parser.add_argument("--port", required=True)         # COMポート番号
parser.add_argument("--name", required=True)         # 出力ディレクトリ名
parser.add_argument("--n", type=int)                 # プロット数
args = parser.parse_args()

try:
    os.mkdir(args.name)
except FileExistsError:
    pass

log_file_path = args.name + "/data.log"	 # ログファイル名
image_path = args.name + "/plot.png"     # グラフ画像名

values = []
values_m = []
n_lines = 0
num_bins = 100

ser = serial.Serial(port=args.port, baudrate=115200)
with open(log_file_path, 'w') as file:
    while True:
        try:
            value = int(ser.readline())
            values.append(value)
            value_m = float(value) * 0.0003 # メートルに換算
            
            values_m.append(value_m)
            n_lines += 1
            # 平均値
            average = np.mean(values)
            # 標準偏差
            sigma = np.std(values)
            sigma_m = np.std(values_m)
            # 期待値
            excepted = sigma_m * np.sqrt(np.pi / 2)
            #excepted = np.average(values_m)
            print("count: {}, value: {}".format(n_lines, value))
            # 最尤推定値
            # max_likehood = np.sqrt((1 / (2 * n_lines)) * np.sum(list(map(lambda x: x ** 2, values))))
            file.write("{}\n".format(value))
            
            # 100回ごとにグラフを更新する
            if n_lines == 1 or n_lines % 10 == 0:
                # ヒストグラムをプロット
                plt.clf()
                n, bins, patches = plt.hist(values, bins=num_bins)
                plt.xlabel('ToF [ps]')
                plt.ylabel('Frequency')
                plt.title('ToF Histgram and Rayleigh Distribution')
                plt.savefig(image_path)
                
            if n_lines == args.n:
                break

        except ValueError:
            pass # 数値以外の行は無
        except KeyboardInterrupt:
            ser.close()
            break