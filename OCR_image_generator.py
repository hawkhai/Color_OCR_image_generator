# -*- coding: utf-8 -*-
"""
OCR Image Generator - Organized Sample Version
Generates 1-2 character samples organized by font, direction, and text color
"""
import os
import random
import time
import argparse
import numpy as np
from PIL import Image

# Import custom modules
from color_utils import FontColor
from font_utils import get_fonts, get_unsupported_chars
from text_generator import get_char_lines
from image_processor import get_horizontal_text_picture, get_vertical_text_picture
from sample_organizer import save_organized_sample

# Import existing modules
from tools.config import load_config
from noiser import Noiser
from tools.utils import apply
from data_aug import apply_blur_on_output, apply_prydown, apply_lr_motion, apply_up_motion


def main():
    """主函数 - 生成组织化的样本"""
    parser = argparse.ArgumentParser()
        
    parser.add_argument('--num_img', type=int, default=100, help="Number of images to generate")
    
    parser.add_argument('--font_min_size', type=int, default=12)
    parser.add_argument('--font_max_size', type=int, default=70,
                        help="Can help adjust the size of the generated text and the size of the picture")
    
    parser.add_argument('--bg_path', type=str, default='./background',
                        help='The generated text pictures will use the pictures of this folder as the background')
                        
    parser.add_argument('--fonts_path', type=str, default='./fonts',
                        help='The font used to generate the picture')
    
    parser.add_argument('--corpus_path', type=str, default='./corpus', 
                        help='The corpus used to generate the text picture')
    
    parser.add_argument('--color_path', type=str, default='./models/colors_new.cp', 
                        help='Color font library used to generate text')
    
    parser.add_argument('--chars_file', type=str, default='dict5990.txt',
                        help='Chars allowed to be appear in generated images')

    parser.add_argument('--customize_color', action='store_true', help='Support font custom color')
    
    parser.add_argument('--blur', action='store_true', default=False,
                        help="Apply gauss blur to the generated image")    
    
    parser.add_argument('--prydown', action='store_true', default=False,
                    help="Blurred image, simulating the effect of enlargement of small pictures")

    parser.add_argument('--lr_motion', action='store_true', default=False,
                    help="Apply left and right motion blur")
                    
    parser.add_argument('--ud_motion', action='store_true', default=False,
                    help="Apply up and down motion blur")                    
    
    parser.add_argument('--random_offset', action='store_true', default=True,
                help="Randomly add offset") 
    
    parser.add_argument('--config_file', type=str, default='noise.yaml',
                    help='Set the parameters when rendering images')
      
    parser.add_argument('--output_dir', type=str, default='./organized_output/', help='Images save dir')

    cf = parser.parse_args()
    
    print('cf.config_file', cf.config_file)
    flag = load_config(cf.config_file) 
    
    # 实例化噪音参数
    noiser = Noiser(flag) 
    
    # 读入字体色彩库
    color_lib = FontColor(cf.color_path)
    print('color_lib loaded successfully')
    
    # 读入字体
    fonts_path = cf.fonts_path
    fonts_list = get_fonts(fonts_path)
    print(f'Loaded {len(fonts_list)} fonts')

    # 读入语料库
    txt_root_path = cf.corpus_path
    char_lines = get_char_lines(txt_root_path=txt_root_path)     
    print(f'Loaded {len(char_lines)} text lines')

    # 读入背景图片
    img_root_path = cf.bg_path
    imnames = os.listdir(img_root_path)
    print(f'Loaded {len(imnames)} background images')
    
    # 创建输出目录
    os.makedirs(cf.output_dir, exist_ok=True)
    
    # 处理标签文件
    labels_path = os.path.join(cf.output_dir, 'labels.txt')
    gs = 0
    if os.path.exists(labels_path):  # 支持中断程序后，在生成的图片基础上继续
        with open(labels_path, 'r', encoding='utf-8') as f:
            lines = list(f.readlines())
        if lines:
            gs = int(lines[-1].strip().split('\t')[0])
            print('Resume generating from step %d' % gs)
        
    # 字典文件    
    chars_file = cf.chars_file
    font_unsupport_chars = get_unsupported_chars(fonts_list, chars_file)
    
    # 开始生成图片
    print('Start generating organized samples...')
    t0 = time.time()
    
    # 统计信息
    stats = {
        'total': 0,
        'horizontal': 0,
        'vertical': 0,
        'black_on_white': 0,
        'white_on_black': 0,
        'fonts': set()
    }
    
    with open(labels_path, 'a', encoding='utf-8') as f:
        for i in range(gs + 1, gs + cf.num_img + 1):
            try:
                # 随机选择背景图片
                imname = random.choice(imnames)
                img_path = os.path.join(img_root_path, imname)

                # 随机决定水平或垂直文本
                rnd = random.random()
                is_vertical = rnd >= 0.8  # 20%概率生成垂直文本
                
                if not is_vertical:  # 水平文本
                    gen_img, chars, font_path = get_horizontal_text_picture(
                        img_path, color_lib, char_lines, fonts_list, font_unsupport_chars, cf
                    )
                    stats['horizontal'] += 1
                else:  # 垂直文本
                    gen_img, chars, font_path = get_vertical_text_picture(
                        img_path, color_lib, char_lines, fonts_list, font_unsupport_chars, cf
                    )
                    stats['vertical'] += 1
                
                if gen_img.mode != 'RGB':
                    gen_img = gen_img.convert('RGB')           
                
                # 应用各种图像增强效果
                if cf.blur:
                    image_arr = np.array(gen_img) 
                    gen_img = apply_blur_on_output(image_arr)            
                    gen_img = Image.fromarray(np.uint8(gen_img))
                    
                if cf.prydown:
                    image_arr = np.array(gen_img) 
                    gen_img = apply_prydown(image_arr)
                    gen_img = Image.fromarray(np.uint8(gen_img))
                    
                if cf.lr_motion:
                    image_arr = np.array(gen_img)
                    gen_img = apply_lr_motion(image_arr)
                    gen_img = Image.fromarray(np.uint8(gen_img))       
                    
                if cf.ud_motion:
                    image_arr = np.array(gen_img)
                    gen_img = apply_up_motion(image_arr)        
                    gen_img = Image.fromarray(np.uint8(gen_img)) 

                if apply(flag.noise):
                    gen_img = np.clip(gen_img, 0., 255.)
                    gen_img = noiser.apply(gen_img)
                    gen_img = Image.fromarray(np.uint8(gen_img))
                
                # 保存组织化的样本
                filepath, sample_info = save_organized_sample(
                    gen_img, chars, cf.output_dir, font_path, is_vertical, i
                )
                
                # 更新统计信息
                stats['total'] += 1
                stats['fonts'].add(sample_info['font_name'])
                if sample_info['color_type'] == 'black_on_white':
                    stats['black_on_white'] += 1
                else:
                    stats['white_on_black'] += 1
                
                # 写入标签文件
                relative_path = os.path.relpath(filepath, cf.output_dir)
                f.write(f"{i}\t{relative_path}\t{chars}\t{sample_info['font_name']}\t{sample_info['direction']}\t{sample_info['color_type']}\n")
                
                print(f'Generated: {i:04d} - {chars} - {sample_info["font_name"]} - {sample_info["direction"]} - {sample_info["color_type"]}')
                
            except Exception as e:
                print(f'Error generating sample {i}: {e}')
                continue
        
    t1 = time.time()
    
    # 打印统计信息
    print('\n=== Generation Complete ===')
    print(f'Total time: {t1 - t0:.2f} seconds')
    print(f'Total samples: {stats["total"]}')
    print(f'Horizontal: {stats["horizontal"]}')
    print(f'Vertical: {stats["vertical"]}')
    print(f'Black on white: {stats["black_on_white"]}')
    print(f'White on black: {stats["white_on_black"]}')
    print(f'Fonts used: {len(stats["fonts"])}')
    print(f'Font names: {", ".join(sorted(stats["fonts"]))}')


if __name__ == '__main__':
    main()
