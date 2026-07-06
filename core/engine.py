"""
核心控制器：硬编码决策树、约束拦截器
负责对Hermes输出的策略方案进行硬性拦截审计
"""
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date
from pathlib import Path

from pydantic import BaseModel, Field, validator

from tools.custom_skills import ConstraintsViolationError, TimeConstraint, TimeFunnelAnalyzer

logger = logging.getLogger(__name__)


class DecisionNodeType(str, Enum):
    """决策节点类型"""
    TIME_CONSTRAINT = "time_constraint"
    BUDGET_CONSTRAINT = "budget_constraint"
    POLICY_COMPLIANCE = "policy_compliance"
    RISK_ASSESSMENT = "risk_assessment"
    LOGICAL_CONSISTENCY = "logical_consistency"


class AuditResult(BaseModel):
    """审计结果"""
    passed: bool = Field(..., description="是否通过审计")
    node_type: DecisionNodeType = Field(..., description="决策节点类型")
    message: str = Field(..., description="审计结果消息")
    violations: List[str] = Field(default_factory=list, description="违反的规则")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="审计证据")
    timestamp: datetime = Field(default_factory=datetime.now, description="审计时间")


@dataclass
class DecisionNode:
    """决策树节点"""
    node_id: str
    node_type: DecisionNodeType
    condition: callable  # 评估函数
    error_message: str
    weight: float = 1.0  # 节点权重
    
    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        评估节点条件
        
        Returns:
            (是否通过, 违反信息列表, 证据)
        """
        try:
            passed, evidence = self.condition(context)
            violations = [] if passed else [self.error_message]
            return passed, violations, evidence
        except Exception as e:
            logger.error(f"Error evaluating node {self.node_id}: {e}")
            return False, [f"评估错误: {str(e)}"], {}


class DecisionTreeEngine:
    """
    硬编码决策树引擎
    
    针对涉及物理限制（如时间冲突、财务预算）、多校录取概率辩论等高风险决策，
    由纯Python编写的决策树进行硬性拦截和结果审计，拒绝LLM模糊输出。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.nodes: List[DecisionNode] = []
        self.audit_history: List[AuditResult] = []
        self._initialize_default_nodes()
        
        if config_path:
            self.load_config(config_path)
    
    def _initialize_default_nodes(self):
        """初始化默认决策节点"""
        # 时间约束节点
        self.add_node(
            DecisionNode(
                node_id="time_constraint_001",
                node_type=DecisionNodeType.TIME_CONSTRAINT,
                condition=self._check_time_constraints,
                error_message="时间约束违反：任务总时间超过可用自由时间",
                weight=1.0
            )
        )
        
        # 预算约束节点
        self.add_node(
            DecisionNode(
                node_id="budget_constraint_001",
                node_type=DecisionNodeType.BUDGET_CONSTRAINT,
                condition=self._check_budget_constraints,
                error_message="财务约束违反：月度支出超过预算",
                weight=0.8
            )
        )
        
        # 政策合规节点
        self.add_node(
            DecisionNode(
                node_id="policy_compliance_001",
                node_type=DecisionNodeType.POLICY_COMPLIANCE,
                condition=self._check_policy_compliance,
                error_message="政策合规违反：策略与官方政策冲突",
                weight=1.2
            )
        )
        
        # 逻辑一致性节点
        self.add_node(
            DecisionNode(
                node_id="logical_consistency_001",
                node_type=DecisionNodeType.LOGICAL_CONSISTENCY,
                condition=self._check_logical_consistency,
                error_message="逻辑一致性违反：策略存在自相矛盾",
                weight=0.9
            )
        )
    
    def add_node(self, node: DecisionNode):
        """添加决策节点"""
        self.nodes.append(node)
    
    def audit_strategy(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, List[AuditResult]]:
        """
        审计策略方案
        
        Args:
            strategy: Hermes输出的策略方案
            context: 审计上下文（包含约束条件、政策数据等）
            
        Returns:
            (是否通过审计, 详细的审计结果列表)
        """
        audit_context = {
            "strategy": strategy,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        results = []
        all_passed = True
        
        for node in self.nodes:
            passed, violations, evidence = node.evaluate(audit_context)
            
            result = AuditResult(
                passed=passed,
                node_type=node.node_type,
                message=f"节点 {node.node_id} 审计: {'通过' if passed else '失败'}",
                violations=violations,
                evidence=evidence,
                timestamp=datetime.now()
            )
            
            results.append(result)
            
            if not passed:
                all_passed = False
                logger.warning(f"决策节点 {node.node_id} 审计失败: {violations}")
        
        self.audit_history.extend(results)
        
        return all_passed, results
    
    def _check_time_constraints(self, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """检查时间约束"""
        strategy = context["strategy"]
        
        # 提取时间约束配置
        time_config = strategy.get("time_constraints", {})
        if not time_config:
            return True, {"message": "未提供时间约束配置"}
        
        try:
            # 使用TimeFunnelAnalyzer进行验证
            from tools.custom_skills import TimeConstraint, TimeFunnelAnalyzer, Task
            
            constraint = TimeConstraint(
                sleep_hours=time_config.get("sleep_hours", 8),
                school_hours=time_config.get("school_hours", 7),
                living_hours=time_config.get("living_hours", 3)
            )
            
            analyzer = TimeFunnelAnalyzer(constraint)
            
            # 添加任务
            tasks_data = strategy.get("tasks", [])
            tasks = []
            for task_data in tasks_data:
                # 这里简化为直接创建Task，实际需要更复杂的转换
                from tools.custom_skills import Task as TaskModel
                task = TaskModel(
                    name=task_data.get("name", ""),
                    duration_hours=task_data.get("duration_hours", 0),
                    priority=task_data.get("priority", 3),
                    category=task_data.get("category", "其他")
                )
                tasks.append(task)
            
            analyzer.add_tasks(tasks)
            
            # 验证约束
            is_valid, violations = analyzer.validate_constraints(raise_on_violation=False)
            
            evidence = {
                "free_hours": constraint.free_hours,
                "total_task_hours": sum(t.duration_hours for t in tasks),
                "violations": violations
            }
            
            return is_valid, evidence
            
        except Exception as e:
            logger.error(f"时间约束检查错误: {e}")
            return False, {"error": str(e)}
    
    def _check_budget_constraints(self, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """检查预算约束"""
        strategy = context["strategy"]
        
        budget_config = strategy.get("budget_constraints", {})
        if not budget_config:
            return True, {"message": "未提供预算约束配置"}
        
        monthly_budget = budget_config.get("monthly_budget", 0)
        expenses = strategy.get("expenses", [])
        
        total_expense = sum(exp.get("amount", 0) for exp in expenses)
        
        is_within_budget = total_expense <= monthly_budget
        evidence = {
            "monthly_budget": monthly_budget,
            "total_expense": total_expense,
            "is_within_budget": is_within_budget
        }
        
        return is_within_budget, evidence
    
    def _check_policy_compliance(self, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """检查政策合规性"""
        strategy = context["strategy"]
        policy_data = context.get("policy_data", {})
        
        if not policy_data:
            return True, {"message": "未提供政策数据"}
        
        # 检查策略中的关键决策是否违反政策
        violations = []
        
        # 示例检查：录取分数线
        admission_strategy = strategy.get("admission_strategy", {})
        target_score = admission_strategy.get("target_score", 0)
        min_score = policy_data.get("min_admission_score", 0)
        
        if target_score < min_score:
            violations.append(f"目标分数({target_score})低于政策最低要求({min_score})")
        
        # 检查时间节点
        deadlines = policy_data.get("deadlines", {})
        plan_dates = strategy.get("plan_dates", {})
        
        for key, deadline in deadlines.items():
            if key in plan_dates:
                plan_date = plan_dates[key]
                if plan_date > deadline:
                    violations.append(f"{key}计划日期({plan_date})晚于政策截止日期({deadline})")
        
        evidence = {
            "policy_checks_performed": len(deadlines) + 1,  # +1 for score check
            "violations_found": len(violations),
            "violations": violations
        }
        
        return len(violations) == 0, evidence
    
    def _check_logical_consistency(self, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """检查逻辑一致性"""
        strategy = context["strategy"]
        
        inconsistencies = []
        
        # 检查时间冲突
        tasks = strategy.get("tasks", [])
        task_schedule = {}
        
        for task in tasks:
            start_time = task.get("start_time")
            duration = task.get("duration_hours", 0)
            
            if start_time and duration:
                end_time = start_time + duration
                # 简化检查：如果有重叠的时间段，标记为冲突
                for other_start, other_end in task_schedule.values():
                    if not (end_time <= other_start or start_time >= other_end):
                        inconsistencies.append(f"任务 '{task.get('name')}' 时间冲突")
                        break
                
                task_schedule[task.get("name")] = (start_time, end_time)
        
        # 检查资源分配冲突
        resource_allocations = strategy.get("resource_allocations", {})
        total_resource = strategy.get("total_resources", {})
        
        for resource_type, allocated in resource_allocations.items():
            available = total_resource.get(resource_type, 0)
            if allocated > available:
                inconsistencies.append(f"资源 '{resource_type}' 分配({allocated})超过可用({available})")
        
        evidence = {
            "inconsistencies_found": len(inconsistencies),
            "inconsistencies": inconsistencies
        }
        
        return len(inconsistencies) == 0, evidence
    
    def generate_audit_report(self, results: List[AuditResult]) -> Dict[str, Any]:
        """生成审计报告"""
        if not results:
            return {"message": "无审计结果"}
        
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        
        # 按节点类型统计
        by_type = {}
        for result in results:
            by_type.setdefault(result.node_type, {"passed": 0, "total": 0})
            by_type[result.node_type]["total"] += 1
            if result.passed:
                by_type[result.node_type]["passed"] += 1
        
        # 收集所有违规
        all_violations = []
        for result in results:
            all_violations.extend(result.violations)
        
        return {
            "summary": {
                "total_audits": total_count,
                "passed_audits": passed_count,
                "failed_audits": total_count - passed_count,
                "pass_rate": (passed_count / total_count * 100) if total_count > 0 else 0,
                "total_violations": len(all_violations)
            },
            "breakdown_by_type": by_type,
            "critical_violations": [v for v in all_violations if "违反" in v],
            "recommendation": self._generate_recommendation(passed_count, total_count, all_violations),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_recommendation(self, passed: int, total: int, violations: List[str]) -> str:
        """生成审计建议"""
        if passed == total:
            return "✅ 策略方案通过所有硬编码审计检查，可提交执行。"
        
        fail_rate = (total - passed) / total * 100
        
        if fail_rate > 50:
            return "❌ 策略方案存在严重问题，需要彻底重新设计。"
        elif fail_rate > 20:
            return "⚠️ 策略方案存在多个问题，需要重大修改。"
        else:
            return "⚠️ 策略方案存在少量问题，建议修正后重新审计。"
    
    def load_config(self, config_path: str):
        """从配置文件加载决策树配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 这里可以实现从JSON配置创建决策节点
            logger.info(f"从 {config_path} 加载了决策树配置")
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
        except json.JSONDecodeError as e:
            logger.error(f"配置文件解析错误: {e}")
    
    def save_audit_history(self, filepath: str):
        """保存审计历史"""
        history_data = [result.dict() for result in self.audit_history]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"审计历史已保存到 {filepath}")


class ConstraintInterceptor:
    """
    约束拦截器
    
    当Hermes输出的策略方案违反物理约束时，直接打回任务流，
    强制Hermes在约束框架内重新生成，直至逻辑自洽。
    """
    
    def __init__(self, engine: DecisionTreeEngine):
        self.engine = engine
        self.interception_count = 0
        self.max_retries = 3
    
    def intercept_and_validate(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        拦截并验证策略
        
        Args:
            strategy: Hermes生成的策略
            context: 验证上下文
            
        Returns:
            (是否通过, 审计报告)
        """
        self.interception_count += 1
        
        # 进行审计
        passed, results = self.engine.audit_strategy(strategy, context)
        
        # 生成审计报告
        report = self.engine.generate_audit_report(results)
        
        if not passed:
            logger.warning(f"策略被拦截 (拦截次数: {self.interception_count})")
            report["intercepted"] = True
            report["interception_count"] = self.interception_count
            report["retry_allowed"] = self.interception_count < self.max_retries
        
        return passed, report
    
    def should_retry(self) -> bool:
        """是否应该重试"""
        return self.interception_count < self.max_retries


if __name__ == "__main__":
    # 测试代码
    print("=== 决策树引擎测试 ===")
    
    engine = DecisionTreeEngine()
    interceptor = ConstraintInterceptor(engine)
    
    # 测试策略
    test_strategy = {
        "name": "海淀小升初策略",
        "time_constraints": {
            "sleep_hours": 8,
            "school_hours": 7,
            "living_hours": 3
        },
        "tasks": [
            {"name": "奥数刷题", "duration_hours": 4, "priority": 5, "category": "学习"},
            {"name": "英语阅读", "duration_hours": 2, "priority": 4, "category": "学习"},
            {"name": "钢琴练习", "duration_hours": 1, "priority": 3, "category": "兴趣"}
        ],
        "budget_constraints": {
            "monthly_budget": 5000
        },
        "expenses": [
            {"name": "补习班", "amount": 3000},
            {"name": "兴趣班", "amount": 1500},
            {"name": "教材", "amount": 500}
        ]
    }
    
    test_context = {
        "policy_data": {
            "min_admission_score": 280,
            "deadlines": {
                "报名截止": "2024-05-15",
                "材料提交": "2024-05-20"
            }
        }
    }
    
    passed, report = interceptor.intercept_and_validate(test_strategy, test_context)
    
    print(f"策略通过: {passed}")
    print(f"审计摘要: {report['summary']}")
    
    if not passed:
        print(f"严重违规: {report.get('critical_violations', [])}")
    
    print("\n=== 测试完成 ===")