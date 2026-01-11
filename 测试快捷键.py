"""
快捷键功能测试脚本
用于测试 pynput 和 pywin32 是否正常工作
"""
import sys


def test_imports():
    """测试必要的库是否已安装"""
    print("=" * 50)
    print("测试 1: 检查依赖库")
    print("=" * 50)
    
    modules = {
        'pynput': '快捷键监听',
        'pynput.keyboard': 'pynput 键盘模块',
        'win32api': 'Windows API (pywin32)',
        'win32con': 'Windows 常量',
        'win32gui': 'Windows GUI API',
    }
    
    all_ok = True
    for module, desc in modules.items():
        try:
            __import__(module)
            print(f"✅ {desc:30} - {module}")
        except ImportError as e:
            print(f"❌ {desc:30} - {module} (缺失)")
            print(f"   错误: {e}")
            all_ok = False
    
    print()
    return all_ok


def test_keyboard_listener():
    """测试键盘监听器"""
    print("=" * 50)
    print("测试 2: 键盘监听器")
    print("=" * 50)
    
    try:
        from pynput import keyboard
        
        print("✅ pynput.keyboard 导入成功")
        
        # 测试创建监听器
        pressed_keys = []
        
        def on_press(key):
            try:
                key_name = key.char if hasattr(key, 'char') else key.name
                pressed_keys.append(key_name)
                print(f"   按键: {key_name}")
            except:
                pass
        
        def on_release(key):
            # 按 ESC 退出
            if key == keyboard.Key.esc:
                return False
        
        print("✅ 监听器创建成功")
        print()
        print("📢 测试说明:")
        print("   1. 现在请按几个键测试（会显示按键名称）")
        print("   2. 按 ESC 键退出测试")
        print("   3. 如果没有任何输出，说明监听器有问题")
        print()
        print("开始监听...")
        print("-" * 50)
        
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
        
        print("-" * 50)
        if pressed_keys:
            print(f"✅ 检测到 {len(pressed_keys)} 个按键")
            return True
        else:
            print("⚠️  未检测到任何按键，可能有问题")
            return False
            
    except Exception as e:
        print(f"❌ 键盘监听器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hotkey_combination():
    """测试快捷键组合"""
    print()
    print("=" * 50)
    print("测试 3: 快捷键组合 (Ctrl+Shift+Space)")
    print("=" * 50)
    
    try:
        from pynput import keyboard
        
        current_keys = set()
        target_hotkey = {'ctrl', 'shift', 'space'}
        hotkey_triggered = False
        
        def on_press(key):
            nonlocal hotkey_triggered
            try:
                # 获取按键名称
                if hasattr(key, 'char') and key.char:
                    key_name = key.char.lower()
                elif hasattr(key, 'name'):
                    key_name = key.name.lower()
                else:
                    return
                
                # 标准化修饰键
                if 'ctrl' in key_name:
                    key_name = 'ctrl'
                elif 'shift' in key_name:
                    key_name = 'shift'
                
                current_keys.add(key_name)
                
                # 检查是否匹配目标快捷键
                if target_hotkey.issubset(current_keys):
                    print()
                    print("🎉 快捷键触发: Ctrl+Shift+Space")
                    print("✅ 快捷键组合测试成功！")
                    hotkey_triggered = True
                    return False  # 停止监听
                    
            except Exception as e:
                print(f"错误: {e}")
        
        def on_release(key):
            try:
                if hasattr(key, 'char') and key.char:
                    key_name = key.char.lower()
                elif hasattr(key, 'name'):
                    key_name = key.name.lower()
                else:
                    return
                
                if 'ctrl' in key_name:
                    key_name = 'ctrl'
                elif 'shift' in key_name:
                    key_name = 'shift'
                
                current_keys.discard(key_name)
                
                # 按 ESC 退出
                if key == keyboard.Key.esc:
                    return False
                    
            except:
                pass
        
        print()
        print("📢 测试说明:")
        print("   1. 请按下 Ctrl+Shift+Space 组合键")
        print("   2. 如果成功，会显示 '快捷键触发' 消息")
        print("   3. 按 ESC 键退出测试")
        print()
        print("等待快捷键...")
        print("-" * 50)
        
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
        
        print("-" * 50)
        return hotkey_triggered
        
    except Exception as e:
        print(f"❌ 快捷键组合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_admin_privileges():
    """检测是否有管理员权限"""
    print()
    print("=" * 50)
    print("测试 4: 检查管理员权限")
    print("=" * 50)
    
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        
        if is_admin:
            print("✅ 当前以管理员权限运行")
        else:
            print("⚠️  当前没有管理员权限")
            print("   提示: 全局快捷键可能需要管理员权限")
            print("   建议: 右键点击程序 → '以管理员身份运行'")
        
        return is_admin
    except Exception as e:
        print(f"⚠️  无法检测管理员权限: {e}")
        return None


def main():
    """主测试流程"""
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║     QuickNote AI - 快捷键功能测试工具             ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    # 测试 1: 依赖库
    deps_ok = test_imports()
    
    if not deps_ok:
        print()
        print("❌ 依赖检查失败！")
        print()
        print("解决方法:")
        print("  pip install pywin32 pynput")
        print()
        input("按 Enter 键退出...")
        sys.exit(1)
    
    # 测试 4: 管理员权限
    is_admin = test_admin_privileges()
    
    # 测试 2: 键盘监听
    listener_ok = test_keyboard_listener()
    
    if not listener_ok:
        print()
        print("⚠️  键盘监听测试有问题")
        print()
        if not is_admin:
            print("建议: 以管理员权限重新运行此测试")
        print()
        retry = input("是否继续测试快捷键组合? (y/n): ")
        if retry.lower() != 'y':
            sys.exit(1)
    
    # 测试 3: 快捷键组合
    hotkey_ok = test_hotkey_combination()
    
    # 总结
    print()
    print("=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"依赖库检查:      {'✅ 通过' if deps_ok else '❌ 失败'}")
    print(f"管理员权限:      {'✅ 有' if is_admin else '⚠️  无'}")
    print(f"键盘监听:        {'✅ 正常' if listener_ok else '❌ 异常'}")
    print(f"快捷键组合:      {'✅ 正常' if hotkey_ok else '⚠️  未测试或失败'}")
    print()
    
    if deps_ok and listener_ok and hotkey_ok:
        print("🎉 所有测试通过！快捷键功能正常！")
        print("   可以放心打包了。")
    elif deps_ok and listener_ok:
        print("⚠️  部分测试通过")
        print("   建议以管理员权限重新测试")
    else:
        print("❌ 测试失败")
        print()
        print("可能的解决方法:")
        print("1. 安装依赖: pip install pywin32 pynput")
        print("2. 以管理员权限运行此脚本")
        print("3. 重启计算机后重试")
    
    print()
    input("按 Enter 键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 键退出...")

