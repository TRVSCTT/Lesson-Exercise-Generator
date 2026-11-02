import json
from lessonforge.checks import check_lesson
from lessonforge.generator import generate
from lessonforge.gold import run_case, run_gold, report_markdown, load_cases
from lessonforge.render import to_markdown
from lessonforge.schema import Lesson, Request
from tests.fakes import FakeLLM, good

REQ = Request(topic="Le théorème de Pythagore", level="4e", duration_minutes=55, n_exercises=6)


class GradeLLM(FakeLLM):
    """Variante : le comparateur valide toutes les paires reçues."""
    def tool_call(self, system, user, tool_name, schema, max_tokens=6000):
        if tool_name == "comparer":
            n = [i for i, e in enumerate(self.last["exercises"], 1) if e["type"] not in ("qcm", "vrai_faux")]
            return {"verdicts": [{"index": i, "agrees": self.judge_agrees} for i in n]}
        return super().tool_call(system, user, tool_name, schema, max_tokens)


def test_good_lesson_passes_checks():
    assert check_lesson(Lesson.model_validate(good()), REQ) == []


def test_checks_catch_each_defect():
    g = good()
    g["stages"][0]["minutes"] = 5                      # total 50 != 55
    g["exercises"][0]["answer"] = "pas un choix"       # qcm
    g["exercises"][1]["answer"] = "peut-être"          # vrai/faux
    g["exercises"][2]["statement"] = "Pas de trou ici" # texte à trous
    g["exercises"].pop()                               # 5 exercices
    issues = " | ".join(check_lesson(Lesson.model_validate(g), REQ))
    for frag in ["totalisent 50", "texte exact", "« Vrai » ou « Faux »", "____", "5 exercices"]:
        assert frag in issues


def test_english_text_rejected():
    g = good()
    for s in g["stages"]:
        s["activity"] = "The students measure the triangle and the teacher explains the rule that is used in this lesson."
    g["key_points"] = ["The square of the hypotenuse is the sum of the squares of the other sides"]
    g["homework"] = "Compute the diagonal of the field with the rule that we have seen."
    for e in g["exercises"]:
        e["explanation"] = "This is the reason why the answer is what it is, and we have seen it in the lesson."
    assert any("français" in i for i in check_lesson(Lesson.model_validate(g), REQ))


def test_retry_fixes_invalid_first_attempt():
    bad = good(); bad["stages"][0]["minutes"] = 1
    llm = FakeLLM([bad, good()])
    r = generate(REQ, llm)
    assert r.ok and r.attempts == 2
    assert "totalisent" in llm.calls[1][1]             # les erreurs précises sont renvoyées au modèle


def test_never_silently_delivers_invalid():
    bad = good(); bad["stages"][0]["minutes"] = 1
    r = generate(REQ, FakeLLM([bad]), max_attempts=2)
    assert not r.ok and r.issues


def test_schema_violation_is_reported():
    r = generate(REQ, FakeLLM([{"status": "ok", "exercises": [{"type": "nope"}]}]), max_attempts=1)
    assert not r.ok and "schéma invalide" in r.issues[0]


def test_markdown_student_hides_answers():
    l = Lesson.model_validate(good())
    assert "Corrigé" in to_markdown(l) and "Corrigé" not in to_markdown(l, student=True)
    assert "Note enseignant" not in to_markdown(l, student=True)


CASE = {"id": "T1", "topic": "Le théorème de Pythagore", "level": "4e", "duration": 55, "exercises": 6,
        "must_include": [["hypoténuse"], ["carré"]]}


def test_gold_case_passes():
    assert run_case(CASE, GradeLLM(), judge=True).passed


def test_gold_fails_on_missing_concept():
    c = dict(CASE, must_include=[["dérivée"]])
    r = run_case(c, GradeLLM(), judge=True)
    assert not r.passed and "notion absente" in r.failures[0]


def test_gold_fails_when_judge_disputes_answer():
    r = run_case(CASE, GradeLLM(judge_agrees=False), judge=True)
    assert not r.passed and any("corrigé contesté" in f for f in r.failures)


def test_gold_declined_cases():
    declined = {"status": "declined", "decline_reason": "Précisez un chapitre précis des mathématiques."}
    c = {"id": "T2", "topic": "les maths", "expect": "declined"}
    assert run_case(c, FakeLLM([declined]), judge=True).passed
    assert not run_case(c, GradeLLM(), judge=True).passed       # a produit un cours -> échec


def test_gold_report_counts_failures():
    rep = run_gold([CASE, dict(CASE, id="T3", must_include=[["dérivée"]])], GradeLLM(), judge=True)
    assert rep["passed"] == 1 and rep["total"] == 2 and rep["pass_rate"] == 0.5
    assert "T3" in report_markdown(rep) and "Échecs" in report_markdown(rep)


def test_shipped_cases_are_well_formed():
    cases = load_cases("gold/cases.jsonl")
    assert len(cases) == 20 and len({c["id"] for c in cases}) == 20
    assert sum(c.get("expect") == "declined" for c in cases) == 2
