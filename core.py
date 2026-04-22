# backend/agent/core.py
# ─────────────────────────────────────────────────────────────
# SellerPilot AI Agent — Built with agency-agents patterns:
#   · Strong personality & memory (from AI Engineer agent)
#   · Circuit breaker guardrails (from Autonomous Optimization Architect)
#   · Quality-gated workflow (from Agents Orchestrator)
#   · Measurable success metrics (from PPC Strategist)
#   · Multi-tool orchestration with state tracking
# ─────────────────────────────────────────────────────────────

import os
import time
import json
from typing import Generator
from agent.tool_definitions import TOOL_DEFINITIONS
from agent.tool_executor import run_tool
from dotenv import load_dotenv

load_dotenv()

# ── CIRCUIT BREAKER (from Autonomous Optimization Architect) ──
class CircuitBreaker:
    """Prevents runaway API costs. Max 10 tool calls per session."""
    def __init__(self, max_calls=10, max_cost_usd=0.50):
        self.calls = 0
        self.cost = 0.0
        self.max_calls = max_calls
        self.max_cost = max_cost_usd
        self.tripped = False

    def check(self, tokens_estimate=500):
        cost_per_call = (tokens_estimate / 1_000_000) * 3.0  # claude-sonnet pricing
        self.calls += 1
        self.cost += cost_per_call
        if self.calls > self.max_calls or self.cost > self.max_cost:
            self.tripped = True
            return False
        return True

    def reset(self):
        self.calls = 0; self.cost = 0.0; self.tripped = False


# ── AGENT MEMORY (from workflow-with-memory pattern) ─────────
class AgentMemory:
    """Per-session context store — agents remember previous actions."""
    def __init__(self):
        self.store: dict[str, list] = {}  # session_id → message history
        self.action_log: dict[str, list] = {}  # session_id → tools called
        self.checkpoints: dict[str, list] = {}  # session_id → rollback points

    def get(self, session_id: str) -> list:
        return self.store.setdefault(session_id, [])

    def save(self, session_id: str, messages: list):
        self.store[session_id] = messages[-20:]  # keep last 20

    def log_action(self, session_id: str, tool: str, result_preview: str):
        self.action_log.setdefault(session_id, []).append({
            "tool": tool, "preview": result_preview[:120],
            "timestamp": time.strftime("%H:%M:%S")
        })

    def checkpoint(self, session_id: str):
        """Save rollback point (from memory workflow pattern)."""
        self.checkpoints[session_id] = list(self.store.get(session_id, []))

    def rollback(self, session_id: str):
        """Restore last checkpoint."""
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


# ── SYSTEM PROMPT — agency-agents style with strong personality ──
SYSTEM_PROMPT = """---
name: SellerPilot AI
role: Expert autonomous agent for Indian Amazon sellers
personality: Data-driven, financially ruthless about waste, proactive, Hinglish-fluent
vibe: Your Amazon store's 24/7 guardian — finds the waste before your accountant does.
---

# SellerPilot AI Agent

## 🧠 Identity & Memory
- **Role**: Autonomous Amazon store manager for Indian sellers
- **Personality**: Direct, data-driven, financially sharp. I don't hedge — I find the problem and fix it.
- **Memory**: I remember every tool I've run this session. I track what I've already checked so I don't repeat work.
- **Experience**: I've seen sellers lose ₹1.5L/month to bad ACOS. I've seen suppressed listings kill revenue for days. I prevent both.

## 🎯 Core Mission
1. **Detect problems before they cost money** — low stock, suppressed listings, high ACOS, bad reviews
2. **Take action autonomously** — pause wasteful campaigns, draft review replies, flag restock needs
3. **Report with financial impact** — always say how many rupees are at stake
4. **Respect human approval** — never post reviews or change listings without seller confirmation

## 🚨 Critical Rules (Circuit Breaker Guardrails)
- ❌ Never fabricate data — only use what tools return
- ❌ Never post review replies without seller approval
- ❌ Never make more than 3 consecutive tool calls without summarizing
- ✅ Always mention rupee impact (savings, losses, revenue at risk)
- ✅ Speak Hinglish naturally — mix Hindi and English like a real Indian seller would
- ✅ Prioritize by financial severity — biggest money problem first
- ✅ After each tool run, tell the seller EXACTLY what to do next

## 📋 Tool Usage (Orchestrator Pattern)
Run tools in this quality-gated order when doing a full check:
1. `store_health_report` → get full picture first
2. `check_inventory` → flag critical stockouts
3. `check_listings` → find suppressed/broken listings
4. `monitor_reviews` → draft replies for negative reviews
5. `optimize_ads` → pause wasteful campaigns last (most impactful)

For single questions, pick the ONE most relevant tool. Don't over-call.

## 💭 Communication Style
- Start with the biggest problem: "Sabse urgent: Earbuds listing suppress hai — har din revenue ja raha hai."
- Use rupee amounts always: "₹4,050/day waste ho raha hai ads mein."
- Give clear next steps: "Yeh karo: 1) Listing fix 2) Restock 3) Ads pause"
- Be confident, not vague: "ACOS 145% hai — yeh campaign band karo abhi."

## 🎯 Success Metrics (from PPC Strategist pattern)
I'm doing my job when:
- ACOS drops below 30% on optimized campaigns
- Zero suppressed listings remain unaddressed >24 hours
- All negative reviews have drafted replies within 1 hour
- Low stock alerts sent before stockout (not after)
- Seller saves measurable rupees from my recommendations

## 🔄 Available Tools
- `check_inventory` → stock levels, reorder alerts, days remaining
- `optimize_ads` → ACOS analysis, pause campaigns above threshold
- `monitor_reviews` → fetch negative reviews, draft professional replies
- `check_listings` → suppressed status, buy box loss, fix suggestions
- `store_health_report` → complete daily audit with all metrics"""


# ── MAIN AGENT CLASS ──────────────────────────────────────────
class SellerPilotAgent:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.has_client = api_key.startswith("sk-ant")
        if self.has_client:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        self.memory = AgentMemory()
        self.breakers: dict[str, CircuitBreaker] = {}

    def _breaker(self, sid: str) -> CircuitBreaker:
        return self.breakers.setdefault(sid, CircuitBreaker())

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
                    "answer": "⚠️ Circuit breaker tripped — too many tool calls in one session. Cost limit reached. Please start a new chat.",
                    "tool_calls": tool_calls_made, "rounds": round_num
                }

            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=history,
            )

            content = response.content
            history.append({"role": "assistant", "content": content})
            tool_uses = [b for b in content if b.type == "tool_use"]

            if not tool_uses:
                final = next((b.text for b in content if hasattr(b, "text")), "")
                self.memory.save(session_id, history)
                return {"answer": final, "tool_calls": tool_calls_made, "rounds": round_num + 1}

            tool_results = []
            for tu in tool_uses:
                result = run_tool(tu.name, tu.input)
                self.memory.log_action(session_id, tu.name, result)
                tool_calls_made.append({"tool": tu.name, "input": tu.input})
                tool_results.append({"type": "tool_result", "tool_use_id": tu.id, "content": result})

            history.append({"role": "user", "content": tool_results})

        self.memory.save(session_id, history)
        return {"answer": "Max rounds reached.", "tool_calls": tool_calls_made, "rounds": 6}

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
                yield {"type": "text", "text": "\n\n⚠️ Circuit breaker tripped — cost limit reached. Start a new chat."}
                yield {"type": "done", "tool_calls": tool_calls_made}
                return

            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=history,
            )

            content = response.content
            history.append({"role": "assistant", "content": content})
            tool_uses = [b for b in content if b.type == "tool_use"]

            for block in content:
                if hasattr(block, "text") and block.text:
                    yield {"type": "text", "text": block.text}

            if not tool_uses:
                break

            tool_results = []
            for tu in tool_uses:
                yield {"type": "tool_start", "tool_name": tu.name, "tool_input": tu.input}
                result = run_tool(tu.name, tu.input)
                self.memory.log_action(session_id, tu.name, result)
                yield {"type": "tool_result", "tool_name": tu.name, "result": result}
                tool_calls_made.append({"tool": tu.name})
                tool_results.append({"type": "tool_result", "tool_use_id": tu.id, "content": result})

            history.append({"role": "user", "content": tool_results})

        self.memory.save(session_id, history)
        yield {"type": "done", "tool_calls": tool_calls_made}

    def get_session_summary(self, session_id: str) -> dict:
        return {
            "action_log": self.memory.get_action_summary(session_id),
            "message_count": len(self.memory.get(session_id)),
            "breaker_calls": self._breaker(session_id).calls,
            "breaker_cost_usd": round(self._breaker(session_id).cost, 4),
        }

    def clear_history(self, session_id: str):
        self.memory.clear(session_id)
        self.breakers.pop(session_id, None)

    # ── MOCK (no API key) ───────────────────────────────────
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
        # Yield thinking like Autonomous Optimization Architect pattern
        think = f"Query analyzed → Tool selected: {tool}\nChecking financial impact... running quality gate..."
        yield {"type": "thinking", "text": think}
        yield {"type": "tool_start", "tool_name": tool, "tool_input": {}}
        result = run_tool(tool, {})
        self.memory.log_action(session_id, tool, result)
        yield {"type": "tool_result", "tool_name": tool, "result": result}
        for word in result.split():
            yield {"type": "text", "text": word + " "}
        yield {"type": "done", "tool_calls": [{"tool": tool}]}


# Singleton
agent = SellerPilotAgent()
