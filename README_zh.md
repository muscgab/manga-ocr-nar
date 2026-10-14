# MangaOCR-Nar-Small

[English](README.md) | [中文](README_zh.md)

[GitHub](https://github.com/muscgab/manga-ocr-nar-small)（只有代码和说明，不含权重） · [Hugging Face](https://huggingface.co/muscgab/manga-ocr-nar-small) · [ModelScope](https://modelscope.cn/models/muscgab/manga-ocr-nar-small)

2026-10-14 由 `mangaocr-nar-small` 改名而来。GitHub 和 Hugging Face 的旧链接会自动跳转到这里；ModelScope 旧仓库保留不删。旧的导入名 `mangaocr_nar_small` 和命令 `mangaocr-nar-small` 仍可使用。

日文漫画文字框 OCR 模型。输入一张文字框裁图，一次前向输出整段文字（非自回归），共 54.2M 参数。

- 在 [JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read)（7,789 框）上：综合分 97.26，CER 1.73%，EM 91.09%。
- RTX 2080 Ti、fp16：逐张 9.1 ms；一页（平均 8.7 框）作为一个 batch，p50 35.5 ms。
- 提供三种格式：NVIDIA GPU（PyTorch，CUDA 图）、CPU（ONNX）、Mac（CoreML，macOS 15 及以上）。

## 示例

裁图取自 [JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read) 中经人工确认标注的框，是挑选出的识别正确的例子，不代表平均水平（平均水平见下文准确率）。输出为模型原样输出。

| 印刷 | 输出 | 手写 | 输出 |
|---|---|---|---|
| <img src="samples/11654687_1.png" height="120"> | 明日からもうてめェにゃ構わねえよ | <img src="samples/10708764_2.png" height="120"> | だからアッチってどこ…(泣) |
| <img src="samples/12127834_0.png" height="120"> | まつ毛の先凍っててキラキラしてる | <img src="samples/10968484_0.png" height="120"> | そんなにたい焼き食べたかったのだろうか… |
| <img src="samples/10288963_7.png" height="120"> | 他のノートもあるって、見るかい? | <img src="samples/10335095_5.png" height="60"> | 料理にふりかけるだけ |
| <img src="samples/11226658_4.png" height="120"> | ニューワ?てのは知んないけど | <img src="samples/12198172_5.png" height="120"> | すごいこと言うな…。 |

图片来自独立画师公开发布的作品，随 Read 以 CC BY-NC-SA 4.0 提供，文件名即 Read 中的框编号。

## 准确率

[JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read)，batch = 1 的输出，评分使用该评测集的 RIN v1 归一化。对照模型：Hayai v2.5 Nova p384（Nova 三个版本中综合分最高）和 mangaOCR（基线）。完整榜单见评测集页面。

全部 7,789 框：

| 指标 | MangaOCR-Nar-Small | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|
| 参数量 | **54M** | 157M | 111M |
| 综合分 ↑ | **97.26** | 96.62 | 90.23 |
| CER % ↓ | **1.73** | 2.40 | 4.84 |
| EM % ↑ | **91.09** | 88.00 | 78.25 |

各部分 EM %（↑）：

| 范围 | 框数 | MangaOCR-Nar-Small | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|
| v1.3 新增 | 4,660 | **91.35** | 88.22 | 78.20 |
| 印刷 | 5,877 | **94.44** | 91.70 | 88.04 |
| 非印刷 | 1,912 | **80.81** | 76.62 | 48.17 |
| hard | 784 | **70.92** | 63.39 | 44.52 |

各部分 CER %（↓）：

| 范围 | 框数 | MangaOCR-Nar-Small | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|
| v1.3 新增 | 4,660 | **1.64** | 2.29 | 4.80 |
| 印刷 | 5,877 | **1.24** | 1.84 | 2.21 |
| 非印刷 | 1,912 | **4.14** | 5.08 | 17.56 |
| hard | 784 | **7.14** | 8.92 | 16.43 |

综合分是印刷与非印刷两部分 1 − NED 的等权平均，定义见评测集 README。

**开发中使用过的评测数据**：Read v1.2（3,142 框）是 MangaOCR-Nar-Small 及其前代的开发集，用于模型选择、对照实验和错误分析。另一个开发集“Sol 手写”（2,248 框）与 v1.3 新增框重合 1,021 框（含新增非印刷 1,110 框中的 1,004 框）。候选池和评测集的图片均未用于训练。详见评测集 README 的“开发用途说明”。

## 速度

RTX 2080 Ti（11 GB），fp16，每个模型绑定 8 个 CPU 核，测法与 JMangaBench_Read v1.3 相同，单位 ms（吞吐除外）。

| 指标 | MangaOCR-Nar-Small | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|
| 逐张延迟，平均 | **9.1** | 54.0 | 84.9 |
| 整页延迟 p50 | **35.5** | 252 | 242 |
| 整页延迟 p90 | **63.1** | 321 | 471 |
| 一次一页，间隔 0 s | **37** | 245 | 288 |
| 一次一页，间隔 10 s | **53** | 289 | 333 |
| 一次一页，间隔 30 s | **56** | 282 | 286 |
| 第一框，连续运行 | **7.5** | 51.5 | 72.6 |
| 第一框，空闲 20 s 后 | **24.7** | 81.7 | 93.3 |
| 最大吞吐（张/秒） | **299** | 175 | 42 |

- 逐张：batch = 1，含预处理。
- 整页：一页的框作为一个 batch，平均 8.7 框。
- 一次一页：逐页请求，页与页之间空闲 0 / 10 / 30 s。
- 最大吞吐对应的 batch：48 / 48 / 56。
- 空闲后变慢来自显卡降频，各模型都有。

### 弱 GPU

笔记本 GTX 1060 Max-Q（6 GB，Pascal，没有高速 fp16，全部按 fp32 运行；CPU i7-8750H，Windows 11）。mangaOCR 未在这台机器上测。

| 指标 | MangaOCR-Nar-Small | Hayai v2.5 Nova p384 |
|---|---|---|
| 逐张延迟 p50（ms） | **25.2** | 115.4 |
| 一次一页，间隔 0 s（ms） | **160** | 676 |
| 一次一页，间隔 10 s（ms） | **169** | 759 |
| EM % | **91.09** | 87.80 |

- 逐张延迟与 EM：MangaOCR-Nar-Small 为全量 7,789 框（EM 与 2080 Ti 相同），Nova p384 为 500 框。
- 一次一页：同 8 页，取每页耗时的中位数。

一页约 0.16–0.19 s，在这类显卡上可以边翻页边识别。上表 MangaOCR-Nar-Small 用的是 CPU 预处理 + CUDA 图的路径；发布默认的 GPU 预处理路径在这张卡上每框慢约 6 ms、整页慢约 9%（195 页 p50 187 ms），每框 CPU 时间从约 150 ms 降到约 6 ms。

其他平台（端到端，含预处理）：

| 格式 | 设备 | 每框耗时 | EM % | 同 CUDA 输出 |
|---|---|---|---|---|
| CUDA 图，fp16 | RTX 2080 Ti | 见上表 | 91.09 | 7,789 |
| ONNX，fp32 | Xeon Gold 6148 | 58.2 ms | 91.09 | 7,788 |
| CoreML，fp16 | M1 Pro GPU | 10.1 ms | 91.05 | 7,778 |

- ONNX：8 线程，逐张 p50。
- CoreML：多函数包，macOS 15；16 框一批时的每框耗时（预处理 2.2 + 推理 7.9 ms）；一次一页 p50 102 ms。
- 同 CUDA 输出：7,789 框中与 CUDA fp16 输出相同的框数。

## 结构

- **编码器**：MonkeyOCRv2-S 视觉编码器（28.5M），由 [zenosai/MonkeyOCRv2-S](https://huggingface.co/zenosai/MonkeyOCRv2-S) 初始化，输出图块嵌入 $h_0$、各层 $h_1 \ldots h_{11}$ 和最终层 $h_{12}$。
- **输入**：裁图等比缩放后补齐到 324 个 14 × 14 的图块（PIL bicubic，空白处填充边缘颜色的中位数）。
- **gamma 融合**：基础记忆 $b = \mathrm{Bridge}(h_{12}) + \mathrm{Pos}(r, c)$。解码器第 $j$ 层读取自己的记忆

$$m_j = b + \gamma_j \odot W_o f_j,\qquad f_j = \sum_{l=0}^{11} \mathrm{softmax}(w_j)_l\,\mathrm{RMSNorm}_l(h_l)$$

  其中 $w_j$ 是该层对 12 个编码层的静态权重，$\gamma_j$ 是逐通道缩放向量，初始化为 0（训练开始时各层只读 $b$）。
- **解码器**：4 层非自回归解码器（宽 512，SwiGLU FFN 2048；位置槽自注意力 + 对记忆的交叉注意力，QK-Norm），65 个输出位置一次给出，遇到结束符截断。
- **词表**：6,817 个字符（`nar_vocabulary_6817.json`）。

**fp16 可用的权重**：发布的权重对部分层做过等价缩放，相关 RMSNorm 的 eps 一并调整，参数写在 `config.json` 的 `reparam` 中。fp32 下输出与原检查点一致（logits 差异约 4e-5），fp16 下中间激活不再溢出。权重以 fp32 存储，加载后可直接转成 fp16。

## 训练

- 从头训练（编码器由 MonkeyOCRv2-S 初始化），279,499 步，batch 128，共见过 35,775,872 张图（8 轮）。4 张 RTX 2080 Ti，解码器 fp32、其余 fp16 混合精度。
- 训练集 4,471,985 张：

| 来源 | 张数 | 占比 |
|---|---|---|
| 合成印刷体 | 1,795,869 | 40.2% |
| 合成手写体 | 1,670,000 | 37.3% |
| AnimeText-OCR | 1,006,116 | 22.5% |

- AnimeText-OCR：[真实漫画裁图](https://huggingface.co/datasets/JustANormalTinkerer/animetext-ocr)，取序列置信度 0.90–0.98 的部分。

- 合成数据的几项分布参数参照了评测集候选池的汇总统计，统计值公开在评测集仓库的 `docs/pool_stats/`。

## 文件

| 文件 | 内容 | 大小 |
|---|---|---|
| `model.safetensors` | 权重，fp32 | 217 MB |
| `config.json` | 结构参数 | 2 KB |
| `nar_vocabulary_6817.json` | 词表 | 48 KB |
| `onnx/` | CPU 用 ONNX | 213 MB |
| `coreml/` | Mac 用 CoreML | 107 MB |
| `manga_ocr_nar_small/` | 推理代码 | — |
| `mangaocr_nar_small/` | 旧导入名（上一行的别名） | — |
| `samples/` | 示例裁图 | 162 KB |
| `SHA256SUMS` | 校验和 | — |

- 权重已做 fp16 重参数化，参数在 `config.json` 的 `reparam` 中（见“结构”）。
- ONNX 为 batch = 1；CoreML 为多函数包（batch 1/2/4/8/16），需要 macOS 15 及以上。
- 推理代码含 CUDA、ONNX、CoreML 三个后端。
- 许可证与来源见 `LICENSE`、`LICENSE_MODEL`、`NOTICE.md`。

## 使用

从 Hugging Face 或 ModelScope 下载完整仓库（GitHub 上没有权重）：

```bash
git lfs install
git clone https://huggingface.co/muscgab/manga-ocr-nar-small
# 或：modelscope download --model muscgab/manga-ocr-nar-small --local_dir manga-ocr-nar-small
cd manga-ocr-nar-small
```

在仓库目录内安装，按平台选一个附加项：

```bash
pip install -e ".[cuda]"   # NVIDIA GPU：需要 torch 与 safetensors
pip install -e ".[cpu]"    # CPU：onnxruntime
pip install -e ".[mac]"    # Mac（macOS 15+）：pyobjc-framework-CoreML，不需要 torch
```

```python
from manga_ocr_nar_small import MangaOcrNarSmall
ocr = MangaOcrNarSmall()                   # backend="auto"：有 CUDA 用 CUDA，macOS 15+ 用 CoreML，否则 ONNX
ocr("crop.png")                            # 一张裁图 -> str
ocr(["crop1.png", "crop2.png"])            # 同一页的裁图一起传入 -> list[str]，作为一个 batch 处理
```

也接受 PIL 图像和 uint8 RGB 数组。命令行：

```bash
manga-ocr-nar-small crop1.png crop2.png     # 每行输出“路径<TAB>文字”
```

**显卡降频（仅 CUDA）**：显卡空闲几秒后会自动降频，下一次请求会变慢。RTX 2080 Ti 上，空闲 20 s 后第一框由 7.5 ms 变为 24.7 ms；一次一页、页间隔 10 s 时每页 53 ms，连续处理时为 37 ms。想要一直保持最高速度，可以把显卡频率锁定在最高档（需要管理员权限，用完后用 `nvidia-smi -rgc` 恢复）：

```text
nvidia-smi -lgc <最高频率>,<最高频率>
```

也可以在 NVIDIA 控制面板中把电源管理模式设为“最高性能优先”。锁频会增加空闲时的功耗和发热。降频的影响因显卡而异：笔记本 GTX 1060 Max-Q 空闲时只降到 1,265–1,392 MHz，同 8 页一次一页、页间隔 30 s 时总耗时比连续处理只多约 4.5%。

输入是文字框裁图，本包不含文字检测。首次在 Mac 上运行时会把 CoreML 包编译到 `coreml/` 目录下，之后直接加载。

## 局限

- 只针对日文漫画中的台词、旁白、旁注；拟声词不是目标。
- 输出最长 65 个位置；更长的文字框需要先切分。
- 非印刷体（手写、艺术字）错误明显多于印刷体（CER 4.14% 对 1.24%）。
- 速度只在上述设备上测过。

## 致谢

- [MonkeyOCRv2](https://arxiv.org/abs/2607.11562)：编码器的结构与初始权重（MonkeyOCRv2-S）。
- [CPPD](https://arxiv.org/abs/2307.12270)：用一组有序查询并行解码的思路。
- [AnimeText](https://arxiv.org/abs/2510.07951) 与 [AnimeText-OCR](https://huggingface.co/datasets/JustANormalTinkerer/animetext-ocr)：真实训练裁图；合成手写体用到的真实假名字形也切自 AnimeText 图片。
- [Real-ESRGAN](https://arxiv.org/abs/2107.10833)：合成手写体的假名字形用 RealESRGAN_x4plus_anime_6B 放大 4 倍。
- [Hayai](https://huggingface.co/JustANormalTinkerer/hayai-ocr-v2.5-nova) 与 [mangaOCR](https://huggingface.co/kha-white/manga-ocr-base)：开发和评测中的对照模型。

## 许可证

- 代码：Apache License 2.0（`LICENSE`）。
- 模型权重：CC BY-NC-SA 4.0（`LICENSE_MODEL`）。训练数据 AnimeText-OCR 为 CC BY-NC-SA 4.0。
- 编码器由 MonkeyOCRv2-S 初始化，上游代码与权重为 Apache License 2.0。来源说明见 `NOTICE.md`。
