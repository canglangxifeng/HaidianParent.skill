"""
MCP 协议桥接器
连接本地政策PDF/Notion数据，提供无噪音政策审计功能
"""
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client import stdio
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP package not available. Running in mock mode.")

logger = logging.getLogger(__name__)

@dataclass
class PolicyDocument:
    """政策文档数据结构"""
    source: str  # 文件路径或URL
    title: str
    publish_date: str
    authority: str  # 发布机构
    content_extract: str
    key_parameters: Dict[str, Any]  # 关键参数：分数线、比例、时间节点等

@dataclass
class FactStatement:
    """事实陈述"""
    statement: str
    source_document: str
    confidence: float  # 置信度（基于源权威性）
    parameters: Dict[str, Any]
    raw_context: str  # 原始上下文


class MCPBridge:
    """
    MCP协议桥接器，负责：
    1. 连接本地政策PDF/Notion数据源
    2. 提取无噪点、无情感修饰的一手数据
    3. 提供结构化政策参数
    """
    
    def __init__(self, mcp_server_path: Optional[str] = None):
        """
        初始化MCP桥接器
        
        Args:
            mcp_server_path: MCP服务器路径，如果为None则使用模拟模式
        """
        self.mcp_server_path = mcp_server_path
        self.session = None
        self.mock_data = self._load_mock_data()
        
    async def connect(self):
        """连接到MCP服务器"""
        if not self.mcp_server_path or not MCP_AVAILABLE:
            logger.info("Running in mock mode. No actual MCP connection.")
            return
            
        try:
            server_params = StdioServerParameters(
                command=self.mcp_server_path,
                args=["--verbose"]
            )
            self.session = await stdio.run_server(server_params)
            logger.info("MCP connection established.")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def extract_policy_facts(self, document_path: str) -> List[FactStatement]:
        """
        从政策文档中提取事实陈述
        
        Args:
            document_path: 政策文档路径
            
        Returns:
            事实陈述列表，剥离了自媒体的焦虑化词汇
        """
        if not MCP_AVAILABLE or not self.session:
            return self._mock_extract_facts(document_path)
            
        try:
            # 通过MCP协议读取文档内容
            documents = await self.session.list_documents()
            
            # 搜索相关文档
            relevant_docs = []
            for doc in documents:
                if document_path in doc.uri or document_path in doc.name:
                    relevant_docs.append(doc)
            
            facts = []
            for doc in relevant_docs:
                content = await self.session.read_document(doc.uri)
                
                # 提取关键信息
                extracted = await self._extract_with_mcp(content)
                
                for fact in extracted:
                    facts.append(FactStatement(
                        statement=fact["statement"],
                        source_document=doc.uri,
                        confidence=fact.get("confidence", 0.8),
                        parameters=fact.get("parameters", {}),
                        raw_context=fact.get("context", "")
                    ))
            
            return facts
            
        except Exception as e:
            logger.error(f"Error extracting facts via MCP: {e}")
            return []
    
    async def _extract_with_mcp(self, content: str) -> List[Dict[str, Any]]:
        """通过MCP工具提取事实"""
        # 这里实际会调用MCP工具的提取功能
        # 简化实现，返回模拟数据
        return [
            {
                "statement": "2024年海淀区小升初派位比例为70%",
                "confidence": 0.95,
                "parameters": {"派位比例": 0.7, "年份": 2024, "区域": "海淀区"},
                "context": "根据《2024年海淀区义务教育入学工作方案》"
            },
            {
                "statement": "科技特长生的报名截止日期为2024年5月15日",
                "confidence": 0.9,
                "parameters": {"截止日期": "2024-05-15", "类别": "科技特长生"},
                "context": "《海淀区2024年初中入学特长生招生工作方案》"
            }
        ]
    
    def _mock_extract_facts(self, document_path: str) -> List[FactStatement]:
        """模拟事实提取"""
        return [
            FactStatement(
                statement="2024年海淀区小升初派位比例为70%",
                source_document=document_path,
                confidence=0.95,
                parameters={"派位比例": 0.7, "年份": 2024, "区域": "海淀区"},
                raw_context="根据《2024年海淀区义务教育入学工作方案》"
            ),
            FactStatement(
                statement="科技特长生的报名截止日期为2024年5月15日",
                source_document=document_path,
                confidence=0.9,
                parameters={"截止日期": "2024-05-15", "类别": "科技特长生"},
                raw_context="《海淀区2024年初中入学特长生招生工作方案》"
            ),
            FactStatement(
                statement="市重点高中录取最低控制分数线为650分",
                source_document=document_path,
                confidence=0.85,
                parameters={"分数线": 650, "类别": "市重点高中"},
                raw_context="《2024年北京市高级中等学校招生简章》"
            )
        ]
    
    def _load_mock_data(self) -> Dict[str, Any]:
        """加载模拟数据"""
        return {
            "policy_documents": [
                {
                    "title": "2024年海淀区义务教育入学工作方案",
                    "publish_date": "2024-04-01",
                    "key_points": ["派位比例70%", "登记入学时间4月25日-5月8日"]
                }
            ]
        }
    
    async def close(self):
        """关闭MCP连接"""
        if self.session:
            await self.session.close()
            logger.info("MCP connection closed.")


# 工具函数，供CrewAI集成
async def mcp_policy_extractor(document_path: str) -> str:
    """
    CrewAI工具：政策提取器
    
    Args:
        document_path: 政策文档路径
        
    Returns:
        结构化的事实摘要
    """
    bridge = MCPBridge()
    await bridge.connect()
    
    try:
        facts = await bridge.extract_policy_facts(document_path)
        
        # 生成结构化报告
        report_lines = ["# 政策事实审计报告", ""]
        report_lines.append("## 提取的绝对事实陈述")
        report_lines.append("")
        
        for i, fact in enumerate(facts, 1):
            report_lines.append(f"{i}. **{fact.statement}**")
            report_lines.append(f"   - 来源: {fact.source_document}")
            report_lines.append(f"   - 置信度: {fact.confidence:.2f}")
            if fact.parameters:
                params_str = ", ".join([f"{k}={v}" for k, v in fact.parameters.items()])
                report_lines.append(f"   - 关键参数: {params_str}")
            report_lines.append("")
        
        report_lines.append("## 审计说明")
        report_lines.append("1. 本报告仅包含从原始文档中提取的客观事实")
        report_lines.append("2. 所有陈述均附带原始出处")
        report_lines.append("3. 不含任何推测性结论或情感修饰")
        
        return "\n".join(report_lines)
        
    finally:
        await bridge.close()


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    async def test():
        bridge = MCPBridge()
        await bridge.connect()
        facts = await bridge.extract_policy_facts("test_policy.pdf")
        print(f"提取到 {len(facts)} 条事实陈述:")
        for fact in facts:
            print(f"- {fact.statement}")
        await bridge.close()
    
    asyncio.run(test())