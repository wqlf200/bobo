#!/usr/bin/env python3
"""俄罗斯方块 - 使用 pygame 实现"""

from __future__ import annotations

import random
import sys

import pygame

# 网格尺寸
COLS = 10
ROWS = 20
CELL = 30

# 窗口尺寸
SIDEBAR = 180
WIDTH = COLS * CELL + SIDEBAR
HEIGHT = ROWS * CELL

# 颜色
BLACK = (15, 15, 25)
GRAY = (40, 40, 55)
WHITE = (240, 240, 245)
GRID_COLOR = (30, 30, 45)

COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (180, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

# 七种方块形状（相对坐标）
SHAPES = {
    "I": [(0, 1), (1, 1), (2, 1), (3, 1)],
    "O": [(1, 0), (2, 0), (1, 1), (2, 1)],
    "T": [(1, 0), (0, 1), (1, 1), (2, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}


class Piece:
    def __init__(self, kind: str | None = None):
        self.kind = kind or random.choice(list(SHAPES.keys()))
        self.color = COLORS[self.kind]
        self.cells = [list(c) for c in SHAPES[self.kind]]
        self.x = COLS // 2 - 2
        self.y = 0

    def rotated_cells(self, direction: int = 1) -> list[list[int]]:
        """direction: 1=顺时针, -1=逆时针"""
        if self.kind == "O":
            return [c[:] for c in self.cells]

        pivot = self.cells[0]
        px, py = pivot
        rotated = []
        for x, y in self.cells:
            dx, dy = x - px, y - py
            if direction == 1:
                rotated.append([px + dy, py - dx])
            else:
                rotated.append([px - dy, py + dx])
        return rotated


class Tetris:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("俄罗斯方块")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22)
        self.big_font = pygame.font.SysFont("arial", 28, bold=True)
        self.reset()

    def reset(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.current = Piece()
        self.next_piece = Piece()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.fall_time = 0
        self.fall_speed = 500  # 毫秒

    def valid(self, cells: list[list[int]], ox: int = 0, oy: int = 0) -> bool:
        for x, y in cells:
            nx, ny = x + self.current.x + ox, y + self.current.y + oy
            if nx < 0 or nx >= COLS or ny >= ROWS:
                return False
            if ny >= 0 and self.board[ny][nx] is not None:
                return False
        return True

    def lock_piece(self):
        for x, y in self.current.cells:
            bx, by = x + self.current.x, y + self.current.y
            if by < 0:
                self.game_over = True
                return
            self.board[by][bx] = self.current.color

        cleared = self.clear_lines()
        if cleared:
            points = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += points.get(cleared, 800) * self.level
            self.lines_cleared += cleared
            self.level = 1 + self.lines_cleared // 10
            self.fall_speed = max(100, 500 - (self.level - 1) * 40)

        self.current = self.next_piece
        self.next_piece = Piece()
        if not self.valid(self.current.cells):
            self.game_over = True

    def clear_lines(self) -> int:
        new_board = [row for row in self.board if any(cell is None for cell in row)]
        cleared = ROWS - len(new_board)
        for _ in range(cleared):
            new_board.insert(0, [None for _ in range(COLS)])
        self.board = new_board
        return cleared

    def move(self, dx: int, dy: int) -> bool:
        if self.valid(self.current.cells, dx, dy):
            self.current.x += dx
            self.current.y += dy
            return True
        return False

    def rotate(self, direction: int = 1):
        rotated = self.current.rotated_cells(direction)
        kicks = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]
        for ox, oy in kicks:
            old = self.current.cells
            self.current.cells = rotated
            if self.valid(self.current.cells, ox, oy):
                self.current.x += ox
                self.current.y += oy
                return
            self.current.cells = old

    def hard_drop(self):
        while self.move(0, 1):
            self.score += 2
        self.lock_piece()

    def update(self, dt: int):
        if self.game_over:
            return
        self.fall_time += dt
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            if not self.move(0, 1):
                self.lock_piece()

    def draw_cell(self, x: int, y: int, color, offset_x: int = 0, offset_y: int = 0, size: int = CELL):
        rect = pygame.Rect(offset_x + x * size + 1, offset_y + y * size + 1, size - 2, size - 2)
        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        highlight = tuple(min(255, c + 40) for c in color)
        pygame.draw.line(self.screen, highlight, rect.topleft, rect.topright, 2)
        pygame.draw.line(self.screen, highlight, rect.topleft, rect.bottomleft, 2)

    def draw_board(self):
        board_rect = pygame.Rect(0, 0, COLS * CELL, HEIGHT)
        pygame.draw.rect(self.screen, BLACK, board_rect)

        for y in range(ROWS):
            for x in range(COLS):
                pygame.draw.rect(
                    self.screen,
                    GRID_COLOR,
                    (x * CELL, y * CELL, CELL, CELL),
                    1,
                )
                if self.board[y][x]:
                    self.draw_cell(x, y, self.board[y][x])

        for x, y in self.current.cells:
            self.draw_cell(x + self.current.x, y + self.current.y, self.current.color)

    def draw_sidebar(self):
        sidebar_x = COLS * CELL
        pygame.draw.rect(self.screen, GRAY, (sidebar_x, 0, SIDEBAR, HEIGHT))

        texts = [
            ("分数", str(self.score)),
            ("等级", str(self.level)),
            ("消行", str(self.lines_cleared)),
        ]
        y = 30
        for label, value in texts:
            self.screen.blit(self.font.render(label, True, WHITE), (sidebar_x + 20, y))
            self.screen.blit(self.big_font.render(value, True, COLORS["I"]), (sidebar_x + 20, y + 24))
            y += 70

        self.screen.blit(self.font.render("下一个", True, WHITE), (sidebar_x + 20, y))
        preview_x = sidebar_x + 50
        preview_y = y + 30
        for x, y_cell in self.next_piece.cells:
            self.draw_cell(x, y_cell, self.next_piece.color, preview_x, preview_y, 20)

        help_y = HEIGHT - 200
        help_lines = [
            "操作说明:",
            "← →  移动",
            "↑    旋转",
            "↓    加速下落",
            "空格  瞬间下落",
            "R    重新开始",
            "Esc  退出",
        ]
        for i, line in enumerate(help_lines):
            self.screen.blit(self.font.render(line, True, WHITE), (sidebar_x + 15, help_y + i * 24))

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            msg = self.big_font.render("游戏结束!", True, WHITE)
            hint = self.font.render("按 R 重新开始", True, WHITE)
            self.screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

    def draw(self):
        self.draw_board()
        self.draw_sidebar()
        pygame.display.flip()

    def handle_key(self, key: int):
        if key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

        if key == pygame.K_r:
            self.reset()
            return

        if self.game_over:
            return

        if key == pygame.K_LEFT:
            self.move(-1, 0)
        elif key == pygame.K_RIGHT:
            self.move(1, 0)
        elif key == pygame.K_DOWN:
            if self.move(0, 1):
                self.score += 1
        elif key == pygame.K_UP:
            self.rotate(1)
        elif key == pygame.K_SPACE:
            self.hard_drop()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

            self.update(dt)
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    Tetris().run()
