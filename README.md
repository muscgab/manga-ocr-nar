# manga-ocr-nar

[English](README.md) | [中文](README_zh.md)

OCR for Japanese manga text boxes. A model takes one cropped text box and outputs the whole text in a single forward pass (non-autoregressive). This repository holds the inference code and docs (no weights) for two models:

| Model | Params | Read v1.3 EM | Weights |
|---|---|---|---|
| **manga-ocr-nar-small** | 54.2M | **91.09%** | [Hugging Face](https://huggingface.co/muscgab/manga-ocr-nar-small) · [ModelScope](https://modelscope.cn/models/muscgab/manga-ocr-nar-small) |
| **manga-ocr-nar-small-distil** | 29.8M | 88.83% | [Hugging Face](https://huggingface.co/muscgab/manga-ocr-nar-small-distil) · [ModelScope](https://modelscope.cn/models/muscgab/manga-ocr-nar-small-distil) |

- **manga-ocr-nar-small**: the more accurate model, especially on long and handwritten text. NVIDIA GPU (PyTorch, CUDA graphs), CPU (ONNX fp32) and Mac (CoreML).
- **manga-ocr-nar-small-distil**: distilled from manga-ocr-nar-small and trained with int8 quantization, for CPUs: 21.0 ms per crop on an M1 Pro and 37.3 ms on a Xeon Gold 6148 (manga-ocr-nar-small: 75.4 ms in fp32 on the same Xeon). On an NVIDIA GPU it is about as fast as manga-ocr-nar-small. NVIDIA GPU (PyTorch, CUDA graphs) and CPU (ONNX int8); no CoreML.

Both use the same code (`manga_ocr_nar_small`, 1.1.0); the model is chosen by the directory you load. Scores: [JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read), 7,789 boxes.

Renamed from `manga-ocr-nar-small` on 2026-10-16 (and from `mangaocr-nar-small` on 2026-10-14). Old GitHub links redirect here. The import name `manga_ocr_nar_small`, the old import name `mangaocr_nar_small` and the commands `manga-ocr-nar-small` / `mangaocr-nar-small` keep working.

## Examples

The crops are boxes with human-confirmed labels in [JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read). They were picked from boxes manga-ocr-nar-small reads correctly and are not representative (see Accuracy for average performance). Outputs are shown exactly as manga-ocr-nar-small produced them.

| Printed | Output | Handwritten | Output |
|---|---|---|---|
| <img src="samples/11654687_1.png" height="120"> | 明日からもうてめェにゃ構わねえよ | <img src="samples/10708764_2.png" height="120"> | だからアッチってどこ…(泣) |
| <img src="samples/12127834_0.png" height="120"> | まつ毛の先凍っててキラキラしてる | <img src="samples/10968484_0.png" height="120"> | そんなにたい焼き食べたかったのだろうか… |
| <img src="samples/10288963_7.png" height="120"> | 他のノートもあるって、見るかい? | <img src="samples/10335095_5.png" height="60"> | 料理にふりかけるだけ |
| <img src="samples/11226658_4.png" height="120"> | ニューワ?てのは知んないけど | <img src="samples/12198172_5.png" height="120"> | すごいこと言うな…。 |

The images come from works published online by independent artists and are provided with Read under CC BY-NC-SA 4.0. File names are the box IDs in Read.

## Accuracy

[JMangaBench_Read v1.3](https://github.com/muscgab/JMangaBench_Read), batch = 1 outputs on an RTX 2080 Ti, scored with the benchmark's RIN v1 normalization. Reference models: Hayai v2.5 Nova p384 (highest composite of the three Nova variants) and mangaOCR (baseline). See the benchmark page for the full leaderboard.

All 7,789 boxes:

| Metric | manga-ocr-nar-small | manga-ocr-nar-small-distil | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|
| Parameters | 54M | **30M** | 157M | 111M |
| Composite ↑ | **97.26** | 96.38 | 96.62 | 90.23 |
| CER % ↓ | **1.73** | 2.32 | 2.40 | 4.84 |
| EM % ↑ | **91.09** | 88.83 | 88.00 | 78.25 |

EM % by subset (↑):

| Subset | Boxes | manga-ocr-nar-small | manga-ocr-nar-small-distil | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|---|
| New in v1.3 | 4,660 | **91.35** | 88.69 | 88.22 | 78.20 |
| Printed | 5,877 | **94.44** | 92.90 | 91.70 | 88.04 |
| Non-printed | 1,912 | **80.81** | 76.31 | 76.62 | 48.17 |
| hard | 784 | **70.92** | 63.78 | 63.39 | 44.52 |
| More than 32 characters | 169 | **73.96** | 63.91 | 55.03 | 48.52 |

CER % by subset (↓):

| Subset | Boxes | manga-ocr-nar-small | manga-ocr-nar-small-distil | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|---|
| New in v1.3 | 4,660 | **1.64** | 2.28 | 2.29 | 4.80 |
| Printed | 5,877 | **1.24** | 1.65 | 1.84 | 2.21 |
| Non-printed | 1,912 | **4.14** | 5.56 | 5.08 | 17.56 |
| hard | 784 | **7.14** | 9.28 | 8.92 | 16.43 |
| More than 32 characters | 169 | **6.42** | 8.50 | 9.57 | 8.66 |

The composite is the equal-weight mean of 1 − NED over the printed and non-printed parts; see the benchmark README for the definition. The int8 ONNX of manga-ocr-nar-small-distil scores EM 88.92 (Xeon Gold 6148, u8u8) and 88.91 (M1 Pro, u8s8) on the same boxes.

**Evaluation data used during development**: Read v1.2 (3,142 boxes) was the development set of both models and their predecessors, used for model selection, controlled experiments and error analysis. Another development set, "Sol handwriting" (2,248 boxes), shares 1,021 boxes with the boxes new in v1.3 (including 1,004 of the 1,110 new non-printed boxes). No image from the candidate pool or the benchmark was used for training. See "Development use" in the benchmark README.

## Speed

RTX 2080 Ti (11 GB), fp16, 8 CPU cores pinned per model, same method as JMangaBench_Read v1.3. Unit: ms (except throughput).

| Metric | manga-ocr-nar-small | manga-ocr-nar-small-distil | Hayai v2.5 Nova p384 | mangaOCR |
|---|---|---|---|---|
| Per-crop latency, mean | 9.1 | **8.4** | 54.0 | 84.9 |
| Page latency p50 | 35.5 | **35.0** | 252 | 242 |
| Page latency p90 | **63.1** | 65.4 | 321 | 471 |
| Page by page, 0 s gap | 37 | **35** | 245 | 288 |
| Page by page, 10 s gap | 53 | **51** | 289 | 333 |
| Page by page, 30 s gap | **56** | 60 | 282 | 286 |
| First crop, running | 7.5 | **7.0** | 51.5 | 72.6 |
| First crop, after 20 s idle | **24.7** | 40.3 | 81.7 | 93.3 |
| Max throughput (crops/s) | **299** | 287 | 175 | 42 |

- Per crop: batch = 1, preprocessing included.
- Page: the boxes of one page as one batch, 8.7 boxes on average.
- Page by page: one request per page, idle for 0 / 10 / 30 s between pages.
- Batch size at max throughput: 48 / 48 / 48 / 56.
- The slowdown after idling comes from GPU down-clocking and affects every model.
- manga-ocr-nar-small-distil runs int8 arithmetic simulated in fp16 on the GPU; the extra quantize-dequantize steps use up most of the time saved by its smaller size. With `compile=True` (below) they are fused and it becomes clearly faster than manga-ocr-nar-small.

### Optional: torch.compile on NVIDIA GPUs

`MangaOcrNarSmall("cuda", compile=True)` compiles the network with `torch.compile` before the CUDA graphs are captured, which fuses its elementwise operations. It needs Triton (Linux) and compiles once per batch size at every start-up (about 3 minutes on an RTX 2080 Ti, 165–171 s measured). Off by default. Same protocol as above:

| Metric | manga-ocr-nar-small | + compile | manga-ocr-nar-small-distil | + compile |
|---|---|---|---|---|
| Per-crop latency, mean | 9.1 | 5.5 | 8.4 | **3.8** |
| Page latency p50 | 35.5 | 23.2 | 35.0 | **19.2** |
| Page latency p90 | 63.1 | 43.3 | 65.4 | **37.0** |
| Page by page, 0 s gap | 37 | 27 | 35 | **23** |
| Page by page, 10 s gap | 53 | 40 | 51 | **35** |
| Page by page, 30 s gap | 56 | **45** | 60 | 48 |
| First crop, running | 7.5 | 5.0 | 7.0 | **4.2** |
| First crop, after 20 s idle | 24.7 | **21.5** | 40.3 | 30.8 |
| Max throughput (crops/s) | 299 | 415 | 287 | **509** |
| Start-up (s) | 6 | 165–169 | 6 | 170–171 |
| EM % (batch = 1) | **91.09** | 91.08 | 88.83 | 88.97 |

- Without compile: the numbers above. With compile: measured on 2026-10-16 with the release code 1.1.0, same machine and protocol, single run.
- Batch size at max throughput with compile: 16 (without: 48).
- Compilation changes fp16 rounding slightly: outputs equal those without compile on 7,787 (manga-ocr-nar-small) and 7,579 (distil) of 7,789 boxes. EM with page batches: 91.05 / 88.84.
- The batched GPU preprocessing used in development (a Triton kernel) is not part of the release; with it, page latency p50 drops further to 13.0 ms (distil) and 18.9 ms (manga-ocr-nar-small).

### Weak GPU

Laptop GTX 1060 Max-Q (6 GB, Pascal, no fast fp16, everything in fp32; CPU i7-8750H, Windows 11), manga-ocr-nar-small only. mangaOCR was not measured on this machine.

| Metric | manga-ocr-nar-small | Hayai v2.5 Nova p384 |
|---|---|---|
| Per-crop latency p50 (ms) | **25.2** | 115.4 |
| Page by page, 0 s gap (ms) | **160** | 676 |
| Page by page, 10 s gap (ms) | **169** | 759 |
| EM % | **91.09** | 87.80 |

- Per-crop latency and EM: all 7,789 boxes for manga-ocr-nar-small (EM same as on the 2080 Ti), 500 boxes for Nova p384.
- Page by page: the same 8 pages, median time per page.

About 0.16–0.19 s per page, so pages can be read while flipping through them on this class of GPU. The manga-ocr-nar-small rows above use CPU preprocessing + CUDA graphs; the default GPU-preprocessing path of the release is about 6 ms slower per crop and about 9% slower per page on this card (195 pages, p50 187 ms), while CPU time per crop drops from about 150 ms to about 6 ms.

### CPU and Mac

End to end, preprocessing included:

| Model | Format | Device | Time per crop | EM % | Same as CUDA |
|---|---|---|---|---|---|
| manga-ocr-nar-small | ONNX, fp32 | Xeon Gold 6148 | 75.4 ms | 91.09 | 7,788 |
| manga-ocr-nar-small | CoreML, fp16 | M1 Pro GPU | 10.1 ms | 91.05 | 7,778 |
| manga-ocr-nar-small-distil | ONNX, int8 (u8u8) | Xeon Gold 6148 | 37.3 ms | 88.92 | 7,599 |
| manga-ocr-nar-small-distil | ONNX, int8 (u8s8) | M1 Pro CPU | 21.0 ms | 88.91 | 7,579 |

- ONNX: 8 threads, per-crop p50, all 7,789 boxes.
- CoreML: multifunction package, macOS 15; time per crop in batches of 16 (preprocessing 2.2 + inference 7.9 ms); page by page p50 102 ms.
- Same as CUDA: boxes (of 7,789) whose output equals the CUDA fp16 output of the same model.
- manga-ocr-nar-small-distil ships two encodings of the same int8 weights: u8s8 for ARM and for x86 CPUs with VNNI, u8u8 for x86 CPUs without VNNI, where onnxruntime's u8s8 kernels can saturate (Xeon Gold 6148, first 300 boxes: u8s8 output equals the CUDA output on 284 boxes, u8u8 on 296). `int8="auto"` (default) picks u8u8 on x86 CPUs without VNNI flags and on x86 CPUs it cannot inspect, u8s8 otherwise. Speed of u8s8 vs u8u8 on x86 with VNNI was not measured.

## Architecture

- **Encoder**: MonkeyOCRv2-S vision encoder (28.5M), initialized from [zenosai/MonkeyOCRv2-S](https://huggingface.co/zenosai/MonkeyOCRv2-S). It outputs the patch embeddings $h_0$, the layers $h_1 \ldots h_{11}$ and the final layer $h_{12}$.
- **Input**: the crop is resized with its aspect ratio kept and padded to 324 patches of 14 × 14 (PIL bicubic; empty area filled with the median colour of the border).
- **Gamma fusion**: base memory $b = \mathrm{Bridge}(h_{12}) + \mathrm{Pos}(r, c)$. Decoder layer $j$ reads its own memory

$$m_j = b + \gamma_j \odot W_o f_j,\qquad f_j = \sum_{l=0}^{11} \mathrm{softmax}(w_j)_l\,\mathrm{RMSNorm}_l(h_l)$$

  where $w_j$ are the layer's static weights over the 12 encoder layers and $\gamma_j$ is a per-channel scale vector initialized to 0 (at the start of training every layer reads only $b$).
- **Decoder**: 4-layer non-autoregressive decoder (width 512, SwiGLU FFN 2048; self-attention over position slots + cross-attention to memory, QK-Norm). All 65 output positions are produced at once and cut at the end token.
- **Vocabulary**: 6,817 characters (`nar_vocabulary_6817.json`).

**fp16-ready weights**: some layers of the released weights are rescaled equivalently, with the eps of the affected RMSNorms adjusted to match; the parameters are in `reparam` in `config.json`. In fp32 the outputs match the original checkpoint (logit differences about 4e-5); in fp16 the intermediate activations no longer overflow. Weights are stored in fp32 and can be cast to fp16 after loading.

**manga-ocr-nar-small-distil** keeps the same design with a smaller student cut from manga-ocr-nar-small:

- Encoder: 6 of the 12 layers (every second one, the last included); the depth fusion keeps the matching layers.
- Decoder: 4 layers, width 384 (6 heads of 64), SwiGLU FFN 1536. The kept channels, heads and FFN units were chosen by their importance on training batches, then all tensors were sliced.
- int8 quantization in training: the inputs of every linear layer of the encoder blocks, the memory bridge and projection, the decoder and the output head are quantized to uint8 per tensor (learned scale and zero point), weights to int8 per output channel. Patch embedding, attention products, norms and residual additions stay in floating point.
- The released weights are stored as their dequantized int8 values; `act_quant` in `config.json` holds the activation scales and zero points, which the PyTorch code applies (quantize-dequantize) to reproduce the int8 model. The weights alone, without this step, are not a usable float model (EM about 81% on Read v1.3).
- The same equivalent fp16 rescaling as above (`reparam`), computed on the quantized model.

## Training

**manga-ocr-nar-small**

- Trained from scratch (encoder initialized from MonkeyOCRv2-S), 279,499 steps, batch 128, 35,775,872 images seen (8 epochs). 4 × RTX 2080 Ti, decoder in fp32, the rest in fp16 mixed precision.
- Training set, 4,471,985 images:

| Source | Images | Share |
|---|---|---|
| Synthetic printed | 1,795,869 | 40.2% |
| Synthetic handwriting | 1,670,000 | 37.3% |
| AnimeText-OCR | 1,006,116 | 22.5% |

- AnimeText-OCR: [real manga crops](https://huggingface.co/datasets/JustANormalTinkerer/animetext-ocr) with sequence confidence 0.90–0.98.
- Several distribution parameters of the synthetic data were set from aggregate statistics of the benchmark's candidate pool; the statistics are published in `docs/pool_stats/` of the benchmark repository.
- How the synthetic handwriting is made (assets, random factors, layout rules, checks, samples): [docs/synthetic_handwriting.md](docs/synthetic_handwriting.md).

**manga-ocr-nar-small-distil**

- Teacher: manga-ocr-nar-small. Same training set; rows whose label is a fixed placeholder sentence of AnimeText-OCR were dropped.
- Loss: the training loss of manga-ocr-nar-small (cross-entropy on the labels and a slot-occupancy term) + KL divergence to the teacher's output distribution + relative MSE between the student's and the teacher's decoder memories.
- Stage 1: 31,250 steps, batch 128 (4.0M images), 1 × RTX 2080 Ti; float for the first 4,687 steps, then int8 quantization on.
- Stage 2: 69,874 steps, batch 256 (17.9M images), 4 × RTX 2080 Ti, int8 quantization throughout.

## Files

On Hugging Face and ModelScope:

| File | manga-ocr-nar-small | manga-ocr-nar-small-distil |
|---|---|---|
| `model.safetensors` | weights, fp32, 217 MB | weights (dequantized int8 values), fp32, 119 MB |
| `config.json` | architecture, fp16 rescaling | architecture, fp16 rescaling, activation quantization, ONNX files |
| `nar_vocabulary_6817.json` | vocabulary | vocabulary |
| `onnx/` | ONNX fp32 for CPU, 213 MB | ONNX int8 for CPU, u8s8 and u8u8, 31 MB each |
| `coreml/` | CoreML for Mac, 107 MB | — |
| `manga_ocr_nar_small/` | inference code (same in both) | inference code (same in both) |
| `samples/` | example crops | — |
| `SHA256SUMS` | checksums | checksums |

- ONNX runs at batch = 1. The CoreML file is a multifunction package (batch 1/2/4/8/16) and needs macOS 15 or later.
- Licenses and provenance: `LICENSE`, `LICENSE_MODEL`, `NOTICE.md`.

## Usage

Download a model repository from Hugging Face or ModelScope (GitHub has no weights):

```bash
git lfs install
git clone https://huggingface.co/muscgab/manga-ocr-nar-small          # or muscgab/manga-ocr-nar-small-distil
# or: modelscope download --model muscgab/manga-ocr-nar-small --local_dir manga-ocr-nar-small
cd manga-ocr-nar-small
```

Install inside the repository directory with one extra for your platform:

```bash
pip install -e ".[cuda]"   # NVIDIA GPU: torch and safetensors
pip install -e ".[cpu]"    # CPU: onnxruntime
pip install -e ".[mac]"    # Mac (macOS 15+, manga-ocr-nar-small only): pyobjc-framework-CoreML, no torch needed
```

```python
from manga_ocr_nar_small import MangaOcrNarSmall
ocr = MangaOcrNarSmall()                   # backend="auto": CUDA if available, CoreML on macOS 15+ (if the model has it), otherwise ONNX
ocr("crop.png")                            # one crop -> str
ocr(["crop1.png", "crop2.png"])            # crops of one page together -> list[str], processed as one batch
```

The model is the repository the code is loaded from; pass `model_dir=` (or set `MANGA_OCR_NAR_SMALL_DIR`) to use another one, for example `MangaOcrNarSmall(model_dir="manga-ocr-nar-small-distil")`. PIL images and uint8 RGB arrays are accepted too. Command line:

```bash
manga-ocr-nar-small crop1.png crop2.png     # prints "path<TAB>text" per line; --model-dir, --backend, --int8
```

**GPU down-clocking (CUDA only)**: the GPU lowers its clock after a few seconds idle, so the next request is slower. On an RTX 2080 Ti the first crop after 20 s idle takes 24.7 ms instead of 7.5 ms (manga-ocr-nar-small); one page at a time takes 53 ms per page with 10 s between pages and 37 ms when processing continuously. To keep top speed, lock the GPU clock at its maximum (needs administrator rights; restore with `nvidia-smi -rgc` afterwards):

```text
nvidia-smi -lgc <max clock>,<max clock>
```

You can also set the power management mode to "Prefer maximum performance" in the NVIDIA Control Panel. Locking the clock increases idle power and heat. The effect depends on the GPU: a laptop GTX 1060 Max-Q only drops to 1,265–1,392 MHz when idle, and with the same 8 pages one at a time and 30 s between pages the total time is only about 4.5% higher than processing continuously.

Inputs are cropped text boxes; this package does not include text detection. On the first run on a Mac the CoreML package is compiled into the `coreml/` directory and loaded directly afterwards.

## Limitations

- Targets dialogue, narration and side notes in Japanese manga; onomatopoeia is not a target.
- At most 65 output positions; longer text boxes need to be split first.
- Non-printed text (handwriting, decorative lettering) has clearly more errors than printed text (manga-ocr-nar-small: CER 4.14% vs 1.24%).
- manga-ocr-nar-small-distil is weaker on long boxes (more than 32 characters: EM 63.91% vs 73.96%) and on non-printed text (76.31% vs 80.81%).
- Speed was measured only on the devices above.

## Acknowledgements

- [MonkeyOCRv2](https://arxiv.org/abs/2607.11562): encoder architecture and initial weights (MonkeyOCRv2-S).
- [CPPD](https://arxiv.org/abs/2307.12270): the idea of parallel decoding with a set of ordered queries.
- [AnimeText](https://arxiv.org/abs/2510.07951) and [AnimeText-OCR](https://huggingface.co/datasets/JustANormalTinkerer/animetext-ocr): real training crops; the real kana glyphs used by the synthetic handwriting were also cut from AnimeText images.
- [Real-ESRGAN](https://arxiv.org/abs/2107.10833): the kana glyphs of the synthetic handwriting were upscaled 4× with RealESRGAN_x4plus_anime_6B.
- [Hayai](https://huggingface.co/JustANormalTinkerer/hayai-ocr-v2.5-nova) and [mangaOCR](https://huggingface.co/kha-white/manga-ocr-base): reference models during development and evaluation.

## License

- Code: Apache License 2.0 (`LICENSE`).
- Model weights (both models): CC BY-NC-SA 4.0 (`LICENSE_MODEL`). The training data AnimeText-OCR is CC BY-NC-SA 4.0.
- The encoder is initialized from MonkeyOCRv2-S, whose upstream code and weights are Apache License 2.0. See `NOTICE.md` for provenance.
