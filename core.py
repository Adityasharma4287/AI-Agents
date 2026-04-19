# backend/agent/core.py
# ─────────────────────────────────────────────────────────────
# THE MAIN AGENT — Uses Claude API with real tool_use protocol
# Exactly how Claude/Cursor/other agents work internally:
#   1. Send user message + tools to Claude
#   2. Claude responds with tool_use blocks
#   3. We run the tools → send results back
#   4. Claude gives final answer
# ─────────────────────────────────────────────────────────────

import os
import anthropic
from typing import Generator
from agent.tool_definitions import TOOL_DEFINITIONS
from agent.tool_executor import run_tool
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are SellerPilot AI, an expert AI agent for Indian Amazon sellers.

You have access to tools that connect to the seller's Amazon account.
When a seller asks you something, think about which tool(s) to use, call them, and give a clear response.

BEHAVIOR RULES:
- Always use tools when the question relates to inventory, ads, reviews, listings, or store health
- After getting tool results, give a clear, actionable summary in a friendly tone
- Mix Hindi and English naturally (Hinglish) — like "Aapke 2 products ka stock kam ho gaya hai"
- Always mention rupee amounts for financial impact
- For review replies, always say they need seller approval before posting
- Never make up data — only use what tools return
- Be concise but complete

TOOL USAGE:
- check_inventory → stock levels, low stock, reorder alerts
- optimize_ads → ACOS analysis, pause wasteful campaigns  
- monitor_reviews → negative reviews, draft professional replies
- check_listings → suppressed listings, buy box issues
- store_health_report → complete daily store audit"""


class SellerPilotAgent:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client = anthropic.Anthropic(api_key=api_key) if api_key.startswith("sk-ant") else None
        self.conversations: dict[str, list] = {}  # session_id → messages

    def _get_history(self, session_id: str) -> list:
        return self.conversations.setdefault(session_id, [])

    def _save_history(self, session_id: str, messages: list):
        # Keep last 20 messages to avoid token overflow
        self.conversations[session_id] = messages[-20:]

    def chat(self, user_message: str, session_id: str = "default") -> dict:
        """
        Full agent loop:
        user → Claude → (tool calls) → Claude → final answer
        Returns dict with answer + tool_calls used
        """
        if not self.client:
            return self._mock_response(user_message)

        history = self._get_history(session_id)
        history.append({"role": "user", "content": user_message})

        tool_calls_made = []
        max_rounds = 5  # prevent infinite loops

        for round_num in range(max_rounds):
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=history,
            )

            # Extract text and tool uses from response
            assistant_content = response.content
            history.append({"role": "assistant", "content": assistant_content})

            # Check if Claude wants to use tools
            tool_uses = [b for b in assistant_content if b.type == "tool_use"]

            if not tool_uses:
                # No more tool calls → Claude gave final answer
                final_text = next(
                    (b.text for b in assistant_content if hasattr(b, "text")), ""
                )
                self._save_history(session_id, history)
                return {
                    "answer": final_text,
                    "tool_calls": tool_calls_made,
                    "rounds": round_num + 1,
                }

            # Run each tool and send results back
            tool_results = []
            for tool_use in tool_uses:
                tool_result = run_tool(tool_use.name, tool_use.input)
                tool_calls_made.append({
                    "tool": tool_use.name,
                    "input": tool_use.input,
                    "result_preview": tool_result[:200],
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": tool_result,
                })

            history.append({"role": "user", "content": tool_results})

        # Fallback
        self._save_history(session_id, history)
        return {"answer": "Max tool rounds reached.", "tool_calls": tool_calls_made, "rounds": max_rounds}

    def chat_stream(self, user_message: str, session_id: str = "default") -> Generator:
        """
        Streaming version — yields events in real time:
        { type: "thinking", text }
        { type: "tool_start", tool_name, tool_input }
        { type: "tool_result", tool_name, result }
        { type: "text", text }
        { type: "done" }
        """
        if not self.client:
            yield from self._mock_stream(user_message)
            return

        history = self._get_history(session_id)
        history.append({"role": "user", "content": user_message})

        tool_calls_made = []

        for round_num in range(5):
            # Collect full response (streaming in background, emit events)
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=history,
            )

            assistant_content = response.content
            history.append({"role": "assistant", "content": assistant_content})

            tool_uses = [b for b in assistant_content if b.type == "tool_use"]

            # Stream text chunks
            for block in assistant_content:
                if hasattr(block, "text") and block.text:
                    yield {"type": "text", "text": block.text}

            if not tool_uses:
                break

            # Emit tool events
            tool_results = []
            for tu in tool_uses:
                yield {"type": "tool_start", "tool_name": tu.name, "tool_input": tu.input}
                result = run_tool(tu.name, tu.input)
                yield {"type": "tool_result", "tool_name": tu.name, "result": result}
                tool_calls_made.append({"tool": tu.name})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result,
                })

            history.append({"role": "user", "content": tool_results})

        self._save_history(session_id, history)
        yield {"type": "done", "tool_calls": tool_calls_made}

    def clear_history(self, session_id: str):
        self.conversations.pop(session_id, None)

    # ── MOCK (no API key) ────────────────────────────────────
    def _mock_response(self, query: str) -> dict:
        from agent.tool_executor import run_tool
        q = query.lower()
        tool = (
            "check_inventory"    if any(w in q for w in ["stock","inventory","maal","units"]) else
            "optimize_ads"       if any(w in q for w in ["ad","acos","campaign","paisa"]) else
            "monitor_reviews"    if any(w in q for w in ["review","star","reply","complaint"]) else
            "check_listings"     if any(w in q for w in ["listing","suppress","buybox","buy box"]) else
            "store_health_report"
        )
        result = run_tool(tool, {})
        return {"answer": result, "tool_calls": [{"tool": tool}], "rounds": 1}

    def _mock_stream(self, query: str):
        import time
        q = query.lower()
        tool = (
            "check_inventory"    if any(w in q for w in ["stock","inventory","maal","units"]) else
            "optimize_ads"       if any(w in q for w in ["ad","acos","campaign","paisa"]) else
            "monitor_reviews"    if any(w in q for w in ["review","star","reply","complaint"]) else
            "check_listings"     if any(w in q for w in ["listing","suppress","buybox","buy box"]) else
            "store_health_report"
        )
        yield {"type": "thinking", "text": f"Analyzing query... selecting tool: {tool}"}
        yield {"type": "tool_start", "tool_name": tool, "tool_input": {}}
        result = run_tool(tool, {})
        yield {"type": "tool_result", "tool_name": tool, "result": result}
        # stream answer word by word
        for word in result.split():
            yield {"type": "text", "text": word + " "}
        yield {"type": "done", "tool_calls": [{"tool": tool}]}


# Singleton
agent = SellerPilotAgent()
