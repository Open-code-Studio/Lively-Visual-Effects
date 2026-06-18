# 灵动:视效 — PBR 材质包

> **Lively Visual Effects** — 为 Minecraft Java 版打造的 PBR（基于物理渲染）材质包，专为 **Iris Shaders** 优化。

---

## ✨ 特性

- 🎨 **labPBR 1.3 标准** — 兼容主流光影（Iris / OptiFine）
- 🧱 **法线贴图** (`_n`) — 增强表面细节与立体感
- ✨ **反射/光滑度/金属度贴图** (`_s`) — 精确控制材质物理属性
- 🔧 **自动生成脚本** — 从基础颜色贴图批量生成 PBR 贴图
- 📦 **轻量化** — 按需安装，不臃肿

---

## 📁 项目结构

```
Lively-Visual-Effects/
├── pack.mcmeta          # 资源包元数据
├── pack.png             # 资源包图标
├── assets/
│   └── minecraft/
│       └── textures/
│           └── block/   # PBR 贴图文件（*.png, *_n.png, *_s.png）
├── scripts/
│   ├── generate_pbr.py  # PBR 贴图批量生成工具
│   └── requirements.txt # Python 依赖
└── docs/
    └── PBR_GUIDE.md     # PBR 格式详细指南
```

---

## 🚀 快速开始

### 1. 安装资源包

将整个项目文件夹复制到 Minecraft 的 `resourcepacks` 目录：

- **Windows**: `%APPDATA%\.minecraft\resourcepacks\`
- **macOS**: `~/Library/Application Support/minecraft/resourcepacks/`
- **Linux**: `~/.minecraft/resourcepacks/`

然后在游戏设置中启用「灵动:视效」资源包。

### 2. 生成 PBR 贴图（可选）

如果你有自己的基础颜色贴图，可以使用脚本自动生成 PBR 贴图：

```bash
cd scripts/
pip install -r requirements.txt
python generate_pbpython generate_pbr.py --input ../source/ --output ../assets/minecraft/textures/block/
```

---

## 🎨 PBR 贴图格式（labPBR 1.3）

| 文件 | 后缀 | 说明 |
|------|------|------|
| 基础颜色 | `stone.png` | 标准漫反射/反照率贴图 |
| 法线贴图 | `stone_n.png` | 切线空间法线（OpenGL 格式，Y+ 向上） |
| 镜面反射 | `stone_s.png` | R=光滑度, G=金属度, B=自发光强度 |

### 通道详解 `_s.png`

| 通道 | 含义 | 值范围 | 说明 |
|------|------|--------|------|
| **R** | 光滑度 (Smoothness) | 0-255 | 0=完全粗糙, 255=镜面光滑 |
| **G** | 金属度 (Metalness) | 0-255 | 0=非金属, 255=完全金属 |
| **B** | 自发光 (Emission) | 0-255 | 0=不发光, 255=全亮 |
| **A** | 次表面散射 (可选) | 0-255 | 仅透明/半透明材质使用 |

---

## 📋 材质分类参考

| 材质类型 | 光滑度 (R) | 金属度 (G) | 自发光 (B) |
|----------|-----------|-----------|-----------|
| 石头 | 30-60 | 0 | 0 |
| 泥土/草地 | 10-30 | 0 | 0 |
| 木板 | 40-80 | 0 | 0 |
| 铁块 | 120-180 | 255 | 0 |
| 金块 | 180-220 | 255 | 0 |
| 玻璃 | 200-255 | 0 | 0 |
| 萤石 | 50-80 | 0 | 255 |
| 水 | 255 | 0 | 0 |

---

## 🔗 兼容的光影包

- [Iris Shaders](https://irisshaders.dev/)（推荐）
- [Complementary Reimagined](https://www.complementary.dev/reimagined/)
- [BSL Shaders](https://bitslablab.com/bslshaders/)
- [SEUS PTGI](https://www.sonicether.com/seus/)
- 任何支持 labPBR 1.3 标准的光影包

---

## 📝 贡献

欢迎提交 PR 改进贴图或脚本工具。请确保所有贴图为 16×16 像素（或更高倍数），PNG 格式。

---

## 📄 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 开源协议。

---

## 💡 提示

> 如果光影中 PBR 效果不明显，请检查：
> 1. 光影是否支持 labPBR 格式
> 2. 资源包是否在光影之上（设置中调整顺序）
> 3. `_n.png` 和 `_s.png` 文件名是否与基础贴图完全一致
