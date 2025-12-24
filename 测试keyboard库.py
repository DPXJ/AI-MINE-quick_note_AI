"""测试 keyboard 库是否正常工作"""
import sys

def test_keyboard_import():
    """测试是否能导入 keyboard 库"""
    try:
        import keyboard
        print("✓ keyboard 库已安装")
        print(f"  版本: {keyboard.__version__ if hasattr(keyboard, '__version__') else '未知'}")
        return True
    except ImportError:
        print("✗ keyboard 库未安装")
        print("  请运行: pip install keyboard>=0.13.5")
        return False

def test_keyboard_function():
    """测试 keyboard 库的基本功能"""
    try:
        import keyboard
        
        print("\n测试快捷键注册...")
        
        # 测试回调
        test_triggered = []
        def test_callback():
            test_triggered.append(True)
            print("  ✓ 快捷键触发成功！")
        
        # 注册测试快捷键（使用不常用的组合避免冲突）
        test_hotkey = "ctrl+shift+f12"
        print(f"  注册测试快捷键: {test_hotkey}")
        
        keyboard.add_hotkey(test_hotkey, test_callback)
        print(f"  ✓ 快捷键已注册")
        
        # 提示用户测试
        print(f"\n请按下 {test_hotkey} 测试...")
        print("(按 Esc 结束测试)")
        
        # 等待用户测试
        import time
        start_time = time.time()
        timeout = 30  # 30秒超时
        
        while time.time() - start_time < timeout:
            if test_triggered:
                print("\n✓ 测试成功！keyboard 库工作正常")
                keyboard.remove_hotkey(test_hotkey)
                return True
            
            # 检查 Esc 键
            if keyboard.is_pressed('esc'):
                print("\n测试已取消")
                keyboard.remove_hotkey(test_hotkey)
                return False
            
            time.sleep(0.1)
        
        print("\n⚠ 测试超时（30秒内未按快捷键）")
        keyboard.remove_hotkey(test_hotkey)
        return False
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("QuickNote AI - keyboard 库测试")
    print("=" * 50)
    print()
    
    # 测试导入
    if not test_keyboard_import():
        print("\n请先安装 keyboard 库后再测试")
        input("\n按回车退出...")
        return
    
    print()
    print("-" * 50)
    
    # 测试功能
    try:
        test_keyboard_function()
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    
    print()
    print("=" * 50)
    print("测试完成")
    print("=" * 50)
    input("\n按回车退出...")

if __name__ == "__main__":
    main()
