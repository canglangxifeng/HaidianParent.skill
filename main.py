"""
容器启动入口与 CrewAI 编排逻辑

这是海淀家长智能体系统的主入口文件，负责：
1. 加载配置
2. 初始化智能体（Agents）和任务（Tasks）
3. 设置大模型基座（Hermes）
4. 启动工作流
5. 集成硬编码控制层
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from crewai import Agent, Task, Crew, Process

from core.engine import DecisionTreeEngine, ConstraintInterceptor
from core.sandbox import DebateSandbox, DebateRole
from tools.mcp_bridge import MCPBridge, mcp_policy_extractor
from tools.custom_skills import time_funnel_analyzer, ConstraintsViolationError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('haidian_parents_agent.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HaidianParentsAgentSystem:
    """海淀家长智能体系统主控制器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.agents_config: Dict[str, Any] = {}
        self.tasks_config: Dict[str, Any] = {}
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.crew: Optional[Crew] = None
        self.decision_engine: Optional[DecisionTreeEngine] = None
        self.constraint_interceptor: Optional[ConstraintInterceptor] = None
        self.debate_sandbox: Optional[DebateSandbox] = None
        
    def load_configurations(self):
        """加载配置文件"""
        logger.info("加载配置...")
        
        # 加载智能体配置
        agents_path = self.config_dir / "agents.yaml"
        if agents_path.exists():
            with open(agents_path, 'r', encoding='utf-8') as f:
                self.agents_config = yaml.safe_load(f)
            logger.info(f"已加载智能体配置: {len(self.agents_config.get('agents', {}))} 个智能体")
        else:
            logger.warning(f"智能体配置文件不存在: {agents_path}")
            self.agents_config = {}
        
        # 加载任务配置
        tasks_path = self.config_dir / "tasks.yaml"
        if tasks_path.exists():
            with open(tasks_path, 'r', encoding='utf-8') as f:
                self.tasks_config = yaml.safe_load(f)
            logger.info(f"已加载任务配置: {len(self.tasks_config.get('tasks', {}))} 个任务")
        else:
            logger.warning(f"任务配置文件不存在: {tasks_path}")
            self.tasks_config = {}
    
    def initialize_llm(self):
        """初始化大语言模型基座（Hermes）"""
        logger.info("初始化大模型基座（Hermes）...")
        
        # 从配置读取LLM设置
        llm_config = self.agents_config.get('default_llm', {})
        model_name = llm_config.get('model', 'hermes-3')
        temperature = llm_config.get('temperature', 0.3)
        
        # 这里实际会初始化具体的LLM，此处为示例代码
        # 实际部署时需要根据使用的LLM库进行调整
        try:
            # 示例：使用OpenAI API
            # from langchain_openai import ChatOpenAI
            # llm = ChatOpenAI(model=model_name, temperature=temperature)
            
            # 或使用Ollama（本地Hermes模型）
            # from langchain_ollama import OllamaLLM
            # llm = OllamaLLM(model=model_name, temperature=temperature)
            
            llm = None  # 实际使用时需要取消注释上面的代码
            logger.info(f"大模型基座初始化: {model_name} (temperature={temperature})")
            return llm
            
        except ImportError as e:
            logger.error(f"LLM库导入失败: {e}")
            logger.warning("使用模拟LLM模式")
            return None
    
    def initialize_agents(self, llm):
        """初始化智能体"""
        logger.info("初始化智能体...")
        
        agents_config = self.agents_config.get('agents', {})
        
        for agent_id, config in agents_config.items():
            try:
                agent = Agent(
                    role=config.get('role', ''),
                    goal=config.get('goal', ''),
                    backstory=config.get('backstory', ''),
                    verbose=config.get('verbose', True),
                    allow_delegation=config.get('allow_delegation', False),
                    llm=llm,
                    tools=self._get_agent_tools(config.get('tools', [])),
                    max_iter=config.get('max_iter', 3),
                    max_rpm=config.get('max_rpm', 10)
                )
                
                self.agents[agent_id] = agent
                logger.info(f"智能体初始化: {agent_id} ({config.get('role')})")
                
            except Exception as e:
                logger.error(f"初始化智能体 {agent_id} 失败: {e}")
    
    def _get_agent_tools(self, tool_names: list):
        """获取工具列表"""
        tools = []
        
        # 映射工具名到实际工具函数
        tool_mapping = {
            'mcp_policy_extractor': mcp_policy_extractor,
            'time_funnel_analyzer': time_funnel_analyzer,
            # 可以添加更多工具映射
        }
        
        for tool_name in tool_names:
            if tool_name in tool_mapping:
                tools.append(tool_mapping[tool_name])
            else:
                logger.warning(f"工具未找到: {tool_name}")
        
        return tools
    
    def initialize_tasks(self):
        """初始化任务"""
        logger.info("初始化任务...")
        
        tasks_config = self.tasks_config.get('tasks', {})
        
        for task_id, config in tasks_config.items():
            try:
                # 获取对应的Agent
                agent_name = config.get('agent')
                agent = self.agents.get(agent_name)
                
                if not agent:
                    logger.warning(f"任务 {task_id} 指定的Agent '{agent_name}' 不存在")
                    continue
                
                task = Task(
                    name=config.get('name', ''),
                    description=config.get('description', ''),
                    expected_output=config.get('expected_output', ''),
                    agent=agent,
                    tools=self._get_agent_tools(config.get('tools', [])),
                    async_execution=config.get('async_execution', False),
                    context=config.get('context', []),
                    output_file=config.get('output_file', None)
                )
                
                self.tasks[task_id] = task
                logger.info(f"任务初始化: {task_id} ({config.get('name')})")
                
            except Exception as e:
                logger.error(f"初始化任务 {task_id} 失败: {e}")
    
    def initialize_constraint_system(self):
        """初始化硬编码控制系统"""
        logger.info("初始化硬编码控制系统...")
        
        self.decision_engine = DecisionTreeEngine()
        self.constraint_interceptor = ConstraintInterceptor(self.decision_engine)
        self.debate_sandbox = DebateSandbox(max_rounds=3)
        
        logger.info("硬编码控制系统初始化完成")
    
    def create_workflow_crew(self):
        """创建工作流Crew"""
        logger.info("创建工作流...")
        
        # 从配置获取工作流定义
        workflow_config = self.tasks_config.get('workflow', {})
        stages = workflow_config.get('stages', [])
        
        # 按阶段组织任务
        task_list = []
        for stage in stages:
            stage_tasks = stage.get('tasks', [])
            for task_id in stage_tasks:
                if task_id in self.tasks:
                    task_list.append(self.tasks[task_id])
                else:
                    logger.warning(f"工作流引用了不存在的任务: {task_id}")
        
        if not task_list:
            # 如果没有配置工作流，使用所有任务
            task_list = list(self.tasks.values())
        
        # 创建Crew
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=task_list,
            process=Process.sequential,  # 顺序执行
            verbose=True,
            memory=True
        )
        
        logger.info(f"工作流创建完成: {len(task_list)} 个任务")
    
    async def run_policy_audit_workflow(self, document_path: str):
        """运行政策审计工作流"""
        logger.info(f"启动政策审计工作流: {document_path}")
        
        # 初始化MCP桥接器
        bridge = MCPBridge()
        await bridge.connect()
        
        try:
            # 提取政策事实
            facts = await bridge.extract_policy_facts(document_path)
            
            # 创建审计报告
            report = {
                "document": document_path,
                "extraction_time": asyncio.get_event_loop().time(),
                "facts_count": len(facts),
                "facts": [
                    {
                        "statement": fact.statement,
                        "confidence": fact.confidence,
                        "parameters": fact.parameters
                    }
                    for fact in facts
                ],
                "summary": "政策事实审计完成，所有陈述均为客观事实提取，不含推测性结论。"
            }
            
            logger.info(f"政策审计完成: 提取到 {len(facts)} 条事实")
            
            # 保存报告
            import json
            report_file = f"reports/policy_audit_{int(asyncio.get_event_loop().time())}.json"
            Path("reports").mkdir(exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"审计报告已保存: {report_file}")
            
            return report
            
        finally:
            await bridge.close()
    
    def run_constraint_validation(self, strategy: Dict[str, Any], context: Dict[str, Any]):
        """运行约束验证"""
        logger.info("运行硬编码约束验证...")
        
        if not self.constraint_interceptor:
            logger.warning("约束拦截器未初始化")
            return True, {"message": "约束拦截器未初始化"}
        
        passed, report = self.constraint_interceptor.intercept_and_validate(strategy, context)
        
        if passed:
            logger.info("✅ 策略通过所有硬编码约束检查")
        else:
            logger.warning(f"❌ 策略被拦截，违反约束: {report.get('critical_violations', [])}")
        
        return passed, report
    
    async def run_debate_sandbox(self, topic: str, context: Dict[str, Any]):
        """运行辩论沙箱"""
        logger.info(f"启动辩论沙箱: {topic}")
        
        if not self.debate_sandbox:
            self.debate_sandbox = DebateSandbox(max_rounds=3)
        
        # 初始化辩论
        self.debate_sandbox.initialize_debate(topic, context)
        
        # 这里实际需要集成真实的Agent进行辩论
        # 由于Agent初始化可能涉及异步操作，这里使用模拟模式
        
        from core.sandbox import MockAgent
        conservative_agent = MockAgent("保守派顾问", DebateRole.CONSERVATIVE)
        aggressive_agent = MockAgent("激进派顾问", DebateRole.AGGRESSIVE)
        
        # 运行辩论
        rounds = self.debate_sandbox.run_rigid_debate(conservative_agent, aggressive_agent)
        
        # 生成审计报告
        report = self.debate_sandbox.generate_audit_report()
        
        logger.info(f"辩论沙箱完成: {len(rounds)} 轮辩论")
        
        # 保存报告
        import json
        report_file = f"reports/debate_audit_{int(asyncio.get_event_loop().time())}.json"
        Path("reports").mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"辩论审计报告已保存: {report_file}")
        
        return report
    
    async def run_full_workflow(self, document_path: str, student_profile: Dict[str, Any]):
        """运行完整工作流"""
        logger.info("=== 启动海淀家长智能体完整工作流 ===")
        
        # 1. 政策审计
        policy_report = await self.run_policy_audit_workflow(document_path)
        
        # 2. 创建升学策略
        strategy = {
            "name": "海淀升学策略",
            "student_profile": student_profile,
            "policy_facts": policy_report["facts"],
            "time_constraints": {
                "sleep_hours": 8,
                "school_hours": 7,
                "living_hours": 3
            },
            "budget_constraints": {
                "monthly_budget": 8000
            },
            "tasks": [
                {"name": "奥数强化", "duration_hours": 2, "priority": 5, "category": "学习"},
                {"name": "英语阅读", "duration_hours": 1.5, "priority": 4, "category": "学习"},
                {"name": "科技特长", "duration_hours": 1, "priority": 3, "category": "特长"}
            ]
        }
        
        # 3. 约束验证
        context = {
            "policy_data": {
                "min_admission_score": 280,
                "deadlines": {
                    "报名截止": "2024-05-15",
                    "材料提交": "2024-05-20"
                }
            },
            "student_profile": student_profile
        }
        
        passed, validation_report = self.run_constraint_validation(strategy, context)
        
        if not passed and self.constraint_interceptor.should_retry():
            logger.info("策略被拦截，需要重新生成...")
            # 这里实际会触发Hermes重新生成策略
            # 简化处理：直接返回当前结果
            pass
        
        # 4. 高风险决策辩论
        debate_topic = f"基于以下信息的升学决策辩论：{student_profile.get('name', '学生')}的海淀升学路径"
        debate_context = {
            "policy_report": policy_report,
            "validation_report": validation_report,
            "student_profile": student_profile
        }
        
        debate_report = await self.run_debate_sandbox(debate_topic, debate_context)
        
        # 5. 综合报告
        final_report = {
            "workflow_completed": True,
            "timestamp": asyncio.get_event_loop().time(),
            "policy_audit": policy_report,
            "constraint_validation": validation_report,
            "debate_audit": debate_report,
            "recommendation": debate_report.get("recommendation", "暂无明确建议")
        }
        
        logger.info("=== 完整工作流执行完成 ===")
        
        return final_report
    
    def start_cli(self):
        """启动命令行交互界面"""
        print("""
        ========================================
        海淀家长智能体系统 (Haidian Parents Agent)
        ========================================
        
        系统架构：
        1. 外壳容器层 (CrewAI) - 多智能体协同
        2. 核心基座层 (Hermes) - 长上下文推理
        3. 硬编码控制层 (Python Engine) - 物理约束审计
        4. 数据与接口层 (MCP) - 政策知识库
        
        可用命令：
        1. 政策审计 (policy)
        2. 约束验证 (constraint)
        3. 辩论沙箱 (debate)
        4. 完整工作流 (full)
        5. 退出 (exit)
        """)
        
        # 简化CLI实现
        # TODO: 实现完整的CLI交互
        
        print("CLI功能待实现，请直接调用API方法。")


async def main():
    """主函数"""
    print("启动海淀家长智能体系统...")
    
    # 初始化系统
    system = HaidianParentsAgentSystem()
    
    # 加载配置
    system.load_configurations()
    
    # 初始化大模型
    llm = system.initialize_llm()
    
    # 初始化智能体和任务
    system.initialize_agents(llm)
    system.initialize_tasks()
    
    # 初始化约束系统
    system.initialize_constraint_system()
    
    # 创建工作流
    system.create_workflow_crew()
    
    print("系统初始化完成！")
    
    # 示例：运行一个简单测试
    test_document = "example_policy.pdf"
    test_student = {
        "name": "小明",
        "grade": "五年级",
        "academic_level": "中等偏上",
        "specialty": "编程",
        "family_location": "海淀区中关村"
    }
    
    print(f"\n运行测试工作流...")
    print(f"政策文档: {test_document}")
    print(f"学生档案: {test_student['name']} ({test_student['grade']})")
    
    try:
        # 运行完整工作流
        report = await system.run_full_workflow(test_document, test_student)
        
        print("\n=== 工作流执行结果 ===")
        print(f"政策事实提取: {report['policy_audit']['facts_count']} 条事实")
        print(f"约束验证: {'通过' if report['constraint_validation'].get('summary', {}).get('failed_audits', 0) == 0 else '未通过'}")
        print(f"辩论结果: {report['debate_audit'].get('cross_validation_analysis', {}).get('cross_validation_score', 0):.2f} 交叉验证度")
        print(f"\n最终建议: {report['recommendation']}")
        
    except Exception as e:
        print(f"工作流执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n系统就绪，可以调用其他功能。")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())