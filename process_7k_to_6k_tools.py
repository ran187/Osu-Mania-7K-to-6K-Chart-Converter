"""
process_osu_tools.py中用到的函数
"""


import global_config
import process_hitobjects_block_tools as prh


def process_metadata_block(metadata_lines): 
    """
    修改[Metadata]下的内容 (从osu_dict中读取)  
    metadata_lines: 列表  
    """
    new_lines = []
    for line in metadata_lines:
        if line.startswith('Version:'):
            new_lines.append(f"{line}_7to6")  
        else:
            new_lines.append(line)
    return new_lines



def process_difficulty_block(difficulty_lines): 
    """
    修改[Difficulty]下的内容 (从osu_dict中读取)  
    difficulty_lines: 列表
    """
    new_lines = []
    for line in difficulty_lines:
        if line.startswith('CircleSize:') and line.strip() == 'CircleSize:7':
            new_lines.append('CircleSize:6')  
        else:
            new_lines.append(line)
    return new_lines


def process_hitobjects_block(hitobjects_lines): 
    """
    修改[HitObjects]下的内容 (从osu_dict中读取)  
    hitobjects_lines: 列表
    """
    track_data = {i: [] for i in range(7)}
    global_max_time = 0  
    for line in hitobjects_lines:
        hit_info = prh.parse_hitobject_line(line)
        if hit_info is None:
            continue
        track_idx = prh.x_to_track(hit_info['x'])
        interval = {
            'start': hit_info['time'],
            'end': hit_info['end_time'],
            'original_line': hit_info['original_line'],
            'original_x': hit_info['x'],
            'is_hold': hit_info['is_hold']
        }
        track_data[track_idx].append(interval)
        global_max_time = max(global_max_time, interval['end'])

    track_bitmaps = prh.create_track_bitmaps(track_data, global_max_time)

    key_shapes = prh.create_key_shapes(track_data)

    # 定义一个函数, 使7k的012轨道映射到6k的012轨道, 7k的456轨道映射到6k的345轨道
    def change_track_num(track_index): 
        if track_index in (0, 1, 2):
            return track_index
        elif track_index in (4, 5, 6):
            return track_index - 1
        
    new_hit_lines = []
    for track_index in range(0, 7):
        if track_index != 3:
            for interval in track_data[track_index]:
                sixk_track_idx = change_track_num(track_index)
                min_x, max_x = global_config.TRACK_RANGES_6[sixk_track_idx]
                new_x = (min_x + max_x) // 2 
                new_line = prh.generate_new_hitobject_line(
                    interval['original_line'], 1, new_x
                )
                new_hit_lines.append(new_line)
    
    # 转移7k的中间轨 (3号轨) 的策略
    for interval in track_data[3]:
        saj = prh.trans_4th_track(key_shapes, track_bitmaps, interval)
        if saj:
            # print(saj)
            new_hit_lines.extend(saj)        
  
    # 定义一个函数用于获取排序键, (元组的第一个元素，即时间)
    def get_time(item):
        return item[0]
    
    hit_with_time = []
    for line in new_hit_lines:
        info = prh.parse_hitobject_line(line)
        if info:
            hit_with_time.append((info['time'], line))
    hit_with_time.sort(key=get_time)
    return [line for (time, line) in hit_with_time]