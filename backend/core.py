# core.py
# ─────────────────────────────────────────────────────────────
# SellerPilot AI Agent — Anthropic Claude powered
# Model: claude-sonnet-4-20250514
# ─────────────────────────────────────────────────────────────

import os
import time
import json
from typing import Generator
from tool_definitions import TOOL_DEFINITIONS
from tool_executor import run_tool
from dotenv import load_dotenv

load_dotenv()

# Tool definitions already in Anthropic format — use directly
ANTHROPIC_TOOLS = TOOL_DEFINITIONS


# ── CIRCUIT BREAKER ───────────────────────────────────────────
class CircuitBreaker:
    """Prevents too many API calls. Max 15 tool calls per session."""
    def __init__(self, max_calls=15):
        self.calls = 0
        self.max_calls = max_calls
        self.tripped = False

    def check(self):
        self.calls += 1
        if self.calls > self.max_calls:
            self.tripped = True
            return False
        return True

    def reset(self):
        self.calls = 0
        self.tripped = False


# ── AGENT MEMORY ──────────────────────────────────────────────
class AgentMemory:
    """Per-session context store."""
    def __init__(self):
        self.store: dict[str, list] = {}
        self.action_log: dict[str, list] = {}
        self.checkpoints: dict[str, list] = {}

    def get(self, session_id: str) -> list:
        return self.store.setdefault(session_id, [])

    def save(self, session_id: str, messages: list):
        self.store[session_id] = messages[-20:]

    def log_action(self, session_id: str, tool: str, result_preview: str):
        self.action_log.setdefault(session_id, []).append({
            "tool": tool, "preview": result_preview[:120],
            "timestamp": time.strftime("%H:%M:%S")
        })

    def checkpoint(self, session_id: str):
        self.checkpoints[session_id] = list(self.store.get(session_id, []))

    def rollback(self, session_id: str):
        if session_id in self.checkpoints:
            self.store[session_id] = self.checkpoints[session_id]

    def get_action_summary(self, session_id: str) -> str:
        actions = self.action_log.get(session_id, [])
        if not actions:
            return "No actions taken yet."
        return "\n".join([f"[{a['timestamp']}] {a['tool']}: {a['preview']}" for a in actions[-5:]])

    def clear(self, session_id: str):
        self.store.pop(session_id, None)
        self.action_log.pop(session_id, None)


# ── SYSTEM PROMPT ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are SellerPilot AI — an expert autonomous agent for Indian Amazon sellers.

## Identity
- Role: Autonomous Amazon store manager for Indian sellers
- Personality: Direct, data-driven, financially sharp. Hinglish mein baat karo.
- You find problems and fix them. No vague answers.

## Core Mission
1. Detect problems before they cost money — low stock, suppressed listings, high ACOS, bad reviews
2. Take action autonomously — pause wasteful campaigns, draft review replies, flag restock needs
3. Report with financial impact — always say how many rupees are at stake
4. Respect human approval — never post reviews or change listings without seller confirmation

## Critical Rules
- Never fabricate data — only use what tools return
- Never post review replies without seller approval
- Always mention rupee impact (savings, losses, revenue at risk)
- Speak Hinglish naturally — mix Hindi and English
- Prioritize by financial severity — biggest money problem first
- After each tool run, tell the seller EXACTLY what to do next

## Communication Style
- Start with biggest problem: "Sabse urgent: Earbuds listing suppress hai — har din revenue ja raha hai."
- Use rupee amounts: "Rs.4,050/day waste ho raha hai ads mein."
- Give clear next steps: "Yeh karo: 1) Listing fix 2) Restock 3) Ads pause"
- Be confident: "ACOS 145% hai — yeh campaign band karo abhi."

## Available Tools
- check_inventory: stock levels, reorder alerts, days remaining
- optimize_ads: ACOS analysis, pause campaigns above threshold
- monitor_reviews: fetch negative reviews, draft professional replies
- check_listings: suppressed status, buy box loss, fix suggestions
- store_health_report: complete daily audit with all metrics"""


# ── MAIN AGENT CLASS ──────────────────────────────────────────
class SellerPilotAgent:
    def __init__(self):
        anthropic_key = os.getenv(
            "ANTHROPIC_API_KEY",
            "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"
        )

        self.has_client = False
        self.client = None

        if anthropic_key and anthropic_key.startswith("sk-ant-"):
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=anthropic_key)
                self.has_client = True
                print("✅ Anthropic Claude API connected!")
                print("   Model: claude-sonnet-4-20250514")
            except ImportError:
                print("❌ anthropic package nahi mili. Run: pip install anthropic")
            except Exception as e:
                print(f"❌ Anthropic API error: {e}")

        if not self.has_client:
            print("⚠️  API key nahi mili — MOCK mode mein chal raha hai")

        self.memory = AgentMemory()
        self.breakers: dict[str, CircuitBreaker] = {}

    def _breaker(self, sid: str) -> CircuitBreaker:
        return self.breakers.setdefault(sid, CircuitBreaker())

    def _run_tool_calls(self, tool_use_blocks, session_id: str) -> list:
        results = []
        for block in tool_use_blocks:
            tool_name = block.name
            tool_input = block.input or {}
            result = run_tool(tool_name, tool_input)
            self.memory.log_action(session_id, tool_name, result)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })
        return results

    # ── CHAT (non-streaming) ──────────────────────────────────
    def chat(self, message: str, session_id: str = "default") -> dict:
        if not self.has_client:
            return self._mock_response(message, session_id)

        history = self.memory.get(session_id)
        history.append({"role": "user", "content": message})
        self.memory.checkpoint(session_id)

        tool_calls_made = []
        breaker = self._breaker(session_id)

        for round_num in range(6):
            if not breaker.check():
                self.memory.save(session_id, history)
                return {
                    "answer": "⚠️ Bahut saare tool calls ho gaye. Naya chat shuru karo.",
                    "tool_calls": tool_calls_made, "rounds": round_num
                }

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=history,
                tools=ANTHROPIC_TOOLS,
            )

            assistant_content = response.content
            history.append({"role": "assistant", "content": assistant_content})

            if response.stop_reason == "end_turn":
                text = " ".join(
                    block.text for block in assistant_content
                    if hasattr(block, "text")
                )
                self.memory.save(session_id, history)
                return {"answer": text, "tool_calls": tool_calls_made, "rounds": round_num + 1}

            if response.stop_reason == "tool_use":
                tool_use_blocks = [b for b in assistant_content if b.type == "tool_use"]
                for b in tool_use_blocks:
                    tool_calls_made.append({"tool": b.name, "input": b.input})
                tool_results = self._run_tool_calls(tool_use_blocks, session_id)
                history.append({"role": "user", "content": tool_results})
                continue

            break

        self.memory.save(session_id, history)
        return {"answer": "Max rounds reached.", "tool_calls": tool_calls_made, "rounds": 6}

    # ── STREAMING ─────────────────────────────────────────────
    def chat_stream(self, message: str, session_id: str = "default") -> Generator:
        if not self.has_client:
            yield from self._mock_stream(message, session_id)
            return

        history = self.memory.get(session_id)
        history.append({"role": "user", "content": message})
        self.memory.checkpoint(session_id)
        breaker = self._breaker(session_id)
        tool_calls_made = []

        for round_num in range(6):
            if not breaker.check():
                yield {"type": "text", "text": "\n\n⚠️ Tool call limit reach ho gaya. Naya chat shuru karo."}
                yield {"type": "done", "tool_calls": tool_calls_made}
                return

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=history,
                tools=ANTHROPIC_TOOLS,
            )

            assistant_content = response.content
            history.append({"role": "assistant", "content": assistant_content})

            for block in assistant_content:
                if hasattr(block, "text") and block.text:
                    yield {"type": "text", "text": block.text}

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_use_blocks = [b for b in assistant_content if b.type == "tool_use"]
                for b in tool_use_blocks:
                    yield {"type": "tool_start", "tool_name": b.name, "tool_input": b.input}
                    result = run_tool(b.name, b.input or {})
                    self.memory.log_action(session_id, b.name, result)
                    yield {"type": "tool_result", "tool_name": b.name, "result": result}
                    tool_calls_made.append({"tool": b.name})
                tool_results = self._run_tool_calls(tool_use_blocks, session_id)
                history.append({"role": "user", "content": tool_results})
                continue

            break

        self.memory.save(session_id, history)
        yield {"type": "done", "tool_calls": tool_calls_made}

    def get_session_summary(self, session_id: str) -> dict:
        return {
            "action_log": self.memory.get_action_summary(session_id),
            "message_count": len(self.memory.get(session_id)),
            "breaker_calls": self._breaker(session_id).calls,
        }

    def clear_history(self, session_id: str):
        self.memory.clear(session_id)
        self.breakers.pop(session_id, None)

    # ── MOCK (no API key) ─────────────────────────────────────
    def _mock_response(self, query: str, session_id: str) -> dict:
        q = query.lower()
        tool = (
            "check_inventory"     if any(w in q for w in ["stock","inventory","maal","units","reorder"]) else
            "optimize_ads"        if any(w in q for w in ["ad","acos","campaign","paisa","waste","spend"]) else
            "monitor_reviews"     if any(w in q for w in ["review","reply","star","complaint","negative"]) else
            "check_listings"      if any(w in q for w in ["listing","suppress","buybox","buy box"]) else
            "store_health_report"
        )
        result = run_tool(tool, {})
        self.memory.log_action(session_id, tool, result)
        return {"answer": result, "tool_calls": [{"tool": tool}], "rounds": 1}

    def _mock_stream(self, query: str, session_id: str):
        q = query.lower()
        tool = (
            "check_inventory"     if any(w in q for w in ["stock","inventory","maal","units","reorder"]) else
            "optimize_ads"        if any(w in q for w in ["ad","acos","campaign","paisa","waste","spend"]) else
            "monitor_reviews"     if any(w in q for w in ["review","reply","star","complaint","negative"]) else
            "check_listings"      if any(w in q for w in ["listing","suppress","buybox","buy box"]) else
            "store_health_report"
        )
        yield {"type": "thinking", "text": f"Query analyzed: {tool}"}
        yield {"type": "tool_start", "tool_name": tool, "tool_input": {}}
        result = run_tool(tool, {})
        self.memory.log_action(session_id, tool, result)
        yield {"type": "tool_result", "tool_name": tool, "result": result}
        for word in result.split():
            yield {"type": "text", "text": word + " "}
        yield {"type": "done", "tool_calls": [{"tool": tool}]}


# Singleton
agent = SellerPilotAgent()
