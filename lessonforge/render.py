from .schema import Lesson


def to_markdown(l: Lesson, student: bool = False) -> str:
    """student=True : fiche élève sans corrigé ni notes enseignant."""
    if l.status == "declined":
        return f"# Sujet refusé\n\n{l.decline_reason}\n"
    o = [f"# {l.title}", f"*{l.level} · {l.duration_minutes} min*", ""]
    if not student:
        o += ["## Objectifs", *[f"- {x}" for x in l.objectives], ""]
        if l.prerequisites:
            o += ["## Prérequis", *[f"- {x}" for x in l.prerequisites], ""]
        if l.materials:
            o += ["## Matériel", *[f"- {x}" for x in l.materials], ""]
        o += ["## Déroulé"]
        for i, s in enumerate(l.stages, 1):
            o += [f"### {i}. {s.name} ({s.minutes} min)", s.activity]
            if s.teacher_notes:
                o += [f"> Note enseignant : {s.teacher_notes}"]
            o += [""]
    o += ["## À retenir", *[f"- {x}" for x in l.key_points], "", "## Exercices"]
    for i, e in enumerate(l.exercises, 1):
        o += [f"**{i}.** ({e.difficulty}) {e.statement}"]
        if e.choices:
            o += [f"   {chr(96 + j)}) {c}" for j, c in enumerate(e.choices, 1)]
        o += [""]
    o += ["## Devoir", l.homework, ""]
    if not student:
        o += ["## Critères d'évaluation", *[f"- {x}" for x in l.assessment_criteria], "",
              "## Corrigé (réservé à l'enseignant)"]
        for i, e in enumerate(l.exercises, 1):
            o += [f"**{i}.** {e.answer}  \n   {e.explanation}"]
    return "\n".join(o) + "\n"
