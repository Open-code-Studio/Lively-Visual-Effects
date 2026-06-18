#!/usr/bin/env python3
"""
灵动:视效 — 3D 立体纹理生成器
生成具有强烈浮雕/立体效果的 Minecraft 方块贴图。
"""

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageDraw

SIZE = 16
OUTPUT = Path("../assets/minecraft/textures/block/")
OUTPUT.mkdir(parents=True, exist_ok=True)

# ============================================================
# 工具函数
# ============================================================

def save(img, name):
    img.save(OUTPUT / f"{name}.png")
    print(f"  ✓ {name}.png")

def array_to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def noise2d(size, scale=4.0):
    """简单伪随机噪声"""
    np.random.seed(42)
    n = np.random.rand(size, size) * 0.5 + 0.25
    n = Image.fromarray((n * 255).astype(np.uint8))
    n = n.resize((size * scale, size * scale), Image.BILINEAR)
    n = n.resize((size, size), Image.BILINEAR)
    return np.array(n, dtype=np.float32) / 255.0

def perlin_like(seed, size=SIZE, octaves=3):
    """多层噪声叠加模拟自然纹理"""
    np.random.seed(seed)
    result = np.zeros((size, size), dtype=np.float32)
    for octave in range(octaves):
        scale = 2 ** octave
        n = np.random.rand(max(2, size//scale), max(2, size//scale))
        n_img = Image.fromarray((n * 255).astype(np.uint8))
        n_img = n_img.resize((size, size), Image.BILINEAR)
        weight = 0.5 ** octave
        result += np.array(n_img, dtype=np.float32) / 255.0 * weight
    result /= result.max()
    return result

def bevel_edge(arr, bevel_width=3, bevel_strength=1.0):
    """对整个贴图边缘做强烈的斜面/倒角效果"""
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            d_top = y + 1
            d_bot = h - y
            d_left = x + 1
            d_right = w - x
            d = min(d_top, d_bot, d_left, d_right)
            if d < bevel_width * 2:
                mask[y, x] = min(1.0, d / (bevel_width * 2))
    return mask

def inner_bevel(canvas, hl_color, sh_color, width=2):
    """在画布上绘制内斜面高光和阴影，产生突出立体感"""
    h, w = canvas.shape[:2]
    result = canvas.copy().astype(np.float32)
    for y in range(h):
        for x in range(w):
            d = min(y, x, h-1-y, w-1-x)
            if d < width:
                t = d / width
                # 左上高光，右下阴影
                if y < h//2 and x < w//2:
                    # 高光区域
                    blend = 1 - min(t * 1.5, 1.0)
                    result[y, x] = canvas[y, x] * (1 - blend) + np.array(hl_color) * blend
                elif y >= h//2 or x >= w//2:
                    # 阴影区域
                    cx, cy = w//2, h//2
                    dx, dy = x - cx, y - cy
                    if dx + dy > 0:
                        blend = 1 - min(t * 1.5, 1.0)
                        result[y, x] = canvas[y, x] * (0.6 + 0.4 * (1 - blend))
    return np.clip(result, 0, 255).astype(np.uint8)

# ============================================================
# 方块纹理生成器
# ============================================================

def make_stone():
    """石头 — 粗糙凹凸表面 + 边缘突出"""
    noise = perlin_like(1, SIZE, 4)
    base_r = int(128 + noise.mean() * 20)
    base_g = int(128 + noise.mean() * 20)
    base_b = int(128 + noise.mean() * 20)
    
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    for y in range(SIZE):
        for x in range(SIZE):
            v = noise[y, x]
            r = base_r + int((v - 0.5) * 40)
            g = base_g + int((v - 0.5) * 40)
            b = base_b + int((v - 0.5) * 40)
            # 添加斑点
            spot = noise[int(y*3)%SIZE, int(x*3)%SIZE]
            r += int((spot - 0.5) * 30)
            g += int((spot - 0.5) * 30)
            b += int((spot - 0.5) * 30)
            img[y, x] = [np.clip(r, 60, 180), np.clip(g, 60, 180), np.clip(b, 60, 180)]
    
    # 整个面的3D隆起效果
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.5))
            factor = factor ** 2.5  # 陡峭的隆起
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.35), 0, 255)
    
    return array_to_img(img)

def make_cobblestone():
    """圆石 — 多个凸起石块拼接"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    # 基础灰色
    base = np.array([120, 115, 110])
    
    # 生成随机石块布局
    blocks = [
        (0, 0, 9, 8), (9, 0, 7, 7),
        (0, 8, 7, 8), (7, 7, 9, 9),
        (8, 3, 8, 5),
    ]
    
    for bx, by, bw, bh in blocks:
        stone_color = base + np.random.randint(-15, 15, 3)
        for y in range(by, min(by+bh, SIZE)):
            for x in range(bx, min(bx+bw, SIZE)):
                # 每个石块内添加微小纹理
                noise_val = (np.random.rand() - 0.5) * 20
                color = np.clip(stone_color + noise_val, 40, 200)
                img[y, x] = color
    
    # 石块间的缝隙
    crack_color = np.array([50, 45, 40])
    for y in range(SIZE):
        for x in range(SIZE):
            # 边界检测 - 缝隙
            is_edge = False
            if x > 0 and img[y, x].sum() > 0 and img[y, x-1].sum() == 0:
                is_edge = True
            if y > 0 and img[y, x].sum() > 0 and img[y-1, x].sum() == 0:
                is_edge = True
            if is_edge:
                img[y, x] = crack_color
    
    # 填充空隙
    for y in range(SIZE):
        for x in range(SIZE):
            if img[y, x].sum() == 0:
                img[y, x] = crack_color
    
    # 每个石块做独立的3D隆起
    for bx, by, bw, bh in blocks:
        bcx, bcy = bx + bw/2, by + bh/2
        for y in range(by, min(by+bh, SIZE)):
            for x in range(bx, min(bx+bw, SIZE)):
                dx = abs(x - bcx) / (bw/2)
                dy = abs(y - bcy) / (bh/2)
                factor = max(0, 1 - max(dx, dy))
                factor = factor ** 3
                img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.4), 0, 255)
    
    # 高光边
    for y in range(SIZE):
        for x in range(SIZE):
            if y == 0 or x == 0:
                img[y, x] = np.clip(img[y, x].astype(float) * 1.4, 0, 255)
            elif (y <= 1 or x <= 1) and (y == 1 or x == 1):
                img[y, x] = np.clip(img[y, x].astype(float) * 1.2, 0, 255)
    
    return array_to_img(img)

def make_planks():
    """木板 — 横向木纹 + 突出立体感"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    wood_base = np.array([160, 120, 70])
    
    for y in range(SIZE):
        # 木纹条纹
        stripe = (math.sin(y * 0.8 + math.sin(y * 0.3) * 2) + 1) / 2
        darkness = stripe * 0.3 + 0.7
        color = (wood_base * darkness).astype(int)
        for x in range(SIZE):
            noise = (np.random.rand() - 0.5) * 15
            c = np.clip(color + noise, 30, 220)
            img[y, x] = c
    
    # 木板分隔线（3块板）
    for split_y in [5, 10]:
        for x in range(SIZE):
            img[split_y, x] = np.array([45, 30, 15])
            if split_y + 1 < SIZE:
                img[split_y+1, x] = np.array([50, 35, 20])
    
    # 3D隆起
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.4))
            factor = factor ** 3.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.3), 0, 255)
    
    return array_to_img(img)

def make_grass_top():
    """草方块顶部 — 绿色草地纹理 + 3D凸起"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            # 绿色基底 + 随机变化
            g = 140 + int((np.random.rand() - 0.5) * 50)
            r = 80 + int((np.random.rand() - 0.5) * 30)
            b = 40 + int((np.random.rand() - 0.5) * 20)
            img[y, x] = [np.clip(r, 30, 160), np.clip(g, 80, 200), np.clip(b, 20, 80)]
    
    # 草叶纹理（细竖线）
    for x in range(SIZE):
        if x % 3 == 0:
            for y in range(SIZE):
                bright = 1 + (np.random.rand() - 0.5) * 0.4
                img[y, x] = np.clip(img[y, x].astype(float) * bright, 0, 255)
    
    # 中心隆起3D
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.3))
            factor = factor ** 2.8
            # 高光偏左上
            light_dir = (x - cx) * -0.3 + (y - cy) * -0.3
            extra = factor * 0.3 + max(0, light_dir) * 0.15
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + extra), 0, 255)
    
    return array_to_img(img)

def make_dirt():
    """泥土 — 粗糙颗粒 + 凹凸感"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    noise_map = perlin_like(7, SIZE, 4)
    
    for y in range(SIZE):
        for x in range(SIZE):
            v = noise_map[y, x]
            r = 120 + int((v - 0.5) * 35)
            g = 85 + int((v - 0.5) * 25)
            b = 50 + int((v - 0.5) * 20)
            # 石块颗粒
            if np.random.rand() < 0.08:
                r += 15
                g += 10
                b += 5
            img[y, x] = [np.clip(r, 50, 180), np.clip(g, 35, 140), np.clip(b, 20, 100)]
    
    # 3D
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.4))
            factor = factor ** 3.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.25), 0, 255)
    
    return array_to_img(img)

def make_brick():
    """砖块 — 砖块纹理 + 强烈凸起"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    brick_color = np.array([180, 70, 45])
    mortar = np.array([130, 120, 110])
    
    brick_h = 4  # 每块砖高度
    for y in range(SIZE):
        row = y // brick_h
        offset = (row % 2) * 4  # 奇偶行错位
        for x in range(SIZE):
            x_adj = (x - offset) % SIZE
            
            # 灰缝
            if y % brick_h == 0 or y % brick_h == brick_h - 1:
                img[y, x] = mortar
            elif x_adj == 0 or x_adj == 7:
                img[y, x] = mortar
            else:
                # 砖块颜色 + 微小变化
                noise = np.random.randint(-10, 10, 3)
                img[y, x] = np.clip(brick_color + noise, 30, 230)
    
    # 每块砖独立3D凸起
    for y in range(SIZE):
        row = y // brick_h
        offset = (row % 2) * 4
        for x in range(SIZE):
            if img[y, x].sum() > mortar.sum():  # 是砖块不是灰缝
                # 在砖块内部的相对位置
                x_adj = (x - offset) % SIZE
                bx = x_adj % 8
                by = y % brick_h
                # 砖块中心隆起
                dx = abs(bx - 3.5) / 3.5
                dy = abs(by - 1.5) / 1.5
                factor = max(0, 1 - max(dx, dy))
                factor = factor ** 2.5
                img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.4), 0, 255)
    
    return array_to_img(img)

def make_iron_block():
    """铁块 — 金属光泽 + 强烈凸起条纹"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            # 金属灰白基底
            v = 200 + (np.sin(y * 0.6) + np.sin(x * 0.7)) * 15
            r = g = b = int(np.clip(v, 170, 235))
            img[y, x] = [r, g, b]
    
    # 金属边框 / 镶边线
    border_color = np.array([100, 100, 100])
    for i in range(2):
        for j in range(SIZE):
            if i < SIZE:
                img[i, j] = border_color
                img[SIZE-1-i, j] = border_color
                img[j, i] = border_color
                img[j, SIZE-1-i] = border_color
    
    # 内边框高光
    hl_color = np.array([255, 255, 255])
    for y in [2, 3]:
        for x in range(2, SIZE-2):
            img[y, x] = hl_color
    for x in [2, 3]:
        for y in range(2, SIZE-2):
            img[y, x] = hl_color
    
    # 3D 中心隆起
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.3))
            factor = factor ** 4.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.5), 0, 255)
    
    return array_to_img(img)

def make_gold_block():
    """金块 — 金色金属 + 强烈凸起条纹"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            r = 240 + int(np.sin(y*0.5) * 15 + np.sin(x*0.6) * 10)
            g = 200 + int(np.sin(y*0.7) * 10 + np.sin(x*0.5) * 12)
            b = 50 + int(np.sin(y*0.4) * 15 + np.sin(x*0.8) * 8)
            img[y, x] = [np.clip(r, 190, 255), np.clip(g, 160, 240), np.clip(b, 30, 100)]
    
    # 边框
    border = np.array([150, 110, 30])
    for i in range(2):
        for j in range(SIZE):
            img[i, j] = border
            img[SIZE-1-i, j] = border
            img[j, i] = border
            img[j, SIZE-1-i] = border
    
    # 内高光
    hl = np.array([255, 255, 200])
    for y in [2, 3]:
        for x in range(2, SIZE-2):
            img[y, x] = hl
    for x in [2, 3]:
        for y in range(2, SIZE-2):
            img[y, x] = hl
    
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.3))
            factor = factor ** 4.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.5), 0, 255)
    
    return array_to_img(img)

def make_diamond_block():
    """钻石块 — 晶体质感 + 3D切面"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            r = 80 + int(np.sin(y*0.5 + x*0.3) * 30)
            g = 200 + int(np.cos(x*0.4 + y*0.3) * 25)
            b = 220 + int(np.sin(x*0.5 - y*0.3) * 20)
            img[y, x] = [np.clip(r, 50, 160), np.clip(g, 170, 255), np.clip(b, 180, 255)]
    
    # 边框
    border = np.array([50, 120, 150])
    for i in range(2):
        for j in range(SIZE):
            img[i, j] = border
            img[SIZE-1-i, j] = border
            img[j, i] = border
            img[j, SIZE-1-i] = border
    
    # 内高光
    hl = np.array([200, 255, 255])
    for y in [2, 3]:
        for x in range(2, SIZE-2):
            img[y, x] = hl
    for x in [2, 3]:
        for y in range(2, SIZE-2):
            img[y, x] = hl
    
    # 对角切面反射
    for y in range(SIZE):
        for x in range(SIZE):
            if x + y < 6 or x + y > 25:
                img[y, x] = np.clip(img[y, x].astype(float) * 1.3, 0, 255)
            if x - y > 8 or y - x > 8:
                img[y, x] = np.clip(img[y, x].astype(float) * 0.8, 0, 255)
    
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.3))
            factor = factor ** 4.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.45), 0, 255)
    
    return array_to_img(img)

def make_obsidian():
    """黑曜石 — 深色玻璃质感 + 紫色光泽"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            v = 25 + int((np.sin(y*0.5 + x*0.6) + np.cos(x*0.4 - y*0.5)) * 8)
            r = np.clip(v + 10, 15, 50)
            g = np.clip(v - 5, 10, 40)
            b = np.clip(v + 30, 40, 90)
            img[y, x] = [r, g, b]
    
    # 紫色光泽条
    for y in range(SIZE):
        if y % 5 < 2:
            for x in range(SIZE):
                img[y, x] = np.clip(img[y, x].astype(float) * 1.2, 0, 255)
                img[y, x][2] = min(255, img[y, x][2] + 20)  # 加蓝紫色
    
    # 3D
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.4))
            factor = factor ** 3.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.3), 0, 255)
    
    return array_to_img(img)

def make_glass():
    """玻璃 — 透明清爽 + 高光条纹"""
    # 玻璃在 Minecraft 中大部分透明，这里做边框/条纹效果
    img = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)  # RGBA
    img[:, :, 3] = 80  # 半透明
    
    for y in range(SIZE):
        for x in range(SIZE):
            r = g = b = 200 + int(np.sin(y*0.6 + x*0.7) * 15)
            img[y, x, :3] = [np.clip(r, 180, 240), np.clip(g, 200, 250), np.clip(b, 220, 255)]
    
    # 边框高亮
    border = np.array([255, 255, 255, 200])
    for i in range(2):
        for j in range(SIZE):
            img[i, j] = border
            img[SIZE-1-i, j] = border
            img[j, i] = border
            img[j, SIZE-1-i] = border
    
    # 对角高光条纹
    for y in range(SIZE):
        for x in range(SIZE):
            if (x + y) % 4 == 0:
                img[y, x, :3] = np.clip(img[y, x, :3].astype(float) * 1.15, 0, 255)
    
    return Image.fromarray(img, "RGBA")

def make_glowstone():
    """萤石 — 明亮颗粒 + 发光中心"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            # 棕黄色基底
            r = 180 + np.random.randint(-20, 20)
            g = 150 + np.random.randint(-15, 25)
            b = 60 + np.random.randint(-15, 20)
            # 亮斑
            if np.random.rand() < 0.3:
                r = min(255, r + 60)
                g = min(255, g + 80)
                b = min(255, b + 80)
            img[y, x] = [np.clip(r, 120, 255), np.clip(g, 100, 255), np.clip(b, 30, 200)]
    
    # 网格纹（萤石特征）
    for y in range(0, SIZE, 5):
        for x in range(SIZE):
            img[y, x] = np.array([200, 160, 70])
            if y+1 < SIZE:
                img[y+1, x] = np.array([190, 150, 60])
    for x in range(0, SIZE, 5):
        for y in range(SIZE):
            img[y, x] = np.array([200, 160, 70])
            if x+1 < SIZE:
                img[y, x+1] = np.array([190, 150, 60])
    
    # 3D
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.4))
            factor = factor ** 2.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.3), 0, 255)
    
    return array_to_img(img)

def make_netherrack():
    """下界岩 — 红色粗糙纹理 + 碎块凸起"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            r = 120 + np.random.randint(-25, 30)
            g = 45 + np.random.randint(-15, 20)
            b = 35 + np.random.randint(-10, 15)
            img[y, x] = [np.clip(r, 70, 170), np.clip(g, 20, 80), np.clip(b, 10, 60)]
    
    # 裂纹/碎块
    for _ in range(8):
        cx = np.random.randint(0, SIZE)
        cy = np.random.randint(0, SIZE)
        r2 = np.random.randint(2, 5)
        for dy in range(-r2, r2+1):
            for dx in range(-r2, r2+1):
                py, px = cy+dy, cx+dx
                if 0 <= py < SIZE and 0 <= px < SIZE and dx*dx+dy*dy <= r2*r2:
                    img[py, px] = np.array([60, 25, 15])
    
    # 3D
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.4))
            factor = factor ** 2.5
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.3), 0, 255)
    
    return array_to_img(img)

def make_emerald_block():
    """绿宝石块 — 深绿色金属"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            r = 30 + int(np.sin(y*0.5) * 15)
            g = 180 + int(np.cos(x*0.5 - y*0.3) * 25)
            b = 90 + int(np.sin(x*0.6) * 15)
            img[y, x] = [np.clip(r, 10, 80), np.clip(g, 130, 240), np.clip(b, 50, 140)]
    
    # 边框
    border = np.array([20, 80, 40])
    for i in range(2):
        for j in range(SIZE):
            img[i, j] = border
            img[SIZE-1-i, j] = border
            img[j, i] = border
            img[j, SIZE-1-i] = border
    
    hl = np.array([180, 255, 200])
    for y in [2, 3]:
        for x in range(2, SIZE-2):
            img[y, x] = hl
    for x in [2, 3]:
        for y in range(2, SIZE-2):
            img[y, x] = hl
    
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.3))
            factor = factor ** 4.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.45), 0, 255)
    
    return array_to_img(img)

def make_gravel():
    """沙砾 — 多色颗粒混合"""
    img = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    
    for y in range(SIZE):
        for x in range(SIZE):
            choice = np.random.rand()
            if choice < 0.35:
                c = [160, 155, 150]
            elif choice < 0.6:
                c = [120, 115, 110]
            elif choice < 0.8:
                c = [100, 90, 80]
            else:
                c = [180, 170, 160]
            noise = np.random.randint(-10, 10, 3)
            img[y, x] = np.clip(np.array(c) + noise, 60, 210)
    
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.4))
            factor = factor ** 3.0
            img[y, x] = np.clip(img[y, x].astype(float) * (1 + factor * 0.2), 0, 255)
    
    return array_to_img(img)

# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("\n  灵动:视效 — 3D 立体纹理生成\n")
    
    textures = {
        "stone": make_stone,
        "cobblestone": make_cobblestone,
        "oak_planks": make_planks,
        "grass_block_top": make_grass_top,
        "dirt": make_dirt,
        "bricks": make_brick,
        "iron_block": make_iron_block,
        "gold_block": make_gold_block,
        "diamond_block": make_diamond_block,
        "obsidian": make_obsidian,
        "glass": make_glass,
        "glowstone": make_glowstone,
        "netherrack": make_netherrack,
        "emerald_block": make_emerald_block,
        "gravel": make_gravel,
        "sand": lambda: make_gravel(),  # 复用沙砾纹理，重命名为sand
    }
    
    for name, func in textures.items():
        try:
            img = func()
            save(img, name)
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    
    print(f"\n  完成! 共生成 {len(textures)} 个纹理")
    print(f"  输出目录: {OUTPUT.resolve()}\n")
