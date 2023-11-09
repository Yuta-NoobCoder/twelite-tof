import argparse
import numpy as np
import matplotlib.pyplot as plt

def convert_to_meter(value):
    return value * 0.000299792458

def table_string(title, value):
    return "{:<9}{:>8.2f}[ps] {:>6.2f}[m]".format(title + ":", value, convert_to_meter(value))

# コマンドライン引数
parser = argparse.ArgumentParser()
parser.add_argument("--dir", required=True) # 入力ファイル
parser.add_argument("--title", required=True) # タイトル
parser.add_argument("--filter",  action='store_true') # 外れ値の除外
parser.add_argument("--plot_analyze",  action='store_true') # 解析値をグラフに含める
args = parser.parse_args()

values = []
n_lines = 0
num_bins = 100

# ファイルを読み込んで数値をリストに追加
with open("{}/data.log".format(args.dir), 'r') as file:
	for line in file:
		try:
			value = int(line.strip())
			values.append(value)
			n_lines += 1
		except ValueError:
			pass  # 数値以外の行は無視

# 四分位範囲を用いた外れ値のフィルター
# filterオプションが指定されていなければ無視

filtered = np.array(values)
if args.filter == True:
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    filter_min = q1 - iqr * 1.5
    filter_max = q3 + iqr * 1.5
    filtered = filtered[(filtered >= filter_min) & (filtered < filter_max)]

# 平均値
average = np.average(filtered)
# 最頻値
unique, freq = np.unique(filtered, return_counts=True)
mode = unique[np.argmax(freq)]

#各値から計測した平均値 Σ(頻度/母数 * 計測値)
μ = 0
for i in range(0, len(unique)):
    μ += (float(freq[i] / n_lines) * unique[i])

# 中央値
median = np.median(filtered)
# 標準偏差
sigma = np.std(filtered)
# 分散
dispersion = sigma ** 2

# ヒストグラムをプロット
fig, ax = plt.subplots(1,1)
ax.hist(filtered, bins=num_bins, density=True)
# --plot_analyzeオプション指定で画像中に解析値を含める
if args.plot_analyze:
    plt.text(0.01, 0.99, "\n".join([table_string('mode', mode),
                                    table_string('median', median),
                                    table_string('μ', average),
                                    table_string('σ', sigma)]),
            horizontalalignment='left', verticalalignment='top', family='monospace', fontsize=8, transform=ax.transAxes)

print("最頻値")
print("{:>.2f}[ps] {:.2f}[m]".format(mode, convert_to_meter(mode)))
print("中央値")
print("{:>.2f}[ps] {:.2f}[m]".format(median, convert_to_meter(median)))
print("平均値, μ")
print("{:>.2f}[ps] {:.2f}[m]".format(average, convert_to_meter(average)))
print("{:>.2f}[ps] {:.2f}[m]".format(μ, convert_to_meter(μ)))
print("標準偏差")
print("{:<.2f}".format(sigma))
print("分散")
print("{:<.2f}".format(dispersion))

# print("レイリー分布におけるσ, 期待値")
# print("{:>.2f}[ps]{:>8.2f}[m]".format(mode, convert_to_meter(mode)))
# print("{:>.2f}[ps]{:>8.2f}[m]".format(mode * np.sqrt(np.pi / 2), convert_to_meter(mode * np.sqrt(np.pi / 2))))
# print("最尤推定値: {}".format(np.sqrt((1 / (2 * n_lines)) * np.sum(list(map(lambda x: x ** 2, values))))))
x = np.linspace(min(filtered), max(filtered), len(filtered))
y_gauss = 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(x - average) ** 2 / (2 * sigma ** 2))
# y_rayleigh = (x / (mode ** 2)) * np.exp( -1 * (x ** 2) / (2 * (mode ** 2)))
plt.subplots_adjust(left=0.16, right=0.95, bottom=0.12, top=0.92)

plt.plot(x, y_gauss, color='red', label='Gauss')
# plt.plot(x, y_rayleigh, color='lime', label='Rayleigh')

plt.xlabel('ToF [ps]')
plt.ylabel('Probability Density')
plt.title('ToF Histgram and Distribution [{}]'.format(args.title))
# plt.legend()
plt.savefig("{}/{}.png".format(args.dir, args.title))