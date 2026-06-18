#!/usr/bin/env python3
"""
灵动:视效 — 全方块 3D 立体纹理生成器
为 Minecraft 1.21 所有主要方块生成带强烈 3D 浮雕效果的 PBR 纹理。
"""

import math, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

SIZE = 16
OUTPUT = Path("../assets/minecraft/textures/block/")
OUTPUT.mkdir(parents=True, exist_ok=True)

# ============================================================
# 工具
# ============================================================

def save(img, name):
    img.save(OUTPUT / f"{name}.png")

def arr2img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def perlin(seed, octaves=4):
    np.random.seed(seed)
    result = np.zeros((SIZE, SIZE), dtype=np.float32)
    for o in range(octaves):
        s = 2 ** o
        n = np.random.rand(max(2, SIZE//s), max(2, SIZE//s))
        ni = Image.fromarray((n*255).astype(np.uint8))
        ni = ni.resize((SIZE, SIZE), Image.BILINEAR)
        result += np.array(ni, dtype=np.float32) / 255.0 * (0.5**o)
    result /= result.max()
    return result

def apply_3d_relief(img_arr, strength=0.3, sharpness=3.0):
    """对整个贴图应用中心隆起 3D 效果"""
    cy, cx = SIZE//2, SIZE//2
    result = img_arr.astype(float).copy()
    for y in range(SIZE):
        for x in range(SIZE):
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            factor = max(0, 1 - dist / (SIZE/1.25))
            factor = factor ** sharpness
            # 左上方向高光
            light = (cx - x) * 0.04 + (cy - y) * 0.04
            result[y, x] *= (1 + factor * strength + light)
    return np.clip(result, 0, 255).astype(np.uint8)

def apply_corner_highlight(img_arr, width=2):
    """左上角高光边，右下角暗边"""
    result = img_arr.astype(float).copy()
    for y in range(SIZE):
        for x in range(SIZE):
            d_top = y
            d_left = x
            if d_top < width and d_left < width:
                t = 1 - max(d_top, d_left) / width
                result[y, x] *= 1 + t * 0.5
            d_bot = SIZE - 1 - y
            d_right = SIZE - 1 - x
            if d_bot < width and d_right < width:
                t = 1 - max(d_bot, d_right) / width
                result[y, x] *= 1 - t * 0.3
    return np.clip(result, 0, 255).astype(np.uint8)

# ============================================================
# 通用生成器
# ============================================================

def gen_noise_block(base_color, noise_amt=30, seed=1):
    """噪声石块类: stone, andesite, diorite, granite, deepslate, tuff, calcite, bedrock"""
    n = perlin(seed, 4)
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(base_color, dtype=float)
    for y in range(SIZE):
        for x in range(SIZE):
            v = n[y, x]
            c = bc + (v - 0.5) * noise_amt * 2
            s = perlin(seed+1, 3)[y, x]
            c += (s - 0.5) * noise_amt * 0.6
            arr[y, x] = np.clip(c, 0, 255)
    arr = apply_3d_relief(arr, 0.28, 3.0)
    return arr2img(arr)

def gen_cobble_like(base_color, mortar_color, seed=1):
    """圆石类: cobblestone, blackstone, deepslate cobble"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    arr[:, :] = mortar_color
    np.random.seed(seed)
    bc = np.array(base_color, dtype=float)
    mc = np.array(mortar_color, dtype=float)
    
    # 随机石块布局
    blocks = np.random.randint(5, 10, size=(12, 4))
    for bx, by, bw, bh in blocks:
        for y in range(by, min(by+bh, SIZE)):
            for x in range(bx, min(bx+bw, SIZE)):
                n = np.random.randint(-15, 15, 3)
                c = np.clip(bc + n, 0, 255)
                arr[y, x] = c
    
    # 每块独立3D
    for bx, by, bw, bh in blocks:
        blk_cx, blk_cy = bx + bw/2, by + bh/2
        for y in range(by, min(by+bh, SIZE)):
            for x in range(bx, min(bx+bw, SIZE)):
                dx = abs(x - blk_cx) / (bw/2 + 0.01)
                dy = abs(y - blk_cy) / (bh/2 + 0.01)
                f = max(0, 1 - max(dx, dy)) ** 3
                arr[y, x] = np.clip(arr[y, x].astype(float) * (1 + f*0.35), 0, 255)
    
    arr = apply_corner_highlight(arr)
    return arr2img(arr)

def gen_planks(wood_color, seed=1):
    """木板: oak_planks 到 warped_planks"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(wood_color, dtype=float)
    for y in range(SIZE):
        stripe = (math.sin(y*0.7 + math.sin(y*0.35)*1.5) + 1) / 2
        dark = stripe * 0.35 + 0.65
        c = bc * dark
        for x in range(SIZE):
            n = np.random.randint(-10, 10, 3)
            arr[y, x] = np.clip(c + n, 0, 255)
    # 分隔线
    gap = np.array([30, 20, 10])
    for sp in [5, 10]:
        arr[sp, :] = gap
        if sp+1 < SIZE:
            arr[sp+1, :] = gap
    arr = apply_3d_relief(arr, 0.25, 3.0)
    return arr2img(arr)

def gen_metal_block(rgb, border_dark=None, seed=1):
    """金属方块: iron, gold, diamond, emerald, netherite, copper 等"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(rgb, dtype=float)
    if border_dark is None:
        border_dark = (bc * 0.4).astype(int)
    else:
        border_dark = np.array(border_dark)
    
    for y in range(SIZE):
        for x in range(SIZE):
            v = bc + (math.sin(y*0.5) + math.sin(x*0.6)) * 10
            arr[y, x] = np.clip(v + np.random.randint(-5, 5, 3), 0, 255)
    
    # 外框
    for i in range(2):
        arr[i, :] = border_dark; arr[SIZE-1-i, :] = border_dark
        arr[:, i] = border_dark; arr[:, SIZE-1-i] = border_dark
    # 内高光槽
    hl = np.array([255, 255, 255])
    for i in [2, 3]:
        arr[i, 2:SIZE-2] = hl; arr[2:SIZE-2, i] = hl
    
    arr = apply_3d_relief(arr, 0.4, 4.0)
    return arr2img(arr)

def gen_ore(stone_color, ore_color, seed=1):
    """矿石: coal_ore, iron_ore, gold_ore, diamond_ore 等"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    sc = np.array(stone_color, dtype=float)
    oc = np.array(ore_color, dtype=float)
    n = perlin(seed, 4)
    for y in range(SIZE):
        for x in range(SIZE):
            noise_val = n[y, x]
            c = sc + (noise_val - 0.5) * 30
            arr[y, x] = np.clip(c, 0, 255)
    
    # 矿石斑点
    np.random.seed(seed+100)
    for _ in range(np.random.randint(4, 9)):
        cx = np.random.randint(2, SIZE-2)
        cy = np.random.randint(2, SIZE-2)
        r = np.random.randint(2, 5)
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                if dx*dx + dy*dy <= r*r:
                    py, px = cy+dy, cx+dx
                    if 0 <= py < SIZE and 0 <= px < SIZE:
                        blend = (dx*dx + dy*dy) / (r*r) if r > 0 else 0
                        arr[py, px] = np.clip(arr[py, px] * blend + oc * (1-blend), 0, 255)
    
    arr = apply_3d_relief(arr, 0.25, 2.8)
    return arr2img(arr)

def gen_terracotta(color, seed=1):
    """陶瓦: 纯色 + 微纹理 + 3D"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    n = perlin(seed, 3)
    for y in range(SIZE):
        for x in range(SIZE):
            v = bc + (n[y, x] - 0.5) * 20
            arr[y, x] = np.clip(v, 0, 255)
    arr = apply_3d_relief(arr, 0.22, 2.8)
    return arr2img(arr)

def gen_concrete(color, seed=1):
    """混凝土: 纯色平滑 + 微颗粒 + 3D"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    np.random.seed(seed)
    for y in range(SIZE):
        for x in range(SIZE):
            n = np.random.randint(-8, 8, 3)
            arr[y, x] = np.clip(bc + n, 0, 255)
    arr = apply_3d_relief(arr, 0.2, 2.5)
    return arr2img(arr)

def gen_wool(color, seed=1):
    """羊毛: 柔软纹理 + 细纤维"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    for y in range(SIZE):
        for x in range(SIZE):
            fiber = math.sin(y*2.5 + x*0.3) * 0.5 + 0.5
            dark = fiber * 0.15 + 0.85
            c = bc * dark + np.random.randint(-5, 5, 3)
            arr[y, x] = np.clip(c, 0, 255)
    arr = apply_3d_relief(arr, 0.15, 2.0)
    return arr2img(arr)

def gen_glass(color, alpha=180, seed=1):
    """玻璃: 半透明 + 高光边框"""
    arr = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    bc = np.array(list(color) + [alpha])
    arr[:, :] = bc
    # 边框高亮
    border = np.array([255, 255, 255, min(255, alpha+50)])
    for i in range(2):
        arr[i, :] = border; arr[SIZE-1-i, :] = border
        arr[:, i] = border; arr[:, SIZE-1-i] = border
    # 对角条纹
    for y in range(SIZE):
        for x in range(SIZE):
            if (x+y) % 5 < 2:
                arr[y, x, :3] = np.clip(arr[y, x, :3].astype(float) * 1.1, 0, 255)
    arr_out = arr.copy()
    arr_out = apply_3d_relief(arr_out[:, :, :3], 0.2, 3.0)
    return Image.fromarray(np.dstack([arr_out, arr[:, :, 3]]).astype(np.uint8))

def gen_brick(brick_color, mortar_color, seed=1):
    """砖块: 交错砖块 + 灰缝 + 每砖独立3D"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(brick_color, dtype=float)
    mc = np.array(mortar_color, dtype=float)
    bh = 4
    for y in range(SIZE):
        row = y // bh
        off = (row % 2) * 4
        for x in range(SIZE):
            xa = (x - off) % SIZE
            if y % bh == 0 or y % bh == bh-1 or xa == 0 or xa == 7:
                arr[y, x] = mc
            else:
                n = np.random.randint(-8, 8, 3)
                arr[y, x] = np.clip(bc + n, 0, 255)
    # 每砖独立3D
    for y in range(SIZE):
        row = y // bh
        off = (row % 2) * 4
        for x in range(SIZE):
            xa = (x - off) % SIZE
            if not (y % bh == 0 or y % bh == bh-1 or xa == 0 or xa == 7):
                bx = xa % 8; by = y % bh
                dx = abs(bx - 3.5) / 3.5; dy = abs(by - 1.5) / 1.5
                f = max(0, 1 - max(dx, dy)) ** 2.5
                arr[y, x] = np.clip(arr[y, x].astype(float) * (1+f*0.35), 0, 255)
    arr = apply_corner_highlight(arr)
    return arr2img(arr)

def gen_netherrack_like(color, seed=1):
    """下界岩类: netherrack, nylium, nether_bricks"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    for y in range(SIZE):
        for x in range(SIZE):
            n = np.random.randint(-20, 20, 3)
            arr[y, x] = np.clip(bc + n, 0, 255)
    # 碎裂纹
    np.random.seed(seed)
    for _ in range(6):
        cx = np.random.randint(0, SIZE); cy = np.random.randint(0, SIZE)
        r = np.random.randint(1, 3)
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                px, py = cx+dx, cy+dy
                if 0 <= px < SIZE and 0 <= py < SIZE and dx*dx+dy*dy <= r*r:
                    arr[py, px] = np.clip(arr[py, px].astype(float) * 0.6, 0, 255)
    arr = apply_3d_relief(arr, 0.25, 2.5)
    return arr2img(arr)

def gen_glow_like(color, pattern='grid', seed=1):
    """发光块: glowstone, shroomlight, sea_lantern, redstone_lamp"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    for y in range(SIZE):
        for x in range(SIZE):
            n = np.random.randint(-15, 20, 3)
            arr[y, x] = np.clip(bc + n, 0, 255)
    # 亮斑
    for y in range(SIZE):
        for x in range(SIZE):
            if np.random.rand() < 0.25:
                arr[y, x] = np.clip(arr[y, x].astype(float) * 1.3, 0, 255)
    if pattern == 'grid':
        for y in range(0, SIZE, 5):
            for x in range(SIZE):
                arr[y, x] = np.clip(bc * 0.85, 0, 255)
                if y+1 < SIZE: arr[y+1, x] = np.clip(bc * 0.9, 0, 255)
        for x in range(0, SIZE, 5):
            for y in range(SIZE):
                arr[y, x] = np.clip(bc * 0.85, 0, 255)
                if x+1 < SIZE: arr[y, x+1] = np.clip(bc * 0.9, 0, 255)
    arr = apply_3d_relief(arr, 0.25, 2.0)
    return arr2img(arr)

def gen_sand_like(color, seed=1):
    """沙类: sand, red_sand, soul_sand, end_stone"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    for y in range(SIZE):
        for x in range(SIZE):
            n = np.random.randint(-12, 12, 3)
            c = np.clip(bc + n, 0, 255)
            if np.random.rand() < 0.05:
                c = np.clip(c.astype(float) * 1.3, 0, 255)
            arr[y, x] = c
    arr = apply_3d_relief(arr, 0.18, 2.8)
    return arr2img(arr)

def gen_log_side(color, seed=1):
    """原木侧面: 竖条纹 + 年轮"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    for y in range(SIZE):
        for x in range(SIZE):
            bar = math.sin(x * 0.8) * 0.5 + 0.5
            dark = bar * 0.3 + 0.7
            c = bc * dark + np.random.randint(-8, 8, 3)
            arr[y, x] = np.clip(c, 0, 255)
    # 深色竖纹
    for x in [3, 7, 11, 14]:
        if x < SIZE:
            arr[:, x] = np.clip(arr[:, x].astype(float) * 0.7, 0, 255)
    arr = apply_3d_relief(arr, 0.22, 3.0)
    return arr2img(arr)

def gen_log_top(color, ring_color=None, seed=1):
    """原木顶部: 年轮纹理"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    if ring_color is None:
        ring_color = (bc * 0.6).astype(int)
    rc = np.array(ring_color, dtype=float)
    cy, cx = SIZE//2, SIZE//2
    for y in range(SIZE):
        for x in range(SIZE):
            d = math.sqrt((x-cx)**2 + (y-cy)**2)
            ring = math.sin(d * 2.5) * 0.5 + 0.5
            inner = max(0, 1 - d/(SIZE/2)) ** 2
            c = bc * (0.7 + ring*0.3) * (0.85 + inner*0.15)
            # 年轮线
            if abs(d - int(d)) < 0.3:
                c = rc
            arr[y, x] = np.clip(c + np.random.randint(-5, 5, 3), 0, 255)
    arr = apply_3d_relief(arr, 0.2, 2.5)
    return arr2img(arr)

def gen_prismarine(color, pattern='brick', seed=1):
    """海晶类: prismarine, dark_prismarine, prismarine_bricks"""
    if pattern == 'brick':
        return gen_brick(color, [60, 100, 110], seed)
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    n = perlin(seed, 4)
    for y in range(SIZE):
        for x in range(SIZE):
            c = bc + (n[y, x] - 0.5) * 30
            arr[y, x] = np.clip(c, 0, 255)
    arr = apply_3d_relief(arr, 0.25, 2.8)
    return arr2img(arr)

def gen_obsidian_like(color, highlight_color=None, seed=1):
    """黑曜石类: obsidian, crying_obsidian"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    hc = np.array(highlight_color) if highlight_color else bc * 1.5
    for y in range(SIZE):
        for x in range(SIZE):
            n = np.random.randint(-10, 10, 3)
            if (x+y) % 6 < 2:
                arr[y, x] = np.clip(hc + n, 0, 255)
            else:
                arr[y, x] = np.clip(bc + n, 0, 255)
    arr = apply_3d_relief(arr, 0.3, 3.0)
    return arr2img(arr)

def gen_dirt_like(color, seed=1):
    """泥土类: dirt, coarse_dirt, rooted_dirt, podzol, mud"""
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    bc = np.array(color, dtype=float)
    n = perlin(seed, 4)
    for y in range(SIZE):
        for x in range(SIZE):
            v = n[y, x]
            c = bc + (v - 0.5) * 30
            if np.random.rand() < 0.06:
                c += 10
            arr[y, x] = np.clip(c, 0, 255)
    arr = apply_3d_relief(arr, 0.22, 3.0)
    return arr2img(arr)

# ============================================================
# 颜色常量
# ============================================================

MC_COLORS = {
    "white":      [235, 230, 220],
    "light_gray": [180, 175, 165],
    "gray":       [100, 95, 90],
    "black":      [25, 20, 25],
    "brown":      [130, 90, 55],
    "red":        [180, 45, 45],
    "orange":     [240, 120, 25],
    "yellow":     [240, 225, 55],
    "lime":       [110, 190, 35],
    "green":      [55, 130, 30],
    "cyan":       [40, 180, 185],
    "light_blue": [100, 160, 230],
    "blue":       [45, 55, 180],
    "purple":     [140, 45, 195],
    "magenta":    [195, 55, 175],
    "pink":       [230, 140, 165],
}

# ============================================================
# 主方块列表 - 按类别
# ============================================================

def all_blocks():
    blocks = {}
    
    # ---- 天然石 ----
    blocks["stone"] =              lambda: gen_noise_block([128, 128, 128], 30, 1)
    blocks["cobblestone"] =        lambda: gen_cobble_like([140, 135, 130], [90, 85, 80], 1)
    blocks["mossy_cobblestone"] =  lambda: gen_cobble_like([130, 140, 110], [70, 85, 60], 99)
    blocks["smooth_stone"] =       lambda: gen_noise_block([160, 160, 160], 15, 2)
    blocks["stone_bricks"] =       lambda: gen_brick([155, 152, 148], [100, 98, 95])
    blocks["cracked_stone_bricks"]=lambda: gen_brick([140, 137, 133], [80, 78, 75], 10)
    blocks["mossy_stone_bricks"] = lambda: gen_brick([140, 145, 120], [75, 80, 60], 20)
    blocks["chiseled_stone_bricks"]=lambda: gen_noise_block([150, 148, 145], 20, 3)
    
    # 安山岩/闪长岩/花岗岩
    blocks["andesite"] =           lambda: gen_noise_block([140, 138, 135], 28, 4)
    blocks["polished_andesite"] =  lambda: gen_noise_block([155, 153, 150], 12, 5)
    blocks["diorite"] =            lambda: gen_noise_block([190, 188, 186], 25, 6)
    blocks["polished_diorite"] =   lambda: gen_noise_block([200, 198, 196], 10, 7)
    blocks["granite"] =            lambda: gen_noise_block([170, 130, 120], 30, 8)
    blocks["polished_granite"] =   lambda: gen_noise_block([185, 145, 135], 12, 9)
    
    # 深板岩系列
    blocks["deepslate"] =          lambda: gen_noise_block([70, 70, 75], 20, 10)
    blocks["cobbled_deepslate"] =  lambda: gen_cobble_like([80, 80, 85], [55, 55, 58], 11)
    blocks["polished_deepslate"] = lambda: gen_noise_block([85, 85, 90], 10, 12)
    blocks["deepslate_bricks"] =   lambda: gen_brick([75, 75, 80], [55, 55, 58], 14)
    blocks["cracked_deepslate_bricks"] = lambda: gen_brick([65, 65, 70], [48, 48, 50], 15)
    blocks["deepslate_tiles"] =    lambda: gen_noise_block([80, 80, 85], 12, 16)
    blocks["cracked_deepslate_tiles"] = lambda: gen_noise_block([68, 68, 72], 15, 17)
    blocks["chiseled_deepslate"] = lambda: gen_noise_block([78, 78, 82], 10, 18)
    
    # 其他石类
    blocks["tuff"] =               lambda: gen_noise_block([110, 108, 100], 25, 13)
    blocks["polished_tuff"] =      lambda: gen_noise_block([125, 123, 115], 10, 19)
    blocks["tuff_bricks"] =        lambda: gen_brick([115, 113, 105], [85, 83, 75], 20)
    blocks["calcite"] =            lambda: gen_noise_block([235, 232, 225], 15, 21)
    blocks["dripstone_block"] =    lambda: gen_noise_block([160, 140, 110], 22, 22)
    blocks["bedrock"] =            lambda: gen_noise_block([50, 50, 50], 15, 23)
    
    # ---- 矿石 ----
    blocks["coal_ore"] =           lambda: gen_ore([120,120,120], [25,25,25], 100)
    blocks["iron_ore"] =           lambda: gen_ore([120,120,120], [200,170,150], 101)
    blocks["gold_ore"] =           lambda: gen_ore([120,120,120], [240,200,50], 102)
    blocks["diamond_ore"] =        lambda: gen_ore([120,120,120], [100,230,240], 103)
    blocks["emerald_ore"] =        lambda: gen_ore([120,120,120], [50,210,100], 104)
    blocks["lapis_ore"] =          lambda: gen_ore([120,120,120], [40,50,180], 105)
    blocks["redstone_ore"] =       lambda: gen_ore([120,120,120], [200,30,30], 106)
    blocks["copper_ore"] =         lambda: gen_ore([120,120,120], [200,120,80], 107)
    
    # 深板岩矿石
    for name, ore_c in [
        ("deepslate_coal_ore", [25,25,25]),
        ("deepslate_iron_ore", [200,170,150]),
        ("deepslate_gold_ore", [240,200,50]),
        ("deepslate_diamond_ore", [100,230,240]),
        ("deepslate_emerald_ore", [50,210,100]),
        ("deepslate_lapis_ore", [40,50,180]),
        ("deepslate_redstone_ore", [200,30,30]),
        ("deepslate_copper_ore", [200,120,80]),
    ]:
        blocks[name] = (lambda c=ore_c: gen_ore([70,70,75], c, 200))
    
    # 下界矿石
    blocks["nether_gold_ore"] =    lambda: gen_ore([120,40,40], [240,200,50], 300)
    blocks["nether_quartz_ore"] =  lambda: gen_ore([120,40,40], [230,225,210], 301)
    blocks["ancient_debris"] =     lambda: gen_ore([120,40,40], [140,90,70], 302)
    
    # ---- 金属块 ----
    blocks["iron_block"] =         lambda: gen_metal_block([220,220,220])
    blocks["gold_block"] =         lambda: gen_metal_block([250,210,50], [150,110,30])
    blocks["diamond_block"] =      lambda: gen_metal_block([80,210,230], [50,130,150])
    blocks["emerald_block"] =      lambda: gen_metal_block([40,195,100], [20,100,50])
    blocks["netherite_block"] =    lambda: gen_metal_block([70,50,50], [35,25,25])
    blocks["lapis_block"] =        lambda: gen_metal_block([40,60,190], [20,35,120])
    blocks["redstone_block"] =     lambda: gen_metal_block([200,30,30], [120,15,15])
    blocks["coal_block"] =         lambda: gen_metal_block([35,35,35], [15,15,15])
    
    # 铜系列
    blocks["copper_block"] =       lambda: gen_metal_block([210,130,80], [130,70,40])
    blocks["exposed_copper"] =     lambda: gen_metal_block([160,140,120], [100,80,60])
    blocks["weathered_copper"] =   lambda: gen_metal_block([100,130,110], [60,80,65])
    blocks["oxidized_copper"] =    lambda: gen_metal_block([70,130,140], [40,80,90])
    blocks["cut_copper"] =         lambda: gen_metal_block([210,135,85], [130,75,45])
    blocks["exposed_cut_copper"] = lambda: gen_metal_block([165,145,125], [105,85,65])
    blocks["weathered_cut_copper"]=lambda: gen_metal_block([105,135,115], [65,85,70])
    blocks["oxidized_cut_copper"] =lambda: gen_metal_block([75,135,145], [45,85,95])
    
    # ---- 泥土类 ----
    blocks["dirt"] =               lambda: gen_dirt_like([135,100,65])
    blocks["coarse_dirt"] =        lambda: gen_dirt_like([122,90,55], 10)
    blocks["rooted_dirt"] =        lambda: gen_dirt_like([125,95,60], 20)
    blocks["podzol_top"] =         lambda: gen_dirt_like([100,75,35], 30)
    blocks["mycelium_top"] =       lambda: gen_dirt_like([110,90,100], 40)
    blocks["mud"] =                lambda: gen_dirt_like([70,55,40], 50)
    blocks["packed_mud"] =         lambda: gen_noise_block([115,95,70], 18, 50)
    blocks["mud_bricks"] =         lambda: gen_brick([120,100,75], [90,70,50], 55)
    
    # 草地
    blocks["grass_block_top"] =    lambda: gen_noise_block([100,165,60], 28, 60)
    blocks["dirt_path_top"] =      lambda: gen_noise_block([160,145,100], 20, 61)
    
    # ---- 沙类 ----
    blocks["sand"] =               lambda: gen_sand_like([230,215,155])
    blocks["red_sand"] =           lambda: gen_sand_like([200,120,55], 10)
    blocks["soul_sand"] =          lambda: gen_sand_like([60,45,35], 20)
    blocks["soul_soil"] =          lambda: gen_sand_like([55,40,30], 30)
    
    # 砂岩
    blocks["sandstone"] =          lambda: gen_noise_block([220,210,160], 18, 70)
    blocks["cut_sandstone"] =      lambda: gen_noise_block([225,215,165], 10, 71)
    blocks["smooth_sandstone"] =   lambda: gen_noise_block([230,220,170], 8, 72)
    blocks["chiseled_sandstone"] = lambda: gen_noise_block([210,200,155], 15, 73)
    blocks["red_sandstone"] =      lambda: gen_noise_block([190,110,45], 18, 80)
    blocks["cut_red_sandstone"] =  lambda: gen_noise_block([195,115,50], 10, 81)
    blocks["smooth_red_sandstone"]=lambda: gen_noise_block([200,120,55], 8, 82)
    
    # ---- 木板 ----
    wood_planks = {
        "oak_planks":      [190,150,90],
        "spruce_planks":   [140,110,70],
        "birch_planks":    [210,195,150],
        "jungle_planks":   [180,140,100],
        "acacia_planks":   [185,120,60],
        "dark_oak_planks": [90,65,40],
        "mangrove_planks": [150,60,45],
        "cherry_planks":   [220,170,175],
        "bamboo_planks":   [195,185,115],
        "crimson_planks":  [130,60,90],
        "warped_planks":   [50,100,110],
    }
    for name, color in wood_planks.items():
        blocks[name] = (lambda c=color: gen_planks(c))
    blocks["bamboo_mosaic"] = lambda: gen_planks([190,180,110], 77)
    
    # ---- 原木侧面 ----
    log_side_colors = {
        "oak_log":         [170,130,70],
        "spruce_log":      [120,90,50],
        "birch_log":       [200,190,145],
        "jungle_log":      [160,120,80],
        "acacia_log":      [140,90,45],
        "dark_oak_log":    [70,50,30],
        "mangrove_log":    [120,50,35],
        "cherry_log":      [170,120,125],
        "crimson_stem":    [120,50,80],
        "warped_stem":     [40,90,100],
    }
    for name, color in log_side_colors.items():
        blocks[name] = (lambda c=color: gen_log_side(c))
    
    # ---- 原木顶部 ----
    log_top_colors = {
        "oak_log_top":            [180,140,75],
        "spruce_log_top":         [130,95,55],
        "birch_log_top":          [215,205,160],
        "jungle_log_top":         [170,130,90],
        "acacia_log_top":         [150,95,50],
        "dark_oak_log_top":       [80,55,35],
        "mangrove_log_top":       [130,55,40],
        "cherry_log_top":         [180,130,135],
        "crimson_stem_top":       [130,55,85],
        "warped_stem_top":        [45,95,105],
    }
    for name, color in log_top_colors.items():
        blocks[name] = (lambda c=color: gen_log_top(c))
    
    # ---- 砖类 ----
    blocks["bricks"] =             lambda: gen_brick([175,70,45], [130,120,110])
    blocks["nether_bricks"] =      lambda: gen_brick([95,40,45], [55,25,30], 90)
    blocks["red_nether_bricks"] =  lambda: gen_brick([120,35,40], [70,25,28], 91)
    blocks["end_stone_bricks"] =   lambda: gen_brick([225,225,190], [190,190,155], 95)
    
    # ---- 下界 ----
    blocks["netherrack"] =         lambda: gen_netherrack_like([130,50,50], 200)
    blocks["crimson_nylium"] =     lambda: gen_netherrack_like([140,30,40], 201)
    blocks["warped_nylium"] =      lambda: gen_netherrack_like([45,85,95], 202)
    blocks["basalt"] =             lambda: gen_noise_block([80,80,85], 15, 203)
    blocks["polished_basalt"] =    lambda: gen_noise_block([90,90,95], 8, 204)
    blocks["smooth_basalt"] =      lambda: gen_noise_block([85,85,90], 6, 205)
    blocks["blackstone"] =         lambda: gen_cobble_like([65,60,65], [40,38,42], 206)
    blocks["polished_blackstone"] =lambda: gen_noise_block([75,70,75], 10, 207)
    blocks["blackstone_bricks"] =  lambda: gen_brick([70,65,70], [45,42,45], 208)
    blocks["gilded_blackstone"] =  lambda: gen_cobble_like([65,60,65], [40,38,42], 209) # simplified
    blocks["magma"] =             lambda: gen_glow_like([150,80,20], 'grid', 210)
    blocks["glowstone"] =         lambda: gen_glow_like([210,180,80], 'grid', 211)
    blocks["shroomlight"] =       lambda: gen_glow_like([250,170,80], 'grid', 212)
    
    # ---- 末地 ----
    blocks["end_stone"] =          lambda: gen_noise_block([225,225,195], 15, 300)
    
    # ---- 黑曜石 ----
    blocks["obsidian"] =           lambda: gen_obsidian_like([30,20,35], [80,40,90])
    blocks["crying_obsidian"] =    lambda: gen_obsidian_like([30,20,35], [150,80,240], 310)
    
    # ---- 海晶 ----
    blocks["prismarine"] =         lambda: gen_noise_block([90,170,160], 22, 400)
    blocks["prismarine_bricks"] =  lambda: gen_brick([100,180,170], [70,140,130], 401)
    blocks["dark_prismarine"] =    lambda: gen_noise_block([50,100,90], 18, 402)
    blocks["sea_lantern"] =        lambda: gen_glow_like([200,230,240], 'grid', 403)
    
    # ---- 陶瓦 (16色) ----
    for color_name, rgb in MC_COLORS.items():
        blocks[f"{color_name}_terracotta"] = (lambda c=rgb: gen_terracotta(c))
    blocks["terracotta"] = lambda: gen_terracotta([180,120,90])
    
    # ---- 混凝土 (16色) ----
    for color_name, rgb in MC_COLORS.items():
        blocks[f"{color_name}_concrete"] = (lambda c=rgb: gen_concrete(c))
    
    # ---- 羊毛 (16色) ----
    for color_name, rgb in MC_COLORS.items():
        blocks[f"{color_name}_wool"] = (lambda c=rgb: gen_wool(c))
    
    # ---- 玻璃 ----
    blocks["glass"] = lambda: gen_glass([220,230,240], 80)
    blocks["tinted_glass"] = lambda: gen_glass([80,80,90], 200)
    for color_name, rgb in MC_COLORS.items():
        blocks[f"{color_name}_stained_glass"] = (lambda c=rgb: gen_glass(c, 160))
    
    # ---- 特殊功能方块 ----
    blocks["bookshelf"] =          lambda: gen_planks([180,145,85], 500)
    blocks["crafting_table"] =     lambda: gen_planks([185,150,90], 501)
    blocks["furnace"] =            lambda: gen_noise_block([120,120,120], 20, 502)
    blocks["gravel"] =             lambda: gen_sand_like([135,130,125], 40)
    blocks["clay"] =               lambda: gen_noise_block([160,165,175], 15, 503)
    
    # ---- 其他 ----
    blocks["purpur_block"] =       lambda: gen_noise_block([190,160,210], 15, 600)
    blocks["purpur_pillar"] =      lambda: gen_noise_block([185,155,205], 12, 601)
    blocks["honeycomb_block"] =    lambda: gen_noise_block([220,170,50], 20, 602)
    blocks["honey_block"] =        lambda: gen_glass([240,190,40], 180, 603)  # translucent sticky
    
    return blocks

# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    blocks = all_blocks()
    print(f"\n  灵动:视效 — 全方块 3D 立体纹理生成")
    print(f"  共 {len(blocks)} 个方块纹理\n")
    
    ok = 0
    for name, func in blocks.items():
        try:
            img = func()
            save(img, name)
            ok += 1
            if ok % 20 == 0:
                print(f"  ... {ok}/{len(blocks)}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    
    print(f"\n  完成! 成功: {ok}/{len(blocks)}")
    print(f"  输出: {OUTPUT.resolve()}\n")
