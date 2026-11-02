"""Vérification indépendante des corrigés : un 2e appel résout chaque exercice SANS voir la réponse attendue,
puis on compare. Un désaccord = corrigé suspect (ou énoncé ambigu) -> la leçon échoue au gold."""
from .checks import norm
from .llm import LLM
from .schema import Lesson

SOLVE_SYS = ("Tu es un correcteur rigoureux. Résous chaque exercice indépendamment, en français. "
             "Réponds de façon brève (qcm : le texte exact du choix ; vrai/faux : « Vrai » ou « Faux »).")
GRADE_SYS = ("Tu compares une réponse attendue et une réponse candidate à un exercice. 'agrees' = true seulement si "
             "elles sont équivalentes sur le fond (formulation, unités ou ordre peuvent différer). Sois strict "
             "sur les nombres, dates et formules.")

SOLVE_SCHEMA = {"type": "object", "properties": {"answers": {"type": "array", "items": {
    "type": "object", "properties": {"index": {"type": "integer"}, "answer": {"type": "string"}},
    "required": ["index", "answer"]}}}, "required": ["answers"]}
GRADE_SCHEMA = {"type": "object", "properties": {"verdicts": {"type": "array", "items": {
    "type": "object", "properties": {"index": {"type": "integer"}, "agrees": {"type": "boolean"},
                                     "note": {"type": "string"}},
    "required": ["index", "agrees"]}}}, "required": ["verdicts"]}


def judge_lesson(l: Lesson, llm: LLM) -> list[dict]:
    """Renvoie [{index, agrees, note}] pour chaque exercice (index à partir de 1)."""
    items = [{"index": i, "type": e.type, "statement": e.statement, "choices": e.choices}
             for i, e in enumerate(l.exercises, 1)]
    solved = llm.tool_call(SOLVE_SYS, f"Exercices :\n{items}", "resoudre", SOLVE_SCHEMA)
    cand = {a["index"]: a["answer"] for a in solved.get("answers", [])}

    out, to_grade = {}, []
    for i, e in enumerate(l.exercises, 1):
        c = cand.get(i)
        if c is None:
            out[i] = {"index": i, "agrees": False, "note": "aucune réponse indépendante"}
        elif e.type in ("qcm", "vrai_faux"):
            ok = norm(c).strip() == norm(e.answer).strip()
            out[i] = {"index": i, "agrees": ok, "note": "" if ok else f"candidat: {c} / attendu: {e.answer}"}
        else:
            to_grade.append({"index": i, "statement": e.statement, "expected": e.answer, "candidate": c})
    if to_grade:
        g = llm.tool_call(GRADE_SYS, f"Paires :\n{to_grade}", "comparer", GRADE_SCHEMA)
        got = {v["index"]: v for v in g.get("verdicts", [])}
        for t in to_grade:
            v = got.get(t["index"])
            out[t["index"]] = ({"index": t["index"], "agrees": bool(v["agrees"]), "note": v.get("note", "")}
                               if v else {"index": t["index"], "agrees": False, "note": "non évalué"})
    return [out[i] for i in sorted(out)]
