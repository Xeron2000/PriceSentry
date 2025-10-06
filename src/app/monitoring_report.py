#!/usr/bin/env python3
"""
PriceSentry 监控报告生成器
生成缓存和性能监控的详细报告
"""

import json
from datetime import datetime

from utils.cache_manager import price_cache
from utils.performance_monitor import performance_monitor


def generate_monitoring_report():
    """生成监控报告"""
    print("=" * 60)
    print("           PriceSentry 监控报告")
    print("=" * 60)
    print(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 获取监控数据
    cache_stats = price_cache.get_stats()
    perf_stats = performance_monitor.get_stats()

    # 缓存管理器报告
    print("📊 缓存管理器报告")
    print("-" * 40)
    print(f"缓存策略: {cache_stats['strategy'].upper()}")
    print(f"当前大小: {cache_stats['size']}/{cache_stats['max_size']}")
    print(f"总条目数: {cache_stats['total_entries']}")
    print(f"命中率: {cache_stats['hit_rate']}")
    print(f"命中次数: {cache_stats['hits']}")
    print(f"未命中次数: {cache_stats['misses']}")
    print(f"驱逐次数: {cache_stats['evictions']}")
    print(f"过期次数: {cache_stats['expirations']}")
    print(f"平均访问时间: {cache_stats['avg_access_time_ms']} ms")
    print(f"估计内存使用: {cache_stats['estimated_memory_bytes']} bytes")
    print(f"运行时间: {cache_stats['uptime_seconds']:.3f} 秒")
    print(f"默认TTL: {cache_stats['default_ttl']} 秒")
    print()

    # 性能监控器报告
    print("⚡ 性能监控器报告")
    print("-" * 40)
    print(f"运行时间: {perf_stats['uptime_seconds']:.3f} 秒")
    print(f"收集的指标数: {perf_stats['metrics_collected']}")
    print(f"系统快照数: {perf_stats['system_snapshots']}")
    print(f"活跃定时器: {perf_stats['active_timers']}")
    print(f"自定义指标: {perf_stats['custom_metrics']}")
    print(f"计数器: {perf_stats['counters']}")
    print(f"直方图: {perf_stats['histograms']}")
    print(f"最近CPU平均: {perf_stats['recent_cpu_avg']:.1f}%")
    print(f"最近内存平均: {perf_stats['recent_memory_avg_mb']:.2f} MB")
    print(f"峰值内存: {perf_stats['peak_memory_mb']:.2f} MB")
    print(f"峰值CPU: {perf_stats['peak_cpu_percent']:.1f}%")
    print()

    # 系统状态
    print("🖥️  系统状态")
    print("-" * 40)
    monitor_status = "🟢 运行中" if performance_monitor._running else "🔴 已停止"
    print(f"监控器运行状态: {monitor_status}")
    if performance_monitor._collection_thread:
        thread_status = (
            "🟢 活跃"
            if performance_monitor._collection_thread.is_alive()
            else "🔴 非活跃"
        )
        print(f"收集线程状态: {thread_status}")
    else:
        print("收集线程状态: 🔴 未启动")
    print()

    # 健康检查
    print("🏥 系统健康检查")
    print("-" * 40)

    # 缓存健康检查
    cache_health = "🟢 健康"
    if cache_stats["hit_rate"] == "0.00%" and cache_stats["total_entries"] > 0:
        cache_health = "🟡 警告 (命中率为0)"
    elif cache_stats["evictions"] > 100:
        cache_health = "🟡 警告 (驱逐次数过多)"

    print(f"缓存健康状态: {cache_health}")

    # 性能健康检查
    perf_health = "🟢 健康"
    if perf_stats["recent_cpu_avg"] > 80:
        perf_health = "🟡 警告 (CPU使用率过高)"
    elif perf_stats["recent_memory_avg_mb"] > 500:
        perf_health = "🟡 警告 (内存使用过高)"

    print(f"性能健康状态: {perf_health}")

    # 整体状态
    overall_health = "🟢 健康"
    if cache_health != "🟢 健康" or perf_health != "🟢 健康":
        overall_health = "🟡 需要关注"

    print(f"整体系统状态: {overall_health}")
    print()

    # 建议
    print("💡 优化建议")
    print("-" * 40)

    if cache_stats["hit_rate"] == "0.00%" and cache_stats["total_entries"] > 0:
        print("- 考虑调整缓存策略或TTL设置")

    if perf_stats["recent_cpu_avg"] > 80:
        print("- CPU使用率过高，考虑优化算法或减少监控频率")

    if perf_stats["recent_memory_avg_mb"] > 500:
        print("- 内存使用过高，考虑清理缓存或调整监控参数")

    if cache_stats["evictions"] > 100:
        print("- 缓存驱逐次数过多，考虑增加缓存大小")

    if perf_stats["system_snapshots"] == 0:
        print("- 系统快照为空，确保性能监控器正常启动")

    if not performance_monitor._running:
        print("- 性能监控器未运行，请检查配置")

    print()

    # 导出JSON报告
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "cache_stats": cache_stats,
        "performance_stats": perf_stats,
        "system_status": {
            "monitor_running": performance_monitor._running,
            "collection_thread_alive": performance_monitor._collection_thread.is_alive()
            if performance_monitor._collection_thread
            else False,
        },
        "health_status": {
            "cache": cache_health,
            "performance": perf_health,
            "overall": overall_health,
        },
    }

    # 保存报告到文件
    with open("monitoring_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print("📄 监控报告已保存到: monitoring_report.json")
    print("=" * 60)


if __name__ == "__main__":
    generate_monitoring_report()
