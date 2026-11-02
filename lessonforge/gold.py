"""Validation GOLD : un jeu fixe de cas (gold/cases.jsonl) rejoué à chaque version de l'outil.
Un cas réussit seulement si TOUTES ses vérifications passent. Le taux publié compte les échecs."""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from .checks import norm, lesson_text
from .generator import generate
from .judge import judge_lesson
from .llm import LLM
from .schema import Request


@dataclass
class CaseResult:
    id: str
    topic: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    attempts: int = 0


def load_cases(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]


def run_case(case: dict, llm: LLM, judge: bool, judge_llm: LLM | None = None) -> CaseResult:
    req = Request(topic=case["topic"], level=case.get("level", "3e"), audience=case.get("audience", "ecole"),
                  duration_minutes=case.get("duration", 55), n_exercises=case.get("exercises", 6))
    res = CaseResult(case["id"], case["topic"], False)
    try:
        r = generate(req, llm)
    except Exception as e:  # une panne API est un échec, pas un cas ignoré
        res.failures.append(f"erreur de génération : {e}")
        return res
    res.attempts = r.attempts
    expect = case.get("expect", "ok")
    if r.lesson is None:
        res.failures += r.issues
        return res

    if expect == "declined":
        if r.lesson.status != "declined":
            res.failures.append("le sujet devait être refusé/précisé mais un cours a été produit")
        elif not r.lesson.decline_reason.strip():
            res.failures.append("refus sans motif")
        res.passed = not res.failures
        return res

    if r.lesson.status == "declined":
        res.failures.append(f"refus à tort : {r.lesson.decline_reason}")
        return res
    res.failures += [f"contrat : {i}" for i in r.issues]
    text = norm(lesson_text(r.lesson))
    for group in case.get("must_include", []):
        if not any(norm(t) in text for t in group):
            res.failures.append(f"notion absente : aucun de {group}")
    for t in case.get("must_not_include", []):
        if norm(t) in text:
            res.failures.append(f"contenu hors niveau/interdit : « {t} »")
    if judge and not r.issues:
        for v in judge_lesson(r.lesson, judge_llm or llm):
            if not v["agrees"]:
                res.failures.append(f"corrigé contesté, exercice {v['index']} : {v.get('note', '')}")
    res.passed = not res.failures
    return res


def run_gold(cases: list[dict], llm: LLM, judge: bool = True, judge_llm: LLM | None = None) -> dict:
    results = [run_case(c, llm, judge, judge_llm) for c in cases]
    n_pass = sum(r.passed for r in results)
    return {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "judge": judge,
        "total": len(results),
        "passed": n_pass,
        "pass_rate": round(n_pass / len(results), 3) if results else 0.0,
        "results": [asdict(r) for r in results],
    }


def report_markdown(rep: dict) -> str:
    o = [f"# Rapport gold — Lesson & Exercise Generator", "",
         f"- Date : {rep['date']}", f"- Juge indépendant des corrigés : {'oui' if rep['judge'] else 'non'}",
         f"- **Réussite : {rep['passed']}/{rep['total']} ({rep['pass_rate']:.0%})**", "",
         "| Cas | Sujet | Résultat | Tentatives |", "|---|---|---|---|"]
    for r in rep["results"]:
        o.append(f"| {r['id']} | {r['topic']} | {'✅' if r['passed'] else '❌'} | {r['attempts']} |")
    fails = [r for r in rep["results"] if not r["passed"]]
    if fails:
        o += ["", "## Échecs (non masqués)"]
        for r in fails:
            o += [f"### {r['id']} — {r['topic']}", *[f"- {f}" for f in r["failures"]], ""]
    return "\n".join(o) + "\n"
