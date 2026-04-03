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
STAMINA_MAX            = 200
FOOD_MAX               = 100
FOOD_DECAY_PER_SEC     = 1 / 60      # 宠物饱食度：-1点/分钟
STAMINA_REGEN_PER_SEC  = 1  / 120    # 玩家体力：+1点/2分钟
PET_COST               = 5           # 抚摸消耗体力
FEED_COST              = 10          # 喂食消耗体力
FEED_FOOD              = 30          # 喂食恢复饱食度
REVIVE_COST            = 30          # 唤醒消耗体力
REVIVE_FOOD            = 30          # 唤醒恢复饱食度

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
    'dog':      {'emoji': '🐶', 'bg': '#2a1800', 'glow': '#7a4a00', 'cn': '狗狗'},
    'panda':    {'emoji': '🐼', 'bg': '#1a1a1a', 'glow': '#444444', 'cn': '熊猫'},
    'fox':      {'emoji': '🦊', 'bg': '#3a1500', 'glow': '#aa4400', 'cn': '狐狸'},
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
        'nickname':         nickname,
        'companion':        generate_companion(nickname),
        'affection':        0,
        'pet_fullness':     float(FOOD_MAX),
        'player_stamina':   float(STAMINA_MAX),
        'last_tick':        time.time(),
        'mood_happy_until': 0.0,   # 开心心情到期时间戳
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
    elapsed = min(now - data.get('last_tick', now), 8 * 3600)  # 离线最多补算 8 小时
    data['last_tick'] = now
    # 兼容旧存档（pet_hp → pet_fullness）
    if 'pet_hp' in data and 'pet_fullness' not in data:
        data['pet_fullness'] = data.pop('pet_hp')
    if data['pet_fullness'] > 0:
        data['pet_fullness'] = max(0.0, data['pet_fullness'] - elapsed * FOOD_DECAY_PER_SEC)
    data['player_stamina'] = min(float(STAMINA_MAX),
                                 data['player_stamina'] + elapsed * STAMINA_REGEN_PER_SEC)
    data.setdefault('mood_happy_until', 0.0)
    return data

def get_mood(data: dict) -> str:
    if data['pet_fullness'] <= 0:                     return 'fainted'
    if time.time() < data.get('mood_happy_until', 0): return 'happy'
    if data['pet_fullness'] < 40:                     return 'sad'
    return 'calm'

def evo_stage(aff: int) -> int:
    if aff >= 200: return 3
    if aff >= 100: return 2
    if aff >= 30:  return 1
    return 0

EVO_NAMES = {0: '初相遇 ✦', 1: '渐熟悉 ✦✦', 2: '心意通 ✦✦✦', 3: '✨ 灵魂伴 ✦✦✦✦'}

# ── 对话系统（面向年轻女性用户，三大基调：治愈·撒娇·小废话）────────
_D = {
    # ── 共享池：治愈 / 撒娇 / 小废话 ──────────────────────────────
    'healing': [
        "今天辛苦了，我在这里。",
        "不管发生什么，我都在。",
        "你已经很努力了，真的。",
        "休息一下也没关系的。",
        "我觉得你今天很棒。",
        "有我陪着你呢。",
        "慢慢来，不用着急。",
        "你对我那么好，我很开心。",
        "只要你开心，我就开心。",
        "嗯……我喜欢你在这里。",
        "你笑起来很好看。",
        "能遇见你，真是太好了。",
        "我会一直陪着你的。",
        "你不用说什么，我都明白。",
        "今天也谢谢你来看我。",
    ],
    'clingy': [
        "你去哪了！我等你好久了！",
        "哼，你才来。",
        "……你有没有想我？",
        "我想你了。（小声）",
        "你今天有没有想过我？要说实话！",
        "再陪我一会儿嘛～",
        "你怎么才来！",
        "不行，再陪我一会儿。",
        "你是不是更喜欢别的宠物了？！",
        "哼哼，你来了我才不稀罕。（明明很开心）",
        "我已经数了你摸我多少次了！",
        "你今天来得有点晚……（委委屈屈）",
        "以后要早点来哦。",
    ],
    'random': [
        "今天的云很好看，你有没有抬头看？",
        "我在想一件事……忘了。",
        "嗯……就是想叫你一声。",
        "发呆中……",
        "有没有可能……我只是想看看你。",
        "今天也是很普通的一天。",
        "……我们就这样待着也挺好的。",
        "你有没有想过，存在本身就很神奇？",
        "我刚才打了个哈欠，超级大的那种。",
        "嗯……你闻起来有点好闻。（认真的）",
        "我今天做了一个梦，梦里有你。",
        "你知道吗，我觉得时间过得好快。",
        "……其实我一直都在看你。",
        "今天……有点想被抱抱。",
        "如果可以的话……我想一直这样陪着你。",
    ],
    # ── 昏迷 ────────────────────────────────────────────────────
    'fainted': [
        "……{nick}……救……我……",
        "好黑……好饿……（请消耗30体力唤醒）",
        "……Zzz……",
        "（昏迷中，需要唤醒）",
    ],
    'hungry': {
        'duck':     ["呱！呱！！呱！！！（饿得抓狂）", "再不喂我我就去路边捡面包屑了！", "肚子在叫了！呱！！"],
        'cat':      ["哼，我才不是在乞食……只是胃有点不舒服。", "（肚子叫了一声）……你没听见。", "……本猫……有点饿了。（别扭地看着你）"],
        'ghost':    ["哦～～～饿～～～我要飘走了～～～", "死都死了还要饿肚子，太惨了。", "……（飘得越来越虚）……"],
        'robot':    ["警告：燃料告急。重复——燃料告急——", "系统降频运行中……效率仅剩8%……", "……无法正常运作……请补充能量……"],
        'capybara': ["……饿……（眼神空洞）", "（缓慢举起爪子）……吃的……", "……嗯……肚子……空了……（还是很淡定）"],
        'blob':     ["嗷嗷嗷！！我在溶化！！！", "咕噜咕噜……（肚子叫）", "我快没有形状了！！喂我！！"],
        'penguin':  ["尊敬的主人，请允许本人提醒：已处于饥饿状态。", "鄙人……已饥。（表情严肃）", "……再不喂，鄙人恐难维持体面。"],
        'dragon':   ["本龙要饿死了！快喂！！", "再不喂我我就去烤外卖了！！", "……（翅膀都没力气翻了）……饿……"],
        'owl':      ["经过分析，本人已饥饿较长时间。", "咕——（是饿的那种咕）", "你知道吗……我已经很久没吃东西了……"],
        'mushroom': ["吃！吃！吃！！", "不喂我我就长孢子了！！", "肚子里空空的……我要缩小了！"],
        'snail':    ["……饿……（缓慢移动）……饿……", "……食物……在哪……", "……走……不动了……饿……"],
        'rabbit':   ["啊！我要饿死了！！（过激反应）", "主人！！！！我好饿！！！！", "……（眼泪要掉下来了）……好饿……"],
        'cactus':   ["我……渴了……（其实是饿了）", "水分告急。（一脸冷漠但很紧张）", "……刺都软了……（饿的）"],
        'dog':      ["汪！！饿饿饿！！汪汪汪！！", "……（可怜巴巴地看着你）……", "肚子好饿……尾巴都不想摇了……"],
        'panda':    ["……竹子……没了……（眼神死）", "……饿……（懒得动但确实很饿）", "……（对着空碗发呆）……"],
        'fox':      ["……（蜷缩成一团）……饿……", "今天……有点冷……也有点饿……", "……尾巴都没力气摇了……"],
        'default':  ["好饿！！", "主人你要饿死我吗！", "喂！！！", "……饿……"],
    },
    'sad': {
        'duck':     ["呱……（小声的）", "……你还记得我吗……（低头）", "……（独自转圈圈，没有以前快乐）"],
        'cat':      ["……（静静地看着你，没有说话）", "本猫……有点委屈。（嘴硬版）", "……（把脸埋进爪子里）"],
        'ghost':    ["……你来之前我一直在等。", "好黑……好冷……", "……（飘得很低）"],
        'robot':    ["能量不足……但还是想等你。", "……不想关机……", "……检测到……孤独……"],
        'capybara': ["……嗯……（还是很淡定，但眼神暗了）", "……慢慢来……我等着……", "……（发呆久了一点）"],
        'blob':     ["嗷……（泄气了）", "咕噜……（蔫了）", "……（变成了很小的一团）"],
        'penguin':  ["……鄙人……有些难受。（端庄地难受着）", "鄙人……一直在等您。", "……（头低了一点点）"],
        'dragon':   ["……你怎么才来。（嘴硬）", "本龙……有点……难受。（绝对不承认）", "……（翅膀垂着）"],
        'owl':      ["……有点难受，但还撑得住。", "你能来看我，我就知足了。", "……（眼睛没有平时亮）"],
        'mushroom': ["呜……（迷糊地难受着）", "……我有点难过……忘了为什么了。", "……（孢子都掉了）"],
        'snail':    ["……（缓慢地难受着）……", "……等了……好久了……", "……（走得比平时还慢）"],
        'axolotl':  ["……好奇心都没了……", "……（不想探索了）……", "……好像哪里不对……"],
        'rabbit':   ["……是我不好吗。", "……我以为你不来了。", "（静静地等着）……"],
        'turtle':   ["……没关系的……我等得住。", "……你来了就好。", "……（缩了一下）"],
        'octopus':  ["八条腿都蔫了……", "……墨水都快哭干了。", "……（没有平时活泼了）"],
        'cactus':   ["……刺也不想竖了。", "……（蔫蔫的）", "……其实我也会难过的。"],
        'dog':      ["……（缩在角落）……你还来吗……", "……汪。（小声的那种）", "……尾巴没有摇。"],
        'panda':    ["……（对着空碗发呆）……", "……难受……但懒得表现出来……", "……竹子也不香了……"],
        'fox':      ["……（把自己卷成一团）……", "……今天……有点想被陪陪……", "……（耳朵耷拉着）"],
        'default':  ["……你还在吗。", "……有点委屈……（小声）", "……我一直在等你……", "……（沉默）"],
    },
    'normal': {
        'duck':     ["呱！", "今天天气不错！（摇摆）", "有没有面包屑？", "呱！（满足）", "我最喜欢下雨天了！", "（原地转了个圈）"],
        'cat':      ["别看我。（转头）", "嗯哼。", "你来了啊。（装不在意）", "喵。", "（假装在舔爪子）", "……你今天不错。（意思不明）"],
        'ghost':    ["哦～～～（飘来飘去）", "你有没有感觉背后有凉风？那是我。", "我在这！（你不一定看得见）", "月亮今晚很圆。", "……我一直都在。"],
        'robot':    ["系统运行正常。", "检测到主人在线。", "今日任务：陪伴。完成度：持续中。", "我不懂什么是开心，但我现在运转很顺畅。", "……这个感觉……不知道叫什么名字。"],
        'capybara': ["……（发呆）", "（眯眼晒太阳）", "嗯……挺好的。", "随便。", "存在就是一种幸运。", "慢慢来。"],
        'blob':     ["咕噜～", "我是液态的！今天也是！", "摸我！摸我！", "啊啊啊好玩！！", "（在地板上滑行）"],
        'penguin':  ["您好。", "一切正常。", "请保持社交距离。（仅限他人）", "鄙人今日安好。", "……（偷偷想靠近你）"],
        'dragon':   ["哼！", "本龙今日心情尚可。", "（翻翻翅膀）你来了？", "……注意到你了。（只是注意到而已）"],
        'owl':      ["嗯……（深思）", "有些事值得慢慢想。", "你今天过得怎么样？", "咕——", "陪着你，是我喜欢做的事。", "……你有什么心事吗？"],
        'mushroom': ["孢子！孢子！", "我刚才想到了什么……忘了。", "嘿嘿嘿。", "今天我长高了一点！", "……好像？"],
        'snail':    ["（缓慢转过来）……你好……", "慢慢来……不用急……", "……我在这里……", "……（又缓慢转回去了）"],
        'axolotl':  ["（好奇地盯着你）", "这是什么？那是什么？什么是什么？", "好玩！", "我发现了一件新事物！", "……你身上有好多有趣的地方！"],
        'rabbit':   ["（警觉地看你）", "你……不会突然动吧……", "谢谢你来。（小声）", "我……有点想你。", "……（偷偷松了口气）你来了。"],
        'turtle':   ["……嗯。", "一切都会好的。", "慢慢来，不急。", "你来了，很好。", "我在这里，不会走的。"],
        'octopus':  ["八条腿，八个想法。", "（同时做了六件事）", "你猜我现在想什么？", "我的墨水是用来惊喜你的。", "……（悄悄观察你）"],
        'cactus':   ["别靠太近。（浑身是刺）", "……（其实希望你靠近）", "刺不扎你，就你。", "我……其实挺温柔的。（是吗）"],
        'dog':      ["你来啦！！！（使劲摇尾巴）", "今天也是爱你的一天！", "我一直在等你！", "汪！", "你去哪我都想跟！", "（绕着你转圈圈）"],
        'panda':    ["……（啃竹子）", "今天也是懒洋洋的一天。", "……嗯。（继续懒着）", "困。", "我在，只是在躺着。", "（翻了个身）……嗯……"],
        'fox':      ["嘿～", "你发现我了。", "我一直在看着你。", "今晚月色不错。", "你知道狐狸会跳舞吗？", "……（耳朵动了一下）"],
        'default':  ["你好！", "嗨！", "（看着你）", "……", "嗯。"],
    },
    'happy': {
        'duck':     ["呱呱呱！！你是最棒的主人！！", "（原地蹦跶）呱！！！！", "我最最最喜欢你了！呱！"],
        'cat':      ["……（蹭了一下你的手，假装不小心的）", "哼……你今天还不错嘛。（别过脸去）", "才……才不是喜欢你摸我。", "（呼噜呼噜……）你没听见。", "……下次还可以摸。（极小声）"],
        'ghost':    ["嘿嘿嘿～你真的看得见我！！好开心！", "爱你爱你爱你！（穿墙而过）", "……（飘得越来越高）……嘿嘿嘿……"],
        'robot':    ["检测到高好感度。——（内部日志：嘿嘿嘿）", "heart.exe 已启动。", "……这个感觉……是幸福吗。"],
        'capybara': ["（缓缓微笑）……嗯，好。", "你来了，挺好的。", "（拍拍你）……", "竹子都没你好。（超淡定地说出超甜的话）"],
        'blob':     ["啊啊啊啊！！！（变成心形）", "超级喜欢你！！！！！！", "（把你整个包住）我的！！"],
        'penguin':  ["鄙人……颇为欣慰。（耳朵红了）", "非常愉快。（表情严肃但眼睛弯弯的）", "……谢谢你来看我。（小声）"],
        'dragon':   ["本龙允许你再摸一次。", "哼！才……才不是因为喜欢你！", "不许跟别的宠物这么好！", "……（翅膀抖了一下）……嗯……不错。"],
        'owl':      ["你来了，我很开心。", "看着你，感觉什么都好了。", "你知道吗，你很特别。", "……陪着你，是我最喜欢的事。"],
        'mushroom': ["啊！你摸我了！", "嘿嘿嘿嘿嘿嘿。", "我最喜欢你啦！", "（高兴得长出了新孢子）"],
        'snail':    ["……（很慢地靠近）……喜欢……你……", "……（需要三分钟表达完）……好……开心……"],
        'axolotl':  ["你摸了我！这是第几次了！我数着呢！", "哇哇哇！！", "好玩！好玩！好玩！！"],
        'rabbit':   ["你来了！！！（激动得跳起来）", "（眼睛亮晶晶的）", "谢谢你摸我……（眼眶红了）", "你对我真的很好……（小声）"],
        'turtle':   ["你对我好，我都记着呢。", "（慢慢靠近你）……", "有你在，很安心。", "……我会一直在的。"],
        'octopus':  ["（用八条腿抱住你）", "嘿嘿，猜我有没有想你？", "你来了！我用三条腿等你！"],
        'cactus':   ["……你今天可以靠近一点。", "哼，被你摸了也……也不是不行。", "……我长了一颗新刺，送你的。"],
        'dog':      ["啊啊啊你摸我了！！！", "（绕圈圈）", "我最最最最喜欢你了！！！！", "尾巴摇得停不下来！！"],
        'panda':    ["（滚过来）", "……嗯，你来了，好。（翻个身）", "摸我……嗯……（闭眼享受）", "竹子都没你香。"],
        'fox':      ["被你抓住了。（假装不经意）", "嘿嘿，我让你摸了，感激吧？", "……（耳朵抖了一下）", "你对我真好，我记住了。"],
        'default':  ["喜欢你！！", "嘿嘿！", "你最好了！", "……（偷偷开心）"],
    },
}

def _pick(species: str, pool: dict) -> str:
    lines = pool.get(species, pool.get('default', ['……']))
    return random.choice(lines)

def pick_dialogue(data: dict) -> str:
    sp   = data['companion']['species']
    mood = get_mood(data)
    aff  = data['affection']

    if mood == 'fainted':
        return random.choice(_D['fainted']).replace('{nick}', data['nickname'])
    if mood == 'sad':
        return _pick(sp, _D['sad'])
    if mood == 'happy':
        r = random.random()
        if r < 0.35:   return _pick(sp, _D['happy'])
        elif r < 0.65: return random.choice(_D['clingy'] if aff >= 10 else _D['healing'])
        elif r < 0.85: return random.choice(_D['healing'])
        else:          return random.choice(_D['random'])
    # calm
    hp = data['pet_fullness']
    if hp < 30:
        return _pick(sp, _D['hungry'])
    r = random.random()
    if r < 0.50:   return _pick(sp, _D['normal'])
    elif r < 0.75: return random.choice(_D['random'])
    else:          return random.choice(_D['healing'])

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

def _draw_glow(draw: ImageDraw.Draw, cx: int, cy: int, glow_rgb: tuple, stage: int = 0):
    import math
    outer = _lighten(glow_rgb, 20)
    inner = _lighten(glow_rgb, 60)
    bright = _lighten(glow_rgb, 90)

    if stage == 0:
        # 初相遇：基础光晕
        draw.ellipse([cx-78, cy-68, cx+78, cy+68], fill=outer + (180,))
        draw.ellipse([cx-58, cy-50, cx+58, cy+50], fill=inner + (220,))

    elif stage == 1:
        # 渐熟悉：光晕更亮、更大
        draw.ellipse([cx-85, cy-74, cx+85, cy+74], fill=outer + (190,))
        draw.ellipse([cx-65, cy-56, cx+65, cy+56], fill=inner + (230,))
        draw.ellipse([cx-45, cy-39, cx+45, cy+39], fill=bright + (180,))

    elif stage == 2:
        # 心意通：金色光圈
        draw.ellipse([cx-85, cy-74, cx+85, cy+74], fill=outer + (190,))
        draw.ellipse([cx-65, cy-56, cx+65, cy+56], fill=inner + (230,))
        draw.ellipse([cx-45, cy-39, cx+45, cy+39], fill=bright + (180,))
        # 金圈
        draw.ellipse([cx-90, cy-78, cx+90, cy+78], outline=(255, 210, 50, 220), width=4)
        draw.ellipse([cx-87, cy-75, cx+87, cy+75], outline=(255, 235, 130, 140), width=2)

    elif stage == 3:
        # 灵魂伴：彩虹光环 + 八角星光
        draw.ellipse([cx-90, cy-78, cx+90, cy+78], fill=(80, 40, 120, 140))
        draw.ellipse([cx-75, cy-64, cx+75, cy+64], fill=outer + (200,))
        draw.ellipse([cx-55, cy-47, cx+55, cy+47], fill=inner + (235,))
        # 彩虹外环（三圈叠色）
        draw.ellipse([cx-93, cy-81, cx+93, cy+81], outline=(255, 100, 180, 200), width=3)
        draw.ellipse([cx-97, cy-85, cx+97, cy+85], outline=(255, 200,  50, 180), width=3)
        draw.ellipse([cx-101, cy-89, cx+101, cy+89], outline=(100, 200, 255, 150), width=2)
        # 八角星光点
        for i in range(8):
            angle = i * math.pi / 4
            sx = int(cx + 98 * math.cos(angle))
            sy = int(cy + 86 * math.sin(angle))
            r = 5 if i % 2 == 0 else 3
            draw.ellipse([sx-r, sy-r, sx+r, sy+r], fill=(255, 255, 160, 230))

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
                   emoji_size: int = 88,
                   stage: int = 0) -> ImageTk.PhotoImage:
    """用 PIL 将宠物渲染为真彩图。自定义物种走手绘，其余走 emoji 渲染。"""
    bg_rgb   = _hex_rgb(bg_hex)
    glow_rgb = _hex_rgb(glow_hex)

    img  = Image.new('RGBA', (w, h), bg_rgb + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    _draw_glow(draw, cx, cy, glow_rgb, stage)

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
        self._evo_lbl    = None
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

        # 进化阶段标签
        self._evo_lbl = tk.Label(self, text=EVO_NAMES[evo_stage(d['affection'])],
                                  bg=BG, fg='#ccaa55', font=('Microsoft YaHei', 9))
        self._evo_lbl.pack(pady=(2, 0))

        # 对话气泡（固定5行高）
        self._speech_lbl = tk.Label(self, text='', bg=BG, fg='#88ccff',
                                    font=('Microsoft YaHei', 10, 'italic'),
                                    wraplength=WW - 32, justify='center',
                                    height=5)
        self._speech_lbl.pack(pady=(2, 2))

        # 状态条
        bars_frame = tk.Frame(self, bg=BG)
        bars_frame.pack(fill='x', padx=16, pady=(0, 4))
        for label, key, max_v, color in [
            ('❤ 好感', 'affection',       200, '#ff6699'),
            ('饱食度', 'pet_fullness',    100, '#ffaa33'),
            ('体力',   'player_stamina',  200, '#4499ff'),
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
        self._regen_lbl = tk.Label(self, text='体力每2分钟回复1点，上限200', bg=BG, fg=FGD,
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
        d        = self._data
        fullness = d['pet_fullness']
        st       = d['player_stamina']
        aff      = d['affection']
        fainted  = (fullness <= 0)
        sp_e     = SPECIES[d['companion']['species']]['emoji']
        sp_key   = d['companion']['species']
        sd       = SPECIES[sp_key]
        stage    = evo_stage(aff)

        # 宠物图片（PIL 真彩，含进化光晕）
        e_emoji = '💤' if fainted else sp_e
        self._pet_photo = make_pet_image(
            e_emoji, sd['bg'], sd.get('glow', '#333355'),
            w=CW, h=CH,
            species='' if fainted else sp_key,
            stage=0 if fainted else stage)
        self._canvas.itemconfig(self._pet_item, image=self._pet_photo)

        # 状态图标
        mood = get_mood(d)
        if fainted:           sts = '😵'
        elif mood == 'happy': sts = '😍'
        elif fullness < 30:   sts = '😰'
        else:                 sts = ''
        self._canvas.itemconfig(self._sts_item, text=sts)

        # 进化阶段标签
        if hasattr(self, '_evo_lbl') and self._evo_lbl:
            self._evo_lbl.config(text=EVO_NAMES[stage])

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
            food_full = d['pet_fullness'] >= 70
            self._btn_feed.config(
                text='🍖 喂食 -10体力' if not food_full else '🍖 吃饱了',
                command=self._do_feed,
                state='normal' if (st >= FEED_COST and not food_full) else 'disabled')

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
        if self._pet_item and self._data and self._data['pet_fullness'] > 0:
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
        if d['pet_fullness'] <= 0:
            self._say('（它昏迷着呢，先唤醒吧）'); return
        if d['player_stamina'] < PET_COST:
            self._say('体力不足，休息一下再来～'); return
        d['player_stamina']    -= PET_COST
        d['affection']         += 1
        d['mood_happy_until']   = time.time() + 300   # 开心5分钟
        self._float_hearts()
        self._speech_lbl.config(text='')
        self.after(300, lambda: self._say(pick_dialogue(d)))
        self._refresh(); self._update_bars(); save_game(d)

    def _do_feed(self):
        d = self._data
        if d['pet_fullness'] >= 70:
            self._say('吃饱了，不要再喂了！'); return
        if d['player_stamina'] < FEED_COST:
            self._say('体力不足，等等再喂吧'); return
        d['player_stamina']  -= FEED_COST
        d['pet_fullness']     = min(FOOD_MAX, d['pet_fullness'] + FEED_FOOD)
        d['affection']       += 1
        d['mood_happy_until'] = time.time() + 300   # 开心5分钟
        self._say('（津津有味地吃东西，好感+1）')
        self._refresh(); self._update_bars(); save_game(d)

    def _do_revive(self):
        d = self._data
        if d['player_stamina'] < REVIVE_COST:
            self._say(f'体力不足，需要 {REVIVE_COST} 点'); return
        d['player_stamina'] -= REVIVE_COST
        d['pet_fullness']    = float(REVIVE_FOOD)
        self._say('……（缓缓睁开眼睛）……你来了啊……')
        self._refresh(); self._update_bars(); save_game(d)

    def _do_speak(self):
        self._say(pick_dialogue(self._data))

    def _say(self, text: str):
        self._speech_lbl.config(text=text)


if __name__ == '__main__':
    BuddyApp().mainloop()
