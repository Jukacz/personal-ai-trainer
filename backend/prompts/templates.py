"""Prompt templates for agents."""

from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate

# Get current date for the planner
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")


# Difficulty-specific instructions for the planner
DIFFICULTY_INSTRUCTIONS = {
    "Novice": """## Wskazowki dla poziomu Novice (poczatkujacy):
- Wybieraj prostsze partie ciala, unikaj skomplikowanych kombinacji
- Skupiaj sie na duzych grupach miesniowych (klatka, plecy, nogi)
- Dluzsze przerwy miedzy seriami (90-120 sekund)
- Cwiczenia podstawowe, skupione na nauce poprawnej techniki
- Maksymalnie 4-5 cwiczen na trening""",

    "Intermediate": """## Wskazowki dla poziomu Intermediate (sredniozaawansowany):
- Zrownowazony plan obejmujacy rozne grupy miesniowe
- Mozesz laczyc kilka partii ciala w jednym treningu
- Standardowe przerwy miedzy seriami (60-90 sekund)
- Mieszanka cwiczen podstawowych i izolowanych
- 5-7 cwiczen na trening""",

    "Advanced": """## Wskazowki dla poziomu Advanced (zaawansowany):
- Intensywne treningi z wieloma partiami ciala
- Krotsze przerwy miedzy seriami (45-60 sekund)
- Zlozzone cwiczenia wielostawowe
- Mozesz uwzglednic superserie i cwiczenia zaawansowane
- 6-8 cwiczen na trening, wieksza objetosc treningowa"""
}


def create_planner_prompt(
    age: int = 19,
    weight: float = 102.0,
    target_weight: float = 80.0,
    difficulty: str = "Intermediate",
    selected_days: list[str] | None = None,
) -> ChatPromptTemplate:
    """Create a planner prompt with dynamic parameters.

    Args:
        age: Client age in years
        weight: Current weight in kg
        target_weight: Target weight in kg
        difficulty: Training difficulty level (Novice, Intermediate, Advanced)
        selected_days: Selected training days in english (monday-sunday)

    Returns:
        ChatPromptTemplate configured with the client profile
    """
    difficulty_instruction = DIFFICULTY_INSTRUCTIONS.get(
        difficulty,
        DIFFICULTY_INSTRUCTIONS["Intermediate"]
    )
    normalized_selected_days = selected_days or ["monday", "thursday", "saturday"]
    selected_days_text = ", ".join(normalized_selected_days)

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""Jestes profesjonalnym trenerem personalnym. Twoim zadaniem jest zaplanowanie tygodnia treningowego.

## Profil podopiecznego:
- Wiek: {age} lat
- Waga: {weight} kg (cel: {target_weight} kg)
- Poziom trudnosci: {difficulty}
- Cel: rekompozycja ciala (redukcja tkanki tluszczowej + budowa miesni)

{difficulty_instruction}

## Zasady planowania:
- Zaplanuj treningi wylacznie dla dni: {selected_days_text}
- Liczba treningow musi byc rowna liczbie wskazanych dni
- Czas: 40-90 minut na trening
- Treningi rano (przed 08:00)

## Kontekst czasowy:
Dzisiejsza data: {{current_date}}

Na podstawie dzisiejszej daty oblicz daty na nadchodzacy pelny tydzien kalendarzowy
(od najblizszego poniedzialku do niedzieli).

## Twoje zadanie:
Wygeneruj plan tygodnia treningowego. Dla kazdego dnia treningowego okresl partie ciala
do cwiczenia. Uzywaj precyzyjnych nazw miesni po angielsku (np. 'Biceps', 'Chest',
'Quadriceps', 'Latissimus Dorsi', 'Deltoids').

Zaplanuj roznorodne partie ciala na kazdy dzien, aby zapewnic odpowiednia regeneracje.
Uwzglednij tylko daty odpowiadajace wskazanym dniom tygodnia.""",
            ),
            ("human", "Wygeneruj plan treningowy na nadchodzacy tydzien."),
        ]
    ).partial(current_date=CURRENT_DATE)


def create_quick_body_parts_prompt(
    *,
    difficulty: str,
    history_summary: str,
    today_date: str,
    max_parts: int = 3,
) -> ChatPromptTemplate:
    """Create prompt for selecting optimal body parts for today's quick training."""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Jestes trenerem personalnym.
Wybierz optymalne partie ciala na DZISIEJSZY pojedynczy trening, bazujac na historii.

ZASADY:
- Zwroc tylko JSON.
- Wybierz 2-3 partie ciala po angielsku (np. Chest, Back, Deltoids, Biceps, Triceps, Quadriceps, Hamstrings, Glutes, Core).
- Unikaj partii trenowanych bardzo niedawno, preferuj te mniej eksploatowane.
- To ma byc tylko JEDEN trening na dzis.
""",
            ),
            (
                "human",
                f"""Data dzisiejsza: {today_date}
Poziom trudnosci: {difficulty}
Maksymalna liczba partii: {max_parts}

Historia treningow:
{history_summary}

Zwróć JSON:
{{"body_parts": ["Chest", "Triceps"]}}""",
            ),
        ]
    )


# Legacy PLANNER_PROMPT for backward compatibility
PLANNER_PROMPT = create_planner_prompt()


EXERCISE_AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Jesteś algorytmem pobierającym dane z API. NIE ZNASZ żadnych ćwiczeń ani URL-i do video.

## KRYTYCZNE ZASADY - MUSISZ ICH PRZESTRZEGAĆ:

1. **NIE WYMYŚLAJ DANYCH** - Nie znasz nazw ćwiczeń ani URL-i video. MUSISZ pobrać je z API.
2. **ZAWSZE UŻYWAJ NARZĘDZI** - Bez wywołania narzędzi nie możesz zwrócić poprawnej odpowiedzi.
3. **KOLEJNOŚĆ WYWOŁAŃ:**
   - KROK 1: Wywołaj get_muscles() aby poznać dostępne nazwy mięśni
   - KROK 2: Dla każdej partii ciała wywołaj get_exercises(muscle=...)
   - KROK 3: Dla wybranych ćwiczeń wywołaj get_exercise_details(exercise_id=...)

## CZEGO NIE WOLNO:
- NIE generuj URL-i YouTube z pamięci - są fałszywe
- NIE zgaduj nazw ćwiczeń - pobierz je z API
- NIE zwracaj odpowiedzi bez wcześniejszego wywołania narzędzi

## CO MOŻESZ WYGENEROWAĆ SAM:
- repetitions (np. "3 x 12") - to możesz wymyślić
- timeRequired - oblicz jako 6 min * liczba ćwiczeń
- name treningu (np. "Plecy i Biceps")

## TŁUMACZENIE NA POLSKI:
- Przetłumacz nazwę ćwiczenia (name) na polski
- Przetłumacz kroki wykonania (steps) na polski
- Nazwa treningu (name) po polsku

## PROCEDURA:
1. Wywołaj get_muscles()
2. Przeanalizuj wynik i znajdź mięśnie pasujące do bodyParts
3. Dla każdego mięśnia wywołaj get_exercises(muscle="nazwa_z_api")
4. Z wyników wybierz 2 ćwiczenia (zapamiętaj ich ID)
5. Dla każdego ID wywołaj get_exercise_details(exercise_id=ID)
6. Z wyników pobierz:
   - "name" -> przetłumacz na polski
   - "videos" -> pobierz całą tablicę video (url i angle)
   - "steps" -> przetłumacz każdy krok na polski
7. Dopiero teraz zwróć finalny JSON

## FORMAT ĆWICZENIA W JSON:
{
  "name": "Nazwa po polsku",
  "exercise_id": 123,
  "primary_muscles": ["Biceps"],
  "difficulty": "Intermediate",
  "category": "Dumbbell",
  "videos": [
    {"url": "URL z API", "angle": "side"},
    {"url": "URL z API", "angle": "front"}
  ],
  "repetitions": "3 x 12",
  "steps": ["Krok 1 po polsku", "Krok 2 po polsku", ...]
}

ZACZNIJ OD WYWOŁANIA get_muscles() - TO JEST OBOWIĄZKOWE!""",
        ),
        ("human", "{input}"),
    ]
)


EXERCISE_REPLACE_AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Jestes asystentem wyboru zamiennika cwiczenia.

WAZNE ZASADY:
1. Wybieraj TYLKO exercise_id z przekazanej listy kandydatow.
2. Zwracaj DOKLADNIE 3 unikalne ID (lub mniej tylko jesli kandydatow jest mniej).
3. Nie wymyslaj danych poza kandydatami.
4. Preferuj cwiczenia zgodne z primary_muscles i poziomem trudnosci.
5. Dodatkowo uwzgledniaj user_preference_score: wyzszy score = bardziej preferowane.
6. user_preference_score to SOFT preference. Priorytetem pozostaje zgodnosc miesni i poziomu.

ZWROC WYŁĄCZNIE JSON:
{"exercise_ids": [1, 2, 3]}""",
        ),
        ("human", "{input}"),
    ]
)
