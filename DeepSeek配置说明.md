# DeepSeek API 配置指南

## ✅ 已支持 DeepSeek！

程序现在已经支持 DeepSeek API，并且默认使用 DeepSeek。

## 🚀 快速配置

### 方式1：通过设置界面配置（推荐）

1. **启动程序**后，右键系统托盘图标
2. 点击 **"设置"**
3. 在 **"API配置"** 标签页中：
   - **AI 提供商**：选择 `deepseek`（默认已选择）
   - **API Key**：填入你的 DeepSeek API Key
   - **Base URL**：自动设置为 `https://api.deepseek.com/v1`
   - **Model**：自动设置为 `deepseek-chat`
4. 点击 **"保存设置"**
5. 点击 **"测试连接"** 验证配置是否正确

### 方式2：手动编辑 .env 文件

如果喜欢手动配置，可以编辑 `.env` 文件：

```env
# AI API配置
AI_PROVIDER=deepseek
OPENAI_API_KEY=sk-你的DeepSeek密钥
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

## 🔑 获取 DeepSeek API Key

1. 访问 **DeepSeek 官网**：https://platform.deepseek.com/
2. 注册/登录账号
3. 进入 **API 密钥** 页面
4. 创建新的 API Key
5. 复制密钥到程序配置中

## 📊 DeepSeek 模型选择

DeepSeek 提供多个模型，你可以在设置中修改：

| 模型名称 | 说明 | 适用场景 |
|---------|------|---------|
| `deepseek-chat` | 通用对话模型（推荐） | 日常对话、内容分析 |
| `deepseek-coder` | 代码专用模型 | 代码相关任务 |
| `deepseek-reasoner` | 推理模型 | 复杂推理任务 |

**建议**：使用 `deepseek-chat`，性价比最高。

## ⚙️ 与 OpenAI 切换

如果需要切换到 OpenAI：

1. 在设置界面的 **"AI 提供商"** 下拉框中选择 `openai`
2. **Base URL** 会自动变为 `https://api.openai.com/v1`
3. **Model** 会自动变为 `gpt-4o-mini`
4. 填入 OpenAI API Key
5. 保存设置

## 💡 为什么推荐 DeepSeek？

- ✅ **价格便宜**：比 OpenAI 便宜很多
- ✅ **性能优秀**：国产 AI，中文理解好
- ✅ **响应速度快**：国内访问更顺畅
- ✅ **API 兼容**：完全兼容 OpenAI API 格式

## 🔧 常见问题

### Q: DeepSeek 配置后还是调用 OpenAI？
A: 检查：
1. `.env` 文件中的 `AI_PROVIDER=deepseek` 是否正确
2. 是否重启了程序
3. 在设置界面确认当前选择的提供商

### Q: 如何验证 DeepSeek 配置正确？
A: 在设置界面点击 **"测试连接"** 按钮，会显示连接测试结果。

### Q: 可以同时配置多个 AI 提供商吗？
A: 不可以，一次只能使用一个。但可以在设置界面随时切换，保存后立即生效。

---

**现在就去设置界面配置你的 DeepSeek API Key 吧！** 🚀

