import copy

GOOD = {
    "status": "ok", "decline_reason": "",
    "title": "Le théorème de Pythagore", "level": "4e", "duration_minutes": 55,
    "objectives": ["Identifier l'hypoténuse dans un triangle rectangle", "Calculer une longueur avec le théorème de Pythagore"],
    "prerequisites": ["Savoir calculer le carré d'un nombre"], "materials": ["Équerre", "Règle"],
    "stages": [
        {"name": "Accroche", "minutes": 10, "activity": "Les élèves mesurent un triangle rectangle dans la classe.", "teacher_notes": ""},
        {"name": "Découverte", "minutes": 20, "activity": "On établit que le carré de l'hypoténuse est la somme des carrés des deux autres côtés.", "teacher_notes": ""},
        {"name": "Pratique", "minutes": 15, "activity": "Exercices guidés au tableau avec les élèves.", "teacher_notes": ""},
        {"name": "Synthèse", "minutes": 10, "activity": "On résume la propriété et ses conditions d'application.", "teacher_notes": ""},
    ],
    "key_points": ["Dans un triangle rectangle, le carré de l'hypoténuse est égal à la somme des carrés des autres côtés"],
    "exercises": [
        {"type": "qcm", "difficulty": "facile", "statement": "Quel côté est l'hypoténuse ?",
         "choices": ["Le plus long", "Le plus court", "Le côté vertical", "Le côté horizontal"],
         "answer": "Le plus long", "explanation": "L'hypoténuse est le côté opposé à l'angle droit, c'est le plus long."},
        {"type": "vrai_faux", "difficulty": "facile", "statement": "Le théorème de Pythagore s'applique à tout triangle.",
         "choices": [], "answer": "Faux", "explanation": "Il ne s'applique qu'aux triangles rectangles."},
        {"type": "texte_a_trous", "difficulty": "moyen", "statement": "Dans un triangle rectangle, le ____ de l'hypoténuse est égal à la somme des ____ des deux autres côtés.",
         "choices": [], "answer": "carré ; carrés", "explanation": "C'est l'énoncé du théorème."},
        {"type": "calcul", "difficulty": "moyen", "statement": "Un triangle rectangle a des côtés de l'angle droit de 3 cm et 4 cm. Calculer l'hypoténuse.",
         "choices": [], "answer": "5 cm", "explanation": "3² + 4² = 25 et la racine de 25 vaut 5."},
        {"type": "calcul", "difficulty": "difficile", "statement": "L'hypoténuse mesure 13 cm et un côté 5 cm. Calculer l'autre côté.",
         "choices": [], "answer": "12 cm", "explanation": "13² − 5² = 169 − 25 = 144, la racine de 144 vaut 12."},
        {"type": "question_ouverte", "difficulty": "difficile", "statement": "Expliquer pourquoi on ne peut pas appliquer le théorème si l'angle droit n'est pas garanti.",
         "choices": [], "answer": "La relation n'est vraie que pour les triangles rectangles.", "explanation": "Sans angle droit, la somme des carrés diffère du carré du plus grand côté."},
    ],
    "homework": "Calculer la diagonale d'un terrain rectangulaire de 30 m sur 40 m.",
    "assessment_criteria": ["Identifie correctement l'hypoténuse", "Pose le calcul sans erreur"],
}


def good():
    return copy.deepcopy(GOOD)


class FakeLLM:
    """Renvoie des sorties préprogrammées dans l'ordre ; le solveur répond comme le corrigé (juge d'accord)."""
    def __init__(self, lessons=None, judge_agrees=True):
        self.lessons = list(lessons or [good()])
        self.calls = []
        self.judge_agrees = judge_agrees
        self.last = None

    def tool_call(self, system, user, tool_name, schema, max_tokens=6000):
        self.calls.append((tool_name, user))
        if tool_name == "emettre_cours":
            self.last = self.lessons.pop(0) if len(self.lessons) > 1 else self.lessons[0]
            return copy.deepcopy(self.last)
        if tool_name == "resoudre":
            ex = self.last["exercises"]
            return {"answers": [{"index": i, "answer": e["answer"] if self.judge_agrees else "???"}
                                for i, e in enumerate(ex, 1)]}
        if tool_name == "comparer":
            return {"verdicts": [{"index": 0, "agrees": True}]}  # remplacé ci-dessous si besoin
        raise AssertionError(tool_name)
