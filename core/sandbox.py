"""
辩论沙箱：多Agent竞争冲突解决机制

针对"派位志愿填报选择风险"等高风险多岔路决策，严禁单Prompt一言堂。
通过构建刚性对话循环，执行3轮辩论，最终由Python计分器提取双方论据的交叉验证度。
"""
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import Counter

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class DebateRole(str, Enum):
    """辩论角色"""
    CONSERVATIVE = "conservative"  # 保守派：基于最低风险、就近派位、财务稳健原则
    AGGRESSIVE = "aggressive"     # 激进派：基于科技特长、跨区加工能力、高收益高风险原则


class ArgumentQuality(str, Enum):
    """论据质量等级"""
    HIGH = "high"       # 高质量：有数据支持、逻辑严谨
    MEDIUM = "medium"   # 中等质量：有逻辑但缺乏数据
    LOW = "low"         # 低质量：情绪化、缺乏依据


@dataclass
class DebateArgument:
    """辩论论据"""
    role: DebateRole
    round_number: int
    content: str
    quality_score: float  # 0-1的质量评分
    supporting_facts: List[str] = field(default_factory=list)
    logical_fallacies: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DebateRound:
    """辩论轮次"""
    round_number: int
    conservative_argument: Optional[DebateArgument] = None
    aggressive_argument: Optional[DebateArgument] = None


class DebateScorer:
    """辩论计分器"""
    
    def __init__(self):
        self.fact_keywords = [
            "数据", "统计", "研究", "报告", "根据", "显示", "表明",
            "probability", "statistics", "research", "study", "data"
        ]
        
        self.fallacy_keywords = [
            "绝对", "一定", "肯定", "不可能", "从来", "永远",
            "绝对化", "情绪化", "无根据", "据说", "听说"
        ]
    
    def score_argument(self, argument: DebateArgument) -> float:
        """评辩论据质量"""
        content = argument.content
        
        # 基础分
        base_score = 0.5
        
        # 事实支持加分
        fact_bonus = 0
        for keyword in self.fact_keywords:
            if keyword in content:
                fact_bonus += 0.05
        
        # 逻辑谬误扣分
        fallacy_penalty = 0
        for keyword in self.fallacy_keywords:
            if keyword in content:
                fallacy_penalty += 0.1
        
        # 长度权重（适中的长度得分更高）
        word_count = len(content.split())
        if 50 <= word_count <= 200:
            length_bonus = 0.1
        elif word_count < 20:
            length_bonus = -0.2
        else:
            length_bonus = 0
        
        # 计算最终得分
        final_score = min(1.0, max(0.0, base_score + fact_bonus - fallacy_penalty + length_bonus))
        
        # 记录分析结果
        argument.supporting_facts = [kw for kw in self.fact_keywords if kw in content]
        argument.logical_fallacies = [kw for kw in self.fallacy_keywords if kw in content]
        argument.quality_score = final_score
        
        return final_score
    
    def calculate_cross_validation(self, arguments: List[DebateArgument]) -> Dict[str, float]:
        """计算交叉验证度"""
        if len(arguments) < 2:
            return {"cross_validation_score": 0.0}
        
        # 提取关键观点
        conservative_points = []
        aggressive_points = []
        
        for arg in arguments:
            if arg.role == DebateRole.CONSERVATIVE:
                conservative_points.extend(self._extract_key_points(arg.content))
            else:
                aggressive_points.extend(self._extract_key_points(arg.content))
        
        # 计算观点重叠度
        overlap = 0
        total_unique = len(set(conservative_points + aggressive_points))
        
        if total_unique > 0:
            conservative_set = set(conservative_points)
            aggressive_set = set(aggressive_points)
            overlap = len(conservative_set.intersection(aggressive_set))
            overlap_score = overlap / total_unique
        else:
            overlap_score = 0
        
        # 质量加权交叉验证
        avg_quality = sum(arg.quality_score for arg in arguments) / len(arguments)
        cross_validation_score = overlap_score * avg_quality
        
        return {
            "cross_validation_score": cross_validation_score,
            "overlap_points": overlap,
            "total_unique_points": total_unique,
            "average_quality": avg_quality
        }
    
    def _extract_key_points(self, text: str) -> List[str]:
        """从文本中提取关键观点"""
        # 简化实现：提取包含关键词的句子
        sentences = re.split(r'[。！？；]', text)
        key_points = []
        
        important_keywords = ["风险", "收益", "优势", "劣势", "建议", "因为", "所以"]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in important_keywords) and len(sentence) > 5:
                key_points.append(sentence[:100])  # 截断避免过长
        
        return key_points


class DebateSandbox:
    """
    辩论沙箱
    
    执行刚性对话循环，限制双方辩论必须严格执行3轮。
    每轮交替输入，最终由Python计分器提取双方论据的交叉验证度。
    """
    
    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds
        self.rounds: List[DebateRound] = []
        self.scorer = DebateScorer()
        self.topic = ""
        self.context = {}
    
    def initialize_debate(self, topic: str, context: Dict[str, Any]):
        """初始化辩论"""
        self.topic = topic
        self.context = context
        self.rounds = []
        logger.info(f"辩论沙箱初始化：主题='{topic}'，最大轮次={self.max_rounds}")
    
    def add_argument(self, role: DebateRole, content: str, round_number: int) -> DebateArgument:
        """添加论据到指定轮次"""
        if round_number < 1 or round_number > self.max_rounds:
            raise ValueError(f"轮次必须在1-{self.max_rounds}之间")
        
        # 确保轮次存在
        while len(self.rounds) < round_number:
            self.rounds.append(DebateRound(round_number=len(self.rounds) + 1))
        
        round_idx = round_number - 1
        
        # 创建论据并评分
        argument = DebateArgument(
            role=role,
            round_number=round_number,
            content=content
        )
        
        # 评分
        self.scorer.score_argument(argument)
        
        # 添加到对应轮次
        if role == DebateRole.CONSERVATIVE:
            self.rounds[round_idx].conservative_argument = argument
        else:
            self.rounds[round_idx].aggressive_argument = argument
        
        logger.info(f"添加{role}论据到第{round_number}轮，质量得分: {argument.quality_score:.2f}")
        
        return argument
    
    def run_rigid_debate(self, conservative_agent, aggressive_agent) -> List[DebateRound]:
        """
        执行刚性辩论循环
        
        Args:
            conservative_agent: 保守派Agent（需有generate方法）
            aggressive_agent: 激进派Agent（需有generate方法）
            
        Returns:
            辩论轮次列表
        """
        logger.info(f"开始{self.max_rounds}轮刚性辩论")
        
        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"=== 第{round_num}轮辩论 ===")
            
            # 保守派发言
            conservative_prompt = self._build_prompt(DebateRole.CONSERVATIVE, round_num)
            conservative_response = conservative_agent.generate(conservative_prompt)
            self.add_argument(DebateRole.CONSERVATIVE, conservative_response, round_num)
            
            # 激进派发言（可以看到保守派观点）
            aggressive_prompt = self._build_prompt(
                DebateRole.AGGRESSIVE, 
                round_num,
                opponent_argument=conservative_response
            )
            aggressive_response = aggressive_agent.generate(aggressive_prompt)
            self.add_argument(DebateRole.AGGRESSIVE, aggressive_response, round_num)
        
        logger.info(f"辩论完成，共{len(self.rounds)}轮")
        return self.rounds
    
    def _build_prompt(self, role: DebateRole, round_num: int, opponent_argument: str = "") -> str:
        """构建辩论提示词"""
        role_desc = {
            DebateRole.CONSERVATIVE: "保守派（基于最低风险、就近派位、财务稳健原则）",
            DebateRole.AGGRESSIVE: "激进派（基于科技特长、跨区加工能力、高收益高风险原则）"
        }
        
        prompt = f"""# 海淀家长决策辩论沙箱 - 第{round_num}轮

## 辩论主题
{self.topic}

## 您的角色
您是一位海淀升学决策的{role_desc[role]}顾问。

## 上下文信息
{json.dumps(self.context, ensure_ascii=False, indent=2)}

## 辩论规则
1. 请基于事实和数据说话，避免情绪化表达
2. 如果有相关统计数据或政策依据，请引用
3. 请考虑物理约束（时间、预算）和实际可行性
"""

        if opponent_argument:
            prompt += f"""

## 对方观点（第{round_num}轮）
{opponent_argument}

请针对对方观点进行回应，提出您的反驳或补充论据。
"""

        if round_num > 1:
            prompt += f"""

## 历史轮次摘要
之前已经进行了{round_num-1}轮辩论，请确保您的论点与之前保持一致。
"""

        prompt += """

## 您的回应要求
请提供清晰、有逻辑的论据，支持您的决策立场。避免使用绝对化语言。
您的回应应该结构化，包含：
1. 核心观点总结
2. 主要论据（事实、数据、逻辑）
3. 风险评估
4. 具体建议

请开始您的回应：
"""
        
        return prompt
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """生成《家长决策博弈审计报告》"""
        # 收集所有论据
        all_arguments = []
        for round_obj in self.rounds:
            if round_obj.conservative_argument:
                all_arguments.append(round_obj.conservative_argument)
            if round_obj.aggressive_argument:
                all_arguments.append(round_obj.aggressive_argument)
        
        # 计算统计数据
        conservative_args = [a for a in all_arguments if a.role == DebateRole.CONSERVATIVE]
        aggressive_args = [a for a in all_arguments if a.role == DebateRole.AGGRESSIVE]
        
        conservative_avg_score = (
            sum(a.quality_score for a in conservative_args) / len(conservative_args)
            if conservative_args else 0
        )
        
        aggressive_avg_score = (
            sum(a.quality_score for a in aggressive_args) / len(aggressive_args)
            if aggressive_args else 0
        )
        
        # 交叉验证度
        cross_validation = self.scorer.calculate_cross_validation(all_arguments)
        
        # 生成报告
        report = {
            "report_type": "家长决策博弈审计报告",
            "topic": self.topic,
            "debate_config": {
                "max_rounds": self.max_rounds,
                "actual_rounds": len(self.rounds),
                "total_arguments": len(all_arguments)
            },
            "performance_summary": {
                "conservative": {
                    "argument_count": len(conservative_args),
                    "average_quality_score": round(conservative_avg_score, 3),
                    "total_fallacies": sum(len(a.logical_fallacies) for a in conservative_args),
                    "total_facts": sum(len(a.supporting_facts) for a in conservative_args)
                },
                "aggressive": {
                    "argument_count": len(aggressive_args),
                    "average_quality_score": round(aggressive_avg_score, 3),
                    "total_fallacies": sum(len(a.logical_fallacies) for a in aggressive_args),
                    "total_facts": sum(len(a.supporting_facts) for a in aggressive_args)
                }
            },
            "cross_validation_analysis": cross_validation,
            "round_by_round_analysis": [],
            "key_insights": self._extract_key_insights(all_arguments),
            "recommendation": self._generate_recommendation(
                conservative_avg_score, 
                aggressive_avg_score,
                cross_validation["cross_validation_score"]
            ),
            "generated_at": datetime.now().isoformat()
        }
        
        # 逐轮分析
        for i, round_obj in enumerate(self.rounds):
            round_analysis = {
                "round_number": i + 1,
                "conservative": None,
                "aggressive": None
            }
            
            if round_obj.conservative_argument:
                round_analysis["conservative"] = {
                    "quality_score": round_obj.conservative_argument.quality_score,
                    "has_facts": len(round_obj.conservative_argument.supporting_facts) > 0,
                    "has_fallacies": len(round_obj.conservative_argument.logical_fallacies) > 0
                }
            
            if round_obj.aggressive_argument:
                round_analysis["aggressive"] = {
                    "quality_score": round_obj.aggressive_argument.quality_score,
                    "has_facts": len(round_obj.aggressive_argument.supporting_facts) > 0,
                    "has_fallacies": len(round_obj.aggressive_argument.logical_fallacies) > 0
                }
            
            report["round_by_round_analysis"].append(round_analysis)
        
        return report
    
    def _extract_key_insights(self, arguments: List[DebateArgument]) -> List[str]:
        """提取关键洞察"""
        insights = []
        
        # 收集常见主题
        topics = Counter()
        for arg in arguments:
            content_lower = arg.content.lower()
            if "风险" in content_lower:
                topics["风险控制"] += 1
            if "收益" in content_lower or "优势" in content_lower:
                topics["收益最大化"] += 1
            if "数据" in content_lower or "统计" in content_lower:
                topics["数据驱动"] += 1
            if "预算" in content_lower or "财务" in content_lower:
                topics["财务考量"] += 1
        
        # 生成洞察
        if topics["风险控制"] > topics["收益最大化"]:
            insights.append("辩论更关注风险控制而非收益最大化，反映家长决策的谨慎倾向")
        else:
            insights.append("辩论更关注收益最大化，反映家长愿意为优质教育承担合理风险")
        
        if topics["数据驱动"] > 0:
            insights.append("双方都尝试引用数据支持观点，体现理性决策倾向")
        
        if any(arg.quality_score < 0.3 for arg in arguments):
            insights.append("部分论据质量较低，包含情绪化或绝对化表达")
        
        # 检查共识领域
        conservative_points = set()
        aggressive_points = set()
        
        for arg in arguments:
            if arg.role == DebateRole.CONSERVATIVE:
                conservative_points.update(self.scorer._extract_key_points(arg.content))
            else:
                aggressive_points.update(self.scorer._extract_key_points(arg.content))
        
        common_points = conservative_points.intersection(aggressive_points)
        if common_points:
            insights.append(f"双方在 {len(common_points)} 个关键点上存在共识")
        
        return insights
    
    def _generate_recommendation(self, conservative_score: float, aggressive_score: float, 
                               cross_validation: float) -> str:
        """生成最终建议"""
        score_diff = conservative_score - aggressive_score
        abs_diff = abs(score_diff)
        
        if cross_validation > 0.7:
            return "✅ 双方论据高度一致，决策风险较低。建议采用折中方案，兼顾双方优点。"
        elif abs_diff < 0.1:
            return "⚖️ 双方论据质量相当，决策存在显著分歧。建议进一步收集数据或咨询第三方专家。"
        elif score_diff > 0.2:
            return "🛡️ 保守派论据质量显著更高，建议优先考虑风险控制策略。"
        elif score_diff < -0.2:
            return "🚀 激进派论据质量显著更高，建议在可控风险范围内采纳高收益策略。"
        else:
            return "⚠️ 双方论据各有优劣，建议制定分阶段策略，先采用保守方案，根据进展灵活调整。"


# Mock Agents for testing
class MockAgent:
    """模拟Agent用于测试"""
    
    def __init__(self, name: str, role: DebateRole):
        self.name = name
        self.role = role
    
    def generate(self, prompt: str) -> str:
        """生成模拟回应"""
        if self.role == DebateRole.CONSERVATIVE:
            return f"""【保守派观点】我认为应该选择就近派位的稳妥方案。
            
主要论据：
1. 根据2023年海淀区教育统计，就近派位成功率高达85%
2. 跨区择校的交通时间成本过高，每天浪费1.5小时在路上
3. 风险可控，即使派位不理想，也有区内优质校保底

建议：选择第一志愿为就近派位学校，确保基本教育质量。"""
        else:
            return f"""【激进派观点】我认为应该尝试跨区科技特长生通道。
            
主要论据：
1. 目标学校的科技特长班高考重点率超过95%
2. 学生有编程竞赛基础，符合特长生申报条件
3. 长期收益远高于风险，即使失败也有区内派位保底

建议：积极准备特长生申报材料，同时填报就近派位作为备选。"""


if __name__ == "__main__":
    # 测试代码
    print("=== 辩论沙箱测试 ===")
    
    # 初始化沙箱
    sandbox = DebateSandbox(max_rounds=3)
    
    # 设置辩论主题和上下文
    topic = "海淀小升初：选择就近派位保守策略 vs 跨区科技特长生激进策略"
    context = {
        "student_profile": {
            "成绩水平": "中等偏上",
            "特长": "编程竞赛二等奖",
            "家庭住址": "海淀区中关村"
        },
        "policy_constraints": {
            "就近派位成功率": "85%",
            "科技特长生录取率": "15%",
            "跨区交通时间": "平均1.5小时/天"
        }
    }
    
    sandbox.initialize_debate(topic, context)
    
    # 创建模拟Agent
    conservative_agent = MockAgent("保守派顾问", DebateRole.CONSERVATIVE)
    aggressive_agent = MockAgent("激进派顾问", DebateRole.AGGRESSIVE)
    
    # 运行辩论
    rounds = sandbox.run_rigid_debate(conservative_agent, aggressive_agent)
    
    # 生成审计报告
    report = sandbox.generate_audit_report()
    
    print(f"\n辩论主题: {report['topic']}")
    print(f"辩论轮次: {report['debate_config']['actual_rounds']}")
    print(f"总论据数: {report['debate_config']['total_arguments']}")
    
    perf = report['performance_summary']
    print(f"\n保守派平均质量: {perf['conservative']['average_quality_score']:.3f}")
    print(f"激进派平均质量: {perf['aggressive']['average_quality_score']:.3f}")
    print(f"交叉验证度: {report['cross_validation_analysis']['cross_validation_score']:.3f}")
    
    print(f"\n关键洞察:")
    for insight in report['key_insights']:
        print(f"- {insight}")
    
    print(f"\n最终建议:")
    print(report['recommendation'])
    
    print("\n=== 测试完成 ===")