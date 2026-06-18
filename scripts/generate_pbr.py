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
    "stone":       {"smoothness": 40,  "metalness": 0,   "emission": 0},
    "cobblestone": {"smoothness": 35,  "metalness": 0,   "emission": 0},
    "dirt":        {"smoothness": 15,  "metalness": 0,   "emission": 0},
    "grass":       {"smoothness": 20,  "metalness": 0,   "emission": 0},
    "sand":        {"smoothness": 25,  "metalness": 0,   "emission": 0},
    "gravel":      {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "wood":        {"smoothness": 60,  "metalness": 0,   "emission": 0},
    "planks":      {"smoothness": 50,  "metalness": 0,   "emission": 0},
    "glass":       {"smoothness": 255, "metalness": 0,   "emission": 0},
    "water":       {"smoothness": 255, "metalness": 0,   "emission": 0},
    "ice":         {"smoothness": 220, "metalness": 0,   "emission": 0},
    "iron":        {"smoothness": 160, "metalness": 255, "emission": 0},
    "gold":        {"smoothness": 200, "metalness": 255, "emission": 0},
    "copper":      {"smoothness": 140, "metalness": 255, "emission": 0},
    "diamond":     {"smoothness": 230, "metalness": 200, "emission": 0},
    "emerald":     {"smoothness": 210, "metalness": 180, "emission": 0},
    "netherite":   {"smoothness": 180, "metalness": 255, "emission": 0},
    "glowstone":   {"smoothness": 60,  "metalness": 0,   "emission": 255},
    "shroomlight": {"smoothness": 50,  "metalness": 0,   "emission": 255},
    "sealantern":  {"smoothness": 100, "metalness": 0,   "emission": 255},
    "redstone":    {"smoothness": 30,  "metalness": 0,   "emission": 128},
    "lapis":       {"smoothness": 100, "metalness": 80,  "emission": 0},
    "obsidian":    {"smoothness": 120, "metalness": 0,   "emission": 0},
    "clay":        {"smoothness": 30,  "metalness": 0,   "emission": 0},
    "wool":        {"smoothness": 5,   "metalness": 0,   "emission": 0},
    "concrete":    {"smoothness": 20,  "metalness": 0,   "emission": 0},
    "brick":       {"smoothness": 45,  "metalness": 0,   "emission": 0},
    "terracotta":  {"smoothness": 40,  "metalness": 0,   "emission": 0},
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
    strength: float = 5.0,
    blur: float = 0.5,
) -> Image.Image:
    """
    从基础颜色贴图生成切线空间法线贴图（OpenGL 格式，Y+）。
    
    步骤:
    1. 转换为灰度图（亮度）
    2. 轻微模糊去噪
    3. Sobel 算子计算梯度
    4. 构建法线向量并归一化
    5. 映射到 [0, 255] RGB 空间
    """
    # 转灰度 + 模糊
    gray = image.convert("L")
    if blur > 0:
        gray = gray.filter(ImageFilter.GaussianBlur(radius=blur))
    gray_arr = np.array(gray, dtype=np.float32) / 255.0

    # Sobel 梯度
    gx = ndimage.sobel(gray_arr, axis=1) * strength
    gy = ndimage.sobel(gray_arr, axis=0) * strength

    # 法线向量 (切线空间)
    nx = -gx
    ny = -gy  # OpenGL: Y+
    nz = np.ones_like(gray_arr)

    # 归一化
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    length = np.maximum(length, 1e-8)
    nx /= length
    ny /= length
    nz /= length

    # 映射到 [0, 1]
    nx = nx * 0.5 + 0.5
    ny = ny * 0.5 + 0.5
    nz = nz * 0.5 + 0.5

    # 组合为 RGB
    normal = np.stack([nx, ny, nz], axis=2)
    normal = np.clip(normal * 255, 0, 255).astype(np.uint8)

    return Image.fromarray(normal, "RGB")


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

    # R: Smoothness — 亮区更光滑，暗区更粗糙
    base_s = material["smoothness"]
    smoothness = base_s + (luminance - 0.5) * variation * 2
    smoothness = np.clip(smoothness, 0, 255)

    # G: Metalness — 金属材质按亮度微调
    base_m = material["metalness"]
    if base_m > 0:
        metalness = base_m + (luminance - 0.5) * variation
        metalness = np.clip(metalness, 0, 255)
    else:
        metalness = np.full_like(smoothness, 0, dtype=np.float32)

    # B: Emission — 发光材质按亮度微调
    base_e = material["emission"]
    if base_e > 0:
        emission = base_e + (luminance - 0.5) * 255
        emission = np.clip(emission, 0, 255)
    else:
        emission = np.full_like(smoothness, 0, dtype=np.float32)

    # A: 255
    alpha = np.full_like(smoothness, 255, dtype=np.float32)

    specular = np.stack([smoothness, metalness, emission, alpha], axis=2)
    specular = np.clip(specular, 0, 255).astype(np.uint8)

    return Image.fromarray(specular, "RGBA")


# ============================================================
# 主逻辑
# ============================================================


def detect_material(filename: str) -> str | None:
    """根据文件名自动推断材质类型。"""
    name = Path(filename).stem.lower()
    for key in sorted(MATERIAL_PRESETS.keys(), key=len, reverse=True):
        if key in name:
            return key
    return None


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
    for img_path in image_files:
        # 确定材质预设
        material_name = args.material or detect_material(img_path.name)
        if material_name and material_name not in MATERIAL_PRESETS:
            print(f"⚠ 未知材质 '{material_name}'，使用 stone 预设")
            material_name = "stone"
        if not material_name:
            material_name = "stone"

        material = MATERIAL_PRESETS[material_name]
        print(f"[{material_name:12}] {img_path.name}  ", end="")

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
            print(f"→ {'  '.join(results)}")
        except Exception as e:
            print(f"✗ 处理失败: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"  完成! 成功: {len(image_files) - failed} 组, 失败: {failed}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
