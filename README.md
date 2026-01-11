# QuickNote AI - 智能笔记助手

一个轻量级的Windows桌面应用，帮助你快速记录灵感并智能同步到Notion和Flomo。

## ✨ 核心功能

### 1. 快捷键快速输入
- 按 `Ctrl+Shift+Space` 快速调出输入窗口
- 输入完成后自动保存到Notion的灵感收集箱
- 极简界面，不打断工作流

### 2. 智能剪切板监控
- 后台自动监控系统剪切板
- AI智能识别有价值的内容
- 自动分流到合适的笔记工具：
  - 📝 金句、知识 → Flomo
  - ✅ 灵感、待办 → Notion

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
1. 复制 `.env.example` 为 `.env`
2. 填入你的API密钥：
   - OpenAI API Key（或Claude API Key）
   - Notion API Key和Database ID
   - Flomo Webhook URL

### 运行程序
```bash
python src/main.py
```

## 📦 打包成exe

```bash
# 使用PyInstaller打包
pyinstaller build.spec

# 打包后的exe位于 dist/QuickNote_AI.exe
```

## ⚙️ 配置说明

### Notion设置
1. 访问 https://www.notion.so/my-integrations
2. 创建新的Integration，获取API Key
3. 创建一个Database（灵感收集箱）
4. 将Integration添加到该Database
5. 复制Database ID到 `.env` 文件

### Flomo设置
1. 打开Flomo App
2. 进入设置 → API → 获取Webhook URL
3. 复制URL到 `.env` 文件

### AI提示词自定义
编辑 `config.yaml` 中的 `ai_rules` 部分，自定义识别规则。

## 🎯 使用场景

- 💡 工作中突然有灵感 → 快捷键快速记录
- 📚 阅读时发现金句 → 复制后自动保存到Flomo
- ✅ 聊天中产生待办 → 复制后自动添加到Notion

## 🛠️ 技术栈

- **GUI**: PyQt5（跨平台，打包体验好）
- **快捷键**: pynput（全局快捷键监听）
- **API集成**: notion-client, requests
- **AI**: OpenAI API / Claude API
- **打包**: PyInstaller

## 📝 注意事项

- 首次运行需要配置API密钥
- 剪切板监控可以通过 `Ctrl+Shift+C` 开关
- 建议使用GPT-4o-mini节省成本
- 程序会在系统托盘常驻运行

## 🔄 版本历史

### v1.0.0 (2025-12-13)
- ✅ 快捷键快速输入功能
- ✅ Notion集成
- ✅ 剪切板监控和AI识别
- ✅ Flomo集成
- ✅ 系统托盘常驻
- ✅ 打包成exe

## 📧 反馈与支持

如有问题或建议，欢迎提Issue。

