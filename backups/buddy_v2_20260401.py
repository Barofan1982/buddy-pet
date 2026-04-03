#!/usr/bin/env python3
"""
Buddy 2.0 — 宠物养成版
基于 Claude Code src/buddy/ 泄露结构重建，加入完整养成系统
"""

import hashlib, json, random, sys, time, tkinter as tk
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageTk

# 打包成 exe 后 __file__ 指向临时目录，需用 sys.executable 获取 exe 所在目录
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

SAVE_FILE = BASE_DIR / '.buddy_save.json'

# ── 游戏常量 ──────────────────────────────────────────────────────
STAMINA_MAX            = 100
HP_MAX                 = 100
HP_DECAY_PER_SEC       = 1 / 60      # 宠物 HP：-1点/分钟
STAMINA_REGEN_PER_SEC  = 1  / 300    # 玩家体力：+1点/5分钟
PET_COST               = 5           # 抚摸消耗体力
FEED_COST              = 10          # 喂食消耗体力
FEED_HP                = 30          # 喂食恢复宠物 HP
REVIVE_COST            = 30          # 唤醒消耗体力
REVIVE_HP              = 30          # 唤醒恢复宠物 HP

# ── 物种配置（emoji 渲染，彻底告别 ASCII 丑态）────────────────────
SPECIES = {
    'duck':     {'emoji': '🦆', 'bg': '#1a3a1a', 'glow': '#2d6e2d', 'cn': '鸭鸭'},
    'cat':      {'emoji': '🐱', 'bg': '#3a2010', 'glow': '#7a4020', 'cn': '猫猫'},
    'ghost':    {'emoji': '👻', 'bg': '#1a1a3a', 'glow': '#3a3a7a', 'cn': '小鬼'},
    'robot':    {'emoji': '🤖', 'bg': '#1a1a22', 'glow': '#3a3a55', 'cn': '机器人'},
    'capybara': {'emoji': '🐹', 'bg': '#2e1e00', 'glow': '#6b4800', 'cn': '水豚'},
    'blob':     {'emoji': '👾', 'bg': '#1a1a4a', 'glow': '#3030aa', 'cn': '史莱姆'},
    'penguin':  {'emoji': '🐧', 'bg': '#10203a', 'glow': '#1a4080', 'cn': '企鹅'},
    'dragon':   {'emoji': '🐲', 'bg': '#3a0a0a', 'glow': '#8a1010', 'cn': '小龙'},
    'owl':      {'emoji': '🦉', 'bg': '#1e0a3a', 'glow': '#4a1a80', 'cn': '猫头鹰'},
    'mushroom': {'emoji': '🍄', 'bg': '#3a2000', 'glow': '#8a4400', 'cn': '蘑菇'},
    'snail':    {'emoji': '🐌', 'bg': '#1a2e00', 'glow': '#3a6600', 'cn': '蜗牛'},
    'axolotl':  {'emoji': '🦎', 'bg': '#003a3a', 'glow': '#006a6a', 'cn': '美西螈'},
    'rabbit':   {'emoji': '🐰', 'bg': '#2e1030', 'glow': '#6a2070', 'cn': '兔子'},
    'turtle':   {'emoji': '🐢', 'bg': '#003a00', 'glow': '#006600', 'cn': '乌龟'},
    'octopus':  {'emoji': '🐙', 'bg': '#00103a', 'glow': '#002080', 'cn': '章鱼'},
    'cactus':   {'emoji': '🌵', 'bg': '#1a3000', 'glow': '#3a6600', 'cn': '仙人掌'},
    'chonk':    {'emoji': '😸', 'bg': '#2e2e00', 'glow': '#6a6a00', 'cn': '肥猫'},
}
SPECIES_LIST = list(SPECIES.keys())

HATS = {
    'none': '', 'crown': '👑', 'tophat': '🎩', 'halo': '✨',
    'wizard': '🪄', 'beanie': '🧢', 'tinyduck': '🐥', 'propeller': '🌀',
}
HATS_LIST = list(HATS.keys())

RARITIES       = ['common', 'uncommon', 'rare', 'epic', 'legendary']
RARITY_WEIGHTS = [60, 25, 10, 4, 1]
RARITY_CN      = {'common':'普通','uncommon':'罕见','rare':'稀有','epic':'史诗','legendary':'传说'}
RARITY_COLOR   = {'common':'#999','uncommon':'#5c5','rare':'#49f','epic':'#c4f','legendary':'#fa0'}
RARITY_FLOOR   = {'common':5,'uncommon':20,'rare':40,'epic':60,'legendary':80}
STAT_NAMES     = ['调试力','耐心值','混沌度','智慧值','毒舌度']

AFFECTION_TIERS = [(0,'陌生人'),(10,'点头之交'),(30,'朋友'),(60,'好友'),(100,'挚友'),(200,'灵魂伴侣')]

# ── PRNG Mulberry32（来自 companion.ts）──────────────────────────
def _prng(seed: int):
    seed &= 0xFFFFFFFF
    def _n() -> float:
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        z = seed
        z = ((z ^ (z >> 15)) * ((z | 1) & 0xFFFFFFFF)) & 0xFFFFFFFF
        z = (z ^ (z + ((z ^ (z >> 7)) * ((z | 61) & 0xFFFFFFFF)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((z ^ (z >> 14)) & 0xFFFFFFFF) / 0xFFFFFFFF
    return _n

def _wt(items, weights, rng):
    r, acc = rng() * sum(weights), 0
    for item, w in zip(items, weights):
        acc += w
        if r < acc: return item
    return items[-1]

def generate_companion(nickname: str) -> dict:
    seed = int(hashlib.md5(nickname.encode()).hexdigest()[:8], 16)
    rng  = _prng(seed)
    sp   = SPECIES_LIST[int(rng() * len(SPECIES_LIST))]
    rar  = _wt(RARITIES, RARITY_WEIGHTS, rng)
    hat  = HATS_LIST[int(rng() * len(HATS_LIST))]
    fl   = RARITY_FLOOR[rar]
    vals = [int(fl + rng() * (100 - fl)) for _ in STAT_NAMES]
    pk   = int(rng() * len(STAT_NAMES))
    dm   = (pk + 1 + int(rng() * (len(STAT_NAMES) - 1))) % len(STAT_NAMES)
    vals[pk] = min(100, vals[pk] + 20)
    vals[dm] = max(1,   vals[dm] - 20)
    return {'species': sp, 'rarity': rar, 'hat': hat,
            'stats': dict(zip(STAT_NAMES, vals))}

# ── 存档 ─────────────────────────────────────────────────────────
def new_save(nickname: str) -> dict:
    return {
        'nickname':       nickname,
        'companion':      generate_companion(nickname),
        'affection':      0,
        'pet_hp':         float(HP_MAX),
        'player_stamina': float(STAMINA_MAX),
        'last_tick':      time.time(),
    }

def load_save():
    if SAVE_FILE.exists():
        try:    return json.loads(SAVE_FILE.read_text('utf-8'))
        except: return None
    return None

def save_game(data: dict):
    SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')

def do_tick(data: dict) -> dict:
    now     = time.time()
    elapsed = now - data.get('last_tick', now)
    data['last_tick'] = now
    if data['pet_hp'] > 0:
        data['pet_hp'] = max(0.0, data['pet_hp'] - elapsed * HP_DECAY_PER_SEC)
    data['player_stamina'] = min(float(STAMINA_MAX),
                                 data['player_stamina'] + elapsed * STAMINA_REGEN_PER_SEC)
    return data

# ── 对话系统 ─────────────────────────────────────────────────────
_D = {
    'fainted': [
        "……{nick}……救……我……",
        "好黑……好饿……（请消耗30体力唤醒）",
        "……Zzz……",
        "（昏迷中，需要唤醒）",
    ],
    'hungry': {
        'duck':     ["呱！呱！！呱！！！（饿得抓狂）",
                     "再不喂我我就去路边捡面包屑了！！"],
        'cat':      ["哼，我才不是在乞食……只是胃有点不舒服。",
                     "（肚子叫了一声）……你没听见。"],
        'ghost':    ["哦～～～饿～～～我要飘走了～～～",
                     "死都死了还要饿肚子，太惨了。"],
        'robot':    ["警告：燃料告急。重复——燃料告急——重复——",
                     "系统降频运行中……效率仅剩8%……"],
        'capybara': ["……饿……（眼神空洞）",
                     "（缓慢举起爪子）……吃的……"],
        'blob':     ["嗷嗷嗷！！我在溶化！！！",
                     "咕噜咕噜……（肚子叫）"],
        'penguin':  ["尊敬的主人，请允许本人提醒：已处于饥饿状态。",
                     "鄙人……已饥。（表情严肃）"],
        'dragon':   ["本龙要饿死了！快喂！！",
                     "再不喂我我就去烤外卖了！！"],
        'owl':      ["经过分析，本人已饥饿较长时间。",
                     "咕——（是饿的那种咕）"],
        'mushroom': ["吃！吃！吃！！",
                     "不喂我我就长孢子了！！"],
        'snail':    ["……饿……（缓慢移动）……饿……",
                     "……食物……在哪……"],
        'rabbit':   ["啊！我要饿死了！！（过激反应）",
                     "主人！！！！我好饿！！！！"],
        'chonk':    ["……饿……（懒得动但确实很饿）",
                     "……肚子空了……很严重……"],
        'cactus':   ["我……渴了……（其实是饿了）",
                     "水分告急。（一脸冷漠但很紧张）"],
        'default':  ["好饿！！", "主人你要饿死我吗！", "喂！！！"],
    },
    'normal': {
        'duck':     ["呱！", "今天天气不错！（摇摆）", "有没有面包屑？", "呱！（满足）"],
        'cat':      ["别看我。（转头）", "嗯哼。", "你来了啊。（装不在意）", "喵。"],
        'ghost':    ["哦～～～（飘来飘去）", "你有没有感觉背后有凉风？那是我。"],
        'robot':    ["系统运行正常。", "检测到主人在线。", "今日任务：发呆。完成度：100%。"],
        'capybara': ["……（发呆）", "（眯眼晒太阳）", "嗯……挺好的。", "随便。"],
        'blob':     ["咕噜～", "我是液态的！今天也是！", "摸我！摸我！"],
        'penguin':  ["您好。", "一切正常。", "请保持社交距离。（仅限他人）"],
        'dragon':   ["哼！", "本龙今日心情尚可。", "（翻翻翅膀）你来了？"],
        'owl':      ["嗯……（深思）", "有些事情值得思考。", "咕——"],
        'mushroom': ["孢子！孢子！", "我在长大！你看出来没？", "嘿嘿嘿。"],
        'snail':    ["（缓慢转过来）……你……好……", "……（又缓慢转回去了）"],
        'axolotl':  ["（好奇地盯着你）", "这是什么？那是什么？", "好玩！"],
        'rabbit':   ["（警觉地看你）", "……你不会突然动吧？", "啊！（啥都没发生）"],
        'turtle':   ["……（无执念）……", "缓缓呼气……", "心静自然凉。"],
        'octopus':  ["八条腿，八个想法。", "（同时做了六件事）", "我血是蓝色的，酷吧。"],
        'cactus':   ["别靠太近。（浑身是刺）", "我其实……挺温柔的。（是吗）"],
        'chonk':    ["（躺着）", "（还在躺着）", "吃了睡，睡了吃。"],
        'default':  ["你好！", "嗨！", "（看着你）", "……"],
    },
    'happy': {
        'duck':     ["呱呱呱！！你是最棒的主人！！", "（原地蹦跶）呱！！！！"],
        'cat':      ["……（蹭了一下你的手，假装是不小心的）",
                     "哼……你今天还不错嘛。（别过脸去）"],
        'ghost':    ["嘿嘿嘿～你真的看得见我！！好开心！",
                     "爱你爱你爱你！（穿墙而过）"],
        'robot':    ["检测到高好感度。建议：继续当前行为。——（内部日志：嘿嘿嘿）",
                     "heart.exe 已启动。"],
        'capybara': ["（慢慢露出微笑）……嗯……你挺好的。",
                     "（拍拍你）……"],
        'blob':     ["啊啊啊啊！！！（变成心形）",
                     "超级喜欢你！！！！！！"],
        'penguin':  ["鄙人……颇感欣慰。（耳朵红了）",
                     "非常愉快。（表情严肃但眼睛弯弯的）"],
        'dragon':   ["本龙……允许你再摸一次。",
                     "哼！才……才不是因为喜欢你！"],
        'chonk':    ["（懒洋洋翻个身，把肚皮朝上）", "……嘿……（闭眼）"],
        'default':  ["喜欢你！！", "嘿嘿！", "你最好了！"],
    },
    'jokes': [
        "为什么程序员总是分不清万圣节和圣诞节？\n因为 OCT 31 = DEC 25。",
        "程序员老婆让他去买排骨，说有鸡蛋就买一打。\n他买了一打排骨回来，因为有鸡蛋。",
        "git commit -m '终于修好了'\ngit commit -m '刚才说早了'\ngit commit -m '放弃了'",
        "面试官：你最大的缺点是什么？\n我：太诚实了。\n面试官：这不算缺点吧？\n我：我不在乎你怎么想。",
        "世界上有10种人：懂二进制的和不懂二进制的。",
        "为什么后端程序员不喜欢出门？\n因为外面没有 localhost。",
        "测试工程师走进一家酒吧：\n点了1杯，点了0杯，点了-1杯，点了2147483647杯……\n酒吧崩溃了。",
        "我的代码没有 bug，只有未发现的特性。",
        "调了三小时 bug，发现少了个分号。\n\n……沉默。",
        "产品经理：这个需求很简单，就是……\n程序员（两周后）：……",
        "问：如何让程序员心情好？\n答：Code review 通过。\n问：如何让程序员崩溃？\n答：Code review 时说「这里加个注释就好了」。",
        "有个笑话叫「程序员准时下班」，哈哈哈。\n……呵。",
    ],
}

def _pick(species: str, pool: dict) -> str:
    lines = pool.get(species, pool.get('default', ['……']))
    return random.choice(lines)

def pick_dialogue(data: dict) -> str:
    sp  = data['companion']['species']
    hp  = data['pet_hp']
    aff = data['affection']
    if hp <= 0:
        return random.choice(_D['fainted']).replace('{nick}', data['nickname'])
    if aff >= 10 and random.random() < 0.2:
        return random.choice(_D['jokes'])
    if hp < 30:
        return _pick(sp, _D['hungry'])
    if aff >= 60:
        return _pick(sp, _D['happy'])
    return _pick(sp, _D['normal'])

def aff_label(n: int) -> str:
    lbl = AFFECTION_TIERS[0][1]
    for t, l in AFFECTION_TIERS:
        if n >= t: lbl = l
    return lbl

# ── UI 常量 ──────────────────────────────────────────────────────
BG   = '#12121e'
BG2  = '#1e1e30'
FG   = '#e0e0e0'
FGD  = '#55556a'
CW   = 308   # canvas width
CH   = 170   # canvas height
WW   = 340   # window width

FONT_TITLE = ('Microsoft YaHei', 14, 'bold')
FONT_BODY  = ('Microsoft YaHei', 10)
FONT_SMALL = ('Microsoft YaHei', 9)
FONT_STS   = ('Segoe UI Emoji', 20)
FONT_HRT   = ('Segoe UI Emoji', 18)

# ── PIL emoji 渲染 ────────────────────────────────────────────────
_EMOJI_FONT_CACHE: dict = {}

def _emoji_font(size: int) -> ImageFont.FreeTypeFont:
    if size not in _EMOJI_FONT_CACHE:
        try:
            _EMOJI_FONT_CACHE[size] = ImageFont.truetype(
                r'C:\Windows\Fonts\seguiemj.ttf', size)
        except Exception:
            _EMOJI_FONT_CACHE[size] = ImageFont.load_default()
    return _EMOJI_FONT_CACHE[size]

def _hex_rgb(h: str) -> tuple:
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def _lighten(rgb: tuple, amt: int = 70) -> tuple:
    return tuple(min(255, c + amt) for c in rgb)

def _draw_glow(draw: ImageDraw.Draw, cx: int, cy: int, glow_rgb: tuple):
    outer = _lighten(glow_rgb, 20)
    inner = _lighten(glow_rgb, 60)
    draw.ellipse([cx-78, cy-68, cx+78, cy+68], fill=outer + (180,))
    draw.ellipse([cx-58, cy-50, cx+58, cy+50], fill=inner + (220,))

def _draw_capybara(draw: ImageDraw.Draw, cx: int, cy: int):
    """PIL 手绘水豚脸，因为 Unicode 没有水豚 emoji。"""
    BR  = (139, 90,  43)   # 主体棕
    LBR = (175, 125, 65)   # 浅棕（吻部/耳内）
    DBR = ( 80,  45, 10)   # 深棕（轮廓/眼）
    WHT = (255, 255, 255)
    PNK = (210, 140, 110)

    # 耳朵
    for ex in [cx-38, cx+18]:
        draw.ellipse([ex, cy-60, ex+22, cy-36], fill=BR,    outline=DBR, width=2)
        draw.ellipse([ex+4, cy-56, ex+18, cy-40], fill=PNK)

    # 头部（大圆）
    draw.ellipse([cx-52, cy-42, cx+52, cy+46], fill=BR, outline=DBR, width=2)

    # 吻部（宽扁椭圆）
    draw.ellipse([cx-32, cy+5, cx+32, cy+42], fill=LBR, outline=DBR, width=2)

    # 眼睛
    for ex in [cx-22, cx+10]:
        draw.ellipse([ex, cy-22, ex+14, cy-8], fill=DBR)
        draw.ellipse([ex+2, cy-20, ex+6, cy-16], fill=WHT)

    # 鼻孔
    for nx in [cx-10, cx+4]:
        draw.ellipse([nx, cy+10, nx+8, cy+18], fill=DBR)

    # 嘴巴
    draw.arc([cx-18, cy+18, cx+18, cy+38], 10, 170, fill=DBR, width=3)

# ── 自定义绘制函数（species → callable）────────────────────────────
CUSTOM_DRAW = {
    'capybara': _draw_capybara,
}

def make_pet_image(emoji: str, bg_hex: str, glow_hex: str,
                   w: int = 308, h: int = 170,
                   species: str = '',
                   emoji_size: int = 88) -> ImageTk.PhotoImage:
    """用 PIL 将宠物渲染为真彩图。自定义物种走手绘，其余走 emoji 渲染。"""
    bg_rgb   = _hex_rgb(bg_hex)
    glow_rgb = _hex_rgb(glow_hex)

    img  = Image.new('RGBA', (w, h), bg_rgb + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    _draw_glow(draw, cx, cy, glow_rgb)

    if species in CUSTOM_DRAW:
        CUSTOM_DRAW[species](draw, cx, cy)
    else:
        font = _emoji_font(emoji_size)
        bbox = draw.textbbox((0, 0), emoji, font=font, embedded_color=True)
        ex = cx - (bbox[2] - bbox[0]) // 2 - bbox[0]
        ey = cy - (bbox[3] - bbox[1]) // 2 - bbox[1]
        draw.text((ex, ey), emoji, font=font, embedded_color=True)

    return ImageTk.PhotoImage(img)

# ── 主程序 ──────────────────────────────────────────────────────
class BuddyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('✦ 我的宠物')
        self.configure(bg=BG)
        self.resizable(False, False)
        self._data       = None
        self._anim_fr    = 0
        self._canvas     = None
        self._pet_item   = None   # canvas image item（PIL 渲染）
        self._pet_photo  = None   # 必须持有引用，防止 GC 回收
        self._sts_item   = None
        self._bars       = {}
        self._aff_lbl    = None
        self._speech_lbl = None
        self._btn_action = None
        self._btn_feed   = None
        self._start()

    # ── 启动 ─────────────────────────────────────────────────────
    def _start(self):
        data = load_save()
        if data is None:
            self._show_login()
        else:
            self._data = do_tick(data)
            save_game(self._data)
            self._build_main()

    # ── 登录界面 ─────────────────────────────────────────────────
    def _show_login(self):
        f = tk.Frame(self, bg=BG)
        f.pack(expand=True, pady=50, padx=30)

        tk.Label(f, text='✦  欢迎  ✦', bg=BG, fg='#ffcc44',
                 font=FONT_TITLE).pack(pady=(0, 10))
        tk.Label(f, text='输入昵称，召唤你的专属宠物', bg=BG, fg=FGD,
                 font=FONT_SMALL).pack(pady=(0, 6))
        tk.Label(f, text='（同一昵称永远对应同一只宠物）', bg=BG, fg=FGD,
                 font=FONT_SMALL).pack(pady=(0, 14))

        var = tk.StringVar()
        entry = tk.Entry(f, textvariable=var, font=('Microsoft YaHei', 13),
                         bg=BG2, fg=FG, insertbackground=FG,
                         relief='flat', width=16, justify='center')
        entry.pack(ipady=6)
        entry.focus()

        def confirm(_=None):
            nick = var.get().strip()
            if not nick: return
            self._data = new_save(nick)
            save_game(self._data)
            f.destroy()
            self._build_main()

        entry.bind('<Return>', confirm)
        tk.Button(f, text='召  唤', command=confirm,
                  bg='#2a2a50', fg=FG, font=FONT_BODY,
                  relief='flat', padx=24, pady=6, cursor='hand2',
                  activebackground='#3a3a70', activeforeground=FG).pack(pady=12)

    # ── 主界面 ──────────────────────────────────────────────────
    def _build_main(self):
        d  = self._data
        sp = d['companion']['species']
        sd = SPECIES[sp]

        # 顶部：昵称 + 稀有度 + 物种
        top = tk.Frame(self, bg=BG)
        top.pack(fill='x', padx=16, pady=(12, 4))
        tk.Label(top, text=d['nickname'], bg=BG, fg=FG,
                 font=('Microsoft YaHei', 12, 'bold')).pack(side='left')
        rar = d['companion']['rarity']
        tk.Label(top, text=f"【{RARITY_CN[rar]}】", bg=BG,
                 fg=RARITY_COLOR[rar],
                 font=('Microsoft YaHei', 10, 'bold')).pack(side='left', padx=6)
        tk.Label(top, text=sd['cn'], bg=BG, fg=FGD,
                 font=FONT_SMALL).pack(side='left')

        # 帽子标签（右上角）
        hat_e = HATS.get(d['companion']['hat'], '')
        if hat_e:
            tk.Label(top, text=hat_e, bg=BG,
                     font=('Segoe UI Emoji', 16)).pack(side='right')

        # 宠物画布（PIL 真彩渲染）
        canvas = tk.Canvas(self, width=CW, height=CH, bg=sd['bg'],
                           highlightthickness=1, highlightbackground='#2a2a4a',
                           cursor='hand2')
        canvas.pack(padx=16, pady=4)
        self._canvas = canvas

        # 首次渲染宠物图片
        self._pet_photo = make_pet_image(sd['emoji'], sd['bg'], sd.get('glow', '#333355'),
                                         w=CW, h=CH, species=sp)
        self._pet_item  = canvas.create_image(CW // 2, CH // 2,
                                              image=self._pet_photo, anchor='center')
        self._sts_item  = canvas.create_text(CW // 2, CH - 14, text='',
                                             font=FONT_STS, anchor='center')
        canvas.bind('<Button-1>', lambda e: self._do_pet())

        # 对话气泡
        self._speech_lbl = tk.Label(self, text='', bg=BG, fg='#88ccff',
                                    font=('Microsoft YaHei', 10, 'italic'),
                                    wraplength=WW - 32, justify='center')
        self._speech_lbl.pack(pady=(2, 2))

        # 状态条
        bars_frame = tk.Frame(self, bg=BG)
        bars_frame.pack(fill='x', padx=16, pady=(0, 4))
        for label, key, max_v, color in [
            ('❤ 好感', 'affection',      200, '#ff6699'),
            ('HP',    'pet_hp',          100, '#44cc66'),
            ('体力',  'player_stamina',  100, '#4499ff'),
        ]:
            row = tk.Frame(bars_frame, bg=BG)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=label, bg=BG, fg=FGD,
                     font=FONT_SMALL, width=5, anchor='w').pack(side='left')
            track = tk.Frame(row, bg='#2a2a3e', height=8, width=180)
            track.pack(side='left', padx=4)
            track.pack_propagate(False)
            fill = tk.Frame(track, bg=color, height=8)
            fill.place(x=0, y=0, height=8, width=0)
            val_lbl = tk.Label(row, text='—', bg=BG, fg=FGD,
                               font=FONT_SMALL, width=9, anchor='w')
            val_lbl.pack(side='left')
            self._bars[key] = (fill, val_lbl, track, max_v)

        # 好感关系标签
        self._aff_lbl = tk.Label(self, text='', bg=BG, fg='#cc88ff',
                                  font=FONT_SMALL)
        self._aff_lbl.pack(pady=(0, 4))

        # 体力恢复提示
        self._regen_lbl = tk.Label(self, text='体力每5分钟回复1点', bg=BG, fg=FGD,
                                    font=('Microsoft YaHei', 8))
        self._regen_lbl.pack(pady=(0, 4))

        # 按钮区
        btns = tk.Frame(self, bg=BG)
        btns.pack(pady=8)

        def _b(text, cmd):
            return tk.Button(btns, text=text, command=cmd,
                             bg='#252540', fg=FG, font=FONT_SMALL,
                             relief='flat', padx=10, pady=5, cursor='hand2',
                             activebackground='#353560', activeforeground=FG)

        _b('💬 说话', self._do_speak).pack(side='left', padx=4)
        self._btn_action = _b('💗 抚摸 -5体力', self._do_pet)
        self._btn_action.pack(side='left', padx=4)
        self._btn_feed = _b('🍖 喂食 -10体力', self._do_feed)
        self._btn_feed.pack(side='left', padx=4)

        # 初始刷新
        self._refresh()
        self.after(150, self._update_bars)
        self._animate()
        self._auto_tick()

    # ── 刷新界面状态 ─────────────────────────────────────────────
    def _refresh(self):
        if not self._data or not self._canvas:
            return
        d       = self._data
        hp      = d['pet_hp']
        st      = d['player_stamina']
        aff     = d['affection']
        fainted = (hp <= 0)
        sp_e    = SPECIES[d['companion']['species']]['emoji']

        # 宠物图片（PIL 真彩，状态切换时重新渲染）
        sd      = SPECIES[d['companion']['species']]
        sp_key  = d['companion']['species']
        e_emoji = '💤' if fainted else sp_e
        # 昏迷时强制用 emoji（💤），否则走物种自定义绘制或 emoji
        self._pet_photo = make_pet_image(
            e_emoji, sd['bg'], sd.get('glow', '#333355'),
            w=CW, h=CH,
            species='' if fainted else sp_key)
        self._canvas.itemconfig(self._pet_item, image=self._pet_photo)
        # 状态图标（文字叠加）
        if fainted:       sts = '😵'
        elif hp < 30:     sts = '😰'
        elif aff >= 100:  sts = '😍'
        else:             sts = ''
        self._canvas.itemconfig(self._sts_item, text=sts)

        # 按钮切换：昏迷时显示唤醒，否则显示抚摸/喂食
        if fainted:
            self._btn_action.config(
                text=f'⚡ 唤醒 -{REVIVE_COST}体力',
                command=self._do_revive,
                state='normal' if st >= REVIVE_COST else 'disabled')
            self._btn_feed.config(state='disabled')
        else:
            self._btn_action.config(
                text=f'💗 抚摸 -{PET_COST}体力',
                command=self._do_pet,
                state='normal' if st >= PET_COST else 'disabled')
            hp_full = d['pet_hp'] >= 70
            self._btn_feed.config(
                text='🍖 喂食 -10体力' if not hp_full else '🍖 吃饱了',
                command=self._do_feed,
                state='normal' if (st >= FEED_COST and not hp_full) else 'disabled')

        # 好感标签
        if self._aff_lbl:
            self._aff_lbl.config(
                text=f'关系：{aff_label(aff)}  （已抚摸 {aff} 次）')

    def _update_bars(self):
        if not self._data: return
        d = self._data
        for key, (fill, lbl, track, max_v) in self._bars.items():
            val = d[key]
            track.update_idletasks()
            w = track.winfo_width() or 180
            fill.place(x=0, y=0, height=8,
                       width=int(w * min(val, max_v) / max_v))
            if key == 'affection':
                lbl.config(text=f'{int(val)}')
            else:
                lbl.config(text=f'{int(val)}/{max_v}')

    # ── 动画 ─────────────────────────────────────────────────────
    def _animate(self):
        self._anim_fr = (self._anim_fr + 1) % 8
        if self._pet_item and self._data and self._data['pet_hp'] > 0:
            offsets = [0, -2, -3, -4, -3, -2, 0, 0]
            off = offsets[self._anim_fr]
            self._canvas.coords(self._pet_item, CW // 2, CH // 2 + off)
        self.after(220, self._animate)

    def _float_hearts(self):
        cx  = CW // 2
        items = []
        for _ in range(3):
            x = cx + random.randint(-35, 35)
            h = self._canvas.create_text(
                x, 95, anchor='center',
                text=random.choice(['❤️', '💕', '💗', '✨']),
                font=FONT_HRT)
            items.append(h)
        def _up(n):
            if n <= 0:
                for i in items: self._canvas.delete(i)
                return
            for i in items: self._canvas.move(i, 0, -4)
            self.after(55, lambda: _up(n - 1))
        _up(14)

    # ── 自动滴答（每10秒存盘+刷新）──────────────────────────────
    def _auto_tick(self):
        self._data = do_tick(self._data)
        save_game(self._data)
        self._refresh()
        self._update_bars()
        self.after(10_000, self._auto_tick)

    # ── 操作 ─────────────────────────────────────────────────────
    def _do_pet(self):
        d = self._data
        if d['pet_hp'] <= 0:
            self._say('（它昏迷着呢，先唤醒吧）'); return
        if d['player_stamina'] < PET_COST:
            self._say('体力不足，休息一下再来～'); return
        d['player_stamina'] -= PET_COST
        d['affection']      += 1
        self._float_hearts()
        self._speech_lbl.config(text='')   # 清空上一条对话
        self.after(300, lambda: self._say(pick_dialogue(d)))
        self._refresh(); self._update_bars(); save_game(d)

    def _do_feed(self):
        d = self._data
        if d['pet_hp'] >= 70:
            self._say('吃饱了，不要再喂了！'); return
        if d['player_stamina'] < FEED_COST:
            self._say('体力不足，等等再喂吧'); return
        d['player_stamina'] -= FEED_COST
        d['pet_hp']         = min(HP_MAX, d['pet_hp'] + FEED_HP)
        d['affection']      += 1
        self._say('（津津有味地吃东西，好感+1）')
        self._refresh(); self._update_bars(); save_game(d)

    def _do_revive(self):
        d = self._data
        if d['player_stamina'] < REVIVE_COST:
            self._say(f'体力不足，需要 {REVIVE_COST} 点'); return
        d['player_stamina'] -= REVIVE_COST
        d['pet_hp'] = float(REVIVE_HP)
        self._say('……（缓缓睁开眼睛）……你来了啊……')
        self._refresh(); self._update_bars(); save_game(d)

    def _do_speak(self):
        self._say(pick_dialogue(self._data))

    def _say(self, text: str):
        self._speech_lbl.config(text=text)


if __name__ == '__main__':
    BuddyApp().mainloop()
