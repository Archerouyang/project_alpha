"""
指令验证性能测试
测试本地预处理 + 缓存优化的效果
"""
import asyncio
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.instruction_validator import validate_and_extract_command, clear_instruction_cache, get_cache_stats

async def test_instruction_performance():
    """测试指令验证的性能优化效果"""
    
    print("🚀 指令验证性能测试开始...")
    
    # 清空缓存
    clear_instruction_cache()
    
    # 测试用例：从简单到复杂
    test_cases = [
        # 本地处理的简单格式（应该很快）
        "AAPL",
        "TSLA",  
        "MSFT",
        "AAPL 1h",
        "TSLA 4h",
        "BTC-USD KRAKEN 1h",
        
        # 需要LLM处理的复杂格式
        "我想看看苹果公司的股票",
        "特斯拉最近怎么样",
        "帮我分析一下比特币",
        "给我写首诗",  # 无关请求
    ]
    
    results = []
    
    for i, test_input in enumerate(test_cases):
        print(f"\n📊 测试 {i+1}/{len(test_cases)}: '{test_input}'")
        
        # 第一次调用（可能缓存未命中）
        start_time = time.time()
        result = await validate_and_extract_command(test_input)
        first_duration = time.time() - start_time
        
        # 第二次调用（应该缓存命中）
        start_time = time.time()
        result_cached = await validate_and_extract_command(test_input)
        second_duration = time.time() - start_time
        
        # 验证两次结果一致
        assert result == result_cached, "缓存结果不一致！"
        
        results.append({
            "input": test_input,
            "first_call": first_duration,
            "cached_call": second_duration,
            "speedup": first_duration / max(second_duration, 0.001),
            "status": result["status"],
            "used_llm": first_duration > 0.1  # 估算是否使用了LLM
        })
        
        print(f"   📈 首次: {first_duration:.3f}s | 缓存: {second_duration:.3f}s | 提速: {first_duration/max(second_duration, 0.001):.1f}x")
        print(f"   ✅ 状态: {result['status']}")
        if result["command"]:
            print(f"   📝 命令: {result['command']}")
    
    # 汇总统计
    print(f"\n📊 === 性能测试汇总 ===")
    cache_stats = get_cache_stats()
    print(f"缓存条目数: {cache_stats['cached_instructions']}")
    
    local_processed = [r for r in results if not r["used_llm"]]
    llm_processed = [r for r in results if r["used_llm"]]
    
    print(f"\n🔥 本地处理 ({len(local_processed)}个):")
    if local_processed:
        avg_local = sum(r["first_call"] for r in local_processed) / len(local_processed)
        print(f"   平均响应时间: {avg_local:.3f}s")
        print(f"   最快: {min(r['first_call'] for r in local_processed):.3f}s")
        print(f"   最慢: {max(r['first_call'] for r in local_processed):.3f}s")
    
    print(f"\n🧠 LLM处理 ({len(llm_processed)}个):")
    if llm_processed:
        avg_llm = sum(r["first_call"] for r in llm_processed) / len(llm_processed)
        print(f"   平均响应时间: {avg_llm:.3f}s")
        print(f"   最快: {min(r['first_call'] for r in llm_processed):.3f}s")
        print(f"   最慢: {max(r['first_call'] for r in llm_processed):.3f}s")
    
    print(f"\n⚡ 缓存效果:")
    avg_first = sum(r["first_call"] for r in results) / len(results)
    avg_cached = sum(r["cached_call"] for r in results) / len(results)
    print(f"   首次平均: {avg_first:.3f}s")
    print(f"   缓存平均: {avg_cached:.3f}s")
    print(f"   整体提速: {avg_first/max(avg_cached, 0.001):.1f}x")
    
    # 显示优化建议
    slow_cases = [r for r in results if r["first_call"] > 1.0]
    if slow_cases:
        print(f"\n⚠️  慢查询 (>1s):")
        for case in slow_cases:
            print(f"   '{case['input']}': {case['first_call']:.3f}s")
    
    print(f"\n🎉 测试完成！智能缓存系统运行正常。")

if __name__ == "__main__":
    asyncio.run(test_instruction_performance()) 