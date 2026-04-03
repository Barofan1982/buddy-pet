# CLAUDE.md — Buddy Pet 宠物养成

## 项目概述
桌面电子宠物养成游戏（Tamagotchi 风格），tkinter + PIL 实现。

## 目标用户
年轻女性玩家（搞艺术的小姑娘），所有设计决策围绕这个群体：
- 对话风格：治愈系 / 撒娇系 / 小废话系，**禁止程序员梗**
- 视觉风格：温柔配色、光晕效果、飘心动画

## 技术栈
- Python 3.12+ / tkinter / PIL (Pillow)
- PyInstaller 打包为 exe（约 19MB）

## 文件结构
```
buddy.py          # 主程序（唯一源文件）
run_buddy.vbs     # 静默启动（自动探测 Python 路径）
Buddy.spec        # PyInstaller 打包配置
Buddy说明书.docx   # 功能说明文档
backups/          # 版本备份
```

## 关键技术要点
- **Emoji 渲染**：tkinter Canvas 无法显示彩色 emoji → 用 PIL + `seguiemj.ttf`（`embedded_color=True`）渲染为 PhotoImage
- **Segoe UI Emoji 字体**：`C:\Windows\Fonts\seguiemj.ttf`（Windows 10+ 通用）
- **水豚特殊处理**：Unicode 无水豚 emoji → `_draw_capybara()` 用 PIL 手绘
- **PhotoImage 防 GC**：必须用 `self._pet_photo` 持有引用，否则图片被垃圾回收变空白
- **PRNG**：Mulberry32 确定性随机，同一昵称永远生成同一只宠物
- **离线补算**：`do_tick()` 中 `elapsed = max(0, min(now - last_tick, 8*3600))`，防时钟回拨 + 8 小时上限

## 游戏数值
- 19 个物种，5 级稀有度，8 种帽子
- 饱食度上限 100，每分钟 -1，喂食 +30（饱食度 ≥70 禁止喂食）
- 体力上限 200，每 2 分钟 +1
- 好感度上限 200，抚摸/喂食各 +1
- 心情：happy（操作后 5 分钟）/ calm / sad（饱食度<40）/ fainted（饱食度=0）
- 进化阶段：初相遇(0) → 渐熟悉(30) → 心意通(100) → 灵魂伴(200)，光晕随阶段升级

## 存档
- 文件：`.buddy_save.json`（exe 同目录，不提交）
- 兼容旧存档：`do_tick()` 自动把 `pet_hp` 迁移为 `pet_fullness`

## 规则
- **每次大改前必须备份到 `backups/`**，命名：`buddy_v{N}_{YYYYMMDD}.py`
- **未经用户明确许可，不得擅自重建 exe**
