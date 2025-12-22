"""
process_7k_to_6k_tools.py中用到的函数
"""


import global_config
import other_tools as ott


def parse_hitobject_line(line):
    """
    将hitobject_line字符串根据含义解析为一个字典, 用于接下来生成track_data  
    line: 字符串  
    """
    parts = line.split(',') 
    x_coordinate = int(parts[0])  
    start_time = int(parts[2])   
    type_value = int(parts[3])   
    is_hold = (type_value == 128)
    end_time = start_time  
        
    if is_hold:
        extras = parts[5]
        end_time = int(extras.split(':')[0]) if ':' in extras else int(extras)
        
    return {
        'x': x_coordinate,
        'time': start_time,
        'end_time': end_time,
        'is_hold': is_hold,
        'original_line': line
        }
    

def x_to_track(x_coordinate):
    """
    根据x坐标, 确定按键的轨道号  
    x_coordinate: 0-511的整数
    """
    for track_index, (min_x, max_x) in enumerate(global_config.TRACK_RANGES_7):
        if min_x <= x_coordinate <= max_x:
            return track_index
    return 0 if x_coordinate < 0 else 6


def create_track_bitmaps(track_data, global_max_time):
    """
    创建轨道位图, 是一个含有7个字节数组的列表, 数组的长度为global_max_time + 1  
    当数组某一位为1, 表示某一轨道的某一时刻有按键 (需要按下)  
    track_data: 列表, 保存hitobjects_line解析得到的信息的数据结构  
    global_max_time: 约等于谱面时长 (毫秒)  
    """
    bitmap_length = global_max_time + 1 
    track_bitmaps = [bytearray(bitmap_length) for _ in range(7)]
    
    for track_index, intervals in track_data.items():
        for interval in intervals:
            for time_point in range(interval['start'], interval['end'] + 1):
                track_bitmaps[track_index][time_point] = 1
    return track_bitmaps


def create_key_shapes(track_date):
    """
    创建键型图, 是一个字典, key为所有出现过的时间刻, value为长度为7的列表  
    当列表某一元素为1, 表示某一时刻对应轨道的按键按下  
    track_date: 列表, 保存hitobjects_line解析得到的信息的数据结构  
    """
    key_shapes = {}
    for track_index in range(7):
        intervals = track_date[track_index]
        for interval in intervals:
            start = interval['start']
            if start not in key_shapes:
                key_shapes[start] = [0] * 7
            key_shapes[start][track_index] = 1
    return key_shapes



def generate_new_hitobject_line(original_line, old_x, new_x): 
    """
    返回修改x坐标后得到的新的hitobjects_line  
    original_line: 原来的hitobjects_line  
    old_x: 没有用到  
    new_x: 新的x坐标
    """
    parts = original_line.split(',')
    parts[0] = str(new_x) 
    return ','.join(parts)


def trans_4th_track(key_shapes, track_bitmaps, interval): 
    """
    按照一定的策略转移7k中间轨道按键  
    key_shapes: 键型图  
    track_bitmaps: 轨道位图  
    interval: 按键信息  
    """
    if not interval['is_hold']:
        hit_line = process_4th_track_note(key_shapes, track_bitmaps, interval)
    elif interval['is_hold']:
        hit_line = process_4th_track_hold(track_bitmaps, interval)
    return hit_line


# ========== 以下函数被trans_4th_track调用 ========== 


def get_key_num(key_shapes, time):
    key_num = 0
    for i in range(0, 7):
        if key_shapes[time][i] == 1:
            key_num = key_num + 1
    return key_num


def is_special_die(key_shapes, time, time_list):
    pre_time, next_time = get_pre_next_time(time, time_list)
    if pre_time and (
            key_shapes[time][0] & key_shapes[pre_time][0] == 0 and \
            key_shapes[time][1] & key_shapes[pre_time][1] == 0 and \
            key_shapes[time][2] & key_shapes[pre_time][2] == 0 and \
            key_shapes[time][3] & key_shapes[pre_time][3] == 1 and \
            key_shapes[time][4] & key_shapes[pre_time][4] == 0 and \
            key_shapes[time][5] & key_shapes[pre_time][5] == 0 and \
            key_shapes[time][6] & key_shapes[pre_time][6] == 0 
        ):
            return True
    if next_time and (
            key_shapes[time][0] & key_shapes[next_time][0] == 0 and \
            key_shapes[time][1] & key_shapes[next_time][1] == 0 and \
            key_shapes[time][2] & key_shapes[next_time][2] == 0 and \
            key_shapes[time][3] & key_shapes[next_time][3] == 1 and \
            key_shapes[time][4] & key_shapes[next_time][4] == 0 and \
            key_shapes[time][5] & key_shapes[next_time][5] == 0 and \
            key_shapes[time][6] & key_shapes[next_time][6] == 0 
        ):
            return True
    return False


def is_qie_a(key_shapes, time, time_list, target_tarck):
    pre_time, next_time = get_pre_next_time(time, time_list)
    a = b = True
    if pre_time and key_shapes[pre_time][target_tarck] == 1:
            a = False
    if next_time and key_shapes[next_time][target_tarck] == 1:
            b = False
    return (a and b)


def get_pre_next_time(time, time_list):
    pre_time = None
    next_time = None
    index = ott.binary_search(time_list, time)
    if index > 0:
        pre_time = time_list[index - 1]
    if index < len(time_list) - 1:
        next_time = time_list[index + 1]
    return pre_time, next_time


def is_interval_translatable(interval, target_track_bitmap, min_gap):
    extended_start = max(0, interval['start'] - min_gap)
    extended_end = interval['end'] + min_gap
    bitmap_lenth = len(target_track_bitmap)
    for time_point in range(extended_start, extended_end + 1):
        if time_point < bitmap_lenth and target_track_bitmap[time_point] == 1:
            return False
    return True


def process_4th_track_note(key_shapes, track_bitmaps, interval):
    """
    对中间轨道的大多数按键直接删除  
    对3种特殊情况分别处理
    """
    track_indexs = global_config.RANDOM_SEQUENCE_6[interval['start'] % 12]
    time_list = sorted(key_shapes.keys())
    key_num = get_key_num(key_shapes, interval['start'])
    new_hit_line = []

    def change_track_num(track_index): 
        if track_index in (0, 1, 2):
            return track_index
        elif track_index in (4, 5, 6):
            return track_index - 1

    if key_num in range(2, 7):
        if (
            is_special_die(key_shapes, interval['start'], time_list) and \
            is_interval_translatable(interval, track_bitmaps[2], global_config.MIN_TIME_GAP)
        ):
            new_hit_line.append(generate_new_hitobject_line(interval['original_line'], 1, 200))
        return new_hit_line
    if key_num == 1:
        if is_qie_a(key_shapes, interval['start'], time_list, 3):
            for track_index in track_indexs:
                if (
                    is_interval_translatable(interval, track_bitmaps[track_index], global_config.MIN_TIME_GAP) and \
                    is_qie_a(key_shapes, interval['start'], time_list, track_index)
                ):
                    new_track = change_track_num(track_index)
                    min_x, max_x = global_config.TRACK_RANGES_6[new_track]
                    new_x = (min_x + max_x) // 2
                    new_hit_line.append(generate_new_hitobject_line(interval['original_line'], 1, new_x))
                    return new_hit_line
        else:
            new_hit_line.append(generate_new_hitobject_line(interval['original_line'], 1, 200))
            return new_hit_line


def get_track_next_time(track_bitmaps, time, target_track):
    bitmap_lenth = len(track_bitmaps[0])
    for i in range(time + 1, bitmap_lenth):
        if track_bitmaps[target_track][i] == 1:
            return i
    return bitmap_lenth - 1


def process_4th_track_hold(track_bitmaps, interval):
    """
    让长按键在谱面比较稀疏时一般能移到第3轨道(1-7)  
    而在谱面比较密集时, 尽努力移到第3轨道  
    移动成功概率受global_config.MIN_TIME_GAP影响  
    """
    # 变量名摆烂了
    z = []
    a = get_track_next_time(track_bitmaps, interval['start'], 2)
    if a - global_config.MIN_TIME_GAP > interval['end']:
        c = interval['end']
    elif(
        a - global_config.MIN_TIME_GAP < interval['end'] and \
        a - global_config.MIN_TIME_GAP > interval['start'] 
    ):
        c = a - global_config.MIN_TIME_GAP
    else:
        c = -1

    x = True
    for j in range(interval['start'] - global_config.MIN_TIME_GAP, interval['start'] + 1):
        if track_bitmaps[2][j] == 1:
            x = False

    if x == True and c != -1:
        d = interval['original_line'].split(',')
        e = d[5].split(':')
        e[0] = str(c)
        d[5] = ':'.join(e)
        y = ','.join(d)
        z.append(generate_new_hitobject_line(y, 1, 200))
        return z