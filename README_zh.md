# manga-ocr-nar

[English](README.md) | [中文](README_zh.md)

日文漫画文字框 OCR。模型输入一张文字框裁图，一次前向输出整段文字（非自回归）。本仓库放推理代码和说明（不含权重），包含两个模型：

| 模型 | 参数量 | Read v1.3 EM | 权重 |
|---|---|---|---|
| **manga-ocr-nar-small** | 54.2M | **91.09%** | [Hugging Face](https://huggingface.co/muscgab/manga-ocr-nar-small) · [ModelScope](https://modelscope.cn/models/muscgab/manga-ocr-nar-small) |
| **manga-ocr-nar-small-distil** | 29.8M | 88.83% | [Hugging Face](https://huggingface.co/muscgab/manga-ocr-nar-small-distil) · [ModelScope](https://modelscope.cn/models/muscgab/manga-ocr-nar-small-distil) |

- **manga-ocr-nar-small**：更准，长文本和手写体尤其明显。支持 NVIDIA GPU（PyTorch，CUDA 图）、CPU（ONNX fp32）和 Mac（CoreML）。
- **manga-ocr-nar-small-distil**：由 manga-ocr-nar-small 蒸馏、以 int8 量化训练，面向 CPU：M1 Pro 上每框 21.0 ms，Xeon Gold 6148 上 37.3 ms（manga-ocr-nar-small 在同一台 Xeon 上用 fp32 为 75.4 ms）。在 NVIDIA GPU 上与 manga-ocr-nar-small 速度相当。支持 NVIDIA GPU（PyTorch，CUDA 图）和 CPU（ONNX int8），没有 CoreML 版。

两个模型共用同一份代码（`manga_ocr_nar_small`，1.1.0），用哪个模型取决于加载的目录。成绩均为 [JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read)（7,789 框）。

2026-10-16 由 `manga-ocr-nar-small` 改名而来（2026-10-14 前叫 `mangaocr-nar-small`）。GitHub 旧链接会自动跳转到这里。导入名 `manga_ocr_nar_small`、旧导入名 `mangaocr_nar_small` 以及命令 `manga-ocr-nar-small` / `mangaocr-nar-small` 仍可使用。

## 示例

裁图取自 [JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read) 中经人工确认标注的框，是 manga-ocr-nar-small 识别正确的例子中挑出来的，不代表平均水平（平均水平见下文准确率）。输出为 manga-ocr-nar-small 的原样输出。

| 印刷 | 输出 | 手写 | 输出 |
|---|---|---|---|
| <img src="samples/11654687_1.png" height="120"> | 明日からもうてめェにゃ構わねえよ | <img src="samples/10708764_2.png" height="120"> | だからアッチってどこ…(泣) |
| <img src="samples/12127834_0.png" height="120"> | まつ毛の先凍っててキラキラしてる | <img src="samples/10968484_0.png" height="120"> | そんなにたい焼き食べたかったのだろうか… |
| <img src="samples/10288963_7.png" height="120"> | 他のノートもあるって、見るかい? | <img src="samples/10335095_5.png" height="60"> | 料理にふりかけるだけ |
| <img src="samples/11226658_4.png" height="120"> | ニューワ?てのは知んないけど | <img src="samples/12198172_5.png" height="120"> | すごいこと言うな…。 |

图片来自独立画师公开发布的作品，随 Read 以 CC BY-NC-SA 4.0 提供，文件名即 Read 中的框编号。

## 准确率

[JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read)，RTX 2080 Ti 上 batch = 1 的输出，评分使用该评测集的 RIN v1 归一化。对照模型：Hayai v2.5 Nova p384（Nova 三个版本中综合分最高）和 mangaOCR（基线）。完整榜单见评测集页面。

全部 7,789 框：

| 指标 | manga-ocr-nar-small | manga-ocr-nar-small-distil | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|
| 参数量 | 54M | **30M** | 157M | 111M |
| 综合分 ↑ | **97.26** | 96.38 | 96.62 | 90.23 |
| CER % ↓ | **1.73** | 2.32 | 2.40 | 4.84 |
| EM % ↑ | **91.09** | 88.83 | 88.00 | 78.25 |

各部分 EM %（↑）：

| 范围 | 框数 | manga-ocr-nar-small | manga-ocr-nar-small-distil | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|---|
| v1.3 新增 | 4,660 | **91.35** | 88.69 | 88.22 | 78.20 |
| 印刷 | 5,877 | **94.44** | 92.90 | 91.70 | 88.04 |
| 非印刷 | 1,912 | **80.81** | 76.31 | 76.62 | 48.17 |
| hard | 784 | **70.92** | 63.78 | 63.39 | 44.52 |
| 超过 32 字 | 169 | **73.96** | 63.91 | 55.03 | 48.52 |

各部分 CER %（↓）：

| 范围 | 框数 | manga-ocr-nar-small | manga-ocr-nar-small-distil | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|---|
| v1.3 新增 | 4,660 | **1.64** | 2.28 | 2.29 | 4.80 |
| 印刷 | 5,877 | **1.24** | 1.65 | 1.84 | 2.21 |
| 非印刷 | 1,912 | **4.14** | 5.56 | 5.08 | 17.56 |
| hard | 784 | **7.14** | 9.28 | 8.92 | 16.43 |
| 超过 32 字 | 169 | **6.42** | 8.50 | 9.57 | 8.66 |

综合分是印刷与非印刷两部分 1 − NED 的等权平均，定义见评测集 README。manga-ocr-nar-small-distil 的 int8 ONNX 在同样的框上 EM 为 88.92（Xeon Gold 6148，u8u8）和 88.91（M1 Pro，u8s8）。

**开发中使用过的评测数据**：Read v1.2（3,142 框）是两个模型及其前代的开发集，用于模型选择、对照实验和错误分析。另一个开发集“Sol 手写”（2,248 框）与 v1.3 新增框重合 1,021 框（含新增非印刷 1,110 框中的 1,004 框）。候选池和评测集的图片均未用于训练。详见评测集 README 的“开发用途说明”。

## 速度

RTX 2080 Ti（11 GB），fp16，每个模型绑定 8 个 CPU 核，测法与 JMangaBench_Read v1.3 相同，单位 ms（吞吐除外）。

| 指标 | manga-ocr-nar-small | manga-ocr-nar-small-distil | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|
| 逐张延迟，平均 | 9.1 | **8.4** | 54.0 | 84.9 |
| 整页延迟 p50 | 35.5 | **35.0** | 252 | 242 |
| 整页延迟 p90 | **63.1** | 65.4 | 321 | 471 |
| 一次一页，间隔 0 s | 37 | **35** | 245 | 288 |
| 一次一页，间隔 10 s | 53 | **51** | 289 | 333 |
| 一次一页，间隔 30 s | **56** | 60 | 282 | 286 |
| 第一框，连续运行 | 7.5 | **7.0** | 51.5 | 72.6 |
| 第一框，空闲 20 s 后 | **24.7** | 40.3 | 81.7 | 93.3 |
| 最大吞吐（张/秒） | **299** | 287 | 175 | 42 |

- 逐张：batch = 1，含预处理。
- 整页：一页的框作为一个 batch，平均 8.7 框。
- 一次一页：逐页请求，页与页之间空闲 0 / 10 / 30 s。
- 最大吞吐对应的 batch：48 / 48 / 48 / 56。
- 空闲后变慢来自显卡降频，各模型都有。
- manga-ocr-nar-small-distil 在 GPU 上用 fp16 模拟 int8 运算，多出来的量化—反量化步骤抵掉了模型变小省下的大部分时间。用下面的 `compile=True` 把这些运算融合后，它明显快于 manga-ocr-nar-small。

### 可选：在 NVIDIA GPU 上使用 torch.compile

`MangaOcrNarSmall("cuda", compile=True)` 会在录制 CUDA 图之前用 `torch.compile` 编译网络，把其中的逐元素运算融合起来。需要 Triton（Linux），每次启动时每个 batch 大小编译一次（RTX 2080 Ti 上约 3 分钟，实测 165–171 s）。默认关闭。测法同上：

| 指标 | manga-ocr-nar-small | + compile | manga-ocr-nar-small-distil | + compile |
|---|---|---|---|---|
| 逐张延迟，均值 | 9.1 | 5.5 | 8.4 | **3.8** |
| 整页延迟 p50 | 35.5 | 23.2 | 35.0 | **19.2** |
| 整页延迟 p90 | 63.1 | 43.3 | 65.4 | **37.0** |
| 一页一页，间隔 0 s | 37 | 27 | 35 | **23** |
| 一页一页，间隔 10 s | 53 | 40 | 51 | **35** |
| 一页一页，间隔 30 s | 56 | **45** | 60 | 48 |
| 首框，连续运行中 | 7.5 | 5.0 | 7.0 | **4.2** |
| 首框，空闲 20 s 后 | 24.7 | **21.5** | 40.3 | 30.8 |
| 最大吞吐（张/s） | 299 | 415 | 287 | **509** |
| 启动（s） | 6 | 165–169 | 6 | 170–171 |
| EM %（batch = 1） | **91.09** | 91.08 | 88.83 | 88.97 |

- 不开 compile：即上表。开 compile：2026-10-16 用发布代码 1.1.0 实测，同一台机器、同一协议，单次运行。
- 开 compile 时最大吞吐对应 batch 16（不开时 48）。
- 编译会轻微改变 fp16 取整：7,789 框中有 7,787（manga-ocr-nar-small）和 7,579（distil） 框与不开 compile 时输出相同。整页 batch 输出的 EM：91.05 / 88.84。
- 开发中用过的 GPU 批量预处理（Triton kernel）不在发布包里；用上它时整页延迟 p50 还能降到 13.0 ms（distil）和 18.9 ms（manga-ocr-nar-small）。

### 弱 GPU

笔记本 GTX 1060 Max-Q（6 GB，Pascal，没有高速 fp16，全部按 fp32 运行；CPU i7-8750H，Windows 11），只测了 manga-ocr-nar-small。mangaOCR 未在这台机器上测。

| 指标 | manga-ocr-nar-small | Hayai v2.5 Nova p384 |
|---|---|---|
| 逐张延迟 p50（ms） | **25.2** | 115.4 |
| 一次一页，间隔 0 s（ms） | **160** | 676 |
| 一次一页，间隔 10 s（ms） | **169** | 759 |
| EM % | **91.09** | 87.80 |

- 逐张延迟与 EM：manga-ocr-nar-small 为全量 7,789 框（EM 与 2080 Ti 相同），Nova p384 为 500 框。
- 一次一页：同 8 页，取每页耗时的中位数。

一页约 0.16–0.19 s，在这类显卡上可以边翻页边识别。上表 manga-ocr-nar-small 用的是 CPU 预处理 + CUDA 图的路径；发布默认的 GPU 预处理路径在这张卡上每框慢约 6 ms、整页慢约 9%（195 页 p50 187 ms），每框 CPU 时间从约 150 ms 降到约 6 ms。

### CPU 与 Mac

端到端，含预处理：

| 模型 | 格式 | 设备 | 每框耗时 | EM % | 同 CUDA 输出 |
|---|---|---|---|---|---|
| manga-ocr-nar-small | ONNX，fp32 | Xeon Gold 6148 | 75.4 ms | 91.09 | 7,788 |
| manga-ocr-nar-small | CoreML，fp16 | M1 Pro GPU | 10.1 ms | 91.05 | 7,778 |
| manga-ocr-nar-small-distil | ONNX，int8（u8u8） | Xeon Gold 6148 | 37.3 ms | 88.92 | 7,599 |
| manga-ocr-nar-small-distil | ONNX，int8（u8s8） | M1 Pro CPU | 21.0 ms | 88.91 | 7,579 |

- ONNX：8 线程，逐张 p50，全部 7,789 框。
- CoreML：多函数包，macOS 15；16 框一批时的每框耗时（预处理 2.2 + 推理 7.9 ms）；一次一页 p50 102 ms。
- 同 CUDA 输出：7,789 框中与同一模型的 CUDA fp16 输出相同的框数。
- manga-ocr-nar-small-distil 的 int8 权重提供两种编码：u8s8 用于 ARM 和支持 VNNI 的 x86 CPU；u8u8 用于不支持 VNNI 的 x86 CPU，因为 onnxruntime 的 u8s8 kernel 在这类 CPU 上可能饱和（Xeon Gold 6148，前 300 框：u8s8 与 CUDA 输出相同 284 框，u8u8 为 296 框）。`int8="auto"`（默认）在不支持 VNNI 的 x86 CPU 以及无法检测的 x86 CPU 上选 u8u8，其余情况选 u8s8。支持 VNNI 的 x86 上两者的速度未测。

## 结构

- **编码器**：MonkeyOCRv2-S 视觉编码器（28.5M），由 [zenosai/MonkeyOCRv2-S](https://huggingface.co/zenosai/MonkeyOCRv2-S) 初始化，输出图块嵌入 $h_0$、各层 $h_1 \ldots h_{11}$ 和最终层 $h_{12}$。
- **输入**：裁图等比缩放后补齐到 324 个 14 × 14 的图块（PIL bicubic，空白处填充边缘颜色的中位数）。
- **gamma 融合**：基础记忆 $b = \mathrm{Bridge}(h_{12}) + \mathrm{Pos}(r, c)$。解码器第 $j$ 层读取自己的记忆

$$m_j = b + \gamma_j \odot W_o f_j,\qquad f_j = \sum_{l=0}^{11} \mathrm{softmax}(w_j)_l\,\mathrm{RMSNorm}_l(h_l)$$

  其中 $w_j$ 是该层对 12 个编码层的静态权重，$\gamma_j$ 是逐通道缩放向量，初始化为 0（训练开始时各层只读 $b$）。
- **解码器**：4 层非自回归解码器（宽 512，SwiGLU FFN 2048；位置槽自注意力 + 对记忆的交叉注意力，QK-Norm），65 个输出位置一次给出，遇到结束符截断。
- **词表**：6,817 个字符（`nar_vocabulary_6817.json`）。

**fp16 可用的权重**：发布的权重对部分层做过等价缩放，相关 RMSNorm 的 eps 一并调整，参数写在 `config.json` 的 `reparam` 中。fp32 下输出与原检查点一致（logits 差异约 4e-5），fp16 下中间激活不再溢出。权重以 fp32 存储，加载后可直接转成 fp16。

**manga-ocr-nar-small-distil** 结构相同，是从 manga-ocr-nar-small 裁出的较小学生模型：

- 编码器：保留 12 层中的 6 层（隔一层取一层，含最后一层），深度融合保留对应的层。
- 解码器：4 层，宽 384（6 个 64 维的头），SwiGLU FFN 1536。保留哪些通道、头和 FFN 单元，按它们在训练数据上的重要性挑选，再把所有张量按此切片。
- 训练中的 int8 量化：编码器各块、记忆的 bridge 与投影、解码器和输出头里每个线性层的输入按张量量化为 uint8（scale 和零点可学习），权重按输出通道量化为 int8。图块嵌入、注意力乘积、归一化和残差相加保持浮点。
- 发布的权重存的是 int8 反量化后的值；`config.json` 的 `act_quant` 存激活的 scale 和零点，PyTorch 代码按此做量化—反量化，复现 int8 模型。只用权重、不做这一步，得到的不是可用的浮点模型（Read v1.3 上 EM 约 81%）。
- 同样做了上面的 fp16 等价缩放（`reparam`），在量化后的模型上计算。

## 训练

**manga-ocr-nar-small**

- 从头训练（编码器由 MonkeyOCRv2-S 初始化），279,499 步，batch 128，共见过 35,775,872 张图（8 轮）。4 张 RTX 2080 Ti，解码器 fp32、其余 fp16 混合精度。
- 训练集 4,471,985 张：

| 来源 | 张数 | 占比 |
|---|---|---|
| 合成印刷体 | 1,795,869 | 40.2% |
| 合成手写体 | 1,670,000 | 37.3% |
| AnimeText-OCR | 1,006,116 | 22.5% |

- AnimeText-OCR：[真实漫画裁图](https://huggingface.co/datasets/JustANormalTinkerer/animetext-ocr)，取序列置信度 0.90–0.98 的部分。
- 合成数据的几项分布参数参照了评测集候选池的汇总统计，统计值公开在评测集仓库的 `docs/pool_stats/`。
- 合成手写数据的生成方法（素材、随机因素、排版规则、检查、样图）：[docs/synthetic_handwriting_zh.md](docs/synthetic_handwriting_zh.md)。

**manga-ocr-nar-small-distil**

- 教师：manga-ocr-nar-small。训练集相同，去掉了标签为 AnimeText-OCR 中某句固定占位句的样本。
- 损失：manga-ocr-nar-small 的训练损失（标签交叉熵与位置槽占用项）+ 对教师输出分布的 KL 散度 + 学生与教师解码器记忆之间的相对 MSE。
- 第一阶段：31,250 步，batch 128（400 万张图），1 张 RTX 2080 Ti；前 4,687 步为浮点，之后开启 int8 量化。
- 第二阶段：69,874 步，batch 256（1,790 万张图），4 张 RTX 2080 Ti，全程 int8 量化。

## 文件

Hugging Face 与 ModelScope 上的文件：

| 文件 | manga-ocr-nar-small | manga-ocr-nar-small-distil |
|---|---|---|
| `model.safetensors` | 权重，fp32，217 MB | 权重（int8 反量化后的值），fp32，119 MB |
| `config.json` | 结构参数、fp16 等价缩放 | 结构参数、fp16 等价缩放、激活量化参数、ONNX 文件名 |
| `nar_vocabulary_6817.json` | 词表 | 词表 |
| `onnx/` | CPU 用 ONNX fp32，213 MB | CPU 用 ONNX int8，u8s8 与 u8u8 各 31 MB |
| `coreml/` | Mac 用 CoreML，107 MB | — |
| `manga_ocr_nar_small/` | 推理代码（两边相同） | 推理代码（两边相同） |
| `samples/` | 示例裁图 | — |
| `SHA256SUMS` | 校验和 | 校验和 |

- ONNX 为 batch = 1；CoreML 为多函数包（batch 1/2/4/8/16），需要 macOS 15 及以上。
- 许可证与来源见 `LICENSE`、`LICENSE_MODEL`、`NOTICE.md`。

## 使用

从 Hugging Face 或 ModelScope 下载模型仓库（GitHub 上没有权重）：

```bash
git lfs install
git clone https://huggingface.co/muscgab/manga-ocr-nar-small          # 或 muscgab/manga-ocr-nar-small-distil
# 或：modelscope download --model muscgab/manga-ocr-nar-small --local_dir manga-ocr-nar-small
cd manga-ocr-nar-small
```

在仓库目录内安装，按平台选一个附加项：

```bash
pip install -e ".[cuda]"   # NVIDIA GPU：需要 torch 与 safetensors
pip install -e ".[cpu]"    # CPU：onnxruntime
pip install -e ".[mac]"    # Mac（macOS 15+，仅 manga-ocr-nar-small）：pyobjc-framework-CoreML，不需要 torch
```

```python
from manga_ocr_nar_small import MangaOcrNarSmall
ocr = MangaOcrNarSmall()                   # backend="auto"：有 CUDA 用 CUDA，macOS 15+ 用 CoreML（模型带 CoreML 时），否则 ONNX
ocr("crop.png")                            # 一张裁图 -> str
ocr(["crop1.png", "crop2.png"])            # 同一页的裁图一起传入 -> list[str]，作为一个 batch 处理
```

默认使用代码所在的模型仓库；要用别的模型，传 `model_dir=`（或设置 `MANGA_OCR_NAR_SMALL_DIR`），例如 `MangaOcrNarSmall(model_dir="manga-ocr-nar-small-distil")`。也接受 PIL 图像和 uint8 RGB 数组。命令行：

```bash
manga-ocr-nar-small crop1.png crop2.png     # 每行输出“路径<TAB>文字”；可加 --model-dir、--backend、--int8
```

**显卡降频（仅 CUDA）**：显卡空闲几秒后会自动降频，下一次请求会变慢。RTX 2080 Ti 上（manga-ocr-nar-small），空闲 20 s 后第一框由 7.5 ms 变为 24.7 ms；一次一页、页间隔 10 s 时每页 53 ms，连续处理时为 37 ms。想要一直保持最高速度，可以把显卡频率锁定在最高档（需要管理员权限，用完后用 `nvidia-smi -rgc` 恢复）：

```text
nvidia-smi -lgc <最高频率>,<最高频率>
```

也可以在 NVIDIA 控制面板中把电源管理模式设为“最高性能优先”。锁频会增加空闲时的功耗和发热。降频的影响因显卡而异：笔记本 GTX 1060 Max-Q 空闲时只降到 1,265–1,392 MHz，同 8 页一次一页、页间隔 30 s 时总耗时比连续处理只多约 4.5%。

输入是文字框裁图，本包不含文字检测。首次在 Mac 上运行时会把 CoreML 包编译到 `coreml/` 目录下，之后直接加载。

## 局限

- 只针对日文漫画中的台词、旁白、旁注；拟声词不是目标。
- 输出最长 65 个位置；更长的文字框需要先切分。
- 非印刷体（手写、艺术字）错误明显多于印刷体（manga-ocr-nar-small：CER 4.14% 对 1.24%）。
- manga-ocr-nar-small-distil 在长文本框（超过 32 字：EM 63.91% 对 73.96%）和非印刷体（76.31% 对 80.81%）上较弱。
- 速度只在上述设备上测过。

## 致谢

- [MonkeyOCRv2](https://arxiv.org/abs/2607.11562)：编码器的结构与初始权重（MonkeyOCRv2-S）。
- [CPPD](https://arxiv.org/abs/2307.12270)：用一组有序查询并行解码的思路。
- [AnimeText](https://arxiv.org/abs/2510.07951) 与 [AnimeText-OCR](https://huggingface.co/datasets/JustANormalTinkerer/animetext-ocr)：真实训练裁图；合成手写体用到的真实假名字形也切自 AnimeText 图片。
- [Real-ESRGAN](https://arxiv.org/abs/2107.10833)：合成手写体的假名字形用 RealESRGAN_x4plus_anime_6B 放大 4 倍。
- [Hayai](https://huggingface.co/JustANormalTinkerer/hayai-ocr-v2.5-nova) 与 [mangaOCR](https://huggingface.co/kha-white/manga-ocr-base)：开发和评测中的对照模型。

## 许可证

- 代码：Apache License 2.0（`LICENSE`）。
- 模型权重（两个模型）：CC BY-NC-SA 4.0（`LICENSE_MODEL`）。训练数据 AnimeText-OCR 为 CC BY-NC-SA 4.0。
- 编码器由 MonkeyOCRv2-S 初始化，上游代码与权重为 Apache License 2.0。来源说明见 `NOTICE.md`。
