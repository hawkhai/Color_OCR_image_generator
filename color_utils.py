# -*- coding: utf-8 -*-
"""
Color utilities for OCR image generation
Contains FontColor class and color-related functions
"""
import cv2
import numpy as np
import pickle
import os
from sklearn.cluster import KMeans


# 自定义 Unpickler 修复模块名
class FixUnpickler(pickle._Unpickler):
    def find_class(self, module, name):
        # 去掉可能的 '\r' 并替换旧函数名
        module = module.strip()
        name = name.strip()  # Also strip name to remove \r characters
        
        # Handle numpy compatibility issues for older pickle files
        if module == "numpy.core.multiarray":
            import numpy as np
            if name == "_reconstruct":
                # Create a simple reconstruction function for compatibility
                def _reconstruct(subtype, shape, dtype):
                    return np.ndarray.__new__(subtype, shape, dtype)
                return _reconstruct
            else:
                # For other numpy.core.multiarray attributes
                try:
                    return getattr(np.core.multiarray, name)
                except AttributeError:
                    try:
                        return getattr(np, name)
                    except AttributeError:
                        # Return a dummy function if attribute doesn't exist
                        return lambda *args, **kwargs: None
        
        # Handle numpy.core._internal
        if module == "numpy.core._internal":
            import numpy as np
            try:
                return getattr(np.core._internal, name)
            except AttributeError:
                return lambda *args, **kwargs: None
            
        return super().find_class(module, name)


class FontColor(object):
    def __init__(self, col_file):
        print(col_file) # ./models/colors_new.cp
        
        # Check if there's a corresponding .npy file
        npy_file = col_file.replace('.cp', '.npy')
        
        if os.path.exists(npy_file):
            print(f"Loading colors from numpy file: {npy_file}")
            self.colorsRGB = np.load(npy_file)
        else:
            try:
                # Try multiple methods to load the pickle file
                with open(col_file, 'rb') as f:
                    try:
                        # First try with FixUnpickler
                        u = FixUnpickler(f)
                        u.encoding = 'latin1'
                        self.colorsRGB = u.load()
                    except:
                        # If that fails, try standard pickle with different protocols
                        f.seek(0)
                        try:
                            self.colorsRGB = pickle.load(f, encoding='latin1')
                        except:
                            f.seek(0)
                            try:
                                self.colorsRGB = pickle.load(f, encoding='bytes')
                            except:
                                # Last resort: create a default color palette
                                print("Warning: Could not load color file, using default colors")
                                self.colorsRGB = self._create_default_colors()
            except Exception as e:
                print(f"Error loading color file: {e}")
                print("Using default color palette")
                self.colorsRGB = self._create_default_colors()
            
        self.ncol = self.colorsRGB.shape[0]

        # convert color-means from RGB to LAB for better nearest neighbour
        # computations:
        self.colorsRGB = np.r_[self.colorsRGB[:, 0:3], self.colorsRGB[:, 6:9]].astype('uint8')
        self.colorsLAB = np.squeeze(cv2.cvtColor(self.colorsRGB[None, :, :], cv2.COLOR_RGB2Lab))
    
    def _create_default_colors(self):
        """Create a default color palette if the pickle file cannot be loaded"""
        # Create a basic color palette with common colors
        colors = []
        for r in range(0, 256, 32):
            for g in range(0, 256, 32):
                for b in range(0, 256, 32):
                    colors.append([r, g, b, 0, 0, 0, r, g, b])  # Format to match expected structure
        return np.array(colors[:500])  # Limit to 500 colors


def Lab2RGB(c):
    """Convert LAB color to RGB"""
    if type(c) == list:
        return cv2.cvtColor(np.array([c], dtype=np.uint8)[None,:],cv2.COLOR_Lab2RGB)
    else:
        return cv2.cvtColor(c[None, :, :],cv2.COLOR_Lab2RGB)


def RGB2Lab(rgb):
    """Convert RGB color to LAB"""
    import numpy as np
    if type(rgb) == list:
        return(cv2.cvtColor(np.asarray([rgb],dtype=np.uint8)[None,:],cv2.COLOR_RGB2Lab))
    else:
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)


def get_bestcolor(color_lib, crop_lab):
    """分析图片，获取最适宜的字体颜色"""
    if crop_lab.size > 4800:
        crop_lab = cv2.resize(crop_lab,(100,16))  #将图像转成100*16大小的图片
    labs = np.reshape(np.asarray(crop_lab), (-1, 3))         #len(labs)长度为160   
    clf = KMeans(n_clusters=8)
    clf.fit(labs)
    
    #clf.labels_是每个聚类中心的数据（假设有八个类，则每个数据标签属于每个类的数据格式就是从0-8），clf.cluster_centers_是每个聚类中心   
    total = [0] * 8
   
    for i in clf.labels_:
        total[i] = total[i] + 1            #计算每个类中总共有多少个数据
 
    clus_result = [[i, j] for i, j in zip(clf.cluster_centers_, total)]  #聚类中心，是一个长度为8的数组
    clus_result.sort(key=lambda x: x[1], reverse=True)    #八个类似这样的数组，第一个数组表示类中心，第二个数字表示属于该类中心的一共有多少数据[[array([242.55732946, 128.1509434 , 122.29608128]), 689], [array([245.03461538, 128.59230769, 125.88846154]), 260],，，，]
  
    color_sample = random.sample(range(color_lib.colorsLAB.shape[0]), 500)   # 范围是（0,9882），随机从这些数字里面选取500个

    
    def caculate_distance(color_lab, clus_result):
        weight = [1, 0.8, 0.6, 0.4, 0.2, 0.1, 0.05, 0.01]
        d = 0
        for c, w in zip(clus_result, weight):

            #计算八个聚类中心和当前所选取颜色距离的标准差之和，每个随机选取的颜色当前聚类中心的差值
            d = d + np.linalg.norm(c[0] - color_lab)           
        return d
 
    color_dis = list(map(lambda x: [caculate_distance(color_lib.colorsLAB[x], clus_result), x], color_sample))   #将color_sample中的每个参数当成x传入函数内,color_lib.colorsLAB[x]是一个元组(r,g,b)也就是字体库里面的颜色
    #color_dis 是一个长度为500的列表[[x,y],[],,,,,]，其中[x,y]其中x表示背景色和当前颜色的距离，y表示该颜色的色号  
    color_dis.sort(key=lambda x: x[0], reverse=True)
    color_num = color_dis[0:200]
    color_l = random.choice(color_num)[1]
    #print('color_dis',color_l)
    #color_num=random.choice(color_dis[0:300])
    #print('color_dis[0][1]',color_dis[0][1])
    return tuple(color_lib.colorsRGB[color_l])
    #return tuple(color_lib.colorsRGB[color_dis[0][1]])


# Import random for get_bestcolor function
import random
