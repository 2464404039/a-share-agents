"""
A-share (Chinese stock) data provider.
Multi-source: Tencent (PE/PB/市值/行情), Sina (K线), baostock (财报), Eastmoney (新闻).
Thread-safe (all HTTP, no shared state).
"""
import logging
import os
import random
import re
import threading
import time
import urllib.request
from typing import Optional

import pandas as pd
import requests

from src.data.models import (
    CompanyNews,
    FinancialMetrics,
    InsiderTrade,
    Price,
)

logger = logging.getLogger(__name__)

_A_SHARE_RE = re.compile(r"^\d{6}\.(SZ|SS|SH|BJ)$", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_a_stock(ticker: str) -> bool:
    return bool(_A_SHARE_RE.match(ticker.strip().upper()))

def _parse(ticker: str) -> tuple[str, str]:
    t = ticker.strip().upper()
    return t.split(".")

def _pure_code(ticker: str) -> str:
    """Extract 6-digit code from 688008.SS → 688008"""
    sym, _ = _parse(ticker)
    return sym

def _market_prefix(code: str) -> str:
    """6-digit code → sh/sz prefix for Tencent/Sina"""
    if code.startswith(("6", "9")):
        return "sh"
    return "sz"

def _f(v) -> Optional[float]:
    if v is None or v == "" or v == "--" or str(v).strip() == "":
        return None
    try:
        return float(str(v).strip().replace(",", ""))
    except (ValueError, TypeError):
        return None

# ---------------------------------------------------------------------------
# 东财防封限流 (Eastmoney anti-ban throttle)
# ---------------------------------------------------------------------------
_EM_SESSION = requests.Session()
_EM_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})
# Bypass any system proxy that may be configured
_EM_SESSION.trust_env = False
_EM_SESSION.proxies = {"http": "", "https": ""}
_EM_MIN_INTERVAL = float(os.environ.get("EM_MIN_INTERVAL", "1.0"))
_em_last_call: list[float] = [0.0]
_em_lock = threading.Lock()

def _em_get(url: str, params=None, headers=None, timeout=15, **kwargs):
    """东财统一请求入口：串行限流 + 复用Session + 随机抖动."""
    with _em_lock:
        wait = _EM_MIN_INTERVAL - (time.time() - _em_last_call[0])
        if wait > 0:
            time.sleep(wait + random.uniform(0.1, 0.3))
        try:
            return _EM_SESSION.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
        finally:
            _em_last_call[0] = time.time()

# ---------------------------------------------------------------------------
# 1. TENCENT 实时行情 (PE/PB/市值/价格) — 最稳定
# ---------------------------------------------------------------------------

_TENCENT_CACHE: dict[str, dict] = {}
_TENCENT_CACHE_TIME: dict[str, float] = {}
_TENCENT_CACHE_LOCK = threading.Lock()

def _tencent_quote_single(ticker: str) -> dict | None:
    """从腾讯qt.gtimg.cn获取单只A股实时行情.
    
    Returns dict with: name, price, pe_ttm, pe_static, pb, mcap_yi, float_mcap_yi,
                      turnover_pct, change_pct, high, low, open, last_close
    """
    code = _pure_code(ticker)
    prefix = _market_prefix(code)
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        # Bypass system proxy
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        resp = opener.open(req, timeout=10)
        raw = resp.read().decode("gbk")
        
        if '"' not in raw:
            return None
        
        vals = raw.split('"')[1].split("~")
        if len(vals) < 53:
            return None
        
        return {
            "name": vals[1],
            "price": float(vals[3]) if vals[3] else 0,
            "last_close": float(vals[4]) if vals[4] else 0,
            "pe_ttm": float(vals[39]) if vals[39] else 0,
            "pe_static": float(vals[52]) if vals[52] else 0,
            "pb": float(vals[46]) if vals[46] else 0,
            "mcap_yi": float(vals[44]) if vals[44] else 0,
            "float_mcap_yi": float(vals[45]) if vals[45] else 0,
            "turnover_pct": float(vals[38]) if vals[38] else 0,
            "change_pct": float(vals[32]) if vals[32] else 0,
            "high": float(vals[33]) if vals[33] else 0,
            "low": float(vals[34]) if vals[34] else 0,
            "open": float(vals[5]) if vals[5] else 0,
        }
    except Exception as e:
        logger.warning("Tencent quote failed for %s: %s", ticker, e)
        return None


def _tencent_quote(ticker: str, max_age: int = 30) -> dict | None:
    """带缓存的腾讯行情接口（30秒内不重复请求）."""
    now = time.time()
    with _TENCENT_CACHE_LOCK:
        if ticker in _TENCENT_CACHE and now - _TENCENT_CACHE_TIME.get(ticker, 0) < max_age:
            return _TENCENT_CACHE[ticker]
    
    result = _tencent_quote_single(ticker)
    if result:
        with _TENCENT_CACHE_LOCK:
            _TENCENT_CACHE[ticker] = result
            _TENCENT_CACHE_TIME[ticker] = now
    return result

# ---------------------------------------------------------------------------
# 2. Sina HTTP K线 (OHLCV) — 备用价格源
# ---------------------------------------------------------------------------

def _sina_kline(code: str, start_date: str, end_date: str) -> list[Price]:
    """从新浪HTTP获取K线数据."""
    prefix = _market_prefix(code)
    url = ("http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           "CN_MarketData.getKLineData")
    params = {"symbol": f"{prefix}{code}", "scale": "240", "ma": "no", "datalen": "800"}
    
    try:
        r = requests.get(url, params=params, timeout=15, proxies={"http": "", "https": ""})
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("Sina kline failed for %s: %s", code, e)
        return []
    
    if not data:
        return []
    
    prices = []
    for item in data:
        d = item.get("day", "")
        if start_date and d < start_date.replace("-", ""):
            continue
        if end_date and d > end_date.replace("-", ""):
            continue
        try:
            prices.append(Price(
                open=float(item["open"]), close=float(item["close"]),
                high=float(item["high"]), low=float(item["low"]),
                volume=int(item["volume"]), time=d,
            ))
        except (ValueError, KeyError):
            continue
    prices.sort(key=lambda p: p.time)
    return prices


# ---------------------------------------------------------------------------
# 3. 东财 PUSH2 K线 (OHLCV) — 主价格源
# ---------------------------------------------------------------------------

def _eastmoney_kline(code: str, exchange: str, start_date: str, end_date: str) -> list[Price]:
    """从东财push2his获取K线数据."""
    sid = f"0.{code}" if exchange in ("SZ", "BJ") else f"1.{code}"
    beg = start_date.replace("-", "")
    end = end_date.replace("-", "")
    
    url = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
           f"?secid={sid}&fields1=f1,f2,f3,f4,f5,f6"
           f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116"
           f"&klt=101&fqt=1&beg={beg}&end={end}")
    
    try:
        r = _em_get(url, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception as e:
        logger.warning("Eastmoney kline failed for %s: %s", code, e)
        return []
    
    if not data or not data.get("data") or not data["data"].get("klines"):
        return []
    
    prices = []
    for line in data["data"]["klines"]:
        cols = line.split(",")
        if len(cols) < 6:
            continue
        try:
            prices.append(Price(
                open=float(cols[1]), close=float(cols[2]),
                high=float(cols[3]), low=float(cols[4]),
                volume=int(float(cols[5])), time=cols[0],
            ))
        except (ValueError, IndexError):
            continue
    prices.sort(key=lambda p: p.time)
    return prices


# ---------------------------------------------------------------------------
# 4. Baostock 财务指标 (thread-safe singleton)
# ---------------------------------------------------------------------------

import baostock as bs
_bs_logged_in = False
_bs_lock = threading.Lock()
_bs_login_time = 0.0


def _ensure_login():
    """每5秒内重新登录（防线程迁移导致socket失效）"""
    global _bs_logged_in, _bs_login_time
    now = time.time()
    with _bs_lock:
        if _bs_logged_in and now - _bs_login_time < 5:
            return
        if _bs_logged_in:
            try:
                bs.logout()
            except Exception:
                pass
            _bs_logged_in = False
        lg = bs.login()
        if lg.error_code != "0":
            raise RuntimeError("baostock login failed")
        _bs_logged_in = True
        _bs_login_time = now


def _bs_q(func, *args, **kwargs):
    """线程安全baostock查询 — 登录+查询+预取 在锁内一次性完成."""
    with _bs_lock:
        # 每次查询都重新登录（防uvicorn多线程socket迁移）
        global _bs_logged_in
        if _bs_logged_in:
            try:
                bs.logout()
            except Exception:
                pass
            _bs_logged_in = False
        lg = bs.login()
        if lg.error_code != "0":
            return "error", [], []
        _bs_logged_in = True
        
        rs = func(*args, **kwargs)
        rows = []
        fields = rs.fields if hasattr(rs, 'fields') else []
        if rs.error_code == "0":
            while rs.next():
                rows.append(rs.get_row_data())
        return rs.error_code, fields, rows


def _latest_fiscal_year(end_date: str) -> int:
    return int(end_date[:4]) - 1


# Cache for financial metrics
_FIN_CACHE: dict[str, list[FinancialMetrics]] = {}
_CACHE_LOCK = threading.Lock()

# ========== PUBLIC API ==========

# -- Price --
_PRICE_CACHE: dict[str, list[Price]] = {}

def get_prices(ticker: str, start_date: str, end_date: str, api_key=None) -> list[Price]:
    """多源获取A股价格：东财 → Sina → baostock."""
    ck = f"p_{ticker}_{start_date}_{end_date}"
    with _CACHE_LOCK:
        if ck in _PRICE_CACHE:
            return _PRICE_CACHE[ck]
    
    code, exchange = _parse(ticker)
    
    # 1. Eastmoney primary
    prices = _eastmoney_kline(code, exchange, start_date, end_date)
    
    # 2. Sina fallback
    if not prices:
        logger.info("Eastmoney empty, trying Sina for %s", ticker)
        prices = _sina_kline(code, start_date, end_date)
    
    # 3. Baostock fallback
    if not prices:
        logger.info("Sina empty, trying baostock for %s", ticker)
        try:
            bs_code = f"{'sh' if exchange in ('SS','SH') else 'sz'}.{code}"
            ec, fields, rows = _bs_q(
                bs.query_history_k_data_plus,
                bs_code, "date,open,high,low,close,volume",
                start_date=start_date, end_date=end_date, frequency="d", adjustflag="2",
            )
            if ec == "0":
                for row in rows:
                    try:
                        prices.append(Price(open=float(row[1]), close=float(row[4]),
                                            high=float(row[2]), low=float(row[3]),
                                            volume=int(float(row[5])), time=row[0]))
                    except (ValueError, IndexError):
                        continue
                prices.sort(key=lambda p: p.time)
        except Exception as e:
            logger.warning("baostock prices failed for %s: %s", ticker, e)
    
    with _CACHE_LOCK:
        _PRICE_CACHE[ck] = prices
    return prices


# -- Financial Metrics --
def get_financial_metrics(ticker: str, end_date: str, period="ttm", limit=10, api_key=None) -> list[FinancialMetrics]:
    ck = f"f_{ticker}_{end_date}"
    with _CACHE_LOCK:
        if ck in _FIN_CACHE:
            return _FIN_CACHE[ck]
    
    code, exchange = _parse(ticker)
    year = _latest_fiscal_year(end_date)
    
    m = FinancialMetrics(
        ticker=ticker, report_period=end_date, period=period, currency="CNY",
        market_cap=None, enterprise_value=None,
        price_to_earnings_ratio=None, price_to_book_ratio=None,
        price_to_sales_ratio=None, enterprise_value_to_ebitda_ratio=None,
        enterprise_value_to_revenue_ratio=None, free_cash_flow_yield=None,
        peg_ratio=None, gross_margin=None, operating_margin=None,
        net_margin=None, return_on_equity=None, return_on_assets=None,
        return_on_invested_capital=None, asset_turnover=None,
        inventory_turnover=None, receivables_turnover=None,
        days_sales_outstanding=None, operating_cycle=None,
        working_capital_turnover=None, current_ratio=None, quick_ratio=None,
        cash_ratio=None, operating_cash_flow_ratio=None,
        debt_to_equity=None, debt_to_assets=None, interest_coverage=None,
        revenue_growth=None, earnings_growth=None, book_value_growth=None,
        earnings_per_share_growth=None, free_cash_flow_growth=None,
        operating_income_growth=None, ebitda_growth=None, payout_ratio=None,
        earnings_per_share=None, book_value_per_share=None,
        free_cash_flow_per_share=None,
    )
    
    # --- (A) Tencent: real-time PE/PB/MCAP ---
    tq = _tencent_quote(ticker)
    price = 0
    if tq:
        m.price_to_earnings_ratio = tq.get("pe_ttm") or None
        if m.price_to_earnings_ratio and m.price_to_earnings_ratio == 0:
            m.price_to_earnings_ratio = None
        m.price_to_book_ratio = tq.get("pb") or None
        if m.price_to_book_ratio and m.price_to_book_ratio == 0:
            m.price_to_book_ratio = None
        mcap_yi = tq.get("mcap_yi", 0)
        if mcap_yi and mcap_yi > 0:
            m.market_cap = mcap_yi * 100000000
        price = tq.get("price", 0)
    
    # --- (B) Baostock: full financial data ---
    bs_code = f"{'sh' if exchange in ('SS','SH') else 'sz'}.{code}"
    try:
        _ensure_login()
        
        # ---- Profit indicators (latest year) ----
        ec, fields, rows = _bs_q(bs.query_profit_data, bs_code, year=year, quarter=4)
        if ec == "0" and rows:
            row = dict(zip(fields, rows[0]))
            m.return_on_equity = _f(row.get("roeAvg"))
            m.net_margin = _f(row.get("npMargin"))
            m.gross_margin = _f(row.get("gpMargin"))
            m.earnings_per_share = _f(row.get("epsTTM"))
            net_profit = _f(row.get("netProfit"))
            revenue = _f(row.get("MBRevenue"))
            
            # Calculate P/S ratio if price and revenue available
            shares = _f(row.get("totalShare"))
            if price and price > 0 and revenue and revenue > 0 and shares and shares > 0:
                m.price_to_sales_ratio = round((price * shares) / revenue, 2)
        else:
            net_profit = None
            revenue = None
        
        # ---- Profit: prior year for growth rates ----
        ec2, fields2, rows2 = _bs_q(bs.query_profit_data, bs_code, year=year - 1, quarter=4)
        if ec2 == "0" and rows2:
            prev = dict(zip(fields2, rows2[0]))
            prev_eps = _f(prev.get("epsTTM"))
            prev_np = _f(prev.get("netProfit"))
            prev_rev = _f(prev.get("MBRevenue"))
            
            if prev_eps and m.earnings_per_share:
                m.earnings_per_share_growth = round((m.earnings_per_share / prev_eps - 1), 4)
            if prev_np and net_profit:
                m.earnings_growth = round((net_profit / prev_np - 1), 4)
            if prev_rev and revenue:
                m.revenue_growth = round((revenue / prev_rev - 1), 4)
        
        # ---- Growth data ----
        ec, fields, rows = _bs_q(bs.query_growth_data, bs_code, year=year, quarter=4)
        if ec == "0" and rows:
            row = dict(zip(fields, rows[0]))
            if not m.revenue_growth:
                m.revenue_growth = _f(row.get("YOYEquity"))
            if not m.earnings_growth:
                m.earnings_growth = _f(row.get("YOYNI"))
        
        # ---- Balance data ----
        ec, fields, rows = _bs_q(bs.query_balance_data, bs_code, year=year, quarter=4)
        if ec == "0" and rows:
            row = dict(zip(fields, rows[0]))
            m.current_ratio = _f(row.get("currentRatio"))
            m.quick_ratio = _f(row.get("quickRatio"))
            m.cash_ratio = _f(row.get("cashRatio"))
            m.debt_to_assets = _f(row.get("liabilityToAsset"))
            
            # Derive debt_to_equity from asset_to_equity
            # D/E = (assets - equity) / equity = asset_to_equity - 1
            a2e = _f(row.get("assetToEquity"))
            if a2e and a2e > 1:
                m.debt_to_equity = round(a2e - 1, 4)
            
            bvps = _f(row.get("bvps"))
            if price and price > 0 and bvps and bvps > 0:
                m.price_to_book_ratio = round(price / bvps, 2)
        
        # ---- Cash flow data ----
        ec, fields, rows = _bs_q(bs.query_cash_flow_data, bs_code, year=year, quarter=4)
        if ec == "0" and rows:
            row = dict(zip(fields, rows[0]))
            m.operating_cash_flow_ratio = _f(row.get("CFOToOR"))
            m.interest_coverage = _f(row.get("ebitToInterest"))
        
        # ---- Operation data ----
        ec, fields, rows = _bs_q(bs.query_operation_data, bs_code, year=year, quarter=4)
        if ec == "0" and rows:
            row = dict(zip(fields, rows[0]))
            m.asset_turnover = _f(row.get("AssetTurnRatio")) or _f(row.get("assetTurn"))
            m.inventory_turnover = _f(row.get("INVTurnRatio")) or _f(row.get("invturn"))
            m.receivables_turnover = _f(row.get("NRTurnRatio")) or _f(row.get("arturn"))
    
    except Exception as e:
        logger.warning("baostock financials failed for %s: %s", ticker, e)
    
    result = [m]
    with _CACHE_LOCK:
        _FIN_CACHE[ck] = result
    return result


# -- Market Cap --
_MC_CACHE: dict[str, float | None] = {}

def get_market_cap(ticker: str, end_date: str, api_key=None) -> float | None:
    ck = f"mc_{ticker}"
    with _CACHE_LOCK:
        if ck in _MC_CACHE:
            return _MC_CACHE[ck]
    
    tq = _tencent_quote(ticker)
    if tq:
        mcap = tq.get("mcap_yi", 0)
        if mcap and mcap > 0:
            val = mcap * 100000000
            with _CACHE_LOCK:
                _MC_CACHE[ck] = val
            return val
    
    # Fallback: price * shares from baostock
    code, exchange = _parse(ticker)
    bs_code = f"{'sh' if exchange in ('SS','SH') else 'sz'}.{code}"
    try:
        _ensure_login()
        ec, fields, rows = _bs_q(bs.query_profit_data, bs_code, year=_latest_fiscal_year(end_date), quarter=4)
        if ec == "0" and rows:
            row = dict(zip(fields, rows[0]))
            shares = _f(row.get("totalShare"))
            if tq and shares:
                val = tq.get("price", 0) * shares
                if val > 0:
                    with _CACHE_LOCK:
                        _MC_CACHE[ck] = val
                    return val
    except Exception:
        pass
    
    with _CACHE_LOCK:
        _MC_CACHE[ck] = None
    return None


# -- News --
def get_company_news(ticker: str, end_date: str, start_date=None, limit=50, api_key=None) -> list[CompanyNews]:
    code, _ = _parse(ticker)
    
    # 东财 search-api
    import json as _json
    url = "https://search-api-web.eastmoney.com/search/jsonp"
    inner_param = {
        "uid": "", "keyword": code,
        "type": ["cmsArticleWebOld"],
        "client": "web", "clientType": "web", "clientVersion": "curr",
        "param": {"cmsArticleWebOld": {
            "searchScope": "default", "sort": "default",
            "pageIndex": 1, "pageSize": min(limit, 50),
            "preTag": "", "postTag": "",
        }},
    }
    params = {
        "cb": "callback",
        "param": _json.dumps(inner_param, ensure_ascii=False),
        "_": "1",
    }
    headers = {
        "Referer": "https://so.eastmoney.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    
    try:
        r = _em_get(url, params=params, headers=headers, timeout=15)
        text = r.text
        text = text[text.index("(") + 1: text.rindex(")")]
        data = _json.loads(text)
        articles = []
        for item in data.get("result", {}).get("cmsArticleWebOld", []):
            pub_date = str(item.get("date", "") or "")[:10]
            if not pub_date:
                continue
            if start_date and pub_date < start_date:
                continue
            if pub_date > end_date:
                continue
            articles.append(CompanyNews(
                ticker=ticker,
                title=item.get("title", ""),
                author=item.get("mediaName", "东方财富"),
                source="东方财富",
                date=pub_date,
                url=item.get("url", ""),
            ))
            if len(articles) >= limit:
                break
        if articles:
            return articles
    except Exception as e:
        logger.warning("eastmoney news failed for %s: %s", code, e)
    
    # Sina fallback
    try:
        prefix = _market_prefix(code)
        url2 = (f"https://vip.stock.finance.sina.com.cn/corp/view/"
                f"vCB_AllNewsStock.php?symbol={prefix}{code}&Page=1")
        r2 = requests.get(url2, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, proxies={"http": "", "https": ""})
        r2.encoding = "gb2312"
        articles = []
        matches = re.findall(
            r"(\d{4}-\d{2}-\d{2})\s*(?:&nbsp;)*(\d{2}:\d{2})\s*(?:&nbsp;)*"
            r"<a[^>]+href='([^']+)'[^>]*>([^<]+)</a>",
            r2.text,
        )
        for date_str, time_str, link, title in matches[:limit]:
            if start_date and date_str < start_date:
                continue
            if date_str > end_date:
                continue
            articles.append(CompanyNews(
                ticker=ticker, title=title.strip(), author=None,
                source="新浪财经", date=date_str, url=link,
            ))
        if articles:
            return articles
    except Exception as e:
        logger.warning("sina news fallback failed: %s", e)
    
    return []


# -- Stubs --
def get_insider_trades(*args, **kwargs) -> list[InsiderTrade]:
    return []

def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "annual",
    limit: int = 10,
    api_key: str = None,
) -> list:
    """Fetch multi-year financial line items from baostock.
    
    Fills real data for fields baostock supports, skips unsupported ones.
    """
    import pandas as pd
    from src.data.models import LineItem
    
    code, exchange = _parse(ticker)
    bs_code = f"{'sh' if exchange in ('SS','SH') else 'sz'}.{code}"
    end_year = _latest_fiscal_year(end_date)
    
    try:
        _ensure_login()
    except RuntimeError:
        return []
    
    # ---- Map requested line items to baostock data sources ----
    # Field → (source_func, bs_field_name)
    FIELD_MAP = {
        "earnings_per_share": ("profit", "epsTTM"),
        "net_income": ("profit", "netProfit"),
        "revenue": ("profit", "MBRevenue"),
        "gross_profit": ("profit", "gpMargin"),  # will multiply by revenue
        "outstanding_shares": ("profit", "totalShare"),
        "return_on_equity": ("profit", "roeAvg"),
        
        "book_value_per_share": ("balance", "bvps"),
        "current_ratio": ("balance", "currentRatio"),
        "quick_ratio": ("balance", "quickRatio"),
        "cash_ratio": ("balance", "cashRatio"),
        "debt_to_assets": ("balance", "liabilityToAsset"),
        
        "inventory_turnover": ("operation", "INVTurnRatio"),
        "asset_turnover": ("operation", "AssetTurnRatio"),
        "receivables_turnover": ("operation", "NRTurnRatio"),
        
        "operating_cash_flow_ratio": ("cashflow", "CFOToOR"),
        "cash_from_operations_to_net_profit": ("cashflow", "CFOToNP"),
    }
    
    # Build a list of fields we can actually fill
    requested = set(item.lower().strip() for item in line_items)
    gross_profit_requested = "gross_profit" in requested
    debt_to_equity_requested = "debt_to_equity" in requested
    operating_margin_requested = "operating_margin" in requested
    gross_margin_requested = "gross_margin" in requested or "gross_margin_pct" in requested
    
    results = []
    
    for year_offset in range(min(limit, 5)):  # up to 5 years back
        yr = end_year - year_offset
        
        # ---- Profit data ----
        ec1, f1, rows1 = _bs_q(bs.query_profit_data, bs_code, year=yr, quarter=4)
        if ec1 != "0" or not rows1:
            continue
        p_row = dict(zip(f1, rows1[0]))
        
        # ---- Balance data ----
        ec2, f2, rows2 = _bs_q(bs.query_balance_data, bs_code, year=yr, quarter=4)
        b_row = dict(zip(f2, rows2[0])) if ec2 == "0" and rows2 else {}
        
        # ---- Operation data ----
        ec3, f3, rows3 = _bs_q(bs.query_operation_data, bs_code, year=yr, quarter=4)
        o_row = dict(zip(f3, rows3[0])) if ec3 == "0" and rows3 else {}
        
        # ---- Cash flow data ----
        ec4, f4, rows4 = _bs_q(bs.query_cash_flow_data, bs_code, year=yr, quarter=4)
        c_row = dict(zip(f4, rows4[0])) if ec4 == "0" and rows4 else {}
        
        # Extract values
        eps = _f(p_row.get("epsTTM"))
        net_income = _f(p_row.get("netProfit"))
        revenue = _f(p_row.get("MBRevenue"))
        shares = _f(p_row.get("totalShare"))
        roe = _f(p_row.get("roeAvg"))
        gross_margin = _f(p_row.get("gpMargin"))
        net_margin = _f(p_row.get("npMargin"))
        
        bvps = _f(b_row.get("bvps"))
        current_ratio = _f(b_row.get("currentRatio"))
        quick_ratio = _f(b_row.get("quickRatio"))
        cash_ratio = _f(b_row.get("cashRatio"))
        d2a = _f(b_row.get("liabilityToAsset"))
        a2e = _f(b_row.get("assetToEquity"))
        
        inv_turn = _f(o_row.get("INVTurnRatio"))
        asset_turn = _f(o_row.get("AssetTurnRatio"))
        recv_turn = _f(o_row.get("NRTurnRatio"))
        
        cfo_to_or = _f(c_row.get("CFOToOR"))
        
        report_date = str(p_row.get("pubDate", "") or p_row.get("statDate", ""))[:10]
        if not report_date or report_date == "":
            continue
        
        # Build the LineItem with all available data
        item_data = {
            "ticker": ticker,
            "report_period": report_date,
            "period": "annual",
            "currency": "CNY",
        }
        
        for field in line_items:
            key = field.strip().lower()
            if key == "earnings_per_share" and eps is not None:
                item_data["earnings_per_share"] = eps
            elif key == "revenue" and revenue is not None:
                item_data["revenue"] = revenue
            elif key == "net_income" and net_income is not None:
                item_data["net_income"] = net_income
            elif key == "outstanding_shares" and shares is not None:
                item_data["outstanding_shares"] = shares
            elif key == "return_on_equity" and roe is not None:
                item_data["return_on_equity"] = roe
            elif key in ("gross_margin", "gross_margin_pct") and gross_margin is not None:
                item_data[key] = gross_margin
            elif key == "net_margin" and net_margin is not None:
                item_data["net_margin"] = net_margin
            elif key == "gross_profit" and revenue and gross_margin:
                item_data["gross_profit"] = revenue * gross_margin
            elif key == "book_value_per_share" and bvps is not None:
                item_data["book_value_per_share"] = bvps
            elif key == "current_ratio" and current_ratio is not None:
                item_data["current_ratio"] = current_ratio
            elif key == "quick_ratio" and quick_ratio is not None:
                item_data["quick_ratio"] = quick_ratio
            elif key == "cash_ratio" and cash_ratio is not None:
                item_data["cash_ratio"] = cash_ratio
            elif key == "debt_to_assets" and d2a is not None:
                item_data["debt_to_assets"] = d2a
            elif key == "debt_to_equity" and a2e and a2e > 1:
                item_data["debt_to_equity"] = round(a2e - 1, 4)
            elif key == "inventory_turnover" and inv_turn is not None:
                item_data["inventory_turnover"] = inv_turn
            elif key == "asset_turnover" and asset_turn is not None:
                item_data["asset_turnover"] = asset_turn
            elif key == "receivables_turnover" and recv_turn is not None:
                item_data["receivables_turnover"] = recv_turn
            elif key == "operating_margin" and net_margin is not None:
                item_data["operating_margin"] = net_margin
            elif key == "operating_cash_flow_ratio" and cfo_to_or is not None:
                item_data["operating_cash_flow_ratio"] = cfo_to_or
            elif key == "return_on_equity" and roe is not None:
                item_data["return_on_equity"] = roe
        
        results.append(LineItem(**item_data))
    
    results.sort(key=lambda x: x.report_period, reverse=True)
    return results
