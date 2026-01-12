import global_config as gc


def is_validate_header(file_path): 
    first_line = read_first_line(file_path)
    cleaned_line = clean_line(first_line)
    if(
        first_line and \
        (cleaned_line == "osufileformatv14" or cleaned_line == "osufileformatv12")
    ):
        return True
    else:
        return False    
        
        
def is_7k(file_path):
    with open(file_path, "r", encoding = "utf-8") as f:
        is_mania = False
        for line in f:
            cleaned_line = clean_line(line)
            if cleaned_line == "Mode:3":
                is_mania = True
            elif is_mania and cleaned_line == "CircleSize:7":
                return True
            elif cleaned_line.startswith("CircleSize:") and cleaned_line != "CircleSize:7":
                return False     
        return False       
        

def read_lines(file_path):
    with open(file_path, "r", encoding = "utf-8") as f:
        lines = []
        for line in f:
            lines.append(line.rstrip())
        return lines
        
        
def modify_metadata_block(metadata_lines):
    new_lines = []
    for line in metadata_lines:
        if line.startswith("Version:"):
            new_lines.append(f"{line}_7to6")
        # elif line.startswith("BeatmapID:"):
        #     new_lines.append("BeatmapID:9876543210")
        else:
            new_lines.append(line)
    return new_lines                                 


def modify_difficulty_block(difficulty_lines):
    new_lines = []
    for line in difficulty_lines:
        if clean_line(line) == "CircleSize:7":
            new_lines.append("CircleSize:6")
        else:
            new_lines.append(line)
    return new_lines


def read_first_line(file_path):
    with open(file_path, "r", encoding = "utf-8") as f:
        first_line = f.readline().rstrip()
        return first_line


def get_hit_info(line):
    parts = line.split(",")
    x = int(parts[0])
    time = int(parts[2])
    type_value = int(parts[3])
    is_hold = (type_value == 128)
    end_time = time
    
    if is_hold:
        extras = parts[5].split(":")
        end_time = int(extras[0])
        
    return {
        "x": x,
        "time": time,
        "end_time": end_time,
        "is_hold": is_hold,
        "original_line": line
    }    
    
    
def x_to_track(x):
    return x * 7 // 512
    
    
def create_track_bitmaps(track_data, max_time):
    bitmap_length = max_time + 1
    track_bitmaps = [bytearray(bitmap_length) for _ in range(7)]
    
    for track_idx, hitobjects in track_data.items():
        for hitobject in hitobjects:
            if hitobject["is_hold"]:
                track_bitmaps[track_idx][hitobject["start"]] = 25
                for t in range(hitobject["start"] + 1, hitobject["end"] + 1):
                    track_bitmaps[track_idx][t] = 5
            else:
                track_bitmaps[track_idx][hitobject["start"]] = 20                
    return track_bitmaps 
    
    
def create_time_list(track_data):
    time_list = []
    for track_idx, hitobjects in track_data.items():
        for hitobject in hitobjects:
            time_list.append(hitobject["start"])
    return sorted(set(time_list))
    
    
def change_track_num(track_idx):
    if track_idx in (0, 1, 2):
        return track_idx
    elif track_idx in (4, 5, 6):
        return track_idx - 1
    else:
        return 10086


def generate_new_hitobject_line_1(original_line, new_x):
    parts = original_line.split(",")
    parts[0] = str(new_x)
    return ",".join(parts)


def get_key_num(track_bitmaps, time):
    key_num = 0
    for track_idx in range(7):
        if track_bitmaps[track_idx][time] == 20 or track_bitmaps[track_idx][time] == 25:
            key_num += 1
    return key_num
    
    
def is_movable(time, target_track_bitmap):
    for t in range(time - gc.MIN_GAP + 1, time + 1):
        if t < 0:
            continue
        elif target_track_bitmap[t] == 5:
            return False
    for t in range(time - gc.MIN_GAP_2 + 1, time + gc.MIN_GAP_2):
        if t < 0 or t > len(target_track_bitmap) - 1:
            continue
        elif target_track_bitmap[t] == 25 or target_track_bitmap[t] == 20:
            return False
    return True
    
    
def is_qie_a(track_bitmaps, time, target_track, time_list):
    pre_time, next_time = get_pre_next_time(time, time_list)
    f1 = f2 = True
    if pre_time and track_bitmaps[target_track][pre_time] >= 20:
        f1 = False
    if next_time and track_bitmaps[target_track][next_time] >= 20:
        f2 = False
    return f1 and f2
    
    
def get_track_next_time(target_track_bitmap, time):
    bitmap_length = len(target_track_bitmap)
    for t in range(time + 1, bitmap_length):
        if target_track_bitmap[t] >= 20:
            return t
    return bitmap_length - 1 + gc.MIN_GAP
    
    
def generate_new_hitobject_line_2(original_line, new_x, time_list):
    parts = original_line.split(",")
    parts[0] = str(new_x)
    if int(parts[2]) == time_list[0]:
        parts[3] = "5"
    else:
        parts[3] = "1"
    extras = parts[5].split(":")
    parts[5] = ":".join(extras[1:])
    return ",".join(parts)
    
    
def generate_new_hitobject_line_3(original_line, new_x, new_end):
    parts = original_line.split(",")
    parts[0] = str(new_x)
    extras = parts[5].split(":")
    extras[0] = str(new_end)
    parts[5] = ":".join(extras)
    return ",".join(parts)
    
    
def clean_line(line):
    return line.replace(" ", "").replace("\n", "").replace("\r", "").replace("\ufeff", "")
    
    
def get_pre_next_time(time, time_list):
    pre_time = next_time = None
    index = binary_search(time_list, time)
    if index > 0:
        pre_time = time_list[index - 1]
    if index < len(time_list) - 1:
        next_time = time_list[index + 1]
    return pre_time, next_time
    
    
def binary_search(seq, num):
    left = 0
    right = len(seq) - 1
    while left <= right:
        mid = (left + right) // 2
        if seq[mid] == num:
            return mid
        elif seq[mid] < num:
            left = mid + 1
        else:
            right = mid - 1
    return -1                                    
    
    
