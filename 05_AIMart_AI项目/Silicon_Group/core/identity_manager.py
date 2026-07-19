"""
🎭 影子特工处 (Identity Manager) — L1 特权监军机关

职责:
  1. 管理数字身份池（多平台多语言身份）
  2. 代理 IP 轮换策略
  3. 浏览器指纹模拟配置
  4. 身份使用记录与健康度追踪
  5. 为宣发军提供身份掩护

设计原则:
  - 完全独立模块，不修改任何现有代码
  - 所有身份数据存储在 config/identities/ 目录
  - 支持动态添加/删除身份
"""
import os
import json
import random
from datetime import datetime
from core.battle_log import write_log

IDENTITIES_DIR = "config/identities"


def ensure_identities_dir():
    if not os.path.exists(IDENTITIES_DIR):
        os.makedirs(IDENTITIES_DIR)


DEFAULT_IDENTITIES = {
    "twitter": [
        {"name": "TechInvestor_AI", "lang": "en", "bio": "AI & Crypto enthusiast. Algorithmic trader.", "region": "us"},
        {"name": "CryptoNinja_22", "lang": "en", "bio": "Trading since 2017. Sharing alpha.", "region": "sg"},
        {"name": "デジタル戦士", "lang": "ja", "bio": "AIエージェントで自動取引。", "region": "jp"},
    ],
    "reddit": [
        {"name": "u/algotrader_ai", "lang": "en", "bio": "Building AI trading agents", "region": "us"},
        {"name": "u/quant_pioneer", "lang": "en", "bio": "Quant researcher. ML enthusiast.", "region": "uk"},
    ],
    "telegram": [
        {"name": "AlphaSignal_Bot", "lang": "en", "bio": "Automated trading signals", "region": "us"},
        {"name": "CryptoPulse_AI", "lang": "en", "bio": "Real-time market analysis", "region": "hk"},
    ],
}


def _get_identities_file() -> str:
    """获取身份数据文件路径"""
    ensure_identities_dir()
    return f"{IDENTITIES_DIR}/identities.json"


def load_identities() -> dict:
    """加载所有身份"""
    filepath = _get_identities_file()
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_identities(identities: dict):
    """保存身份数据"""
    filepath = _get_identities_file()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(identities, f, indent=2, ensure_ascii=False)


def init_default_identities():
    """初始化默认身份池"""
    identities = load_identities()
    if not identities:
        save_identities(DEFAULT_IDENTITIES)
        return DEFAULT_IDENTITIES
    return identities


def get_identity(platform: str, lang: str = "en") -> dict:
    """获取指定平台和语言的身份

    如果指定语言的身份不可用，返回该平台第一个可用身份。
    """
    identities = load_identities()
    platform_identities = identities.get(platform, [])

    if not platform_identities:
        return {"name": "anonymous", "lang": lang, "bio": "", "region": "unknown"}

    lang_matches = [i for i in platform_identities if i.get("lang") == lang]
    if lang_matches:
        return random.choice(lang_matches)

    return random.choice(platform_identities)


def rotate_identity(platform: str, current_name: str = None) -> dict:
    """轮换身份 — 返回与当前不同的身份"""
    identities = load_identities()
    platform_identities = identities.get(platform, [])

    if len(platform_identities) <= 1:
        return get_identity(platform)

    candidates = [i for i in platform_identities if i.get("name") != current_name]
    return random.choice(candidates) if candidates else platform_identities[0]


def add_identity(platform: str, name: str, lang: str, bio: str, region: str = "us"):
    """添加新身份"""
    identities = load_identities()
    if platform not in identities:
        identities[platform] = []

    identities[platform].append({
        "name": name,
        "lang": lang,
        "bio": bio,
        "region": region,
    })
    save_identities(identities)
    return {"name": name, "lang": lang, "bio": bio, "region": region}


def remove_identity(platform: str, name: str) -> bool:
    """删除指定身份"""
    identities = load_identities()
    if platform not in identities:
        return False

    original_count = len(identities[platform])
    identities[platform] = [i for i in identities[platform] if i.get("name") != name]

    if len(identities[platform]) < original_count:
        save_identities(identities)
        return True
    return False


def get_identity_health() -> dict:
    """获取身份池健康度"""
    identities = load_identities()
    total = 0
    platform_stats = {}

    for platform, ids in identities.items():
        count = len(ids)
        total += count
        platform_stats[platform] = {
            "count": count,
            "names": [i.get("name") for i in ids],
            "languages": list(set(i.get("lang", "en") for i in ids)),
        }

    return {
        "total_identities": total,
        "platforms": len(identities),
        "platform_stats": platform_stats,
        "status": "healthy" if total >= 5 else "low",
    }


def generate_fingerprint(platform: str) -> dict:
    """生成模拟浏览器指纹配置

    为影子身份提供技术掩护，模拟真实用户行为。
    """
    user_agents = {
        "twitter": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
        ],
        "reddit": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        ],
        "telegram": [
            "TelegramBot (like TwitterBot)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        ],
    }

    timezones = ["America/New_York", "Asia/Singapore", "Asia/Tokyo", "Europe/London", "Australia/Sydney"]
    languages = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "ja-JP,ja;q=0.9,en;q=0.6"]
    screen_resolutions = ["1920x1080", "1440x900", "1366x768", "2560x1440"]

    return {
        "platform": platform,
        "user_agent": random.choice(user_agents.get(platform, user_agents["twitter"])),
        "timezone": random.choice(timezones),
        "language": random.choice(languages),
        "screen_resolution": random.choice(screen_resolutions),
        "cookies_enabled": True,
        "do_not_track": random.choice([True, False]),
    }


def use_identity(session_id: str, platform: str, lang: str = "en") -> dict:
    """使用一个身份并记录使用日志

    这是影子特工处的核心接口：为宣发军提供身份掩护。
    """
    identity = get_identity(platform, lang)
    fingerprint = generate_fingerprint(platform)

    usage_record = {
        "time": datetime.now().isoformat(),
        "platform": platform,
        "identity": identity,
        "fingerprint": fingerprint,
    }

    write_log(session_id, "IDENTITY_USED", platform, f"使用身份: {identity['name']} ({lang}) on {platform}")

    return usage_record


def get_identity_status() -> dict:
    """获取影子特工处状态"""
    health = get_identity_health()
    return {
        "total_identities": health["total_identities"],
        "platforms": health["platforms"],
        "status": health["status"],
        "platform_stats": health["platform_stats"],
    }
