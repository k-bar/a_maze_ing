"""keyboard codes config for MiniLibX dedicated for Linux platform (X11)"""

KEY_1 = 49
KEY_2 = 50
KEY_3 = 51
KEY_4 = 52
KEY_5 = 53

N_KEY_1 = 65436
N_KEY_2 = 65433
N_KEY_3 = 65435
N_KEY_4 = 65430
N_KEY_5 = 65437
N_KEY_6 = 65432
N_KEY_7 = 65429
N_KEY_8 = 65431
N_KEY_9 = 65434

KEY_R = 114
KEY_W = 119
KEY_K = 107
KEY_P = 112
KEY_D = 100
KEY_A = 97
KEY_B = 98

KEY_UP = 65362
KEY_DOWN = 65364
KEY_LEFT = 65361
KEY_RIGHT = 65363

SPACE = 32
KEY_ENTER = 65293
KEY_ESC = 65307

# Event for closing windows by cross
MLX_EVENT_DESTROY = 17
MLX_MASK_NO_MASK = 0

KEY_MAP = {
    KEY_1: "regen",
    N_KEY_1: "regen",
    KEY_4: "quit",
    N_KEY_4: "quit",
    KEY_ESC: "quit",
    KEY_5: "hide_toggle",
    N_KEY_5: "hide_toggle",
    KEY_3: "cycle_color",
    N_KEY_3: "cycle_color",
    SPACE: "pause",
    KEY_RIGHT: "skip",
    KEY_A: "cycle_maze_generator"
}
