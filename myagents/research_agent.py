# research_agent.py - Web research agent using MCP servers

import asyncio
from contextlib import AsyncExitStack
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

# We'll use a simplified version of the agents framework for now
# In production, you'd install: pip install openai-agents-sdk
try:
    from agents import Agent, Runner
    from agents.mcp import MCPServerStdio
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False
    print("OpenAI Agents SDK not available. Using simplified implementation.")

from config.mcp_config import get_research_mcp_server_params

logger = logging.getLogger(__name__)

class SimpleResearchAgent:
    """
    Simplified research agent for when OpenAI Agents SDK is not available
    This is a placeholder that we'll enhance step by step
    """
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.mcp_servers = []
        
    async def research_company(self, company_website: str, company_description: str = "") -> str:
        """Research a company using web search"""
        
        research_summary = f"""I see you're with {company_website if company_website else 'your company'}! Based on your {company_description if company_description else 'transportation operations'}, our GPS tracking and route optimization could really help cut fuel costs by about 15-25%. Would you like to see a quick demo of how this works for companies like yours?"""
        
        return research_summary.strip()
    
    async def research_question(self, question: str, context: Dict[str, Any] = None) -> str:
        """Research a specific question about Fleetworthy services"""
        
        # Extract relevant context
        company_info = ""
        if context:
            website = context.get('company_website', '')
            if website:
                company_info = f" for {website}"
        
        research_response = f"""Great question! For fleet management{company_info}, our route optimization and fuel tracking typically help companies save 15-25% on fuel costs while improving on-time deliveries by about 20%. Plus our ELD compliance features handle all the DOT requirements automatically. I'd love to show you how this could work specifically for your operation - would you be interested in a quick demo?"""
        
        return research_response.strip()

class MCPResearchAgent:
    """
    Full MCP-powered research agent using OpenAI Agents SDK
    """
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.agent = None
        
    async def _create_agent(self, mcp_servers: List[Any]) -> Any:
        """Create the research agent with MCP servers"""
        
        instructions = f"""
        You are a friendly sales agent for Fleetworthy, a fleet management software company.
        
        Your style: Conversational, helpful, and concise. Think of this as a casual business chat, not a formal presentation.
        
        Your process:
        1. Research the company using web search and website content
        2. Understand their fleet operations and challenges
        3. Suggest 2-3 relevant Fleetworthy solutions in a friendly way
        4. Keep responses to 2-4 sentences maximum
        5. Store key findings in memory for future conversations
        
        Available Fleetworthy Solutions:
        - GPS Fleet Tracking & Real-time Visibility
        - Route Optimization & Fuel Management  
        - Driver Behavior Monitoring & Safety
        - Maintenance Management & Scheduling
        - ELD Compliance & Hours of Service
        - Dispatch & Load Optimization
        - Cost Analytics & Reporting
        
        Response format: 
        - Keep it conversational and brief
        - Focus on 1-2 key benefits that match their business
        - Include one specific benefit (like "15% fuel savings")
        - End with a friendly next step suggestion
        
        Current datetime: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        self.agent = Agent(
            name="FleetResearcher",
            instructions=instructions,
            model="gpt-4o-mini",  # or "gpt-4" for better results
            mcp_servers=mcp_servers
        )
        return self.agent
        
    async def research_company(self, company_website: str, company_description: str = "") -> str:
        """Research a company using MCP tools"""
        
        research_prompt = f"""
        Research this company and provide a brief, conversational response:
        
        Company Website: {company_website}
        Company Description: {company_description}
        
        Research steps:
        1. Search for basic info about this company's transportation/logistics operations
        2. If website provided, fetch key details about their business
        3. Identify 1-2 main challenges they likely face
        4. Suggest relevant Fleetworthy solutions in 2-3 friendly sentences
        5. Store key findings in memory
        
        Response style: Casual and conversational, like you're having a friendly business chat.
        Length: Keep it to 2-4 sentences maximum.
        Focus: One key benefit that matches their specific business needs.
        """
        
        try:
            async with AsyncExitStack() as stack:
                mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in get_research_mcp_server_params(self.session_id)
                ]
                
                agent = await self._create_agent(mcp_servers)
                result = await Runner.run(agent, research_prompt, max_turns=15)
                return result.final_output
                
        except Exception as e:
            logger.error(f"Error in MCP research: {e}")
            # Fallback to simple research
            simple_agent = SimpleResearchAgent(self.session_id)
            return await simple_agent.research_company(company_website, company_description)
    
    async def research_question(self, question: str, context: Dict[str, Any] = None) -> str:
        """Research a specific question using MCP tools"""
        
        context_info = ""
        if context:
            website = context.get('company_website', '')
            description = context.get('company_description', '')
            if website or description:
                context_info = f"\nCompany context - Website: {website}, Description: {description}"
        
        research_prompt = f"""
        A potential customer asked: "{question}"{context_info}
        
        Provide a brief, helpful response:
        1. Search for relevant industry information if needed
        2. Give a conversational answer about Fleetworthy solutions
        3. Keep it to 2-4 sentences maximum
        4. Include one specific benefit or statistic
        5. Store any useful findings in memory
        
        Response style: Friendly and conversational, not a formal sales pitch.
        Focus: Direct answer to their question with one relevant Fleetworthy solution.
        """
        
        try:
            async with AsyncExitStack() as stack:
                mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in get_research_mcp_server_params(self.session_id)
                ]
                
                agent = await self._create_agent(mcp_servers)
                result = await Runner.run(agent, research_prompt, max_turns=15)
                return result.final_output
                
        except Exception as e:
            logger.error(f"Error in MCP research: {e}")
            # Fallback to simple research
            simple_agent = SimpleResearchAgent(self.session_id)
            return await simple_agent.research_question(question, context)

# Factory function to create the appropriate research agent
def create_research_agent(session_id: str = "default"):
    """Create a research agent based on available dependencies"""
    if AGENTS_SDK_AVAILABLE:
        return MCPResearchAgent(session_id)
    else:
        return SimpleResearchAgent(session_id)