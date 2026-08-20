import re
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import datetime


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
    thought: str = ""


@dataclass
class ThoughtStep:
    role: str
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_result: Optional[str] = None


class JarvisAgent:
    def __init__(self, assistant_ref):
        self.assistant = assistant_ref
        self.max_iterations = 6

    # ----- Intent -> tool selection heuristic (self-thinking) -----
    def reason(self, query: str) -> Dict[str, Any]:
        steps: List[ThoughtStep] = []
        q = query.strip()
        context = self.assistant.memory.get_recent_context(turns=4)

        steps.append(ThoughtStep(role="user", content=q))
        initial_thought = self._initial_analysis(q, context)
        steps.append(ThoughtStep(role="thought", content=initial_thought))

        iteration = 0
        final_answer: Optional[str] = None
        tool_outputs: List[Dict] = []

        while iteration < self.max_iterations:
            iteration += 1

            tools_to_call = self._select_tools(q, context, step=iteration, prior_outputs=tool_outputs)

            if not tools_to_call:
                break

            for call in tools_to_call:
                steps.append(ThoughtStep(
                    role="plan",
                    thought=call.thought,
                    tool_calls=[call]
                ))
                try:
                    result = self._execute_tool(call)
                    tool_outputs.append({"tool": call.name, "args": call.args, "result": result})
                    steps.append(ThoughtStep(
                        role="tool",
                        content=call.name,
                        tool_result=str(result)[:2000]
                    ))
                    if call.name == "final_answer":
                        final_answer = result
                        break
                    if self._result_answers_question(q, result):
                        final_answer = self._synthesize_answer(q, result, tool_outputs)
                        break
                except Exception as e:
                    steps.append(ThoughtStep(role="error", content=f"{call.name} failed: {e}"))
                    continue
            if final_answer:
                break

        if final_answer is None:
            final_answer = self._synthesize_answer(q, None, tool_outputs, fallback_to_llm=True)

        steps.append(ThoughtStep(role="assistant", content=final_answer))
        return {
            "answer": final_answer,
            "iterations": iteration,
            "tool_calls": tool_outputs,
            "reasoning_trace": [
                {"step": i, "role": s.role, "content": s.content[:1200]}
                for i, s in enumerate(steps)
            ],
        }

    # ----- Heuristic planning (self-thinking core) -----
    def _initial_analysis(self, query: str, context: str) -> str:
        q = query.lower()
        needs = []
        if re.search(r"\b(open|start|launch)\b", q) and re.search(
            r"\b(chrome|firefox|edge|notepad|calculator|word|excel|powerpoint|outlook|terminal|code|settings|spotify|discord|camera|store|paint)\b", q):
            needs.append("open_app")
        if re.search(r"\b(close|terminate|kill|end|stop)\b.*\b(app|program|process)\b|\b(close|terminate|kill)\b.*\b(chrome|firefox|edge|notepad|word|excel)\b", q):
            needs.append("close_app")
        if re.search(r"\b(weather|temperature|forecast|rain|sunny|humid)\b", q):
            needs.append("weather")
        if re.search(r"\b(file|folder|directory)\b|\b(list|ls|dir|show|files)\b.*\b(folder|in|at|on)\b", q):
            needs.append("list_folder")
        if re.search(r"\b(create|make|new)\b.*\b(folder|directory)\b", q):
            needs.append("create_folder")
        if re.search(r"\b(copy|cp)\b.*\b(to|into)\b", q):
            needs.append("copy")
        if re.search(r"\b(move|mv|cut and paste)\b.*\b(to|into)\b", q):
            needs.append("move")
        if re.search(r"\b(rename|ren)\b", q):
            needs.append("rename")
        if re.search(r"\b(delete|remove|rm|del)\b.*\b(file|folder|directory)\b", q):
            needs.append("delete")
        if re.search(r"\b(screenshot|snap|capture|screen shot|take a picture)\b", q):
            needs.append("screenshot")
        if re.search(r"\b(brightness|screen|dim|bright)\b", q):
            needs.append("set_brightness")
        if re.search(r"\b(volume|sound|mute|loud|quiet)\b", q):
            needs.append("set_volume")
        if re.search(r"\b(lock|logout)\b.*\b(pc|computer|screen|system)\b|\b(lock screen)\b", q):
            needs.append("lock_screen")
        if re.search(r"\b(shut down|shutdown|turn off|power off)\b", q):
            needs.append("shutdown")
        if re.search(r"\b(restart|reboot)\b", q):
            needs.append("restart")
        if re.search(r"\b(sleep|standby|suspend)\b", q):
            needs.append("sleep")
        if re.search(r"\b(search|find|look|google|web|internet)\b", q) and not re.search(
            r"\b(file|folder|in my|on this pc|on my computer)\b", q):
            needs.append("web_search")
        if re.search(r"\b(wikipedia|who is|explain|tell me about|what is|define)\b", q) or (len(query.split()) > 3 and not needs):
            needs.append("knowledge")
        if re.search(r"\b(map|maps|direction|route|distance|near me|nearby|location)\b", q):
            needs.append("maps")
        if re.search(r"\b(time|clock|hour|date|day)\b.*\b(in|at|for|zone)\b|\b(what time|current time|local time).*\b(in|at|in the|in)\b", q):
            needs.append("world_time")
        if re.search(r"\b(country|population|capital|currency|region)\b", q):
            needs.append("country")
        if re.search(r"\b(convert|conversion|rate|exchange|dollar|rupee|euro|pound|yen|usd|inr|eur|gbp|jpy|cad|aud)\b", q):
            needs.append("currency")
        if re.search(r"\b(calculate|math|maths|solve|compute|equation|plus|minus|times|divide|square root|factorial|derivative|integral)\b", q) or re.match(r"^[\d+\-*/().%\^ ]+$", q):
            needs.append("calculator")
        if not needs:
            needs.append("knowledge")

        return (
            f"Analyzing query: '{query}'. "
            f"Detected likely intents/tools: {', '.join(needs)}. "
            f"Will now call the relevant tools and synthesize an answer from their output."
        )

    def _select_tools(self, query: str, context: str, step: int, prior_outputs: List[Dict]) -> List[ToolCall]:
        q = query.lower()
        calls: List[ToolCall] = []
        already = {p["tool"] for p in prior_outputs}

        def add(name: str, args: Dict, thought: str):
            if name in already and name in ("final_answer",):
                return
            calls.append(ToolCall(name=name, args=args, thought=thought))

        # PC control
        if step == 1:
            app_m = re.search(r"\b(open|start|launch)\s+(?:the\s+|an?\s+)?(.+?)(?:\s+(?:app|application|program))?$", q)
            if app_m:
                add("open_app", {"name": app_m.group(2).strip()}, "User wants to open an app")
            else:
                for app in ["chrome", "firefox", "edge", "notepad", "calculator", "word", "excel", "powerpoint",
                            "outlook", "terminal", "code", "vs code", "settings", "spotify", "discord",
                            "camera", "store", "paint", "task manager", "control panel"]:
                    if re.search(rf"\b(open|start|launch)\s+(?:the\s+)?{re.escape(app)}\b", q):
                        add("open_app", {"name": app}, f"User wants to open {app}")
                        break

            close_m = re.search(r"\b(close|kill|terminate|end|stop)\s+(?:the\s+|an?\s+)?(.+?)(?:\s+(?:app|application|program|process))?$", q)
            if close_m:
                add("close_app", {"name": close_m.group(2).strip()}, "User wants to close an app/process")

            # Folders / files
            if re.search(r"\b(list|ls|dir|show|what.?s in|display)\b.*\b(folder|directory|files)\b|\b(list|ls|show)\b.*\bfiles\b", q):
                p = self._extract_path(q) or "."
                add("list_folder", {"path": p}, f"List files in {p}")

            if re.search(r"\b(create|make|new)\b.*\b(folder|directory)\b", q):
                p = self._extract_path(q) or "./New Folder"
                add("create_folder", {"path": p}, f"Create folder at {p}")

            if re.search(r"\b(delete|remove|del|rm)\b", q) and re.search(r"\b(file|folder|directory)\b", q):
                p = self._extract_path(q)
                if p:
                    add("delete", {"path": p, "skip_confirm": True}, f"Delete {p}")

            m = re.search(r"(?:copy|cp)\s+(?P<src>[\"']?[^\"']+[\"']?)\s+to\s+(?P<dst>[\"']?[^\"']+[\"']?)", q, re.IGNORECASE)
            if m:
                add("copy", {"src": m.group("src").strip().strip("\"'"), "dst": m.group("dst").strip().strip("\"'")},
                    f"Copy {m.group('src')} to {m.group('dst')}")
            m = re.search(r"(?:move|mv)\s+(?P<src>[\"']?[^\"']+[\"']?)\s+to\s+(?P<dst>[\"']?[^\"']+[\"']?)", q, re.IGNORECASE)
            if m:
                add("move", {"src": m.group("src").strip().strip("\"'"), "dst": m.group("dst").strip().strip("\"'")},
                    f"Move {m.group('src')} to {m.group('dst')}")
            m = re.search(r"(?:rename)\s+(?P<src>[\"']?[^\"']+[\"']?)\s+(?:to|as)\s+(?P<to>[\"']?[^\"']+[\"']?)", q, re.IGNORECASE)
            if m:
                add("rename", {"path": m.group("src").strip().strip("\"'"), "new_name": m.group("to").strip().strip("\"'")},
                    f"Rename file")

            # Screen / sound / power
            if re.search(r"\b(screenshot|snap|screen ?shot|capture)\b", q):
                add("screenshot", {}, "Take a screenshot")
            m = re.search(r"bright(?:ness)?\s+(?:to\s+)?(\d{1,3})\s*(?:percent|%|\b)", q)
            if m:
                add("set_brightness", {"level": int(m.group(1))}, f"Set brightness to {m.group(1)}%")
            elif re.search(r"\b(dim|lower brightness|decrease brightness)\b", q):
                add("set_brightness", {"level": 30}, "Dim the screen")
            elif re.search(r"\b(max brightness|full brightness|increase brightness)\b", q):
                add("set_brightness", {"level": 100}, "Full brightness")
            m = re.search(r"volume\s+(?:to\s+)?(\d{1,3})\s*(?:percent|%|\b)", q)
            if m:
                add("set_volume", {"level": int(m.group(1))}, f"Set volume to {m.group(1)}%")
            elif re.search(r"\b(mute|silent|no sound)\b", q):
                add("set_volume", {"level": 0}, "Mute volume")
            elif re.search(r"\b(full volume|max volume)\b", q):
                add("set_volume", {"level": 100}, "Full volume")
            if re.search(r"\b(lock|lock ?screen)\b", q):
                add("lock_screen", {}, "Lock the computer")
            if re.search(r"\b(shut down|shutdown|power off|turn off)\b", q):
                add("shutdown", {"seconds": 60}, "Schedule shutdown in 60s (user can cancel)")
            if re.search(r"\b(cancel.*shutdown|abort.*shutdown|stop.*shutdown)\b", q):
                add("cancel_shutdown", {}, "Cancel pending shutdown")
            if re.search(r"\b(restart|reboot)\b", q):
                add("restart", {"seconds": 15}, "Restart in 15s")
            if re.search(r"\b(sleep|standby|suspend|nap)\b", q):
                add("sleep", {}, "Put PC to sleep")

            # Data / knowledge
            if re.search(r"\b(weather|temperature|forecast|rain|humid|sunny|windy|snow)\b", q) or (
                re.search(r"\b(hot|cold|warm|cool)\b", q) and not re.search(r"\b(food|drink|coffee|tea|water)\b", q)):
                loc = self._extract_location(q) or ""
                add("weather", {"location": loc}, f"Fetch weather for {loc or 'default location'}")

            if re.search(r"\b(google|search|look up|find)\b", q) or (re.search(r"\b(news|latest|today|2024|2025|2026)\b", q) and "knowledge" not in already):
                sq = self._strip_commands(q)
                if sq:
                    add("web_search", {"query": sq, "max_results": 5}, f"Search web for '{sq}'")

            if re.search(r"\b(map|maps|location|direction|route|near me|nearby|distance)\b", q):
                mq = self._strip_commands(q)
                add("maps", {"query": mq or "my location"}, "Look up location/direction")

            if re.search(r"\b(time|date|day)\b.*\b(in|at|for|zone)\b", q):
                m = re.search(r"\bin\s+(.+?)(?:\s*now)?\s*[\.?]?$", q)
                tz = m.group(1).strip() if m else "UTC"
                add("world_time", {"timezone_or_city": tz}, f"Time in {tz}")

            if re.search(r"\b(country|capital|population|currency|region|language)\b", q):
                c = self._extract_country(q)
                if c:
                    add("country", {"name": c}, f"Country info for {c}")

            if re.search(r"\b(convert|conversion|exchange|rate)\b|\b(usd|inr|eur|gbp|jpy|cad|aud|aed|sgd|sar|pkr|bdt|ngn|try|mxn|brl|zar|cny|rub|krw)\b", q):
                info = self._extract_currency(q)
                if info:
                    add("currency_convert", info, f"Currency convert {info}")

            if re.search(r"\b(mathematics|math|maths|solve|calculate|compute|what is|evaluate|equation|integral|derivative|factor|simplify)\b", q) or re.match(r"^[\d+\-*/().%\^ ]+$", q):
                add("calculator", {"expression": self._extract_calc_expr(q)}, f"Solve math expression")

            if re.search(r"\b(process|running|task|apps|what is running|cpu|memory)\b", q):
                add("list_processes", {"limit": 10}, "List top processes")

            if re.search(r"\b(system info|computer spec|about this pc|my system|specs|storage)\b", q):
                add("system_info", {}, "Gather system information")

            # LLM knowledge: always offer as synthesis step if nothing concrete matched
            if not calls or (len(query.split()) > 3 and not any(t.name in ("knowledge", "web_search") for t in calls)):
                add("knowledge", {"query": query, "context": context}, "Consult LLM/Wikipedia for general knowledge")

        if calls and not any(t.name == "final_answer" for t in calls):
            pass  # synthesize once tools run

        return calls[:4]

    def _execute_tool(self, call: ToolCall) -> Any:
        name = call.name
        args = call.args
        S = self.assistant
        P = S.pc
        D = S.data

        # PC
        if name == "open_app": return P.open_app(args["name"])
        if name == "close_app": return P.close_app(args["name"])
        if name == "list_folder": return P.list_folder(args.get("path", "."))
        if name == "create_folder": return P.create_folder(args["path"])
        if name == "delete": return P.delete(args["path"], skip_confirm=args.get("skip_confirm", True))
        if name == "copy": return P.copy(args["src"], args["dst"])
        if name == "move": return P.move(args["src"], args["dst"])
        if name == "rename": return P.rename(args["path"], args["new_name"])
        if name == "screenshot": return P.take_screenshot()
        if name == "set_brightness": return P.set_brightness(args["level"])
        if name == "get_brightness": return P.get_brightness()
        if name == "set_volume": return P.set_volume(args["level"])
        if name == "get_volume": return P.get_volume()
        if name == "lock_screen": return P.lock_screen()
        if name == "shutdown": return P.shutdown(args.get("seconds", 60))
        if name == "cancel_shutdown": return P.cancel_shutdown()
        if name == "restart": return P.restart(args.get("seconds", 15))
        if name == "sleep": return P.sleep()
        if name == "hibernate": return P.hibernate()
        if name == "list_processes": return P.list_running_processes(args.get("limit", 20))
        if name == "system_info": return P.system_info()
        if name == "open_url": return P.open_url(args["url"])
        if name == "google_search": return P.google_search(args["query"])
        if name == "youtube_search": return P.youtube_search(args["query"])
        if name == "maps_search": return P.maps_search(args["query"])
        if name == "directions": return P.directions(args["origin"], args["destination"])
        if name == "open_folder": return P.open_folder(args.get("path", "."))
        if name == "open_file": return P.open_file(args["path"])
        if name == "search_files": return P.search_files(args["pattern"], args.get("root", "."))

        # Data
        if name == "weather": return D.weather(args.get("location", ""))
        if name == "web_search": return [r.__dict__ for r in D.web_search(args["query"], args.get("max_results", 5))]
        if name == "maps": return [r.__dict__ for r in D.maps_search(args["query"])]
        if name == "world_time": return D.get_time_in(args["timezone_or_city"])
        if name == "country": return D.get_country(args["name"]) or f"No country data for: {args['name']}"
        if name == "currency_convert": return D.currency_convert(args["amount"], args["from_code"], args["to_code"])
        if name == "calculator":
            expr = args.get("expression")
            return S.skill_handler.handle("calculator", f"calculate {expr}")

        # Knowledge / LLM
        if name == "knowledge":
            resp = S.llm.answer(args["query"], context=args.get("context"))
            return {"provider": resp.provider, "text": resp.text, "sources": resp.sources, "error": resp.error}

        return {"error": f"Unknown tool: {name}"}

    # ----- NLP helpers to extract args from natural language -----
    @staticmethod
    def _extract_path(q: str) -> Optional[str]:
        patterns = [
            r"[\"']([^\"']+)[\"']",
            r"(?:folder|directory|in|at|on|path)\s+[:]?\s*([A-Za-z]:\\[^\s,;]+|(?:~|\.|\.\.|/)[^\s,;]+)",
            r"([A-Za-z]:\\[^\s,;]+|(?:~|\.|\.\.)/[^\s,;]*)",
        ]
        for p in patterns:
            m = re.search(p, q, re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip(".,!?;:")
        return None

    @staticmethod
    def _extract_location(q: str) -> Optional[str]:
        m = re.search(r"\b(?:weather|forecast|temperature|in|at|for)\s+(?:in|at|for)?\s*([A-Za-z][A-Za-z\s]+?)(?:\s+(?:today|tomorrow|now|this week|please|\.|$))", q, re.IGNORECASE)
        if m:
            loc = m.group(1).strip()
            if loc.lower() not in ("weather", "forecast", "temperature", "the", "is"):
                return loc.title()
        return None

    @staticmethod
    def _extract_country(q: str) -> Optional[str]:
        m = re.search(r"\b(?:country|info about|details on|capital of|population of|currency of|region of)\s+([A-Za-z][A-Za-z\s&.]+)", q, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
        m = re.search(r"\b(?:in|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", q)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _extract_currency(q: str) -> Optional[Dict]:
        codes = ["USD","INR","EUR","GBP","JPY","CAD","AUD","AED","SGD","SAR","PKR","BDT","NGN","TRY","MXN","BRL","ZAR","CNY","RUB","KRW","NZD"]
        q_up = q.upper()
        found = [c for c in codes if c in q_up]
        m_amt = re.search(r"(?:\$|£|€|₹|¥|₩|₽|₺|₦|R\$|₵|RM)\s*([0-9]+(?:[.,][0-9]+)?)|([0-9]+(?:[.,][0-9]+)?)\s*(?:dollars?|rupees?|euros?|pounds?|yen|won|rubles?|liras?|reais?|rands?|yuans?|pesos?|nairas?)", q, re.IGNORECASE)
        amount = 1.0
        if m_amt:
            g = m_amt.group(1) or m_amt.group(2)
            try:
                amount = float(g.replace(",", "."))
            except Exception:
                pass
        if len(found) >= 2:
            m_to = re.search(r"(?:to|into|->|=>)\s*([A-Z]{3})", q_up)
            if m_to:
                to_code = m_to.group(1)
                from_code = next((c for c in found if c != to_code), found[0])
            else:
                from_code, to_code = found[0], found[1]
            return {"amount": amount, "from_code": from_code, "to_code": to_code}
        if len(found) == 1 and (" to " in q.lower() or " in " in q.lower()):
            from_code = found[0]
            to_match = re.search(r"(?:to|in)\s+([A-Za-z ]+)", q, re.IGNORECASE)
            if to_match:
                to_text = to_match.group(1).strip().lower()
                map_ = {"dollar":"USD","rupee":"INR","euro":"EUR","pound":"GBP","yen":"JPY","yuan":"CNY","peso":"MXN","rand":"ZAR","ruble":"RUB","won":"KRW","lira":"TRY","dinar":"BHD","real":"BRL","naira":"NGN"}
                for k, v in map_.items():
                    if k in to_text:
                        return {"amount": amount, "from_code": from_code, "to_code": v}
        return None

    @staticmethod
    def _extract_calc_expr(q: str) -> str:
        expr = q
        word_map = {
            r"\bplus\b": "+", r"\bminus\b": "-", r"\btimes\b": "*",
            r"\bdivided by\b": "/", r"\bof\b": "*", r"\bpercent\b": "/100",
            r"\bpercentage\b": "/100", r"\bsquared\b": "**2", r"\bcubed\b": "**3",
            r"\bwhat is\b": "", r"\bcalculate\b": "", r"\bsolve\b": "",
            r"\bevaluate\b": "", r"\bcompute\b": "", r"\bfind\b": "",
            r"\bequals?\b": "=", r"\bthe value of\b": "", r"\bmath (?:problem|question)\b": "",
        }
        for pat, repl in word_map.items():
            expr = re.sub(pat, repl, expr, flags=re.IGNORECASE)
        expr = re.sub(r"[^0-9+\-*/().%^ a-zA-Z]", "", expr)
        expr = expr.replace("^", "**").strip()
        return expr

    @staticmethod
    def _strip_commands(q: str) -> str:
        s = q.lower()
        s = re.sub(r"^(jarvis[,:\s]*)", "", s)
        s = re.sub(r"\b(hey|okay|ok|hi|yo)\s+jarvis\b[.,!?]*\s*", "", s)
        s = re.sub(r"^\s*(please|can you|could you|will you|i want you to|i need you to|would you|do me a favor and)\s+", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+(please|thanks|thank you|ok|okay)\s*[\.!?]*$", "", s, flags=re.IGNORECASE)
        s = re.sub(r"^(search|google|look up|find|tell me about|explain|what is|who is|define|search for|give me|i need)\s+", "", s, flags=re.IGNORECASE)
        return s.strip(" .!?;:")

    @staticmethod
    def _result_answers_question(q: str, result) -> bool:
        if result is None:
            return False
        if isinstance(result, dict) and result.get("success") is False:
            return False
        if isinstance(result, dict) and "error" in result:
            return False
        if isinstance(result, str) and len(result) > 80:
            return True
        if isinstance(result, list) and len(result) >= 2:
            return True
        return False

    def _synthesize_answer(self, q: str, direct: Any, tools: List[Dict], fallback_to_llm: bool = True) -> str:
        texts: List[str] = []
        for t in tools:
            texts.append(self._stringify_tool(t))
        tool_text = "\n\n".join(texts) if texts else ""

        if direct and isinstance(direct, str) and len(direct) > 20:
            return direct

        if fallback_to_llm and len(tool_text) > 0:
            prompt = (
                f"User query: {q}\n\n"
                f"Here is the raw output from tool executions JARVIS performed:\n{tool_text}\n\n"
                f"Now produce a clear, final, concise answer to the user's query in natural English."
                f" Summarize key numbers and mention success/failure of actions. "
                f"If the tool says success is False, clearly state the error and what to try instead."
            )
            r = self.assistant.llm.answer(prompt)
            if r.text and not r.error:
                return r.text

        if tool_text:
            return f"Here are the results:\n{tool_text}"
        # Fallback via general LLM knowledge
        r = self.assistant.llm.answer(q)
        return r.text or "I'm sorry, I couldn't resolve that query right now."

    @staticmethod
    def _stringify_tool(t: Dict) -> str:
        tool, args, result = t.get("tool", ""), t.get("args", {}), t.get("result", "")
        head = f"[Tool: {tool}] args={json.dumps(args)[:300]}"
        body = ""
        if isinstance(result, str):
            body = result[:1500]
        elif isinstance(result, dict):
            if "text" in result and isinstance(result["text"], str):
                body = result["text"][:1500]
            elif "success" in result:
                lines = []
                for k, v in result.items():
                    if isinstance(v, list) and len(v) > 6:
                        lines.append(f"{k}: (list with {len(v)} items)")
                    else:
                        sv = str(v)
                        if len(sv) > 400:
                            sv = sv[:400] + "..."
                        lines.append(f"{k}: {sv}")
                body = "\n".join(lines)
            else:
                body = json.dumps(result, indent=2, default=str)[:1500]
        elif isinstance(result, list):
            lines = []
            for i, r in enumerate(result[:10]):
                lines.append(f"{i+1}. {json.dumps(r, default=str)[:300]}")
            body = "\n".join(lines)
        else:
            body = str(result)[:1500]
        return f"{head}\n{body}"
