#!/usr/bin/env python3
"""
PriceSentry 监控仪表板
展示缓存管理和性能监控的实时状态
"""

import time

from utils.cache_manager import price_cache
from utils.performance_monitor import performance_monitor


def clear_screen():
    """清空终端屏幕"""
    print("\033[2J\033[H", end="")


def display_monitoring_dashboard():
    """显示监控仪表板"""
    while True:
        try:
            clear_screen()

            # 获取监控数据
            cache_stats = price_cache.get_stats()
            perf_stats = performance_monitor.get_stats()

            # 显示标题
            print("=" * 60)
            print("           PriceSentry 监控仪表板")
            print("=" * 60)
            print(f"更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # 缓存管理器状态
            print("📊 缓存管理器状态")
            print("-" * 40)
            print(f"  缓存大小: {cache_stats['size']}/{cache_stats['max_size']}")
            print(f"  总条目数: {cache_stats['total_entries']}")
            print(f"  命中率: {cache_stats['hit_rate']}")
            print(f"  命中次数: {cache_stats['hits']}")
            print(f"  未命中次数: {cache_stats['misses']}")
            print(f"  驱逐次数: {cache_stats['evictions']}")
            print(f"  过期次数: {cache_stats['expirations']}")
            print(f"  平均访问时间: {cache_stats['avg_access_time_ms']} ms")
            print(f"  估计内存使用: {cache_stats['estimated_memory_bytes']} bytes")
            print(f"  运行时间: {cache_stats['uptime_seconds']:.3f} 秒")
            print(f"  默认TTL: {cache_stats['default_ttl']} 秒")
            print()

            # 性能监控器状态
            print("⚡ 性能监控器状态")
            print("-" * 40)
            print(f"  运行时间: {perf_stats['uptime_seconds']:.3f} 秒")
            print(f"  收集的指标数: {perf_stats['metrics_collected']}")
            print(f"  系统快照数: {perf_stats['system_snapshots']}")
            print(f"  活跃定时器: {perf_stats['active_timers']}")
            print(f"  自定义指标: {perf_stats['custom_metrics']}")
            print(f"  计数器: {perf_stats['counters']}")
            print(f"  直方图: {perf_stats['histograms']}")
            print(f"  最近CPU平均: {perf_stats['recent_cpu_avg']:.1f}%")
            print(f"  最近内存平均: {perf_stats['recent_memory_avg_mb']:.2f} MB")
            print(f"  峰值内存: {perf_stats['peak_memory_mb']:.2f} MB")
            print(f"  峰值CPU: {perf_stats['peak_cpu_percent']:.1f}%")
            print()

            # 系统状态
            print("🖥️  系统状态")
            print("-" * 40)
            monitor_status = (
                "🟢 运行中" if performance_monitor._running else "🔴 已停止"
            )
            print(f"  监控器运行状态: {monitor_status}")

            thread_alive = (
                performance_monitor._collection_thread
                and performance_monitor._collection_thread.is_alive()
            )
            thread_status = "🟢 活跃" if thread_alive else "🔴 非活跃"
            print(f"  收集线程状态: {thread_status}")
            print()

            print("按 Ctrl+C 退出监控...")

            # 等待更新
            time.sleep(2)

        except KeyboardInterrupt:
            print("\n\n监控仪表板已停止")
            break
        except Exception as e:
            print(f"监控仪表板错误: {e}")
            time.sleep(1)


if __name__ == "__main__":
    print("启动 PriceSentry 监控仪表板...")
    display_monitoring_dashboard()
