import tkinter as tk
from tkinter import filedialog
import os
import zipfile
import shutil
import global_config as gc
import process_osu as po


def create_main_window():
    root = tk.Tk()
    root.title("OSU!MANIA 7 to 6")
    root.geometry("320*240")
    only_keep_6k = tk.BooleanVar(value = True)
    
    def on_button_click():
        file_path = filedialog.askopenfilename(
            initialdir = os.path.expanduser(gc.DOWNLOADS_PATH),
            title = "选择文件",
            filetypes = ((".osz", "*.osz"),)
        )
        
        if file_path:
            file_name = os.path.basename(file_path)
            print(f"\n========== 开始处理: {file_name} ==========")
            process_osz(file_path, only_keep_6k.get())
            print("========== 处理结束 ==========\n")
            
    tk.Button(
        root,
        text = "选择文件 (默认路径: 下载)",
        command = on_button_click
    ).pack(pady = 60)
    
    tk.Checkbutton(
        root,
        text = "仅保留转换后的谱面",
        variable = only_keep_6k
    ).pack(pady = 0)
    
    root.mainloop()


def process_osz(file_path, only_keep_6k):
    file_name = os.path.basename(file_path)
    name_without_ext, ext = os.path.splitext(file_name)
    output_path = os.path.join(os.path.expanduser(gc.DESKTOP_PATH), f"{name_without_ext}_7to6{ext}")
    temp_dir = os.path.join(os.path.expanduser(gc.DESKTOP_PATH), "temp_osu")
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    with zipfile.ZipFile(file_path, "r") as zip_f:
        zip_f.extractall(temp_dir)
    print("  已解压 osz 文件到临时目录")
    
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".osu"):
                po.process_osu(os.path.join(root, file))
                if only_keep_6k:
                    os.remove(os.path.join(root, file))

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_f:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path2 = os.path.join(root, file)
                arcname = os.path.relpath(file_path2, temp_dir)
                zip_f.write(file_path2, arcname)
    print(f"  处理后的所有谱面已保存至 {output_path}")
    
    shutil.rmtree(temp_dir)
    print("  临时目录已删除")
    
    
if __name__ == "__main__":
    create_main_window()
