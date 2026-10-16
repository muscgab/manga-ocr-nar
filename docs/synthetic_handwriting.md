# Synthetic handwriting data

[English](synthetic_handwriting.md) | [中文](synthetic_handwriting_zh.md)

Training data of manga-ocr-nar-small, manga-ocr-nar-small-distil and manga-ocr-base-CPT: 1,670,000 synthetic handwriting images, 37.3% of the training set. This page describes how our renderer makes them. The renderer itself is not released, because it is built around a text corpus taken from copyrighted manga.

## Samples

Ten images exactly as they appear in the training set (picked from a random sample of finished images for short, everyday sentences). The label is the training target.

| Image | Label | Image | Label |
|---|---|---|---|
| <img src="synthetic_handwriting/hw01.png" height="110"> | くわしいなー | <img src="synthetic_handwriting/hw06.png" height="160"> | じゃあいいじゃん |
| <img src="synthetic_handwriting/hw02.png" height="100"> | なんだそれ… | <img src="synthetic_handwriting/hw07.png" width="260"> | そりゃそうだな… |
| <img src="synthetic_handwriting/hw03.png" height="160"> | もしかして、 | <img src="synthetic_handwriting/hw08.png" width="260"> | 確認をしたいので |
| <img src="synthetic_handwriting/hw04.png" height="200"> | 分かるんだよ | <img src="synthetic_handwriting/hw09.png" height="160"> | いいこと思いついたんだ |
| <img src="synthetic_handwriting/hw05.png" height="140"> | ちょうどよかった | <img src="synthetic_handwriting/hw10.png" height="200"> | 冷静に考えると |

## Overview

Each image is built glyph by glyph, not typeset with one font in one pass:

1. **Plan**: draw the sample's settings from fixed quotas (text length, glyph height, vertical or horizontal, number of lines, scene, style, branch).
2. **Text**: pick a line from the corpus that the chosen font can draw completely; optionally add punctuation or change how a symbol is written.
3. **Glyphs**: render every character separately from a handwriting font; replace kana with real handwritten kana glyphs whose stroke width matches.
4. **Layout**: place the glyphs along hand-drawn-looking lines, with random size, rotation, spacing and line shape, plus rules for punctuation, small kana and numbers.
5. **Scene**: put the text into a speech balloon or directly onto a real manga background, crop, and simulate printing and image compression.
6. **Checks**: reject the image if any glyph is unreadable, touches too much, or breaks the rules, and draw again; after each batch, an independent audit re-checks every saved image.

## 1. Assets

### 1.1 Text

- Source: the text of a private manga collection (6,085 books, 662,305 pages). The renderer and the corpus stay private for this reason; the 10 samples above are short everyday sentences.
- OCR: a comic text/bubble detector (ogkalu) cut the text boxes, and [manga-ocr](https://github.com/kha-white/manga-ocr) read them as the teacher. On 12.0% of the boxes (573,953 of 4,765,926), PaddleOCR-VL-For-Manga also read the box and a likelihood rule chose between the two readings; manga-ocr's reading was kept for 97.8% of all boxes.
- Cleaning by two language models, OpenAI GPT-5.6 Luna and Terra, each called without tools and with only the text it judges. Luna proposes keep / delete / fix for each line; Terra (high reasoning) rules on every Luna proposal other than keep, seeing the whole page's text; a line is deleted only on Terra's verdict. Only clear advertising, credits, website watermarks and scan-group residue are removed. Anything that may belong to the story is kept (attack names, game UI, sound effects, titles), and so is anything uncertain.
  - The first 372,851 pages went through an earlier pass of this kind under older rules, which also removed chapter titles and skill/UI labels.
  - The other 289,454 pages (2,064,508 lines): a rule pre-screen kept 2,039,154 lines directly; Luna judged the remaining 25,354 (550 per request) and Terra 18,199 of them; a final rule check restored 1,658 lines that Terra had marked for deletion; 8,659 lines were deleted.
- Deduplication: of 4,412,517 non-empty lines, lines that are not Japanese, contain no letters, or have unbalanced brackets were dropped; the rest were deduplicated across books into 3,325,673 unique lines, each with its occurrence count.
- Split by book: lines from 587 books are kept for validation renders only; training renders use the rest.
- Per length bucket, the first N lines in a fixed random order: 1–4 characters all 162,157; 5–8 characters 292,000; 9–16 characters 198,000; 17–32 characters 76,000 (728,157 lines).
- Rule filter: lines with advertising residue, rare Latin tokens or rare characters were removed (1,395 lines).
- Sampling weight: how often the line occurs in the source, and × 2.2 for lines written only in kana. Sampling by occurrence alone gives about 47% kana-only lines; the reference boxes of 2.1 have 61%, and the factor 2.2 brings it to about 61%.
- Labels use the project's training normalization (for example `．．．` → `…`, `！` → `!`, `～` → `〜`). Source lines have at most 32 characters.

### 1.2 Fonts

- Free Japanese handwriting fonts were collected from their authors' sites (51 at first, a few more later), with source and license recorded for each. No font file is distributed.
- Every glyph outline was checked for being non-empty: a font's character map often lists characters it cannot actually draw, so lines are matched to what each font really draws.
- Visual selection: kept clear everyday handwriting; dropped cursive and semi-cursive brush styles and strongly decorative fonts.
- Final pool: 42 faces from 29 fonts, in three groups (everyday 35, emphatic 6, special 1). Group weights depend on the sample's style (a "note" mostly uses everyday fonts, an "emphasis" more emphatic ones).

  The fonts in the final pool:

  | Font | Author | Faces | Group |
  |---|---|---|---|
  | [仕事メモ書き](https://font.sumomo.ne.jp/shigoto.html) | Sumomomoji / Do-Font | 1 | everyday |
  | [DartsFont](https://www.p-darts.jp/font/dartsfont/) | DAICHI / ProjectDARTS | 1 | everyday |
  | [みちます](https://blog.masuseki.com/?p=197) | 桝田道也 / Michiya Masuda | 1 | everyday |
  | [きろ字 / Kiloji](https://kironono.hatenablog.jp/entry/fonts-kiloji) | kilo | 4 | everyday |
  | [851手書き雑フォント](https://pm85122.onamae.jp/851fontpage.html) | 8:51:22 pm | 1 | everyday |
  | [Y.OzFont ペン字版 (おおがな YOz)](http://yozvox.web.fc2.com/82A882B782B782DF8374834883938367.html) | Y.Oz Vox | 5 | everyday |
  | [Y.OzFont ペン字版 (こがな YOzakura)](http://yozvox.web.fc2.com/82A882B782B782DF8374834883938367.html) | Y.Oz Vox | 1 | everyday |
  | [KFひま字](https://www.kfstudio.net/font/kfhimaji/) | sachie / KF STUDIO | 1 | everyday |
  | [りいてがきN](http://aoirii.babyblue.jp/font/riitn/) | あおいりい | 1 | everyday |
  | [TekitouPoem / 適当ポエム](https://github.com/Hagi42/TekitouPoem-Font) | Hagi42 | 3 | everyday |
  | [ふい字](http://hp.vector.co.jp/authors/VA039499/) | ふい | 1 | everyday |
  | [まきばフォント](http://hp.vector.co.jp/authors/VA039499/) | ふい | 1 | everyday |
  | [あずきフォント](https://azukifont.com/font/azuki.html) | 日向梓 | 1 | everyday |
  | [うずらフォント](https://azukifont.com/font/uzura.html) | 日向梓 | 1 | everyday |
  | [あんずもじ2020](https://apricot.ciao.jp/site3-7.html) | 京風子 | 1 | everyday |
  | [みかちゃん](https://mikachan-font.com/) | みかちゃん | 4 | everyday |
  | [かずフォント](https://ikimono.uvs.jp/font/kazufont_menu.html) | かず | 1 | everyday |
  | [かずフォント２](https://ikimono.uvs.jp/font/kazufont_menu.html) | かず | 1 | everyday |
  | [Klee One](https://github.com/fontworks-fonts/Klee) | FONTWORKS | 1 | everyday |
  | [kawaii手書き文字](https://font.spicy-sweet.com/) | spicy-sweet | 1 | everyday |
  | [チルアウト / Chillout TYP](https://typingart.net/?p=471) | Typingart & Co. | 1 | everyday |
  | [Azuki LB](https://azukifont.com/font/azuki.html) | 日向梓 | 1 | everyday |
  | [Klee One SemiBold](https://github.com/fontworks-fonts/Klee) | FONTWORKS | 1 | everyday |
  | [851チカラヨワク](https://pm85122.onamae.jp/851ch-yw.html) | 8:51:22 pm | 1 | emphatic |
  | [851チカラヅヨク](https://pm85122.onamae.jp/851ch-dz.html) | 8:51:22 pm | 2 | emphatic |
  | [りいてがき筆](http://aoirii.babyblue.jp/font/riitf/index.html) | あおいりい | 1 | emphatic |
  | [Yuji Boku](https://github.com/Kinutafontfactory/Yuji) | Yuji Kataoka / Kinuta Font Factory | 1 | emphatic |
  | [おつとめフォント](https://font.sleepcows.com/) | 何某亭 | 1 | emphatic |
  | [BR Wakaisho](https://github.com/BridgeRiver/BRWakaishotai) | BridgeRiver | 1 | special |

- A font is used for a line only if it draws every character of the line. If one symbol is missing, the whole line switches to another font (at most 2 times); the renderer never mixes in a fallback font for letters.
- Very small text (below 13 px) uses only 13 faces that stay readable at that size, and kanji with at most 10 strokes.

### 1.3 Real handwritten kana

Fonts are drawn by font designers; real manga handwriting is not. So kana (not kanji) are partly taken from real manga pages:

1. **Candidate pages**: [AnimeText-OCR](https://huggingface.co/datasets/JustANormalTinkerer/animetext-ocr) (fixed revision) crops scored by a small classifier on frozen DINO features for handwritten appearance. Kept: handwriting score ≥ 0.95, Japanese, OCR confidence ≥ 0.9, 3–40 characters with at least 2 kana, short side ≥ 18 px. Only handwritten dialogue and side notes; no sound effects, no kanji.
2. **Cropping by a vision model**: 8 separate GPT-6.1 Sol sessions looked at each source image, chose a rotation and a box per kana, and a deterministic script cut the pixels (no redrawing). Each session then reviewed its own contact sheets and fixed wrong labels (for example ん/人, せ/た, ユ/エ, ぷ/ぶ); the main agent and independent Sol sessions spot-checked. Result: 4,843 single kana from 1,201 source images, 159 labels (2,733 hiragana, 2,110 katakana).
3. **Cleaning**: Sol removed dirt and stroke fragments of neighbouring characters, only by deleting marked components of a colour-separated alpha mask; glyphs with missing strokes, wrong labels or inseparable neighbours were quarantined. 4,475 clean, 368 quarantined.
4. **Upscaling**: RealESRGAN_x4plus_anime_6B ×4 (compared with SwinIR ×2, HAT ×4 and contour smoothing on test sets first). Sol and the main agent checked every upscaled glyph against its source and fixed artefacts (false white cores, grey seams, leftover dots); 513 glyphs were edited. 4,352 accepted, 103 watch, 20 quarantined.
5. **Human review**: the author reviewed all 4,352 glyphs by character in a grid page and rejected 62 → 4,290 glyphs. Small ぃ (no reliable native sample) is a scaled-down い (50 derived glyphs) → 4,340 entries, 159 labels.
6. **Uprighting**: glyphs cut from slanted lines carry the line's slant. Four Sol sessions estimated the reading axis of each text line or column in the source image (1,170 sources), and all glyphs of that line were rotated together so the line becomes upright, keeping each glyph's own natural slant. 13 glyphs without a reliable axis were set by hand by the author. 2,940 rotated, 1,350 unchanged.
7. **Use in rendering**: a kana is replaced only by a bank glyph whose stroke width is within ×1.35 of the line's target; all body glyphs of an image must stay within ×1.65 of each other in stroke width. A glyph is never enlarged beyond 4× its native crop; otherwise the font's glyph is used.

### 1.4 Backgrounds

- 101,079 text-free crops from [AnimeText](https://huggingface.co/datasets/deepghs/AnimeText) (fixed revision, train split); 96,043 are used for training renders and 5,036 for validation renders.
- Per source page: take the union of the annotated text boxes and a text detector's boxes, expand each by max(16 px, 15%), and search for free rectangles with both sides ≥ 192 px (native pixels; no upscaling, erasing or inpainting). At most 3 crops per page.
- Rejected: large flat areas (a flat connected region ≥ 20% or a flat rectangle ≥ 15% of the crop, any colour); any hit of a comic text detector, run on the crop, its 90° rotation and overlapping 512 px windows; isolated dark marks touching the crop edge.
- Every crop was then checked visually by a GPT-5.6 Luna session (4 images per request) for leftover text, sound effects and isolated punctuation; suspicious crops were rejected. A second, stricter pass over white marks quarantined 1,980 of 11,091 re-checked crops.
- Checked against the page IDs of our benchmark ([JMangaBench_Read](https://github.com/muscgab/JMangaBench_Read), 2,726 IDs): no overlap.

### 1.5 Speech balloons

- 52 balloon images with writable-area masks: 28 made with GPT Image from reference balloons (text removed, outline kept), then picked by the author and stretched to balanced proportions; 17 from manga-editor-desu (GPL-3, SVG); 4 drawn by the author; 3 procedural.
- Shapes include oval, caption box, cloud, thought, burst, thorn, polygon, heart and others. 40 have a dark outline, 10 none, 2 are white text on black.
- No single balloon may exceed 1/26 (3.85%) of balloon samples; over-used ones were down-weighted in three calibration rounds.

## 2. Rendering one image

### 2.1 Planned distributions

Every dimension is an exact quota over a batch (shuffled deterministically), not an independent coin flip:

| Dimension | Values |
|---|---|
| Text length | 1–4 / 5–8 / 9–16 / 17–32 characters: 43.4 / 29.2 / 19.8 / 7.6% |
| Glyph height | 16 bins from 8 to 96 px (8–15 px together 5.9%, 15–33 px 43.6%, 33–96 px 50.5%) |
| Orientation | vertical 85%, horizontal 15% (recipes can override) |
| Lines | depends on length, for example 1–4 characters: 1 line 92%; 17–32 characters: 1/2/3/4 lines 3/50/37/10% |
| Scene | in a speech balloon 80%, directly on a manga background 20% |
| Style | note 35%, mutter 30%, emphasis 20%, expressive 15% (style changes font groups and how strongly lines bend) |
| Branch | recipe 40%, capped 30%, free 30% (see 2.3) |

The length and glyph-height distributions follow the marginals of 2,516 real non-printed text boxes from the candidate pool of our benchmark (boxes that GPT-6.1 Sol labelled non-printed, i.e. handwritten, artistic or mixed; the benchmark's own pages and sound effects excluded). Only these summary statistics were used, never the images.

### 2.2 Text changes

- **Label-changing additions** (the label is recomputed): insert a comma 14%, a wave dash 10%, a doubled mark 4.5%, ♪ 0.6%; lengthen a wave 15%, a very long ellipsis 1.7%.
- **Label-preserving variants** (10% per group): write the same thing another way, for example `!?` vs `！？`, three-dot vs two-dot pause, different long-dash forms. Ellipses keep their exact dot count; 5 or more dots become a long ellipsis over two cells.
- Hearts (♡) are drawn as shapes.

### 2.3 Three branches

- **Recipe (40%)**: one of 15 layout recipes written after studying real manga handwriting, for example "near-straight natural handwriting", "short line slanted as a whole", "one line with a soft bend and drift", "parallel columns with uneven ends", "dense block", "sparse short reaction", "small long horizontal side note", "short lead-in then a long text", "repeated short words offset as a group". Each recipe fixes its own track count, orientation and the strength of each variation.
- **Capped (30%)**: the variation factors of 2.4 are drawn freely, but at most 2 may be at the strongest level, and a strong size change excludes other strong factors.
- **Free (30%)**: the same factors without the cap.

### 2.4 Random variation factors

Each factor is switched on with its own probability and then gets a strength level 1–5 (levels 1/2/3/4/5 with probability 6/24/40/24/6%; the glyph-rotation and line-angle factors also draw a direction):

| Factor | On | What it changes |
|---|---|---|
| Glyph size | 90% | smooth size trend along the line plus per-glyph jitter (level 5: about ×0.89–1.37) |
| Glyph rotation | 88% | slow tilt trend plus noise, clockwise or counter-clockwise (level 5: 8–12°) |
| Glyph slant | 70% | shear of the glyphs to the right or left, repeated glyphs differ slightly (level 5: 14–15°) |
| Aspect | 82% | narrower or wider glyphs (level 5: ×0.75–0.83 or ×1.20–1.31) |
| Line shape | 85% | random-walk curve through 4–10 knots, RMS 0.10–0.18 em (15% stronger) |
| Whole-text angle | 90% | rotate everything, mostly small (level 1 55%) |
| Line angle | 55% | lines tilt independently of each other |
| Spacing | 90% | looser or irregular gaps with a persistent rhythm (narrow / normal / wide) |
| Columns | 75% | looser columns, staggered starts |
| Phrase emphasis | 18% | one word of 2–10 characters ×1.34–1.50 larger |
| Attachments | 75% | small trailing marks such as ♡ ! ? next to the text |
| Symbols | 72% | length and thickness of long dashes, waves and ellipses |
| Punctuation rotation | 60% | rotate punctuation 15–40° |
| Punctuation spacing | 85% | gaps after pauses and before closing brackets |
| Container | 80% | fit text into the balloon's writable area |
| Crop | 95% | margins of the final crop, tight / loose / left / right |
| Acquisition | 70% | blur σ 0.15–0.4, small brightness and contrast change, down-sampling ×0.85–0.98 |

### 2.5 Layout

- **Splitting into lines**: break points prefer punctuation, with balanced lengths. One-line, two-line and multi-line layouts use templates such as compact, shared slant, staggered, contour-following, fanned tail and local emphasis. Depending on the style, 30–90% of lines follow an irregular hand-drawn curve instead of a straight line.
- **Layout routes**: normal 60%, two blocks 20% (a main block plus a smaller one at ×0.78–0.92, often slanted the opposite way), one low bend 20% (a 15–25° turn inside a line). The last two need long enough text, so in finished images two blocks appear in about 6%.
- **Glyph contact**: up to 3 neighbouring pairs may touch slightly, as in fast writing; the ink gap between consecutive glyphs is capped so a line never falls apart.
- **Pen**: one target stroke width per image; emphasis may be up to ×1.6 bolder; pen pressure varies smoothly over the text (×0.7–1.4).
- **Manga typesetting rules**:
  - 2-character numbers and Latin, `!!`, `!?` in vertical text are set horizontally in one cell (tate-chū-yoko); 3-character numbers in half of the cases;
  - small kana (ゃゅょっ…) sit offset in the cell, at most 82% of the size of a full kana;
  - vertical text uses vertical forms of brackets and long dashes;
  - ellipses sit centred in their cell; trailing `!!` or `!?` stand stacked vertically in 5% of cases.
- **Tiny text** (below 13 px): simpler layouts, smaller angles, wider gaps and stricter contrast.

### 2.6 Scene and imaging

- **In a balloon (80%)**: choose a balloon whose writable area fits the text's aspect ratio (up to 6 candidates), then crop around the text so 1.5–7.5% of the background shows (15% of the time 10–30%). 10% of balloons are fitted tightly around the ink (rotated up to ±25° and stretched).
- **Directly on a background (20%)**: 97% on bright areas with dark ink, 3% on difficult areas (including white ink); flat crops are rejected.
- **White under-layer** behind the text where the background would interfere: a soft outline (70%) or a wide white patch along the glyphs (30%).
- **Ink**: pure black in 87% of images, otherwise a dark grey or brown between 3 and 50 (luma), following the darkest ink of the real reference boxes.
- **Encoding**: rendered at 4× and reduced; saved as PNG (23%) or JPEG with quality 96–100 (56%), 84–88 (30%), 89–95 (11%), 60–83 (3%); small text never below 92.

## 3. Checks

### 3.1 Automatic checks on every image

An image is rejected and drawn again with a new seed (up to 160 attempts) if any check fails:

- every glyph keeps enough contrast against what is behind it (whole text and per glyph);
- glyph overlap ≤ 10% per glyph and ≤ 4% in total; touching only as allowed above;
- body glyph height not below 75% of the planned bin, visible ink above a floor;
- stroke width consistent across the image;
- gaps after punctuation and before neighbours stay open;
- no gap in a line beyond the limit;
- reading order, glyph ownership masks and label match the drawn image.

Some failures are repaired in place instead of starting over: swap the font of one kana that would exceed its size budget, drop one touching pair, undo tight spacing for one pair, or re-lay the two blocks. In 1,160,000 images rendered with the final configuration, 122,710 retries happened (0.11 per image); the most common reasons were inconsistent stroke width (37,153) and too little space between tightly set glyphs (30,784).

Because hard cases are retried, finished images lean slightly towards easier ones. On an earlier version we replayed the first attempt of every image: kana-only lines 61.8% at the first attempt vs 62.0% in finished images, lines with punctuation 53.0% vs 54.7%; the font mix differed by 4.7% (total variation).

### 3.2 Independent audit

- After every shard of 50 images, a separate audit reloads the saved PNG and masks and recomputes the checks; failing images are redrawn (up to 3 rounds).
- After every batch, a final audit runs over all images again.
- All batches whose audit records were kept (the 80 batches of the first 800,000 images and 116 batches of the last machine) passed the final audit with 0 replaced and 0 dropped images; the records of 14 other batches were not kept.
- Every batch records the SHA-256 of all code, the configuration, fonts, corpus, background and balloon lists. The same seed reproduces the same images byte for byte, which we used to check that parallel modes do not change the output.

### 3.3 Comparison with real handwriting

- **Geometry**: long side, aspect ratio, number of lines and vertical/horizontal share were compared bucket by bucket with the 2,516 real non-printed reference boxes. Remaining small differences were accepted; for example, boxes taller than wide make up 74.0% of our images vs 83.2% of the references.
- **Image statistics** (on an earlier version, 1,000 reference boxes): a small CNN separating real from synthetic crops (5-fold) reached AUC 0.63, and a logistic regression on 5 tone statistics 0.81. After matching the ink tone to the references, the tone-only AUC dropped to 0.64. The remaining difference is in the background (fewer pure white pixels, more paper texture). These tests are weak and were used to find differences, not as a pass mark.
- **"What looks wrong" checks** against the references led to concrete fixes, for example: line breaks inside words, too few hearts, balloon background showing too much or too little, too much tate-chū-yoko stacking, and pure-black ink being too frequent or too rare.

### 3.4 Looking at the images

- The renderer went through about 170 versions in three weeks. Changes were judged on sample sheets inspected by eye, by the author and by AI reviewers.
- The author reviewed the font pool, all real kana glyphs and the hand-set angles; balloons and background rules were changed after the author's comments.
- Before production, a written walkthrough of the whole production chain was checked line by line against the code and the remote machines in an independent review (Claude); the errors it found were corrected.
- After production, 250 random finished images were inspected.

## 4. Production

- 1,670,000 images in 167 batches of 10,000, each with its own seed, rendered on 5 machines and uploaded batch by batch.
- Two code versions with the same configuration: 800,000 images, then 870,000 images after a fix for a rare crash. The crash was an OpenCV edge-detection bug that corrupted memory; the fix runs that function without SIMD and does not change any output. Batches that had crashed were re-run with their original seeds and completed.

## 5. Limitations

- The contribution of this data was not measured on its own (no training run with and without it).
- Real handwritten glyphs exist only for kana; kanji, Latin and symbols come from fonts.
- The corpus is OCR output. Cleaning targeted non-story text, not misreadings, so some labels keep the teacher's OCR errors; the image is rendered from the same text, so image and label still agree.
- The reference boxes used for distributions and comparisons were labelled by a language model (GPT-6.1 Sol), not by people.
- Retries make finished images slightly easier than planned (3.1).
- The background crops come from one dataset (AnimeText), so their style range is limited to it.
- The corpus was not deduplicated against benchmark labels: in a check on the previous corpus version, 546 of 3,135 label texts of JMangaBench_Read v1.2 also occurred in it, almost all short common phrases (130 with 5 or more characters, 1 with 10 or more).
- In vertical text, a few dash-like marks were drawn rotated while the label kept the horizontal form. This was fixed in the renderer after this data had been produced.
