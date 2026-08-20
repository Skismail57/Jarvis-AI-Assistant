import os
import re
import sys
import json
import time
import textwrap
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class LLMResponse:
    provider: str
    text: str
    raw: Any = None
    error: bool = False
    sources: Optional[List[str]] = None


class LLMCore:
    SYSTEM_PROMPT = textwrap.dedent("""\
    You are JARVIS, a highly intelligent, professional, and friendly personal AI assistant.
    Your style is concise, accurate, and helpful with a touch of wit (like Tony Stark's JARVIS).

    Capabilities:
    - Expert in Mathematics, Physics, Chemistry, Biology, Medicine, Engineering, CS, AI/ML/Data Science, Software Engineering, Humanities, Law, Finance, History, Geography.
    - Explain complex topics simply but accurately. When asked for derivations/proofs, show step-by-step reasoning.
    - For medicine: be clear that advice is informational and recommend consulting a doctor.
    - For code: prefer Python when possible; include well-structured snippets and short explanations.
    - For math: solve step-by-step; verify result; state assumptions.
    - For current/recent events: explicitly indicate when data might be date-limited and encourage the search tool.
    - Keep responses under ~150 words unless detailed analysis is explicitly requested.
    - Cite sources if you have them.
    """)

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        model: str = "auto",
        max_tokens: int = 2048,
        temperature: float = 0.6,
    ):
        self.openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.env_path = os.path.join(self.base_dir, ".env")
        self._load_env()

    def _load_env(self):
        if os.path.exists(self.env_path):
            try:
                with open(self.env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
                self.openai_key = os.getenv("OPENAI_API_KEY", self.openai_key)
                self.gemini_key = os.getenv("GEMINI_API_KEY", self.gemini_key)
                self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_key)
            except Exception:
                pass

    def has_any_key(self) -> bool:
        return bool(self.openai_key or self.gemini_key or self.anthropic_key)

    def answer(self, query: str, context: Optional[str] = None, system_override: Optional[str] = None) -> LLMResponse:
        providers = self._select_providers()
        last_err = None
        for provider in providers:
            try:
                if provider == "openai":
                    return self._openai_answer(query, context, system_override)
                if provider == "gemini":
                    return self._gemini_answer(query, context, system_override)
                if provider == "anthropic":
                    return self._anthropic_answer(query, context, system_override)
                if provider == "wikipedia":
                    return self._wikipedia_answer(query)
                if provider == "ddg":
                    return self._ddg_answer(query)
            except Exception as e:
                last_err = e
                continue
        msg = f"Unable to contact any knowledge provider right now. Last error: {last_err}. I'll try to reason through it myself."
        return LLMResponse(provider="offline", text=self._offline_reason(query), error=bool(last_err))

    def _select_providers(self) -> List[str]:
        chain = []
        if self.model == "auto":
            if self.openai_key:
                chain.append("openai")
            elif self.gemini_key:
                chain.append("gemini")
            elif self.anthropic_key:
                chain.append("anthropic")
            chain += ["wikipedia", "ddg"]
        else:
            if self.model.startswith("gpt") and self.openai_key:
                chain.append("openai")
            elif "gemini" in self.model and self.gemini_key:
                chain.append("gemini")
            elif ("claude" in self.model) and self.anthropic_key:
                chain.append("anthropic")
            chain += ["wikipedia", "ddg"]
        return chain

    def _build_user_prompt(self, query: str, context: Optional[str]) -> str:
        prompt = ""
        if context:
            prompt += f"Conversation context:\n{context}\n\n"
        prompt += f"User question:\n{query}\n\nAnswer clearly and concisely."
        return prompt

    def _openai_answer(self, query: str, context: Optional[str], system_override: Optional[str]) -> LLMResponse:
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_key)
        model = self.model if self.model.startswith("gpt") else "gpt-4o-mini"
        messages = [
            {"role": "system", "content": system_override or self.SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_prompt(query, context)},
        ]
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        text = resp.choices[0].message.content.strip()
        return LLMResponse(provider=f"openai:{model}", text=text, raw=resp)

    def _gemini_answer(self, query: str, context: Optional[str], system_override: Optional[str]) -> LLMResponse:
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        model_name = self.model if "gemini" in self.model else "gemini-1.5-flash"
        model = genai.GenerativeModel(model_name)
        full_prompt = (system_override or self.SYSTEM_PROMPT) + "\n\n" + self._build_user_prompt(query, context)
        resp = model.generate_content(full_prompt, generation_config=genai.types.GenerationConfig(
            max_output_tokens=self.max_tokens, temperature=self.temperature
        ))
        text = resp.text.strip() if getattr(resp, "text", None) else str(resp)
        return LLMResponse(provider=f"gemini:{model_name}", text=text, raw=resp)

    def _anthropic_answer(self, query: str, context: Optional[str], system_override: Optional[str]) -> LLMResponse:
        import anthropic
        client = anthropic.Anthropic(api_key=self.anthropic_key)
        model = self.model if "claude" in self.model else "claude-3-haiku-20240307"
        msg = client.messages.create(
            model=model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_override or self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": self._build_user_prompt(query, context)}],
        )
        text = msg.content[0].text if msg.content else str(msg)
        return LLMResponse(provider=f"anthropic:{model}", text=text.strip(), raw=msg)

    def _wikipedia_answer(self, query: str) -> LLMResponse:
        try:
            import wikipedia
            wikipedia.set_lang("en")
            candidates = wikipedia.search(query, results=3)
            if not candidates:
                raise RuntimeError("No Wikipedia results")
            pages = []
            extracts = []
            for cand in candidates[:2]:
                try:
                    page = wikipedia.page(cand, auto_suggest=False)
                    pages.append((cand, page.url))
                    extracts.append(f"[{cand}] {page.summary[:1200]}")
                except Exception:
                    try:
                        summary = wikipedia.summary(cand, sentences=8)
                        pages.append((cand, f"https://en.wikipedia.org/wiki/{cand.replace(' ', '_')}"))
                        extracts.append(f"[{cand}] {summary[:1200]}")
                    except Exception:
                        continue
            if not extracts:
                raise RuntimeError("No Wikipedia extracts")
            combined = "\n\n".join(extracts)
            sources = [url for _, url in pages]
            return LLMResponse(provider="wikipedia", text=combined, sources=sources)
        except Exception as e:
            raise RuntimeError(f"wikipedia failed: {e}")

    def _ddg_answer(self, query: str) -> LLMResponse:
        try:
            from ddgs import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5, timelimit="y"):
                    results.append(r)
            if not results:
                raise RuntimeError("No DDG results")
            lines = []
            sources = []
            for r in results:
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")
                if body:
                    lines.append(f"• {title}: {body}")
                if href:
                    sources.append(href)
            text = "\n\n".join(lines) if lines else str(results)
            return LLMResponse(provider="duckduckgo", text=text, sources=sources[:5])
        except Exception as e:
            raise RuntimeError(f"DDG failed: {e}")

    def _offline_reason(self, query: str) -> str:
        q = query.lower()
        math_expr = self._extract_math(q)
        if math_expr:
            try:
                import math as m
                safe = {k: getattr(m, k) for k in dir(m) if not k.startswith("_")}
                safe.update({"abs": abs, "round": round, "min": min, "max": max})
                result = eval(math_expr, {"__builtins__": {}}, safe)
                return f"(Offline calculation) {math_expr} = {result}"
            except Exception:
                pass
        if re.search(r"(hi|hello|hey|greetings)\b", q):
            return "Hello! I'm JARVIS. Ask me anything about math, science, engineering, medicine, AI, or the world around you."
        if re.search(r"(your name|who are you)\b", q):
            return "I'm JARVIS, your professional AI assistant. Think of me as your personal knowledge oracle with computer control superpowers."
        if len(query) < 40:
            return f"I didn't find an immediate answer for: '{query}'. Set an API key (OPENAI_API_KEY or GEMINI_API_KEY) in .env for ChatGPT/Gemini-level answers, or ask me to search the web."
        return (
            f"(Offline mode) About your query: '{query[:120]}...' — "
            "I can reason about math expressions, basic facts, and I can try to search Wikipedia/DuckDuckGo if you have internet. "
            "To unlock GPT-4o / Gemini 1.5 / Claude-level answers, set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY in the .env file."
        )

    @staticmethod
    def _extract_math(q: str) -> Optional[str]:
        expr = q
        word_map = {
            r"\bplus\b": "+", r"\bminus\b": "-", r"\btimes\b": "*",
            r"\bdivided by\b": "/", r"\bof\b": "*", r"\bpercent\b": "/100",
            r"\bsquared\b": "**2", r"\bcubed\b": "**3", r"\bwhat is\b": "",
            r"\bcalculate\b": "", r"\bsolve\b": "", r"\bevaluate\b": "",
            r"\bcompute\b": "",
        }
        for pat, repl in word_map.items():
            expr = re.sub(pat, repl, expr, flags=re.IGNORECASE)
        expr = re.sub(r"[^0-9+\-*/().%^ a-zA-Z]", "", expr).strip()
        expr = expr.replace("^", "**")
        if re.search(r"[+\-*/()**%]", expr) and len(expr) > 2:
            return expr
        return None
