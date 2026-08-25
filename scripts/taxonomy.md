# 5 主题分类规约

> 本文件是自动化周报脚本在抓取新文章后分类时**必须**参考的准则。
> 修改本文件前请同步更新 `articles.json` 的 `topics` 数组、`index.html` 的内嵌 `topics` 数组、`scripts/update_db.py` 的 `VALID_TOPICS` 集合。

## 总原则

1. **多标签允许**：一篇文章可以同时属于 2 个主题（如 "ESG 强制披露" 同时是公司治理 + 金融监管）。
2. **必须设置 `primary_topic`**：从 `topics` 数组中选一个，作为该文章在筛选/排序时的主分类。
3. **不确定归 `other`**：宁可少标、不可错标。
4. **避免标签膨胀**：单篇文章最多 2 个 `topics`，通常 1 个就够。
5. **看标题+摘要**：分类依据是 title + abstract 的实质内容，而非来源机构（来源是 source_id 字段，不影响分类）。

## 五个主题

### 1. `corporate_governance` — 公司治理

**定义**：上市公司、有限责任公司、合伙企业、合作社等商业组织的内部治理结构与机制。

**典型议题**：
- 董事会结构、独立董事、董事会监督义务（Caremark 等）
- 股东权利（投票权、提案权、起诉权、books and records）
- 高管薪酬、薪酬投票（Say-on-Pay）
- 股东积极主义、对冲基金干预
- CEO/董事长分离、继任规划
- 章程/ bylaws、设立地竞争（Dexit、特拉华 vs 内华达）
- 信义义务（忠实义务、善意义务）
- ESG 投票与可持续治理
- 董事的声誉、适格性、利益冲突
- 国际体育组织、非营利组织、合作社的"类治理"问题

**判断口诀**：问"这事是关于公司/组织**内部**怎么决策、怎么被治理的吗？"

**典型关键词（中英）**：board of directors, fiduciary duty, shareholder proposal, executive compensation, Caremark, Delaware, Say-on-Pay, proxy access, ESG voting, board independence, 董事会, 信义义务, 高管薪酬, 股东提案, 股东积极主义

**反例**（归他类）：
- "SEC 规则变更影响董事会披露" → 优先 `financial_regulation`（规则本身）
- "AI 在董事会决策中的应用" → 同时 `tech_data_ai`（双标签）
- "FIFA 治理" → 归 `other`（不属于商事组织治理，跨学科但落脚在公司治理方法）— 实际可标 `corporate_governance` + `other`

---

### 2. `financial_regulation` — 金融监管

**定义**：监管机构对金融机构、资本市场、金融工具的规制。

**典型议题**：
- SEC、CFTC、FDIC、OCC 等机构的新规提案与意见
- 注册发行、披露义务（10-K, 10-Q, 8-K, S-1, S-3）
- 投资者保护、投资者适当性
- 共同基金、对冲基金、ETF 的规制
- 银行合并、资本充足率、巴塞尔协议
- 上市公司退市、转板
- ESG/可持续报告规则（CSRD、ISSB、SEC climate rule）
- 投资顾问 Pay-to-Play、broker-dealer 规则
- 电子交付、招股说明书电子化
- 跨境证券、合格司法辖区

**判断口诀**：问"这事是**监管者**在制定/执行什么**规则**，或**金融机构**在遵守什么**披露义务**？"

**典型关键词**：SEC, CFTC, FDIC, FINRA, disclosure, registration, prospectus, Form 10-K, Form S-1, mutual fund, investment adviser, pay-to-play, ESG disclosure, climate disclosure, Basel, capital requirement, 金融监管, 注册发行, 信息披露, 投资者保护

**反例**：
- "公司治理结构对 SEC 披露的影响" → 同时 `corporate_governance`（双标签）
- "证券欺诈的刑事责任" → 归 `financial_regulation`（证券执法）
- "央行数字货币（CBDC）的设计" → 同时 `tech_data_ai`（双标签）

---

### 3. `antitrust` — 反垄断

**定义**：竞争法、合并控制、市场支配地位滥用、卡特尔。

**典型议题**：
- 美国 FTC / DOJ 反垄断执法
- 欧盟 DG COMP 合并控制
- 经营者集中申报、附条件批准
- 市场界定、相关市场认定
- 滥用市场支配地位、纵向限制
- 卡特尔、串通投标、价格操纵
- 数字平台反垄断（Gatekeeper 理论、自优待）
- 反垄断经济学（动态竞争、创新市场）
- 国家安全审查（CFIUS）

**判断口诀**：问"这事是关于**市场竞争结构、合并、市场支配行为**的规制吗？"

**典型关键词**：merger, antitrust, competition, market definition, monopoly, cartel, Sherman Act, Clayton Act, DG COMP, horizontal merger, vertical merger, killer acquisition, 反垄断, 经营者集中, 市场支配地位, 卡特尔

**反例**：
- "银行合并的资本充足率" → 同时 `financial_regulation`（双标签，因为是金融监管合并审批）
- "并购中的股东保护" → 归 `corporate_governance`（从治理角度谈合并）

---

### 4. `tech_data_ai` — 科技、数据与AI

**定义**：人工智能、数据治理、平台/科技公司规制、隐私、网络安全、加密资产。

**典型议题**：
- AI 治理、AI 责任、算法歧视
- GDPR、CCPA、中国《个人信息保护法》
- 平台责任（Section 230、欧盟 DSA/DMA Gatekeeper 义务）
- 加密资产、DeFi、稳定币、央行数字货币（CBDC）
- 网络安全披露、勒索软件、数据泄露
- 自动化决策、人机协作的法律责任
- 知识产权与 AI 训练数据
- 算法定价、个性化定价的反垄断意义

**判断口诀**：问"这事**核心技术对象**是 AI、数据、算法、平台、加密资产、网络安全吗？"

**典型关键词**：artificial intelligence, AI governance, algorithm, machine learning, data protection, GDPR, privacy, data breach, cybersecurity, cryptocurrency, stablecoin, DeFi, platform regulation, Section 230, 人工智能, 算法, 隐私, 数据保护, 平台治理, 加密资产

**反例**：
- "AI 影响劳动就业" → 归 `tech_data_ai`（虽然有劳动法维度，但主题是 AI）
- "AI 在并购审查中的应用" → 同时 `antitrust`（双标签）

---

### 5. `other` — 其他

**定义**：不属于上述 4 类的商法/法律议题。

**典型议题**：
- 行政法（独立机构、规章审查、单一行政分支理论）
- 国际经贸法（CFIUS、出口管制、贸易制裁、关税）
- 劳动法、税法
- 刑法（白领犯罪、FCPA、反海外腐败）
- 宪法（行政分支、监管国家的合宪性问题）
- 跨学科研究（经济学与法律、历史与法律）
- 国际比较法
- 法律职业、法律教育
- 商事法一般理论
- 体育治理、宗教组织治理等"非公司"组织

**判断口诀**：当不属于前 4 类，或主题跨度太大无法聚焦时，标 `other`。

---

## 分类决策树（实操流程）

```
读 title + abstract
  │
  ├─ 提到具体监管规则（SEC、FDIC、CSRD、Basel…）？
  │   └─ 是 → financial_regulation
  │
  ├─ 提到合并、市场支配、卡特尔、反垄断执法？
  │   └─ 是 → antitrust
  │
  ├─ 提到 AI / 算法 / 隐私 / 数据 / 平台 / 加密？
  │   └─ 是 → tech_data_ai
  │
  ├─ 提到董事会 / 股东 / 高管薪酬 / 信义义务 / 公司章程？
  │   └─ 是 → corporate_governance
  │
  └─ 都不沾边 → other
```

## 复合标签的判定标准

只有当两个主题**都**是文章的主要议题时才双标签。例如：
- "ESG 强制披露对董事会的新要求" → 金融监管 + 公司治理 ✅（两个都是核心）
- "AI 辅助董事会决策" → 科技/数据/AI + 公司治理 ✅
- "AI 在并购预测中的应用" → 科技/数据/AI + 反垄断 ✅
- "AI 工具在公司法教育中的使用" → 科技/数据/AI + 其他 ✅
- "公司法领域的 AI 政策" → 主要还是 `tech_data_ai`，**不**双标签 `corporate_governance`

## 更新本规约的 checklist

修改主题分类时，必须同步：
- [ ] `database/articles.json` 中 `topics` 数组
- [ ] `index.html` 中 `<script id="db-data">` 块内的 `topics` 数组
- [ ] `scripts/update_db.py` 中 `VALID_TOPICS` 集合
- [ ] 本文件 `scripts/taxonomy.md`
- [ ] 历史文章的 topics 字段（用 scripts/retax.py 重新分类，如需要）
