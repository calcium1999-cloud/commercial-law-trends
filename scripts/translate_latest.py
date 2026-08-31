#!/usr/bin/env python3
"""Add Chinese translations and affiliations for the latest 10 articles."""
import json

DB_PATH = "database/articles.json"

translations = {
    "art_226": {
        "title_cn": "反觉醒公司治理",
        "abstract_cn": "在现代时期，公司法并未被视为特别具有党派色彩。这在一定程度上可能是因为特拉华州——作为公司法的主要制定州——已将非党派性纳入其公司法设计之中。然而，近年来德克萨斯州已开始积极与特拉华州争夺公司注册业务，其方式之一便是制定明显具有党派倾向的公司法规则。本文探讨了这一反觉醒公司治理运动的背景、发展及其对公司法领域的深远影响。",
        "affiliations": "Not stated",
    },
    "art_227": {
        "title_cn": "中国的利益相关者参与与ESG",
        "abstract_cn": "中国的国家主导型利益相关者模式能够产生真正的企业积极行动和ESG影响力，但其有效性依赖于强大的制度渠道，且仍易受到政治把关的影响。传统观点将中国的利益相关者参与视为形式主义，但本文认为实际情况更为复杂，中国独特的制度框架在特定条件下能够产生实质性的企业治理效果。",
        "affiliations": "Not stated",
    },
    "art_228": {
        "title_cn": "上市法案后漫长程序与信息披露时机",
        "abstract_cn": "上市法案（欧盟法规2024/2809）和欧盟委员会授权法规（欧盟2026/789）重新界定了欧盟资本市场法中争议最大的问题之一：发行人必须在何时披露在合并、授权程序或其他持续性过程中逐渐产生的内幕信息。本文分析了新法规对信息披露时机的要求及其对发行人合规义务的影响。",
        "affiliations": "Bocconi University",
    },
    "art_229": {
        "title_cn": "冷战时期美国军方如何以私营企业为模型",
        "abstract_cn": "A.J. Murphy是美国军事史、资本主义史以及性别与性史学者。其即将出版的著作《五角大楼资本主义：冷战时期美国军方如何以私营企业为模型》（哈佛大学出版社）叙述了冷战时期美国军方如何系统性地采用私营企业的管理理念和运营模式，将企业管理逻辑嵌入军事组织结构与战略规划之中。",
        "affiliations": "Not stated",
    },
    "art_230": {
        "title_cn": "为何私募市场基金对散户投资者具有危险性",
        "abstract_cn": "Ben Bates是哈佛大学法学院公司治理项目研究员。其研究聚焦于公司和证券法，运用实证方法研究公开市场和私募市场中投资者面临的风险。最新研究关注允许散户投资者接触私募市场资产的基金，分析了这类基金在流动性、估值和利益冲突方面对散户投资者构成的潜在风险。",
        "affiliations": "Harvard Law School Program on Corporate Governance",
    },
    "art_231": {
        "title_cn": "证券集体诉讼趋势：AI相关诉讼激增，指控损失与和解金额攀升",
        "abstract_cn": "Tijana Brien、Brett De Jarnette和Brian French是Cooley LLP合伙人。本文基于Cooley律所备忘录。两家领先咨询机构——Cornerstone Research和NERA——近期发布了2026年上半年证券集体诉讼起诉与和解报告。两份报告均指出起诉活动显著增加，投资者指控损失与和解金额大幅增长，其中AI相关诉讼成为推动增长的重要因素。",
        "affiliations": "Cooley LLP",
    },
    "art_232": {
        "title_cn": "关于SEC修订新兴成长公司便利待遇与申报人分类提案的意见函",
        "abstract_cn": "Maureen McNichols是斯坦福大学商学院Marriner S. Eccles会计与公共及私人管理教授。本文基于由多位教授、前监管者以及会计和审计从业者联名向美国证券交易委员会提交的意见函，针对SEC关于修订新兴成长公司便利待遇和申报人分类标准的提案，提出了系统性修改建议。",
        "affiliations": "Stanford Graduate School of Business",
    },
    "art_233": {
        "title_cn": "董事薪酬上涨，但领导岗位除外",
        "abstract_cn": "Matthew Vnuk是合伙人，Kyle White是高级经理，Cedrick Jean-Louis是高级分析师，均任职于Compensation Advisory Partners。本文基于CAP备忘录。每年CAP分析美国最大100家上市公司的非雇员董事薪酬方案，研究发现整体薪酬水平呈上升趋势，但领导岗位（如首席董事、审计委员会主席）的薪酬增幅相对较小。",
        "affiliations": "Compensation Advisory Partners",
    },
    "art_234": {
        "title_cn": "私募信贷中的养老基金受托人与审慎人标准",
        "abstract_cn": "随着私募信贷发展为主流资产类别，代表受益人管理养老基金投资组合的受托人面临不断演变的挑战。本文探讨了指导养老基金受托人在应对私募信贷市场中信息不对称和流动性风险时的审慎人标准，分析了受托人在投资决策中应遵循的法律义务与最佳实践。",
        "affiliations": "Columbia Law School",
    },
    "art_235": {
        "title_cn": "挑战银行监管机构检查结果",
        "abstract_cn": "作为监管格局更广泛转变的一部分，联邦银行监管机构正致力于使检查更加客观并聚焦于财务层面。例如，联邦金融机构检查委员会（FFIEC）近期发布了拟议规则制定通知，将修订评估体系。本文分析了银行机构对检查结果提出异议的法律途径与实务策略。",
        "affiliations": "Columbia Law School",
    },
}

# Fix data quality issues
fixes = {
    "art_227": {"authors": "Tianxiang He, Lin Lin"},
    "art_228": {"title": "Protracted Processes and the Timing of Disclosure After the Listing Act", "authors": "Filippo Annunziata"},
}

with open(DB_PATH, "r", encoding="utf-8") as f:
    db = json.load(f)

articles = db.get("articles", [])
updated = 0
for art in articles:
    aid = art.get("id", "")
    if aid in translations:
        t = translations[aid]
        if t.get("title_cn"):
            art["title_cn"] = t["title_cn"]
        if t.get("abstract_cn"):
            art["abstract_cn"] = t["abstract_cn"]
        if t.get("affiliations"):
            art["affiliations"] = t["affiliations"]
        updated += 1
    if aid in fixes:
        f = fixes[aid]
        if f.get("title"):
            art["title"] = f["title"]
        if f.get("authors"):
            art["authors"] = f["authors"]

with open(DB_PATH, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print(f"Updated {updated} articles")

# Verify
last10 = articles[-10:]
na_title = sum(1 for a in last10 if not a.get("title_cn"))
na_abstract = sum(1 for a in last10 if not a.get("abstract_cn"))
na_affil = sum(1 for a in last10 if not a.get("affiliations") or a.get("affiliations") == "Not stated")
print(f"Missing title_cn: {na_title}")
print(f"Missing abstract_cn: {na_abstract}")
print(f"Not stated affiliations: {na_affil}")
for a in last10:
    print(f"  {a['id']} | {a.get('title_cn','NONE')[:30]} | affil: {a.get('affiliations','NONE')[:30]}")
