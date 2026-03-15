"""
Autonomous Agent Module
Implements multi-step reasoning and tool-calling using LangChain.
Built for the Enterprise GenAI Orchestrator.
"""

from typing import List, Optional, Any
from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from loguru import logger

class AutonomousAgent:
    """
    An enterprise-grade autonomous agent capable of solving complex tasks 
    through tool-calling and iterative reasoning.
    """

    def __init__(
        self,
        azure_endpoint: str,
        api_key: str,
        api_version: str,
        deployment_name: str,
        tools: Optional[List[Tool]] = None,
    ):
        """
        Initializes the agent with Azure OpenAI and a suite of tools.
        """
        self.llm = AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            openai_api_key=api_key,
            openai_api_version=api_version,
            azure_deployment=deployment_name,
            temperature=0,  # Strict reasoning
        )
        self.tools = tools or []
        self._setup_agent()
        logger.info(f"Initialized AutonomousAgent with {len(self.tools)} tools.")

    def _setup_agent(self):
        """
        Internal method to configure the LangChain agent with OpenAI functions.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert enterprise AI assistant. Your goal is to solve the user's "
                "task accurately and concisely. Use available tools to fetch data or "
                "perform actions when necessary. Follow a step-by-step reasoning process."
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create the agent using OpenAI Functions pattern
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

    async def run(self, user_input: str, chat_history: Optional[List[Any]] = None) -> str:
        """
        Executes the agent for a given user input.
        """
        logger.info(f"Agent received input: {user_input}")
        try:
            response = await self.agent_executor.ainvoke({
                "input": user_input,
                "chat_history": chat_history or [],
            })
            output = response.get("output", "No response generated.")
            logger.debug(f"Agent response: {output}")
            return output
        except Exception as e:
            logger.exception(f"Agent failed to execute: {str(e)}")
            return f"Error: {str(e)}"

# Example Tool
def get_company_revenue(ticker: str) -> str:
    """Mock tool for demonstration."""
    logger.info(f"Tool Call: Revenue lookup for {ticker}")
    return f"The revenue for {ticker} in Q4 2023 was $15.4B."

revenue_tool = Tool(
    name="CompanyRevenueLookup",
    func=get_company_revenue,
    description="Useful for finding the quarterly or annual revenue of a company using its ticker symbol."
)
