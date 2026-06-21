// Chinese (Simplified) translations for AI Hedge Fund
const zh: Record<string, string> = {
  // Top bar
  'Toggle left sidebar': '切换左边栏',
  'Toggle Right Side Bar (⌘B)': '切换左边栏 (⌘B)',
  'Toggle bottom panel': '切换底部面板',
  'Toggle Bottom Panel (⌘J)': '切换底部面板 (⌘J)',
  'Toggle right sidebar': '切换右边栏',
  'Toggle Right Side Bar (⌘I)': '切换右边栏 (⌘I)',
  'Open settings': '打开设置',
  'Open Settings (⌘,)': '打开设置 (⌘,)',
  'Language': '语言',
  '中文': '中文',
  'English': 'English',

  // Welcome screen
  'Welcome to the AI Hedge Fund': '欢迎使用 AI 对冲基金',
  'Create a flow from the left sidebar (⌘B) to open it in a tab, or open settings (⌘,) to configure your preferences.': '从左侧边栏创建一个流程 (⌘B)，或在设置中配置你的偏好 (⌘,)。',
  'Flows now open in tabs': '流程现在以标签页形式打开',

  // Left sidebar
  'Flows': '流程',
  'Save "Untitled Flow"': '保存"未命名流程"',
  'Create new flow': '新建流程',
  'Search flows...': '搜索流程...',
  'No flows saved yet': '暂无保存的流程',
  'Create your first flow to get started': '创建你的第一个流程开始使用',
  'Recent Flows': '最近流程',
  'My Flows': '我的流程',
  'Templates': '模板',

  // Flow actions
  'Save Current Flow': '保存当前流程',
  'Save': '保存',
  'Create New Flow': '新建流程',

  // Create dialog
  'Create New Flow': '新建流程',
  'Create a new flow with a custom name and description.': '创建一个自定义名称和描述的流程。',
  'Flow Name': '流程名称',
  'Enter flow name': '输入流程名称',
  'Description (optional)': '描述（可选）',
  'Enter flow description (optional)': '输入流程描述（可选）',
  'Creating...': '创建中...',
  'Create Flow': '创建流程',
  'Cancel': '取消',
  // Components
  'Components': '组件',
  'Search components...': '搜索组件...',
  'Start Nodes': '起始节点',
  'Analysts': '分析师',
  'Swarms': '团队',
  'End Nodes': '结束节点',

  // Stock Analyzer Node
  'Stock Analyzer': '股票分析器',
  'Stock Input': '股票输入',
  'Enter individual stocks and connect this node to Analysts to generate insights.': '输入个股并连接到分析师节点以生成分析。',
  'Tickers': '股票代码',
  'Enter tickers': '输入股票代码',
  'Available Cash': '可用资金',
  'Start Date': '开始日期',
  'End Date': '结束日期',
  'Advanced': '高级选项',
  'Single Run': '单次运行',
  'Backtest': '回测',
  'Run': '运行',
  'Stop': '停止',
  'You can add multiple tickers using commas (AAPL,NVDA,TSLA)': '支持多个股票代码，用逗号分隔（如 AAPL,NVDA,TSLA）',

  // Agent Node
  'Agent': '分析师',
  'Model': '模型',
  'Select model': '选择模型',
  'None': '无',
  'Use default model': '使用默认模型',

  // Portfolio Manager Node
  'Portfolio Manager': '投资组合管理器',
  'Portfolio Analyzer': '投资组合分析器',

  // Risk Manager
  'Risk Manager': '风险管理器',

  // Settings
  'Settings': '设置',
  'API Keys': 'API 密钥',
  'Language Models': '语言模型',
  'Ollama': '本地模型',
  'General': '通用',
  'Appearance': '外观',
  'Theme': '主题',
  'Light': '浅色',
  'Dark': '深色',
  'System': '跟随系统',

  // API Keys page
  'Add API Key': '添加 API 密钥',
  'Provider': '提供商',
  'API Key': 'API 密钥',
  'Status': '状态',
  'Active': '已启用',
  'Inactive': '已停用',
  'Actions': '操作',
  'Save Key': '保存密钥',
  'Delete': '删除',
  'Test Connection': '测试连接',

  // Models page
  'Cloud Models': '云端模型',
  'Available Models': '可用模型',
  'DeepSeek V4 Pro': 'DeepSeek V4 Pro',
  'DeepSeek V4 Flash': 'DeepSeek V4 Flash',
  'GPT-4.1': 'GPT-4.1',
  'GPT-4o': 'GPT-4o',
  'Claude': 'Claude',
  'Default': '默认',

  // Bottom panel
  'Output': '输出',
  'Backtest Results': '回测结果',
  'Logs': '日志',

  // Status
  'Idle': '就绪',
  'Running': '运行中',
  'Complete': '完成',
  'Error': '错误',
  'Done': '完成',
  'Processing': '处理中',
  'Preparing hedge fund run': '准备对冲基金运行',

  // Backtest
  'Performance Metrics': '性能指标',
  'Sharpe Ratio': '夏普比率',
  'Sortino Ratio': '索提诺比率',
  'Max Drawdown': '最大回撤',
  'Total Return': '总收益率',
  'Initial Portfolio Value': '初始投资组合价值',
  'Final Portfolio Value': '最终投资组合价值',

  // Trading decision
  'Analysis for': '分析',
  'TRADING DECISION': '交易决策',
  'PORTFOLIO SUMMARY': '投资组合摘要',
  'Action': '操作',
  'BUY': '买入',
  'SELL': '卖出',
  'HOLD': '持有',
  'Quantity': '数量',
  'Confidence': '置信度',
  'Reasoning': '推理过程',
  'Signal': '信号',
  'Bullish': '看涨',
  'Bearish': '看跌',
  'Neutral': '中性',
  'No valid trade available': '无有效交易',
  'Analysis complete': '分析完成',
  'Failed to generate hedge fund decisions': '生成对冲基金决策失败',
  'An error occurred while processing the request': '处理请求时发生错误',

  // Analyst names
  'Aswath Damodaran': '阿斯沃斯·达摩达兰',
  'Ben Graham': '本杰明·格雷厄姆',
  'Bill Ackman': '比尔·阿克曼',
  'Cathie Wood': '凯西·伍德',
  'Charlie Munger': '查理·芒格',
  'Michael Burry': '迈克尔·伯里',
  'Mohnish Pabrai': '莫尼什·帕伯莱',
  'Nassim Taleb': '纳西姆·塔勒布',
  'Peter Lynch': '彼得·林奇',
  'Phil Fisher': '菲利普·费雪',
  'Rakesh Jhunjhunwala': '拉克什·金君瓦拉',
  'Stanley Druckenmiller': '斯坦利·德鲁肯米勒',
  'Warren Buffett': '沃伦·巴菲特',
  'Fundamentals Analyst': '基本面分析师',
  'Technical Analyst': '技术分析师',
  'Valuation Analyst': '估值分析师',
  'Sentiment Analyst': '情绪分析师',
  'News Sentiment': '新闻情绪',
  'Growth Analyst': '增长分析师',

  // Error messages
  'Loading': '加载中',
  'No flows match your search': '没有找到匹配的流程',
  'No components match your search': '没有找到匹配的组件',
  'No components available': '暂无可用组件',
  'Components will appear here when loaded': '组件加载后将在此显示',
  'Failed to fetch agents': '获取分析师列表失败',
  'Failed to start hedge fund run': '启动对冲基金运行失败',
  'Connection error': '连接错误',
  'Unknown error occurred': '发生未知错误',
  'Client disconnected, cancelling hedge fund execution': '客户端已断开，取消对冲基金执行',
};

// English identity map (pass-through)
const en: Record<string, string> = {};

export const translations = { zh, en };
export type SupportedLocale = 'en' | 'zh';

export function getTranslation(key: string, locale: SupportedLocale): string {
  if (locale === 'zh') {
    return zh[key] || key;
  }
  return key;
}
