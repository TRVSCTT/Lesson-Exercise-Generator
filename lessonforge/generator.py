from dataclasses import dataclass, field
from pydantic import ValidationError
from .checks import check_lesson
from .llm import LLM
from .prompts import SYSTEM, user_prompt, retry_prompt
from .schema import Lesson, Request

SCHEMA = Lesson.model_json_schema()


@dataclass
class Result:
    lesson: Lesson | None
    issues: list[str] = field(default_factory=list)   # vide = valide
    attempts: int = 0

    @property
    def ok(self) -> bool:
        return self.lesson is not None and not self.issues


def generate(req: Request, llm: LLM, max_attempts: int = 3) -> Result:
    """Génère, valide, et redemande avec la liste précise des erreurs. Ne livre jamais une leçon invalide
    sans le signaler : si les tentatives échouent, `issues` reste rempli."""
    prompt = user_prompt(req)
    lesson, issues = None, ["aucune tentative"]
    for attempt in range(1, max_attempts + 1):
        raw = llm.tool_call(SYSTEM, prompt, "emettre_cours", SCHEMA)
        try:
            lesson = Lesson.model_validate(raw)
        except ValidationError as e:
            lesson = None
            issues = [f"schéma invalide : {err['loc']} {err['msg']}" for err in e.errors()[:10]]
        else:
            issues = check_lesson(lesson, req)
        if not issues:
            return Result(lesson, [], attempt)
        prompt = retry_prompt(req, issues)
    return Result(lesson, issues, max_attempts)
