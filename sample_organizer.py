# -*- coding: utf-8 -*-
"""
Sample organization utilities for OCR image generation
Contains functions for organizing samples by font, direction, and text color
"""
import os
import cv2
import numpy as np
from PIL import Image


def get_font_name(font_path):
    """从字体路径提取字体名称"""
    font_name = os.path.basename(font_path)
    # 移除文件扩展名
    font_name = os.path.splitext(font_name)[0]
    # 清理特殊字符，用于文件夹名
    font_name = font_name.replace(' ', '_').replace('(', '').replace(')', '')
    return font_name


def analyze_text_color(image):
    """分析图像确定是黑底白字还是白底黑字
    Returns: 'black_on_white' 或 'white_on_black'
    """
    # 转换为灰度图
    if isinstance(image, Image.Image):
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # 计算图像的平均亮度
    mean_brightness = np.mean(gray)
    
    # 使用Otsu阈值分割来分离前景和背景
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 计算白色像素的比例
    white_ratio = np.sum(binary == 255) / binary.size
    
    # 如果白色像素占多数，则认为是黑字白底
    if white_ratio > 0.5:
        return 'black_on_white'
    else:
        return 'white_on_black'


def get_text_direction(is_vertical, rotation=0):
    """确定文本方向
    Args:
        is_vertical: 是否为垂直文本
        rotation: 旋转角度（对于垂直文本）
    Returns: 'horizontal', 'vertical_up', 'vertical_down', 'left', 'right'
    """
    if not is_vertical:
        return 'horizontal'
    else:
        # 垂直文本默认为从上到下
        return 'vertical_down'


def create_sample_directory(output_dir, font_name, direction, color_type):
    """创建样本存储目录结构
    目录结构: output_dir/font_name/direction/color_type/
    """
    sample_dir = os.path.join(output_dir, font_name, direction, color_type)
    os.makedirs(sample_dir, exist_ok=True)
    return sample_dir


def get_sample_info(image, font_path, is_vertical=False):
    """获取样本的完整信息
    Returns: dict with font_name, direction, color_type, sample_dir
    """
    font_name = get_font_name(font_path)
    direction = get_text_direction(is_vertical)
    color_type = analyze_text_color(image)
    
    return {
        'font_name': font_name,
        'direction': direction,
        'color_type': color_type
    }


def save_organized_sample(image, chars, output_dir, font_path, is_vertical, img_index):
    """保存组织化的样本到对应子文件夹
    Returns: 保存的文件路径
    """
    # 获取样本信息
    sample_info = get_sample_info(image, font_path, is_vertical)
    
    # 创建目录
    sample_dir = create_sample_directory(
        output_dir, 
        sample_info['font_name'], 
        sample_info['direction'], 
        sample_info['color_type']
    )
    
    # 生成文件名
    filename = f"img_{img_index:07d}_{chars}.jpg"
    filepath = os.path.join(sample_dir, filename)
    
    # 保存图像
    if isinstance(image, Image.Image):
        image.save(filepath)
    else:
        cv2.imwrite(filepath, image)
    
    return filepath, sample_info
