"""
纯Python实现的刚性计算工具
包含物理时间漏斗分析器、财务约束检查器等
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import time
import logging
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum

logger = logging.getLogger(__name__)


class TimeUnit(str, Enum):
    """时间单位"""
    HOURS = "hours"
    MINUTES = "minutes"


class ConstraintsViolationError(Exception):
    """约束违反异常"""
    def __init__(self, message: str, violations: List[str]):
        super().__init__(message)
        self.violations = violations
        self.message = message
    
    def __str__(self):
        return f"{self.message}: {', '.join(self.violations)}"


# Pydantic模型定义
class TimeConstraint(BaseModel):
    """时间约束模型"""
    sleep_hours: float = Field(ge=0, le=24, description="刚性睡眠时间（小时）")
    school_hours: float = Field(ge=0, le=24, description="校内物理时间（小时）")
    living_hours: float = Field(ge=0, le=24, description="日常通勤/洗漱/就餐时间（小时）")
    
    @validator('sleep_hours', 'school_hours', 'living_hours')
    def validate_hour_range(cls, v):
        if v < 0 or v > 24:
            raise ValueError(f"时间必须在0-24小时之间，当前值: {v}")
        return v
    
    @property
    def total_commitment_hours(self) -> float:
        """总承诺时间"""
        return self.sleep_hours + self.school_hours + self.living_hours
    
    @property
    def free_hours(self) -> float:
        """自由支配时间"""
        return 24.0 - self.total_commitment_hours


class Task(BaseModel):
    """任务模型"""
    name: str = Field(..., description="任务名称")
    duration_hours: float = Field(ge=0, description="任务持续时间（小时）")
    priority: int = Field(ge=1, le=5, description="优先级（1-5，5最高）")
    category: str = Field(..., description="任务类别：学习、兴趣、休息等")


class TimeFunnelAnalyzer:
    """
    每日物理时间漏斗分析器
    
    根据PRD要求：设每日总时间上限为固定常数 T_max = 24，
    设校内物理时间为 t_school，刚性睡眠时间为 t_sleep，
    日常通勤/洗漱/就餐时间为 t_live。
    则留给Agent自由编排的教育物理时间净值 t_free 计算公式为：
    t_free = T_max - (t_school + t_sleep + t_live)
    
    当Agent编排的课外网课、奥数刷题、原版阅读时间总和 Σ t_tasks > t_free 时，
    必须抛出 ConstraintsViolationError。
    """
    
    def __init__(self, time_constraint: TimeConstraint):
        """
        初始化时间漏斗分析器
        
        Args:
            time_constraint: 时间约束配置
        """
        self.constraint = time_constraint
        self.tasks: List[Task] = []
    
    def add_task(self, task: Task):
        """添加任务到分析器"""
        self.tasks.append(task)
    
    def add_tasks(self, tasks: List[Task]):
        """批量添加任务"""
        self.tasks.extend(tasks)
    
    def validate_constraints(self, raise_on_violation: bool = True) -> Tuple[bool, List[str]]:
        """
        验证所有任务是否满足时间约束
        
        Args:
            raise_on_violation: 是否在违反约束时抛出异常
            
        Returns:
            (是否通过验证, 违反约束的详细信息列表)
        """
        violations = []
        
        # 计算总任务时间
        total_task_hours = sum(task.duration_hours for task in self.tasks)
        
        # 计算可用自由时间
        free_hours = self.constraint.free_hours
        
        # 检查时间约束
        if total_task_hours > free_hours:
            violation_msg = (
                f"任务总时间({total_task_hours:.2f}h)超过可用自由时间({free_hours:.2f}h)。"
                f"超出 {(total_task_hours - free_hours):.2f} 小时。"
            )
            violations.append(violation_msg)
        
        # 检查单个任务时间合理性
        for task in self.tasks:
            if task.duration_hours > 8:
                violations.append(f"任务'{task.name}'持续时间({task.duration_hours}h)过长，可能不切实际")
        
        # 检查总时间不超过24小时
        total_all_hours = self.constraint.total_commitment_hours + total_task_hours
        if total_all_hours > 24:
            violations.append(f"总时间配置({total_all_hours:.2f}h)超过24小时物理上限")
        
        if violations and raise_on_violation:
            raise ConstraintsViolationError(
                message="时间约束验证失败",
                violations=violations
            )
        
        return len(violations) == 0, violations
    
    def get_time_analysis_report(self) -> Dict[str, Any]:
        """
        生成时间分析报告
        
        Returns:
            详细的时间分析报告
        """
        total_task_hours = sum(task.duration_hours for task in self.tasks)
        free_hours = self.constraint.free_hours
        utilization_rate = (total_task_hours / free_hours * 100) if free_hours > 0 else 0
        
        # 按类别分组
        categories: Dict[str, float] = {}
        for task in self.tasks:
            categories[task.category] = categories.get(task.category, 0) + task.duration_hours
        
        return {
            "time_constraints": {
                "sleep_hours": self.constraint.sleep_hours,
                "school_hours": self.constraint.school_hours,
                "living_hours": self.constraint.living_hours,
                "total_commitment_hours": self.constraint.total_commitment_hours,
                "free_hours": free_hours,
            },
            "task_summary": {
                "total_tasks": len(self.tasks),
                "total_task_hours": total_task_hours,
                "utilization_rate_percent": round(utilization_rate, 2),
                "remaining_hours": max(0, free_hours - total_task_hours),
            },
            "task_breakdown": [
                {
                    "name": task.name,
                    "duration_hours": task.duration_hours,
                    "priority": task.priority,
                    "category": task.category
                }
                for task in self.tasks
            ],
            "category_distribution": categories,
            "recommendations": self._generate_recommendations(total_task_hours, free_hours)
        }
    
    def _generate_recommendations(self, total_task_hours: float, free_hours: float) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if total_task_hours > free_hours:
            overflow = total_task_hours - free_hours
            recommendations.append(
                f"⚠️ 时间溢出警告：需要削减 {overflow:.2f} 小时的任务量"
            )
        
        # 检查高优先级任务
        high_priority_tasks = [t for t in self.tasks if t.priority >= 4]
        if len(high_priority_tasks) > 3:
            recommendations.append(
                f"注意：高优先级任务({len(high_priority_tasks)}个)过多，可能影响执行效果"
            )
        
        # 检查学习时间分布
        study_hours = sum(t.duration_hours for t in self.tasks if "学习" in t.category or "study" in t.category.lower())
        if study_hours > 6:
            recommendations.append(
                "建议：单日学习时间过长，应考虑间隔休息，避免疲劳"
            )
        
        if free_hours - total_task_hours > 2:
            recommendations.append(
                f"还有 {free_hours - total_task_hours:.2f} 小时空闲时间，可考虑加入休息或兴趣活动"
            )
        
        return recommendations
    
    def optimize_schedule(self) -> List[Task]:
        """
        优化任务安排（简单版本）
        按优先级排序，确保不超过时间限制
        
        Returns:
            优化后的任务列表
        """
        # 按优先级降序排序
        sorted_tasks = sorted(self.tasks, key=lambda t: t.priority, reverse=True)
        
        optimized = []
        remaining_hours = self.constraint.free_hours
        
        for task in sorted_tasks:
            if task.duration_hours <= remaining_hours:
                optimized.append(task)
                remaining_hours -= task.duration_hours
            else:
                logger.info(f"由于时间限制，跳过低优先级任务: {task.name}")
        
        return optimized


# CrewAI工具函数
def time_funnel_analyzer(
    sleep_hours: float,
    school_hours: float,
    living_hours: float,
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    CrewAI工具：时间漏斗分析器
    
    Args:
        sleep_hours: 刚性睡眠时间
        school_hours: 校内物理时间
        living_hours: 日常生活时间
        tasks: 任务列表，每个任务包含name, duration_hours, priority, category
        
    Returns:
        时间分析报告，如果违反约束则抛出异常
    """
    try:
        # 验证输入
        constraint = TimeConstraint(
            sleep_hours=sleep_hours,
            school_hours=school_hours,
            living_hours=living_hours
        )
        
        analyzer = TimeFunnelAnalyzer(constraint)
        
        # 转换任务
        task_objects = []
        for task_data in tasks:
            task = Task(**task_data)
            task_objects.append(task)
        
        analyzer.add_tasks(task_objects)
        
        # 验证约束
        is_valid, violations = analyzer.validate_constraints(raise_on_violation=True)
        
        # 生成报告
        report = analyzer.get_time_analysis_report()
        report["validation_passed"] = is_valid
        report["violations"] = violations
        
        return report
        
    except ValidationError as e:
        raise ValueError(f"输入数据验证失败: {e}")
    except ConstraintsViolationError as e:
        # 重新抛出，让CrewAI能处理
        raise e


# 其他刚性计算工具
class BudgetConstraintChecker:
    """财务约束检查器"""
    
    def __init__(self, monthly_budget: float):
        self.monthly_budget = monthly_budget
        self.expenses: List[Dict[str, Any]] = []
    
    def add_expense(self, name: str, amount: float, category: str):
        """添加支出项目"""
        self.expenses.append({
            "name": name,
            "amount": amount,
            "category": category
        })
    
    def check_budget(self) -> Tuple[bool, float, List[str]]:
        """
        检查预算约束
        
        Returns:
            (是否超预算, 总支出, 警告信息列表)
        """
        total_expense = sum(expense["amount"] for expense in self.expenses)
        is_over_budget = total_expense > self.monthly_budget
        
        warnings = []
        if is_over_budget:
            warnings.append(f"月度支出({total_expense:.2f}元)超过预算({self.monthly_budget:.2f}元)")
        
        # 检查大额支出
        large_expenses = [e for e in self.expenses if e["amount"] > self.monthly_budget * 0.3]
        for expense in large_expenses:
            warnings.append(f"大额支出警告: {expense['name']} ({expense['amount']:.2f}元)")
        
        return not is_over_budget, total_expense, warnings


if __name__ == "__main__":
    # 测试代码
    print("=== 时间漏斗分析器测试 ===")
    
    # 创建时间约束
    constraint = TimeConstraint(
        sleep_hours=8,
        school_hours=7,
        living_hours=3
    )
    
    print(f"自由时间: {constraint.free_hours:.2f} 小时")
    
    # 创建分析器
    analyzer = TimeFunnelAnalyzer(constraint)
    
    # 添加任务
    tasks = [
        Task(name="奥数刷题", duration_hours=2, priority=4, category="学习"),
        Task(name="原版阅读", duration_hours=1.5, priority=3, category="阅读"),
        Task(name="课外网课", duration_hours=2, priority=5, category="学习"),
        Task(name="体育训练", duration_hours=1, priority=2, category="兴趣"),
    ]
    
    analyzer.add_tasks(tasks)
    
    # 验证约束
    try:
        is_valid, violations = analyzer.validate_constraints()
        print(f"验证通过: {is_valid}")
        if violations:
            print(f"违反约束: {violations}")
    except ConstraintsViolationError as e:
        print(f"约束违反异常: {e}")
    
    # 生成报告
    report = analyzer.get_time_analysis_report()
    print(f"\n时间分析报告:")
    print(f"总任务时间: {report['task_summary']['total_task_hours']:.2f}h")
    print(f"利用率: {report['task_summary']['utilization_rate_percent']}%")
    print(f"剩余时间: {report['task_summary']['remaining_hours']:.2f}h")
    
    print("\n=== 测试完成 ===")