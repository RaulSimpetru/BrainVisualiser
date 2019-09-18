import os

import cv2
import numpy as np


def return_input_file_paths(input_folder_path):
	"""Returns the paths for the borders, textures and masks"""
	
	if not os.path.exists(input_folder_path):
		input_folder_path = "inputs/input1"
	
	result = []
	texture = []
	tumor_masks = []
	for file in os.listdir(input_folder_path):
		if "texture" not in file:
			if "border" in file:
				result.append(input_folder_path + "/" + file)
			elif "mask" in file:
				tumor_masks.append(input_folder_path + "/" + file)
			else:
				texture.append(input_folder_path + "/" + file)
	
	result.sort(key=lambda x: int(x.replace(input_folder_path + "/", "").split("_")[4]))
	texture.sort(key=lambda x: int(x.replace(input_folder_path + "/", "").split("_")[4].replace(".png", "")))
	tumor_masks.sort(key=lambda x: int(x.replace(input_folder_path + "/", "").split("_")[4]))
	
	# print(result)
	# print(texture)
	# print(tumor_masks)
	base_contours = return_contours(result)
	mask_contours = return_contours(tumor_masks)
	# print(len(mask_contours))
	mask_output = []
	for mask_path, contour in zip(tumor_masks, mask_contours):
		mask_output.append({"index": int(mask_path.split("_")[4]) - 1, "contour": contour})
	
	textures = make_textures_v3(texture, input_folder_path, base_contours, mask_output)
	# print(result)
	
	return result, textures, mask_output


def apply_brightness_contrast(input_img, brightness, contrast):
	"""Applies brightness and contrast"""
	
	if brightness != 0:
		if brightness > 0:
			shadow = brightness
			highlight = 255
		else:
			shadow = 0
			highlight = 255 + brightness
		alpha_b = (highlight - shadow) / 255
		gamma_b = shadow
		
		buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
	else:
		buf = input_img.copy()
	
	if contrast != 0:
		f = 131 * (contrast + 127) / (127 * (131 - contrast))
		alpha_c = f
		gamma_c = 127 * (1 - f)
		
		buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)
	
	return buf


def apply_otsu(img):
	"""Applies Otsu's binarizazion for thresholding"""
	
	blur = cv2.GaussianBlur(img, (0, 0), sigmaX=6, sigmaY=5)
	
	_, result = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	return result


def find_best_contours_v3(contours, img_dims):
	"""Finds the best contours by filtering for contours with an area above 1E4 px and closest to the center of the img"""
	
	x_size, y_size = img_dims
	x_center = x_size / 2
	y_center = y_size / 2
	
	max_possible_score = np.sqrt(x_center ** 2 + y_center ** 2)
	
	result = []
	
	sizes = [cv2.contourArea(i) for i in contours]
	
	if any(i > 1E4 for i in sizes):
		result = [contour for contour in contours if cv2.contourArea(contour) > 1E4]
		return result
	else:
		for contour in contours:
			x_center_contour, y_center_contour = find_centroid(contour)
			score = np.sqrt((x_center - x_center_contour) ** 2 + (y_center - y_center_contour) ** 2)
			
			if score <= max_possible_score:
				result.append([contour, score])
		
		result.sort(key=lambda x: x[1])
		
		try:
			return [result[0][0]]
		except IndexError:
			return result


def find_centroid(contour):
	"""Find centroid"""
	
	length = len(contour)
	
	sum_x = np.sum(contour[:, 0][:, 0])
	sum_y = np.sum(contour[:, 0][:, 1])
	
	return sum_x / length, sum_y / length


def find_centroid_v2(contour):
	"""Find centroid"""
	
	length = len(contour)

	sum_x = np.sum(item[0] for item in contour)
	sum_y = np.sum(item[1] for item in contour)
	
	return sum_x / length, sum_y / length


def auto_append(array, what_to_append):
	"""Auto appends elements to an array (P.S. is this explanation really needed?)"""
	
	for element in what_to_append:
		array.append(element)


def return_largest_contour(input_contours):
	"""Returns larges contour from all given contours"""
	
	best_size = 0
	result = None
	for temp in input_contours:
		if cv2.contourArea(temp[0]) > best_size:
			best_size = cv2.contourArea(temp[0])
			result = temp
	
	return result


def return_contours(img_paths):
	"""Return contours of the given img paths"""
	
	contours = []
	for img_path in img_paths:
		input = cv2.imread(img_path)
		gray = cv2.cvtColor(input, cv2.COLOR_RGBA2GRAY)
		c_and_b = apply_brightness_contrast(gray, 120, 120)
		otsu = apply_otsu(c_and_b)
		edged = cv2.Canny(otsu, 10, 400, True)
		temp_contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		contour = find_best_contours_v3(temp_contours, (input.shape[1], input.shape[0]))
		
		contours.append(contour)
	
	return contours


def pyglet_bulk_return_contour_for_surfaces_with_colors(img_paths, mask_inputs):
	"""it returns all needed vertices and colors and texture coordinates to be able to display one head"""
	
	slab_thickness = 0.1537185 - 0.005219956 * len(img_paths) + 0.00007904272 * len(img_paths) ** 2 - 4.481312e-7 * len(
		img_paths) ** 3  # a function to determine the slab_thickness given how many slabs are given
	
	space_between_slabs = 0.000125
	
	top_polygons = []
	top_colors = []
	
	middle_polygons = []
	middle_colors = []
	
	bottom_polygons = []
	bottom_colors = []
	
	mask_top_polygons = []
	mask_bot_polygons = []
	mask_middle_polygons = []
	mask_top_and_bot_colors = []
	mask_middle_colors = []
	
	bottom_height = 0 - ((len(img_paths) / 2) * (slab_thickness + space_between_slabs))
	
	contours = return_contours(img_paths)
	
	max_x = 256
	max_y = 256
	min_x = min_y = 0
	
	maping_scale_array = [-1, 1]
	
	largest_contour = return_largest_contour(contours)
	
	temp_x, temp_y = find_centroid(largest_contour[0])
	
	x_reference = np.interp(temp_x, [min_x, max_x], maping_scale_array)
	y_reference = np.interp(temp_y, [min_y, max_y], maping_scale_array)
	
	for j, contour in enumerate(contours):
		
		top_points = []
		top_color = []
		
		middle_points = []
		middle_color = []
		
		bottom_points = []
		bottom_color = []
		
		r, g, b, a = 173, 216, 230, 100
		
		top_height_between_top_and_bot = bottom_height + slab_thickness
		
		for mask_input in mask_inputs:
			if j == mask_input.get("index"):
				mask_top_points = []
				mask_bot_points = []
				mask_middle_points = []
				mask_top_and_bot_color = []
				mask_middle_color = []
				
				for i in range(len(mask_input.get("contour")[0])):
					temp_contour = mask_input.get("contour")
					try:
						if i + 1 < len(temp_contour[0]):
							x1 = np.interp(temp_contour[0][i][0][0], [min_x, max_x], maping_scale_array)
							y1 = np.interp(temp_contour[0][i][0][1], [min_y, max_y], maping_scale_array)
							x2 = np.interp(temp_contour[0][i + 1][0][0], [min_x, max_x], maping_scale_array)
							y2 = np.interp(temp_contour[0][i + 1][0][1], [min_y, max_y], maping_scale_array)
						
						else:
							x1 = np.interp(temp_contour[0][len(temp_contour[0]) - 1][0][0], [min_x, max_x], maping_scale_array)
							y1 = np.interp(temp_contour[0][len(temp_contour[0]) - 1][0][1], [min_y, max_y], maping_scale_array)
							x2 = np.interp(temp_contour[0][0][0][0], [min_x, max_x], maping_scale_array)
							y2 = np.interp(temp_contour[0][0][0][1], [min_y, max_y], maping_scale_array)
					
					except IndexError:
						if i + 1 < len(temp_contour[0]):
							x1 = np.interp(temp_contour[0][i][0], [min_x, max_x], maping_scale_array)
							y1 = np.interp(temp_contour[0][i][1], [min_y, max_y], maping_scale_array)
							x2 = np.interp(temp_contour[0][i + 1][0], [min_x, max_x], maping_scale_array)
							y2 = np.interp(temp_contour[0][i + 1][1], [min_y, max_y], maping_scale_array)
						
						else:
							x1 = np.interp(temp_contour[0][len(temp_contour[0]) - 1][0], [min_x, max_x], maping_scale_array)
							y1 = np.interp(temp_contour[0][len(temp_contour[0]) - 1][1], [min_y, max_y], maping_scale_array)
							x2 = np.interp(temp_contour[0][0][0], [min_x, max_x], maping_scale_array)
							y2 = np.interp(temp_contour[0][0][1], [min_y, max_y], maping_scale_array)
					
					x1 = x1 - x_reference
					x2 = x2 - x_reference
					y1 = y1 - y_reference
					y2 = y2 - y_reference
					
					auto_append(mask_top_points, (x1, y1, top_height_between_top_and_bot))
					auto_append(mask_top_and_bot_color, (255, 0, 0, 255))
					
					auto_append(mask_middle_points, (x1, y1, top_height_between_top_and_bot))
					auto_append(mask_middle_points, (x1, y1, bottom_height))
					auto_append(mask_middle_points, (x2, y2, bottom_height))
					
					for _ in range(6):
						auto_append(mask_middle_color, (255, 0, 0, 255))
					
					auto_append(mask_middle_points, (x1, y1, top_height_between_top_and_bot))
					auto_append(mask_middle_points, (x2, y2, bottom_height))
					auto_append(mask_middle_points, (x2, y2, top_height_between_top_and_bot))
					
					auto_append(mask_bot_points, (x1, y1, bottom_height))
				
				mask_top_polygons.append(("v3f", tuple(mask_top_points)))
				mask_top_and_bot_colors.append(("c4B", tuple(mask_top_and_bot_color)))
				
				mask_middle_polygons.append(("v3f", tuple(mask_middle_points)))
				mask_middle_colors.append(("c4B", tuple(mask_middle_color)))
				
				mask_bot_polygons.append(("v3f", tuple(mask_bot_points)))
		
		for i in range(len(contour[0])):
			
			try:
				if i + 1 < len(contour[0]):
					x1 = np.interp(contour[0][i][0][0], [min_x, max_x], maping_scale_array)
					y1 = np.interp(contour[0][i][0][1], [min_y, max_y], maping_scale_array)
					x2 = np.interp(contour[0][i + 1][0][0], [min_x, max_x], maping_scale_array)
					y2 = np.interp(contour[0][i + 1][0][1], [min_y, max_y], maping_scale_array)
				
				else:
					x1 = np.interp(contour[0][len(contour[0]) - 1][0][0], [min_x, max_x], maping_scale_array)
					y1 = np.interp(contour[0][len(contour[0]) - 1][0][1], [min_y, max_y], maping_scale_array)
					x2 = np.interp(contour[0][0][0][0], [min_x, max_x], maping_scale_array)
					y2 = np.interp(contour[0][0][0][1], [min_y, max_y], maping_scale_array)
			
			except IndexError:
				if i + 1 < len(contour[0]):
					x1 = np.interp(contour[0][i][0], [min_x, max_x], maping_scale_array)
					y1 = np.interp(contour[0][i][1], [min_y, max_y], maping_scale_array)
					x2 = np.interp(contour[0][i + 1][0], [min_x, max_x], maping_scale_array)
					y2 = np.interp(contour[0][i + 1][1], [min_y, max_y], maping_scale_array)
				
				else:
					x1 = np.interp(contour[0][len(contour[0]) - 1][0], [min_x, max_x], maping_scale_array)
					y1 = np.interp(contour[0][len(contour[0]) - 1][1], [min_y, max_y], maping_scale_array)
					x2 = np.interp(contour[0][0][0], [min_x, max_x], maping_scale_array)
					y2 = np.interp(contour[0][0][1], [min_y, max_y], maping_scale_array)
			
			x1 = x1 - x_reference
			x2 = x2 - x_reference
			y1 = y1 - y_reference
			y2 = y2 - y_reference
			
			auto_append(top_points, (x1 * 1.001, y1 * 1.001, top_height_between_top_and_bot))
			auto_append(top_color, (int(r * (1 - 0.65)), int(g * (1 - 0.65)), int(b * (1 - 0.65)), 255))
			
			auto_append(middle_points, (x1, y1, top_height_between_top_and_bot))
			auto_append(middle_points, (x1, y1, bottom_height))
			auto_append(middle_points, (x2, y2, bottom_height))
			
			for _ in range(6):
				auto_append(middle_color, (r, g, b, a))
			
			auto_append(middle_points, (x1, y1, top_height_between_top_and_bot))
			auto_append(middle_points, (x2, y2, bottom_height))
			auto_append(middle_points, (x2, y2, top_height_between_top_and_bot))
			
			auto_append(bottom_points, (x1 * 1.001, y1 * 1.001, bottom_height))
			auto_append(bottom_color, (int(r * (1 - 0.65)), int(g * (1 - 0.65)), int(b * (1 - 0.65)), 255))
		
		bottom_height = top_height_between_top_and_bot + space_between_slabs
		
		top_polygons.append(("v3f", tuple(top_points)))
		top_colors.append(("c4B", tuple(top_color)))
		
		middle_polygons.append(("v3f", tuple(middle_points)))
		middle_colors.append(("c4B", tuple(middle_color)))
		
		bottom_polygons.append(("v3f", tuple(bottom_points)))
		bottom_colors.append(("c4B", tuple(bottom_color)))
	
	return zip(top_polygons, top_colors), zip(middle_polygons, middle_colors), zip(bottom_polygons, bottom_colors), \
	       zip(mask_top_polygons, mask_top_and_bot_colors), zip(mask_middle_polygons, mask_middle_colors), \
	       zip(mask_bot_polygons, mask_top_and_bot_colors), mask_inputs[0].get("index")


def make_textures_v3(img_paths, output_folder_path, base_contours, mask_inputs):
	output_textures_paths = []
	
	if not os.path.exists(output_folder_path):
		os.makedirs(output_folder_path)
	
	for i, img_path in enumerate(img_paths):
		
		file_path = "{}/texture_{}.png".format(output_folder_path, str(i))
		
		if os.path.isfile(file_path):
			output_textures_paths.append(file_path)
			continue
		
		input = cv2.imread(img_path)
		contour = base_contours[i]
		
		rgba = cv2.cvtColor(input, cv2.COLOR_RGB2RGBA)
		
		h = input.shape[0]
		w = input.shape[1]
		
		for y in range(0, (h + 10)):
			for x in range(0, w):
				try:
					if cv2.pointPolygonTest(np.float32(contour[0]), (x, y + 5), False) < 0:
						rgba[y][x] = [0, 0, 0, 0]
				except:
					continue
		
		for mask_input in mask_inputs:
			if i == (mask_input.get("index")):
				cv2.drawContours(rgba, mask_input.get("contour"), -1, (0, 0, 255, 255), 1)
		
		file_path = "{}/texture_{}.png".format(output_folder_path, str(i))
		
		cv2.imwrite(file_path, rgba)
		
		output_textures_paths.append(file_path)
	
	return output_textures_paths
