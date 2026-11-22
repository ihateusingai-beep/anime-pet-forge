# 奶黃貓貓 Neko

`anime-cat-pet` · v2 · 73 格 · 2.52 MiB

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

## 重點：尾巴剪影

第一版跑步 sheet 嘅尾巴向後飄，令角色寬高比到 1.36–1.45，**超出 192 px 格仔**。組裝器為咗塞得落，會將成行縮細 —— 貓貓喺跑步動畫入面就會突然比其它行細。

修正方法係喺 prompt 度直接規定剪影：

> "the fluffy tail is curled UP over the back in a compact curve close to the
> body, never stretched out behind. The whole cat stays compact: the total
> width of the cat is only slightly wider than the cat is tall."

重生成之後 `cap=1.00`，全行冇被縮。

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
