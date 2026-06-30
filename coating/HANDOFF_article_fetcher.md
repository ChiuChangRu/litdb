# Article Fetcher 交接文件
> 任務：為 LitDB 的 48 篇文獻（非專利/商用）批量 fetch 原文 abstract，AI 解析出實驗組（experiments）和技術路線（technology_map），寫入 article.json

---

## 背景說明

### 為什麼要做這個？

`papers.json` 是 LitDB 的主資料庫，每篇文獻有 `patentResults.full.examples[]`，但文獻類（期刊/綜述）的 examples 品質極差：
- 每篇幾乎只有 1 個 example
- COF/WCA 數值多數是「未報告」「具體值見原文」
- AI 報告引擎拿到這些資料，只能輸出「效果顯著」之類的廢話

**解決方案**：建立獨立的 `article.json`，透過 fetch 原文 → AI 解析，把每篇文獻的實驗組（每個實驗條件一筆）拆開存入，讓報告引擎有具體數值可用。

### 兩個 JSON 的關係

```
papers.json          ← 主資料庫（不要改動）
  └─ id: "G08"       ← 用 id 關聯
  └─ title, doi...
  └─ abstract_note   ← 使用者手寫筆記，有些含數值，可作為 fetch fallback

article.json         ← 解析結果庫（這次要填的）
  └─ id: "G08"       ← 同一個 id
  └─ fetch_url       ← 已填好
  └─ raw_abstract    ← fetch 後填入
  └─ experiments[]   ← AI 解析後填入（實驗型論文用）
  └─ technology_map[]← AI 解析後填入（review/綜述用）
```

**兩個 JSON 以 `id` 為唯一 key 關聯，不會錯位。**

---

## 檔案清單

| 檔案 | 說明 |
|------|------|
| `papers.json` | 主資料庫，102 篇（含專利43、期刊33、綜述13、商用11、會議1、市場1）|
| `article.json` | 待填入的解析結果庫，48 篇文獻（非專利/商用），全部 fetch_status: "pending" |
| `article-fetcher.html` | 批量 fetch + AI 解析工具（瀏覽器執行）|

---

## article.json Schema

每篇結構如下：

```json
{
  "id": "G08",
  "doc_type": "期刊論文",
  "title": "Quaternized chitosan-functionalized catheter...",
  "year": 2025,
  "fetch_url": "https://doi.org/10.1080/09205063.2025.2574946",
  "fetch_type": "doi",
  "fetch_status": "pending",   // pending | fetching | parsing | done | failed | skipped
  "fetched_at": "",
  "raw_abstract": "",          // fetch 後填入：原文 abstract 純文字
  "paper_type": "",            // AI 填入：experimental | review | market
  "main_finding": "",          // AI 填入：一句話核心結論（中文，60字內）
  "review_scope": "",          // review 專用：涵蓋範圍
  "technology_map": [],        // review 專用：技術路線列表（見下方結構）
  "experiments": []            // 實驗論文專用：實驗組列表（見下方結構）
}
```

### experiments[] 每項結構（實驗型期刊論文）

```json
{
  "name": "實驗組名稱（材料+基材，如：QCS/SBMA UV，TPU導管）",
  "is_control": false,         // true = 對照組
  "substrate": "TPU/PU/silicone/導管/支架/通用",
  "primer": "底塗（成分+wt%），null if none",
  "topcoat": "面塗（成分+wt%），null if none",
  "crosslinker": "交聯劑，null if none",
  "photoinitiator": "光起始劑，null if none",
  "curing": "固化條件，null if none",
  "wca": "WCA 數值（如 7.4°），null if none",
  "cof": "COF 數值（如 0.16），null if none",
  "adhesion": "附著力（如 Grade 0），null if none",
  "durability": "耐久測試，null if none",
  "antibacterial": "抗菌結果（如 E.coli 抑制 98%），null if none",
  "antifouling": "抗汙/抗結痂結果，null if none",
  "other_results": "其他結果，null if none",
  "notes": "補充說明，null if none"
}
```

### technology_map[] 每項結構（綜述 review）

```json
{
  "route": "技術路線名稱（如：SBMA zwitterionic UV接枝）",
  "materials": ["SBMA", "PEGDA"],
  "mechanism": "作用機制（中文），null if unknown",
  "substrate": "適用基材，null if not specified",
  "representative_formula": "代表性配方（成分+wt%），null if not specified",
  "wca": "代表性 WCA，null if not reported",
  "cof": "代表性 COF，null if not reported",
  "antibacterial": "抗菌效果，null if not reported",
  "antifouling": "抗汙/抗結痂效果，null if not reported",
  "durability": "耐久性描述，null if not reported",
  "advantages": "優點（中文），null if not stated",
  "limitations": "缺點/限制（中文），null if not stated",
  "refs_in_paper": "原文引用的代表文獻，null if not extractable",
  "notes": "補充說明，null if none"
}
```

---

## Fetch 策略（依 fetch_type）

| fetch_type | 篇數 | 策略 | CORS |
|-----------|------|------|------|
| doi (doi_direct) | 18 | CrossRef API: `https://api.crossref.org/works/{DOI}` | ✓ |
| pubmed (pubmed_direct) | 7 | PubMed efetch: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={PMID}&rettype=abstract&retmode=text` | ✓ |
| pmc | 4 | PMC efetch: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={PMCID}&rettype=abstract&retmode=text` | ✓ |
| fulltext / article / blog / ref | 9 | 直接 fetch URL，抽 abstract 段落 | ✓ 多數可以 |
| page (ScienceDirect abs) | 5 | CrossRef by PII: `https://api.crossref.org/works?query.bibliographic={PII}&rows=1` | ✓ |
| scholar | 1 | Google Scholar 封鎖，fallback 到 abstract_note | ✗ |
| pdf | 1 | PDF 通常被擋，fallback 到 abstract_note | ✗ |
| none | 1 | 無來源，跳過（fetch_status: skipped） | — |

**預計成功率：40/47 篇取到原文，7 篇 fallback 用 abstract_note**

---

## AI 解析 System Prompts

### 實驗型論文（experimental）

```
你是醫療塗層技術的文獻解析專家。
任務：閱讀實驗型論文的摘要或全文，將實驗內容拆解為結構化陣列。

拆解原則：
1. 每個獨立實驗條件（不同材料組合、濃度、製程、對照組）= 一個 experiment
2. 對照組必須列出（is_control: true）
3. 數值要具體：「COF 0.16」不是「低摩擦」；「WCA 7.4°」不是「親水性佳」
4. 若數值因條件不同而有範圍（如 COF 0.12–0.22 依分子量），寫範圍 + notes 說明
5. 若測試多種基材，每種基材分開列
6. 沒有的欄位填 null

只輸出 JSON（不要 markdown 或說明）
[schema 見上方 experiments[] 結構]
```

### 綜述/Review

```
你是醫療塗層技術的文獻解析專家。
任務：閱讀 review/綜述 文章，整理出文章中涵蓋的所有技術路線與配方。

重點：review 彙整多篇研究，每條技術路線可能有多個配方變體。
把每條路線/方法整理成獨立條目，包含代表性配方、性能數值、優缺點。

只輸出 JSON（不要 markdown 或說明）
[schema 見上方 technology_map[] 結構]
```

### 市場報告

```
你是醫療器材產業分析專家。
任務：閱讀市場報告或產業分析，整理關鍵市場數據和技術趨勢。
用 technology_map[] 格式輸出（route = 技術類別或市場區隔）
```

---

## Claude API 呼叫格式

使用 Sonnet 4.6，proxy 為 Cloudflare Worker：

```javascript
const response = await fetch(PROXY_URL, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'claude-sonnet-4-6',
    max_tokens: 3000,
    system: SYSTEM_PROMPT,     // 依 doc_type 選擇上方三種之一
    messages: [{
      role: 'user',
      content: `請解析以下文獻，依格式輸出 JSON：

ID: ${article.id}
標題: ${article.title}
類型: ${article.doc_type}
年份: ${article.year}

摘要筆記（可能含關鍵數值）:
${papers_map[article.id]?.abstract_note || ''}

原文摘要/全文片段:
${article.raw_abstract || ''}`
    }]
  })
});

const data = await response.json();
let text = data.content[0].text;
text = text.replace(/^```json\s*/i, '').replace(/```\s*$/i, '').trim();
const parsed = JSON.parse(text);
```

---

## 執行流程

```
for each article in article.json where fetch_status === 'pending':
  1. fetch raw_abstract（依 fetch_type 選策略，失敗 fallback 到 abstract_note）
  2. 依 doc_type 選 system prompt（experimental / review / market）
  3. 呼叫 Claude API 解析
  4. 依 paper_type 填入 experiments[] 或 technology_map[]
  5. 更新 fetch_status = 'done'（或 'failed'）
  6. 立即存檔（每篇跑完就存，避免中斷損失）
  7. 等待 1.5 秒再跑下一篇
```

---

## 注意事項

1. **每篇跑完立即存檔**，不要等全部跑完才存，避免中斷損失
2. **失敗篇目** fetch_status 設為 `failed`，記錄 error 訊息，之後可單獨重跑
3. **COF/WCA 數值務必具體**，不接受「顯著降低」「較低」這類模糊描述
4. **對照組（control group）必須列出**，is_control: true，這樣才能做比較
5. **review 篇的 technology_map** 要拆出每條技術路線，不要只寫一條「總結」
6. **abstract_note 可作為補充**，當原文 fetch 失敗時，abstract_note 通常含使用者手寫的關鍵數值
7. **null vs 空字串**：沒有資料的欄位填 null，不要填 "" 或 "未報告"

---

## 驗收標準

跑完後請確認：
- [ ] 48 篇中至少 40 篇 fetch_status = 'done'
- [ ] 每篇 experiments[] 或 technology_map[] 至少有 1 筆（非空陣列）
- [ ] 有對照組的實驗論文，experiments[] 包含 is_control: true 的項目
- [ ] review 篇（綜述）的 technology_map[] 至少有 2 條技術路線
- [ ] COF/WCA 數值是具體數字（如 0.16、7.4°），不是文字描述

---

## 後續整合

跑完後回傳 article.json，整合方式：

```javascript
// LitDB 報告引擎讀取方式
const articleMap = Object.fromEntries(articleData.articles.map(a => [a.id, a]));

// 取某篇的解析結果
const enriched = (paperId) => ({
  ...papersMap[paperId],           // papers.json 原始資料
  ...articleMap[paperId]           // article.json 解析結果
});
```

---

*文件產生日期：2026-06-30*
*對應 LitDB 版本：papers.json meta.version 2.0，article.json meta.version 2.0*
