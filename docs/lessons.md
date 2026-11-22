# 製作紀錄：Anime Pet Forge

呢份係三隻寵物由零到匯入 App 嘅完整紀錄 —— 重點唔係「點做」，而係「邊度會出事」。

---

## 1. 目標與規格

MiniMax Pet v2 圖集規格（權威喺官方 `minimax-pet` skill）：

| 項目 | 值 |
|---|---|
| 畫布 | 1536 × 2288 px |
| 網格 | 8 欄 × 11 行 |
| 單格 | 192 × 208 px |
| 動畫軌 | 9 條 = 57 格（idle 6 / run-right 8 / run-left 8 / wave 4 / jump 5 / failed 8 / waiting 6 / work 6 / review 6） |
| 視線方向 | 16 格（row 9 同 row 10，每行 8 格，22.5° 步進，0° = **上**） |
| 總格數 | 73 |
| 編碼 | 靜態 8-bit RGBA 非交錯 PNG，真 alpha，≤ 8 MiB |

**關鍵理解**：視線唔係由「右」開始。0° 係**向上**，順時針 22.5° 一格。所以 row 9 係「上 → 右下」，row 10 係「下 → 左上」。

---

## 2. 三隻寵物

| Pet | 角色 | 特殊處理 |
|---|---|---|
| `anime-cat-pet` | 原創奶黃貓貓 | 尾巴剪影問題（見 §4.1） |
| `eva-rei-pet` | 原創 chibi 零波（短鮑頭） | 基礎款 |
| `eva-rei-long-pet` | 原創 chibi 零波（及腰長直藍髮 + 呆毛 + 紅髮夾） | 長髮兩條規則（見 §4.2） |

---

## 3. 圖片生成呢一步

### 3.1 角色設定圖係整個流程嘅「真相來源」

所有姿勢 sheet 都係**掛住同一張設定圖**去生成。設定圖一差，全 73 格都差。

所以設定圖一定用 **text-only 文字設計稿**寫，唔靠運氣 —— 模型冇其它線索，你唔講佢就唔會自己決定。

### 3.2 ⚠️ 官方圖片搜尋服務掛咗

`connector__matrix__search_images` 連續 3 次即時失敗（serper provider，`latency_ms=0`）。

**處理**：改用 `web_search` 文字核實官方造型細節，再用文字設計稿重建角色。

**後續影響**：長髮版**唔係**由用戶附嘅官方圖 pixel 改出。呢點要主動同用戶講清楚，唔可以扮成係「ref 咗官方圖」。同樣地，官方 EVA 圖本身觸發咗 image model 嘅安全過濾器（`err_code: 451`），按規則冇改 prompt 重試。

### 3.3 ⚠️ Reference URL 會過期

設定圖要上載去簽名臨時 URL（大約 1 個鐘）。**每批之前都要重新上載**。用過期 URL 唔一定會 error —— 有可能照樣生成，但角色變咗另一個。

### 3.4 批次

每批 3 張 sheet（gaze 單獨一批因為 16 格要 4K 方形）。一隻寵物 = 1 張設定圖 + 4 批 = 5 次生成。

---

## 4. 版面：三個真實踩過嘅坑

### 4.1 尾巴令成行被縮細 🔴

貓貓第一版跑步 sheet，尾巴向後飄，角色寬高比到 **1.36–1.45**，超出 192 px 格仔。

組裝器嘅做法係：如果有任何一格會爆格，就將**成行**縮細去遷就。於是貓貓喺跑步動畫入面**突然比其它行細**，但：

- validator 全綠
- 匯入成功
- 完全冇任何警告

**修正**：喺 prompt 直接規定剪影 ——

> "the fluffy tail is curled UP over the back in a compact curve close to the
> body, never stretched out behind."

重生成之後 `cap=1.00`，全行冇被縮。

💡 **守門**：組裝器每行都印 `cap=` 數值。`cap < 1.00` = 呢行被縮過，唔應該接受。

### 4.2 長髮有兩種爆格方式 🔴

| 情況 | 症狀 | 對策 |
|---|---|---|
| 站立時散開 | 角色變闊 | `prompts.global_note`：「hangs in a compact curtain … never fanning out to the sides」 |
| 跑步時揚開 | 剪影拉長 | 跑步 sheet 專屬 note：「close to her back and shoulders … the whole figure stays upright and narrow」 |

兩樣都要寫，唔可以二選一。

### 4.3 Sheet 嘅 panel 唔會均分 🔴

模型畫出嚟嘅 4×4 網格，panel 唔等大。組裝器用 alpha mask 反推真實 panel 邊界，唔啱就 fallback 做平均切分。

但如果 sheet 入面有一條**淡淡嘅水平線**（地平線、枱邊），相對門檻（峰值 2 %）會當佢係內容，column 數就對唔上 → 切格全錯。

**對策**：純白背景，冇地平線、冇地面線、冇陰影。

---

## 5. 組裝：點解要歸一化

每格 192 × 208，角色要：

1. **高度一致** → 用同行中位數做基準，再按 clamp 範圍微調個別 frame
2. **腳底線一致** → 用同行中位數腳底位置做 baseline
3. **唔爆格** → 計出全行縮放上限 `cap`，統一乘落所有 frame
4. **保留動作** → idle 嘅呼吸起伏、jump 嘅拋物弧要保留，所以 baseline 係「相對中位數」而唔係死值

`jump` 行用 `fixed_scale=True`：跳躍五格高度差太多，逐格 clamp 會令佢哋互相唔同大。

---

## 6. 重構成可重用 skill

原本三隻寵物各有自己一套 `tools/`，其中 `cutout.sh`、`fetch.sh` 完全一樣，`assemble.py` 只差 pet id 同 displayName。呢個唔適合放上 GitHub。

重構後：

| 之前 | 之後 |
|---|---|
| 3 份 `make_batch.py`，prompt 硬編碼 | 1 份通用 script + 每隻寵物一個 `char.json` |
| 3 份 `assemble.py` | 1 份，行 `char.json` 嘅參數 |
| prompt 無紀錄 | `char.json`（結構化）+ `prompts.json`（逐字紀錄） |

### 6.1 ⚠️ 遷移最容易出事嘅位：prompt 唔只一個版本

貓貓嘅 10 張 sheet 其實寫過唔同版本：

- `idle` 用**短版** character block + "In all six panels" ground line + 唔同嘅 grid 開頭
- `run-right` / `run-left` 用**重生成版**（尾巴修好嗰次），grid 開頭又唔同，background 都多咗 "no floor line"
- 其它用標準版

所以 `char.json` 支援 **per-sheet override**：`grid_header` / `character_prompt` / `ground_prompt` / `background_prompt`。

### 6.2 ⚠️ `note: ""` 同「冇 note」唔同

原本 `sheet()` 永遠會插入 `note`（預設空字串），即係 prompt 裡面永遠有一個**空段落**。但貓貓 `idle` 係手寫 prompt，**完全冇呢個段落**。

兩個 prompt 唔一樣。所以 `char.json` 用「**冇 `note` key**」代表段落唔存在，「`note: ""`」代表段落存在但係空。

### 6.3 驗證方法

唔可以「睇落啱」就算。兩個硬驗證：

```sh
# A) 由 char.json 重建嘅 prompt == 歷史 prompt？
#    → 30/30 EXACT MATCH

# B) 由新 script 組裝出嚟嘅圖集 == 已出貨圖集？
#    → from-sheets: diff = 0（三隻）
#    → from-frames: diff = 0（三隻）
```

B 之所以做到，係因為**每隻寵物都帶住 73 張單格 PNG**（`frames/`，共 19 MB）。咁樣任何人 clone 完都可以喺唔使重新生成任何一張圖嘅情況下，砌出完全相同嘅圖集。

---

## 7. 匯入 App

走 App 正規流程：外觀 → 匯入寵物 → 揀兩個檔 → 睇預覽 → 確認。

三個坑：

1. **上載後 input 會被清空** → 工具會報「file count mismatch」，係**假陰性**。要睇 App 自己嘅結果面板。
2. **桌面浮窗開住時，主 panel 係 `display:none !important`** → 匯入頁喺入面，要用 `style.setProperty(k, v, 'important')` 強制顯示先入得到。**用完要還原**，否則浮窗白屏。
3. **唔可以**寫 Host dataDir、唔可以用私有 endpoint、唔可以改安裝包。

匯入用嘅中轉檔放喺 `node_modules/.pet-import/`（已被 gitignore），用完以 `mavis-trash` 清走。

---

## 8. 安全

- `req/*.json` 入面有簽名 OSS URL（`x-oss-credential` + `x-oss-signature`）。**唔可以入 git。** 改用 `prompts.json` 保存 prompt 內容。
- 用戶自己個 repo（`chinese-reading`）全程冇被污染，`git status` 乾淨。
- 附圖觸發 451 之後，冇改 prompt 硬闖，亦冇將繞過手法寫成工具。

---

## 9. 下一步

- [ ] 學校實機測試（iPad + Windows 平板）—— 驗證有冇 zh-HK voice
- [ ] v2 `audio` 欄位：預生成 mp3 解決多音字同私隱問題
- [ ] 更多角色實驗（多隻不同剪影）
