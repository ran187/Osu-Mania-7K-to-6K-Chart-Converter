"""
main.py中函数process_osu_tool用到的函数 
"""


import parse_osu_file_tools as pat
import process_7k_to_6k_tools as pt7


def parse_osu_file(file_path): 
    """
    解析osu文件, 分为/校验版本\判断是否为7k谱\读取文件内容\文件内容解析到数据结构中  
    file_path:文件路径  
    """
    if not pat.validate_osu_header(file_path):
        print("不支持的osu文件版本")
        return None, None

    if not pat.check_is_7k(file_path):
        print("osu文件不是7k谱面")
        return None, None

    lines = pat.read_osu_file_lines(file_path)
    if not lines:
        return None, None    

    osu_dict, blocks_order = pat.parse_osu_blocks(lines)

    return osu_dict, blocks_order


def process_7k_to_6k(osu_dict): 
    """
    7k到6k谱的转换过程, 分为/修改[Metadata]\修改[Difficulty]\修改[HitObjects]  
    osu_dict: 字典, 保存文件内容, 可以由parse_osu_file函数得到  
    """
    if '[Metadata]' in osu_dict: 
        osu_dict['[Metadata]'] = pt7.process_metadata_block(osu_dict['[Metadata]'])
    
    if '[Difficulty]' in osu_dict:
        osu_dict['[Difficulty]'] = pt7.process_difficulty_block(osu_dict['[Difficulty]'])
    
    if '[HitObjects]' in osu_dict:
        osu_dict['[HitObjects]'] = pt7.process_hitobjects_block(osu_dict['[HitObjects]']) 
    
    return osu_dict


def write_osu_file(osu_dict, blocks_order, output_path): 
    """
    将修改后的内容写入新的osu文件  
    osu_dict: 字典, 保存修改后的文件内容, 可由process_7k_to_6k函数得到  
    blocks_order: 列表, 保存文件内容的顺序, 按顺序写入文件  
    output_path: 写入文件的路径  
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("osu file format v14\n\n")
        for block in blocks_order:
            f.write(f"{block}\n")
            for line in osu_dict.get(block, []):
                f.write(f"{line}\n")
            f.write("\n")
        print(f"处理后的osu文件已保存至 {output_path}")
