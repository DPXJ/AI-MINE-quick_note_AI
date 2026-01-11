"""快速设置并运行程序"""
import os
from pathlib import Path

# 获取当前目录
current_dir = Path(__file__).parent

# 创建.env文件（如果不存在）
env_file = current_dir / ".env"
if not env_file.exists():
    env_content = """# AI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Notion配置
NOTION_API_KEY=your_notion_api_key_here
NOTION_DATABASE_ID=your_database_id_here

# Flomo配置
FLOMO_API_URL=https://flomoapp.com/iwh/your_webhook_url_here
"""
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("[OK] .env文件已创建")
    print("\n[!] 请先编辑 .env 文件，填入你的API密钥！")
    print("\n然后重新运行此脚本。")
else:
    print("[OK] .env文件已存在")
    print("\n[启动] 正在启动 QuickNote AI...")
    print("=" * 50)
    
    # 切换到项目目录并运行主程序
    os.chdir(current_dir)
    
    # 添加项目目录到Python路径
    import sys
    sys.path.insert(0, str(current_dir))
    
    # 运行主程序
    try:
        from src.main import main
        main()
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"\n[错误] 启动失败: {e}")
        print("\n请检查：")
        print("1. 是否安装了所有依赖: pip install -r requirements.txt")
        print("2. .env文件配置是否正确")
        print("3. 查看日志文件: logs/ 目录")

