import os

import cv2
from PIL import Image
from tqdm import tqdm

import ContourV6 as cT

INPUT_PATH = "kaggle_3m/"

OUTPUT_PATH = "inputs/"


def rgba2gray():
	"""make all imgs gray"""
	
	img_array = []
	
	for PATIENT_PATH in tqdm(os.listdir(INPUT_PATH)):
		for IMG_PATH in os.listdir(INPUT_PATH + PATIENT_PATH + "/"):
			if "mask" and ".tif" not in IMG_PATH:
				img_path_relative = INPUT_PATH + PATIENT_PATH + "/" + IMG_PATH
				img = cv2.imread(img_path_relative, 0)
				cv2.imwrite(img_path_relative.replace("tif", "png"), img)
				img_array.append(img_path_relative)


def remove_black_masks():
	"""remove all blank masks"""
	
	for PATIENT_PATH in tqdm(os.listdir(INPUT_PATH)):
		for IMG_PATH in os.listdir(INPUT_PATH + PATIENT_PATH + "/"):
			if "mask" and ".tif" in IMG_PATH:
				img_path_relative = INPUT_PATH + PATIENT_PATH + "/" + IMG_PATH
				image = cv2.imread(img_path_relative, 0)
				if cv2.countNonZero(image) == 0:
					os.remove(img_path_relative)


def move_to_input():
	"""move all img to the needed location"""
	
	for i, PATIENT_PATH in tqdm(enumerate(os.listdir(INPUT_PATH))):
		patient_folder = OUTPUT_PATH + "input{}".format(i + 1)
		
		if not os.path.exists(patient_folder):
			os.makedirs(patient_folder)
		
		for IMG_PATH in os.listdir(INPUT_PATH + PATIENT_PATH + "/"):
			img_path_relative = INPUT_PATH + PATIENT_PATH + "/" + IMG_PATH
			os.rename(img_path_relative, patient_folder + "/" + IMG_PATH)
		
		os.removedirs(INPUT_PATH + PATIENT_PATH)


def make_textures():
	"""make textures for all patients"""
	
	for INPUT in tqdm(os.listdir(OUTPUT_PATH)):
		input_path = OUTPUT_PATH + "/" + INPUT
		cT.return_input_file_paths(input_path)
	

def add_5px_upper_and_lower_border():
	"""add 5px to the top and to the bottom of imgs"""
	
	for PATIENT_PATH in tqdm(os.listdir(INPUT_PATH)):
		for IMG_PATH in os.listdir(INPUT_PATH + PATIENT_PATH + "/"):
			if "mask" not in IMG_PATH:
				img_path_relative = INPUT_PATH + PATIENT_PATH + "/" + IMG_PATH
				
				img = cv2.imread(img_path_relative, 0)
				
				if cv2.countNonZero(img) == 0:
					os.remove(img_path_relative)
				else:
					pil_img = Image.open(img_path_relative)

					img_w, img_h = pil_img.size
					background = Image.new('RGBA', (img_w, img_h + 10), (0, 0, 0, 255))
					background.paste(pil_img, (0, 5))
					background.save(img_path_relative[:-4] + "_border.png")

					pil_img.save(img_path_relative.replace("tif", "png"))
					os.remove(img_path_relative)
				
				
add_5px_upper_and_lower_border()
rgba2gray()
remove_black_masks()
move_to_input()
make_textures()
