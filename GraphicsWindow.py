
import pygame
from datetime import datetime
from Model import *

T_WIDTH = 100
MARGIN = 40
MIS = 250
HEIGHT = T_WIDTH * 8 + MARGIN * 2
S_WIDTH = HEIGHT + MIS
mouse_x = 0
mouse_y = 0
piece_images = []
font = None
PIECE_SIZE = 64


def main():
	global font
	pygame.init()
	init_piece_images()
	font = pygame.font.SysFont('Times New Roman',20)
	display = pygame.display.set_mode((S_WIDTH,HEIGHT))
	pygame.display.set_caption('Monopoly Chess')
	
	board = Board()
	#Highlighted moves for the player to chose
	moves = []
	#Moves that would be legal in vanilla chess, but are too expensive for the play
	expensive_moves = []
	
	#This is set to the move for whichever piece needs to be promoted. 
	#Used to display promotion interface 
	promoting = None
	
	#The team that is currently in the phase of their turn in which they purchase tiles
	purchasing = NO_TEAM
	
	#The piece that the mouse is dragging
	held_piece = ()
	
	
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				break
		

		draw_board(display, board, moves, expensive_moves, promoting, purchasing, held_piece)
		pygame.display.update()
		event = pygame.event.wait()
		if promoting == None and purchasing == NO_TEAM:
			if event.type == pygame.MOUSEBUTTONDOWN and in_board(event):
				mouse_tile = tile_from_mouse(event.pos)
				team_moved = NO_TEAM
				did_move = False
				for move in moves:
					if move.dest[0] == mouse_tile[0] and move.dest[1] == mouse_tile[1]:
						if move.must_promote:
							promoting = move
						else:
							team_moved = board.do_move(move)
						moves = []
						expensive_moves = []
						
						did_move = True
						
				purchasing = team_moved
				if len(board.get_purchaseable_tiles(purchasing)) == 0:
					purchasing = NO_TEAM
				if not did_move:
					moves = board.get_legal_moves_from(mouse_tile[0], mouse_tile[1])
					expensive_moves = board.get_expensive_moves_from(mouse_tile[0], mouse_tile[1])
					if board.piece_at(mouse_tile[0], mouse_tile[1]) != None:
						held_piece = mouse_tile
			if len(held_piece) == 2 and not pygame.mouse.get_pressed()[0]:
				held_piece = ()
				mouse_tile = tile_from_mouse(pygame.mouse.get_pos())
				filtered_moves = list(filter(lambda m: m.dest == mouse_tile,moves))
				if len(filtered_moves) > 0:
					move = filtered_moves[0]
					if move.must_promote:
						promoting = move
					else:
						team_moved = board.do_move(move)
					moves = []
					expensive_moves = []
					purchasing = team_moved
					
					
		elif promoting == None:
			if event.type == pygame.MOUSEBUTTONDOWN and in_board(event):
				mouse_tile = tile_from_mouse(event.pos)
				if board.can_purchase_tile(mouse_tile, purchasing):
					board.purchase_tile(mouse_tile, purchasing)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				x = T_WIDTH * 8 + MARGIN + MIS // 4
				y = T_WIDTH * 3 + MARGIN + T_WIDTH // 2
				if x <= event.pos[0] <= x + MIS // 2 and y <= event.pos[1] <= y + T_WIDTH:
					purchasing = NO_TEAM
			if len(board.get_purchaseable_tiles(purchasing)) == 0:
				purchasing = NO_TEAM

		else:
			if event.type == pygame.MOUSEBUTTONDOWN and in_board(event):
				index = (event.pos[0] - MARGIN) // (2 * T_WIDTH)
				if index == 0:
					promoting.promote_to = make_piece(QUEEN, promoting.team)
				elif index == 1:
					promoting.promote_to = make_piece(KNIGHT, promoting.team)
				elif index == 2:
					promoting.promote_to = make_piece(BISHOP, promoting.team)
				elif index == 3:
					promoting.promote_to = make_piece(ROOK, promoting.team)
				purchasing = promoting.team
				board.do_move(promoting)
				promoting = None
				
		if board.is_game_over() == 3:
			winner = "White"
			if board.get_team_moving() == BLACK:
				winner = "Black"
			print(winner + " wins by opponent bankruptcy!")
			break
		if board.is_game_over() == 2:
			winner = "White"
			if board.get_team_moving() == WHITE:
				winner = "Black"
			print(winner + " wins by checkmate!")
			break
			
		elif board.is_game_over() == 1:
			print("Stalemate!")
			break
	
def in_board(event):
	return MARGIN < event.pos[0] < MARGIN + T_WIDTH * 8\
		and  MARGIN < event.pos[1] < MARGIN + T_WIDTH * 8
def draw_board(disp, board, moves, expensive_moves, promoting, purchasing, held_piece):
	disp.fill(0xC19A6B)
	for x in range(0,8):
		for y in range(0,8):
			r = pygame.Rect(x * T_WIDTH + MARGIN, y * T_WIDTH + MARGIN, T_WIDTH, T_WIDTH)
			tile_color = (200,200,200)
			if (x + y) % 2 == 1:
				tile_color = (100,100,100)
			pygame.draw.rect(disp, tile_color, r)
			
			draw_piece(disp, board, x, y, held_piece)
			draw_owner_rect(disp, board, x, y)
				
		draw_text(disp, str(8 - x),(MARGIN / 2, T_WIDTH * x + MARGIN + T_WIDTH / 2))
		draw_text(disp, str(8 - x),(S_WIDTH - MARGIN / 2 - MIS, T_WIDTH * x + MARGIN + T_WIDTH / 2))
		draw_text(disp, chr(ord('A') + x), (MARGIN + T_WIDTH * (x + 1/2), MARGIN / 2))
		draw_text(disp, chr(ord('A') + x), (MARGIN + T_WIDTH * (x + 1/2), HEIGHT - MARGIN / 2))
	if len(held_piece) == 2:
		offset = PIECE_SIZE / 2
		p_loc = (pygame.mouse.get_pos()[0] - offset, pygame.mouse.get_pos()[1] - offset) 
		draw_piece_at(disp, p_loc, board.piece_at(held_piece[0], held_piece[1]))
	draw_incomes(disp, board)
	if promoting != None:
		draw_promotion_overlay(disp, board, promoting.team)
	if purchasing != NO_TEAM:
		draw_purchasing_options(disp, board, purchasing)
		draw_end_turn_button(disp)
	for move in moves:
		highlight_move(disp, move, (0,0,200), board)
	for move in expensive_moves:
		highlight_move(disp, move, (200,0,0), board)
	for x in range(0,8):
		for y in range(0,8):
			price = 100 * board.tile_values[x][y]
			tx = MARGIN + T_WIDTH * (x + 1/2)
			ty = MARGIN + T_WIDTH * (y + 7/8)
			draw_text(disp, "$" + str(price), (tx,ty))

def draw_piece_at(disp, loc, p):
	if p != None:
		row = 0
		if p.team == WHITE:
			row = 0
		else:
			row = 1
		img = piece_images[2 * (p.image - 1) + row]
		disp.blit(img, (int(loc[0]), int(loc[1])))


def draw_piece(disp, board, x, y, held_piece):
	p = board.pieces[x][y]
	if p != None and (len(held_piece) == 0 or x != held_piece[0] or y != held_piece[1]):
		p_x = int(MARGIN + T_WIDTH * (x + 1/2) - PIECE_SIZE / 2)
		p_y = int(MARGIN + T_WIDTH * (y + 1/2) - PIECE_SIZE / 2)
		draw_piece_at(disp, (p_x, p_y), p)
		

def draw_owner_rect(disp, board, x, y):
	if board.tile_teams[x][y] != NO_TEAM:
		rm = 4
		r_x = x * T_WIDTH + rm + MARGIN
		r_y = y * T_WIDTH + rm + MARGIN
		r_width = T_WIDTH - 2 * rm
		r2 = pygame.Rect(r_x, r_y, r_width, r_width)
		tile_color = (255,255,255)
		if board.tile_teams[x][y] == BLACK:
			tile_color = (0,0,0)
		pygame.draw.rect(disp, tile_color, r2, rm)

def draw_incomes(disp, board):
	inc_x = S_WIDTH - MARGIN - MIS / 2
	inc_y_w = HEIGHT - 2 * MARGIN
	inc_y_b = 2 * MARGIN
	draw_text(disp, "White Money: $" + str(board.money[WHITE]), (inc_x, inc_y_w - 60))
	draw_text(disp, "White Income: +$" + str(board.income[WHITE]), (inc_x, inc_y_w - 30))
	draw_text(disp, "White Expenses: -$" + str(board.rent[WHITE]), (inc_x, inc_y_w))
	draw_text(disp, "Black Money: $" + str(board.money[BLACK]), (inc_x, inc_y_b))
	draw_text(disp, "Black Income: +$" + str(board.income[BLACK]), (inc_x, inc_y_b + 30))
	draw_text(disp, "Black Expenses: -$" + str(board.rent[BLACK]), (inc_x, inc_y_b + 60))

def highlight_move(disp, move, color, board):
	trans = pygame.Surface((T_WIDTH, T_WIDTH))
	trans.set_alpha(128)
	trans.fill(color)
	x = move.dest[0]
	y = move.dest[1]
	disp.blit(trans, (x * T_WIDTH + MARGIN, y * T_WIDTH + MARGIN))
	text_x = (x + 1/2) * T_WIDTH + MARGIN
	text_y = (y + 1/4) * T_WIDTH + MARGIN
	text_color = (255,0,0)
	if move.net_profit >= 0:
		text_color = (0,255,0)
	draw_text(disp, "$" + str(move.net_profit), (text_x,text_y), text_color)
	

def draw_text(disp, string, loc, color = (0,0,0)):
	text = font.render(string, True, color)
	x = int(loc[0] - text.get_rect().width / 2)
	y = int(loc[1] - text.get_rect().height / 2)
	disp.blit(text, (x, y))
		
def tile_from_mouse(point):
	return (int((point[0] - MARGIN) // T_WIDTH), int((point[1] - MARGIN) // T_WIDTH))
	
def draw_purchasing_options(disp, board, team):
	tiles = board.get_purchaseable_tiles(team)
	for tile in tiles:
		trans = pygame.Surface((T_WIDTH, T_WIDTH))
		trans.set_alpha(128)
		trans.fill((0,200,0))
		disp.blit(trans, (tile[0] * T_WIDTH + MARGIN, tile[1] * T_WIDTH + MARGIN))

def draw_promotion_overlay(disp, board, team):
	
	cover = pygame.Surface((T_WIDTH * 8, T_WIDTH * 8))
	cover.set_alpha(128)
	cover.fill((0,0,0))
	disp.blit(cover, (MARGIN, MARGIN))
	promote_types = [2,4,3,5]

	if team == WHITE:
		row = 0
	else:
		row = 1
	
	for i in range(0,4):
		im = piece_images[(promote_types[i] - 1) * 2 + row]
		x = int(MARGIN + T_WIDTH * (1 + 2 * i) - im.get_rect().width / 2)
		y = int(MARGIN + 4 * T_WIDTH - im.get_rect().width / 2)
		disp.blit(im, (x, y))

	if MARGIN < pygame.mouse.get_pos()[0] < S_WIDTH - MARGIN:
		j = ( pygame.mouse.get_pos()[0] - MARGIN) // (2 * T_WIDTH)
		trans = pygame.Surface((T_WIDTH * 2, T_WIDTH * 8))
		trans.set_alpha(128)
		trans.fill((255,255,255))
		disp.blit(trans, (j * T_WIDTH * 2 + MARGIN, MARGIN))

def draw_end_turn_button(disp):
	trans = pygame.Surface((MIS // 2, T_WIDTH))
	trans.fill((100,100,200))
	disp.blit(trans, (T_WIDTH * 8 + MARGIN + MIS // 4, 4 * T_WIDTH + MARGIN - T_WIDTH // 2))	
	draw_text(disp, "End Turn", (T_WIDTH * 8 + MARGIN + MIS // 2, 4 * T_WIDTH + MARGIN))

def init_piece_images():
	for i in range(1,7):
		for j in range(1,3):
			piece_images.append(pygame.image.load("row-" + str(j) + "-col-" + str(i) + ".png"))
			

main()
