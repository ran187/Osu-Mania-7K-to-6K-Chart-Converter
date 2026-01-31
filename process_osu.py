import os 
import ssaj as a
import global_config as gc


def process_osu(file_path):
    if not a.is_validate_header(file_path):
        print("  不支持的谱面版本, 跳过")
        return
    
    if not a.is_7k(file_path):
        print("  不是 7k 谱面, 跳过")
        return
             
    lines = a.read_lines(file_path)
    osu_blocks = {}
    blocks_order = []
    current_block = None
    current_lines = []
    
    for line in lines:
        if line.startswith("[") and line.endswith("]"):
            if current_block:
                osu_blocks[current_block] = current_lines.copy()
            current_block = line
            blocks_order.append(current_block)
            current_lines = []
        else:
            if current_block and line.strip():
                current_lines.append(line)
    if current_block:
        osu_blocks[current_block] = current_lines.copy()
        
    if "[Metadata]" in osu_blocks:
        osu_blocks["[Metadata]"] = a.modify_metadata_block(osu_blocks["[Metadata]"])
        
    if "[Difficulty]" in osu_blocks:
        osu_blocks["[Difficulty]"] = a.modify_difficulty_block(osu_blocks["[Difficulty]"])
        
    if "[HitObjects]" in osu_blocks:
        osu_blocks["[HitObjects]"] = modify_hitobjects_block(osu_blocks["[HitObjects]"])
        
    file_dir, file_name = os.path.split(file_path)
    name_without_ext, ext = os.path.splitext(file_name)
    output_path = os.path.join(file_dir, f"{name_without_ext}_7to6{ext}")
    osu_header = a.read_first_line(file_path)
    
    with open(output_path, "w", encoding = "utf-8") as f:
        f.write(f"{osu_header}\n\n")
        for block in blocks_order:
            f.write(f"{block}\n")
            for line in osu_blocks.get(block, []):
                f.write(f"{line}\n")
            f.write("\n")
    print("  谱面转换完成 +1")            
                
    
def modify_hitobjects_block(hitobjects_lines):
    track_data = {i:[] for i in range(7)}
    max_time = 0
    
    for line in hitobjects_lines:
        hit_info = a.get_hit_info(line)
        track_idx = a.x_to_track(hit_info["x"])
        hitobject = {
            "start": hit_info["time"],
            "end": hit_info["end_time"],
            "original_line": hit_info["original_line"],
            "is_hold": hit_info["is_hold"]
        }                
        track_data[track_idx].append(hitobject)
        max_time = max(max_time, hitobject["end"])

    new_lines = []
    for track_idx, hitobjects in track_data.items():
        if track_idx == 3:
            continue
        for hitobject in hitobjects:
            six_track_num = a.change_track_num(track_idx)
            new_x = 80 * six_track_num + 50
            new_line = a.generate_new_hitobject_line_1(hitobject["original_line"], new_x)
            new_lines.append(new_line)

    track_bitmaps = a.create_track_bitmaps(track_data, max_time)   
    time_list = a.create_time_list(track_data)   
    for hitobject in track_data[3]:
        new_line = trans_4th_track(track_bitmaps, time_list, hitobject)
        if new_line:
            new_lines.append(new_line)
            
    new_lines.sort(key = lambda x: int(x.split(",")[2]))
    return new_lines                        
    
    
def trans_4th_track(track_bitmaps, time_list, hitobject):
    key_num = a.get_key_num(track_bitmaps, hitobject["start"])

    if not hitobject["is_hold"]:
        if key_num in range(2, 8):
            return None
        elif a.is_qie_a(track_bitmaps, hitobject["start"], 3, time_list):
            track_seq = gc.RANDOM_SEQUENCE_6[hitobject["start"] % 6]
            for track_idx in track_seq:
                if(
                    a.is_movable(hitobject["start"], track_bitmaps[track_idx]) and \
                    a.is_qie_a(track_bitmaps, hitobject["start"], track_idx, time_list)
                ):
                    new_track = a.change_track_num(track_idx)
                    new_x = 80 * new_track + 50
                    new_line = a.generate_new_hitobject_line_1(hitobject["original_line"], new_x)
                    return new_line
        else:
            track_seq = gc.RANDOM_SEQUENCE_6[hitobject["start"] % 6]
            for track_idx in track_seq:
                if a.is_movable(hitobject["start"], track_bitmaps[track_idx]):
                    new_track = a.change_track_num(track_idx)
                    new_x = 80 * new_track + 50
                    new_line = a.generate_new_hitobject_line_1(hitobject["original_line"], new_x)
                    return new_line
                
    elif hitobject["is_hold"]:
        if key_num == 1:
            track_seq = gc.RANDOM_SEQUENCE_6[hitobject["start"] % 6]
            for track_idx in track_seq:
                if a.is_movable(hitobject["start"], track_bitmaps[track_idx]):
                    new_track = a.change_track_num(track_idx)
                    new_x = 80 * new_track + 50
                    new_line = a.generate_new_hitobject_line_2(hitobject["original_line"], new_x, time_list)
                    return new_line
                
        #target_track = gc.RANDOM_SEQUENCE_6[hitobject["start"] % 6][0]
        #if a.is_movable(hitobject["start"], track_bitmaps[target_track]):
        #    new_track = a.change_track_num(target_track)
        #    new_x = 80 * new_track + 50
        #    next_time = a.get_track_next_time(track_bitmaps[target_track], hitobject["start"])
        #    if hitobject["start"] >= next_time - gc.MIN_GAP:
        #        new_line = a.generate_new_hitobject_line_2(hitobject["original_line"], new_x, time_list)
        #        return new_line
        #    else:
        #        new_end = min(next_time - gc.MIN_GAP, hitobject["end"])
        #        new_line = a.generate_new_hitobject_line_3(hitobject["original_line"], new_x, new_end)
        #        return new_line
        #else:
        #    return None
