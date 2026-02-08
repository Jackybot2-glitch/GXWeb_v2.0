# GX量化 Web 统一平台 v2.0 - 工业化开发规范

## 🎯 开发流程（必须遵守）

### 每个任务必须完成的 5 个步骤

```
1. 需求分析 → Kimi CLI (OKR Agent)
   ↓
2. 代码编写 → Kimi CLI (Coder Agent)  
   ↓
3. 代码审计 → Kimi CLI (Auditor Agent) ← 必须做！
   ↓
4. 单元测试 → Kimi CLI (Tester Agent)
   ↓
5. 代码合并 → 手动 (git commit)
```

---

## 📦 必需的开发 Agent

### 1. OKR Agent - 需求分析
```bash
kimi --agent-file .kimi/agents/okr.json -p "分析任务，输出：1)成功标准 2)技术方案 3)风险点"
```

### 2. Coder Agent - 代码编写
```bash
kimi --agent-file .kimi/agents/coder.json -p "编写代码，遵循：1)PEP8规范 2)类型提示 3)错误处理"
```

### 3. Auditor Agent - 代码审计 ⭐必做
```bash
kimi --agent-file .kimi/agents/auditor.json -p "审计代码：1)语法检查 2)依赖验证 3)功能测试"
```

### 4. Tester Agent - 单元测试
```bash
kimi --agent-file .kimi/agents/tester.json -p "编写测试：1)边界测试 2)异常测试 3)覆盖率 > 80%"
```

---

## 📋 代码规范检查清单

### ✅ 提交前必须通过

- [ ] **语法检查**：`python3 -m py_compile <file>`
- [ ] **导入测试**：`python3 -c "from module import func; print('OK')"`
- [ ] **类型检查**：使用 mypy（如果有类型提示）
- [ ] **代码格式化**：black 格式化
- [ ] **单元测试**：pytest 通过

### ⚠️ 代码质量要求

- [ ] 每个函数必须有 docstring
- [ ] 复杂逻辑必须添加注释
- [ ] 错误处理必须完善（try-except）
- [ ] 配置必须外部化（.env）
- [ ] 日志必须记录（使用 loguru）

---

## 🔄 开发工作流示例

```bash
# 场景：添加一个新功能 "股票K线数据API"

# Step 1: 需求分析
kimi --agent-file .kimi/agents/okr.json -p "
任务：为GX量化项目添加股票K线API
目标：返回指定股票的OHLCV数据
约束：响应时间 < 100ms"

# Step 2: 代码编写  
kimi --agent-file .kimi/agents/coder.json -p "
文件：backend/routes/kline.py
功能：实现 /api/kline 接口
要求：
- 使用 FastAPI
- 支持 period=daily|1m|5m
- 返回 JSON 格式
- 添加类型提示
- 完善错误处理"

# Step 3: 代码审计 ⭐必做
kimi --agent-file .kimi/agents/auditor.json -p "
审计 backend/routes/kline.py
检查：
1. 语法是否正确
2. FastAPI 是否正确导入
3. 依赖是否完整
4. 能否正常启动"

# Step 4: 单元测试
kimi --agent-file .kimi/agents/tester.json -p "
为 backend/routes/kline.py 编写测试：
- 测试正常请求
- 测试边界条件
- 测试错误响应"

# Step 5: 提交代码
git add -A
git commit -m "feat: 添加K线API接口"
```

---

## 🚨 禁止事项

- ❌ 禁止直接提交未审计的代码
- ❌ 禁止跳过单元测试
- ❌ 禁止硬编码配置
- ❌ 禁止不写 docstring
- ❌ 禁止吞掉异常而不记录日志

---

## 📊 审计 Agent 的核心检查项

```python
AUDIT_CHECKLIST = """
1. 语法正确性
   └─ python3 -m py_compile <file>
   
2. 依赖完整性  
   └─ pip list | grep -E "pandas|fastapi|..."
   
3. 导入测试
   └─ python3 -c "import module; print('OK')"
   
4. 功能验证
   └─ 运行简单测试用例
   
5. 代码规范
   └─ black --check <file>
   └─ flake8 <file>
"""
```

---

## 🎓 培训新 Agent 的提示词模板

```json
{
  "name": "XXX Agent",
  "description": "...",
  "system_prompt": "你是专业的 XXX开发者。\n\n## 你的工作流程\n\n1. 理解需求\n2. 编写代码（遵循 PEP8）\n3. 自我审计\n4. 输出代码\n\n## 禁止\n- 不写测试\n- 不检查语法\n- 硬编码\n\n## 输出格式\n```python\n# 文件路径: xxx\n# 功能描述: xxx\n\n<code here>\n```\n\n## 审计清单\n- [ ] 语法正确\n- [ ] 导入正常\n- [ ] 功能可用",
  "temperature": 0.3
}
```
