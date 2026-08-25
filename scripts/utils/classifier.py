#!/usr/bin/env python3
"""主题分类器 — 基于 taxonomy.md 的关键词规则匹配。"""
import re

TOPIC_KEYWORDS = {
    "corporate_governance": [
        "board of directors", "fiduciary duty", "shareholder", "executive compensation",
        "caremark", "delaware", "say-on-pay", "say on pay", "proxy access",
        "board independence", "shareholder activism", "shareholder proposal",
        "bylaw", "charter", "esg voting", "director", "proxy season",
        "investor", "stewardship", "corporate governance", "governance",
        "boardroom", "ceo", "chair", "independent director", "fiduciary",
        "shareholder vote", "annual meeting", "proxy statement",
        "institutional investor", "hedge fund", "activist",
        "compensation", "equity comp", "stock option",
        "信义义务", "董事会", "股东", "高管薪酬", "公司治理",
        "独立董事", "股东提案", "股东积极主义",
        "takeover", "merger", "acquisition", " Revlon",
        "duty of care", "duty of loyalty", "business judgment",
        "private equity", "leveraged buyout", "lbo",
        "controlling shareholder", "dual class", "sunset provision",
    ],
    "financial_regulation": [
        "sec", "securities", "disclosure", "registration", "prospectus",
        "10-k", "10-q", "form s-1", "form 8-k", "mutual fund",
        "investment adviser", "broker-dealer", "finra",
        "esg disclosure", "climate disclosure", "basel",
        "capital requirement", "banking", "bank regulation",
        "cftc", "fdic", "occ", "financial regulation",
        "prudential", "solvency", "market integrity",
        "issuer", "underwriting", "going public", "ipo",
        "derivatives", "securitization", "shadow banking",
        "stress test", "living will", "resolution",
        "crypto", "token", "digital asset",
        "stablecoin", "cbdc",
        "金融监管", "信息披露", "证券法", "注册发行", "投资者保护",
        "sec rule", "commission", "enforcement", "sanction",
        "antifraud", "antifraud", "material misstatement",
        "insider trading", "short swing", "schedule 13",
        "section 16", "regulation", "rule 10b", "rule 14a",
        "perril", "pma", "benefit corporation",
        "federal reserve", "fsb", "financial stability",
    ],
    "antitrust": [
        "antitrust", "competition", "merger control", "monopoly",
        "market power", "cartel", "price fixing", "sherman act",
        "clayton act", "ftc", "doj", "dg comp",
        "horizontal merger", "vertical merger", "killer acquisition",
        "market definition", "dominant position", "abuse of dominance",
        "exclusionary", "predatory", "tying", "refusal to deal",
        "反垄断", "经营者集中", "市场支配地位", "卡特尔",
        "antitrust", "competition law", "competition policy",
        "merger review", "hart-scott-rodino", "hsr",
        "consumer welfare", "bigness", "concentration",
        "platform monopoly", "self-preferencing", "gatekeeper",
        "dma", "dsa", "digital markets",
        "maverick", "coordinated effects", "unilateral effects",
    ],
    "tech_data_ai": [
        "artificial intelligence", "ai governance", "algorithm",
        "machine learning", "data protection", "gdpr", "privacy",
        "data breach", "cybersecurity", "cryptocurrency",
        "defi", "stablecoin", "platform regulation",
        "section 230", "dsa", "dma", "gatekeeper",
        "ai act", "algorithmic", "automated decision",
        "generative ai", "llm", "large language model",
        "data governance", "data portability",
        "人工智能", "算法", "隐私", "数据保护", "平台治理", "加密资产",
        "ai", "machine learning", "neural network",
        "cyber", "ransomware", "data security",
        "biometric", "facial recognition",
        "open source", "interoperability",
        "smart contract", "blockchain", "nft",
        "digital platform", "tech regulation",
    ],
}

TOPIC_PRIORITY = [
    "financial_regulation",
    "antitrust",
    "tech_data_ai",
    "corporate_governance",
]


def classify(title, abstract, keywords):
    """Classify article into 1-2 topics. Returns (topics, primary_topic)."""
    text = " ".join(filter(None, [title, abstract, " ".join(keywords or [])])).lower()

    scores = {}
    for topic, kws in TOPIC_KEYWORDS.items():
        score = 0
        for kw in kws:
            if kw in text:
                score += 1
        if score > 0:
            scores[topic] = score

    if not scores:
        return ["other"], "other"

    ranked = sorted(scores.items(), key=lambda x: (-x[1], TOPIC_PRIORITY.index(x[0]) if x[0] in TOPIC_PRIORITY else 99))

    topics = [t for t, _ in ranked[:2]]
    primary = topics[0]

    return topics, primary
