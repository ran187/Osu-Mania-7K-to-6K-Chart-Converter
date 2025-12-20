"""
o!m 7k谱转6k谱
"""


import tkinter as tk
from tkinter import filedialog
import os
import zipfile
import shutil
import process_osu_tools as pro
import global_config


def create_main_windows():  
    """
    创建使用界面  
    """
    root = tk.Tk()
    root.title("OSU!MANIA 7 to 6")
    root.geometry("320x240")  
    only_keep_6k = tk.BooleanVar(value=True) 

    def on_button_click():
        file_path = create_file_select_window()
        if file_path:
            process_file(file_path, only_keep_6k.get())

    tk.Button(
        root,
        text="选择文件（默认路径：下载）",
        command=on_button_click
    ).pack(pady=60)

    tk.Checkbutton(
        root,
        text="仅保留转换后的谱面",
        variable=only_keep_6k
    ).pack(pady=0)

    root.mainloop()


def create_file_select_window(): 
    """
    创建选择处理文件的界面, 并返回文件路径  
    """
    file_path = filedialog.askopenfilename(
        initialdir=os.path.expanduser(global_config.DOWNLOADS_PATH),
        title="选择文件",
        filetypes=((".osz", "*.osz"), (".osu", "*.osu"))
    )
    return file_path


def process_file(file_path, only_keep_6k):
    """
    根据文件类型执行不同的处理步骤  
    file_path: 文件路径  
    only_keep_6k: 若为True, 新的文件只会保留6k谱面  
    """
    name_without_ext, ext = os.path.splitext(file_path)

    if ext == ".osu":
        print(f"\n========== 开始处理osu文件 {name_without_ext} ==========)")
        process_osu(file_path)
        print(f"========== osu文件处理结束 ==========\n")
    elif ext == ".osz":
        print(f"\n========== 开始处理osz文件 {name_without_ext} ==========")
        process_osz(file_path, only_keep_6k)
        print(f"========== osz文件处理结束 ==========\n")
    else:
        print(f"不支持的文件类型 {ext}")


def process_osu(file_path, is_belong_osz=False): 
    """
    处理osu文件, 分为/解析原文件\文件转换\写入新文件  
    file_path: 文件路径  
    is_belong_osz: 若为True, 表示处理osz文件时调用该函数, 这会影响最终的写入路径  
    """
    file_dir, file_name = os.path.split(file_path)
    name_without_ext, ext = os.path.splitext(file_name)

    if is_belong_osz:
        output_file_path = os.path.join(file_dir, f"{name_without_ext}_7to6{ext}")
    else:
        output_file_path = os.path.join(os.path.expanduser(global_config.DESKTOP_PATH), f"{name_without_ext}_7to6{ext}")
    
    osu_dict, blocks_order = pro.parse_osu_file(file_path)
    if osu_dict is None or blocks_order is None:
        return 
    
    osu_dict = pro.process_7k_to_6k(osu_dict)

    pro.write_osu_file(osu_dict, blocks_order, output_file_path)


def process_osz(file_path, only_keep_6k): 
    """
    处理osz文件, 分为/解压缩\处理各个osu文件\重新压缩  
    file_path: 文件路径  
    only_keep_6k: 若为True, 新的文件只会保留6k谱面  
    """
    file_name = os.path.basename(file_path)
    name_without_ext, ext = os.path.splitext(file_name)
    output_file_path = os.path.join(os.path.expanduser(global_config.DESKTOP_PATH), f"{name_without_ext}_7to6{ext}")
    temp_dir = os.path.join(os.path.expanduser(global_config.DESKTOP_PATH), "osz_temp_process")

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    print(f"已解压osz文件到临时目录 {temp_dir}")
    
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.osu'):
                process_osu(os.path.join(root, file), True)
                if only_keep_6k:
                    os.remove(os.path.join(root, file))

    with zipfile.ZipFile(output_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path2 = os.path.join(root, file)
                arcname = os.path.relpath(file_path2, temp_dir)
                zip_ref.write(file_path2, arcname)
    print(f"处理后的osz文件已保存至 {output_file_path}")

    shutil.rmtree(temp_dir)
    print(f"临时目录 {temp_dir} 已删除")


if __name__ == "__main__":
    create_main_windows()
    