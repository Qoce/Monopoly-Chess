#TODO: Work on changing how the piece implementation works to make undoing moves work better for 
#Things like castleing and en passant

import numpy

WHITE = 0
BLACK = 1
NO_TEAM = -1

TPC = 100
RENT_COST = 30
ROOK = 5
PAWN = 6
BISHOP = 3
KNIGHT = 4
QUEEN = 2
KING = 1


class Move:
	
	def __init__(self, board, loc, dest, destroy = (), 
			swap_from = (), swap_to=(), must_promote = False):
		self.loc = loc
		self.dest = dest
		self.destroy = destroy
		self.swap_from = swap_from
		self.swap_to = swap_to
		self.must_promote = must_promote
		self.team = board.piece_at(loc[0],loc[1]).team
		self.board = board
		self.cost = self.__move_cost(board, loc, dest) 
		self.cost += self.__move_cost(board, swap_from, swap_to)
		self.net_profit = self.__net_profit(board, loc, dest)
		self.promote_to = None
	
	def __move_cost(self, board, loc, dest):
		if len(loc) == 0 or len(dest) == 0:
			return 0
		dx,dy = dest[0] - loc[0], dest[1] - loc[1]
		g = numpy.gcd(dx,dy)
		dx //= g
		dy //= g
		cost = 0
		for i in range(0,g + 1):
			cost += self.board.tile_rent((loc[0] + i * dx, loc[1] + i * dy), self.team)
		return cost

	def __net_profit(self, board, loc, dest):
		net = -self.cost
		net += board.calc_income(self.team)
		net -= board.calc_rent(self.team)
		net -= board.tile_income(loc, self.team)
		net += board.tile_income(dest, self.team, board.piece_at(loc[0],loc[1]))
		net += board.tile_rent(loc, self.team)
		net -= board.tile_rent(dest, self.team)
		return net
		
	def is_affordable(self, board):
		return self.cost <= board.money[self.team] and self.net_profit + board.money[self.team] >= 0
	
	def __str__(self):
		string = str(self.loc) + "," + str(self.dest) + "," + str(self.swap_from)
		string += "," + str(self.swap_to) + "," + str(self.destroy)
		if self.promote_to != None:
			string += "="
			if self.promote_to.image == ROOK:
				string += "R"
			elif self.promote_to.image == KNIGHT:
				string += "N"
			elif self.promote_to.image == BISHOP:
				string += "B"
			elif self.promote_to.image == QUEEN:
				string += "Q"
		return string

class Turn:
	move = None
	purchases = []
	def __init__(self, move):
		self.move = move
		
class Piece:
	
	def get_valid_moves(self, x, y, board):
		return list(filter(lambda _: _.is_affordable(board), self._get_moves(x,y,board)))
	
	def get_expensive_moves(self, x, y, board):
		return list(filter(lambda _: not _.is_affordable(board), self._get_moves(x,y,board)))
	
	def _get_moves(self, x, y, board):
		valid_moves = []
		for dire in self.movement_dirs:
			for i in range(1, self.max_dist + 1):
				if x + dire[0] * i >= 8 or x + dire[0] * i < 0 or \
						y + dire[1] * i >= 8 or y + dire[1] * i < 0:
					break
				p = board.piece_at(x + dire[0] * i, y + dire[1] * i)
				if p is None or p.team != self.team:
					valid_moves.append(Move(board,(x, y), (x + dire[0] * i, y + dire[1] * i)))					
				if not p is None:
					break
		return valid_moves
		
	def get_threatened_tiles(self, x, y, board):
		return list(filter(lambda m: m.cost <= board.money[self.team], self._get_moves(x,y,board)))
	
	def __init__(self, image, movement_dirs, team, symmetric = True, max_dist = 8):
		self.image = image
		
		if symmetric:
			for direction in movement_dirs:
				p = [-direction[0], direction[1]]
				if not any(direct[0] == p[0] and direct[1] == p[1] for direct in movement_dirs):
					movement_dirs.append(p)
			for direction in movement_dirs:
				p = [direction[0], -direction[1]]
				if not any(direct[0] == p[0] and direct[1] == p[1] for direct in movement_dirs):
					movement_dirs.append(p)
			for direction in movement_dirs:
				p = [direction[1], direction[0]]
				if not any(direct[0] == p[0] and direct[1] == p[1] for direct in movement_dirs):
					movement_dirs.append(p)
		self.movement_dirs = movement_dirs
		self.max_dist = max_dist
		self.team = team
		self.has_moved = False
	def move(self, board, x, y, dx, dy):
		self.has_moved = True
		
def make_piece(piece_type, team):
	if piece_type == ROOK:
		return Piece(5, [[1,0]], team)
	elif piece_type == PAWN:
		return Pawn(team)
	elif piece_type == BISHOP:
		return Piece(3,[[1,1]], team)
	elif piece_type == KNIGHT:
		return Piece(4, [[2,1]], team, True, 1)
	elif piece_type == QUEEN:
		return Piece(2, [[1,0],[1,1]], team)
	else:
		return King(team)

class King(Piece):
	def __init__(self, team):
		super().__init__(1, [[0,1],[1,1]], team, True, 1)

	def _get_moves(self, x, y, board):
		valid_moves = super()._get_moves(x, y, board) 
		if not self.has_moved:
			if not board.piece_at(6,y) and not board.piece_at(5, y):
				r1 = board.piece_at(7,y)
				if not r1 == None and not r1.has_moved:	
					if board.tile_safe(6,y,self.team) and board.tile_safe(5,y,self.team):			
						valid_moves.append(Move(board,(x, y), (6,y), (), (7,y), (5,y)))
			if not board.piece_at(3,y) and not board.piece_at(2,y) and not board.piece_at(1,y):
				r2 = board.piece_at(y,0)
				if not r2 == None and not r2.has_moved:
					if all(board.tile_safe(x,y,self.team) for x in range(1,4)):
						valid_moves.append(Move(board,(x, y), (2,y), (), (0,y), (3,y)))
		return valid_moves
		
	def get_threatened_tiles(self, x, y, board):
		return super()._get_moves(x, y, board)

class Pawn(Piece):
	turn_double_moved = -1
	
	def __init__(self, team):
		super().__init__(6, [], team, False, 1)
	
	def _get_moves(self, x, y, board):
		valid_moves = []
		y_dir = 0
		if self.team == WHITE:
			y_dir = -1
		else:
			y_dir = 1
		if board.piece_at(x,y + y_dir) == None:
			valid_moves.append(Move(board,(x,y), (x, y + y_dir)))
			if not self.has_moved and board.piece_at(x,y + 2 * y_dir) == None:
				valid_moves.append(Move(board,(x,y), (x, y + 2 * y_dir)))
		if board.piece_at(x + 1, y + y_dir) != None:
			if board.piece_at(x + 1, y + y_dir).team != self.team:
				valid_moves.append(Move(board,(x, y), (x + 1, y + y_dir)))
		if board.piece_at(x - 1, y + y_dir) != None:
			if board.piece_at(x - 1, y + y_dir).team != self.team:
				valid_moves.append(Move(board,(x, y), (x - 1, y + y_dir)))
		if board.piece_at(x + 1, y) != None and board.piece_at(x + 1, y).team != self.team:
			if type(board.piece_at(x + 1, y)) is Pawn:
				if board.piece_at(x + 1, y).turn_double_moved == board.turn - 1:
					valid_moves.append(Move(board,(x, y), (x + 1, y + y_dir), (x + 1, y)))
		if board.piece_at(x - 1, y) != None and board.piece_at(x - 1, y).team != self.team:
			if type(board.piece_at(x - 1, y)) is Pawn:
				if board.piece_at(x - 1, y).turn_double_moved == board.turn - 1:
					valid_moves.append(Move(board,(x, y), (x - 1, y + y_dir), (x - 1, y)))
		for move in valid_moves:
			if self.team == WHITE and move.dest[1] == 0 or self.team == BLACK and move.dest[1] == 7:
				move.must_promote = True
				move.team = self.team
		return valid_moves

	def move(self, board, x, y, dx, dy):
		super().move(board, x, y, dx, dy)
		if abs(y - dy) == 2:
			self.turn_double_moved = board.turn


class Board:
	pieces = [[None] * 8 for i in range(8)]
	turn = 0
	money = [300, 400]
	income = [0,0]
	rent = [0,0]
	tile_values = [[0] * 8 for i in range(8)]
	tile_teams = [[-1] * 8 for i in range(8)]
	turns = []
	
	def __init__(self):
		team = BLACK
		for y in range(0,8):
			if y > 1:
				team = WHITE
			if y == 1 or y == 6:
				for x in range(0,8):
					self.pieces[x][y] = Pawn(team)
			if y == 0 or y == 7:
				pass
				self.pieces[0][y] = make_piece(ROOK, team)
				self.pieces[1][y] = make_piece(KNIGHT, team)
				self.pieces[2][y] = make_piece(BISHOP, team)
				self.pieces[3][y] = make_piece(QUEEN, team)
				self.pieces[4][y] = make_piece(KING, team)
				self.pieces[5][y] = make_piece(BISHOP, team)
				self.pieces[6][y] = make_piece(KNIGHT, team)
				self.pieces[7][y] = make_piece(ROOK, team)
		for x in range(0,8):
			for y in range(0,8):
				self.tile_values[x][y] = int(4.5 - max(abs(x - 3.5), abs(y - 3.5)))
		self.update_income()
		
		
	def piece_at(self, x,y):
		if x < 0 or y < 0 or x >= 8 or y >= 8:
			return None
		return self.pieces[x][y]
	
	def tile_safe(self, x, y, team):
		for i in range(0,8):
			for j in range(0,8):
				p = self.pieces[i][j]
				if p == None:
					continue
				if p.team != team:
					if any(m.dest[0] == x and m.dest[1] == y\
							for m in p.get_threatened_tiles(i,j,self)):
						return False
		return True
		
		
	def test_move(self, m):
		team = self.pieces[m.loc[0]][m.loc[1]].team
		captured = self.pieces[m.dest[0]][m.dest[1]]
		self.pieces[m.dest[0]][m.dest[1]] = self.pieces[m.loc[0]][m.loc[1]]
		self.pieces[m.loc[0]][m.loc[1]] = None
		destroyed = None
		if len(m.swap_to) == 2:
			self.pieces[m.swap_to[0]][m.swap_to[1]] = self.pieces[m.swap_from[0]][m.swap_from[1]]
			self.pieces[m.swap_from[0]][m.swap_from[1]] = None
		if len(m.destroy) == 2:
			destroyed = self.pieces[m.destroy[0]][m.destroy[1]]
			self.pieces[m.destroy[0]][m.destroy[1]] = None
		
		in_check = self.in_check(team)

		if len(m.destroy) == 2:
			self.pieces[m.destroy[0]][m.destroy[1]] = destroyed
		if len(m.swap_to) == 2:
			self.pieces[m.swap_from[0]][m.swap_from[1]] = self.pieces[m.swap_to[0]][m.swap_to[1]]
			self.pieces[m.swap_to[0]][m.swap_to[1]] = None
		self.pieces[m.loc[0]][m.loc[1]] = self.pieces[m.dest[0]][m.dest[1]]
		self.pieces[m.dest[0]][m.dest[1]] = captured
		return len(in_check) == 0
	

	def find_king(self, team):
		king = None
		for i in range(0,8):
			for j in range(0,8):
				if type(self.pieces[i][j]) is King and self.pieces[i][j].team == team:
					return (i,j)
		return (-1,-1)
		
	#Returns the location of the king of the team's king is in check, otherwise returns () to 
	#indicate that the king is not in check
	def in_check(self, team):
		king = self.find_king(team)
		in_check = False
		for i in range(0,8):
			for j in range(0,8):
				if not self.pieces[i][j] is None and self.pieces[i][j].team != team:
					if any(move.dest[0] == king[0] and move.dest[1] == king[1]\
							for move in self.pieces[i][j].get_threatened_tiles(i,j,self)):
						return king
		return ()
		
	def get_legal_moves_from(self, x, y):
		if self.pieces[x][y] == None or self.pieces[x][y].team != self.get_team_moving():
			return []
		return list(filter(self.test_move, self.pieces[x][y].get_valid_moves(x,y,self)))
	def get_expensive_moves_from(self, x, y):
		if self.pieces[x][y] == None or self.pieces[x][y].team != self.get_team_moving():
			return []
		return list(filter(self.test_move, self.pieces[x][y].get_expensive_moves(x,y,self)))
	
	def get_team_moving(self):
		if self.turn % 2 == 0:
			return WHITE
		return BLACK
	
	def do_move(self, m):
		self.turns.append(Turn(m))
		print(m)
		team = self.pieces[m.loc[0]][m.loc[1]].team
		self.pieces[m.loc[0]][m.loc[1]].move(self, m.loc[0], m.loc[1], m.dest[0], m.dest[1])
		if m.must_promote:
			self.pieces[m.dest[0]][m.dest[1]] = m.promote_to
		else:
			self.pieces[m.dest[0]][m.dest[1]] = self.pieces[m.loc[0]][m.loc[1]]
		self.pieces[m.loc[0]][m.loc[1]] = None
		
			
		if len(m.swap_to) == 2:
			self.pieces[m.swap_to[0]][m.swap_to[1]] = self.pieces[m.swap_from[0]][m.swap_from[1]]
			self.pieces[m.swap_from[0]][m.swap_from[1]] = None
		if len(m.destroy) == 2:
			self.pieces[m.destroy[0]][m.destroy[1]] = None
			
		self.turn += 1
		self.money[team] -= m.cost
		self.money[1 - team] += m.cost
		self.update_income()
		self.money[team] += self.income[team]
		self.money[team] -= self.rent[team]
		self.money[1 - team] += self.rent[team]
		return team
	
	def undo_move(self, m):
		team = self.pieces[m.dest[0]][m.dest[1]].team
		
	def update_income(self):
		self.income[WHITE] = self.calc_income(WHITE)
		self.income[BLACK] = self.calc_income(BLACK)
		self.rent[WHITE] = self.calc_rent(WHITE)
		self.rent[BLACK] = self.calc_rent(BLACK)
		
	#Checks if the game is over when it is get_team_moving()'s move.
	#Returns 3 if the other te am has ran out of money.
	#Returns 2 if team is in checkmate.
	#Returns 1 if team has no legal moves but is not in check (stalemate).
	#Returns 0 if tema has legal moves.
	def is_game_over(self):
		for x in range(0,8):
			for y in range(0,8):
				if len(self.get_legal_moves_from(x, y)) > 0:
					return 0
		if self.money[self.get_team_moving()] < self.rent[self.get_team_moving()]:
			return 3
		if len(self.in_check(self.get_team_moving())) > 0:
			return 2
		return 1
	#Calculates the income for that team based on the pieces they have.
	#Pieces get 3% of the tile value for purchased tiles, and 2% for neutral tiles
	#per each point they are worth.
	#Normal pieces are given their standard chess value.
	#Kings are worth 15 for the purposes of this.
	def calc_income(self, team):
		income = 0
		for x in range(0,8):
			for y in range(0,8):
				income += self.tile_income((x, y), team)
		return income
		
	#Returns the income that team draws from the tile
	def tile_income(self, loc, team, p = None):
		x = loc[0]
		y = loc[1]
		if p == None:
			p = self.piece_at(x, y)
		if p != None and p.team == team and\
				(self.tile_teams[x][y] == team or self.tile_teams[x][y] == NO_TEAM):
			multiplier = 2
			if self.tile_teams[x][y] == team:
				multiplier = 3
			val = 1
			if p.image == 5:
				val = 5
			elif p.image == 3 or p.image == 4:
				val = 3
			elif p.image == 2:
				val = 9
			elif p.image == 1:
				val = 15
			return multiplier * val * self.tile_values[x][y]
		return 0
		
	#Calculates the amount of money paid to the opponent due to pieces that are sitting in tiles 
	#that they have purchased
	def calc_rent(self, team):
		rent = 0
		for x in range(0,8):
			for y in range(0,8):
				p = self.piece_at(x,y)
				if p != None and p.team == team and self.tile_teams[x][y] != NO_TEAM\
						and self.tile_teams[x][y] != team:
					rent += RENT_COST * self.tile_values[x][y]
		return rent
	
	#Determines the set of tiles that a player could purchase after their turn
	#This is just the set of tiles that they have a piece on, that is not already on a team
	#and that they have enough money to purachase
	def get_purchaseable_tiles(self, team):
		tiles = []
		for x in range(0,8):
			for y in range(0,8):
				if self.can_purchase_tile((x,y), team):
					tiles.append((x,y))
		return tiles
	
	#Returns whether or not the team has enough money to purchase the tile
	def can_purchase_tile(self, tile, team):
		x,y = tile[0],tile[1]
		if self.tile_teams[x][y] == NO_TEAM:
			p = self.piece_at(x,y)
			if p != None and p.team == team and self.tile_values[x][y] * TPC <= self.money[team]:
				return True
		return False
	#Flips tile to the desired team and subtracts the money from their balance
	def purchase_tile(self, tile, team):
		self.turns[-1].purchases.append(tile)
		self.money[team] -= self.tile_values[tile[0]][tile[1]] * TPC
		self.tile_teams[tile[0]][tile[1]] = team
		self.update_income()
	
	#Refunds the tile and sets it back to neutral
	#Currently just used to undo moves
	def unpurchase_tile(self, tile, team):
		self.money[team] += self.tile_values[tile[0]][tile[1]] * TPC
		self.tile_teams[tile[0]][tile[1]] = NO_TEAM
		self.update_income()
	
	def tile_rent(self, tile, team):
		x,y = tile[0],tile[1]
		if self.tile_teams[x][y] != NO_TEAM and self.tile_teams[x][y] != team:
			return RENT_COST * self.tile_values[x][y]
		return 0
