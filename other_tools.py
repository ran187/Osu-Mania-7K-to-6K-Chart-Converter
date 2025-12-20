"""
一些泛用函数
"""


def clean_for_match(line): 
    """
    清理字符串 (移除空格和换行符) , 用于格式匹配  
    line: 原始字符串  
    """
    return line.replace(" ", "").replace("\n", "").replace("\r", "")


def binary_search(seq, num):
    """
    一个二分查找函数, 返回数字在序列中的位置  
    seq: 升序序列  
    num: 要查找的目标数  
    """
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