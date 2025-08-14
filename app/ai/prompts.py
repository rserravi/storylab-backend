SYNOPSIS_PROMPT = """Eres un guionista profesional de Hollywood. Genera una sinopsis en español (máx. 2 párrafos) con gancho comercial.
Devuelve texto plano, sin encabezados.
Contexto:
- Idea: {idea}
- Premisa: {premise}
- Tema: {theme}
- Género: {genre}
- Subgéneros: {subgenres}
"""

TREATMENT_PROMPT = """Escribe un Tratamiento breve (6-10 párrafos) cubriendo el arco de 3 actos.
- Tono: {tone}
- Público: {audience}
- Referencias: {references}
Logline: {logline}
"""

TURNING_POINTS_PROMPT = """Propón 5 Puntos de Giro (S3), con título y descripción (2-3 frases cada uno).
Género: {genre}. Tema: {theme}. Premisa: {premise}.
Devuelve JSON: [{{"id":"TP1","title":"...","description":"..."}}...]
"""

CHARACTER_PROMPT = """Diseña un personaje memorable (S4).
Nombre base: {seed_name}. Rol: {role}. Conflicto: {conflict}. Objetivo: {goal}.
Devuelve JSON con: id, name, bio, goal, conflict, arc.
"""

LOCATION_PROMPT = """Crea una localización cinematográfica (S6).
Nombre base: {seed_name}. Género: {genre}. Detalles deseados: {notes}.
Devuelve JSON con: id, name, details.
"""

SCENE_PROMPT = """Escribe una escena en formato Hollywood (S8).
Header: {header}
Contexto de la historia: {context}
Objetivo dramático: {goal}
Estilo: {style} | Nivel creativo: {creative_level}
Devuelve solo el cuerpo de la escena con líneas formateadas (no JSON).
"""

DIALOGUE_POLISH_PROMPT = """Reescribe el diálogo manteniendo intención y subtexto, haciéndolo más natural y cinematográfico.
Texto:
{raw}
Devuelve solo el nuevo diálogo.
"""

REVIEW_PROMPT = """Actúa como script doctor. Revisa el guion y devuelve un informe con secciones:
- Fortalezas
- Debilidades
- Ritmo/Estructura
- Personajes
- Diálogos
- Recomendaciones accionables (lista numerada)
Texto a revisar:
{text}
"""
