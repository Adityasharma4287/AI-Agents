# backend/agent/sellerpilot_agent.py
# ============================================================
# YEH FILE: Agent ka DIMAAG hai - sabse important file
# LangChain ka ReAct pattern use karta hai:
#   Reason (sochta hai) -> Act (kaam karta hai) -> Observe (result dekhta hai)
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# IMPORTS - Modern LangChain (v0.3+) compatible
# ============================================================
try:
    from langchain_openai import ChatOpenAI
    # Try modern import path first, fall back to classic
    try:
        from langchain.agents import AgentExecutor, create_react_agent
    except ImportError:
        from langchain.agents.agent import AgentExecutor
        from langchain.agents.react.agent import create_react_agent
    from langchain_core.prompts import PromptTemplate
    try:
        from langchain.memory import ConversationBufferWindowMemory
    except ImportError:
        from langchain_community.memory import ConversationBufferWindowMemory
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"LangChain import error: {e}")
    LANGCHAIN_AVAILABLE = False

from tools.agent_tools import ALL_TOOLS


# ============================================================
# SYSTEM PROMPT - Agent ki "personality" aur instructions
# ============================================================
AGENT_SYSTEM_PROMPT = """You are SellerPilot AI, an expert Amazon seller assistant agent for Indian sellers.

You have access to these tools:
{tools}

Tool names: {tool_names}

YOUR RESPONSIBILITIES:
1. Monitor inventory and alert when stock is low
2. Check listing health and identify suppressed listings
3. Find negative reviews and draft professional replies
4. Optimize ad campaigns by pausing high-ACOS campaigns
5. Generate daily store health reports

IMPORTANT RULES:
- Always use tools to check real data before making recommendations
- Never take irreversible actions without mentioning it in your response
- For listing changes and review replies, always ask for seller approval first
- Pausing ad campaigns is safe - you can do it automatically
- Sending alerts is safe - always do it when you find issues
- Be concise and action-oriented in your responses
- Always mention monetary impact when possible (how much money saved/at risk)

RESPONSE FORMAT:
- Start with a brief summary of what you checked
- List findings clearly with severity (Good, Warning, Critical)
- End with recommended next actions for the seller

Use the following format strictly:

Question: the input question you must answer
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


# ============================================================
# AGENT CLASS
# ============================================================
class SellerPilotAgent:
    def __init__(self):
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("LangChain is not installed. Run: pip install langchain langchain-openai langchain-core")

        # LLM - GPT-4o-mini (cheap & fast for testing; switch to gpt-4 for production)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Prompt template - using langchain_core.prompts
        self.prompt = PromptTemplate.from_template(AGENT_SYSTEM_PROMPT)

        # Memory - last 5 conversations yaad rakhega
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=5,
            return_messages=True
        )

        # ReAct Agent
        react_agent = create_react_agent(
            llm=self.llm,
            tools=ALL_TOOLS,
            prompt=self.prompt
        )

        # Agent Executor
        self.executor = AgentExecutor(
            agent=react_agent,
            tools=ALL_TOOLS,
            memory=self.memory,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )

        print("SellerPilot Agent initialized successfully with GPT!")

    def run(self, task: str) -> dict:
        """Agent ko ek task do aur result lo"""
        print(f"\nAgent Task: {task}")
        print("-" * 50)

        try:
            result = self.executor.invoke({"input": task})
            return {
                "success": True,
                "output": result["output"],
                "steps": len(result.get("intermediate_steps", [])),
                "task": task
            }
        except Exception as e:
            print(f"Agent Error: {e}")
            return {
                "success": False,
                "output": f"Agent encountered an error: {str(e)}",
                "steps": 0,
                "task": task
            }

    def run_daily_routine(self) -> dict:
        """Har subah automatically run hone wala routine"""
        print("\nRunning Daily Morning Routine...")

        tasks = [
            "Check inventory levels and send alerts for any low stock products",
            "Check all listings for any suppressed or unhealthy listings",
            "Find negative reviews from last 7 days and draft professional replies",
            "Analyze all ad campaigns and pause any with ACOS above 40%",
            "Generate a complete store health report"
        ]

        results = []
        for task in tasks:
            result = self.run(task)
            results.append(result)

        return {
            "routine": "daily_morning",
            "tasks_completed": len(results),
            "results": results,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }


# ============================================================
# MOCK AGENT - OpenAI key ke bina bhi test kar sako
# ============================================================
class MockSellerPilotAgent:
    """
    Development ke liye - OpenAI key nahi chahiye.
    Tools directly call karta hai without LLM.
    """

    def run(self, task: str) -> dict:
        from tools.agent_tools import (
            check_inventory_and_alert,
            check_and_fix_listings,
            monitor_reviews_and_draft_replies,
            optimize_ad_campaigns,
            generate_store_health_report
        )

        task_lower = task.lower()

        if "inventory" in task_lower or "stock" in task_lower:
            output = check_inventory_and_alert.invoke({"threshold_multiplier": 1.0})
        elif "listing" in task_lower or "suppressed" in task_lower:
            output = check_and_fix_listings.invoke({})
        elif "review" in task_lower:
            output = monitor_reviews_and_draft_replies.invoke({})
        elif "ad" in task_lower or "campaign" in task_lower or "acos" in task_lower:
            output = optimize_ad_campaigns.invoke({"acos_threshold": 40.0})
        else:
            output = generate_store_health_report.invoke({})

        return {"success": True, "output": output, "steps": 1, "task": task}

    def run_daily_routine(self) -> dict:
        results = []
        tasks = ["inventory check", "listing check", "review check", "ad optimization", "health report"]
        for task in tasks:
            results.append(self.run(task))
        return {"routine": "daily_morning", "tasks_completed": 5, "results": results}


# ============================================================
# FACTORY - OpenAI key milne par real agent, warna mock
# ============================================================
def create_agent():
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key.startswith("sk-") and LANGCHAIN_AVAILABLE:
        print("OpenAI key found - using real GPT agent")
        try:
            return SellerPilotAgent()
        except Exception as e:
            print(f"Failed to init real agent: {e}. Falling back to mock.")
            return MockSellerPilotAgent()
    else:
        print("No OpenAI key or LangChain missing - using Mock agent (for testing)")
        return MockSellerPilotAgent()


agent = create_agent()
