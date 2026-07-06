# HaidianParent.skill (Codename: HaidianMatrix)

> **家庭教育与儿童成长全生命周期数字资产管理系统 (海淀父母版 - MVP v1.0.0)**

[![Code License: MIT](https://img.shields.io/badge/Code_License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Content License: CC BY-NC-SA 4.0](https://img.shields.io/badge/Content_License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Status](https://img.shields.io/badge/Status-Beta--v1.1.0-blue.svg)]()
[![重构版本](https://img.shields.io/badge/重构-CrewAI多智能体架构-critical)]()

---

## 🔄 重要重构声明 (2026年7月)

鉴于AI Agent 技术的爆发式演进，本项目已进行**彻底的底层重构**。旧有代码因单文件 Prompt 堆叠、缺乏物理约束审计，无法应对高频政策波动和极端精确度要求，现决定**彻底抛弃旧有业务实现代码，仅保留原项目的版权声明、资产归属与核心说明文档**。

**重构的核心宗旨**：引入现代多智能体协同框架与刚性规则引擎，将"育儿玄学"全面解构为可审计、可优化、无幻觉的"工程项目管理问题"。

---

## 🏗️ 全新四层架构 (重构版本 v1.1.0)

重构后的系统由四层核心骨架构成，明确划分了大模型概率推演与 Python 刚性计算的边界：

### 1. 外壳容器层 (CrewAI)
负责多智能体（Agents）角色定义、提示词（Prompt）隔离、任务流（Tasks）协同网络编排及 MCP 接口映射，不承载底层大模型黑盒逻辑。

### 2. 核心基座层 (Hermes)
作为 CrewAI 容器内所有核心 Agent 的默认大模型基座。利用其长上下文（Long-context）推理特长，负责非结构化经验归因、情感/行为状态跟踪及长周期策略连续性维护。

### 3. 硬编码控制层 (Python Engine)
针对涉及物理限制（如时间冲突、财务预算）、多校录取概率辩论等高风险决策，由纯 Python 编写的决策树与规则引擎进行硬性拦截和结果审计，拒绝 LLM 模糊输出。

### 4. 数据与接口层 (MCP)
基于 Model Context Protocol 协议，将海淀升学政策知识库、学生历史错题本、家庭物理日历抽象为标准服务，作为 Skill 注入容器。

```mermaid
flowchart TD
    U[家长输入] --> C[CrewAI 容器层<br/>多智能体编排]
    C --> A1[“政策审计员 Agent<br/>Hermes 基座”]
    C --> A2[“升学规划专家 Agent<br/>Hermes 基座”]
    C --> A3[“辩论沙箱 Agents<br/>保守派 vs 激进派”]
    
    A1 --> MCP[MCP 协议层<br/>政策 PDF/Notion 数据]
    A2 --> PE[“Python 硬编码引擎<br/>物理约束审计”]
    A3 --> DS[“辩论沙箱<br/>3轮刚性对话”]
    
    PE --> VC{约束验证}
    VC -->|通过| O[结构化输出]
    VC -->|拒绝| R[强制重新生成]
    
    DS --> DR[《决策博弈审计报告》]
```

## 📁 重构后目录结构

```
HaidianParent.skill/
├── copyright.txt                    # 版权与资产归属说明（唯一保留的旧版文档）
├── README.md                        # 本文件
├── LICENSE-CODE-MIT                 # 代码 MIT 许可证
├── LICENSE-CONTENT-CC-BY-NC-SA-4.0  # 内容 CC BY-NC-SA 4.0 许可证
├── skill.json                       # Zoo 舱单元数据
│
├── config/                          # 声明式配置（重构新增）
│   ├── agents.yaml                  # 多智能体角色、环境与信任域配置
│   └── tasks.yaml                   # 任务流水线（政策审计、升学规划、辩论沙箱）
│
├── core/                            # 硬编码控制层（重构新增）
│   ├── __init__.py
│   ├── engine.py                    # 核心控制器：硬编码决策树、约束拦截器
│   └── sandbox.py                   # 辩论沙箱：多Agent竞争冲突解决机制
│
├── tools/                           # 工具层（重构扩展）
│   ├── mcp_bridge.py                # MCP协议桥接器，连接政策PDF/Notion数据
│   ├── custom_skills.py             # 纯Python刚性计算工具（时间漏斗、财务约束）
│   ├── health_ingress.json          # 原有健康工具
│   ├── policy_crawler.json          # 原有政策爬虫
│   └── question_bank_router.json    # 原有题库路由
│
├── main.py                          # 容器启动入口与CrewAI编排逻辑（重构新增）
├── requirements.txt                 # 依赖配置（已更新为重构版本）
│
├── src/                             # 原有引擎实现（MIT授权）
│   └── engines/
│       ├── school_matching.py       # 择校引擎
│       ├── academic_rca.py          # 错题RCA引擎
│       └── physical_performance.py  # 体育引擎
│
├── prompts/                         # 核心提示词（CC BY-NC-SA 4.0）
│   ├── system_prompt.md             # 全局系统提示词
│   └── engines/                     # 引擎专属控制提示词
│
└── schemas/                         # 原有数据Schema
    ├── error_logs_rca.json
    └── user_state.json
```

## 🔧 核心重构功能模块

### 1. 基于RAG与MCP的无噪音政策审计
- **输入边界**：教委官方文件PDF、派位比例表、招生截止时间
- **处理逻辑**：通过MCP接口精确提取无噪点、无情感修饰的一手数据
- **输出要求**：绝对事实陈述报告，严禁包含任何"推测"结论

### 2. 物理边界硬审计（时间/财务约束漏斗）
- **核心公式**：`t_free = 24 - (t_school + t_sleep + t_live)`
- **拦截机制**：当Agent编排的课外网课、奥数刷题、原版阅读时间总和`Σ t_tasks > t_free`时，Python控制层抛出`ConstraintsViolationError`，直接打回任务流，强制Hermes在约束框架内重新生成

### 3. 多Agent竞争辩论沙箱（Debate Sandbox）
- **保守派 (Agent B1)**：基于最低风险、就近派位、财务稳健原则
- **激进派 (Agent B2)**：基于科技特长、跨区加工能力、高收益高风险原则
- **控制机制**：Python硬编码限制双方辩论必须严格执行3轮，最终由Python计分器提取双方论据的交叉验证度

### 4. 记忆双轨制架构（重构防错核心）
1. **严禁全权依赖Hermes的内置大模型记忆记录绝对数字**：统测精确分数、区排名、全区划线指标必须存放在结构化本地JSON字典或轻量级数据库中
2. **释放Hermes的内置记忆特长于非结构化资产**：允许Hermes在长上下文中记忆孩子的性格特质、情绪挫败感、家庭长线教育风格

## 🚀 快速启动（重构版本）

```bash
# 克隆仓库
git clone https://github.com/canglangxifeng/HaidianParent.skill.git

# 进入项目目录
cd HaidianParent.skill

# 安装重构依赖（需更新requirements.txt）
pip install -r requirements.txt

# 启动重构系统
python main.py

# 或运行特定功能
python -c "from main import HaidianParentsAgentSystem; system = HaidianParentsAgentSystem()"
```

## 📊 依赖更新

重构版本新增以下核心依赖：
- `crewai>=0.28.8` - 多智能体协同框架
- `pydantic>=2.0.0` - 数据验证与配置管理
- `mcp>=0.1.0` - Model Context Protocol
- `pyyaml>=6.0` - YAML配置文件解析

## 🧪 测试验证

```bash
# 测试物理时间漏斗分析器
python -c "
from tools.custom_skills import TimeFunnelAnalyzer, TimeConstraint, Task
constraint = TimeConstraint(sleep_hours=8, school_hours=7, living_hours=3)
analyzer = TimeFunnelAnalyzer(constraint)
print(f'可用时间: {constraint.free_hours}小时')
"

# 测试决策树引擎
python -c "
from core.engine import DecisionTreeEngine
engine = DecisionTreeEngine()
print('决策树引擎初始化成功')
"

# 测试辩论沙箱
python -c "
from core.sandbox import DebateSandbox
sandbox = DebateSandbox(max_rounds=3)
print('辩论沙箱初始化成功')
"
```

## 📈 重构迁移指南

### 向后兼容性说明
- **旧有业务实现代码**：已被彻底弃用，建议迁移到新架构
- **原有数据Schema**：保持兼容，可通过适配器集成到新系统
- **原有提示词**：可转换为CrewAI Agent的backstory和goal配置
- **原有引擎**：可作为CrewAI Tools集成到新架构中

### 迁移建议
1. 将原有`src/engines/`转换为CrewAI Tools
2. 将原有提示词重构为`config/agents.yaml`中的角色定义
3. 使用`core/engine.py`中的硬编码约束拦截器替代原有的软性检查
4. 通过`tools/mcp_bridge.py`集成原有数据源

## 📄 许可证与商用授权声明 (保持不变)

本仓库采用**代码与内容分离的混合授权模式 (Split-Licensing Mode)**：

### 💻 1. 代码与系统架构 (Source Code & Architecture)
*   **授权协议**：[MIT License](LICENSE-CODE-MIT)
*   **权益边界**：本仓库中的所有工程结构、前后端代码、JSON数据结构定义（Data Schema）、API接口逻辑等，均允许任何人自由用于个人、团队或**商业用途**。

### 🧠 2. 核心提示词、知识库与方法论内容 (Prompts, Knowledge Base & Content)
*   **授权协议**：[CC BY-NC-SA 4.0](LICENSE-CONTENT-CC-BY-NC-SA-4.0)
*   **权益边界**：系统核心提示词、教育策略知识库文本、学科方法论等**内容资产**：
    *   **允许**：个人用户自由下载、阅读、编辑、根据自身家庭情况进行非商业性修改
    *   **严禁商用**：未经项目版权所有人明确的书面授权，严禁将上述内容用于任何营利性场景

### ⚠️ 商业授权获取途径
如果您计划将本系统中的核心提示词（Prompts）或方法论内容整合进商业项目，必须事先联系项目发起团队取得官方书面商业授权。

**联系邮箱：15628071@qq.com**

---

## 📞 联系

*   **项目维护**：HaidianParent.skill Project Team
*   **重构技术咨询**：GitHub Issues
*   **商业授权咨询**：15628071@qq.com
*   **GitHub仓库**：https://github.com/canglangxifeng/HaidianParent.skill

---

Copyright (c) 2026 HaidianParent.skill Project. All Rights Reserved.

*重构完成时间：2026年7月6日*
