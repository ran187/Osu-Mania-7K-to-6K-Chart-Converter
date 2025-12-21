"""
process_osu_tools.py中用到的函数 
""" 


import other_tools as ott


def validate_osu_header(file_path): 
    """
    校验文件格式是否为v14或v12版本  
    file_path: 文件路径  
    """
    with open(file_path, 'r',encoding='utf-8') as file:
        for line in file:
            return (ott.clean_for_match(line) == "osufileformatv14" or ott.clean_for_match(line) == "osufileformatv12")
        return False


def check_is_7k(file_path): 
    """
    校验文件是否为7k谱面  
    file_path: 文件路径  
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        in_general = False  
        in_difficulty = False  
        is_mania = False  
        is_7keys = False  
            
        for line in file:
            current_line = line.rstrip('\n\r')            
            if current_line.startswith('[') and current_line.endswith(']'):
                in_general = (current_line == "[General]")
                in_difficulty = (current_line == "[Difficulty]")
                if is_mania and is_7keys:
                    break  
                continue
                
            if in_general and not is_mania:
                is_mania = (ott.clean_for_match(current_line) == "Mode:3")
               
            elif in_difficulty and not is_7keys:
                is_7keys = (ott.clean_for_match(current_line) == "CircleSize:7")
                
            if is_mania and is_7keys:
                break     
        return is_mania and is_7keys
  
    
def read_osu_file_lines(file_path): 
    """
    按行读取文件  
    file_path: 文件路径  
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.rstrip('\n\r') for line in file]


def parse_osu_blocks(lines):
    """
    将读取到的文件行保存在数据结构中  
    lines: 列表, 文件内容按行保存, 可以由read_osu_file_lines函数得到  
    """
    osu_blocks = {}
    blocks_order = []
    current_block = None  
    current_lines = []    
    
    for line in lines:
        if line.startswith('[') and line.endswith(']'):
            if current_block is not None:
                osu_blocks[current_block] = current_lines.copy()
            current_block = line
            blocks_order.append(current_block)
            current_lines = []
        else:
            if current_block is not None and line.strip() != "":
                current_lines.append(line)
    
    if current_block is not None:
        osu_blocks[current_block] = current_lines
    
    return osu_blocks, blocks_order