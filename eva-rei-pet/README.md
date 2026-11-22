# 零波 Rei（短髮版）

`eva-rei-pet` · v2 · 73 格 · 2.38 MiB

原創 chibi 零波：鋼藍色鮑頭短髮（齊瀏海 + 兩條短側鬚）、紅色大眼、白色 EV 插入栓服（高身黑邊領口、髖部同大腿橙色滾邊、黑色帶扣、淡紫藍側片、深灰長靴），暖深棕描邊。

| 檔案 | 內容 |
|---|---|
| `pet.json` | App 讀嘅 metadata |
| `spritesheet.png` | 1536 × 2288 v2 圖集 |
| `atlas-preview.png` | 逐格預覽圖 |
| `char.json` | 生產設定 |
| `prompts.json` | 每張 sheet 逐字 prompt |
| `frames/` | 73 張單格 PNG |
| `refs/` | 角色設定原圖 |

## 關於原創性

呢隻係**原創 chibi 重新設計**，唔係官方 artwork 嘅改圖。官方 EVA 角色屬第三方 IP，所以：
* 唔畫任何 NERV logo 或者可讀文字（模型渲染文字一定出錯）
* 造型描述係由文字設計稿出發，唔係抄官方圖

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
