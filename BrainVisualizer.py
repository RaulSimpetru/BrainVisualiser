import os
import random

from OpenGL.GL import glGenTextures as GenTextures
from OpenGL.GL import glLight as Light
from pyglet.gl import *
from pyglet.window import key

import Contour as cT

stop_rotating = False
show_tumor = False
show_head = True
turn_right = True

window = pyglet.window.Window(width=1400, height=800, caption="Brain Visualizer")
window.projection = pyglet.window.Projection3D()

possible_inputs = os.listdir("inputs")
possible_inputs.sort(key=lambda x: int(x.replace("input", "")))

random_input = possible_inputs[random.randint(0, len(possible_inputs) - 1)]

input_files, texture_files, mask_output = cT.return_input_file_paths("inputs/{}".format(random_input))

tops, middles, bottoms, mask_tops, mask_middles, mask_bottoms, first_mask_index = cT.pyglet_bulk_return_contour_for_surfaces_with_colors(
	input_files, mask_output)

origin_axis = pyglet.graphics.vertex_list(2, ("v3f", (0, 0, -10, 0, 0, 10)), ("c3B", (255, 0, 0, 255, 0, 0)))

texture_canvas = pyglet.graphics.vertex_list(6, ('v3f', (
	-1.2, -1.2, 0,
	1.2, -1.2, 0,
	-1.2, 1.2, 0,
	1.2, -1.2, 0,
	1.2, 1.2, 0,
	-1.2, 1.2, 0
)), ('t2f', (0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1)))

draw_exclusively = -1
degree = 0

to_draw = [i for i in range(len(input_files))]


def load_images(texture_paths):
	texture_data = []
	
	for texture_path in texture_paths:
		
		img = pyglet.image.load(texture_path)
		textureData = img.get_data()
		
		texture_data.append(textureData)
	
	bg_img_gl = GenTextures(len(texture_paths))
	
	if len(bg_img_gl) < 2:
		print("More Brain Slices required")
		exit()
	
	return texture_data, bg_img_gl


texture_datas, bgImgGL = load_images(texture_files)


def bulk_brain_surfaces(tops, middles, bottoms, mask_tops, mask_middles, mask_bottoms):
	"""Creates all needed vertex_lists for drawing the head"""
	
	top_lists = []
	middle_lists = []
	bottom_lists = []
	mask_top_lists = []
	mask_middle_lists = []
	mask_bottom_lists = []
	
	for top, color in tops:
		top_lists.append(pyglet.graphics.vertex_list(int(len(top[1]) / 3), top, color))
	
	for middle, color in middles:
		middle_lists.append(pyglet.graphics.vertex_list(int(len(middle[1]) / 3), middle, color))
	
	for bottom, color in bottoms:
		bottom_lists.append(pyglet.graphics.vertex_list(int(len(bottom[1]) / 3), bottom, color))
	
	for mask_top, mask_color in mask_tops:
		mask_top_lists.append(pyglet.graphics.vertex_list(int(len(mask_top[1]) / 3), mask_top, mask_color))
	
	for mask_middle, mask_color in mask_middles:
		mask_middle_lists.append(pyglet.graphics.vertex_list(int(len(mask_middle[1]) / 3), mask_middle, mask_color))
	
	for mask_bottom, mask_color in mask_bottoms:
		mask_bottom_lists.append(pyglet.graphics.vertex_list(int(len(mask_bottom[1]) / 3), mask_bottom, mask_color))
	
	return top_lists, middle_lists, bottom_lists, mask_top_lists, mask_middle_lists, mask_bottom_lists


top_lists, middle_lists, bottom_lists, mask_top_lists, mask_middle_lists, mask_bottom_lists = \
	bulk_brain_surfaces(tops, middles, bottoms, mask_tops, mask_middles, mask_bottoms)


def stop_or_start_rotating():
	global stop_rotating
	
	if stop_rotating:
		stop_rotating = False
	else:
		stop_rotating = True


def show_or_dont_tumor():
	global show_tumor
	
	if show_tumor:
		show_tumor = False
	else:
		show_tumor = True


def show_or_dont_head():
	global show_head
	
	if show_head:
		show_head = False
	else:
		show_head = True


def set_right_rotation():
	global turn_right
	if not turn_right:
		turn_right = True


def set_left_rotation():
	global turn_right
	if turn_right:
		turn_right = False


@window.event
def on_draw():
	window.clear()
	
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	
	glPushMatrix()
	
	glEnable(GL_LIGHTING)
	glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
	glEnable(GL_COLOR_MATERIAL)
	glEnable(GL_LIGHT0)
	
	Light(GL_LIGHT0, GL_POSITION, (1, 1, 0))
	Light(GL_LIGHT0, GL_AMBIENT, (0, 0, 0, 1))
	Light(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
	Light(GL_LIGHT0, GL_SPECULAR, (1, 1, 1, 1))
	
	glRotatef(90, -1, 0, 0)
	glTranslatef(-1.3, 0, 0)
	glRotatef(degree, 0, 0, 1)
	
	if show_tumor:
		for i in range(len(mask_middle_lists)):
			if i + first_mask_index in to_draw:
				mask_top_lists[i].draw(GL_POLYGON)
				mask_middle_lists[i].draw(GL_TRIANGLES)
				mask_bottom_lists[i].draw(GL_POLYGON)
	
	if show_head:
		for i in range(len(middle_lists)):
			
			if i in to_draw:
				
				top_lists[i].draw(GL_LINE_LOOP)
				bottom_lists[i].draw(GL_LINE_LOOP)
				
				glDepthMask(False)
				middle_lists[i].draw(GL_TRIANGLES)
				glDepthMask(True)
	
	glTranslatef(1.3, 0, 0)
	
	glPopMatrix()
	
	glPushMatrix()
	
	glDisable(GL_LIGHTING)
	glDisable(GL_COLOR_MATERIAL)
	
	glTranslatef(1.5, 0, 0)
	
	if draw_exclusively != -1 and draw_exclusively != len(middle_lists):
		glLineWidth(5)
		
		up_line = pyglet.graphics.vertex_list(2, (
			'v3f', (-1.65, top_lists[draw_exclusively].vertices[2] + 0.125, 0, -0.8, 1.2, 0)))
		down_line = pyglet.graphics.vertex_list(2, (
			'v3f', (-1.65, bottom_lists[draw_exclusively].vertices[2] - 0.125, 0, -0.8, -1.2, 0)))
		
		up_line.draw(GL_LINES)
		down_line.draw(GL_LINES)
		
		glEnable(GL_TEXTURE_2D)
		
		glBindTexture(GL_TEXTURE_2D, bgImgGL[draw_exclusively])
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 256, 256, 0, GL_BGRA, GL_UNSIGNED_BYTE, texture_datas[draw_exclusively])
		
		texture_canvas.draw(GL_TRIANGLES)
		
		glDisable(GL_TEXTURE_2D)
	
	glTranslatef(-1.5, 0, 0)
	
	glPopMatrix()


@window.event
def on_key_press(symbol, _):
	global to_draw, draw_exclusively
	
	if symbol == key.SPACE:
		stop_or_start_rotating()
	
	elif symbol == key.Q:
		show_or_dont_tumor()
	
	elif symbol == key.E:
		show_or_dont_head()
	
	elif symbol == key.ESCAPE:
		quit()
	
	elif symbol in [key.D, key.RIGHT]:
		set_right_rotation()
	
	elif symbol in [key.A, key.LEFT]:
		set_left_rotation()
	
	elif symbol in [key.W, key.UP]:
		draw_exclusively += 1
		to_draw = [draw_exclusively]
		
		if draw_exclusively > len(middle_lists):
			draw_exclusively = -1
			to_draw = [i for i in range(len(middle_lists))]
	
	elif symbol in [key.S, key.DOWN]:
		draw_exclusively -= 1
		if draw_exclusively < -1:
			draw_exclusively = -1
		
		if draw_exclusively != -1:
			to_draw = [draw_exclusively]
		else:
			to_draw = [i for i in range(len(middle_lists))]


def increment_rotation_degree():
	global degree
	
	if turn_right:
		degree += 1
	else:
		degree -= 1
	
	if degree > 360:
		degree = 0
	elif degree < 0:
		degree = 360


def rotate(_):
	if not stop_rotating:
		increment_rotation_degree()


if __name__ == "__main__":
	glMatrixMode(GL_MODELVIEW)
	glEnable(GL_BLEND)
	glEnable(GL_DEPTH_CLAMP)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glEnable(GL_MULTISAMPLE_ARB)
	glEnable(GL_DEPTH_TEST)
	glTranslatef(0, 0, -2.9)
	
	screen = pyglet.canvas.get_display().get_default_screen()
	
	window.set_location(x=int(screen.width / 2 - (1400 / 2)), y=int(screen.height / 2 - 400))
	
	pyglet.clock.schedule_interval(rotate, 1 / 60)
	pyglet.app.run()
