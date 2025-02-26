# api/app.py
from flask import Flask, render_template, request, redirect, url_for, session
import random

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

def generate_empty_board(rows, cols):
    return [[{'isMine': False, 'isRevealed': False, 'isFlagged': False, 'adjacentMines': 0} 
             for _ in range(cols)] for _ in range(rows)]

def place_mines(board, num_mines, rows, cols):
    mines_placed = 0
    while mines_placed < num_mines:
        r = random.randint(0, rows - 1)
        c = random.randint(0, cols - 1)
        if not board[r][c]['isMine']:
            board[r][c]['isMine'] = True
            mines_placed += 1

def calculate_adjacents(board, rows, cols):
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    for r in range(rows):
        for c in range(cols):
            if board[r][c]['isMine']:
                board[r][c]['adjacentMines'] = -1
                continue
            count = 0
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc]['isMine']:
                    count += 1
            board[r][c]['adjacentMines'] = count

def init_game(rows, cols, num_mines):
    board = generate_empty_board(rows, cols)
    place_mines(board, num_mines, rows, cols)
    calculate_adjacents(board, rows, cols)
    return board

def flood_fill(board, r, c, rows, cols):
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            cell = board[nr][nc]
            if not cell['isRevealed'] and not cell['isMine']:
                cell['isRevealed'] = True
                if cell['adjacentMines'] == 0:
                    flood_fill(board, nr, nc, rows, cols)

@app.route('/')
def index():
    rows = 10
    cols = 10
    num_mines = 10
    if 'board' not in session:
        board = init_game(rows, cols, num_mines)
        session['board'] = board
        session['game_over'] = False
        session['game_won'] = False
    else:
        board = session['board']
    return render_template(
        'index.html', 
        board=board, 
        rows=rows, 
        cols=cols, 
        game_over=session.get('game_over', False), 
        game_won=session.get('game_won', False)
    )


@app.route('/reveal', methods=['POST'])
def reveal():
    rows = 10
    cols = 10
    num_mines = 10
    board = session.get('board')
    if board is None:
        return redirect(url_for('index'))
    r = int(request.form.get('r'))
    c = int(request.form.get('c'))
    cell = board[r][c]
    if cell['isRevealed'] or cell['isFlagged']:
        return redirect(url_for('index'))
    cell['isRevealed'] = True
    if cell['isMine']:
        session['game_over'] = True
        # Reveal all mines
        for i in range(rows):
            for j in range(cols):
                if board[i][j]['isMine']:
                    board[i][j]['isRevealed'] = True
    elif cell['adjacentMines'] == 0:
        flood_fill(board, r, c, rows, cols)
    # Check win condition: all non-mine cells revealed
    revealed_count = sum(1 for row in board for cell in row if cell['isRevealed'])
    if revealed_count == rows * cols - num_mines:
        session['game_won'] = True
    session['board'] = board
    return redirect(url_for('index'))

@app.route('/flag', methods=['POST'])
def flag():
    board = session.get('board')
    if board is None:
        return redirect(url_for('index'))
    r = int(request.form.get('r'))
    c = int(request.form.get('c'))
    cell = board[r][c]
    if not cell['isRevealed']:
        cell['isFlagged'] = not cell['isFlagged']
    session['board'] = board
    return redirect(url_for('index'))

@app.route('/restart')
def restart():
    session.pop('board', None)
    session.pop('game_over', None)
    session.pop('game_won', None)
    return redirect(url_for('index'))

# Expose the Flask app as "app" so Vercel can use it as the serverless function entrypoint.
if __name__ == '__main__':
    app.run()
