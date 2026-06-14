# LitDB / Pigtail / MedQA 部署設定 SOP

**版本**：1.0 ｜ **更新日期**：2026-06-14 ｜ **作者**：Jeremy / Claude

---

## 一、系統架構總覽

```
GitHub（程式碼倉庫）
  ├── ChiuChangRu/litdb      ← 文獻知識管理系統
  ├── ChiuChangRu/Pigtail    ← 文獻自動檢索（已停用日報）
  └── ChiuChangRu/DMAIC      ← MedQA 品質管理工具

GitHub Pages（免費網頁託管）
  ├── chiuchangru.github.io/litdb/
  └── chiuchangru.github.io/Pigtail/

外部服務
  ├── Anthropic API（Claude AI，付費）
  ├── Google OAuth（Sheets 同步，免費）
  └── Semantic Scholar API（引文查詢，免費）
```

---

## 二、GitHub Token 設定（一次性）

### 用途
讓 Claude 可以直接從對話中推送程式碼到你的 GitHub 倉庫，不需要手動上傳。

### 步驟

1. 用瀏覽器打開：`github.com/settings/tokens/new`
2. 填入：
   - **Note**：`claude-deploy`
   - **Expiration**：No expiration
   - **Select scopes**：勾選 `repo`（整個勾）
3. 點 **Generate token**
4. 複製 `ghp_...` 開頭的 token
5. 在 Claude 對話中貼上 token

### 安全注意

- Token 等同密碼，不要分享給他人
- 隨時可到 `github.com/settings/tokens` 撤銷
- 建議定期更換（每 3-6 個月）

### 目前使用中的 Token

```
（請在 Claude 對話中提供）
```

> ⚠️ 如果此 token 失效，重新產生一個貼給 Claude 即可。

---

## 三、日常更新流程

### 請 Claude 修改並推送

```
你：「幫我把 litdb 的搜尋框改成支援 OR 搜尋」
Claude：（修改程式碼）→（推送到 GitHub）→「✅ 推送成功」
你：重新整理 chiuchangru.github.io/litdb/ 即可看到更新
```

### 推送指令格式（Claude 內部使用）

```bash
# 1. 取得目前檔案的 SHA
SHA=$(curl -s -H "Authorization: token {TOKEN}" \
  https://api.github.com/repos/ChiuChangRu/{REPO}/contents/{FILE} \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('sha',''))")

# 2. 推送新版本
CONTENT=$(base64 -w 0 {LOCAL_FILE})
curl -s -X PUT \
  -H "Authorization: token {TOKEN}" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/ChiuChangRu/{REPO}/contents/{FILE} \
  -d '{"message":"commit message","content":"'$CONTENT'","sha":"'$SHA'"}'
```

---

## 四、GitHub Pages 設定（一次性）

### 用途
將 GitHub 倉庫的 HTML 檔案發布為可瀏覽的網頁。

### 步驟

1. 進入倉庫（例如 litdb）
2. Settings → Pages
3. Source：Deploy from a branch
4. Branch：main / root
5. Save

### 各倉庫 Pages 狀態

| 倉庫 | Pages | 網址 |
|------|-------|------|
| litdb | ✅ 已開啟 | chiuchangru.github.io/litdb/ |
| Pigtail | ✅ 已開啟 | chiuchangru.github.io/Pigtail/ |
| DMAIC | ✅ 已開啟 | chiuchangru.github.io/DMAIC/ |

---

## 五、Anthropic API Key 設定

### 用途
LitDB 的 AI 對話、AI 自動填入、翻譯功能需要 Claude API。

### 步驟

1. 前往 `console.anthropic.com`
2. 登入 → API Keys → Create Key
3. 複製 `sk-ant-api03-...` 金鑰

### 使用位置

| 用途 | 設定方式 |
|------|---------|
| LitDB AI 功能 | litdb 網頁 → ⚙ 設定 → Claude API Proxy URL |
| MedQA | HTML 檔案內的設定 |
| Pigtail 日報（已停用） | GitHub Secrets → ANTHROPIC_API_KEY |

### 費用監控

- 前往 `console.anthropic.com` → Usage 查看
- LitDB 日常使用：每月約 $1-2 USD
- 目前餘額：約 $2.70

---

## 六、Google OAuth 設定（一次性）

### 用途
LitDB 的 Google Sheets 同步功能（跨裝置備份）。

### 前置條件
- Google Cloud Console 帳號（免費）
- 專案名稱：litdb

### 步驟

1. 前往 `console.cloud.google.com`
2. 確認頂部專案為 **litdb**

#### 6.1 啟用 API
3. 左側 → API 和服務 → 程式庫
4. 搜尋並啟用 **Google Sheets API**
5. 搜尋並啟用 **Google Drive API**

#### 6.2 OAuth 同意畫面
6. 左側 → OAuth 同意畫面
7. 使用者類型：外部
8. 應用程式名稱：`litdb`
9. 使用者支援 email：你的 email
10. 儲存

#### 6.3 加入測試使用者
11. 左側 → 目標對象
12. 測試使用者 → + Add users
13. 輸入 `gogoyankee@gmail.com`
14. 儲存

#### 6.4 建立憑證
15. 左側 → 憑證 → + 建立憑證 → OAuth 用戶端 ID
16. 應用程式類型：網頁應用程式
17. 已授權的 JavaScript 來源：`https://chiuchangru.github.io`
18. 建立 → 複製用戶端 ID

### 目前設定

| 項目 | 值 |
|------|-----|
| Google Cloud 專案 | litdb |
| Client ID | `794566862514-jrcn9pkvc4brtt4dt8r3m3g6slsgl888.apps.googleusercontent.com` |
| 測試使用者 | gogoyankee@gmail.com |
| 已授權來源 | https://chiuchangru.github.io |

### 第一次登入注意
會看到「此應用程式未經 Google 驗證」警告，點 **繼續** 即可（測試模式正常現象）。

---

## 七、Pigtail 自動日報設定（已停用）

### 架構

```
GitHub Actions（每天 08:00 台灣時間）
  → search_agent.py（搜尋 PubMed + USPTO）
  → Claude Haiku 分析
  → 產生 reports/YYYY-MM-DD.md
  → git commit + push
```

### 啟用/停用

| 操作 | 步驟 |
|------|------|
| 停用 | Actions → Daily Literature Search → ⋯ → Disable workflow |
| 啟用 | Actions → Daily Literature Search → ⋯ → Enable workflow |
| 手動跑一次 | Actions → Daily Literature Search → Run workflow |

### 必要 Secret

| 名稱 | 位置 |
|------|------|
| ANTHROPIC_API_KEY | Pigtail → Settings → Secrets → Actions |

---

## 八、LitDB 功能速查

| 功能 | 需要 API？ | 費用 |
|------|-----------|------|
| 📚 文庫瀏覽/篩選 | ❌ | 免費 |
| 🕸 關係圖 | ❌ | 免費 |
| 🔥 缺口分析 | ❌ | 免費 |
| 🌳 引文樹 | ❌（Semantic Scholar） | 免費 |
| 🔎 PubMed 批次搜尋 | ❌ | 免費 |
| 🤖 AI 對話 | ✅ Claude API | ~$0.002/次 |
| 🤖 AI 自動填入 | ✅ Claude API | ~$0.001/篇 |
| 🌐 翻譯 | ✅ Claude API | ~$0.001/篇 |
| 🤖 AI 補標籤 | ✅ Claude API | ~$0.001/篇 |
| 📊 Google Sheets 同步 | ✅ Google OAuth | 免費 |
| 📎 書籤小工具 | ❌ | 免費 |

---

## 九、常見問題

### Q: Token 失效怎麼辦？
A: 到 `github.com/settings/tokens/new` 重新產生，貼給 Claude。

### Q: Google 登入被擋？
A: 確認 Google Cloud Console → 目標對象 → 測試使用者有你的 email。

### Q: API 餘額用完？
A: 到 `console.anthropic.com` 加值。LitDB 免 API 功能仍可使用。

### Q: 網頁更新後沒變化？
A: GitHub Pages 有快取，按 Ctrl+Shift+R 強制重整，或等 2-3 分鐘。

### Q: 如何新增其他人使用 LitDB？
A: Google Cloud → 目標對象 → + Add users 加入對方 email。

---

## 十、重要連結

| 服務 | 網址 |
|------|------|
| LitDB | https://chiuchangru.github.io/litdb/ |
| Pigtail | https://chiuchangru.github.io/Pigtail/ |
| MedQA | https://chiuchangru.github.io/DMAIC/ |
| GitHub 倉庫 | https://github.com/ChiuChangRu |
| GitHub Token 管理 | https://github.com/settings/tokens |
| Anthropic Console | https://console.anthropic.com |
| Google Cloud Console | https://console.cloud.google.com |
| Semantic Scholar | https://www.semanticscholar.org |
| PubMed | https://pubmed.ncbi.nlm.nih.gov |
