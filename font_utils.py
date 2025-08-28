# -*- coding: utf-8 -*-
"""
Font utilities for OCR image generation
Contains font handling and character support functions
"""
import os
import pickle
import hashlib
from fontTools.ttLib import TTCollection, TTFont


def get_fonts(fonts_path):
    """获取字体文件列表"""
    font_files = os.listdir(fonts_path)
    fonts_list = []
    for font_file in font_files:
        font_path = os.path.join(fonts_path, font_file)
        fonts_list.append(font_path)
    return fonts_list


def chose_font(fonts, font_sizes):
    """选择字体"""
    f_size = random.choice(font_sizes)  # 不满就取最大字号吧
    font = random.choice(fonts[f_size])
    return font


def word_in_font(word, unsupport_chars, font_path):
    """检查单词中的字符是否在字体中支持"""
    for c in word:
        if c in unsupport_chars:
            print('Retry pick_font(), \'%s\' contains chars \'%s\' not supported by font %s' % (word, c, font_path))  
            return True
        else:
            continue


def get_unsupported_chars(fonts, chars_file):
    """
    Get fonts unsupported chars by loads/saves font supported chars from cache file
    :param fonts:
    :param chars_file:
    :return: dict
        key -> font_path
        value -> font unsupported chars
    """
    charset = load_chars(chars_file)
    charset = ''.join(charset)
    fonts_chars = get_fonts_chars(fonts, chars_file)
    fonts_unsupported_chars = {}
    for font_path, chars in fonts_chars.items():
        unsupported_chars = list(filter(lambda x: x not in chars, charset))
        fonts_unsupported_chars[font_path] = unsupported_chars
    return fonts_unsupported_chars


def load_chars(filepath):
    """加载字符文件"""
    if not os.path.exists(filepath):
        print("Chars file not exists.")
        exit(1)

    ret = ''
    with open(filepath, 'r', encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                break
            ret += line[0]
    return ret


def get_fonts_chars(fonts, chars_file):
    """
    loads/saves font supported chars from cache file
    :param fonts: list of font path. e.g ['./data/fonts/msyh.ttc']
    :param chars_file: arg from parse_args
    :return: dict
        key -> font_path
        value -> font supported chars
    """
    out = {}

    cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', '.caches'))
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    chars = load_chars(chars_file)
    chars = ''.join(chars)

    for font_path in fonts:
        string = ''.join([font_path, chars])
        file_md5 = md5(string)

        cache_file_path = os.path.join(cache_dir, file_md5)

        if not os.path.exists(cache_file_path):
            ttf = load_font(font_path)
            _, supported_chars = check_font_chars(ttf, chars)
            print('Save font(%s) supported chars(%d) to cache' % (font_path, len(supported_chars)))

            with open(cache_file_path, 'wb') as f:
                pickle.dump(supported_chars, f, pickle.HIGHEST_PROTOCOL)
        else:
            with open(cache_file_path, 'rb') as f:
                supported_chars = pickle.load(f)
            print('Load font(%s) supported chars(%d) from cache' % (font_path, len(supported_chars)))

        out[font_path] = supported_chars

    return out


def load_font(font_path):
    """
    Read ttc, ttf, otf font file, return a TTFont object
    """

    # ttc is collection of ttf
    if font_path.endswith('ttc'):
        ttc = TTCollection(font_path)
        # assume all ttfs in ttc file have same supported chars
        return ttc.fonts[0]

    if font_path.endswith('ttf') or font_path.endswith('TTF') or font_path.endswith('otf'):
        ttf = TTFont(font_path, 0, allowVID=0,
                     ignoreDecompileErrors=True,
                     fontNumber=-1)

        return ttf


def md5(string):
    """计算字符串的MD5哈希值"""
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()


def check_font_chars(ttf, charset):
    """
    Get font supported chars and unsupported chars
    :param ttf: TTFont ojbect
    :param charset: chars
    :return: unsupported_chars, supported_chars
    """
    #chars = chain.from_iterable([y + (Unicode[y[0]],) for y in x.cmap.items()] for x in ttf["cmap"].tables)
    chars_int = set()
    for table in ttf['cmap'].tables:
        for k, v in table.cmap.items():
            chars_int.add(k)            
            
    unsupported_chars = []
    supported_chars = []
    for c in charset:
        if ord(c) not in chars_int:
            unsupported_chars.append(c)
        else:
            supported_chars.append(c)

    ttf.close()
    return unsupported_chars, supported_chars


# Import random for chose_font function
import random
