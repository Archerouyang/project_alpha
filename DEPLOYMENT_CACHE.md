# 缓存系统部署指南

## 📋 概述

本项目使用智能缓存系统来显著提升性能，但缓存数据不应该被版本控制。本文档说明如何在不同环境中正确管理缓存。

## 🏗️ 架构设计

```
cache_data/
├── data/       # API数据缓存 (TTL: 5分钟)
├── chart/      # 图表缓存 (TTL: 10分钟)  
└── analysis/   # AI分析缓存 (TTL: 30分钟)
```

## ☁️ 云端部署策略

### 1. 缓存数据处理原则

✅ **应该做的:**
- 缓存目录在每个环境中自动创建
- 缓存在运行时自动生成
- 定期清理过期缓存
- 监控缓存性能

❌ **不应该做的:**
- 将缓存文件提交到git
- 在环境间同步缓存文件
- 手动管理缓存文件

### 2. 新环境初始化

```bash
# 1. 克隆代码（不包含缓存）
git clone <repository>
cd project_alpha

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化缓存目录
python scripts/cache_manager.py init

# 4. 启动应用（缓存自动生成）
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Docker部署配置

```dockerfile
# Dockerfile 中的建议配置
FROM python:3.11

WORKDIR /app
COPY . .

# 安装依赖
RUN pip install -r requirements.txt

# 创建缓存目录（但不复制缓存文件）
RUN mkdir -p cache_data/{data,chart,analysis}

# 启动应用
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🛠️ 缓存管理工具

### 使用缓存管理器

```bash
# 查看缓存状态
python scripts/cache_manager.py status

# 清理所有缓存
python scripts/cache_manager.py clear

# 清理特定类别缓存
python scripts/cache_manager.py clear --category data

# 清理过期缓存（推荐）
python scripts/cache_manager.py clear-expired

# 初始化缓存目录
python scripts/cache_manager.py init
```

### API端点管理

```bash
# 获取缓存统计
curl http://localhost:8000/api/cache/stats

# 清理过期缓存
curl -X POST http://localhost:8000/api/cache/clear

# 清空所有缓存（调试用）
curl -X DELETE http://localhost:8000/api/cache/all
```

## 📊 性能监控

### 缓存命中率监控

```bash
# 获取性能统计
curl http://localhost:8000/api/performance/stats

# 获取详细报告
curl http://localhost:8000/api/performance/report
```

### 预期性能指标

| 场景 | 目标命中率 | 预期响应时间 |
|------|------------|--------------|
| 数据缓存 | 70%+ | 数据获取: <0.1s |
| 图表缓存 | 60%+ | 图表生成: <0.5s |
| 分析缓存 | 80%+ | AI分析: <0.1s |

## 🔧 维护任务

### 日常维护

```bash
# 每日执行 - 清理过期缓存
0 2 * * * /path/to/project/scripts/cache_manager.py clear-expired

# 每周执行 - 检查缓存状态
0 9 * * 1 /path/to/project/scripts/cache_manager.py status
```

### 故障排除

**问题1: 缓存目录不存在**
```bash
python scripts/cache_manager.py init
```

**问题2: 缓存占用空间过大**
```bash
python scripts/cache_manager.py status  # 检查大小
python scripts/cache_manager.py clear   # 清理缓存
```

**问题3: 性能下降**
```bash
# 检查缓存命中率
curl http://localhost:8000/api/performance/stats
# 重置性能计数器
curl -X POST http://localhost:8000/api/performance/reset
```

## 🚀 云服务器部署清单

### 部署前检查

- [ ] `.gitignore` 包含 `cache_data/`
- [ ] 环境变量配置完整
- [ ] 依赖包安装完成
- [ ] 缓存目录权限正确

### 部署后验证

- [ ] 缓存目录自动创建
- [ ] API健康检查通过: `/api/health`
- [ ] 首次查询成功生成缓存
- [ ] 第二次查询命中缓存

### 生产环境建议

1. **监控设置**
   - 设置缓存命中率告警（<50%）
   - 监控磁盘空间使用
   - 定期检查应用性能

2. **备份策略**
   - 代码备份（不包含缓存）
   - 配置文件备份
   - 数据库备份（如果有）

3. **扩展考虑**
   - 多实例部署时缓存不共享
   - 可考虑Redis等外部缓存
   - 负载均衡配置

## 📈 性能优化建议

1. **缓存策略优化**
   - 根据使用模式调整TTL
   - 监控内存使用情况
   - 定期清理过期缓存

2. **存储优化**
   - 使用SSD存储提升性能
   - 定期检查磁盘空间
   - 考虑缓存压缩

3. **网络优化**
   - 使用CDN加速静态资源
   - 优化API响应格式
   - 实现HTTP缓存头

---

**📞 需要帮助？**
- 查看 [README.md](README.md) 了解基本使用
- 运行 `python scripts/cache_manager.py --help` 查看工具帮助
- 访问 `/api/health` 检查系统状态 