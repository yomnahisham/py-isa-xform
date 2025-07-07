import pygame
import sys

# ========== Constants ==========
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
TILE_SIZE = 16
ROWS = SCREEN_HEIGHT // TILE_SIZE  # 15
COLS = SCREEN_WIDTH // TILE_SIZE   # 20

TILE_MAP_ADDR = 0xF000
TILE_DATA_ADDR = 0xF200
PALETTE_ADDR = 0xFA00

# ========== Palette Reader ==========
def get_palette(memory):
    palette = []
    for i in range(16):
        byte = memory[PALETTE_ADDR + i]
        r = ((byte >> 5) & 0b111) * 255 // 7
        g = ((byte >> 2) & 0b111) * 255 // 7
        b = (byte & 0b11) * 255 // 3
        palette.append((r, g, b))
    return palette

# ========== Tile Reader ==========
def get_tile(memory, tile_index):
    base = TILE_DATA_ADDR + tile_index * 128
    pixels = []
    for i in range(128):
        byte = memory[base + i]
        pixels.append(byte & 0x0F)
        pixels.append((byte >> 4) & 0x0F)
    return pixels

# ========== Draw Screen ==========
def draw_screen(screen, memory):
    palette = get_palette(memory)
    for row in range(ROWS):
        for col in range(COLS):
            tile_index = memory[TILE_MAP_ADDR + row * COLS + col]
            tile_pixels = get_tile(memory, tile_index)
            for y in range(TILE_SIZE):
                for x in range(TILE_SIZE):
                    color_index = tile_pixels[y * TILE_SIZE + x]
                    color = palette[color_index]
                    screen.set_at((col * TILE_SIZE + x, row * TILE_SIZE + y), color)

# ========== Public Function ==========
def run_graphics(memory):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ZX16 Graphics Display")
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        draw_screen(screen, memory)
        pygame.display.flip()
        clock.tick(30)
