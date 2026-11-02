"""Contrat de sortie : tout ce que l'outil produit passe par ces modèles."""
from typing import Literal
from pydantic import BaseModel, Field

ExerciseType = Literal["qcm", "vrai_faux", "texte_a_trous", "question_ouverte", "calcul"]


class Request(BaseModel):
    topic: str
    level: str = "3e"
    audience: Literal["ecole", "centre"] = "ecole"
    duration_minutes: int = Field(55, ge=20, le=240)
    n_exercises: int = Field(6, ge=2, le=15)


class Stage(BaseModel):
    name: str
    minutes: int = Field(ge=1)
    activity: str
    teacher_notes: str = ""


class Exercise(BaseModel):
    type: ExerciseType
    difficulty: Literal["facile", "moyen", "difficile"]
    statement: str
    choices: list[str] = []          # qcm uniquement
    answer: str                      # qcm: texte exact d'un choix ; vrai_faux: "Vrai"/"Faux"
    explanation: str


class Lesson(BaseModel):
    status: Literal["ok", "declined"] = "ok"
    decline_reason: str = ""
    title: str = ""
    level: str = ""
    duration_minutes: int = 0
    objectives: list[str] = []
    prerequisites: list[str] = []
    materials: list[str] = []
    stages: list[Stage] = []
    key_points: list[str] = []
    exercises: list[Exercise] = []
    homework: str = ""
    assessment_criteria: list[str] = []
