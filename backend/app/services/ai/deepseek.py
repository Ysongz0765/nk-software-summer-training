from __future__ import annotations

import json
from typing import cast

import httpx
from pydantic import TypeAdapter, ValidationError

from app.core.exceptions import AIServiceUnavailableError
from app.schemas.report import (
    MissingInformationResult,
    ReportContent,
    ReportGenerationRequest,
    TaskExtractionInput,
    TaskItem,
)
from app.services.ai.base import AIReportService

DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash"
JSON_OBJECT_RESPONSE = {"type": "json_object"}
TASK_LIST_ADAPTER = TypeAdapter(list[TaskItem])

JsonObject = dict[str, object]


class DeepSeekAIReportService(AIReportService):
    def __init__(
        self,
        api_key: str,
        base_url: str = DEEPSEEK_DEFAULT_BASE_URL,
        model: str = DEEPSEEK_DEFAULT_MODEL,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key.strip():
            raise AIServiceUnavailableError("AI_API_KEY is required when AI_PROVIDER=deepseek")

        self._api_key = api_key.strip()
        self._base_url = base_url.rstrip("/") or DEEPSEEK_DEFAULT_BASE_URL
        self._model = model.strip() or DEEPSEEK_DEFAULT_MODEL
        self._timeout_seconds = timeout_seconds

    async def extract_tasks(self, input_data: TaskExtractionInput) -> list[TaskItem]:
        payload = await self._chat_json(
            system_prompt=_TASK_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=json.dumps(input_data.model_dump(mode="json"), ensure_ascii=False),
        )
        raw_tasks = payload.get("tasks")
        if raw_tasks is None:
            raw_tasks = payload

        try:
            tasks = TASK_LIST_ADAPTER.validate_python(raw_tasks)
        except ValidationError as exc:
            raise AIServiceUnavailableError(
                "DeepSeek task response failed schema validation"
            ) from exc

        return [task.model_copy(update={"source": "ai"}) for task in tasks]

    async def check_missing_information(self, tasks: list[TaskItem]) -> MissingInformationResult:
        payload = await self._chat_json(
            system_prompt=_MISSING_INFORMATION_SYSTEM_PROMPT,
            user_prompt=json.dumps(
                {"tasks": [task.model_dump(mode="json") for task in tasks]},
                ensure_ascii=False,
            ),
        )
        raw_result = payload.get("result")
        if raw_result is None:
            raw_result = payload

        try:
            return MissingInformationResult.model_validate(raw_result)
        except ValidationError as exc:
            raise AIServiceUnavailableError(
                "DeepSeek missing-information response failed schema validation"
            ) from exc

    async def generate_report(self, request: ReportGenerationRequest) -> ReportContent:
        payload = await self._chat_json(
            system_prompt=_REPORT_GENERATION_SYSTEM_PROMPT,
            user_prompt=json.dumps(request.model_dump(mode="json"), ensure_ascii=False),
        )
        raw_report = payload.get("report")
        if raw_report is None:
            raw_report = payload

        try:
            report = ReportContent.model_validate(raw_report)
        except ValidationError as exc:
            raise AIServiceUnavailableError(
                "DeepSeek report response failed schema validation"
            ) from exc

        return report.model_copy(
            update={
                "report_type": request.report_type,
                "date": request.report_date,
                "custom_fields": {
                    **report.custom_fields,
                    "generated_by": "DeepSeekAIReportService",
                    "model": self._model,
                },
            }
        )

    async def _chat_json(self, system_prompt: str, user_prompt: str) -> JsonObject:
        request_payload: JsonObject = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": JSON_OBJECT_RESPONSE,
            "stream": False,
            "temperature": 0.2,
            "max_tokens": 4096,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json=request_payload,
                )
                response.raise_for_status()
                response_payload = cast(JsonObject, response.json())
        except httpx.HTTPStatusError as exc:
            raise AIServiceUnavailableError(
                f"DeepSeek API returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise AIServiceUnavailableError("DeepSeek API request failed") from exc
        except ValueError as exc:
            raise AIServiceUnavailableError("DeepSeek API returned invalid JSON") from exc

        content = _extract_message_content(response_payload)
        return _loads_json_object(content)


def _extract_message_content(response_payload: JsonObject) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIServiceUnavailableError("DeepSeek API response missing choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise AIServiceUnavailableError("DeepSeek API response has invalid choice item")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise AIServiceUnavailableError("DeepSeek API response missing message")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise AIServiceUnavailableError("DeepSeek API response returned empty content")

    return content


def _loads_json_object(content: str) -> JsonObject:
    normalized = content.strip()
    if normalized.startswith("```"):
        normalized = (
            normalized.removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

    try:
        parsed = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise AIServiceUnavailableError("DeepSeek content is not valid JSON") from exc

    if not isinstance(parsed, dict):
        raise AIServiceUnavailableError("DeepSeek content must be a JSON object")

    return cast(JsonObject, parsed)


_TASK_EXTRACTION_SYSTEM_PROMPT = """
你是 ReportFlow AI 的任务提取模块。你必须只输出一个 json 对象，不要输出 Markdown。

目标：从用户输入、OCR 文本或上下文中识别日报/周报任务。

输出 JSON 示例：
{
  "tasks": [
    {
      "id": "ai-task-1",
      "title": "完成 OCR 接口联调",
      "description": "从输入内容识别出的任务说明",
      "status": "completed",
      "progress": 100,
      "evidence_file_ids": [],
      "confidence": 0.92,
      "source": "ai",
      "user_confirmed": false
    }
  ]
}

规则：
- status 只能是 pending、in_progress、completed。
- progress 必须是 0 到 100 的整数。
- confidence 必须是 0 到 1 的数字。
- 没有明确完成信号时，不要把任务标成 completed。
- 最多输出 10 项任务。
- 所有字段必须满足项目 Pydantic Schema。
""".strip()

_MISSING_INFORMATION_SYSTEM_PROMPT = """
你是 ReportFlow AI 的信息补全检查模块。你必须只输出一个 json 对象，不要输出 Markdown。

输入是任务列表。判断生成日报/周报还缺哪些信息，并给出面向用户的补充问题。

输出 JSON 示例：
{
  "missing_fields": ["task_confirmation", "next_plan"],
  "questions": ["请确认未确认任务的标题、状态和进度是否准确。"],
  "confidence": 0.86
}

规则：
- missing_fields 使用简短英文 snake_case。
- questions 使用中文。
- confidence 必须是 0 到 1 的数字。
""".strip()

_REPORT_GENERATION_SYSTEM_PROMPT = """
你是 ReportFlow AI 的日报/周报内容生成模块。你必须只输出一个 json 对象，不要输出 Markdown。

输入包含 report_type、title、report_date、tasks、style 和 source_data。
请生成满足 ReportContent Schema 的结构化报表。

输出 JSON 示例：
{
  "report": {
    "report_type": "daily",
    "title": "项目日报",
    "date": "2026-07-23",
    "summary": "本期完成 OCR 接口联调并推进 AI 接入。",
    "completed_tasks": [],
    "in_progress_tasks": [],
    "problems": ["暂无阻塞问题。"],
    "solutions": ["保持当前推进节奏。"],
    "next_plan": ["继续完善真实服务接入。"],
    "custom_fields": {},
    "missing_fields": [],
    "style": "concise"
  }
}

规则：
- date 必须等于输入 report_date。
- completed_tasks 放 completed 状态任务。
- in_progress_tasks 放非 completed 状态任务。
- 不要虚构未出现在输入中的关键事实。
- 如果信息不足，在 missing_fields 中明确标出。
- 所有字段必须满足项目 Pydantic Schema。
""".strip()
