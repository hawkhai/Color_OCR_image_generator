# -*- coding: utf-8 -*-
"""
Text generation utilities for OCR image generation
Contains functions for generating text content and corpus handling
"""
import os
import random


def get_char_lines(txt_root_path):
    """从文本文件中读取字符行"""
    txt_files = os.listdir(txt_root_path) 
    char_lines = []
    for txt in txt_files:
        f = open(os.path.join(txt_root_path, txt), mode='r', encoding='utf-8')
        lines = f.readlines()
        f.close()
        for line in lines:
            char_lines.append(line.strip().replace('\xef\xbb\xbf', '').replace('\ufeff', ''))
        return char_lines


def get_chars(char_lines):
    """获取随机字符串"""
    while True:
        char_line = random.choice(char_lines)
        if len(char_line) > 0:
            break
    line_len = len(char_line)         
    char_len = random.randint(1, 20)  #  4
    if line_len <= char_len:
        return char_line
    char_start = random.randint(0, line_len - char_len)
    chars = char_line[char_start:(char_start + char_len)]
    return chars
