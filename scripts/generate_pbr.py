#!/usr/bin/env python3
"""
灵动:视效 — PBR 贴图批量生成工具
===================================
从基础颜色贴图自动生成 labPBR 1.3 标准格式的:
  - 法线贴图 (Normal Map, _n.png)
  - 镜面/金属/发光贴图 (Specular Map, _s.png)

用法:
  python generate_pbr.py --input ./source/ --output ./output/
  python generate_pbr.py --input ./source/ --output ./output/ --material stone
  python generate_pbr.py --input ./source/ --output ./output/ --material iron
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# ============================================================
# 材质预设: 定义不同材质的 PBR 参数
# ============================================================

MATERIAL_PRESETS: dict[str, dict[str, int]] = {
    # 天然石类
    "stone":        {"smoothness": 40,  "metalness": 0,   "emission": 0},
    "cobblestone":  {"smoothness": 35,  "metalness": 0,   "emission": 0},
    "andesite":     {"smoothness": 35,  "metalness": 0,   "emission": 0},
    "diorite":      {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "granite":      {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "deepslate":    {"smoothness": 50,  "metalness": 0,   "emission": 0},
    "tuff":         {"smoothness": 25,  "metalness": 0,   "emission": 0},
    "calcite":      {"smoothness": 45,  "metalness": 0,   "emission": 0},
    "dripstone":    {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "bedrock":      {"smoothness": 100, "metalness": 0,   "emission": 0},
    "sandstone":    {"smoothness": 20,  "metalness": 0,   "emission": 0},
    "red_sandstone": {"smoothness": 20, "metalness": 0,   "emission": 0},
    "basalt":       {"smoothness": 80,  "metalness": 0,   "emission": 0},
    "blackstone":   {"smoothness": 45,  "metalness": 0,   "emission": 0},
    "end_stone":    {"smoothness": 25,  "metalness": 0,   "emission": 0},
    "purpur":       {"smoothness": 50,  "metalness": 0,   "emission": 0},
    "quartz":       {"smoothness": 60,  "metalness": 0,   "emission": 0},
    "netherrack":   {"smoothness": 20,  "metalness": 0,   "emission": 0},
    "nylium":       {"smoothness": 18,  "metalness": 0,   "emission": 0},
    
    # 泥土/草地类
    "dirt":         {"smoothness": 15,  "metalness": 0,   "emission": 0},
    "mud":          {"smoothness": 10,  "metalness": 0,   "emission": 0},
    "podzol":       {"smoothness": 15,  "metalness": 0,   "emission": 0},
    "mycelium":     {"smoothness": 15,  "metalness": 0,   "emission": 0},
    "grass":        {"smoothness": 20,  "metalness": 0,   "emission": 0},
    "farmland":     {"smoothness": 10,  "metalness": 0,   "emission": 0},
    "dirt_path":    {"smoothness": 12,  "metalness": 0,   "emission": 0},
    
    # 沙砾类
    "sand":         {"smoothness": 25,  "metalness": 0,   "emission": 0},
    "gravel":       {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "soul_sand":    {"smoothness": 10,  "metalness": 0,   "emission": 0},
    "soul_soil":    {"smoothness": 12,  "metalness": 0,   "emission": 0},
    "clay":         {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "suspicious":   {"smoothness": 25,  "metalness": 0,   "emission": 0},
    
    # 木材类
    "planks":       {"smoothness": 50,  "metalness": 0,   "emission": 0},
    "wood":         {"smoothness": 60,  "metalness": 0,   "emission": 0},
    "log":          {"smoothness": 55,  "metalness": 0,   "emission": 0},
    "stem":         {"smoothness": 55,  "metalness": 0,   "emission": 0},
    "hyphae":       {"smoothness": 50,  "metalness": 0,   "emission": 0},
    "stripped":     {"smoothness": 45,  "metalness": 0,   "emission": 0},
    "bamboo":       {"smoothness": 55,  "metalness": 0,   "emission": 0},
    
    # 砖类
    "brick":        {"smoothness": 45,  "metalness": 0,   "emission": 0},
    "nether_brick": {"smoothness": 40,  "metalness": 0,   "emission": 0},
    
    # 混凝土/陶瓦
    "concrete":     {"smoothness": 20,  "metalness": 0,   "emission": 0},
    "terracotta":   {"smoothness": 40,  "metalness": 0,   "emission": 0},
    "glazed":       {"smoothness": 120, "metalness": 0,   "emission": 0},
    
    # 羊毛/地毯
    "wool":         {"smoothness": 5,   "metalness": 0,   "emission": 0},
    "carpet":       {"smoothness": 5,   "metalness": 0,   "emission": 0},
    
    # 金属类
    "iron":         {"smoothness": 160, "metalness": 255, "emission": 0},
    "gold":         {"smoothness": 200, "metalness": 255, "emission": 0},
    "copper":       {"smoothness": 140, "metalness": 255, "emission": 0},
    "diamond":      {"smoothness": 230, "metalness": 200, "emission": 0},
    "emerald":      {"smoothness": 210, "metalness": 180, "emission": 0},
    "netherite":    {"smoothness": 180, "metalness": 255, "emission": 0},
    "lapis":        {"smoothness": 100, "metalness": 80,  "emission": 0},
    "redstone":     {"smoothness": 30,  "metalness": 0,   "emission": 128},
    "coal":         {"smoothness": 40,  "metalness": 50,  "emission": 0},
    
    # 矿石类
    "ore":          {"smoothness": 45,  "metalness": 100, "emission": 0},
    "debris":       {"smoothness": 150, "metalness": 255, "emission": 0},
    
    # 玻璃/透明类
    "glass":        {"smoothness": 255, "metalness": 0,   "emission": 0},
    "ice":          {"smoothness": 220, "metalness": 0,   "emission": 0},
    "water":        {"smoothness": 255, "metalness": 0,   "emission": 0},
    
    # 发光类
    "glowstone":    {"smoothness": 60,  "metalness": 0,   "emission": 255},
    "shroomlight":  {"smoothness": 50,  "metalness": 0,   "emission": 255},
    "sea_lantern":  {"smoothness": 100, "metalness": 0,   "emission": 255},
    "lantern":      {"smoothness": 180, "metalness": 200, "emission": 200},
    "magma":        {"smoothness": 40,  "metalness": 0,   "emission": 180},
    "lamp":         {"smoothness": 30,  "metalness": 0,   "emission": 128},
    "candle":       {"smoothness": 60,  "metalness": 0,   "emission": 200},
    "campfire":     {"smoothness": 60,  "metalness": 0,   "emission": 150},
    "fire":         {"smoothness": 255, "metalness": 0,   "emission": 255},
    "lava":         {"smoothness": 100, "metalness": 0,   "emission": 255},
    "beacon":       {"smoothness": 230, "metalness": 200, "emission": 200},
    "amethyst":     {"smoothness": 200, "metalness": 0,   "emission": 80},
    
    # 特殊类
    "obsidian":     {"smoothness": 120, "metalness": 0,   "emission": 0},
    "prismarine":   {"smoothness": 60,  "metalness": 0,   "emission": 20},
    "coral":        {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "moss":         {"smoothness": 10,  "metalness": 0,   "emission": 0},
    "honey":        {"smoothness": 200, "metalness": 0,   "emission": 20},
    "slime":        {"smoothness": 200, "metalness": 0,   "emission": 0},
    "snow":         {"smoothness": 15,  "metalness": 0,   "emission": 0},
    "nether_wart":  {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "wart":         {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "shroom":       {"smoothness": 20,  "metalness": 0,   "emission": 0},
    "fungus":       {"smoothness": 20,  "metalness": 0,   "emission": 0},
    "target":       {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "sculk":        {"smoothness": 5,   "metalness": 0,   "emission": 40},
    "respawn_anchor": {"smoothness": 100,"metalness": 0,   "emission": 150},
    "sponge":       {"smoothness": 5,   "metalness": 0,   "emission": 0},
    "tnt":          {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "barrel":       {"smoothness": 50,  "metalness": 0,   "emission": 0},
    "bookshelf":    {"smoothness": 45,  "metalness": 0,   "emission": 0},
    "crafting":     {"smoothness": 50,  "metalness": 0,   "emission": 0},
    "furnace":      {"smoothness": 40,  "metalness": 50,  "emission": 0},
    "dispenser":    {"smoothness": 40,  "metalness": 50,  "emission": 0},
    "dropper":      {"smoothness": 40,  "metalness": 50,  "emission": 0},
    "observer":     {"smoothness": 40,  "metalness": 50,  "emission": 0},
    "piston":       {"smoothness": 50,  "metalness": 80,  "emission": 0},
    "hopper":       {"smoothness": 120, "metalness": 200, "emission": 0},
    "rail":         {"smoothness": 150, "metalness": 255, "emission": 0},
    "anvil":        {"smoothness": 130, "metalness": 255, "emission": 0},
    "chain":        {"smoothness": 150, "metalness": 255, "emission": 0},
    "cauldron":     {"smoothness": 140, "metalness": 255, "emission": 0},
    "bell":         {"smoothness": 200, "metalness": 255, "emission": 0},
}

# ============================================================
# 色彩空间转换
# ============================================================


def rgb_to_luminance(rgb: np.ndarray) -> np.ndarray:
    """将 RGB 图像转为亮度通道 (0-1)。"""
    return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]


# ============================================================
# 法线贴图生成
# ============================================================


def generate_normal_map(
    image: Image.Image,
    strength: float = 3.0,
    blur: float = 0.6,
) -> Image.Image:
    """
    从基础颜色贴图生成切线空间法线贴图（OpenGL 格式，Y+）。
    
    改进算法:
    1. 转为灰度图，强模糊去掉高频颜色噪点
    2. 边缘检测找结构性凹凸（砖缝、木纹、石缝）
    3. 低频分量做柔和地形
    4. 组合为高度图，再 Sobel 计算法线
    """
    # 转灰度
    gray = np.array(image.convert("L"), dtype=np.float32) / 255.0
    
    # 多层模糊：强模糊→低频大形状，保留高频做细节
    if blur > 0:
        gray_pil = Image.fromarray((gray * 255).astype(np.uint8))
        
        # 低频分量: 强模糊，代表大块形状
        low_freq = np.array(
            gray_pil.filter(ImageFilter.GaussianBlur(radius=blur * 3)),
            dtype=np.float32
        ) / 255.0
        
        # 中频分量: 中等模糊，保留纹理结构
        mid_freq = np.array(
            gray_pil.filter(ImageFilter.GaussianBlur(radius=blur)),
            dtype=np.float32
        ) / 255.0
        
        # 高频分量 = 原始灰度 - 中频（细节/噪点，大幅压缩）
        high_freq = gray - mid_freq
        high_freq = np.clip(high_freq, -0.15, 0.15) * 0.3  # 压制高频
        
        # 高度图 = 低频为主 + 少量高频细节
        height = low_freq * 0.7 + mid_freq * 0.2 + high_freq * 0.1
    else:
        height = gray
    
    # Sobel 梯度
    gx = ndimage.sobel(height, axis=1) * strength
    gy = ndimage.sobel(height, axis=0) * strength
    
    # 限制最大梯度（防止法线过度倾斜）
    gx = np.clip(gx, -3.0, 3.0)
    gy = np.clip(gy, -3.0, 3.0)
    
    # 法线向量 (切线空间, OpenGL: Y+)
    nx = -gx
    ny = -gy
    nz = np.ones_like(height)
    
    # 归一化
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    length = np.maximum(length, 1e-8)
    nx /= length
    ny /= length
    nz /= length
    
    # 映射到 [0, 255]
    nx = nx * 0.5 + 0.5
    ny = ny * 0.5 + 0.5
    nz = nz * 0.5 + 0.5
    
    normal = np.stack([nx, ny, nz], axis=2)
    normal = np.clip(normal * 255, 0, 255).astype(np.uint8)
    
    return Image.fromarray(normal.astype(np.uint8))


# ============================================================
# 镜面/金属/发光贴图生成
# ============================================================


def generate_specular_map(
    image: Image.Image,
    material: dict[str, int],
    variation: float = 15.0,
) -> Image.Image:
    """
    生成 labPBR 1.3 格式的 _s.png 贴图。
    
    通道:
      R = Smoothness（基于亮度微调）
      G = Metalness（部分材质基于亮度微调）
      B = Emission（固定值或基于亮度）
      A = 255（完全不透明）
    """
    gray = np.array(image.convert("L"), dtype=np.float32)

    # 根据亮度在材质预设附近做微调，增加真实感
    luminance = gray / 255.0

    # Complementary 使用 G 通道做主光滑度!
    base_s = material["smoothness"]
    smoothness = base_s + (luminance - 0.5) * variation * 2
    smoothness = np.clip(smoothness, 0, 255)

    # R: 辅助金属度（Complementary 也用 R 做部分材质的 emission/smoothness）
    base_m = material["metalness"]
    if base_m > 0:
        metalness = base_m + (luminance - 0.5) * variation
        metalness = np.clip(metalness, 0, 255)
    else:
        # 非金属: R 也放光滑度（双通道兼容）
        metalness = smoothness.copy()

    # B: Emission（自发光）
    base_e = material["emission"]
    if base_e > 0:
        emission = base_e + (luminance - 0.5) * 255
        emission = np.clip(emission, 0, 255)
    else:
        emission = np.full_like(smoothness, 0, dtype=np.float32)

    # A: 255
    alpha = np.full_like(smoothness, 255, dtype=np.float32)

    # 注意通道顺序: R, G=smoothness, B, A
    specular = np.stack([metalness, smoothness, emission, alpha], axis=2)
    specular = np.clip(specular, 0, 255).astype(np.uint8)

    return Image.fromarray(specular)


# ============================================================
# 主逻辑
# ============================================================


# 检测优先级: 具体关键词 > 通用关键词
DETECT_ORDER = [
    "respawn_anchor", "sea_lantern", "soul_sand", "soul_soil", "red_sandstone",
    "nether_brick", "dirt_path", "end_stone", "shroomlight",
    "glowstone", "magma", "candle", "campfire", "lantern", "beacon", "amethyst",
    "debris", "netherite", "diamond", "emerald", "gold", "iron", "copper", "coal",
    "lapis", "redstone", "quartz",
    "cobblestone", "sandstone", "blackstone", "deepslate", "andesite", "diorite",
    "granite", "dripstone", "calcite", "basalt", "tuff", "bedrock",
    "obsidian", "prismarine", "purpur",
    "ore", "log", "stem", "hyphae", "planks", "bamboo", "stripped",
    "coral", "slime", "honey", "snow", "ice", "glass",
    "wool", "carpet",
    "concrete", "terracotta", "glazed",
    "brick", "mud", "clay",
    "dirt", "podzol", "mycelium", "grass", "farmland",
    "sand", "gravel", "suspicious",
    "netherrack", "nylium", "wart", "fungus", "shroom",
    "moss", "sculk", "sponge",
    "lava", "fire", "lamp",
    "barrel", "bookshelf", "crafting", "furnace", "dispenser", "dropper",
    "observer", "piston", "hopper", "rail", "anvil", "chain", "cauldron",
    "bell", "tnt", "target",
    "stone",
]

def detect_material(filename: str) -> str | None:
    """根据文件名自动推断材质类型。"""
    name = Path(filename).stem.lower()
    for key in DETECT_ORDER:
        if key in name:
            if key in MATERIAL_PRESETS:
                return key
            # 映射别名
            if key == "nether_brick":
                return "brick"
    return "stone"


def process_image(
    input_path: Path,
    output_dir: Path,
    material: dict[str, int],
    normal_strength: float,
    normal_blur: float,
    variation: float,
    overwrite: bool,
) -> tuple[str, str]:
    """处理单张图片，生成 _n 和 _s 贴图。"""
    base_name = input_path.stem
    img = Image.open(input_path).convert("RGBA")

    out_normal = output_dir / f"{base_name}_n.png"
    out_specular = output_dir / f"{base_name}_s.png"

    results = []

    # 法线贴图
    if overwrite or not out_normal.exists():
        normal_map = generate_normal_map(img, strength=normal_strength, blur=normal_blur)
        normal_map.save(out_normal, "PNG")
        results.append(f"✓ {out_normal.name}")
    else:
        results.append(f"⊙ {out_normal.name} (已存在，跳过)")

    # 镜面贴图
    if overwrite or not out_specular.exists():
        specular_map = generate_specular_map(img, material, variation=variation)
        specular_map.save(out_specular, "PNG")
        results.append(f"✓ {out_specular.name}")
    else:
        results.append(f"⊙ {out_specular.name} (已存在，跳过)")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="灵动:视效 - PBR 贴图批量生成工具 (labPBR 1.3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate_pbr.py -i ./source/ -o ./output/                   # 自动检测材质
  python generate_pbr.py -i ./source/ -o ./output/ -m iron            # 强制使用 iron 预设
  python generate_pbr.py -i ./source/ -o ./output/ -s 8.0 -b 0.3     # 自定义法线参数
  python generate_pbr.py -i ./source/ -o ./output/ --list-materials   # 列出所有材质预设
        """,
    )
    parser.add_argument("-i", "--input", help="输入目录（含基础颜色贴图）")
    parser.add_argument("-o", "--output", help="输出目录（生成的 PBR 贴图）")
    parser.add_argument("-m", "--material", help="强制指定材质类型（覆盖自动检测）")
    parser.add_argument("-s", "--normal-strength", type=float, default=5.0, help="法线强度 (默认: 5.0)")
    parser.add_argument("-b", "--normal-blur", type=float, default=0.5, help="法线预模糊半径 (默认: 0.5)")
    parser.add_argument("-v", "--variation", type=float, default=15.0, help="光滑度亮度变化幅度 (默认: 15.0)")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有贴图")
    parser.add_argument("--verbose", action="store_true", help="显示详细处理日志")
    parser.add_argument("--list-materials", action="store_true", help="列出所有可用材质预设并退出")

    args = parser.parse_args()

    # 列出材质预设
    if args.list_materials:
        print("\n可用材质预设:\n")
        print(f"{'名称':<16} {'光滑度':<10} {'金属度':<10} {'自发光':<10}")
        print("-" * 46)
        for name, params in MATERIAL_PRESETS.items():
            print(f"{name:<16} {params['smoothness']:<10} {params['metalness']:<10} {params['emission']:<10}")
        print()
        return

    # 检查必要参数
    if not args.input or not args.output:
        parser.error("需要同时指定 --input 和 --output")

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.is_dir():
        print(f"错误: 输入目录不存在: {input_dir}", file=sys.stderr)
        sys.exit(1)

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 收集所有 PNG 基础贴图（排除已有的 _n 和 _s 后缀）
    image_files = sorted(
        [f for f in input_dir.glob("*.png") if not f.stem.endswith(("_n", "_s", "_e"))]
    )

    if not image_files:
        print("错误: 输入目录中没有找到 PNG 贴图", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  灵动:视效 — PBR 贴图批量生成")
    print(f"  输入: {input_dir} ({len(image_files)} 张贴图)")
    print(f"  输出: {output_dir}")
    print(f"  格式: labPBR 1.3 (OpenGL 法线)")
    print(f"{'='*50}\n")

    # 逐一处理
    failed = 0
    for idx, img_path in enumerate(image_files):
        # 确定材质预设
        material_name = args.material or detect_material(img_path.name)
        if material_name not in MATERIAL_PRESETS:
            material_name = "stone"

        material = MATERIAL_PRESETS[material_name]

        try:
            results = process_image(
                img_path,
                output_dir,
                material,
                args.normal_strength,
                args.normal_blur,
                args.variation,
                args.overwrite,
            )
        except Exception as e:
            if args.verbose:
                print(f"  ✗ {img_path.name}: {e}")
            failed += 1
        
        if args.verbose or (idx + 1) % 100 == 0:
            print(f"  进度: {idx + 1}/{len(image_files)}  ({material_name})")

    print(f"\n{'='*50}")
    print(f"  完成! 成功: {len(image_files) - failed} 组, 失败: {failed}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
