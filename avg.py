import csv

def calculate_average(filename):
    with open(filename, 'r') as file:
        # CSVファイルをリストに変換
        rows = [list(map(int, row)) for row in csv.reader(file)]

    # 各列の合計とカウントを保存する変数
    sum_col1, sum_col2, count_col1, count_col2 = 0, 0, 0, 0

    # 合計とカウントを計算
    for row in rows:
        if row[0] != -1:
            sum_col1 += row[0]
            count_col1 += 1
        if row[1] != -1:
            sum_col2 += row[1]
            count_col2 += 1

    # 平均を計算
    avg_col1 = sum_col1 / count_col1 if count_col1 > 0 else None
    avg_col2 = sum_col2 / count_col2 if count_col2 > 0 else None

    return avg_col1, avg_col2

# ファイル名を指定して平均を計算
filename = '0131_take6/offset.log'  # ファイル名を実際のファイル名に変更してください
avg_col1, avg_col2 = calculate_average(filename)

# 結果を出力
print(f"1列目の平均: {avg_col1}")
print(f"2列目の平均: {avg_col2}")

import math

def calculate_distance(x1, y1, x2, y2):
    # 2点間の距離を計算
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance

# 2点の座標を入力として受け取る
# x1 = float(input("点1のx座標を入力してください: "))
# y1 = float(input("点1のy座標を入力してください: "))
# x2 = float(input("点2のx座標を入力してください: "))
# y2 = float(input("点2のy座標を入力してください: "))

p1 = (5, 0)
p2 = (4.8, 6.6)

# 距離を計算
distance = calculate_distance(p1[0], p1[1], p2[0], p2[1])

# 0.000297をかける
result = distance / 0.000297

# 結果を表示
print(f"2点間の距離: {distance}")
print(f"計算結果（0.000297をかけた値）: {result}")