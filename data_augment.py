#!/usr/bin/env python
#-*- coding:utf-8 -*-
#
# Author: Donny You (youansheng@gmail.com)
#

from PIL import Image, ImageEnhance, ImageOps, ImageFile
import numpy as np
import random
import threading, os, time

ImageFile.LOAD_TRUNCATED_IMAGES = True

class DataAugmentation(object):
    def __init__(self):
        pass

    @staticmethod
    def open_image(image_file):
        return Image.open(image_file, mode = "r")

    @staticmethod
    def color_normalize(image, mean, std = None):
        image -= mean
        if std is not None:
            image /= std
        return image
        
    @staticmethod
    def random_rotation(image, mode=Image.BICUBIC):
        random_angle = np.random.randint(1, 360)
        return image.rotate(random_angle, mode)

    @staticmethod
    def gradual_shade(image, max_brightness):
        image_list = list()
        image_width = image.size[0]
        image_height = image.size[1]
        image = np.asarray(image)
        imageud = np.copy(image)
        imagedu = np.copy(image)
        imagelr = np.copy(image)
        imagerl = np.copy(image)

        for i in range(image_width):
            alpha = ((image_width - 2.0 * i) * 1.0) / (image_width * 1.0) * max_brightness
            for j in range(image_height):
                for k in range(3):
                    # imagelr[j, i, k] = min(imagelr[j, i, k] * (1 + alpha * imagelr[j, i, k] / 255.0), 255)
                    imagelr[j, i, k] = min(imagelr[j, i, k] * (1 + alpha), 255)
                    # imagerl[j, i, k] = min(imagerl[j, i, k] * (1 - alpha * imagerl[j, i, k] / 255.0), 255)
                    imagerl[j, i, k] = min(imagerl[j, i, k] * (1 - alpha), 255)

        for i in range(image_height):
            alpha = ((image_height - 2.0 * i) * 1.0) / (image_height * 1.0) * max_brightness
            for j in range(image_width):
                for k in range(3):
                    # imageud[i, j, k] = min(imageud[i, j, k] * (1 + alpha * imageud[i, j, k] / 255.0), 255)
                    imageud[i, j, k] = min(imageud[i, j, k] * (1 + alpha), 255)
                    # imagedu[i, j, k] = min(imagedu[i, j, k] * (1 - alpha * imagedu[i, j, k] / 255.0), 255)
                    imagedu[i, j, k] = min(imagedu[i, j, k] * (1 - alpha), 255)

        image_list.append(Image.fromarray(np.uint8(imageud)))
        image_list.append(Image.fromarray(np.uint8(imagedu)))
        image_list.append(Image.fromarray(np.uint8(imagelr)))
        image_list.append(Image.fromarray(np.uint8(imagerl)))

        return image_list

    @staticmethod
    def color_jitter(image, color_fac, bright_fac, contrast_fac, sharp_fac):
        """ color jittering """
        color_image = ImageEnhance.Color(image).enhance(color_fac)  

        brightness_image = ImageEnhance.Brightness(color_image).enhance(bright_fac)

        contrast_image = ImageEnhance.Contrast(brightness_image).enhance(contrast_fac)

        sharp_image = ImageEnhance.Sharpness(contrast_image).enhance(sharp_fac)

        return sharp_image

    @staticmethod
    def random_gaussian(image, mean=0.2, sigma=0.3):

        def gaussian_noisy(im, mean=0.2, sigma=0.3):
            for _i in range(len(im)):
                im[_i] += random.gauss(mean, sigma)
            return im

        img = np.asarray(image)
        img.flags.writeable = True
        width, height = img.shape[:2]
        img_r = gaussian_noisy(img[:, :, 0].flatten(), mean, sigma)
        img_g = gaussian_noisy(img[:, :, 1].flatten(), mean, sigma)
        img_b = gaussian_noisy(img[:, :, 2].flatten(), mean, sigma)
        img[:, :, 0] = img_r.reshape([width, height])
        img[:, :, 1] = img_g.reshape([width, height])
        img[:, :, 2] = img_b.reshape([width, height])
        return Image.fromarray(np.uint8(img))

    @staticmethod
    def save_image(image, path):
        image.save(path)


def colorJitter(image, random_times = 10):
    image_list = list()

    for i in range(random_times):
        color_fac = np.random.randint(5, 15) / 10.
        bright_fac = np.random.randint(5, 15) / 10.
        contrast_fac = np.random.randint(5, 15) / 10.
        sharp_fac = np.random.randint(0, 31) / 10.

        tmp_image = DataAugmentation.color_jitter(image, 
                                                  color_fac, 
                                                  bright_fac, 
                                                  contrast_fac, 
                                                  sharp_fac)
        image_list.append(tmp_image)

    return image_list

def addNoisy(image, random_times = 2):
    image_list = list()
    for i in range(random_times):
        tmp_image = DataAugmentation.random_gaussian(image, 0, 5.0)
        image_list.append(tmp_image)

    return image_list

def gradualBrightness(image, random_times = 2):
    image_list = list()
    for i in range(random_times):
        bright_fac = np.random.randint(8, 11) / 10.
        tmp_image_list = DataAugmentation.gradual_shade(image, bright_fac)
        for image in tmp_image_list:
            image_list.append(image)

    return image_list


if __name__ == '__main__':
    save_dir = "/home/donny/save"
    image_dir = "/home/donny/test"
    image_list = os.listdir(image_dir)
    for image_file in image_list:
        image_path = image_dir + "/" + image_file
        (shotname, extension) = os.path.splitext(image_file)
        try:
            image = DataAugmentation.open_image(image_path)
        except IOError:
            print image_path
            continue

        DataAugmentation.save_image(image, save_dir + "/" + image_file)
        if shotname.split("_")[-1] == "0":
            print image_file
            continue

        count = 0
        for im in colorJitter(image):
            DataAugmentation.save_image(im, save_dir + "/" + shotname + "_au" + str(count) + ".jpg")
            count += 1

        for im in addNoisy(image):
            DataAugmentation.save_image(im, save_dir + "/" + shotname + "_au" + str(count) + ".jpg")
            count += 1

        for im in gradualBrightness(image):
            DataAugmentation.save_image(im, save_dir + "/" + shotname + "_au" + str(count) + ".jpg")
            count += 1
