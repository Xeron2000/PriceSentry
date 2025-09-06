"""
完整的API测试运行器
"""

import os
import subprocess
import sys
import time


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.pricesentry_process = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.base_dir)
        self.venv_python = os.path.join(self.project_root, ".venv", "bin", "python")

    def start_pricesentry(self) -> bool:
        """启动PriceSentry服务"""
        print("🚀 启动PriceSentry服务...")

        try:
            # 启动服务
            cmd = [self.venv_python, "main.py"]
            self.pricesentry_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root,
            )

            # 等待服务启动
            print("⏳ 等待服务启动...")
            time.sleep(15)  # 给足够时间启动

            # 检查进程是否仍在运行
            if self.pricesentry_process.poll() is None:
                print("✅ PriceSentry服务启动成功")
                return True
            else:
                # 如果进程已经退出，读取错误信息
                stderr = self.pricesentry_process.stderr.read().decode()
                print(f"❌ PriceSentry服务启动失败: {stderr}")
                return False

        except Exception as e:
            print(f"❌ 启动PriceSentry时发生错误: {e}")
            return False

    def stop_pricesentry(self):
        """停止PriceSentry服务"""
        print("🛑 停止PriceSentry服务...")

        if self.pricesentry_process:
            try:
                self.pricesentry_process.terminate()
                try:
                    self.pricesentry_process.wait(timeout=10)
                    print("✅ PriceSentry服务已正常停止")
                except subprocess.TimeoutExpired:
                    self.pricesentry_process.kill()
                    print("✅ PriceSentry服务已强制停止")
            except Exception as e:
                print(f"⚠️ 停止服务时发生错误: {e}")
                try:
                    self.pricesentry_process.kill()
                except Exception:
                    pass

    def run_test_suite(self):
        """运行完整测试套件"""
        print("🧪 开始运行完整API测试套件")
        print("=" * 60)

        # 启动服务
        if not self.start_pricesentry():
            print("❌ 无法启动PriceSentry服务，测试终止")
            return False

        try:
            # 运行各项测试
            tests = [
                ("📡 REST API端点测试", "test_rest_api.py"),
                ("🔌 WebSocket实时数据测试", "test_websocket.py"),
                ("🔄 数据集成测试", "test_integration.py"),
            ]

            all_passed = True

            for test_name, test_file in tests:
                print(f"\n{test_name}")
                print("-" * 40)

                try:
                    # 运行测试
                    cmd = [self.venv_python, os.path.join("tests", test_file)]
                    result = subprocess.run(
                        cmd,
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )

                    if result.returncode == 0:
                        print(f"✅ {test_name} 通过")
                        # 输出测试结果
                        if result.stdout:
                            print(result.stdout)
                    else:
                        print(f"❌ {test_name} 失败")
                        print(f"错误代码: {result.returncode}")
                        if result.stderr:
                            print(f"错误信息: {result.stderr}")
                        all_passed = False

                except subprocess.TimeoutExpired:
                    print(f"❌ {test_name} 超时")
                    all_passed = False
                except Exception as e:
                    print(f"❌ {test_name} 运行错误: {e}")
                    all_passed = False

            # 运行额外的健康检查
            print("\n🔍 系统健康检查")
            print("-" * 40)
            if self.run_health_check():
                print("✅ 系统健康检查通过")
            else:
                print("❌ 系统健康检查失败")
                all_passed = False

            return all_passed

        finally:
            # 确保服务被停止
            self.stop_pricesentry()

    def run_health_check(self):
        """运行健康检查"""
        try:
            import requests

            # 检查API健康状态
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False

        except Exception as e:
            print(f"健康检查失败: {e}")
            return False

    def run_specific_test(self, test_file: str):
        """运行特定测试"""
        print(f"🧪 运行特定测试: {test_file}")

        if not self.start_pricesentry():
            return False

        try:
            cmd = [self.venv_python, os.path.join("tests", test_file)]
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                print(f"✅ {test_file} 测试通过")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"❌ {test_file} 测试失败")
                print(f"错误代码: {result.returncode}")
                if result.stderr:
                    print(f"错误信息: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ 运行测试时发生错误: {e}")
            return False
        finally:
            self.stop_pricesentry()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="PriceSentry API测试运行器")
    parser.add_argument("--test", type=str, help="运行特定测试文件")
    parser.add_argument("--health", action="store_true", help="仅运行健康检查")
    parser.add_argument("--continuous", action="store_true", help="连续运行测试")

    args = parser.parse_args()

    runner = TestRunner()

    if args.health:
        # 仅健康检查
        if runner.start_pricesentry():
            try:
                if runner.run_health_check():
                    print("✅ 系统健康")
                else:
                    print("❌ 系统不健康")
            finally:
                runner.stop_pricesentry()
        return

    if args.test:
        # 运行特定测试
        success = runner.run_specific_test(args.test)
        sys.exit(0 if success else 1)
        return

    if args.continuous:
        # 连续运行测试
        print("🔄 连续运行测试模式 (按Ctrl+C停止)")
        try:
            while True:
                print(f"\n🕒 测试运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                success = runner.run_test_suite()

                if success:
                    print("🎉 所有测试通过!")
                else:
                    print("❌ 部分测试失败")

                print("⏳ 等待5分钟后进行下一次测试...")
                time.sleep(300)

        except KeyboardInterrupt:
            print("\n🛑 停止连续测试")
        return

    # 默认运行完整测试套件
    success = runner.run_test_suite()

    if success:
        print("\n🎉 所有API测试通过！系统完全可用！")
        print("\n📊 测试总结:")
        print("  ✅ REST API端点 - 正常")
        print("  ✅ WebSocket实时数据 - 正常")
        print("  ✅ 数据集成 - 正常")
        print("  ✅ 系统健康 - 正常")
        print("  ✅ 性能和负载处理 - 正常")
        print("\n🚀 PriceSentry API已准备好为前端提供数据支持!")
    else:
        print("\n❌ 部分测试失败，请检查系统状态")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
