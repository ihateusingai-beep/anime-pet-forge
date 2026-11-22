# 安裝

## 只需要 skill（唔要寵物成品）

```sh
git clone https://github.com/ihateusingai-beep/anime-pet-forge.git
cp -R anime-pet-forge/skill/anime-pet-forge ~/.minimax/skills/
```

之後喺 MiniMax Code 入面就會見到 `anime-pet-forge` skill。

Hermes Agent 用同一個格式：

```sh
cp -R anime-pet-forge/skill/anime-pet-forge ~/.hermes/skills/creative/
```

---

## 依賴

| 依賴 | 用途 | 備註 |
|---|---|---|
| **Node.js ≥ 22** | 官方 validator (`validate-art.mjs`) | 唔需要 `npm install`，validator 零依賴 |
| **Python 3 + Pillow** | 組裝器 `assemble_atlas.py` | `pip install pillow` |
| **mcode-tools CLI** | 圖片生成、去背、落載 | MiniMax Code 內置 |
| **官方 `minimax-pet` plugin** | 規格同 validator | `validate.sh` 會喺 runtime 自動搵返佢，唔會 hardcode 路徑 |

`validate.sh` 會自己搵官方 skill 目錄：

```
~/.minimax/**/skills/minimax-pet/scripts/validate-art.mjs
```

搵唔到就會直接報錯退出，唔會靜靜跳過驗證。

---

## 匯入一隻寵物

1. 裝好官方 **MiniMax Pet** plugin
2. 打開 App → **外觀** → **匯入寵物**
3. 一齊揀 `pet.json` 同 `spritesheet.png`（兩個都要）
4. 睇預覽圖 → 確認

每隻寵物用自己嘅 id。覆蓋一個已經存在嘅 id 之前，**一定先問用戶**。

匯入用嘅中轉檔放喺一個已經被 gitignore 嘅位置（例如 `node_modules/.pet-import/`），用完即刻清走，唔好留低喺 repo 入面。

---

## 重建圖集（唔使重新生成任何圖）

```sh
python3 skill/anime-pet-forge/scripts/assemble_atlas.py \
        --char anime-cat-pet/char.json \
        --from-frames anime-cat-pet/frames \
        --out anime-cat-pet
```

輸出與 repo 入面嘅 `spritesheet.png` **逐像素一致**（三隻都驗證過 diff = 0）。

之後記得重新驗證：

```sh
bash skill/anime-pet-forge/scripts/validate.sh anime-cat-pet
```
