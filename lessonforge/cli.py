import argparse
import json
import sys
from pathlib import Path
from .generator import generate
from .gold import load_cases, run_gold, report_markdown
from .llm import AnthropicLLM
from .render import to_markdown
from .schema import Request


def cmd_generate(a) -> int:
    if len(a.topic.strip()) < 3:
        print("Sujet trop court.", file=sys.stderr)
        return 2
    req = Request(topic=a.topic.strip(), level=a.level, audience=a.audience,
                  duration_minutes=a.duration, n_exercises=a.exercises)
    res = generate(req, AnthropicLLM(a.model))
    if res.lesson is None:
        print("Échec : " + "; ".join(res.issues), file=sys.stderr)
        return 1
    if res.lesson.status == "declined":
        print(f"Sujet non traité : {res.lesson.decline_reason}", file=sys.stderr)
        return 3
    if res.issues:
        print(f"Avertissement : la leçon ne respecte pas tout le contrat après {res.attempts} essais :", file=sys.stderr)
        for i in res.issues:
            print(f"  - {i}", file=sys.stderr)
    out = (res.lesson.model_dump_json(indent=2) if a.format == "json"
           else to_markdown(res.lesson, student=a.student))
    if a.output:
        Path(a.output).write_text(out, encoding="utf-8")
        print(f"Écrit : {a.output}", file=sys.stderr)
    else:
        print(out)
    return 0 if not res.issues else 1


def cmd_gold(a) -> int:
    cases = load_cases(a.cases)[: a.limit] if a.limit else load_cases(a.cases)
    llm = AnthropicLLM(a.model)
    rep = run_gold(cases, llm, judge=not a.no_judge)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "gold_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    md = report_markdown(rep)
    (out / "gold_report.md").write_text(md, encoding="utf-8")
    print(md)
    ok = rep["pass_rate"] >= a.threshold
    print(f"Seuil {a.threshold:.0%} : {'ATTEINT' if ok else 'NON ATTEINT'}", file=sys.stderr)
    return 0 if ok else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lessonforge", description="PKG-45 Lesson & Exercise Generator")
    p.add_argument("--model", default=None, help="modèle Claude (défaut: $LESSONFORGE_MODEL)")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="sujet -> plan de cours + exercices")
    g.add_argument("topic")
    g.add_argument("--level", default="3e")
    g.add_argument("--audience", choices=["ecole", "centre"], default="ecole")
    g.add_argument("--duration", type=int, default=55, help="minutes")
    g.add_argument("--exercises", type=int, default=6)
    g.add_argument("--format", choices=["md", "json"], default="md")
    g.add_argument("--student", action="store_true", help="fiche élève : sans corrigé")
    g.add_argument("-o", "--output")
    g.set_defaults(fn=cmd_generate)

    v = sub.add_parser("gold", help="rejoue le jeu gold et publie le taux de réussite")
    v.add_argument("--cases", default="gold/cases.jsonl")
    v.add_argument("--out", default="reports")
    v.add_argument("--threshold", type=float, default=0.9)
    v.add_argument("--no-judge", action="store_true", help="saute la résolution indépendante des corrigés")
    v.add_argument("--limit", type=int, default=0)
    v.set_defaults(fn=cmd_gold)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
