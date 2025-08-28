# -*- coding: utf-8 -*-
"""
OCR Image Generator - Refactored Main Module
@author: zcswdt
@email: jhsignal@126.com
@file: OCR_image_generator_refactored.py
@time: 2020/06/24
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

# Import existing modules
from tools.config import load_config
from noiser import Noiser
from tools.utils import apply
from data_aug import apply_blur_on_output, apply_prydown, apply_lr_motion, apply_up_motion


def main():
    """主函数"""
    parser = argparse.ArgumentParser()
        
    parser.add_argument('--num_img', type=int, default=30, help="Number of images to generate")
    
    parser.add_argument('--font_min_size', type=int, default=12)
    parser.add_argument('--font_max_size', type=int, default=70,
                        help="Can help adjust the size of the generated text and the size of the picture")
    
    parser.add_argument('--bg_path', type=str, default='./background',
                        help='The generated text pictures will use the pictures of this folder as the background')
                        
    parser.add_argument('--fonts_path', type=str, default='./fonts/chinse_jian',
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
      
    parser.add_argument('--output_dir', type=str, default='./output/', help='Images save dir')

    cf = parser.parse_args()
    
    print('cf.config_file', cf.config_file)
    flag = load_config(cf.config_file) 
    
    # 实例化噪音参数
    noiser = Noiser(flag) 
    
    # 读入字体色彩库
    color_lib = FontColor(cf.color_path)
    print('color_lib', color_lib)
    
    # 读入字体
    fonts_path = cf.fonts_path
    fonts_list = get_fonts(fonts_path)

    # 读入语料库
    txt_root_path = cf.corpus_path
    char_lines = get_char_lines(txt_root_path=txt_root_path)     

    # 读入背景图片
    img_root_path = cf.bg_path
    imnames = os.listdir(img_root_path)
    
    # 处理标签文件
    labels_path = 'labels.txt'
    gs = 0
    if os.path.exists(labels_path):  # 支持中断程序后，在生成的图片基础上继续
        f = open(labels_path, 'r', encoding='utf-8')
        lines = list(f.readlines())
        f.close()
        gs = int(lines[-1].strip().split('.')[0].split('_')[1])
        print('Resume generating from step %d' % gs)
        print('gs', gs)
        
    # 字典文件    
    chars_file = cf.chars_file
    font_unsupport_chars = get_unsupported_chars(fonts_list, chars_file)
    
    # 开始生成图片
    f = open(labels_path, 'a', encoding='utf-8')
    print('start generating...')
    t0 = time.time()
    img_n = 0
    
    for i in range(gs + 1, cf.num_img):
        img_n += 1
        print('img_n', img_n)
        imname = random.choice(imnames)
        img_path = os.path.join(img_root_path, imname)

        rnd = random.random()
        if rnd < 0.8:  # 设定产生水平文本的概率
            gen_img, chars = get_horizontal_text_picture(img_path, color_lib, char_lines, fonts_list, font_unsupport_chars, cf)       
        else:  # 设定产生竖直文本的概率
            gen_img, chars = get_vertical_text_picture(img_path, color_lib, char_lines, fonts_list, font_unsupport_chars, cf)            
        
        save_img_name = 'img_3_' + str(i).zfill(7) + '.jpg'
        
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

        print('gen_img2', gen_img)
    
        if apply(flag.noise):
            gen_img = np.clip(gen_img, 0., 255.)
            gen_img = noiser.apply(gen_img)
            gen_img = Image.fromarray(np.uint8(gen_img))
            print('gen_img1', gen_img)
            
        gen_img.save(cf.output_dir + save_img_name)
        f.write(save_img_name + ' ' + chars + '\n')
        print('gennerating:-------' + save_img_name)
        
    t1 = time.time()
    print('all_time', t1 - t0)
    f.close()


if __name__ == '__main__':
    main()
