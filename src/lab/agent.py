"""GUIDE Phần 1 - Dựng tác tử (agent) bằng Deep Agents.   >>> SINH VIÊN CÀI ĐẶT make_backend VÀ build_agent <<<

Pseudo-code: guides/pseudocode/01_agent.md
Kiểm tra:    pytest tests/test_02_agent.py
"""
import sys
from pathlib import Path
from typing import Any, Optional

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict, Field

from .model import make_model
from .subagents import get_subagents

# ---- CÓ SẴN, KHÔNG SỬA: system prompt dùng chung cho mọi sinh viên (để đường cơ sở so sánh được) ----
PATHS_NOTE = (
    "PATHS: every path is relative to the sandbox root and never starts with '/'. "
    "The task files are in the folder workspace/ (for example workspace/app.log). "
    "Use exactly this relative form both in the file tools and in the shell (execute); "
    "the shell starts in the sandbox root. "
)
BASE_PROMPT = (
    "You are an engineering assistant working in a sandbox. "
    + PATHS_NOTE
    + "Use the shell to run Python and tests. "
    "When you are done, reply with a short summary that mentions only files you really created or changed."
)
SKILLS_NOTE = (
    " Skills are in the folder skills/ (one sub-folder per skill with a SKILL.md). "
    "As your FIRST action, read the SKILL.md of every skill whose description could apply to the task, "
    "then follow them. Never modify skills/."
)
SUBAGENTS_NOTE = (
    " You have specialised subagents (see the description of the task tool). "
    "For anything beyond a trivial step, delegate to a suitable subagent and put ALL the task rules and file paths "
    "in the delegation message, because a subagent sees only what you send. "
    "Check what a subagent returns before you rely on it."
)
# --------------------------------------------------------------------------------------------------

# Well-known tool names exposed by Deep Agents. Any other name from the model is treated as a typo
# and replaced with a recovery text message.
_KNOWN_TOOL_NAMES = {
    "ls", "read_file", "write_file", "edit_file", "delete", "glob", "grep",
    "execute", "task",
}

# Recovery note shown to the model when the previous output had a malformed tool call.
# This is a defensive guard only; it does NOT change the system prompt for well-formed outputs.
_RECOVERY_NOTE = (
    "The previous response was rejected by the tool layer because the tool name was not in the "
    "available tool list, or its arguments were not a valid JSON object. "
    "REMINDER: only use the tools listed in the tool definitions above. "
    "Use the EXACT tool names shown there (for example 'execute' not 'exec'). "
    "For multi-line Python code, prefer writing the script to a file with write_file and "
    "running it with execute (e.g. command='python workspace/script.py'); avoid heredocs in "
    "execute because they often break the JSON. Always output a single, valid tool call with "
    "valid JSON arguments."
)


def _is_bad_tool_call(msg: AIMessage) -> bool:
    """Return True if the AIMessage has a tool call that the harness would refuse to dispatch."""
    for tc in (msg.tool_calls or []):
        if not isinstance(tc, dict):
            return True
        name = tc.get("name")
        if not name or name not in _KNOWN_TOOL_NAMES:
            return True
        if not isinstance(tc.get("args"), dict):
            return True
    return False


class _SafeChatModel(BaseChatModel):
    """Chat model that delegates to a wrapped model and replaces malformed tool calls
    with a recovery text message.

    Some hosted chat models occasionally emit a tool call with a wrong tool name
    (e.g. ``exec`` instead of ``execute``) or with arguments that are not a JSON
    object. Those tool calls are rejected by the underlying API with HTTP 400.
    This wrapper inspects every response and, when it detects a malformed tool
    call, swaps the response for a short text message asking the model to retry.
    For well-formed responses it is a transparent pass-through, so the baseline
    condition behaves identically to the underlying model.
    """

    inner: Any = Field(exclude=True, description="The actual chat model to delegate to.")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def _llm_type(self) -> str:
        return "safe-wrapper"

    def bind_tools(self, tools, **kwargs):
        # Delegate binding to the inner model so the tool schemas are still the real ones.
        # Force tool_choice="auto" so hosted models (e.g. Groq `gpt-oss-120b`) cannot
        # infer "none" by default and reject valid outputs. Also disable parallel tool
        # calls because gpt-oss-120b on Groq does not support them and may hallucinate
        # the wrong tool name when multiple calls are emitted.
        # These kwargs are OpenAI-compatible-endpoint specific; other providers (e.g. Gemini) reject them.
        if type(self.inner).__name__ == "ChatOpenAI":
            kwargs.setdefault("tool_choice", "auto")
            kwargs.setdefault("parallel_tool_calls", False)
        new_inner = self.inner.bind_tools(tools, **kwargs)
        return _SafeChatModel(inner=new_inner)

    def _merge_bound_kwargs(self, kwargs: dict) -> dict:
        """Pull the bound `tools` / `tool_choice` from a `_ChatModelBinding` inner model
        so they are not silently dropped when `_generate` is called directly.
        Without this, `self.inner._generate(messages, **kwargs)` resolves the method via
        `RunnableBinding.__getattr__` which calls the bound chat model with only the
        caller's kwargs and never merges the binding's stored kwargs.
        """
        inner = self.inner
        for _ in range(5):
            inner = getattr(inner, "bound", inner)
        # The chain is _ChatModelBinding -> ChatOpenAI (or another _ChatModelBinding).
        # Walk binding wrappers and collect their bound kwargs.
        merged = dict(kwargs)
        cur = self.inner
        for _ in range(5):
            bound_kwargs = getattr(cur, "kwargs", None)
            if isinstance(bound_kwargs, dict):
                for k, v in bound_kwargs.items():
                    merged.setdefault(k, v)
            cur = getattr(cur, "bound", None)
            if cur is None:
                break
        return merged

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        call_kwargs = self._merge_bound_kwargs(kwargs)
        result: ChatResult = self.inner._generate(messages, stop=stop, run_manager=run_manager, **call_kwargs)
        for gen in result.generations:
            msg = gen.message
            if isinstance(msg, AIMessage) and _is_bad_tool_call(msg):
                gen.message = AIMessage(content=_RECOVERY_NOTE, tool_calls=[], invalid_tool_calls=[])
        return result

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        call_kwargs = self._merge_bound_kwargs(kwargs)
        result: ChatResult = await self.inner._agenerate(messages, stop=stop, run_manager=run_manager, **call_kwargs)
        for gen in result.generations:
            msg = gen.message
            if isinstance(msg, AIMessage) and _is_bad_tool_call(msg):
                gen.message = AIMessage(content=_RECOVERY_NOTE, tool_calls=[], invalid_tool_calls=[])
        return result


def _make_safe_model(model):
    """Return `model` unchanged if it is already a BaseChatModel; otherwise wrap it."""
    if isinstance(model, BaseChatModel):
        return _SafeChatModel(inner=model)
    return model


def make_backend(sandbox: Path):
    """Tạo backend (môi trường thực thi) cho tác tử.

    Yêu cầu:
      - Thư mục gốc (root_dir) là `sandbox`; đường dẫn tương đối `workspace/...` và `skills/...`
        phải dùng được ở CẢ công cụ tệp lẫn shell (shell chạy với thư mục làm việc = `sandbox`).
      - Tác tử chạy được lệnh shell và gọi được `python` (cần đặt PATH).
      - KHÔNG chuyển biến môi trường của bạn vào shell của tác tử (khóa API không được lộ).
    """
    python_dir = str(Path(sys.executable).parent)
    env = {
        "PATH": f"{python_dir}:/usr/local/bin:/usr/bin:/bin",
        "HOME": str(sandbox),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return LocalShellBackend(
        root_dir=sandbox,
        virtual_mode=True,
        inherit_env=False,
        env=env,
        timeout=120,
    )


def build_agent(sandbox: Path, mode: str = "single", use_skills: bool = False, model=None):
    """Tạo tác tử Deep Agents.

    Tham số:
      sandbox:    thư mục chứa `workspace/` (và `skills/` nếu có).
      mode:       "single"    -> tác tử mặc định (có subagent `general-purpose` sẵn của Deep Agents)
                  "subagents" -> thêm các subagent từ `get_subagents()` (nối PATHS_NOTE vào `system_prompt` của MỖI subagent,
                                 vì subagent không nhận BASE_PROMPT) và thêm SUBAGENTS_NOTE vào prompt chính
      use_skills: True -> nạp thư mục "/skills/" qua tham số `skills=` của create_deep_agent
                  và thêm SKILLS_NOTE vào prompt.
      model:      mô hình ngôn ngữ; None -> dùng `make_model()`.
    mode không hợp lệ -> ném ValueError.
    Trả về: đồ thị (graph) đã biên dịch, gọi bằng `.invoke({"messages": [...]})`.
    """
    if mode not in {"single", "subagents"}:
        raise ValueError(f"unknown mode: {mode!r} (expected 'single' or 'subagents')")

    kwargs: dict = {}
    prompt = BASE_PROMPT

    if mode == "subagents":
        # subagent KHÔNG nhận BASE_PROMPT, nên nối PATHS_NOTE vào system_prompt của từng subagent;
        # nếu không, subagent trộn lẫn "/workspace/x" và "workspace/x" và báo "không tìm thấy tệp"
        kwargs["subagents"] = [
            {**sub, "system_prompt": sub["system_prompt"] + " " + PATHS_NOTE}
            for sub in get_subagents()
        ]
        prompt = prompt + SUBAGENTS_NOTE

    if use_skills:
        kwargs["skills"] = ["/skills/"]
        prompt = prompt + SKILLS_NOTE

    raw_model = model if model is not None else make_model()
    safe_model = _make_safe_model(raw_model)

    return create_deep_agent(
        model=safe_model,
        system_prompt=prompt,
        backend=make_backend(sandbox),
        **kwargs,
    )
