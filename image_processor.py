# -*- coding: utf-8 -*-
"""
Image processing utilities for OCR image generation
Contains functions for horizontal and vertical text image generation
"""
import cv2
import numpy as np
import random
from PIL import Image, ImageDraw, ImageFont

from color_utils import get_bestcolor
from font_utils import word_in_font
from text_generator import get_chars


def get_horizontal_text_picture(image_file, color_lib, char_lines, fonts_list, font_unsupport_chars, cf):
    """获得水平文本图片"""
    retry = 0
    img = Image.open(image_file)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    w, h = img.size
    
    # 随机加入空格
    rd = random.random()
    if rd < 0.3: 
        while True:              
            width = 0
            height = 0
            chars_size = []
            y_offset = 10 ** 5    
            
            # 随机获得不定长的文字
            chars = get_chars(char_lines)

            # 随机选择一种字体
            font_path = random.choice(fonts_list)
            font_size = random.randint(cf.font_min_size, cf.font_max_size)
            
            # 获得字体，及其大小
            font = ImageFont.truetype(font_path, font_size) 
            # 不支持的字体文字，按照字体路径在该字典里索引即可        
            unsupport_chars = font_unsupport_chars[font_path]   
                                      
            for c in chars:
                size = font.getsize(c)
                chars_size.append(size)
                width += size[0]
                
                # set max char height as word height
                if size[1] > height:
                    height = size[1]
    
                # Min chars y offset as word y offset
                # Assume only y offset
                c_offset = font.getoffset(c)
                if c_offset[1] < y_offset:
                    y_offset = c_offset[1]    
                    
            char_space_width = int(height * np.random.uniform(-0.1, 0.3))
    
            width += (char_space_width * (len(chars) - 1))            
            
            f_w, f_h = width, height
            
            if f_w < w:
                # 完美分割时应该取的
                x1 = random.randint(0, w - f_w)
                y1 = random.randint(0, h - f_h)
                x2 = x1 + f_w
                y2 = y1 + f_h
                
                # 加一点偏移
                if cf.random_offset:
                    print('cf.random_offset', cf.random_offset)
                    # 随机加一点偏移，且随机偏移的概率占30%                
                    rd = random.random()                    
                    if rd < 0.3:  # 设定偏移的概率
                        # 分支1：带字符间距的水平文本，需要更多空间适应字符间距变化
                        crop_y1 = y1 - random.random() / 12 * f_h
                        crop_x1 = x1 - random.random() / 8 * f_h
                        crop_y2 = y2 + random.random() / 12 * f_h
                        crop_x2 = x2 + random.random() / 8 * f_h
                        crop_y1 = int(max(0, crop_y1))
                        crop_x1 = int(max(0, crop_x1))
                        crop_y2 = int(min(h, crop_y2))
                        crop_x2 = int(min(w, crop_x2))
                    else:
                        crop_y1 = y1
                        crop_x1 = x1
                        crop_y2 = y2
                        crop_x2 = x2
                else:
                    crop_y1 = y1
                    crop_x1 = x1
                    crop_y2 = y2
                    crop_x2 = x2                
                
                crop_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                crop_lab = cv2.cvtColor(np.asarray(crop_img), cv2.COLOR_RGB2Lab)
           
                all_in_fonts = word_in_font(chars, unsupport_chars, font_path)
                if (np.linalg.norm(np.reshape(np.asarray(crop_lab), (-1, 3)).std(axis=0)) > 55 or all_in_fonts) and retry < 30:  # 颜色标准差阈值，颜色太丰富就不要了
                    retry = retry + 1                               
                    continue
                if not cf.customize_color:
                    best_color = get_bestcolor(color_lib, crop_lab)
                else:    
                    r = random.choice([7, 9, 11, 14, 13, 15, 17, 20, 22, 50, 100])
                    g = random.choice([8, 10, 12, 14, 21, 22, 24, 23, 50, 100])
                    b = random.choice([6, 8, 9, 10, 11, 30, 21, 34, 56, 100])
                    best_color = (r, g, b)                
                break
            else:
                pass  
                
        draw = ImageDraw.Draw(img)    
        for i, c in enumerate(chars):
            draw.text((x1, y1), c, best_color, font=font)
            x1 += (chars_size[i][0] + char_space_width)    
        crop_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        return crop_img, chars, font_path 
   
    else:
        while True:            
            # 随机获得不定长的文字
            chars = get_chars(char_lines)
        
            # 随机选择一种字体
            font_path = random.choice(fonts_list)
            font_size = random.randint(cf.font_min_size, cf.font_max_size)
            
            # 获得字体，及其大小
            font = ImageFont.truetype(font_path, font_size) 
            # 不支持的字体文字，按照字体路径在该字典里索引即可    
            unsupport_chars = font_unsupport_chars[font_path]  
            f_w, f_h = font.getsize(chars)
            
            if f_w < w:
                # 完美分割时应该取的
                x1 = random.randint(0, w - f_w)
                y1 = random.randint(0, h - f_h)
                x2 = x1 + f_w
                y2 = y1 + f_h
                                
                # 加一点偏移
                if cf.random_offset:                
                    # 随机加一点偏移，且随机偏移的概率占30%                
                    rd = random.random()
                    if rd < 0.3:  # 设定偏移的概率
                        # 分支2：整体水平文本，可以更紧凑
                        crop_y1 = y1 - random.random() / 25 * f_h
                        crop_x1 = x1 - random.random() / 20 * f_h
                        crop_y2 = y2 + random.random() / 25 * f_h
                        crop_x2 = x2 + random.random() / 20 * f_h
                        crop_y1 = int(max(0, crop_y1))
                        crop_x1 = int(max(0, crop_x1))
                        crop_y2 = int(min(h, crop_y2))
                        crop_x2 = int(min(w, crop_x2))
                    else:
                        crop_y1 = y1
                        crop_x1 = x1
                        crop_y2 = y2
                        crop_x2 = x2
                else:
                    crop_y1 = y1
                    crop_x1 = x1
                    crop_y2 = y2
                    crop_x2 = x2    
    
                crop_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                crop_lab = cv2.cvtColor(np.asarray(crop_img), cv2.COLOR_RGB2Lab)
                
                # 判断语料中每个字是否在字体文件中
                all_in_fonts = word_in_font(chars, unsupport_chars, font_path)
                if (np.linalg.norm(np.reshape(np.asarray(crop_lab), (-1, 3)).std(axis=0)) > 55 or all_in_fonts) and retry < 30:  # 颜色标准差阈值，颜色太丰富就不要了,单词不在字体文件中不要
                    retry = retry + 1                               
                    print('retry', retry)
                    continue
                if not cf.customize_color:    
                    best_color = get_bestcolor(color_lib, crop_lab)
                
                # 可以自定义字体颜色
                else:
                    r = random.choice([7, 9, 11, 14, 13, 15, 17, 20, 22, 50, 100])
                    g = random.choice([8, 10, 12, 14, 21, 22, 24, 23, 50, 100])
                    b = random.choice([6, 8, 9, 10, 11, 30, 21, 34, 56, 100])
                    best_color = (r, g, b)
                break
            else:
                pass
    
        draw = ImageDraw.Draw(img)
        draw.text((x1, y1), chars, best_color, font=font)
        crop_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                
        return crop_img, chars, font_path


def get_vertical_text_picture(image_file, color_lib, char_lines, fonts_list, font_unsupport_chars, cf):
    """获得垂直文本图片"""
    img = Image.open(image_file)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    w, h = img.size
    retry = 0
    while True:
                
        # 随机获得不定长的文字
        chars = get_chars(char_lines)
        
        # 随机选择一种字体
        font_path = random.choice(fonts_list)
        font_size = random.randint(cf.font_min_size, cf.font_max_size)
        
        # 获得字体，及其大小
        font = ImageFont.truetype(font_path, font_size) 
        # 不支持的字体文字，按照字体路径在该字典里索引即可    
        unsupport_chars = font_unsupport_chars[font_path]  
        
        ch_w = []
        ch_h = []
        for ch in chars:
            wt, ht = font.getsize(ch)
            ch_w.append(wt)
            ch_h.append(ht)
        f_w = max(ch_w)
        f_h = sum(ch_h)
        # 完美分割时应该取的,也即文本位置
        if h > f_h:
            x1 = random.randint(0, w - f_w)
            y1 = random.randint(0, h - f_h)
            x2 = x1 + f_w
            y2 = y1 + f_h            
                      
            if cf.random_offset:                
                # 随机加一点偏移，且随机偏移的概率占30%                
                rd = random.random()
                if rd < 0.3:  # 设定偏移的概率
                    # 分支3：垂直文本，垂直方向需要更多空间，水平方向可以紧凑
                    crop_y1 = y1 - random.random() / 15 * f_h
                    crop_x1 = x1 - random.random() / 25 * f_h
                    crop_y2 = y2 + random.random() / 15 * f_h
                    crop_x2 = x2 + random.random() / 25 * f_h
                    crop_y1 = int(max(0, crop_y1))
                    crop_x1 = int(max(0, crop_x1))
                    crop_y2 = int(min(h, crop_y2))
                    crop_x2 = int(min(w, crop_x2))
                else:
                    crop_y1 = y1
                    crop_x1 = x1
                    crop_y2 = y2
                    crop_x2 = x2
            else:
                crop_y1 = y1
                crop_x1 = x1
                crop_y2 = y2
                crop_x2 = x2               
                                               
            crop_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            crop_lab = cv2.cvtColor(np.asarray(crop_img), cv2.COLOR_RGB2Lab)
            
            all_in_fonts = word_in_font(chars, unsupport_chars, font_path)
            if (np.linalg.norm(np.reshape(np.asarray(crop_lab), (-1, 3)).std(axis=0)) > 55 or all_in_fonts) and retry < 30:  # 颜色标准差阈值，颜色太丰富就不要了
                retry = retry + 1
                continue
            if not cf.customize_color:
                best_color = get_bestcolor(color_lib, crop_lab)
            else:
                r = random.choice([7, 9, 11, 14, 13, 15, 17, 20, 22, 50, 100])
                g = random.choice([8, 10, 12, 14, 21, 22, 24, 23, 50, 100])
                b = random.choice([6, 8, 9, 10, 11, 30, 21, 34, 56, 100])
                best_color = (r, g, b)                
            break
        else:
            pass

    draw = ImageDraw.Draw(img)
    i = 0
    for ch in chars:
        draw.text((x1, y1), ch, best_color, font=font)
        y1 = y1 + ch_h[i]
        i = i + 1

    crop_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    crop_img = crop_img.transpose(Image.ROTATE_90)
    return crop_img, chars, font_path
