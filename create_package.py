#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""创建完整分发包"""
import shutil
import sys
from pathlib import Path

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 定义路径
dist_dir = Path('dist')
version = 'QuickNote_AI_v0.32'
package_dir = dist_dir / f'分发包_{version}'
zip_path = dist_dir / f'QuickNote_AI_分发包_v{version.split("_v")[1]}.zip'

print("=" * 50)
print("创建完整分发包")
print("=" * 50)
print()

# 1. 清理旧的分发包
if package_dir.exists():
    print(f"[清理] 删除旧的分发包目录: {package_dir}")
    shutil.rmtree(package_dir)

# 2. 创建分发包目录
print(f"[1/4] 创建分发包目录: {package_dir}")
package_dir.mkdir(parents=True, exist_ok=True)

# 3. 复制程序文件夹
print(f"[2/4] 复制程序文件...")
program_dir = dist_dir / version
if program_dir.exists():
    shutil.copytree(program_dir, package_dir / version)
    print(f"  [OK] 程序文件夹已复制")
else:
    print(f"  [ERROR] 未找到程序文件夹 {program_dir}")
    exit(1)

# 4. 复制配置文件模板
print(f"[3/4] 复制配置文件模板...")
if Path('config.yaml').exists():
    shutil.copy('config.yaml', package_dir / 'config.yaml.example')
    print(f"  [OK] config.yaml.example 已复制")
else:
    print(f"  [WARN] config.yaml 不存在，跳过")

if Path('env.example').exists():
    shutil.copy('env.example', package_dir / '.env.example')
    print(f"  [OK] .env.example 已复制")
else:
    print(f"  [WARN] env.example 不存在，跳过")

# 5. 创建README（如果不存在）
readme_path = package_dir / 'README.md'
if not readme_path.exists():
    print(f"[4/4] 创建README.md...")
    readme_content = """# QuickNote AI - 快速开始指南

## 📦 文件说明

- `QuickNote_AI_v0.32\\` - 主程序文件夹（包含所有运行文件）
- `config.yaml.example` - 配置文件模板（可选，程序会自动创建）
- `.env.example` - 环境变量配置模板（可选，程序会自动创建）

## 🚀 快速开始

### 第一步：运行程序

1. 进入 `QuickNote_AI_v0.32\\` 文件夹
2. 双击 `QuickNote_AI_v0.32.exe` 运行程序
3. 程序会最小化到系统托盘（任务栏右下角）
4. 右键托盘图标 → 选择"设置"打开配置界面

### 第二步：配置API密钥（通过设置界面）

**无需提前配置！** 程序可以在没有配置文件的情况下启动。

1. 右键系统托盘图标 → 选择"设置"
2. 在设置界面中填入你的API密钥：
   - **AI配置**：`OPENAI_API_KEY` - DeepSeek或其他OpenAI兼容API的密钥
   - **Notion配置**：`NOTION_API_KEY` 和 `NOTION_DATABASE_ID`（可选）
   - **Flomo配置**：`FLOMO_API_URL`（可选）
   - **TickTick配置**：`TICKTICK_WEBHOOK_URL`（可选）
3. 点击"保存"按钮，配置会自动保存到 `.env` 和 `config.yaml` 文件
4. 配置完成后，相关功能即可使用

**注意**：如果配置文件不存在，程序会自动创建。你也可以参考 `config.yaml.example` 和 `.env.example` 手动创建配置文件。

## ⌨️ 快捷键

- `Ctrl+Shift+Space` - 打开快速输入窗口
- `Ctrl+Shift+C` - 开启/关闭剪切板自动同步

## ⚙️ 功能说明

### 快速输入

按 `Ctrl+Shift+Space` 打开快速输入窗口，支持：
- **Notion**：状态、优先级、标签
- **Flomo**：标签
- **TickTick**：自动识别时间并设置提醒

### 剪切板自动同步

开启后，复制的内容会自动识别并同步到对应平台：
- 包含时间信息的任务 → TickTick
- 知识、金句、方法论 → Flomo
- 待办、灵感 → Notion

## 🔧 常见问题

### Q1: 程序无法启动

**解决方法**：
1. 安装 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. 确保程序路径中没有中文字符
3. 以管理员身份运行（全局快捷键需要管理员权限）

### Q2: 快捷键不工作

**解决方法**：
1. 以管理员身份运行程序
2. 检查快捷键是否与其他程序冲突
3. 在设置中重新设置快捷键

### Q3: API连接失败

**解决方法**：
1. 检查设置界面中的API密钥是否正确
2. 检查网络连接
3. 检查防火墙设置

## 📝 注意事项

1. **不要删除 `_internal` 文件夹**：这是程序运行必需的依赖文件
2. **路径建议**：避免使用包含中文字符的路径
3. **管理员权限**：全局快捷键功能需要管理员权限
4. **配置文件**：可以通过设置界面配置，程序会自动创建 `.env` 和 `config.yaml` 文件

## 🆘 技术支持

如果遇到问题：
1. 查看 `logs` 文件夹中的日志文件
2. 确保已安装 Visual C++ Redistributable
3. 尝试以管理员身份运行
4. 检查配置文件是否正确

祝使用愉快！🎉
"""
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"  [OK] README.md 已创建")

# 6. 创建压缩包
print()
print(f"[5/5] 创建压缩包...")
if zip_path.exists():
    zip_path.unlink()
    print(f"  [OK] 删除旧压缩包")

shutil.make_archive(str(zip_path).replace('.zip', ''), 'zip', package_dir)

if zip_path.exists():
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print()
    print("=" * 50)
    print("[SUCCESS] 打包完成！")
    print("=" * 50)
    print(f"压缩包位置: {zip_path}")
    print(f"压缩包大小: 约 {size_mb:.1f} MB")
    print()
    print("分发包包含：")
    print(f"  [OK] {version}/ - 主程序文件夹")
    print(f"  [OK] config.yaml.example - 配置模板")
    print(f"  [OK] .env.example - API密钥模板")
    print(f"  [OK] README.md - 使用说明")
    print()
    print("可以直接发送给其他用户使用！")
else:
    print("[ERROR] 压缩包创建失败")
    exit(1)

