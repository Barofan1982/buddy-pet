# ✦ Buddy Pet ✦

> 桌面宠物养成游戏 / Desktop Virtual Pet Game

---

## 简介 | Description

**Buddy Pet** 是一款桌面虚拟宠物养成游戏（类似电子宠物机）。你可以通过输入昵称召唤专属宠物，喂食、抚摸、对话，陪伴它成长，见证你们从陌生人到灵魂伴侣的进化之旅。

**Buddy Pet** is a desktop virtual pet raising game (Tamagotchi-style) designed for young female users. Enter a nickname to summon your unique companion, feed it, pet it, chat with it, and watch your bond evolve from strangers to soulmates.

---

## 功能特色 | Features

### 19 种宠物 | 19 Species

每个昵称通过哈希算法生成唯一的宠物组合（物种 + 稀有度 + 帽子 + 属性）。

Each nickname deterministically generates a unique pet combination (species + rarity + hat + stats) via hash-based PRNG.

| 物种 Species | Emoji | 物种 Species | Emoji |
|:---:|:---:|:---:|:---:|
| 鸭鸭 Duck | :duck: | 猫猫 Cat | :cat: |
| 小鬼 Ghost | :ghost: | 机器人 Robot | :robot: |
| 水豚 Capybara | :hamster: | 史莱姆 Blob | :space_invader: |
| 企鹅 Penguin | :penguin: | 小龙 Dragon | :dragon: |
| 猫头鹰 Owl | :owl: | 蘑菇 Mushroom | :mushroom: |
| 蜗牛 Snail | :snail: | 美西螈 Axolotl | :lizard: |
| 兔子 Rabbit | :rabbit: | 乌龟 Turtle | :turtle: |
| 章鱼 Octopus | :octopus: | 仙人掌 Cactus | :cactus: |
| 狗狗 Dog | :dog: | 熊猫 Panda | :panda_face: |
| 狐狸 Fox | :fox_face: | | |

### 心情系统 | Mood System

宠物拥有四种心情状态，影响对话内容和表情：

Your pet has four mood states that affect dialogue and expressions:

- **开心 Happy** -- 被抚摸/喂食后持续 5 分钟，表情为心眼
- **平静 Calm** -- 默认状态，随机说话、治愈、小废话
- **难过 Sad** -- 饱食度低于 40 时触发，委屈、等待
- **昏迷 Fainted** -- 饱食度为 0，需消耗 30 体力唤醒

### 进化阶段 | Evolution Stages (4 Levels)

好感度提升解锁进化阶段，每个阶段带有独特的视觉光晕效果：

Affection milestones unlock evolution stages, each with unique visual glow effects:

| 阶段 Stage | 好感度 Affection | 名称 Name | 光晕效果 Glow Effect |
|:---:|:---:|:---:|:---|
| 0 | 0+ | 初相遇 First Meeting | 基础光晕 Basic glow |
| 1 | 30+ | 渐熟悉 Getting Closer | 更亮更大光晕 Brighter & larger glow |
| 2 | 100+ | 心意通 Hearts Connected | 金色光圈 Golden ring |
| 3 | 200+ | 灵魂伴 Soulmates | 彩虹光环 + 八角星光 Rainbow halo + star rays |

### 对话系统 | Dialogue System

三大基调：治愈、撒娇、小废话。每个物种拥有独立的个性化台词。

Three core tones: healing, clingy, and random chatter. Each species has its own personality-specific lines.

- **治愈 Healing** -- 温暖陪伴类台词
- **撒娇 Clingy** -- 好感度达到 10 后解锁，撒娇黏人台词
- **小废话 Random** -- 日常碎碎念
- **物种专属 Species-specific** -- 每种心情 (normal/happy/sad/hungry) 都有 19 种物种各自的台词

### 数值系统 | Stats

| 属性 Stat | 上限 Max | 说明 Description |
|:---:|:---:|:---|
| 饱食度 Fullness | 100 | 每分钟 -1，降到 0 宠物昏迷 |
| 体力 Stamina | 200 | 每 2 分钟 +1，用于抚摸/喂食/唤醒 |
| 好感度 Affection | 200 | 抚摸/喂食各 +1，决定进化阶段和关系称号 |

关系称号 Relationship titles: 陌生人 Stranger -> 点头之交 Acquaintance -> 朋友 Friend -> 好友 Close Friend -> 挚友 Best Friend -> 灵魂伴侣 Soulmate

### PIL 渲染 | PIL Emoji Rendering

使用 Pillow (PIL) 进行真彩 emoji 渲染，水豚物种采用手绘 PIL 绘图（因为 Unicode 没有水豚 emoji）。每个物种有专属背景色和光晕色。

Uses Pillow (PIL) for true-color emoji rendering. The capybara species features a custom hand-drawn PIL illustration (since Unicode has no capybara emoji). Each species has its own background and glow colors.

### 离线补算 | Offline Time Catch-up

关闭游戏后再次打开，自动补算离线期间的饱食度下降和体力恢复（最多补算 8 小时）。

When you reopen the game after being away, it automatically catches up on fullness decay and stamina regeneration for the offline period (capped at 8 hours).

### 其他特色 | Other Features

- 5 种稀有度（普通/罕见/稀有/史诗/传说）| 5 rarity tiers (Common / Uncommon / Rare / Epic / Legendary)
- 8 种帽子装饰 | 8 hat accessories
- 浮动爱心动画 | Floating heart animations
- 呼吸式弹跳动画 | Breathing bounce animation
- 自动每 10 秒存档 | Auto-save every 10 seconds

---

## 环境要求 | Requirements

- **Python 3** (3.8+)
- **Pillow** (PIL)
- **tkinter** (Python 自带 / included with Python)

安装 Pillow / Install Pillow:

```bash
pip install Pillow
```

---

## 运行方式 | How to Run

三种启动方式 / Three ways to launch:

```bash
# 1. 直接运行 Python 脚本 / Run Python script directly
python buddy.py

# 2. 使用 VBS 脚本静默启动（无控制台窗口）/ Silent launch via VBS (no console window)
# 双击 run_buddy.vbs / Double-click run_buddy.vbs

# 3. 使用打包好的 exe / Use the packaged exe
# 双击 dist/Buddy.exe / Double-click dist/Buddy.exe
```

---

## 游戏玩法 | Game Mechanics

1. **召唤宠物** -- 输入昵称，相同昵称永远对应同一只宠物
2. **抚摸** -- 消耗 5 体力，好感 +1，触发 5 分钟开心状态
3. **喂食** -- 消耗 10 体力，恢复 30 饱食度，好感 +1（饱食度 >= 70 时无法喂食）
4. **说话** -- 点击对话按钮，宠物会根据当前心情和物种说出不同台词
5. **唤醒** -- 宠物昏迷时，消耗 30 体力唤醒并恢复 30 饱食度
6. **养成** -- 持续互动提升好感度，解锁进化阶段和关系称号

1. **Summon** -- Enter a nickname; the same nickname always produces the same pet
2. **Pet** -- Costs 5 stamina, +1 affection, triggers 5-min happy mood
3. **Feed** -- Costs 10 stamina, restores 30 fullness, +1 affection (disabled when fullness >= 70)
4. **Talk** -- Click the chat button; your pet speaks based on current mood and species
5. **Revive** -- When fainted, costs 30 stamina to revive with 30 fullness restored
6. **Grow** -- Keep interacting to raise affection, unlock evolution stages and relationship titles

---

## 许可证 | License

MIT
