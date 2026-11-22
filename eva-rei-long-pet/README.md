# 零波 Rei 長髮版

`eva-rei-long-pet` · v2 · 73 格 · 2.55 MiB

官方長髮造型嘅原創 chibi 零波：**及腰長直鋼藍髮**、頭頂**三角呆毛**、 bangs 側邊**紅色髮夾**、兩條長側鬚、紅色大眼，白色 EV 插入栓服配橙色滾邊。插入栓服沿用短髮版，保持桌寵家族一致。

| 檔案 | 內容 |
|---|---|
| `pet.json` | App 讀嘅 metadata |
| `spritesheet.png` | 1536 × 2288 v2 圖集 |
| `atlas-preview.png` | 逐格預覽圖 |
| `char.json` | 生產設定 |
| `prompts.json` | 每張 sheet 逐字 prompt |
| `frames/` | 73 張單格 PNG |
| `refs/` | 角色設定原圖 |

## 造型依據

官方長髮零 = EVA 3.0+1.0 時代造型：及腰長直藍髮 + 三角呆毛 + 紅色髮夾。

⚠️ **呢隻唔係由用戶附嘅官方圖 pixel 改出。** 該圖觸發咗官方 image model 嘅安全過濾器（`err_code: 451`），按規則冇改 prompt 重試；而家官方圖片搜尋服務亦不可用。所以係**用文字設計稿（text-only）重新設計**同一個角色 —— 保留辨識特徵，但係乾淨原創重繪。

## 兩條長髮專屬規則

長髮有兩種爆格方式，兩樣都要喺 prompt 封死：

1. **站立時散開** → `prompts.global_note`：
   > "Her long hair hangs in a compact curtain close to her body in every pose,
   > never fanning out to the sides."

2. **跑步時揚開** → 跑步 sheet 專屬 note：
   > "her long hair hangs in a compact curtain close to her back and shoulders,
   > never fanning out wide. The whole figure stays upright and narrow"

## 重建

```sh
python3 ../skill/anime-pet-forge/scripts/assemble_atlas.py \
        --char char.json --from-frames frames --out .
```

逐像素一致（已驗證 diff = 0）。

## 驗證

```
官方 validator → {"ok": true, "version": 2, "width": 1536, "height": 2288,
                   "frames": 73, "warnings": []}
```
