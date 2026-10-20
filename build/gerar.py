# -*- coding: utf-8 -*-
"""
Gerador do portal PASION.

Monta todas as páginas HTML da raiz a partir de um cabeçalho, um rodapé e um
modelo de matéria únicos. Edite os textos aqui ou em build/materias/*.html e
rode, a partir da raiz do projeto:

    python build/gerar.py            # páginas, portal.js, sitemap, feed
    python build/gerar.py --capas    # também redesenha as capas JPG (usa o Chrome)

Fotos das matérias: coloque o original em build/fotos/<slug>.jpg|png|webp (veja
build/fotos/BRIEFING.md). O gerador recorta em 1200x630, comprime o JPG abaixo de
300 KB e cria o WebP em assets/images/fotos/. Sem foto, a matéria usa a arte.
    npx tailwindcss@3.4.17 -c build/tailwind.config.js -i build/tailwind.src.css -o assets/css/tailwind.css --minify

O resultado (HTML estático) é o que vai para o servidor; esta pasta não entra
na imagem Docker.
"""
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ATUAL = ' aria-current="page"'
RAIZ = Path(__file__).resolve().parent.parent
BUILD = RAIZ / 'build'
SITE = 'https://pasionnoticias.proxserverabner.site'
NOME = 'PASION'
EMAIL = 'redaccion@proxserverabner.site'   # e-mail de contato (provisório)
META_PIXEL_ID = '1879343259722567'                      # ID do Pixel da Meta; vazio = desligado
VERSAO = '20261020c'
HOJE = '2026-10-20'

EDITORIAS = {
    'futebol':    {'nome': 'Fútbol',              'ancora': 'futebol'},
    'economia':   {'nome': 'Economía del deporte', 'ancora': 'economia'},
    'consumidor': {'nome': 'Consumidor',          'ancora': 'consumidor'},
}

AUTORES = {
    'Martín Acosta': {
        'id': 'autor-martin-acosta', 'cargo': 'Periodista de economía del deporte',
        'foto': 'assets/images/autor-martin-acosta.svg',
        'bio': 'Economista, cubre las finanzas de los clubes, los patrocinios y el dinero que circula en el fútbol argentino.'},
    'Mariana Benítez': {
        'id': 'autor-mariana-benitez', 'cargo': 'Periodista de tecnología',
        'foto': 'assets/images/autor-mariana-benitez.jpg',
        'bio': 'Periodista, cubre medios de pago, billeteras virtuales, seguridad digital y el funcionamiento de las plataformas.'},
    'Dr. Carlos Ferreyra': {
        'id': 'autor-carlos-ferreyra', 'cargo': 'Editor jefe',
        'foto': 'assets/images/autor-carlos-ferreyra.jpg',
        'bio': 'Abogado, responde por la edición del portal y sigue las leyes y reglas que afectan al deporte y al consumidor.'},
}

# Ordem = ordem de importância na home e na lista de notícias.
# arte: texto curto da capa (linha 1, linha 2).
MATERIAS = [
    dict(slug='noticia-liga-profesional', fonte='liga-profesional', editoria='futebol',
         publicada='2026-10-19T10:00:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Liga Profesional', 'Torneos cortos, tabla anual y descensos')),
    dict(slug='noticia-seleccion-argentina', fonte='seleccion-argentina', editoria='futebol',
         publicada='2026-09-02T16:20:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Selección Argentina', 'Títulos, Eliminatorias y Mundial 2026')),
    dict(slug='noticia-copa-argentina', fonte='copa-argentina', editoria='futebol',
         publicada='2026-10-18T15:30:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Copa Argentina', 'Eliminación directa y cupo a la Libertadores')),
    dict(slug='noticia-libertadores', fonte='libertadores', editoria='futebol',
         publicada='2026-10-20T09:00:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Libertadores', 'Cómo entran los argentinos a la copa')),
    dict(slug='noticia-sponsors-futbol-argentino', fonte='patrocinios', editoria='economia',
         publicada='2026-08-18T10:40:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Sponsors en el fútbol', 'Cómo llegan las marcas a la camiseta')),
    dict(slug='noticia-derechos-de-transmision', fonte='transmision', editoria='economia',
         publicada='2026-09-16T14:00:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Derechos de TV', 'Quién transmite el fútbol argentino')),
    dict(slug='noticia-sad-sociedades-anonimas-deportivas', fonte='sad', editoria='economia',
         publicada='2026-09-08T09:30:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('SAD en Argentina', 'Qué son y en qué estado están')),
    dict(slug='noticia-entradas-derechos-hincha', fonte='entradas', editoria='consumidor',
         publicada='2026-09-25T11:45:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Entradas', 'Arrepentimiento, reembolso y dónde reclamar')),
    dict(slug='noticia-estafas-transferencias', fonte='estafas-transferencias', editoria='consumidor',
         publicada='2026-10-02T10:20:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Estafas con transferencias', 'Qué hacer y dónde reclamar')),
]

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']


def e(texto):
    return html.escape(texto or '', quote=True)


def data_br(iso, hora=True):
    d = datetime.fromisoformat(iso)
    texto = f'{d.day} de {MESES[d.month - 1]} de {d.year}'
    return f'{texto}, {d:%H}:{d:%M} h' if hora else texto


def dominio(url):
    return re.sub(r'^https?://(www\.)?', '', url).split('/')[0]


def data_curta(iso):
    return datetime.fromisoformat(iso).strftime('%d/%m/%Y')


# --------------------------------------------------------------------------
# Leitura das matérias
# --------------------------------------------------------------------------
def ler_materia(m):
    bruto = (BUILD / 'materias' / f"{m['fonte']}.html").read_text(encoding='utf-8')
    meta_txt = re.search(r'<!--\s*META(.*?)-->', bruto, re.S).group(1)
    meta = {}
    for linha in meta_txt.strip().splitlines():
        if ':' in linha:
            k, v = linha.split(':', 1)
            meta[k.strip()] = v.strip()
    m['title'] = meta['title']
    m['description'] = meta['description']
    m['resumo'] = meta.get('card_summary', meta['description'])
    m['autor'] = meta['autor'] if meta['autor'] in AUTORES else next(a for a in AUTORES if meta['autor'] in a or a in meta['autor'])
    m['trilha'] = meta.get('breadcrumb', '')
    m['fontes'] = [f.strip() for f in meta.get('fontes', '').split(';') if f.strip()]
    m['h1'] = html.unescape(re.sub(r'<[^>]+>', '', re.search(r'<h1[^>]*>(.*?)</h1>', bruto, re.S).group(1))).strip()
    m['linha_fina'] = html.unescape(re.sub(r'<[^>]+>', '', re.search(r'<p class="linha-fina">(.*?)</p>', bruto, re.S).group(1))).strip()
    corpo = re.search(r'<div class="corpo">(.*)</div>', bruto, re.S).group(1).strip()
    corpo = re.sub(r'<a ([^>]*href="https?://[^"]*"[^>]*)>', lambda r: '<a ' + (r.group(1) if 'rel=' in r.group(1) else r.group(1) + ' rel="noopener noreferrer"') + '>', corpo)
    m['corpo'] = corpo
    palavras = len(re.sub(r'<[^>]+>', ' ', corpo).split())
    m['leitura'] = max(2, round(palavras / 220))
    m['url'] = f"{m['slug']}.html"
    m['capa'] = f"assets/images/capas/{m['slug']}.jpg"
    m['alt'] = f"Arte de PASION con el texto “{m['arte'][0]}: {m['arte'][1]}”"
    m['capa_web'] = m['capa']
    m['credito'] = 'Arte: PASION'
    foto = preparar_foto(m['slug'])
    if foto:
        m['capa'], m['capa_web'] = foto
        m['alt'] = IMAGENS.get(m['slug'], {}).get('alt') or m['alt']
        m['credito'] = 'Imagen ilustrativa generada con inteligencia artificial'
    return m


IMAGENS = json.loads((BUILD / 'imagens.json').read_text(encoding='utf-8')) if (BUILD / 'imagens.json').exists() else {}


def preparar_foto(slug):
    """Converte build/fotos/<slug>.* em JPG 1200x630 (< 300 KB) e WebP. Devolve (jpg, webp) ou None."""
    origem = next((f for f in sorted((BUILD / 'fotos').glob(f'{slug}.*')) if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')), None)
    if not origem:
        return None
    jpg = RAIZ / 'assets/images/fotos' / f'{slug}.jpg'
    webp = jpg.with_suffix('.webp')
    if not (jpg.exists() and webp.exists() and jpg.stat().st_mtime >= origem.stat().st_mtime):
        from PIL import Image
        img = Image.open(origem).convert('RGB')
        alvo = 1200 / 630
        if img.width / img.height > alvo:
            novo_w = round(img.height * alvo)
            x = (img.width - novo_w) // 2
            img = img.crop((x, 0, x + novo_w, img.height))
        else:
            novo_h = round(img.width / alvo)
            y = (img.height - novo_h) // 2
            img = img.crop((0, y, img.width, y + novo_h))
        img = img.resize((1200, 630), Image.LANCZOS)
        jpg.parent.mkdir(parents=True, exist_ok=True)
        for qualidade in (85, 80, 75, 70, 65, 60):
            img.save(jpg, 'JPEG', quality=qualidade, optimize=True, progressive=True)
            if jpg.stat().st_size < 300 * 1024:
                break
        img.save(webp, 'WEBP', quality=80, method=6)
        print('  foto:', jpg.relative_to(RAIZ), f'{jpg.stat().st_size // 1024} KB /', f'{webp.stat().st_size // 1024} KB webp')
    return (f'assets/images/fotos/{slug}.jpg', f'assets/images/fotos/{slug}.webp')


# --------------------------------------------------------------------------
# Peças comuns
# --------------------------------------------------------------------------
ESCUDO = ('<svg viewBox="0 0 80 100" width="26" height="32" aria-hidden="true" focusable="false">'
          '<path d="M40 4 76 16v36c0 26-20 38-36 44C24 90 4 78 4 52V16Z" fill="#0F766E"/>'
          '<path d="m23 50 12 12 22-26" stroke="#fff" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')

LUPA = ('<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" '
        'stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>')


def logo(claro=False):
    cor = 'text-white' if claro else 'text-slate-900'
    destaque = 'text-teal-300' if claro else 'text-teal-700'
    return (f'{ESCUDO}<span class="text-xl font-black tracking-[.04em] {cor}">'
            f'<span class="{destaque}">PASION</span></span>')


def form_busca(sufixo, classes):
    return f'''<form data-busca-form role="search" action="noticias.html" method="get" class="relative {classes}">
        <label for="busca-{sufixo}" class="sr-only">Buscar noticias</label>
        <input id="busca-{sufixo}" type="search" name="q" placeholder="Buscar noticias" autocomplete="off" role="combobox" aria-autocomplete="list" aria-controls="busca-{sufixo}-lista" aria-expanded="false" class="w-full h-11 rounded-full border border-slate-300 bg-slate-50 pl-4 pr-12 text-base text-slate-900 placeholder:text-slate-500 focus:bg-white">
        <button type="submit" class="touch-target absolute right-0 top-0 text-slate-600 hover:text-teal-700" aria-label="Buscar">{LUPA}</button>
        <div id="busca-{sufixo}-lista" class="busca-resultados" hidden></div>
      </form>'''


def cabecalho(ativo):
    itens = [('inicio', './', 'Inicio'),
             ('futebol', './#futebol', 'Fútbol'),
             ('economia', './#economia', 'Economía del deporte'),
             ('consumidor', './#consumidor', 'Consumidor'),
             ('noticias', 'noticias.html', 'Todas las noticias')]
    nav = '\n'.join(
        f'<li><a href="{href}" class="inline-flex h-11 items-center px-3 text-sm font-semibold whitespace-nowrap text-slate-700 hover:text-teal-700"'
        f'{ATUAL if chave == ativo else ""}>{rotulo}</a></li>'
        for chave, href, rotulo in itens)
    return f'''<a href="#conteudo" class="skip-link">Ir al contenido</a>
  <header class="site-header sticky top-0 z-50 bg-white border-b border-slate-200">
    <div class="masthead">
    <div class="masthead-inner max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">
      <a href="./" class="flex items-center gap-2 shrink-0" aria-label="PASION, página de inicio">{logo(claro=ativo == 'inicio')}</a>
      <time id="headerLiveDate" class="hidden lg:block text-sm text-slate-600"></time>
      {form_busca('topo', 'hidden md:block ml-auto w-72')}
      <button id="buscaToggle" type="button" class="inline-flex items-center justify-center min-w-[44px] min-h-[44px] md:hidden ml-auto text-slate-700" aria-expanded="false" aria-controls="buscaPainel" aria-label="Abrir búsqueda">{LUPA}</button>
      <a href="anuncia.html" class="hidden sm:inline-flex h-11 items-center px-4 rounded-full border border-slate-300 text-sm font-semibold text-slate-700 hover:border-teal-700 hover:text-teal-700">Anunciá</a>
    </div>
    </div>
    <div id="buscaPainel" class="md:hidden border-t border-slate-200 px-4 py-3" hidden>
      {form_busca('celular', 'w-full')}
    </div>
    <nav aria-label="Secciones" class="border-t border-slate-200">
      <ul class="nav-editorias max-w-6xl mx-auto px-2 flex overflow-x-auto">
        {nav}
      </ul>
    </nav>
  </header>'''


def rodape():
    return f'''<footer class="bg-slate-900 text-slate-300 mt-16">
    <div class="max-w-6xl mx-auto px-4 py-12 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
      <div>
        <a href="./" class="flex items-center gap-2" aria-label="PASION, página de inicio">{logo(claro=True)}</a>
        <p class="mt-4 text-sm leading-relaxed">Noticias de fútbol, economía del deporte y derechos del consumidor, con fuente en cada dato.</p>
      </div>
      <div>
        <h2 class="text-sm font-bold uppercase tracking-wide text-white">Secciones</h2>
        <ul class="mt-3 space-y-1 text-sm">
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#futebol">Fútbol</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#economia">Economía del deporte</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#consumidor">Consumidor</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="noticias.html">Todas las noticias</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="feed.xml">Feed RSS</a></li>
        </ul>
      </div>
      <div>
        <h2 class="text-sm font-bold uppercase tracking-wide text-white">Institucional</h2>
        <ul class="mt-3 space-y-1 text-sm">
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="quienes-somos.html">Quiénes somos y equipo editorial</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="quienes-somos.html#politica-editorial">Política editorial</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="contacto.html">Contacto</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="anuncia.html">Anunciá</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="politica-de-privacidad.html">Privacidad</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="terminos-de-uso.html">Términos de uso</a></li>
          <li><button type="button" data-abrir-cookies class="py-1.5 text-left hover:text-white hover:underline">Preferencias de cookies</button></li>
        </ul>
      </div>
      <div>
        <h2 class="text-sm font-bold uppercase tracking-wide text-white">Secciones</h2>
        <ul class="mt-3 space-y-1 text-sm">
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#futebol">Fútbol</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#economia">Economía del deporte</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#consumidor">Consumidor</a></li>
        </ul>
      </div>
    </div>
    <div class="border-t border-slate-700">
      <p class="max-w-6xl mx-auto px-4 py-5 text-sm text-slate-400">© 2026 PASION. Contenido periodístico.</p>
    </div>
  </footer>

  <div id="cookieConsentBanner" role="region" aria-label="Preferencias de cookies" hidden>
    <div class="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center gap-3">
      <p class="flex-1 text-sm leading-relaxed">Usamos cookies de medición de audiencia y de anuncios solo si aceptás. Rechazar no cambia nada de lo que leés. <a href="politica-de-privacidad.html#cookies">Más información</a></p>
      <div class="flex gap-2">
        <button type="button" data-cookie="recusar" class="flex-1 md:flex-none h-11 px-6 rounded-full border-2 border-white text-sm font-bold hover:bg-white hover:text-slate-900">Rechazar</button>
        <button type="button" data-cookie="aceitar" class="flex-1 md:flex-none h-11 px-6 rounded-full border-2 border-white text-sm font-bold hover:bg-white hover:text-slate-900">Aceptar</button>
      </div>
    </div>
  </div>
  <script src="assets/js/portal.js?v={VERSAO}" defer></script>'''


ORG_ID = f'{SITE}/#organizacao'


def jsonld_org():
    return {
        '@type': 'NewsMediaOrganization', '@id': ORG_ID, 'name': NOME, 'url': f'{SITE}/',
        'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/images/logo-512.png', 'width': 512, 'height': 512},
        'email': EMAIL,
        'publishingPrinciples': f'{SITE}/quienes-somos.html#politica-editorial',
        'correctionsPolicy': f'{SITE}/quienes-somos.html#correcciones',
        'masthead': f'{SITE}/quienes-somos.html#equipo',
        'actionableFeedbackPolicy': f'{SITE}/contacto.html',
        'inLanguage': 'es-AR',
        'areaServed': {'@type': 'Country', 'name': 'Argentina'},
        'address': {'@type': 'PostalAddress', 'addressCountry': 'AR'},
    }


def pagina(arquivo, titulo, descricao, corpo, ativo='', og_tipo='website', imagem=None, imagem_alt=None,
           extra_head='', grafo=None, robots='index, follow, max-image-preview:large'):
    url = f'{SITE}/' if arquivo == 'index.html' else f'{SITE}/{arquivo}'
    imagem = imagem or 'assets/images/og-pasion.jpg'
    imagem_alt = imagem_alt or 'PASION: fútbol, economía del deporte y derechos del consumidor'
    grafo = [jsonld_org()] + (grafo or [])
    ld = json.dumps({'@context': 'https://schema.org', '@graph': grafo}, ensure_ascii=False, indent=1)
    if arquivo == 'index.html':
        classe_body = 'antialiased home-page'
    elif og_tipo == 'article':
        classe_body = 'antialiased news-page'
    else:
        classe_body = 'antialiased'
    doc = f'''<!DOCTYPE html>
<html lang="es-AR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(titulo)}</title>
  <meta name="description" content="{e(descricao)}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{url}">
  <link rel="alternate" hreflang="es-AR" href="{url}">
  <link rel="alternate" hreflang="x-default" href="{url}">
  <meta name="geo.region" content="AR">
  <meta name="geo.placename" content="Argentina">
  <meta name="theme-color" content="#0B132B">
  <link rel="icon" href="assets/images/favicon.svg" type="image/svg+xml">
  <link rel="alternate" type="application/rss+xml" title="PASION: últimas noticias" href="{SITE}/feed.xml">

  <meta property="og:site_name" content="{NOME}">
  <meta property="og:locale" content="es_AR">
  <meta property="og:type" content="{og_tipo}">
  <meta property="og:title" content="{e(titulo.replace(' | PASION', ''))}">
  <meta property="og:description" content="{e(descricao)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE}/{imagem}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{e(imagem_alt)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{e(titulo.replace(' | PASION', ''))}">
  <meta name="twitter:description" content="{e(descricao)}">
  <meta name="twitter:image" content="{SITE}/{imagem}">
{extra_head}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400..900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/tailwind.css?v={VERSAO}">
  <link rel="stylesheet" href="assets/css/portal.css?v={VERSAO}">
  <script type="application/ld+json">
{ld}
  </script>
</head>
<body class="{classe_body}">
  {cabecalho(ativo)}

{corpo}

  {rodape()}
</body>
</html>
'''
    (RAIZ / arquivo).write_text(doc, encoding='utf-8', newline='\n')


def chapeu(ed, link=True):
    nome = EDITORIAS[ed]['nome']
    if link:
        return f'<a href="./#{EDITORIAS[ed]["ancora"]}" class="chapeu-badge chapeu-{ed} relative z-10">{nome}</a>'
    return f'<span class="chapeu-badge chapeu-{ed}">{nome}</span>'


def publicidade(slot, formato='retangulo'):
    """Espaço publicitário sempre rotulado. Usa o criativo de assets/images/anuncios/ se existir."""
    img = RAIZ / 'assets' / 'images' / 'anuncios' / f'{formato}.webp'
    if img.exists():
        w, h = {'retangulo': (300, 250), 'faixa': (728, 90)}[formato]
        miolo = (f'<a href="anuncia.html" data-slot="{slot}" class="block">'
                 f'<img src="assets/images/anuncios/{formato}.webp" width="{w}" height="{h}" loading="lazy" '
                 f'alt="Anunciá en PASION: hablá con nuestro equipo comercial" class="w-full h-auto"></a>')
    else:
        miolo = (f'<a href="anuncia.html" data-slot="{slot}" class="article-ad-creative">'
                 f'<span class="article-ad-brand">{logo(claro=True)}</span>'
                 f'<span class="article-ad-title">Tu marca <strong>acá</strong></span>'
                 f'<span class="article-ad-copy">Hablá con el equipo comercial de PASION.</span>'
                 f'<span class="article-ad-cta">Anunciá acá <span aria-hidden="true">→</span></span></a>')
    return f'<aside class="ad-slot" aria-label="Publicidad"><span class="ad-label">Publicidad</span>{miolo}</aside>'


def billboard(slot):
    """Carrossel de três criativos de demonstração, com altura reservada e controles acessíveis."""
    anuncios = [
        (f'<a href="anuncia.html" data-slot="{slot}" class="billboard-slide billboard-first" aria-label="Publicidad Passo Nobre: tu próximo paso empieza acá">'
         f'<picture><source media="(max-width: 767px)" srcset="assets/images/home/anuncio-passo-nobre-mobile.jpg">'
         f'<img src="assets/images/home/anuncio-passo-nobre-01.jpg" width="1072" height="176" '
         f'alt="Passo Nobre — tu próximo paso empieza acá. Comodidad, estilo y rendimiento para tu día, dentro y fuera de la cancha. Conocé la colección." class="billboard-img"></picture>'
         f'<span class="billboard-copy billboard-mobile-copy"><span class="billboard-brand">PASSO NOBRE</span>'
         f'<strong>Tu próximo paso<br>empieza acá.</strong>'
         f'<span class="billboard-caption">Comodidad, estilo y rendimiento.</span>'
         f'<span class="billboard-cta">Conocé la colección <span aria-hidden="true">→</span></span></span>'
         f'<img src="assets/images/home/produto-tenis.webp" width="560" height="330" alt="" class="billboard-mobile-product"></a>'),
        (f'<a href="anuncia.html" data-slot="{slot}" class="billboard-slide billboard-slide--produto billboard-slide--ritmo" aria-label="Publicidad Passo Nobre: comodidad que acompaña tu ritmo" hidden>'
         f'<span class="billboard-copy"><span class="billboard-brand">PASSO NOBRE</span>'
         f'<strong>Comodidad que acompaña<br>tu ritmo.</strong>'
         f'<span class="billboard-caption">Movimiento con propósito, en cada paso.</span></span>'
         f'<img src="assets/images/home/produto-tenis.webp" width="560" height="330" alt="Zapatilla deportiva destacada" class="billboard-product">'
         f'<span class="billboard-cta">Conocé la colección <span aria-hidden="true">→</span></span></a>'),
        (f'<a href="anuncia.html" data-slot="{slot}" class="billboard-slide billboard-slide--produto billboard-slide--jogo" aria-label="Publicidad Passo Nobre: hecho para acompañar el juego" hidden>'
         f'<span class="billboard-copy"><span class="billboard-brand">PASSO NOBRE</span>'
         f'<strong>Tu juego empieza<br>en cada paso.</strong>'
         f'<span class="billboard-caption">Ligereza y estilo dentro y fuera de la cancha.</span></span>'
         f'<img src="assets/images/home/produto-tenis.webp" width="560" height="330" alt="Zapatilla deportiva destacada" class="billboard-product">'
         f'<span class="billboard-cta">Mirá la colección <span aria-hidden="true">→</span></span></a>'),
    ]
    slides = '\n'.join(anuncios)
    controles = ''.join(
        f'<button type="button" class="billboard-dot" data-ad-goto="{i}" aria-label="Mostrar anuncio {i + 1} de 3" aria-pressed="{"true" if i == 0 else "false"}"></button>'
        for i in range(3))
    return (f'<aside class="billboard" aria-label="Publicidad"><span class="billboard-label">Publicidad</span>'
            f'<div class="billboard-area" data-ad-carousel aria-roledescription="carrossel">{slides}'
            f'<div class="billboard-controls" aria-label="Controles de los anuncios">'
            f'<button type="button" class="billboard-nav" data-ad-prev aria-label="Anuncio anterior">‹</button>'
            f'<div class="billboard-dots">{controles}</div>'
            f'<button type="button" class="billboard-nav" data-ad-next aria-label="Anuncio siguiente">›</button>'
            f'<button type="button" class="billboard-toggle" data-ad-toggle aria-pressed="false" aria-label="Pausar anuncios">Ⅱ</button>'
            f'</div></div></aside>')


def cartao(m, tamanho='medio', carregar='lazy', capa=None, classe=''):
    tit = {'grande': 'text-2xl md:text-4xl', 'medio': 'text-lg md:text-xl', 'pequeno': 'text-base'}[tamanho]
    resumo = '' if tamanho == 'pequeno' else f'<p class="mt-2 text-base text-slate-600 leading-relaxed">{e(m["resumo"])}</p>'
    prioridade = ' fetchpriority="high"' if carregar == 'eager' else ''
    capa = capa or m['capa_web']
    return f'''<article class="card-link group {classe}">
          <div class="overflow-hidden rounded-lg bg-slate-200">
            <img src="{capa}" width="1200" height="630" alt="" loading="{carregar}"{prioridade} class="w-full h-auto aspect-[1200/630] object-cover">
          </div>
          <div class="mt-3">{chapeu(m['editoria'])}</div>
          <h3 class="headline {tit} mt-2"><a href="{m['url']}" class="stretched">{e(m['h1'])}</a></h3>
          {resumo}
          <p class="mt-2 text-sm text-slate-600"><time datetime="{m['publicada']}">{data_curta(m['publicada'])}</time>{' · actualizada' if m['atualizada'] else ''}</p>
        </article>'''


def item_lista(m):
    return f'''<li class="card-link py-4 border-b border-slate-200 flex gap-4">
            <img src="{m['capa_web']}" width="120" height="63" alt="" loading="lazy" class="w-24 sm:w-32 h-auto aspect-[1200/630] object-cover rounded shrink-0">
            <div>
              <span class="text-xs font-bold uppercase tracking-wide text-teal-700">{EDITORIAS[m['editoria']]['nome']}</span>
              <a href="{m['url']}" class="stretched block headline text-base sm:text-lg mt-1">{e(m['h1'])}</a>
              <p class="mt-1 text-sm text-slate-600"><time datetime="{m['publicada']}">{data_curta(m['publicada'])}</time></p>
            </div>
          </li>'''


def item_lateral(m):
    return f'''<li class="article-more-item">
            <img src="{m['capa_web']}" width="120" height="120" alt="" loading="lazy">
            <div class="article-more-copy">
              <span class="article-more-category">{EDITORIAS[m['editoria']]['nome']}</span>
              <a href="{m['url']}" class="stretched">{e(m['h1'])}</a>
              <time datetime="{m['publicada']}">{data_curta(m['publicada'])}</time>
            </div>
          </li>'''


# --------------------------------------------------------------------------
# Matéria
# --------------------------------------------------------------------------
def gerar_materia(m, todas):
    autor = AUTORES[m['autor']]
    ed = EDITORIAS[m['editoria']]
    url_abs = f"{SITE}/{m['url']}"
    atual = (f' · Actualizada el <time datetime="{m["atualizada"]}">{data_br(m["atualizada"])}</time>'
             if m['atualizada'] else '')
    nota = (f'<p class="mt-8 rounded-lg border border-amber-300 bg-amber-50 p-4 text-base text-amber-900">'
            f'<strong>Nota de la redacción.</strong> {e(m["nota"])}</p>') if m['nota'] else ''
    fontes = ''
    if m['fontes']:
        lis = '\n'.join(f'<li><a href="{e(f)}" rel="noopener noreferrer">{e(dominio(f))}</a></li>' for f in m['fontes'])
        fontes = f'<section class="mt-10" aria-labelledby="fuentes-titulo"><h2 id="fuentes-titulo" class="text-lg font-extrabold text-slate-900">Fuentes consultadas</h2><ul class="mt-3 list-disc pl-6 text-base text-slate-700 space-y-1">{lis}</ul></section>'
    mesmas = [o for o in todas if o is not m and o['editoria'] == m['editoria']]
    outras = [o for o in todas if o is not m and o['editoria'] != m['editoria']]
    relacionadas = (mesmas + outras)[:3]
    leia = '\n'.join(cartao(o, 'pequeno') for o in relacionadas)
    mais = '\n'.join(item_lateral(o) for o in [o for o in todas if o is not m][:5])
    whats = 'https://wa.me/?text=' + quote(f"{m['h1']} {url_abs}")

    corpo = f'''  <main id="conteudo" class="article-shell max-w-6xl mx-auto px-4 py-6 lg:py-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_300px]">
    <article class="news-story min-w-0">
      <nav aria-label="Ruta de navegación" class="text-sm text-slate-600">
        <ol class="flex flex-wrap items-center gap-x-2 gap-y-1">
          <li><a href="./" class="underline hover:text-teal-700">Inicio</a></li>
          <li aria-hidden="true">›</li>
          <li><a href="./#{ed['ancora']}" class="underline hover:text-teal-700">{ed['nome']}</a></li>
          <li aria-hidden="true">›</li>
          <li aria-current="page">{e(m['trilha'] or m['h1'])}</li>
        </ol>
      </nav>

      <header class="story-heading mt-6">
        {chapeu(m['editoria'])}
        <h1 class="headline text-3xl sm:text-4xl lg:text-5xl mt-3">{e(m['h1'])}</h1>
        <p class="mt-4 text-lg sm:text-xl text-slate-600 leading-relaxed">{e(m['linha_fina'])}</p>
        <div class="story-byline mt-6 pb-6 border-b border-slate-200 flex items-center gap-3">
          <img src="{autor['foto']}" width="48" height="48" alt="" class="w-12 h-12 rounded-full object-cover bg-slate-200">
          <div class="text-sm leading-relaxed">
            <p>Por <a href="quienes-somos.html#{autor['id']}" class="font-semibold text-slate-900 underline hover:text-teal-700">{e(m['autor'])}</a>, {autor['cargo'].lower()}</p>
            <p class="text-slate-600">Publicada el <time datetime="{m['publicada']}">{data_br(m['publicada'])}</time>{atual} · Lectura de {m['leitura']} min</p>
          </div>
        </div>
      </header>

      <figure class="story-hero mt-6">
        <img src="{m['capa_web']}" width="1200" height="630" alt="{e(m['alt'])}" fetchpriority="high" class="w-full h-auto rounded-lg">
        <span class="story-art-brand" aria-label="PASION">PASION</span>
        <figcaption class="mt-2 text-sm text-slate-600">{m['credito']}</figcaption>
      </figure>

      {nota}

      <div class="article-body mt-8">
{m['corpo']}
      </div>

      {fontes}

      

      <div class="mt-10 flex flex-wrap items-center gap-3">
        <span class="text-sm font-bold text-slate-900">Compartí:</span>
        <a href="{whats}" rel="noopener noreferrer" class="inline-flex h-11 items-center px-4 rounded-full bg-emerald-700 text-white text-sm font-semibold hover:bg-emerald-800">WhatsApp</a>
        <button type="button" data-copiar-link="{url_abs}" aria-describedby="status-copiar" class="h-11 px-4 rounded-full border border-slate-300 text-sm font-semibold text-slate-700 hover:border-teal-700 hover:text-teal-700">Copiar enlace</button>
        <span id="status-copiar" class="text-sm text-slate-600" aria-live="polite"></span>
      </div>

      <p class="mt-6 text-sm text-slate-600">¿Viste un error en esta nota? <a href="contacto.html" class="underline hover:text-teal-700">Avisale a la redacción</a>. Lo corregimos y registramos la corrección acá.</p>

      <section class="mt-12 pt-8 border-t border-slate-200" aria-labelledby="leia-tambem">
        <h2 id="leia-tambem" class="text-xl font-extrabold text-slate-900">Leé también</h2>
        <div class="mt-5 grid gap-6 sm:grid-cols-3">
{leia}
        </div>
      </section>
    </article>

    <div class="article-sidebar space-y-8">
      {publicidade('materia-lateral')}
      <section aria-labelledby="mais-noticias">
        <h2 id="mais-noticias" class="text-lg font-extrabold text-slate-900 border-b-2 border-slate-900 pb-2">Más noticias <a href="noticias.html" class="article-more-all">Ver todas <span aria-hidden="true">→</span></a></h2>
        <ul>
{mais}
        </ul>
      </section>
    </div>
  </main>'''

    grafo = [
        {'@type': 'Person', '@id': f"{SITE}/quienes-somos.html#{autor['id']}", 'name': m['autor'],
         'jobTitle': autor['cargo'], 'url': f"{SITE}/quienes-somos.html#{autor['id']}", 'worksFor': {'@id': ORG_ID}},
        {'@type': 'NewsArticle', '@id': f'{url_abs}#materia', 'mainEntityOfPage': url_abs,
         'headline': m['h1'], 'description': m['description'],
         'image': [{'@type': 'ImageObject', 'url': f"{SITE}/{m['capa']}", 'width': 1200, 'height': 630}],
         'datePublished': m['publicada'], 'dateModified': m['atualizada'] or m['publicada'],
         'author': {'@id': f"{SITE}/quienes-somos.html#{autor['id']}"}, 'publisher': {'@id': ORG_ID},
         'articleSection': ed['nome'], 'inLanguage': 'es-AR', 'isAccessibleForFree': True,
         'wordCount': len(re.sub(r'<[^>]+>', ' ', m['corpo']).split())},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Inicio', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': ed['nome'], 'item': f"{SITE}/#{ed['ancora']}"},
            {'@type': 'ListItem', 'position': 3, 'name': m['trilha'] or m['h1']}]},
    ]
    extra = '\n'.join([
        f'  <meta property="article:published_time" content="{m["publicada"]}">',
        f'  <meta property="article:modified_time" content="{m["atualizada"] or m["publicada"]}">',
        f'  <meta property="article:section" content="{ed["nome"]}">',
        f'  <meta property="article:author" content="{SITE}/quienes-somos.html#{autor["id"]}">',
        f'  <meta property="article:publisher" content="{SITE}/">',
        f'  <meta name="author" content="{e(m["autor"])}">',
    ])
    pagina(m['url'], m['title'], m['description'], corpo, ativo=m['editoria'], og_tipo='article',
           imagem=m['capa'], imagem_alt=m['alt'], extra_head=extra, grafo=grafo)


# --------------------------------------------------------------------------
# Home e lista de notícias
# --------------------------------------------------------------------------
def gerar_home(ms):
    destaque, d2, d3 = ms[0], ms[1], ms[2]
    destaque['home_capa'] = 'assets/images/home/capa-liga-profesional.jpg'
    d2['home_capa'] = 'assets/images/home/capa-seleccion.jpg'
    d3['home_capa'] = 'assets/images/home/capa-copa-argentina.jpg'
    secoes = ''
    for chave, ed in EDITORIAS.items():
        da_secao = [m for m in ms if m['editoria'] == chave and m not in (destaque, d2, d3)]
        if not da_secao:
            da_secao = [m for m in ms if m['editoria'] == chave]
        cards = '\n'.join(cartao(m) for m in da_secao)
        secoes += f'''
      <section id="{ed['ancora']}" aria-labelledby="titulo-{chave}" class="pt-10">
        <h2 id="titulo-{chave}" class="text-2xl font-black text-slate-900 border-b-2 border-slate-900 pb-2">{ed['nome']}</h2>
        <div class="mt-6 grid gap-8 sm:grid-cols-2">
{cards}
        </div>
      </section>'''
    escolhas = '\n'.join(item_lista(m) for m in ms[3:7])
    primeiro = ms[0]
    corpo = f'''  <div class="ticker-container">
    <div class="max-w-6xl mx-auto px-4 h-12 flex items-center gap-3">
      <span class="ticker-badge px-2 py-1 rounded shrink-0">Destacadas</span>
      <a id="tickerText" href="{primeiro['url']}" class="flex-1 min-w-0 truncate text-sm font-semibold hover:underline">{e(primeiro['h1'])}</a>
      <button id="tickerPausa" type="button" class="touch-target shrink-0 text-white" aria-pressed="false" aria-label="Pausar el cambio de destacadas"><span data-icone aria-hidden="true">❚❚</span></button>
    </div>
  </div>

  <main id="conteudo" class="home-main max-w-6xl mx-auto px-4 py-6">
    <h1 class="sr-only">PASION: noticias de fútbol, economía del deporte y derechos del consumidor</h1>
    {billboard('home-topo')}

    <section aria-label="Titulares" class="home-headlines">
      {cartao(destaque, 'grande', 'eager', destaque['home_capa'], 'home-feature')}
      <div class="home-secondary">
        {cartao(d2, 'pequeno', capa=d2['home_capa'], classe='home-side-card')}
        {cartao(d3, 'pequeno', capa=d3['home_capa'], classe='home-side-card')}
      </div>
    </section>

    <div class="mt-4 grid gap-10 lg:grid-cols-[minmax(0,1fr)_300px]">
      <div class="min-w-0">
{secoes}
      </div>

      <div class="space-y-8 pt-10">
        <section aria-labelledby="escolhas">
          <h2 id="escolhas" class="text-lg font-extrabold text-slate-900 border-b-2 border-slate-900 pb-2">Selección de la redacción</h2>
          <ul>
{escolhas}
          </ul>
          <a href="noticias.html" class="mt-4 inline-flex h-11 items-center text-sm font-bold text-teal-700 underline">Ver todas las noticias</a>
        </section>
        <section aria-labelledby="habla-redaccion" class="rounded-lg bg-slate-900 p-5 text-slate-200">
          <h2 id="habla-redaccion" class="text-lg font-extrabold text-white">¿Tenés un tema para proponer o viste un error?</h2>
          <p class="mt-2 text-base leading-relaxed">Escribile a la redacción. Leemos todos los mensajes y corregimos lo que esté mal.</p>
          <a href="contacto.html" class="mt-4 inline-flex h-11 items-center px-5 rounded-full bg-white text-sm font-bold text-slate-900 hover:bg-teal-50">Hablá con la redacción</a>
        </section>
      </div>
    </div>
  </main>'''
    grafo = [{'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': f'{SITE}/', 'name': NOME, 'inLanguage': 'es-AR',
              'publisher': {'@id': ORG_ID},
              'potentialAction': {'@type': 'SearchAction', 'target': f'{SITE}/noticias.html?q={{search_term_string}}',
                                  'query-input': 'required name=search_term_string'}}]
    pagina('index.html', 'PASION: fútbol, economía del deporte y consumidor',
           'Portal de noticias sobre fútbol, economía del deporte y derechos del consumidor. Notas con fuente, '
           'lenguaje claro y correcciones transparentes.', corpo, ativo='inicio', grafo=grafo)


def gerar_noticias(ms):
    por_data = sorted(ms, key=lambda m: m['publicada'], reverse=True)
    itens = '\n'.join(f'''<li data-materia class="card-link py-5 border-b border-slate-200 flex gap-4">
            <img src="{m['capa_web']}" width="160" height="84" alt="" loading="lazy" class="w-28 sm:w-40 h-auto aspect-[1200/630] object-cover rounded shrink-0">
            <div class="min-w-0">
              <span class="text-xs font-bold uppercase tracking-wide text-teal-700">{EDITORIAS[m['editoria']]['nome']}</span>
              <h2 class="headline text-lg sm:text-xl mt-1"><a href="{m['url']}" class="stretched">{e(m['h1'])}</a></h2>
              <p class="mt-1 text-base text-slate-600 hidden sm:block">{e(m['resumo'])}</p>
              <p class="mt-1 text-sm text-slate-600"><time datetime="{m['publicada']}">{data_br(m['publicada'], hora=False)}</time> · {e(m['autor'])}</p>
            </div>
          </li>''' for m in por_data)
    corpo = f'''  <main id="conteudo" class="max-w-3xl mx-auto px-4 py-10">
    <h1 class="headline text-3xl sm:text-4xl">Todas las noticias</h1>
    <p class="mt-3 text-lg text-slate-600">Las notas más recientes primero. Buscá por un tema, un equipo o una palabra.</p>
    <form action="noticias.html" method="get" role="search" class="mt-6" onsubmit="return false">
      <label for="buscaPagina" class="block text-sm font-bold text-slate-900">Buscar en las noticias</label>
      <input id="buscaPagina" type="search" name="q" autocomplete="off" class="mt-2 w-full h-12 rounded-lg border border-slate-300 px-4 text-base" placeholder="Ej.: Liga Profesional, estafas, sponsors">
    </form>
    <p id="buscaStatus" class="mt-4 text-sm text-slate-600" role="status">{len(ms)} notas publicadas.</p>
    <ul class="mt-2">
{itens}
    </ul>
  </main>'''
    grafo = [{'@type': 'CollectionPage', 'url': f'{SITE}/noticias.html', 'name': 'Todas las noticias', 'isPartOf': {'@id': f'{SITE}/#site'},
              'mainEntity': {'@type': 'ItemList', 'itemListElement': [
                  {'@type': 'ListItem', 'position': i + 1, 'url': f"{SITE}/{m['url']}"} for i, m in enumerate(por_data)]}}]
    pagina('noticias.html', 'Todas las noticias | PASION',
           'Lista completa de las notas de PASION sobre fútbol, economía del deporte y derechos del consumidor, '
           'de la más reciente a la más antigua.', corpo, ativo='noticias', grafo=grafo)


# --------------------------------------------------------------------------
# Páginas institucionais
# --------------------------------------------------------------------------
def institucional(arquivo, titulo, descricao, h1, conteudo, ativo='', chapeu_txt=''):
    ch = f'<p class="text-sm font-bold uppercase tracking-wide text-teal-700">{chapeu_txt}</p>' if chapeu_txt else ''
    corpo = f'''  <main id="conteudo" class="max-w-3xl mx-auto px-4 py-10">
    {ch}
    <h1 class="headline text-3xl sm:text-4xl mt-2">{h1}</h1>
    <div class="prose-institucional mt-6">
{conteudo}
    </div>
  </main>'''
    pagina(arquivo, titulo, descricao, corpo, ativo=ativo)


def gerar_institucionais():
    autores = '\n'.join(f'''<div id="{a['id']}" class="flex gap-4 rounded-lg border border-slate-200 bg-white p-5 scroll-mt-32">
          <img src="{a['foto']}" width="64" height="64" alt="" class="w-16 h-16 rounded-full object-cover bg-slate-200 shrink-0">
          <div><h3 class="text-lg font-extrabold text-slate-900">{e(nome)}</h3><p class="text-sm font-semibold text-teal-700">{a['cargo']}</p><p class="mt-1 text-base">{a['bio']}</p></div>
        </div>''' for nome, a in AUTORES.items())

    institucional('quienes-somos.html', 'Quiénes somos, equipo y política editorial | PASION',
        'Conocé PASION: qué cubrimos, quién escribe, cómo chequeamos la información, cómo corregimos errores '
        'y cómo separamos la publicidad del periodismo.',
        'Quiénes somos', f'''
      <p class="text-lg">PASION es un portal de noticias sobre fútbol, economía del deporte y derechos del consumidor. Explicamos reglas, contratos y cambios en la ley que afectan a quienes siguen el deporte, con fuente en cada dato.</p>

      <h2 id="que-cubrimos">Qué cubrimos</h2>
      <ul>
        <li><strong>Fútbol:</strong> competencias, reglamentos y selecciones.</li>
        <li><strong>Economía del deporte:</strong> patrocinios, ingresos de los clubes, tributos y trabajo en el sector.</li>
        <li><strong>Consumidor:</strong> pagos, estafas, derechos y qué cambia cuando cambia la ley.</li>
      </ul>

      <h2 id="equipo">Equipo editorial</h2>
      <div class="not-prose grid gap-4">
        {autores}
      </div>

      <h2 id="politica-editorial">Política editorial</h2>
      <ul>
        <li>Toda nota se apoya en una fuente primaria siempre que existe: ley, reglamento, documento oficial o entidad responsable. Las fuentes figuran al final del texto.</li>
        <li>Separamos el hecho de la opinión. Cuando hay análisis, se identifica como tal.</li>
        <li>Las imágenes ilustrativas las produce la redacción, algunas con ayuda de inteligencia artificial, y se identifican en el epígrafe.</li>
      </ul>

      <h2 id="correcciones">Política de correcciones</h2>
      <p>Si nos equivocamos, corregimos. Si encontrás un dato erróneo, <a href="contacto.html">escribile a la redacción</a>. Cuando la corrección cambia el sentido de la nota, publicamos una aclaración en el propio texto, con la fecha y lo que se modificó.</p>

      <h2 id="publicidad">Publicidad y periodismo</h2>
      <p>Los anuncios aparecen siempre dentro de un espacio con la etiqueta “Publicidad” y no interfieren en la agenda de temas. Los anunciantes no leen las notas antes de su publicación. Mirá las reglas completas en <a href="anuncia.html">Anunciá</a>.</p>

      <h2 id="datos">Contacto de la redacción</h2>
      <p>Correo electrónico: <a href="mailto:{EMAIL}">{EMAIL}</a></p>''')

    institucional('contacto.html', 'Contacto: hablá con la redacción | PASION',
        'Hablá con la redacción de PASION: enviá sugerencias de temas, avisá sobre un error, pedí información '
        'comercial o ejercé tus derechos de privacidad.',
        'Hablá con la redacción', f'''
      <p class="text-lg">Sugerencia de tema, corrección, publicidad o privacidad: todo llega por la misma dirección, <a href="mailto:{EMAIL}">{EMAIL}</a>. Respondemos en días hábiles.</p>

      <form id="formContato" class="not-prose mt-8 grid gap-5 rounded-lg border border-slate-200 bg-white p-5 sm:p-6" novalidate>
        <div>
          <label for="contato-nome" class="block text-sm font-bold text-slate-900">Tu nombre</label>
          <input id="contato-nome" name="nome" type="text" autocomplete="name" required class="mt-2 w-full h-12 rounded-lg border border-slate-300 px-4 text-base">
        </div>
        <div>
          <label for="contato-email" class="block text-sm font-bold text-slate-900">Tu correo electrónico</label>
          <input id="contato-email" name="email" type="email" autocomplete="email" inputmode="email" required class="mt-2 w-full h-12 rounded-lg border border-slate-300 px-4 text-base">
        </div>
        <div>
          <label for="contato-assunto" class="block text-sm font-bold text-slate-900">Asunto</label>
          <select id="contato-assunto" name="assunto" class="mt-2 w-full h-12 rounded-lg border border-slate-300 px-3 text-base bg-white">
            <option>Sugerencia de tema</option>
            <option>Corrección de información</option>
            <option>Publicidad</option>
            <option>Privacidad y datos personales</option>
            <option>Otro asunto</option>
          </select>
        </div>
        <div>
          <label for="contato-mensagem" class="block text-sm font-bold text-slate-900">Mensaje</label>
          <textarea id="contato-mensagem" name="mensagem" rows="6" required class="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3 text-base"></textarea>
        </div>
        <div>
          <button type="submit" class="h-12 px-6 rounded-full bg-teal-700 text-base font-bold text-white hover:bg-teal-800">Escribir correo</button>
          <p class="mt-2 text-sm text-slate-600">El botón abre tu aplicación de correo con el mensaje listo. No se guarda nada en el sitio.</p>
          <p id="contatoStatus" class="mt-2 text-base font-semibold text-slate-900" role="status"></p>
        </div>
      </form>''')

    institucional('anuncia.html', 'Anunciá en PASION: formatos y reglas | PASION',
        'Anunciá en PASION: formatos disponibles, reglas de aceptación y cómo hablar con el equipo comercial. '
        'Publicidad siempre identificada y separada del periodismo.',
        'Anunciá en PASION', f'''
      <p class="text-lg">Lectores que siguen el fútbol, el dinero y los derechos del consumidor. Tu marca aparece en un espacio identificado como publicidad, lejos del texto periodístico.</p>

      <h2 id="formatos">Formatos</h2>
      <div class="not-prose tabela-rolavel">
        <table class="w-full text-left text-base border-collapse">
          <thead><tr class="bg-slate-100"><th class="border border-slate-200 px-3 py-2">Formato</th><th class="border border-slate-200 px-3 py-2">Tamaño</th><th class="border border-slate-200 px-3 py-2">Dónde aparece</th></tr></thead>
          <tbody>
            <tr><td class="border border-slate-200 px-3 py-2">Rectángulo mediano</td><td class="border border-slate-200 px-3 py-2">300 × 250</td><td class="border border-slate-200 px-3 py-2">Columna lateral de la portada y de las notas</td></tr>
            <tr><td class="border border-slate-200 px-3 py-2">Superbanner</td><td class="border border-slate-200 px-3 py-2">728 × 90</td><td class="border border-slate-200 px-3 py-2">Parte superior de la portada, en pantallas grandes</td></tr>
          </tbody>
        </table>
      </div>
      <p>Los datos de audiencia y los precios se envían a pedido, con el período de referencia.</p>

      <h2 id="reglas">Reglas de aceptación</h2>
      <ul>
        <li>Cumplimos la Ley 24.240 de Defensa del Consumidor, la Ley 22.802 de Lealtad Comercial y el Código de Ética y Autorregulación Publicitaria del CONARP: no aceptamos anuncios engañosos, abusivos ni de productos prohibidos por ley.</li>
        <li>No aceptamos promesas de ganancias fáciles, ingresos extra garantizados ni crédito sin información de costos.</li>
        <li>Todo anuncio lleva la etiqueta “Publicidad”, y los enlaces se marcan como patrocinados.</li>
        <li>El contenido patrocinado, cuando lo hay, se identifica en el título y no lo escribe la redacción.</li>
      </ul>

      <h2 id="contratar">Cómo contratar</h2>
      <p>Escribí a <a href="mailto:{EMAIL}?subject=Publicidad">{EMAIL}</a> con el asunto “Publicidad”, el período y el formato que te interesa.</p>''')

    institucional('terminos-de-uso.html', 'Términos de uso | PASION',
        'Términos de uso de PASION: naturaleza periodística del portal, uso del contenido, responsabilidad sobre '
        'la información, enlaces externos y foro competente.',
        'Términos de uso', '''
      <p class="text-sm text-slate-600">Última actualización: 20 de octubre de 2026</p>

      <h2>1. Qué es PASION</h2>
      <p>PASION es un medio periodístico de información. Publicamos noticias, guías y reportajes sobre fútbol, economía del deporte y derechos del consumidor.</p>

      <h2>2. Uso de la información</h2>
      <p>Las notas informan y no reemplazan el asesoramiento jurídico, financiero o médico para tu caso. Las fechas, los plazos y las reglas pueden cambiar; por eso cada nota muestra cuándo fue publicada y actualizada.</p>

      <h2>3. Enlaces a otros sitios</h2>
      <p>Indicamos fuentes oficiales y servicios de ayuda. No respondemos por el contenido ni por la disponibilidad de sitios de terceros.</p>

      <h2>4. Derechos de autor</h2>
      <p>Los textos, las artes y la marca de PASION están protegidos por la Ley 11.723 de Propiedad Intelectual de la Argentina. Podés citar fragmentos con crédito y enlace a la nota original. La reproducción íntegra requiere autorización.</p>''')

    institucional('politica-de-privacidad.html', 'Política de privacidad y cookies | PASION',
        'Conocé qué datos trata PASION, para qué, por cuánto tiempo y cómo ejercer tus derechos según la Ley 25.326, '
        'incluida la elección sobre las cookies de medición y de publicidad.',
        'Política de privacidad', f'''
      <p class="text-sm text-slate-600">Última actualización: 20 de octubre de 2026 · Ley 25.326 de Protección de los Datos Personales de la Argentina</p>

      <h2>1. En resumen</h2>
      <p>Leés PASION sin registrarte. No vendemos ni cedemos datos personales. Las cookies de medición y de publicidad solo funcionan si las aceptás.</p>

      <h2>2. Qué datos tratamos</h2>
      <ul>
        <li><strong>Datos técnicos de acceso</strong>, como la dirección IP y el navegador, que el servidor registra por seguridad.</li>
        <li><strong>Tu elección sobre las cookies</strong>, guardada en tu propio navegador.</li>
        <li><strong>Datos de medición y de publicidad</strong> (por ejemplo, el Pixel de Meta), solo si aceptás las cookies.</li>
        <li><strong>Lo que nos escribís</strong> por correo electrónico, cuando decidís contactarnos.</li>
      </ul>

      <h2>3. Para qué los usamos</h2>
      <ul>
        <li>Mantener el sitio en línea y protegido contra ataques.</li>
        <li>Medir la audiencia y el resultado de nuestras campañas de difusión, si das tu consentimiento.</li>
        <li>Responder a tus mensajes.</li>
      </ul>

      <h2 id="cookies">4. Cookies y cómo cambiar tu elección</h2>
      <p>En la primera visita, elegís entre aceptar o rechazar. Podés cambiar la elección en cualquier momento:</p>
      <p><button type="button" data-abrir-cookies class="h-11 px-5 rounded-full border border-slate-300 text-sm font-bold text-slate-900 hover:border-teal-700">Revisar preferencias de cookies</button></p>
      <p>Las fuentes tipográficas del sitio se cargan desde Google Fonts, lo que envía a Google la dirección IP de tu navegador.</p>

      <h2>5. Tus derechos</h2>
      <p>Según la Ley 25.326, podés pedir el acceso a tus datos (art. 14) y su rectificación, actualización o supresión (art. 16). La Agencia de Acceso a la Información Pública (AAIP) es el órgano de control de esa ley y atiende denuncias y reclamos. Escribí a <a href="mailto:{EMAIL}?subject=Privacidad">{EMAIL}</a> con el asunto “Privacidad”.</p>''')


# --------------------------------------------------------------------------
# portal.js, sitemap, feed, llms.txt
# --------------------------------------------------------------------------
def gerar_js(ms):
    linhas = ',\n'.join('  ' + json.dumps({'titulo': m['h1'], 'resumo': m['resumo'], 'editoria': EDITORIAS[m['editoria']]['nome'],
                                            'url': m['url']}, ensure_ascii=False) for m in ms)
    src = (BUILD / 'portal.src.js').read_text(encoding='utf-8')
    src = src.replace('  /*MATERIAS*/', linhas).replace('/*EMAIL*/', EMAIL).replace('/*PIXEL*/', META_PIXEL_ID)
    (RAIZ / 'assets' / 'js' / 'portal.js').write_text(src, encoding='utf-8', newline='\n')


def gerar_sitemap(ms):
    urls = [('', HOJE, '1.0'), ('noticias.html', HOJE, '0.8')]
    urls += [(m['url'], (m['atualizada'] or m['publicada'])[:10], '0.9') for m in ms]
    urls += [(p, HOJE, '0.4') for p in ['quienes-somos.html', 'contacto.html', 'anuncia.html',
                                         'politica-de-privacidad.html', 'terminos-de-uso.html']]
    corpo = '\n'.join(f'  <url><loc>{SITE}/{u}</loc><lastmod>{d}</lastmod><priority>{p}</priority></url>' for u, d, p in urls)
    (RAIZ / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{corpo}\n</urlset>\n', encoding='utf-8', newline='\n')


def gerar_feed(ms):
    from email.utils import format_datetime
    por_data = sorted(ms, key=lambda m: m['publicada'], reverse=True)
    itens = '\n'.join(f'''  <item>
    <title>{e(m['h1'])}</title>
    <link>{SITE}/{m['url']}</link>
    <guid isPermaLink="true">{SITE}/{m['url']}</guid>
    <description>{e(m['description'])}</description>
    <category>{EDITORIAS[m['editoria']]['nome']}</category>
    <dc:creator>{e(m['autor'])}</dc:creator>
    <pubDate>{format_datetime(datetime.fromisoformat(m['publicada']))}</pubDate>
    <enclosure url="{SITE}/{m['capa']}" type="image/jpeg" length="{(RAIZ / m['capa']).stat().st_size if (RAIZ / m['capa']).exists() else 0}"/>
  </item>''' for m in por_data)
    (RAIZ / 'feed.xml').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>PASION</title>
  <link>{SITE}/</link>
  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>Noticias de fútbol, economía del deporte y derechos del consumidor.</description>
  <language>es-AR</language>
{itens}
</channel>
</rss>
''', encoding='utf-8', newline='\n')


def gerar_llms(ms):
    linhas = '\n'.join(f"- [{m['h1']}]({SITE}/{m['url']}): {m['description']}" for m in ms)
    (RAIZ / 'llms.txt').write_text(f'''# PASION

> Portal de noticias en español (Argentina) sobre fútbol, economía del deporte y derechos del consumidor, con foco en la Argentina. Cada nota lista las fuentes consultadas.

## Secciones
- Fútbol: competencias, reglamentos y selecciones.
- Economía del deporte: patrocinios, tributos y trabajo en el sector.
- Consumidor: pagos, estafas, derechos y cambios en la ley.

## Notas
{linhas}

## Institucional
- [Quiénes somos, equipo y política editorial]({SITE}/quienes-somos.html)
- [Todas las noticias]({SITE}/noticias.html)
- [Feed RSS]({SITE}/feed.xml)
- [Contacto]({SITE}/contacto.html)
''', encoding='utf-8', newline='\n')


# --------------------------------------------------------------------------
# Capas (HTML renderizado pelo Chrome e salvo como JPG 1200x630)
# --------------------------------------------------------------------------
CORES = {'futebol': ('#D97706', '#FEF3C7'), 'economia': ('#059669', '#D1FAE5'), 'consumidor': ('#7E22CE', '#F3E8FF')}
MOTIVOS = {
    'futebol': '<svg class="motivo" viewBox="0 0 400 260" fill="none" stroke="currentColor" stroke-width="4"><rect x="10" y="10" width="380" height="240" rx="6"/><path d="M200 10v240"/><circle cx="200" cy="130" r="44"/><rect x="10" y="70" width="60" height="120"/><rect x="330" y="70" width="60" height="120"/></svg>',
    'economia': '<svg class="motivo" viewBox="0 0 400 260" fill="none" stroke="currentColor" stroke-width="4"><path d="M20 240h360"/><rect x="40" y="150" width="50" height="90"/><rect x="120" y="110" width="50" height="130"/><rect x="200" y="70" width="50" height="170"/><rect x="280" y="30" width="50" height="210"/><path d="M40 120 140 80l80 20 120-80" stroke-width="6"/></svg>',
    'consumidor': '<svg class="motivo" viewBox="0 0 400 260" fill="none" stroke="currentColor" stroke-width="4"><path d="M200 15 300 50v70c0 65-50 100-100 120-50-20-100-55-100-120V50Z"/><path d="m155 130 30 30 60-70" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}


def capa_html(rotulo, linha1, linha2, ed):
    forte, claro = CORES[ed] if ed else ('#14B8A6', '#CCFBF1')
    motivo = MOTIVOS.get(ed, MOTIVOS['consumidor'])
    return f'''<!DOCTYPE html><html lang="es-AR"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400..900&display=swap" rel="stylesheet">
<style>
*{{margin:0;box-sizing:border-box}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{font-family:Inter,sans-serif;background:#0B132B;color:#fff;position:relative}}
.faixa{{position:absolute;left:0;top:0;bottom:0;width:18px;background:{forte}}}
.grade{{position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.07) 1.5px,transparent 1.5px);background-size:28px 28px}}
.motivo{{position:absolute;right:60px;top:50%;transform:translateY(-50%);width:420px;color:{forte};opacity:.55}}
.conteudo{{position:absolute;left:90px;top:0;bottom:0;width:640px;display:flex;flex-direction:column;justify-content:center}}
.rotulo{{display:inline-block;align-self:flex-start;background:{claro};color:#0B132B;font-weight:800;font-size:24px;letter-spacing:.08em;text-transform:uppercase;padding:8px 16px;border-radius:6px}}
h1{{font-size:{86 if len(linha1) < 14 else 70}px;font-weight:900;line-height:1.02;letter-spacing:-.03em;margin-top:28px}}
p{{font-size:38px;font-weight:600;line-height:1.2;color:#CBD5E1;margin-top:22px}}
.marca{{position:absolute;left:90px;bottom:44px;font-size:24px;font-weight:900;letter-spacing:-.01em}}
.marca span{{color:#5EEAD4}}
</style></head><body>
<div class="grade"></div><div class="faixa"></div>{motivo}
<div class="conteudo"><span class="rotulo">{e(rotulo)}</span><h1>{e(linha1)}</h1><p>{e(linha2)}</p></div>
<div class="marca">PASION</div>
</body></html>'''


def chrome():
    for c in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']:
        if os.path.exists(c):
            return c
    raise SystemExit('Chrome não encontrado.')


def renderizar(html_txt, destino_jpg, w=1200, h=630, qualidade=84):
    from PIL import Image
    tmp = BUILD / '_render'
    tmp.mkdir(exist_ok=True)
    src = tmp / 'capa.html'
    png = tmp / 'capa.png'
    src.write_text(html_txt, encoding='utf-8')
    subprocess.run([chrome(), '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={w},{h}',
                    '--virtual-time-budget=6000', '--force-device-scale-factor=1', f'--screenshot={png}', src.as_uri()],
                   check=True, capture_output=True)
    img = Image.open(png).convert('RGB').crop((0, 0, w, h))
    destino_jpg.parent.mkdir(parents=True, exist_ok=True)
    if destino_jpg.suffix == '.png':
        img.save(destino_jpg, optimize=True)
    else:
        img.save(destino_jpg, 'JPEG', quality=qualidade, optimize=True, progressive=True)
    print('  capa:', destino_jpg.relative_to(RAIZ), f'{destino_jpg.stat().st_size // 1024} KB')


def gerar_capas(ms):
    for m in ms:
        renderizar(capa_html(EDITORIAS[m['editoria']]['nome'], m['arte'][0], m['arte'][1], m['editoria']), RAIZ / 'assets/images/capas' / f"{m['slug']}.jpg")
    renderizar(capa_html('Portal de noticias', 'PASION', 'Fútbol, economía del deporte y derechos del consumidor', None),
               RAIZ / 'assets/images/og-pasion.jpg')
    logo_html = f'''<!DOCTYPE html><html><head><style>html,body{{margin:0;width:512px;height:512px;background:#fff;display:flex;align-items:center;justify-content:center}}svg{{width:340px;height:auto}}</style></head><body>{ESCUDO.replace('width="26" height="32"', '')}</body></html>'''
    renderizar(logo_html, RAIZ / 'assets/images/logo-512.png', 512, 512)


def main():
    ms = [ler_materia(m) for m in MATERIAS]
    if '--capas' in sys.argv:
        gerar_capas(ms)
    for m in ms:
        gerar_materia(m, ms)
    gerar_home(ms)
    gerar_noticias(ms)
    gerar_institucionais()
    gerar_js(ms)
    gerar_sitemap(ms)
    gerar_feed(ms)
    gerar_llms(ms)
    print(f'{len(ms)} matérias + home, notícias e 6 institucionais geradas.')
    for m in ms:
        print(f"  {len(m['title']):>3} {len(m['description']):>3}  {m['url']}")


if __name__ == '__main__':
    main()
