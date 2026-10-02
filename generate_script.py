# -*- coding: utf-8 -*-
"""
Cerebro del canal GYM ("Fit en 30s").
Gemini ELIGE el tema libre cada dia (dentro del canal). Para que no se repita ni
derive, se le pasa una PISTA rotatoria distinta cada dia (un area/enfoque), ademas
de formato, gancho y cierre (todo por rotacion determinista).
Devuelve el mismo dict que usa generate.py.
"""
import os, sys, json, datetime, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("GEMINI_MODEL", "").strip()
_MODEL_CANDIDATES = [
    "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash",
    "gemini-2.5-flash-lite", "gemini-2.0-flash-001", "gemini-1.5-flash",
]

CANAL_NOMBRE = "GIMNASIO Y ENTRENAMIENTO"
HASHTAGS_BASE = ("gym", "fitness", "entrenamiento", "rutina")
TEMA_GENERICO = "el entrenamiento"
TITULO_FALLBACK = "3 errores en {base} que frenan tus resultados"
BG_DEFAULT = "red"
BROLL_FALLBACK = "silhouette of a person doing a deep squat in an empty gym at night"
BROLL_EJEMPLOS = ("gimnasio real con luz dura y polvo en el aire, personas anonimas (de espaldas, "
                  "recortadas o a contraluz); ej: 'close up of hands gripping a barbell with chalk, "
                  "gym light', 'silhouette of a person doing a deep squat in an empty gym at night', "
                  "'dumbbell rack in a dim gym, shallow depth of field'")
TONO = ("directo y practico, de entrenador que va al grano. Espanol de Espana. Frases cortas. "
        "Cada frase, una correccion util. Sin humo ni promesas.")
REGLA_EXTRA = ("- INFORMA, NO RECETES: nada de dietas, calorias, dosis de suplementos, perdida de peso "
               "prometida ni consejos medicos. Si el tema roza una molestia o lesion, di que eso lo "
               "valora un profesional.\n"
               "- Nada de cuerpos sexualizados ni primeros planos de gluteos o abdomen desnudo. "
               "Personas anonimas y vestidas para entrenar.\n"
               "- Cada escena muestra EXACTAMENTE el ejercicio o el fallo que se esta narrando.")
MASTER_FALLBACK = "Eres un guionista de Shorts de gimnasio y entrenamiento en espanol de Espana."

PISTAS = [
    ("la sentadilla y sus fallos", "silhouette doing a deep squat in an empty gym"),
    ("press de banca y pecho", "barbell bench press bar over a chest, low angle"),
    ("espalda, remo y dominadas", "hands gripping a pull up bar, chalk dust"),
    ("peso muerto y la tecnica de la cadera", "loaded barbell on gym floor, close up of plates"),
    ("hombros sin hacerse dano", "lateral raise silhouette against a window"),
    ("core, abdominales y postura", "plank position silhouette on a gym floor"),
    ("piernas, gemelos y tren inferior", "calf raise on a step, close up of shoes"),
    ("descanso entre series y recuperacion", "gym clock on a wall with weights below"),
    ("cardio y su sitio junto a las pesas", "treadmill belt in motion, dim gym light"),
    ("calentar bien en pocos minutos", "person doing arm circles in an empty gym"),
    ("entrenar en casa sin material", "bodyweight push up on a living room floor"),
    ("progresar y no estancarte", "hands adding a small plate to a barbell"),
    ("errores tipicos de principiante", "beginner using a barbell rack, wide shot"),
    ("mitos del gimnasio que siguen vivos", "empty gym with mirrors and dim lights"),
    ("constancia y motivacion para ir", "lone figure entering a gym at night"),
    ("la respiracion al levantar peso", "close up of a lifter's chest and belt, side light"),
    ("el sueno, el descanso y los resultados", "dark bedroom with gym bag by the door"),
    ("como saber si progresas de verdad", "hand marking a training notebook on a bench"),
]

FORMATOS = [
    "3 ERRORES: tres fallos concretos sobre el tema, con su correccion en la misma frase.",
    "EL FALLO GORDO: un solo error del tema, por que arruina el resultado y como se arregla.",
    "MITO O VERDAD: tres creencias del gimnasio sobre el tema y lo que dice la practica.",
    "COMO SE HACE: la tecnica del tema en cuatro pasos rapidos y claros.",
    "LO QUE NADIE TE DICE: 3 cosas sobre el tema que no te cuentan en el gimnasio.",
]

GANCHOS = [
    "abre nombrando el fallo exacto que hace el espectador cada semana, y remata con 'y aun hay uno peor'",
    "abre con una imagen concreta del ejercicio mal hecho, en presente, como si lo estuvieras viendo",
    "abre desmontando algo que se repite en todos los gimnasios y es mentira",
    "abre con una cifra concreta (series, minutos, semanas) que cambia el resultado",
    "abre con una pregunta incomoda sobre por que no progresa desde hace meses",
]

CTAS = [
    "¿Cuál fallabas tú? Comenta el número.",
    "Guárdate esto para tu próximo entrenamiento.",
    "Etiqueta al del gimnasio que lo hace mal.",
    "¿Qué ejercicio quieres el próximo día?",
    "Sígueme, que mañana corrijo otro.",
]

POWER = ("error", "errores", "fallo", "deja de", "asi si", "nadie", "jamas", "mito",
         "no vas a creer", "brutal", "frena", "progresar", "peor", "mejor", "secreto")

BGS = ["blue", "green", "orange", "purple", "teal", "red"]


def _run_seed():
    try:
        return int(os.environ.get("GITHUB_RUN_NUMBER", "0"))
    except ValueError:
        return 0

def _daykey():
    return datetime.date.today().toordinal() + _run_seed()

def _rot(lst, stride):
    return lst[(_daykey() * stride) % len(lst)]


def _list_models(key):
    try:
        url = ("https://generativelanguage.googleapis.com/v1beta/models"
               f"?key={key}&pageSize=200")
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read().decode())
        return [m.get("name", "").replace("models/", "") for m in data.get("models", [])
                if "generateContent" in (m.get("supportedGenerationMethods") or [])]
    except Exception:
        return []

def _model_order(key):
    order = []
    if MODEL:
        order.append(MODEL)
    for m in _MODEL_CANDIDATES:
        if m not in order:
            order.append(m)
    disc = _list_models(key)
    # Prioriza Gemini 'flash', luego otros Gemini, luego el resto.
    # Los 'gemma' (no dan JSON fiable) van al final.
    for m in disc:
        if "gemini" in m and "flash" in m and m not in order:
            order.append(m)
    for m in disc:
        if "gemini" in m and m not in order:
            order.append(m)
    for m in disc:
        if "gemma" not in m and m not in order:
            order.append(m)
    for m in disc:
        if m not in order:
            order.append(m)
    return order

def _post_generate(model, prompt, key):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 1.0, "responseMimeType": "application/json"},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    return data["candidates"][0]["content"]["parts"][0]["text"]

def _extract_json(txt):
    """Saca un JSON valido aunque el modelo lo envuelva en ```json ... ``` o texto."""
    if not txt:
        return None
    t = txt.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t[:4].lower() == "json":
            t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j != -1 and j > i:
        t = t[i:j + 1]
    try:
        return json.loads(t)
    except Exception:
        return None

def _gen_json(prompt, key):
    """Prueba modelos hasta obtener un JSON valido. Salta los que fallen o
    devuelvan basura (p.ej. gemma con respuesta vacia). None si ninguno lo da."""
    last = None
    for model in _model_order(key):
        try:
            txt = _post_generate(model, prompt, key)
        except Exception as e:
            last = e
            continue
        obj = _extract_json(txt)
        if isinstance(obj, dict) and obj.get("lines"):
            sys.stderr.write(f"[ai] modelo usado: {model}\n")
            return obj
        sys.stderr.write(f"[ai] {model} no dio JSON valido; pruebo otro.\n")
    if last:
        sys.stderr.write(f"[ai] ultimo error: {last}\n")
    return None


# Red de seguridad: si el modelo escribe sin enes ni tildes, se restauran las
# palabras mas comunes (el subtitulo salia como "MANANA" en vez de "MANANA" con ene).
_ORTO = {
    "manana": "mañana", "ano": "año", "anos": "años", "nino": "niño", "ninos": "niños",
    "nina": "niña", "ninas": "niñas", "senor": "señor", "senora": "señora",
    "espanol": "español", "espanola": "española", "Espana": "España", "espana": "España",
    "pequeno": "pequeño", "pequena": "pequeña", "sueno": "sueño", "suenos": "sueños",
    "bano": "baño", "banos": "baños", "compania": "compañía", "montana": "montaña",
    "manana,": "mañana,", "ensenar": "enseñar", "ensena": "enseña", "diseno": "diseño",
    "extrano": "extraño", "dano": "daño", "danos": "daños", "puno": "puño",
    "canon": "cañón", "otono": "otoño", "sueno.": "sueño.", "duena": "dueña",
    "dueno": "dueño", "acompanar": "acompañar", "manana.": "mañana.",
}

def _fix_orto(txt):
    if not isinstance(txt, str) or not txt:
        return txt
    out = []
    for w in txt.split(" "):
        low = w.lower()
        rep = _ORTO.get(low) or _ORTO.get(w)
        if rep:
            if w[:1].isupper():
                rep = rep[:1].upper() + rep[1:]
            out.append(rep)
        else:
            out.append(w)
    return " ".join(out)


def _validate(s, tema="", cta="", broll_en=""):
    assert isinstance(s.get("lines"), list) and 4 <= len(s["lines"]) <= 12, "lineas fuera de rango"
    for ln in s["lines"]:
        assert ln.get("voice"), "linea sin voz"
        ln.setdefault("cap", "")
        ln["voice"] = _fix_orto(ln["voice"])
        ln["cap"] = _fix_orto(ln["cap"])
    s.setdefault("bg", BG_DEFAULT)
    if s["bg"] not in BGS:
        s["bg"] = BG_DEFAULT
    hs = [h.lstrip("#") for h in s.get("hashtags", []) if h.strip()]
    if not hs or hs[0].lower() != "shorts":
        hs = ["Shorts"] + [h for h in hs if h.lower() != "shorts"]
    s["hashtags"] = (hs + list(HASHTAGS_BASE))[:6]

    # TITULO: obliga a que lleve un numero o una palabra potente
    t = _fix_orto((s.get("title") or "").strip())
    low = t.lower()
    tiene_num = any(c.isdigit() for c in t) or any(w in low for w in
        ("tres", "cuatro", "cinco", "dos"))
    tiene_power = any(p in low for p in POWER)
    if not t:
        base = (tema or TEMA_GENERICO).strip()
        t = TITULO_FALLBACK.format(base=base)
    if "#short" not in low:
        t = t + " #shorts"
    s["title"] = t

    # CTA obligatorio como ultima linea (cebo de comentarios)
    if cta:
        last = (s["lines"][-1].get("voice", "") or "").lower()
        if "coment" not in last and "abajo" not in last and "sigue" not in last and "guarda" not in last:
            s["lines"].append({"voice": cta, "cap": "comenta abajo"})

    if not (s.get("description") or "").strip():
        s["description"] = (t.replace(" #shorts", "") + ". " + (cta or "")).strip()
    s["description"] = _fix_orto(s["description"]).rstrip()

    # BROLL como pista de imagen
    bl = s.get("broll_list")
    if not isinstance(bl, list) or not bl:
        bl = [broll_en] if broll_en else []
    bl = [b.strip() for b in bl if isinstance(b, str) and b.strip()][:12]
    if bl:
        s["broll_list"] = bl
        s["broll"] = bl[0]
    elif broll_en:
        s["broll_list"] = [broll_en]; s["broll"] = broll_en

    try:
        s["video_idx"] = int(s.get("video_idx", -1))
    except (TypeError, ValueError):
        s["video_idx"] = -1
    s["ai_disclosure"] = False
    s["id"] = "ia-" + datetime.date.today().isoformat()
    s.pop("chart", None)
    return s


def _schema(broll_en, formato, gancho, cta, pista):
    hs = '", "'.join(["Shorts"] + list(HASHTAGS_BASE))
    return f"""
Devuelve UNICAMENTE un JSON valido (sin texto alrededor) con esta forma exacta:
{{
  "title": "titulo IMPACTANTE con un NUMERO y/o una palabra potente. Sobre el tema de HOY. Max 80 caracteres, 1 emoji opcional, incluye #shorts.",
  "description": "1-2 frases con gancho + hashtags. Termina invitando a comentar.",
  "hashtags": ["{hs}"],
  "bg": "uno de: orange, red, purple, teal",
  "broll": "{broll_en}",
  "broll_list": ["una ESCENA para RECREAR con IA por CADA linea, EN INGLES, concreta, con ACCION, lugar y luz ({BROLL_EJEMPLOS}). En el MISMO orden que 'lines'. UNA escena por CADA linea (mismo numero de escenas que de lineas), y cada escena debe mostrar EXACTAMENTE lo que se narra en esa linea. Describe una imagen VIVA, como un plano de cine."],
  "ai_disclosure": false,
  "video_idx": "indice 0-based de la ESCENA de broll_list que MAS ganaria con MOVIMIENTO de video real (la mas dinamica). Devuelve -1 si ninguna lo necesita. Como MUCHO una.",
  "lines": [
    {{"voice": "frase que se narra (numeros en palabras)", "cap": "subtitulo corto en pantalla (2-4 palabras)"}}
  ]
}}
GUION DE HOY (canal de {CANAL_NOMBRE}, formato viral, DISTINTO a cualquier dia anterior):
- ELIGE TU EL TEMA DE HOY: libre, dentro del canal de {CANAL_NOMBRE}. Concreto y con gancho. Que sea DISTINTO a lo mas tipico y a lo de dias anteriores; NO te repitas ni tires siempre por lo mismo.
- PISTA PARA VARIAR HOY (orientate hacia esta zona para no caer siempre en lo mismo, pero TU decides el tema y el enfoque exactos, y puedes afinar dentro de ella): {pista}.
- FORMATO DE HOY: {formato}
- LINEA 1 = GANCHO (primer segundo). Tecnica de hoy: {gancho}. PROHIBIDO usar frases-comodin genericas ("el noventa por ciento no sabe esto", "prepara la cabeza", "esto te va a explotar la mente", "agarrate"): NO enganchan, suenan a bot. El gancho debe ser CONCRETO, especifico y util, sacado de lo MAS fuerte del tema de hoy, y ABRIR UN BUCLE (promete algo aun mejor que todavia no cuentas). Nada de empezar con "En [tema]...".
- Luego el contenido, cada parte concreta y VERAZ (nada inventado). De menos a mas: lo mejor al final.
- Encadena con TENSION ("pero lo siguiente es mejor", "y aun hay mas"), NO con "primero, segundo, tercero" a secas.
- ORTOGRAFIA: espanol de Espana IMPECABLE, con TILDES y con la letra ENE (mañana, año, España, sueño, pequeño). NUNCA sustituyas la ñ por n. Cuidado con articulos y concordancia. Frases cortas y en presente.
- ULTIMA LINEA = CIERRE que invita a participar: algo tipo "{cta}".
- Entre 5 y 8 lineas en total. Frases cortas y con energia (ritmo de Short, 30-45 s).
- Tono: {TONO}
- 'cap' sin emojis. 'voice' escribe los numeros con letras.
- SEGURIDAD (obligatorio): las escenas deben ser APTAS PARA YOUTUBE Y PUBLICIDAD. Con fuerza, pero SIN sangre, heridas, cuerpos mutilados, desnudos ni violencia explicita. Nada de caras de personas reales famosas.
{REGLA_EXTRA}
- CRITICO: cada escena de 'broll_list' debe MOSTRAR EXACTAMENTE lo que se narra en esa parte, EN EL MISMO ORDEN. NADA generico ni palabras sueltas: escena de cine con accion + lugar + luz, EN INGLES.
"""


def generate():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    try:
        master = open(os.path.join(BASE, "PROMPT-MAESTRO.md"), encoding="utf-8").read()
    except Exception:
        master = MASTER_FALLBACK

    pista, broll_en = _rot(PISTAS, 1)
    tema = ""  # el tema lo ELIGE Gemini; 'pista' solo orienta para no repetir
    formato = _rot(FORMATOS, 3)
    gancho = _rot(GANCHOS, 5)
    cta = _rot(CTAS, 7)
    hoy = datetime.date.today().isoformat()

    prompt = (master
              + f"\n\n---\nTAREA DE HOY ({hoy}):\n"
              + f"Crea un Short de {CANAL_NOMBRE} con el formato viral de abajo. ELIGE tu el tema (libre, del canal, sin repetir), "
                "y sigue EXACTAMENTE el formato, el gancho y el cierre que se te asignan. Todo debe ser VERAZ.\n"
              + _schema(broll_en, formato, gancho, cta, pista))
    try:
        s = _gen_json(prompt, key)
        if not s:
            raise RuntimeError("ningun modelo dio JSON valido")
        s = _validate(s, tema=tema, cta=cta, broll_en=broll_en)
        return s
    except Exception as e:
        sys.stderr.write(f"[ai] no se pudo generar con IA ({e}); se usara el banco.\n")
        return None


if __name__ == "__main__":
    import json as _j
    s = generate()
    print(_j.dumps(s, ensure_ascii=False, indent=2) if s else "None (sin GEMINI_API_KEY o error)")
