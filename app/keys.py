"""keyboard codes config for MiniLibX dedicated for Linux platform (X11)"""

KEY_0 = 48
KEY_1 = 49
KEY_2 = 50
KEY_3 = 51
KEY_4 = 52
KEY_5 = 53
KEY_6 = 54
KEY_7 = 55
KEY_8 = 56
KEY_9 = 57

N_KEY_0 = 65435
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
KEY_S = 115
KEY_W = 119
KEY_K = 107
KEY_P = 112
KEY_D = 100
KEY_A = 97
KEY_B = 98
KEY_C = 99

KEY_H = 104
KEY_N = 110

KEY_Q = 113

KEY_UP = 65362
KEY_DOWN = 65364
KEY_LEFT = 65361
KEY_RIGHT = 65363

KEY_PLUS = 61
KEY_MINUS = 45
KEY_N_PLUS = 65451
KEY_N_MINUS = 65453

BACKSPACE = 65288
SPACE = 32
KEY_ENTER = 65293
KEY_N_ENTER = 65421
KEY_ESC = 65307
KEY_TAB = 65289
KEY_END = 65367

# Event for closing windows by cross
MLX_EVENT_CLIENT_MESSAGE = 33
MLX_EVENT_CONFIGURE = 22
MLX_MASK_STRUCTURE_NOTIFY = 1 << 17  # 131072
MLX_EVENT_DESTROY = 17
MLX_MASK_NO_MASK = 0

KEY_MAP = {
    KEY_0: "digit_0",
    KEY_1: "digit_1",
    KEY_2: "digit_2",
    KEY_3: "digit_3",
    KEY_4: "digit_4",
    KEY_5: "digit_5",
    KEY_6: "digit_6",
    KEY_7: "digit_7",
    KEY_8: "digit_8",
    KEY_9: "digit_9",

    N_KEY_0: "digit_0",
    N_KEY_1: "digit_1",
    N_KEY_2: "digit_2",
    N_KEY_3: "digit_3",
    N_KEY_4: "digit_4",
    N_KEY_5: "digit_5",
    N_KEY_6: "digit_6",
    N_KEY_7: "digit_7",
    N_KEY_8: "digit_8",
    N_KEY_9: "digit_9",

    KEY_PLUS: "speed_up",
    KEY_MINUS: "speed_down",
    KEY_N_PLUS: "speed_up",
    KEY_N_MINUS: "speed_down",

    KEY_ESC: "quit",
    KEY_Q: "quit",
    SPACE: "pause",
    KEY_END: "skip",
    KEY_ENTER: "enter_action",
    KEY_N_ENTER: "enter_action",
    BACKSPACE: "seed_backspace",
    KEY_A: "cycle_maze_generator",
    KEY_S: "cycle_solver",
    KEY_K: "activate_seed_input",
    KEY_H: "hide_toggle",
    KEY_P: "toggle_perfect",
    KEY_R: "regen",
    KEY_N: "randomize_seed",

    KEY_C: "cycle_palette",

    KEY_TAB: "toggle_arrow_mode",

    KEY_LEFT: "move_left",
    KEY_RIGHT: "move_right",
    KEY_UP: "move_up",
    KEY_DOWN: "move_down"
}
