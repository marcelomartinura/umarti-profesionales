#!/usr/bin/env python3
"""Genera el directorio de profesionales a partir de data/profesionales.csv.

Uso:  python3 tools/build.py
Escribe index.html, sumate/index.html, p/<slug>/index.html, sitemap.xml y robots.txt
en la raíz del repositorio. Las fichas marcadas como ejemplo llevan noindex.
"""
import csv
import html
import json
import re
import shutil
import unicodedata
from urllib.parse import quote
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://profesionales.umartidigital.com"
MARCA = "Umarti Profesionales"
MIN_PARA_CONTADORES = 10  # los contadores del inicio aparecen recién con 10 fichas reales

CATEGORIAS = [
    "Contabilidad e impuestos", "Derecho", "Arquitectura y construcción", "Ingeniería",
    "Diseño y fotografía", "Marketing y comunicación", "Tecnología y desarrollo",
    "Consultoría de negocios", "Recursos humanos", "Finanzas y seguros",
    "Educación y capacitación", "Traducción e idiomas", "Salud y bienestar", "Inmobiliario",
]
PAISES = [
    "México", "Argentina", "Colombia", "Chile", "Perú", "Uruguay", "Paraguay", "Bolivia",
    "Ecuador", "Panamá", "Costa Rica", "Guatemala", "República Dominicana", "Venezuela",
]
MODALIDADES = ["Online", "Presencial", "Online y presencial"]

e = lambda s: html.escape(str(s or ""), quote=True)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def iniciales(nombre):
    partes = [p for p in nombre.split() if p]
    return (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()


def cargar():
    with open(ROOT / "data" / "profesionales.csv", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    profesionales = []
    for r in filas:
        if not r.get("nombre", "").strip():
            continue
        r = {k: (v or "").strip() for k, v in r.items()}
        r["ejemplo"] = r["ejemplo"].lower() in ("si", "sí", "true", "1")
        r["slug"] = r["slug"] or slugify(f'{r["profesion"]}-{r["nombre"]}-{r["ciudad"]}')
        r["servicios"] = [s.strip() for s in r["servicios"].split("|") if s.strip()]
        r["wa"] = re.sub(r"\D", "", r["whatsapp"])
        profesionales.append(r)
    # reales primero, después los ejemplos
    profesionales.sort(key=lambda p: (p["ejemplo"], p["nombre"]))
    return profesionales


# ---------- piezas comunes ----------

def head(titulo, descripcion, url, noindex=False, extra=""):
    robots = '<meta name="robots" content="noindex, follow">\n' if noindex else ""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
{robots}<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{SITE}/assets/img/umarti-logo.png">
<meta name="theme-color" content="#0B1E2F">
<link rel="icon" type="image/png" href="/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/styles.css">
{extra}</head>
<body>
<header class="topbar">
  <div class="wrap topbar__inner">
    <a href="/" class="brand" aria-label="{MARCA}, ir al inicio">
      <img src="/assets/img/umarti-logo.webp" alt="" width="112" height="33">
      <span class="brand__name">Profesionales</span>
    </a>
    <nav class="topbar__nav" aria-label="Secciones">
      <a href="/#directorio">Buscar</a>
      <a href="/#como-funciona">Cómo funciona</a>
      <a href="/sumate/" class="btn btn--small">Suma tu ficha</a>
    </nav>
  </div>
</header>
"""


FOOTER = f"""
<footer class="footer">
  <div class="wrap footer__inner">
    <p><strong>{MARCA}</strong> es un proyecto de <a href="https://umartidigital.com">Umarti Digital</a>.</p>
    <p>Los profesionales publican sus propios datos. Umarti no interviene en los acuerdos ni en los pagos entre profesionales y clientes.</p>
    <nav aria-label="Pie de página"><a href="/">Directorio</a><a href="/sumate/">Suma tu ficha</a><a href="https://consultoria.umartidigital.com">Consultoría</a></nav>
  </div>
</footer>
"""


def avatar(p, clase="avatar"):
    return f'<span class="{clase}" aria-hidden="true">{e(iniciales(p["nombre"]))}</span>'


# ---------- inicio ----------

def tarjeta(p):
    texto_busqueda = " ".join([p["nombre"], p["profesion"], p["categoria"], p["ciudad"], p["pais"], *p["servicios"]])
    servicios = "".join(f"<li>{e(s)}</li>" for s in p["servicios"][:3])
    marca = '<span class="tag tag--ejemplo">Ejemplo</span>' if p["ejemplo"] else ""
    anios = f' · {e(p["anios"])} años de experiencia' if p["anios"] else ""
    return f"""      <article class="card" data-cat="{e(p['categoria'])}" data-pais="{e(p['pais'])}" data-texto="{e(texto_busqueda)}">
        <a href="/p/{e(p['slug'])}/" class="card__link">
          <div class="card__top">
            {avatar(p)}
            <div>
              <h3 class="card__name">{e(p['nombre'])}</h3>
              <p class="card__job">{e(p['profesion'])}</p>
            </div>
            {marca}
          </div>
          <p class="card__meta">{e(p['ciudad'])}, {e(p['pais'])}{anios}</p>
          <ul class="card__services">{servicios}</ul>
          <p class="card__foot"><span class="tag">{e(p['modalidad'])}</span><span class="card__cta">Ver ficha</span></p>
        </a>
      </article>"""


def inicio(profs):
    reales = [p for p in profs if not p["ejemplo"]]
    cats = Counter(p["categoria"] for p in profs)
    paises = sorted({p["pais"] for p in profs})
    chips = ['<button type="button" class="chip is-active" data-cat="">Todas</button>']
    for c in CATEGORIAS + sorted(set(cats) - set(CATEGORIAS)):
        if cats[c]:
            chips.append(f'<button type="button" class="chip" data-cat="{e(c)}">{e(c)} <span class="chip__n">{cats[c]}</span></button>')
    opciones_pais = "".join(f'<option value="{e(x)}">{e(x)}</option>' for x in paises)

    if len(reales) >= MIN_PARA_CONTADORES:
        estado = f"""<dl class="stats">
          <div><dt>profesionales</dt><dd>{len(reales)}</dd></div>
          <div><dt>especialidades</dt><dd>{len({p['categoria'] for p in reales})}</dd></div>
          <div><dt>países</dt><dd>{len({p['pais'] for p in reales})}</dd></div>
        </dl>"""
    else:
        estado = '<p class="launch">El directorio está en lanzamiento y estamos sumando a los primeros profesionales. <a href="/sumate/">Publicar tu ficha es gratis</a>.</p>'

    tarjetas = "\n".join(tarjeta(p) for p in profs)
    descripcion = ("Directorio de profesionales independientes de Latinoamérica: contadores, abogados, arquitectos, "
                   "diseñadores, consultores y más. Revisa su experiencia y contáctalos directo por WhatsApp o email.")
    ld = {
        "@context": "https://schema.org", "@type": "WebSite", "name": MARCA, "url": SITE + "/",
        "description": descripcion,
        "publisher": {"@type": "Organization", "name": "Umarti Digital", "url": "https://umartidigital.com"},
    }
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'

    return head("Directorio de profesionales independientes en Latinoamérica | " + MARCA, descripcion, SITE + "/", extra=extra) + f"""
<main>
  <section class="hero">
    <div class="wrap">
      <h1>Encuentra al profesional que necesitas, y háblale directo</h1>
      <p class="hero__lead">Contadores, abogados, arquitectos, diseñadores, consultores y más profesionales independientes de Latinoamérica. Revisa su experiencia y sus servicios, y contáctalos por WhatsApp o email, sin intermediarios.</p>
      <form class="search" role="search" onsubmit="return false">
        <label class="search__field">
          <span class="sr-only">Buscar</span>
          <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>
          <input type="search" id="q" placeholder="Profesión, servicio o ciudad" autocomplete="off">
        </label>
        <label class="search__country">
          <span class="sr-only">País</span>
          <select id="pais"><option value="">Todos los países</option>{opciones_pais}</select>
        </label>
      </form>
      {estado}
    </div>
  </section>

  <section class="section" id="directorio">
    <div class="wrap">
      <div class="chips" role="group" aria-label="Especialidad">
        {''.join(chips)}
      </div>
      <div class="results__head">
        <h2>Profesionales</h2>
        <p id="contador" aria-live="polite">{len(profs)} profesionales</p>
      </div>
      <div class="grid" id="grid">
{tarjetas}
      </div>
      <p class="empty" id="vacio" hidden>No hay profesionales con esa búsqueda todavía. Prueba con otra palabra, otra especialidad u otro país.</p>
    </div>
  </section>

  <section class="section section--mist" id="como-funciona">
    <div class="wrap how">
      <div>
        <h2>Si buscas un profesional</h2>
        <ol class="steps">
          <li><strong>Busca</strong> por profesión, servicio, ciudad o país.</li>
          <li><strong>Revisa la ficha:</strong> experiencia, servicios y si atiende online o presencial.</li>
          <li><strong>Contáctalo directo</strong> por WhatsApp o email. Sin comisiones ni intermediarios.</li>
        </ol>
      </div>
      <div>
        <h2>Si eres profesional</h2>
        <ol class="steps">
          <li><strong>Completa el formulario</strong> con tu experiencia y tus servicios.</li>
          <li><strong>Revisamos tus datos</strong> y publicamos tu ficha con su propia página.</li>
          <li><strong>Recibe consultas</strong> directo en tu WhatsApp o tu email.</li>
        </ol>
        <a href="/sumate/" class="btn">Suma tu ficha gratis</a>
      </div>
    </div>
  </section>
</main>
{FOOTER}
<script src="/assets/js/directorio.js" defer></script>
</body>
</html>
"""


# ---------- ficha ----------

def ficha(p):
    titulo = f'{p["nombre"]}, {p["profesion"].lower()} en {p["ciudad"]}, {p["pais"]} | {MARCA}'
    descripcion = f'{p["profesion"]} en {p["ciudad"]}, {p["pais"]}. ' + p["bio"][:120].rstrip() + ("…" if len(p["bio"]) > 120 else "")
    url = f'{SITE}/p/{p["slug"]}/'
    servicios = "".join(f"<li>{e(s)}</li>" for s in p["servicios"])

    if p["ejemplo"]:
        aviso = '<div class="sample"><div class="wrap">Esta es una ficha de ejemplo para mostrar cómo se ve el directorio. La persona y sus datos no son reales.</div></div>'
        contacto = '<p class="contact__note">En una ficha real, aquí aparecen los botones de WhatsApp, email, LinkedIn y sitio web del profesional.</p>'
        extra = ""
    else:
        aviso = ""
        botones = []
        if p["wa"]:
            msg = f'Hola {p["nombre"].split()[0]}, te encontré en {MARCA} y quiero hacerte una consulta.'
            botones.append(f'<a class="btn" href="https://wa.me/{p["wa"]}?text={quote(msg)}" rel="nofollow">Escribir por WhatsApp</a>')
        if p["email"]:
            botones.append(f'<a class="btn btn--ghost" href="mailto:{e(p["email"])}?subject={quote("Consulta desde " + MARCA)}">Enviar email</a>')
        if p["linkedin"]:
            botones.append(f'<a class="btn btn--ghost" href="{e(p["linkedin"])}" rel="nofollow noopener" target="_blank">LinkedIn</a>')
        if p["web"]:
            botones.append(f'<a class="btn btn--ghost" href="{e(p["web"])}" rel="nofollow noopener" target="_blank">Sitio web</a>')
        contacto = f'<div class="contact__buttons">{"".join(botones)}</div>'
        ld = {
            "@context": "https://schema.org", "@type": "ProfessionalService",
            "name": f'{p["nombre"]}, {p["profesion"]}', "url": url, "description": p["bio"],
            "areaServed": p["pais"], "address": {"@type": "PostalAddress", "addressLocality": p["ciudad"], "addressCountry": p["pais"]},
            "employee": {"@type": "Person", "name": p["nombre"], "jobTitle": p["profesion"]},
            "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Servicios",
                                "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s}} for s in p["servicios"]]},
        }
        extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'

    anios = f'<div><dt>Experiencia</dt><dd>{e(p["anios"])} años</dd></div>' if p["anios"] else ""
    return head(titulo, descripcion, url, noindex=p["ejemplo"], extra=extra) + f"""
<main>
  {aviso}
  <section class="profile">
    <div class="wrap">
      <nav class="crumbs" aria-label="Ruta"><a href="/">Profesionales</a> <span aria-hidden="true">/</span> <a href="/?cat={quote(p['categoria'])}#directorio">{e(p['categoria'])}</a></nav>
      <div class="profile__head">
        {avatar(p, "avatar avatar--xl")}
        <div>
          <h1>{e(p['nombre'])}</h1>
          <p class="profile__job">{e(p['profesion'])} en {e(p['ciudad'])}, {e(p['pais'])}</p>
        </div>
      </div>
      <div class="profile__grid">
        <div>
          <h2>Sobre mí</h2>
          <p class="profile__bio">{e(p['bio'])}</p>
          <h2>Servicios</h2>
          <ul class="ticks">{servicios}</ul>
        </div>
        <aside class="contact" aria-label="Contacto">
          <dl class="facts">
            <div><dt>Ubicación</dt><dd>{e(p['ciudad'])}, {e(p['pais'])}</dd></div>
            <div><dt>Modalidad</dt><dd>{e(p['modalidad'])}</dd></div>
            {anios}
            <div><dt>Especialidad</dt><dd>{e(p['categoria'])}</dd></div>
          </dl>
          {contacto}
        </aside>
      </div>
    </div>
  </section>
</main>
{FOOTER}
</body>
</html>
"""


# ---------- súmate ----------

def sumate():
    cat = "".join(f"<option>{e(c)}</option>" for c in CATEGORIAS) + "<option>Otra</option>"
    pais = "".join(f"<option>{e(c)}</option>" for c in PAISES) + "<option>Otro</option>"
    mod = "".join(f"<option>{e(c)}</option>" for c in MODALIDADES)
    descripcion = "Publica gratis tu ficha de profesional independiente y recibe consultas directo en tu WhatsApp o tu email."
    return head("Suma tu ficha de profesional | " + MARCA, descripcion, SITE + "/sumate/") + f"""
<main>
  <section class="section join">
    <div class="wrap join__grid">
      <div class="join__intro">
        <h1>Suma tu ficha al directorio</h1>
        <p>Completa tus datos y publicamos tu ficha, con su propia página para que te encuentren en Google. Publicar tu ficha es gratis durante el lanzamiento.</p>
        <ul class="ticks">
          <li>Recibes las consultas directo, sin comisiones.</li>
          <li>Revisamos cada ficha antes de publicarla.</li>
          <li>Puedes pedir cambios o la baja cuando quieras.</li>
        </ul>
      </div>
      <div>
        <div class="notice notice--ok" id="form-ok" role="status" hidden>Recibimos tus datos. Te avisamos por email cuando tu ficha esté publicada.</div>
        <div class="notice notice--error" id="form-error" role="alert" hidden>No se pudieron enviar tus datos. Revisa que los campos obligatorios estén completos e inténtalo de nuevo.</div>
        <form class="form" action="/registro.php" method="post">
          <fieldset>
            <legend>Tus datos</legend>
            <div class="form__row">
              <label>Nombre y apellido<input name="nombre" required maxlength="80" autocomplete="name"></label>
              <label>Profesión<input name="profesion" required maxlength="60" placeholder="Por ejemplo: Contadora pública"></label>
            </div>
            <div class="form__row">
              <label>Especialidad<select name="categoria" required>{cat}</select></label>
              <label>Años de experiencia<input name="anios" type="number" min="0" max="60" inputmode="numeric"></label>
            </div>
            <div class="form__row">
              <label>País<select name="pais" required>{pais}</select></label>
              <label>Ciudad<input name="ciudad" required maxlength="60" autocomplete="address-level2"></label>
            </div>
            <label>Modalidad<select name="modalidad">{mod}</select></label>
          </fieldset>
          <fieldset>
            <legend>Tu trabajo</legend>
            <label><span>Sobre ti <span class="hint">(hasta 400 caracteres)</span></span><textarea name="bio" rows="4" required maxlength="400" placeholder="A quién ayudas y cómo trabajas."></textarea></label>
            <label><span>Servicios <span class="hint">(uno por línea, hasta 5)</span></span><textarea name="servicios" rows="5" required maxlength="500"></textarea></label>
          </fieldset>
          <fieldset>
            <legend>Cómo te contactan</legend>
            <div class="form__row">
              <label><span>WhatsApp <span class="hint">(con código de país)</span></span><input name="whatsapp" type="tel" maxlength="25" placeholder="+52 442 123 4567" autocomplete="tel"></label>
              <label>Email<input name="email" type="email" required maxlength="120" autocomplete="email"></label>
            </div>
            <div class="form__row">
              <label><span>LinkedIn <span class="hint">(opcional)</span></span><input name="linkedin" type="url" maxlength="200" placeholder="https://www.linkedin.com/in/…"></label>
              <label><span>Sitio web <span class="hint">(opcional)</span></span><input name="web" type="url" maxlength="200" placeholder="https://…"></label>
            </div>
          </fieldset>
          <label class="check"><input type="checkbox" name="acepto" value="si" required> <span>Acepto que se publiquen estos datos en mi ficha del directorio.</span></label>
          <label class="hp" aria-hidden="true">No completar<input name="sitio" tabindex="-1" autocomplete="off"></label>
          <button type="submit" class="btn">Enviar mis datos</button>
        </form>
      </div>
    </div>
  </section>
</main>
{FOOTER}
<script>
  (function () {{
    var q = new URLSearchParams(location.search);
    if (q.get('enviado') === '1') document.getElementById('form-ok').hidden = false;
    if (q.get('enviado') === '0') document.getElementById('form-error').hidden = false;
  }})();
</script>
</body>
</html>
"""


def main():
    profs = cargar()
    hoy = date.today().isoformat()

    # limpiar fichas generadas antes
    if (ROOT / "p").exists():
        shutil.rmtree(ROOT / "p")

    (ROOT / "index.html").write_text(inicio(profs), encoding="utf-8")
    (ROOT / "sumate").mkdir(exist_ok=True)
    (ROOT / "sumate" / "index.html").write_text(sumate(), encoding="utf-8")
    for p in profs:
        d = ROOT / "p" / p["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(ficha(p), encoding="utf-8")

    urls = [SITE + "/", SITE + "/sumate/"] + [f'{SITE}/p/{p["slug"]}/' for p in profs if not p["ejemplo"]]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{hoy}</lastmod></url>\n" for u in urls)
        + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

    reales = sum(not p["ejemplo"] for p in profs)
    print(f"Listo: {len(profs)} fichas ({reales} reales, {len(profs) - reales} de ejemplo).")


if __name__ == "__main__":
    main()
