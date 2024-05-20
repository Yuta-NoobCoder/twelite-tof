def calculate_coordinate(x1, y1, d1, x2, y2, d2):
    # AからBへのベクトル
    delta_x = x2 - x1
    delta_y = y2 - y1
    
    # C点までの比率
    ratio = d1 / (d1 + d2)
    
    # C点の座標
    x = x1 + ratio * delta_x
    y = y1 + ratio * delta_y
    
    return x, y

# 例として、点A(0, 0)、点B(3, 4)、それぞれの距離が5と4の場合
x1, y1 = 0, 0
x2, y2 = 3, 4
d1, d2 = 5, 4

result = calculate_coordinate(x1, y1, d1, x2, y2, d2)
print(f"点Cの座標: {result}")