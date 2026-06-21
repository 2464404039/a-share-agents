# 🤖 AI 多 Agent 量化投资系统

基于开源项目 [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) 二次开发，**全面适配 A 股市场**。

19 个 AI Agent 模拟巴菲特、彼得·林奇、本杰明·格雷厄姆等投资大师的分析逻辑，并行分析股票并给出交易决策。

---

## ✨ 功能特点

### 🧠 多 Agent 智能分析
- **19 个独立 AI Agent** 并行分析，覆盖价值投资、成长投资、技术分析、量化分析等流派
- 分析师列表：巴菲特、格雷厄姆、彼得·林奇、查理·芒格、费雪、凯西·伍德、塔勒布、达摩达兰、迈克尔·伯里、比尔·阿克曼、德鲁肯米勒、拉凯什·金君瓦拉、莫尼什·帕伯莱、Aswath Damodaran
- **LangGraph 有向无环图编排**，Agent 并发执行，Portfolio Manager 汇总决策

### 🇨🇳 全面 A 股支持
- **A 股股票直接分析**，输入 `688008.SS` / `000001.SZ` 即可
- **四源数据自动容错**：
  - 🔵 **腾讯行情 API** — 实时 PE、PB、市值（最稳定，秒级返回）
  - 🟢 **baostock** — K 线数据 + 完整三张财务报表
  - 🟡 **新浪财经** — K 线备用 + 新闻
  - 🔴 **东方财富** — 新闻分析 + K线备用
- **数据自动降级**：一个源挂了自动切下一个，零中断

### 📊 完整财务数据覆盖
| 字段 | 来源 |
|------|------|
| PE / PB / 市值 | 腾讯实时行情 |
| P/S 市销率 | baostock 营收计算 |
| ROE / 毛利率 / 净利率 | baostock 利润表 |
| EPS / EPS 增长率 | baostock 连续 3 年对比 |
| 资产负债率 / 负债权益比 | baostock 资产负债表 |
| 流动比率 / 速动比率 / 现金比率 | baostock 资产负债表 |
| 资产周转率 / 库存周转率 / 应收周转率 | baostock 运营数据 |
| 经营现金流/营收比 | baostock 现金流量表 |
| 新闻情感分析 | 东方财富 + 新浪双源 |

### 🖥️ 双端可用
- **CLI 模式** — `poetry run python src/main.py --ticker 688008.SS --analysts-all`
- **Web UI** — FastAPI + React + TypeScript 可视化界面

---

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Poetry

### 安装

```bash
git clone https://github.com/2464404039/ai-hedge-fund.git
cd ai-hedge-fund
poetry install
```

### 配置 API Key

本项目需要 **DeepSeek API Key**（分析师使用的 AI 模型）：

```cmd
set DEEPSEEK_API_KEY=sk-your-key-here
```

### 运行 CLI

**单个 A 股全部分析师：**
```cmd
cd /d C:\Users\Administrator\ai-hedge-fund && set DEEPSEEK_API_KEY=*** && poetry run python src/main.py --ticker 688008.SS --model deepseek-v4-pro --analysts-all
```

**只跑特定分析师（更快）：**
```cmd
poetry run python src/main.py --ticker 688008.SS --model deepseek-v4-pro --analysts "fundamentals_analyst,growth_analyst,valuation_analyst"
```

**美股也支持：**
```cmd
poetry run python src/main.py --ticker AAPL --model deepseek-v4-pro --analysts-all
```

### 启动 Web UI

```cmd
:: 终端 1：启动后端
cd /d C:\Users\Administrator\ai-hedge-fund
poetry run uvicorn app.backend.main:app --host 127.0.0.1 --port 8080

:: 终端 2：启动前端
cd /d C:\Users\Administrator\ai-hedge-fund\app\frontend
npm run dev
```

浏览器打开 `http://localhost:5173`，拖拽 Agent 节点到画布，连接节点，点击 Run。

---

## 🔧 与原项目的主要改进

| 改进项 | 原项目 | 本项目 |
|--------|--------|--------|
| A 股支持 | ❌ 仅美股 | ✅ 全 A 股（6000+ 股票） |
| PE/PB/市值 | ❌ 需付费 API | ✅ 腾讯免费实时行情 |
| 财务报表 | ❌ 需付费 financialdatasets.ai | ✅ baostock 免费获取 |
| 数据容错 | ❌ 单源，挂了就报错 | ✅ 4 源自动降级 |
| 新闻分析 | ❌ 仅美股 | ✅ A 股新闻情感分析 |
| 多线程稳定性 | ❌ uvicorn 下 crash | ✅ 锁内登录+查询，线程安全 |
| 代理兼容性 | ❌ Windows 代理导致请求失败 | ✅ 全链路代理绕过 |
| 界面 | 英文 | ✅ 中文 |
| LLM 错误恢复 | ❌ JSON 解析失败静默丢弃 | ✅ 立即重试，成功率 100% |

---

## 📁 项目结构

```
ai-hedge-fund/
├── src/
│   ├── agents/              # 19 个 AI 分析师 + 风控/组合管理
│   ├── tools/
│   │   ├── api.py           # 数据路由（A股/美股自动分发）
│   │   └── akshare_data.py  # A 股多源数据层（核心）
│   ├── data/
│   │   ├── models.py        # 数据模型
│   │   └── cache.py         # 缓存
│   ├── llm/models.py        # LLM 模型管理
│   ├── graph/               # LangGraph 图编排
│   ├── utils/               # 工具函数
│   └── main.py              # CLI 入口
├── app/
│   ├── backend/             # FastAPI 后端
│   └── frontend/            # React + TypeScript 前端
└── pyproject.toml
```

---

## 📝 技术栈

- **Python 3.11+** / **LangGraph** / **LangChain**
- **FastAPI** / **Pydantic v2** / **SQLAlchemy**
- **React** / **TypeScript** / **Tailwind CSS** / **Vite**
- **DeepSeek V4** / **OpenAI** / **Anthropic** 等多模型支持
- **Pandas** / **NumPy** / **SciPy**（技术指标计算）
- **baostock** / **腾讯行情** / **新浪财经** / **东方财富**（A 股数据源）

---

## ⚠️ 免责声明

本项目仅供**教育和研究**使用。所有 AI 分析结果不构成投资建议。交易决策风险自负。

---

## 📄 许可证

MIT License - 基于 [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) 修改
