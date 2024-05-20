import numpy as np
from dateutil.parser import parse

with open("double_tof_data/dual_honban_2/data.log", "r") as f:
    data_dict = {}
    data_avg_dict = {}
    
    for row in f:
        raw = row.replace('\n', '')
        arr = raw.split(",")
        
        if arr[0] not in data_dict:
            data_dict[arr[0]] = [int(arr[1])]
        else:
            data_dict[arr[0]].append(int(arr[1]))
            
    for k,v in data_dict.items():
        data_avg_dict[k] = int(np.mean(v))
        
    old_time_str = ''
    for k,v in data_avg_dict.items():
        print("{},{},{}".format(k,v,1))
        time = parse(k)
        if old_time_str != '':
            old_time = parse(old_time_str)
            diff = time - old_time
            # print("{},{},{}".format(diff, time,v))
            # print("{}".format(int(diff.microseconds / 1000)))
        # else:
            # print("{},{}".format(time,v))
        old_time_str = k
        
