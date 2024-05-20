from datetime import datetime

def sort_log_by_time(log_file_path, output_file_path):
    # ログを読み込んで時系列でソートするための関数
    def get_timestamp(log_entry):
        # ログエントリから時間を取得する
        return datetime.strptime(log_entry.split(',')[0], '%H:%M:%S.%f')

    # ログファイルを読み込む
    with open(log_file_path, 'r', encoding='utf-8') as file:
        log_entries = file.readlines()

    # 時系列でソート
    sorted_log = sorted(log_entries, key=get_timestamp)

    # ソートしたログを新しいファイルに書き込む
    with open(output_file_path, 'w', encoding='utf-8') as file:
        # ソートしたログを書き込む
        file.writelines(sorted_log)

# 使用例
input_log_path = 'data.log'
output_log_path = 'data_sorted.log'
sort_log_by_time(input_log_path, output_log_path)