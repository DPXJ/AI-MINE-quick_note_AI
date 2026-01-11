# QuickNote AI - 安装和使用指南

## 📦 安装步骤

### 1. 安装Python（如果未安装）
- 访问 https://www.python.org/downloads/
- 下载并安装 Python 3.10 或更高版本
- **重要**：安装时勾选 "Add Python to PATH"

### 2. 安装依赖
打开命令提示符（cmd）或PowerShell，进入项目目录，执行：

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

#### 3.1 创建 .env 文件
在项目根目录创建 `.env` 文件（可以复制 `.env.template` 并重命名）

#### 3.2 配置 OpenAI API
```
OPENAI_API_KEY=sk-你的密钥
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

💡 **获取OpenAI API Key**：
1. 访问 https://platform.openai.com/api-keys
2. 注册并登录
3. 创建新的API密钥

#### 3.3 配置 Notion
```
NOTION_API_KEY=secret_你的密钥
NOTION_DATABASE_ID=你的数据库ID
```

💡 **获取Notion API Key和Database ID**：

1. **创建Integration**：
   - 访问 https://www.notion.so/my-integrations
   - 点击 "+ New integration"
   - 给它起个名字（如"QuickNote AI"）
   - 复制 "Internal Integration Token"（这就是 API Key）

2. **创建Database**：
   - 在Notion中创建一个新页面
   - 添加一个Database（表格视图）
   - 设置以下属性（列）：
     - `标题`（Title）- 主键
     - `状态`（Status）- 状态类型，选项：待办、进行中、完成
     - `优先级`（Select）- 单选，选项：高、中、低
     - `创建时间`（Date）
     - `标签`（Multi-select）- 多选

3. **连接Integration到Database**：
   - 打开创建的Database页面
   - 点击右上角的 "..." 菜单
   - 选择 "Add connections"
   - 选择你创建的Integration

4. **获取Database ID**：
   - 复制Database页面的URL
   - 格式：`https://notion.so/workspace/database_id?v=...`
   - `database_id` 就是你需要的ID（32位字符串）

#### 3.4 配置 Flomo（可选）
```
FLOMO_API_URL=https://flomoapp.com/iwh/你的webhook地址
```

💡 **获取Flomo Webhook URL**：
1. 打开Flomo App或网页版
2. 进入 设置 → API
3. 复制 Webhook URL

### 4. 配置AI识别规则（可选）
编辑 `config.yaml` 文件，自定义AI识别规则和快捷键。

## 🚀 运行程序

### 开发模式运行
双击 `run.bat` 或在命令行执行：
```bash
python src/main.py
```

### 打包成exe
双击 `build.bat` 或在命令行执行：
```bash
pyinstaller build.spec
```

打包完成后，可执行文件在 `dist/QuickNote_AI.exe`

## ⌨️ 使用方法

### 快捷键
- `Ctrl+Shift+Space`：打开快速输入窗口
- `Ctrl+Shift+C`：切换剪切板监控开关

### 快速输入
1. 按下 `Ctrl+Shift+Space`
2. 输入你的灵感
3. 按 `Enter` 提交（`Ctrl+Enter` 换行）
4. 按 `Esc` 取消

### 剪切板监控
1. 程序启动后，剪切板监控自动开启
2. 复制任何文本，AI会自动判断是否有价值
3. 如果有价值，会自动保存到Notion或Flomo
4. 可以通过 `Ctrl+Shift+C` 或托盘菜单切换开关

### 系统托盘
- 单击图标：显示菜单
- 双击图标：打开快速输入
- 右键菜单：
  - 快速输入
  - 剪切板监控开关
  - 设置
  - 退出

## 🔧 配置说明

### config.yaml 配置项

#### 快捷键配置
```yaml
hotkeys:
  quick_input: "ctrl+shift+space"
  toggle_clipboard: "ctrl+shift+c"
```

#### 剪切板配置
```yaml
clipboard:
  enabled: true  # 启动时是否开启
  check_interval: 1.0  # 检查间隔（秒）
  min_length: 10  # 最小字符数
  max_length: 5000  # 最大字符数
```

#### AI规则配置
编辑 `ai_rules` 部分，自定义识别规则和提示词。

## ❓ 常见问题

### Q1: 程序启动失败
**A**: 检查以下几点：
1. 是否安装了所有依赖？`pip install -r requirements.txt`
2. `.env` 文件是否配置正确？
3. API密钥是否有效？

### Q2: 快捷键不生效
**A**: 
1. 检查快捷键是否与其他程序冲突
2. 尝试以管理员权限运行
3. 检查 `config.yaml` 中的快捷键配置

### Q3: Notion连接失败
**A**: 
1. 确认API Key正确
2. 确认Database ID正确
3. 确认Integration已连接到Database
4. 在设置界面点击"测试连接"

### Q4: AI识别不准确
**A**: 
1. 编辑 `config.yaml` 中的 AI 提示词
2. 调整关键词列表
3. 可以切换使用不同的AI模型

### Q5: 打包后的exe无法运行
**A**: 
1. 确保 `.env` 和 `config.yaml` 文件与 exe 在同一目录
2. 检查Windows防火墙/杀毒软件是否拦截
3. 以管理员权限运行

## 📊 日志文件
程序运行日志保存在 `logs/` 目录下，可以查看详细的运行信息和错误信息。

## 🔒 安全提示
- `.env` 文件包含敏感信息（API密钥），请勿分享或上传到公开仓库
- 建议定期更换API密钥
- 打包exe时，密钥会被包含在文件中，注意保管

## 💡 使用技巧

### Notion Database 最佳实践
1. 创建视图：
   - 按状态分组（待办/进行中/完成）
   - 按优先级排序
   - 按创建时间筛选（今天/本周）

2. 定期回顾：
   - 每天查看新增的灵感
   - 将待办标记为完成
   - 将有价值的内容整理到其他页面

### Flomo 使用建议
1. 使用标签体系：
   - #金句 - 深刻的见解
   - #产品 - 产品相关
   - #AI - AI技术相关
   - #方法论 - 思维框架

2. 定期复习：
   - 使用Flomo的复习功能
   - 导出到其他知识管理工具

## 🎯 效率提升建议
1. 将快捷键设置成最顺手的组合
2. 根据使用习惯调整AI识别规则
3. 定期查看日志，了解识别效果
4. 建立自己的标签体系

---

祝你使用愉快！如有问题，请查看日志文件或提交Issue。

