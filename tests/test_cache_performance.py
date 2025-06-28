# tests/test_cache_performance.py
import asyncio
import time
import os
import sys
from typing import List, Dict, Any

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from backend.core.orchestrator import AnalysisOrchestrator
from backend.core.smart_cache import get_cache
from backend.core.performance_monitor import get_monitor

class CachePerformanceTester:
    """
    缓存性能测试器
    测试首次请求vs缓存命中的性能差异
    验证不同TTL设置的效果
    压力测试缓存系统稳定性
    """
    
    def __init__(self):
        self.orchestrator = AnalysisOrchestrator()
        self.cache = get_cache()
        self.monitor = get_monitor()
        self.test_results = []
    
    async def test_cache_performance(self, ticker: str = "AAPL", interval: str = "1d", num_candles: int = 100):
        """测试缓存性能"""
        print(f"🧪 === Cache Performance Test for {ticker} ===")
        
        # 清理现有缓存确保干净测试
        self.cache.clear_all_cache()
        self.monitor.reset_stats()
        
        # 第一次请求（预期缓存未命中）
        print(f"\n📊 First Request (Expected Cache MISS)")
        start_time = time.time()
        
        result1, message1 = await self.orchestrator.generate_report(ticker, interval, num_candles, None)
        
        first_duration = time.time() - start_time
        
        if not result1:
            print(f"❌ First request failed: {message1}")
            return None
        
        print(f"✅ First request completed in {first_duration:.2f}s")
        
        # 等待短暂时间
        await asyncio.sleep(1)
        
        # 第二次请求（预期缓存命中）
        print(f"\n⚡ Second Request (Expected Cache HIT)")
        start_time = time.time()
        
        result2, message2 = await self.orchestrator.generate_report(ticker, interval, num_candles, None)
        
        second_duration = time.time() - start_time
        
        if not result2:
            print(f"❌ Second request failed: {message2}")
            return None
        
        print(f"✅ Second request completed in {second_duration:.2f}s")
        
        # 计算性能提升
        if first_duration > 0:
            improvement = ((first_duration - second_duration) / first_duration) * 100
            speedup = first_duration / second_duration if second_duration > 0 else float('inf')
        else:
            improvement = 0
            speedup = 1
        
        test_result = {
            'ticker': ticker,
            'interval': interval,
            'first_duration': first_duration,
            'second_duration': second_duration,
            'improvement_percent': improvement,
            'speedup_factor': speedup,
            'cache_stats': self.cache.get_cache_stats(),
            'hit_rates': self.monitor.get_cache_hit_rates()
        }
        
        self.test_results.append(test_result)
        
        print(f"\n📈 Performance Results:")
        print(f"   First request (cache miss): {first_duration:.2f}s")
        print(f"   Second request (cache hit): {second_duration:.2f}s")
        print(f"   🚀 Performance improvement: {improvement:.1f}%")
        print(f"   ⚡ Speedup factor: {speedup:.1f}x")
        
        return test_result
    
    async def test_multiple_symbols(self, symbols: List[str] = ["AAPL", "MSFT", "GOOGL"], interval: str = "1d"):
        """测试多个股票的缓存效果"""
        print(f"\n🔄 === Multi-Symbol Cache Test ===")
        
        results = []
        
        for symbol in symbols:
            print(f"\n🎯 Testing {symbol}...")
            result = await self.test_cache_performance(symbol, interval, 50)
            if result:
                results.append(result)
            
            # 短暂延迟避免API限制
            await asyncio.sleep(2)
        
        return results
    
    async def test_cache_expiration(self, ticker: str = "TSLA", interval: str = "1d"):
        """测试缓存过期机制"""
        print(f"\n⏰ === Cache Expiration Test ===")
        
        # 设置短暂的TTL用于测试（需要修改配置）
        print(f"Testing with ticker {ticker}")
        
        # 第一次请求
        start_time = time.time()
        result1, _ = await self.orchestrator.generate_report(ticker, interval, 50, None)
        first_duration = time.time() - start_time
        
        if not result1:
            print("❌ First request failed")
            return
        
        print(f"✅ First request: {first_duration:.2f}s")
        
        # 立即第二次请求（应该命中缓存）
        start_time = time.time()
        result2, _ = await self.orchestrator.generate_report(ticker, interval, 50, None)
        cached_duration = time.time() - start_time
        
        print(f"✅ Cached request: {cached_duration:.2f}s")
        
        # 手动清理过期缓存
        print("\n🧹 Manually clearing expired cache...")
        cleared_count = self.cache.clear_expired_cache()
        print(f"Cleared {cleared_count} entries")
        
        # 第三次请求（缓存可能已清理）
        start_time = time.time()
        result3, _ = await self.orchestrator.generate_report(ticker, interval, 50, None)
        after_clear_duration = time.time() - start_time
        
        print(f"✅ After clear request: {after_clear_duration:.2f}s")
        
        return {
            'first_duration': first_duration,
            'cached_duration': cached_duration,
            'after_clear_duration': after_clear_duration,
            'cleared_count': cleared_count
        }
    
    def generate_performance_report(self) -> str:
        """生成详细的性能测试报告"""
        if not self.test_results:
            return "No test results available."
        
        report_lines = [
            "=== 缓存性能测试报告 ===",
            f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"测试样本数: {len(self.test_results)}",
            ""
        ]
        
        total_improvement = 0
        total_speedup = 0
        
        for i, result in enumerate(self.test_results, 1):
            report_lines.extend([
                f"📊 测试 #{i}: {result['ticker']} ({result['interval']})",
                f"   首次请求: {result['first_duration']:.2f}s",
                f"   缓存命中: {result['second_duration']:.2f}s",
                f"   性能提升: {result['improvement_percent']:.1f}%",
                f"   加速倍数: {result['speedup_factor']:.1f}x",
                ""
            ])
            
            total_improvement += result['improvement_percent']
            total_speedup += result['speedup_factor']
        
        # 计算平均值
        avg_improvement = total_improvement / len(self.test_results)
        avg_speedup = total_speedup / len(self.test_results)
        
        report_lines.extend([
            "📈 总体统计:",
            f"   平均性能提升: {avg_improvement:.1f}%",
            f"   平均加速倍数: {avg_speedup:.1f}x",
            ""
        ])
        
        # 添加缓存命中率统计
        if self.test_results:
            last_hit_rates = self.test_results[-1]['hit_rates']
            report_lines.extend([
                "🎯 缓存命中率:",
                f"   数据获取: {last_hit_rates.get('data', 0):.1f}%",
                f"   图表生成: {last_hit_rates.get('chart', 0):.1f}%",
                f"   AI分析: {last_hit_rates.get('analysis', 0):.1f}%",
                ""
            ])
        
        # 性能评估
        report_lines.extend([
            "💡 性能评估:"
        ])
        
        if avg_improvement > 80:
            report_lines.append("   ✅ 缓存效果优秀，性能提升显著")
        elif avg_improvement > 50:
            report_lines.append("   📈 缓存效果良好，达到预期目标")
        elif avg_improvement > 20:
            report_lines.append("   ⚠️ 缓存效果一般，可能需要调优")
        else:
            report_lines.append("   ❌ 缓存效果不理想，需要检查配置")
        
        if avg_speedup > 5:
            report_lines.append("   🚀 加速效果突出，用户体验大幅提升")
        elif avg_speedup > 2:
            report_lines.append("   ⚡ 加速效果良好，用户体验明显改善")
        else:
            report_lines.append("   📊 加速效果有限，建议进一步优化")
        
        return "\n".join(report_lines)

async def main():
    """主测试函数"""
    print("🚀 Starting Cache Performance Tests...")
    
    tester = CachePerformanceTester()
    
    try:
        # 单个股票测试
        print("\n=== Single Stock Test ===")
        await tester.test_cache_performance("AAPL", "1d", 100)
        
        # 多股票测试
        print("\n=== Multi-Stock Test ===")
        await tester.test_multiple_symbols(["MSFT", "GOOGL"], "1d")
        
        # 缓存过期测试
        print("\n=== Cache Expiration Test ===")
        await tester.test_cache_expiration("TSLA", "1d")
        
        # 生成最终报告
        print("\n" + "="*60)
        final_report = tester.generate_performance_report()
        print(final_report)
        
        # 保存报告到文件
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        report_file = f"cache_performance_test_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(final_report)
        print(f"\n📄 Performance report saved to: {report_file}")
        
        # 显示系统性能监控报告
        performance_report = tester.monitor.generate_report()
        print(f"\n📊 System Performance Report:")
        print(performance_report)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 