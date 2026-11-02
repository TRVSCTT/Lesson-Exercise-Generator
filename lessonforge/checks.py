"""Contrôles déterministes (sans IA) appliqués à chaque leçon générée."""
import re
import unicodedata
from .schema import Lesson, Request

FR = set("le la les un une des du de d et est sont en dans pour par sur avec ce cette ces qui que quoi il elle ils elles "
         "on nous vous au aux ne pas plus ou où se sa son ses leur leurs mais donc car si comme à y a été être "
         "avoir fait".split())
EN = set("the and is are of to in for with that this these which what it they we you not or but if as be been "
         "have has was were from by on at an".split())


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def lesson_text(l: Lesson) -> str:
    parts = [l.title, *l.objectives, *l.prerequisites, *l.materials, *l.key_points, l.homework,
             *l.assessment_criteria]
    for s in l.stages:
        parts += [s.name, s.activity, s.teacher_notes]
    for e in l.exercises:
        parts += [e.statement, *e.choices, e.answer, e.explanation]
    return "\n".join(p for p in parts if p)


def french_ratio(text: str) -> tuple[float, float]:
    words = re.findall(r"[a-zà-ÿ']+", text.lower())
    words = [w.split("'")[-1] for w in words] + [w for w in words]
    if not words:
        return 0.0, 0.0
    return (sum(w in FR for w in words) / len(words), sum(w in EN for w in words) / len(words))


def check_lesson(l: Lesson, req: Request) -> list[str]:
    """Renvoie la liste des problèmes ; vide = la leçon respecte le contrat."""
    if l.status == "declined":
        return [] if l.decline_reason.strip() else ["declined sans decline_reason"]
    issues: list[str] = []
    if not l.title.strip():
        issues.append("titre vide")
    if not 2 <= len(l.objectives) <= 5:
        issues.append(f"{len(l.objectives)} objectifs (attendu 2 à 5)")
    if len(l.stages) < 3:
        issues.append(f"{len(l.stages)} étapes (minimum 3)")
    total = sum(s.minutes for s in l.stages)
    if total != req.duration_minutes:
        issues.append(f"les étapes totalisent {total} min, attendu exactement {req.duration_minutes}")
    if not l.key_points:
        issues.append("aucun point clé de synthèse")
    if not l.homework.strip():
        issues.append("devoir vide")
    if len(l.exercises) != req.n_exercises:
        issues.append(f"{len(l.exercises)} exercices, attendu exactement {req.n_exercises}")
    if len(l.exercises) >= 4 and len({e.difficulty for e in l.exercises}) < 2:
        issues.append("tous les exercices ont la même difficulté")
    seen = set()
    for i, e in enumerate(l.exercises, 1):
        tag = f"exercice {i}"
        if not e.statement.strip():
            issues.append(f"{tag}: énoncé vide")
        if not e.answer.strip():
            issues.append(f"{tag}: réponse vide")
        if not e.explanation.strip():
            issues.append(f"{tag}: explication vide")
        if norm(e.statement) in seen:
            issues.append(f"{tag}: énoncé en double")
        seen.add(norm(e.statement))
        if e.type == "qcm":
            if len(e.choices) != 4:
                issues.append(f"{tag}: qcm avec {len(e.choices)} choix (attendu 4)")
            if len({norm(c) for c in e.choices}) != len(e.choices):
                issues.append(f"{tag}: choix en double")
            if e.answer not in e.choices:
                issues.append(f"{tag}: la réponse n'est pas le texte exact d'un choix")
        elif e.choices:
            issues.append(f"{tag}: des choix fournis pour un exercice de type {e.type}")
        if e.type == "vrai_faux" and e.answer not in ("Vrai", "Faux"):
            issues.append(f"{tag}: réponse vrai/faux doit être « Vrai » ou « Faux »")
        if e.type == "texte_a_trous" and "____" not in e.statement:
            issues.append(f"{tag}: texte à trous sans « ____ »")
    fr, en = french_ratio(lesson_text(l))
    if fr < 0.12 or en > fr:
        issues.append(f"le texte ne semble pas être en français (fr={fr:.2f}, en={en:.2f})")
    return issues
