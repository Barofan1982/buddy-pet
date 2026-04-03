#!/usr/bin/env python3
"""
Buddy — Claude Code 伴侣精灵本地复刻版
基于泄露的 src/buddy/ 模块结构重建
"""

import hashlib
import random
import tkinter as tk
from tkinter import font as tkfont

# ─────────────────────────────────────────────────────────────────
#  原始数据 (来自 types.ts)
# ─────────────────────────────────────────────────────────────────

EYES = ['·', '✦', '×', '◉', '@', '°', '♥', '★']

HATS_LIST = ['none', 'crown', 'tophat', 'propeller', 'halo', 'wizard', 'beanie', 'tinyduck']

RARITIES    = ['common', 'uncommon', 'rare', 'epic', 'legendary']
RARITY_WEIGHTS = [60, 25, 10, 4, 1]
RARITY_COLORS  = {
    'common':    '#999999',
    'uncommon':  '#55cc55',
    'rare':      '#4499ff',
    'epic':      '#cc44ff',
    'legendary': '#ffaa00',
}
RARITY_FLOORS = {'common': 5, 'uncommon': 20, 'rare': 40, 'epic': 60, 'legendary': 80}

STAT_NAMES = ['DEBUGGING', 'PATIENCE', 'CHAOS', 'WISDOM', 'SNARK']

# ─────────────────────────────────────────────────────────────────
#  精灵 ASCII 图 (基于 sprites.ts 结构重建)
#  每帧 6 行: 第 0 行 = 帽子槽, 第 1-5 行 = 身体
#  {E} → 眼睛字符 (1 char)
# ─────────────────────────────────────────────────────────────────

BODIES = {
    'duck': [
        [' ',
         '   <({E} ^)>  ',
         '    (====)    ',
         '     \\__/    ',
         '    _/ \\_ ',
         '~~~~~~~~~~~~~~~'],
        [' ',
         '   <({E} -)>  ',
         '    (====)    ',
         '     \\__/    ',
         '    _/ \\_ ',
         '               '],
        [' ',
         '   <({E} ^)>  ',
         '    (====)    ',
         '     \\__/    ',
         '    _/ \\_ ',
         '~~ splash! ~~~'],
    ],
    'cat': [
        [' ',
         '   /\\_/\\    ',
         '  ({E}  {E}) ',
         '   (  w  )   ',
         '    |   |    ',
         '   _|___|_   '],
        [' ',
         '   /\\-/\\    ',
         '  ({E}  {E}) ',
         '   (  w  )   ',
         '    |   |    ',
         '   _|___|_   '],
        [' ',
         '   /\\_/\\    ',
         '  ({E}  {E}) ',
         '   ( ~w~ )   ',
         '   (|   |)   ',
         '   _|___|_   '],
    ],
    'ghost': [
        [' ',
         '    _____    ',
         '   ({E} {E}) ',
         '   ( ooo )   ',
         '    \\___/   ',
         '   /|   |\\  '],
        [' ',
         '    _____    ',
         '   ({E} {E}) ',
         '   ( ooo )   ',
         '    \\___/   ',
         '  / |   | \\ '],
        [' ',
         '    _____    ',
         '   ({E} {E}) ',
         '   ( OOO )   ',
         '    \\___/   ',
         '   ~|boo|~   '],
    ],
    'robot': [
        [' ',
         '   [_____]   ',
         '   |{E} {E}| ',
         '   | === |   ',
         '   |_____|   ',
         '   _/   \\_  '],
        [' ',
         '   [_____]   ',
         '   |{E} {E}| ',
         '   | =*= |   ',
         '   |_____|   ',
         '   _/   \\_  '],
        [' ',
         ' *-[_____]-* ',
         '   |{E} {E}| ',
         '   | === |   ',
         '   |_____|   ',
         '   _/   \\_  '],
    ],
    'capybara': [
        [' ',
         '   (_____)   ',
         '   ({E} {E}) ',
         '   ( ~~~~ )  ',
         '   |_| |_|   ',
         '  /  | |  \\ '],
        [' ',
         '   (_____)   ',
         '   ({E} {E}) ',
         '   ( ~~~~ )  ',
         '   |_| |_|   ',
         ' ~ /  | |  ~ '],
        [' ',
         '   (_____)   ',
         '  ({E}^ {E}) ',
         '   ( ~~~~ )  ',
         '   |_| |_|   ',
         '  /  | |  \\ '],
    ],
    'blob': [
        [' ',
         '    _____    ',
         '   (     )   ',
         '  ( {E}{E} ) ',
         '   (  u  )   ',
         '    \\___/   '],
        [' ',
         '    _____    ',
         '   (     )   ',
         '  ( {E}{E} ) ',
         '   ( ~u~ )   ',
         '    \\___/   '],
        [' ',
         '    ______   ',
         '   (      )  ',
         '  ( {E}{E} ) ',
         '   (  u  )   ',
         '    \\____/  '],
    ],
    'penguin': [
        [' ',
         '   _______   ',
         '  ({E}   {E})',
         '   (  v  )   ',
         '   /|   |\\  ',
         '  /_|___|_\\ '],
        [' ',
         '   _______   ',
         '  ({E}   {E})',
         '   (  v  )   ',
         '  / |   | \\ ',
         '  \\_|___|_/ '],
        [' ',
         '   _______   ',
         '  ({E}   {E})',
         '   (  v  )   ',
         '   /|   |\\  ',
         ' ~~_|___|_~~ '],
    ],
    'dragon': [
        [' ',
         '  /\\    /\\  ',
         ' ({E}    {E})',
         '  ( fire! )  ',
         '   \\    /   ',
         '   /\\  /\\  '],
        [' ',
         '  /\\    /\\  ',
         ' ({E}    {E})',
         '  ( FIRE! )  ',
         '   \\    /   ',
         '  ~/\\  /\\~ '],
        [' ',
         '*-/\\    /\\-*',
         ' ({E}    {E})',
         ' (FIRE!!!!!) ',
         '   \\    /   ',
         '  ~/\\  /\\~ '],
    ],
    'owl': [
        [' ',
         '   /\\ /\\    ',
         '  ({E}  {E}) ',
         '   ( OwO )   ',
         '    |   |    ',
         '   _|___|_   '],
        [' ',
         '   /\\ /\\    ',
         '  ({E}  {E}) ',
         '   ( OwO )   ',
         '   (|   |)   ',
         '   _|___|_   '],
        [' ',
         '   /\\ /\\    ',
         '  ({E}-  {E})',
         '   ( -w- )   ',
         '    |   |    ',
         '   _|___|_   '],
    ],
    'mushroom': [
        [' ',
         '    _____    ',
         '   /·   ·\\  ',
         '  ({E}   {E})',
         '   |_____|   ',
         '   \\_____/  '],
        [' ',
         '    _____    ',
         '   / ·  ·\\  ',
         '  ({E}   {E})',
         '   |_____|   ',
         '   \\_____/  '],
        [' ',
         '  * _____  * ',
         '   /·   ·\\  ',
         '  ({E}   {E})',
         '   |_____|   ',
         '  *\\_____/* '],
    ],
    'snail': [
        [' ',
         '    ____     ',
         '   /    \\   ',
         '  ( {E}{E})  ',
         ' /~~~~~~~\\  ',
         '  \\______/  '],
        [' ',
         '    ____     ',
         '   /    \\   ',
         '  ( {E}{E})  ',
         '/~~~~~~~\\.  ',
         '  \\______/  '],
        [' ',
         '    ~~~~     ',
         '   / ~~ \\   ',
         '  ( {E}{E})  ',
         '~/~~~~~~~\\~ ',
         '  \\______/  '],
    ],
    'axolotl': [
        [' ',
         ' vv  ({E})  vv',
         '  (  {E}   ) ',
         '  ( ~gill~ ) ',
         '   |     |   ',
         '~~~/|   |\\~~'],
        [' ',
         ' vv  ({E})  vv',
         '  (  {E}   ) ',
         '  ( ~gill~ ) ',
         '   |     |   ',
         '   /|   |\\  '],
        [' ',
         'vvv  ({E}) vvv',
         '  (  {E}   ) ',
         '  (~~gill~~) ',
         '   |     |   ',
         '~~~/|   |\\~~'],
    ],
    'chonk': [
        [' ',
         '  /\\_______/\\',
         ' ({E}       {E})',
         ' (   chonk   )',
         '  \\_________/',
         '  /  |   |  \\'],
        [' ',
         '  /\\_______/\\',
         ' ({E}       {E})',
         ' (  CHONK!!  )',
         '  \\_________/',
         '  /  |   |  \\'],
        [' ',
         '  /\\_______/\\',
         ' ({E}  z  z {E})',
         ' (  chonk... )',
         '  \\_________/',
         '  /  |   |  \\'],
    ],
}

HAT_LINES = {
    'none':      None,
    'crown':     '     vVVv    ',
    'tophat':    '    _____    ',
    'propeller': '    -/-\\-   ',
    'halo':      '    (~~~)    ',
    'wizard':    '     /\\     ',
    'beanie':    '   _(___     ',
    'tinyduck':  '   <(^)>     ',
}

SPECIES_LIST = list(BODIES.keys())

SPEECH_LINES = [
    "hello!",
    "...",
    "pet me?",
    "beep boop",
    ">:3",
    "zzzz",
    "woof?",
    "hi!!",
    ":D",
    "*exists*",
    "debug mode",
    "1+1=?",
    "feed me",
    "nya~",
    "honk!",
    "i am here",
    "*wiggles*",
    "...ok",
    "let's code",
    "chaos!!",
]

# ─────────────────────────────────────────────────────────────────
#  PRNG & 生成逻辑 (来自 companion.ts — Mulberry32)
# ─────────────────────────────────────────────────────────────────

def _mulberry32(seed: int):
    seed = seed & 0xFFFFFFFF
    def _next() -> float:
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        z = seed
        z = ((z ^ (z >> 15)) * ((z | 1) & 0xFFFFFFFF)) & 0xFFFFFFFF
        z = (z ^ (z + ((z ^ (z >> 7)) * ((z | 61) & 0xFFFFFFFF)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((z ^ (z >> 14)) & 0xFFFFFFFF) / 0xFFFFFFFF
    return _next


def _hash_seed(user_id: str) -> int:
    return int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)


def _weighted_pick(items, weights, rng):
    total = sum(weights)
    r = rng() * total
    acc = 0
    for item, w in zip(items, weights):
        acc += w
        if r < acc:
            return item
    return items[-1]


def roll_companion(user_id: str | None = None) -> dict:
    if user_id is None:
        user_id = str(random.randint(0, 0xFFFFFF))
    rng   = _mulberry32(_hash_seed(user_id))
    species = SPECIES_LIST[int(rng() * len(SPECIES_LIST))]
    rarity  = _weighted_pick(RARITIES, RARITY_WEIGHTS, rng)
    eye     = EYES[int(rng() * len(EYES))]
    hat     = HATS_LIST[int(rng() * len(HATS_LIST))]
    floor   = RARITY_FLOORS[rarity]
    vals    = [int(floor + rng() * (100 - floor)) for _ in STAT_NAMES]
    peak    = int(rng() * len(STAT_NAMES))
    dump    = (peak + 1 + int(rng() * (len(STAT_NAMES) - 1))) % len(STAT_NAMES)
    vals[peak] = min(100, vals[peak] + 20)
    vals[dump] = max(1,   vals[dump] - 20)
    return {
        'user_id': user_id,
        'species': species,
        'rarity':  rarity,
        'eye':     eye,
        'hat':     hat,
        'stats':   dict(zip(STAT_NAMES, vals)),
    }


def render_frame(companion: dict, frame: int) -> list[str]:
    frames = BODIES[companion['species']]
    lines  = [l.replace('{E}', companion['eye']) for l in frames[frame % 3]]
    hat_line = HAT_LINES.get(companion['hat'])
    if hat_line:
        lines[0] = hat_line
    return lines

# ─────────────────────────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────────────────────────

BG       = '#12121e'
BG2      = '#1e1e30'
FG       = '#e0e0e0'
FG_DIM   = '#666680'
ACCENT   = '#4466ff'

class BuddyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('✦ Buddy')
        self.configure(bg=BG)
        self.resizable(False, False)

        self._companion  = None
        self._frame_idx  = 0
        self._speech_job = None
        self._pet_job    = None

        self._build()
        self._roll()
        self.after(100, self._update_bars)   # 等布局完成再画进度条
        self._tick()

    # ── 构建界面 ──────────────────────────────────────────────────

    def _build(self):
        mono = ('Courier New', 14)

        # 标题
        tk.Label(self, text='✦  B U D D Y  ✦', bg=BG, fg='#ffcc44',
                 font=('Courier New', 13, 'bold')).pack(pady=(14, 2))

        # 物种 & 稀有度
        self._lbl_name = tk.Label(self, text='', bg=BG, fg=FG,
                                  font=('Courier New', 11, 'bold'))
        self._lbl_name.pack()

        # 精灵显示区
        self._sprite = tk.Text(self, width=18, height=7, bg=BG2, fg=FG,
                               font=('Courier New', 16), relief='flat',
                               cursor='hand2', state='disabled',
                               selectbackground=BG2)
        self._sprite.pack(padx=24, pady=(8, 4))
        self._sprite.bind('<Button-1>', self._on_pet)

        # 对话气泡
        self._lbl_speech = tk.Label(self, text='', bg=BG, fg='#88ccff',
                                    font=('Courier New', 11, 'italic'))
        self._lbl_speech.pack(pady=(0, 6))

        # 属性栏
        stats_box = tk.Frame(self, bg=BG)
        stats_box.pack(padx=24, fill='x')
        self._bars: dict[str, tuple] = {}
        stat_colors = ['#4488ff', '#44cc88', '#ff6644', '#ccaa44', '#cc44cc']
        for i, stat in enumerate(STAT_NAMES):
            row = tk.Frame(stats_box, bg=BG)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=stat[:3], bg=BG, fg=FG_DIM,
                     font=('Courier New', 9), width=4, anchor='w').pack(side='left')
            track = tk.Frame(row, bg='#2a2a40', height=8, width=160)
            track.pack(side='left', padx=4)
            track.pack_propagate(False)
            fill = tk.Frame(track, bg=stat_colors[i], height=8)
            fill.place(x=0, y=0, height=8, width=0)
            val_lbl = tk.Label(row, text='—', bg=BG, fg=FG_DIM,
                               font=('Courier New', 9), width=3)
            val_lbl.pack(side='left')
            self._bars[stat] = (fill, val_lbl, track)

        # 按钮行
        btns = tk.Frame(self, bg=BG)
        btns.pack(pady=12)
        _btn = lambda parent, text, cmd: tk.Button(
            parent, text=text, command=cmd,
            bg='#252540', fg=FG, activebackground='#353560',
            activeforeground=FG, font=('Courier New', 10),
            relief='flat', padx=10, pady=5, cursor='hand2')
        _btn(btns, '🎲  Roll',   self._roll   ).pack(side='left', padx=6)
        _btn(btns, '💬  Speak',  self._speak  ).pack(side='left', padx=6)
        _btn(btns, '❤  Pet',    self._do_pet ).pack(side='left', padx=6)

    # ── 逻辑 ──────────────────────────────────────────────────────

    def _roll(self):
        self._companion = roll_companion()
        self._frame_idx = 0
        self._clear_speech()
        rarity = self._companion['rarity']
        color  = RARITY_COLORS[rarity]
        hat    = self._companion['hat']
        hat_tag = f'[{hat}]' if hat != 'none' else ''
        self._lbl_name.config(
            text=f"{self._companion['species'].upper()}  {hat_tag}  [{rarity.upper()}]",
            fg=color)
        self._render()
        self._update_bars()

    def _render(self):
        if not self._companion:
            return
        lines = render_frame(self._companion, self._frame_idx)
        self._sprite.config(state='normal')
        self._sprite.delete('1.0', 'end')
        for line in lines:
            self._sprite.insert('end', line + '\n')
        self._sprite.config(state='disabled')

    def _tick(self):
        self._frame_idx = (self._frame_idx + 1) % 3
        self._render()
        self.after(600, self._tick)

    def _update_bars(self):
        if not self._companion:
            return
        for stat, val in self._companion['stats'].items():
            fill, lbl, track = self._bars[stat]
            track.update_idletasks()
            w = track.winfo_width() or 160
            fill.place(x=0, y=0, height=8, width=int(w * val / 100))
            lbl.config(text=str(val))

    def _speak(self):
        msg = random.choice(SPEECH_LINES)
        self._show_speech(f'"{msg}"')

    def _on_pet(self, _event):
        self._do_pet()

    def _do_pet(self):
        self._show_speech('♥  ♥  ♥')

    def _show_speech(self, text: str):
        self._clear_speech()
        self._lbl_speech.config(text=text)
        self._speech_job = self.after(3000, self._clear_speech)

    def _clear_speech(self):
        if self._speech_job:
            self.after_cancel(self._speech_job)
            self._speech_job = None
        self._lbl_speech.config(text='')


# ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = BuddyApp()
    app.mainloop()
