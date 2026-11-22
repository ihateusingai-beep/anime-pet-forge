# 奶黃貓貓 Neko

`anime-cat-pet` · v2 · 73 格 · 2.50 MiB

一隻原創 chibi 動漫風奶黃貓貓：奶白毛色、左耳同頭頂有蜜桃色虎斑、綠松石色大眼、粉色三角鼻、圓圓腮紅、w 形小嘴，暖深棕描邊，平面 cel-shading 動漫吉祥物風格。

| 檔案 | 內容 |
|---|---|
| `pet.json` | App 讀嘅 metadata |
| `spritesheet.png` | 1536 × 2288 v2 圖集（8 欄 × 11 行，每格 192 × 208） |
| `atlas-preview.png` | 逐格預覽圖 |
| `char.json` | 生產設定：reference prompt、10 張 sheet 嘅 panel 文字、組裝參數 |
| `prompts.json` | 每張 sheet 逐字記錄嘅 prompt（原樣存档） |
| `frames/` | 73 張單格 192 × 208 PNG |
| `refs/` | 角色設定原圖 |

## 重點：跑步嘅剪影（改咗兩次）

**第一版**：尾巴向後飄，角色寬高比到 1.36–1.45，超出 192 px 格仔。組裝器為咗塞得落，會將成行縮細 —— 貓貓喺跑步動畫入面就會突然比其它行細。

**第二版**：尾巴收起咗，但「壓低身體」嗰兩格仍然闊（w/h 1.19–1.21），成行依然要縮 11%。

**最終版**：改用**直立跳躍式**（head 喺 hip 正上方、前爪收喺胸前、後爪收喺 hip 下），w/h 跌到 0.84–0.86：

> "the cat bounds forward in a playful UPRIGHT bounding prance. Its chest and head are
> held HIGH, its back is nearly vertical, and the head sits directly above the hips,
> so the body reads as a tall compact shape rather than a long horizontal one …
> The front paws reach down and forward under the chest and never stretch out in
> front of the face; the hind paws tuck under the hips and never stretch out behind."

結果：**10 行全部 `cap=1.00`、每格高度都係 168–168**，跑步動畫同企立完全同大。

💡 **守門**：`scripts/check_atlas.py` 會由圖集反推每行嘅 cap（完成品每行中位高度 = `target_h × cap`），所以呢類問題唔會再靜靜漏過。

## 重建

```sh
python3 ../skill/anime-pet-forge/scripts/assemble_atlas.py \
        --char char.json --from-frames frames --out .
```

輸出與 `spritesheet.png` **逐像素一致**（已驗證 diff = 0）。

## 驗證

```
官方 validator → {"ok": true, "version": 2, "width": 1536, "height": 2288,
                   "frames": 73, "warnings": []}
```
