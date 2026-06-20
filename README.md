# 灵动:视效 - Lively Visual Effects

## 🎨 项目简介

**灵动:视效** 是一套为 Minecraft 精心打造的 PBR（基于物理渲染）材质包及其专属光影系统。  

设计理念:

> *"在不魔改原版画风的前提下，给所有方块加上真实的质感"*

---

## ✨ 核心特性

### 材质包 (Texture Pack)
- **原版风格 PBR** — 忠实于 Minecraft 原版视觉，仅增强材质质感
- **完整 PBR 贴图** — Normal Map（法线）、MER Map（金属/发光/粗糙）、Height Map（高度）、Specular Map（反射）
- **多分辨率支持** — 64x / 128x / 256x 三档可选
- **双版本兼容** — 支持 Java 版（Iris/Optifine/Oculus）和基岩版 RTX
- **智能材质分类** — 自动识别石质、木质、金属、泥土、发光等材质类型

### 专属光影 (Shader Pack)
- **完整 PBR 渲染管线** — Cook-Torrance BRDF + GGX 分布
- **体积光 (Volumetric Light)** — 真实的大气散射和丁达尔效应
- **屏幕空间反射 (SSR)** — 金属、水面等光滑表面的实时反射
- **环境光遮蔽 (SSAO)** — 增强场景深度感
- **柔阴影 (PCF Shadow)** — 5x5 百分比渐近滤波软阴影
- **泛光效果 (Bloom)** — ACES 色调映射 + 色彩分级
- **动态水面** — 带波浪法线、菲涅尔反射、焦散模拟的水渲染

---

## 📁 项目结构

```
Lively-Visual-Effects/
├── texture_pack/              # PBR 材质包
│   ├── manifest.json          # 基岩版清单
│   ├── pack.mcmeta            # Java 版清单
│   ├── pack_icon.png          # 材质包图标
│   ├── textures/
│   │   ├── texture_list.json  # PBR 贴图定义
│   │   ├── terrain_texture.json
│   │   └── blocks/            # PBR 贴图文件
│   │       ├── stone.png      # 颜色贴图
│   │       ├── stone_n.png    # 法线贴图
│   │       ├── stone_mer.png  # 金属/发光/粗糙
│   │       ├── stone_s.png    # 反射贴图 (LabPBR)
│   │       └── ...
│   └── subpacks/              # 分辨率变体
│       ├── 64x/
│       ├── 128x/
│       └── 256x/
├── shader_pack/               # 专属光影
│   ├── shaders/
│   │   ├── shaders.properties # 光影配置
│   │   ├── gbuffers_terrain.* # 地形渲染
│   │   ├── gbuffers_water.*   # 水面渲染
│   │   ├── composite*.fsh     # 多通道合成
│   │   ├── shadow.*           # 阴影映射
│   │   ├── final.*            # 后处理输出
│   │   └── lib/               # 着色器库
│   │       ├── pbr.glsl       # PBR 材质系统
│   │       ├── lighting.glsl  # 光照计算
│   │       └── util.glsl      # 工具函数
│   └── shader.properties
├── tools/
│   ├── generate_pbr.py        # PBR 贴图生成器
│   └── requirements.txt
└── README.md
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd tools
pip install -r requirements.txt
```

### 2. 生成 PBR 贴图

```bash
# 生成示例贴图用于测试
python generate_pbr.py --samples

# 从你的原版贴图生成 PBR 版本
python generate_pbr.py --input /path/to/vanilla/textures --output ../texture_pack

# 只生成材质包图标
python generate_pbr.py --icon
```

### 3. 使用材质包

**Java 版 (Iris/Optifine)**:
1. 将 `texture_pack/` 文件夹复制到 `.minecraft/resourcepacks/`
2. 在游戏设置中启用 "灵动:视效" 材质包
3. 搭配 Iris 或 Optifine 使用光影

**基岩版 (Bedrock RTX)**:
1. 将 `texture_pack/` 作为 `.mcpack` 导入
2. 在全局资源中启用
3. 需要支持 RTX 的设备

### 4. 使用专属光影

**Java 版 (Iris)**:
1. 将 `shader_pack/` 文件夹复制到 `.minecraft/shaderpacks/`
2. 在 Iris 设置中选择 "灵动:视效"
3. 确保材质包同步启用

---

## 🎯 PBR 材质标准

本材质包支持以下 PBR 贴图格式：

| 贴图 | 文件名 | 格式 | 说明 |
|------|--------|------|------|
| 颜色 | `name.png` | RGB(A) | 基础颜色/反照率 |
| 法线 | `name_n.png` | RGB | 切线空间法线贴图 |
| MER | `name_mer.png` | RGB | R=金属度 G=自发光 B=粗糙度 |
| 反射 | `name_s.png` | RGBA | LabPBR 反射/光滑度 |
| 高度 | `name_heightmap.png` | L | 视差贴图高度 |

---

## 🎨 材质分类（零雾老师风格）

| 类别 | 粗糙度 | 金属度 | 高度强度 | 代表方块 |
|------|--------|--------|----------|----------|
| 石质 | 0.55-0.90 | 0.0 | 0.2-0.6 | stone, cobblestone, deepslate |
| 木质 | 0.60-0.75 | 0.0 | 0.1-0.3 | planks, logs |
| 泥土 | 0.85-0.95 | 0.0 | 0.1-0.3 | dirt, sand, gravel |
| 砖块 | 0.55-0.60 | 0.0 | 0.2 | bricks, nether_bricks |
| 金属 | 0.10-0.25 | 0.7-1.0 | 0.03-0.05 | iron, gold, diamond blocks |
| 玻璃 | 0.05 | 0.0 | 0.0 | glass |
| 发光 | 0.20-0.60 | 0.0-0.6 | 0.05-0.2 | glowstone, redstone_block |

---

## 📝 技术参考

- **零雾构想 (ZeroPBR)** by 零雾05_Fogg05 — 原版 PBR 材质设计理念
- **LabPBR 1.3** — Java 版 PBR 材质标准
- **NVIDIA Minecraft RTX PBR Guide** — 基岩版 RTX PBR 规范
- **Cook-Torrance BRDF** — 基于物理的反射模型
- **GGX/Trowbridge-Reitz NDF** — 微面元法线分布

---

## 📄 许可

本项目遵循 MIT License 开源协议。  
材质包设计理念学习自零雾老师的作品，本项目为独立创作。

---

**灵动:视效** — 让 MC 的每一块方块，都拥有真实的灵魂 ✨
