# -*- coding: utf-8 -*-
"""
Gerador do portal Arena Diária.

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
SITE = 'https://arenadiaria.proxserverabner.site'
NOME = 'Arena Diária'
EMAIL = 'redacao@arenadiaria.com.br'   # e-mail de contato (provisório)
META_PIXEL_ID = '1879343259722567'                      # ID do Pixel da Meta; vazio = desligado
VERSAO = '20261013d'                     # muda o cache de CSS/JS a cada publicação
HOJE = '2026-10-13'

EDITORIAS = {
    'futebol':    {'nome': 'Futebol',             'ancora': 'futebol'},
    'economia':   {'nome': 'Economia do esporte', 'ancora': 'economia'},
    'consumidor': {'nome': 'Consumidor',          'ancora': 'consumidor'},
}

AUTORES = {
    'Rodrigo Albuquerque': {
        'id': 'autor-rodrigo-albuquerque', 'cargo': 'Repórter de economia do esporte',
        'foto': 'assets/images/autor-rodrigo-albuquerque.svg',
        'bio': 'Economista, cobre finanças dos clubes, patrocínios e o dinheiro que circula no futebol brasileiro.'},
    'Mariana Silva': {
        'id': 'autor-mariana-silva', 'cargo': 'Repórter de tecnologia',
        'foto': 'assets/images/autor-mariana-silva.jpg',
        'bio': 'Jornalista, cobre meios de pagamento, Pix, segurança digital e o funcionamento das plataformas.'},
    'Dr. Carlos Eduardo Mendes': {
        'id': 'autor-carlos-eduardo-mendes', 'cargo': 'Editor-chefe',
        'foto': 'assets/images/autor-carlos-eduardo.jpg',
        'bio': 'Advogado, responde pela edição do portal e acompanha leis e regras que afetam o esporte e o consumidor.'},
}

# Ordem = ordem de importância na home e na lista de notícias.
# arte: texto curto da capa (linha 1, linha 2).
MATERIAS = [
    dict(slug='noticia-brasileirao-rodada', fonte='brasileirao', editoria='futebol',
         publicada='2026-10-13T09:00:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Brasileirão', '20 clubes, 38 rodadas, nenhuma final')),
    dict(slug='noticia-selecao-brasileira', fonte='selecao', editoria='futebol',
         publicada='2026-09-02T16:20:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Seleção Brasileira', 'Cinco títulos e a força da base')),
    dict(slug='noticia-copa-do-brasil', fonte='copa-do-brasil', editoria='futebol',
         publicada='2026-10-10T15:30:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Copa do Brasil', '126 clubes, 9 fases e vaga na Libertadores')),
    dict(slug='noticia-libertadores', fonte='libertadores', editoria='futebol',
         publicada='2026-10-06T18:10:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Libertadores', 'Do pré-torneio à final em jogo único')),
    dict(slug='noticia-patrocinios-futebol', fonte='patrocinios', editoria='economia',
         publicada='2026-08-18T10:40:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Patrocínio no futebol', 'Do master da camisa ao nome do estádio')),
    dict(slug='noticia-direitos-de-transmissao', fonte='transmissao', editoria='economia',
         publicada='2026-09-16T14:00:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Direitos de TV', 'O que muda com a lei do mandante')),
    dict(slug='noticia-saf-sociedade-anonima-futebol', fonte='saf', editoria='economia',
         publicada='2026-09-08T09:30:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('SAF no futebol', 'Como o clube vira empresa e paga dívidas')),
    dict(slug='noticia-ingressos-direitos-torcedor', fonte='ingressos', editoria='consumidor',
         publicada='2026-09-25T11:45:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Ingressos', 'Meia-entrada, reembolso e onde reclamar')),
    dict(slug='noticia-pix-golpes-med', fonte='pix-golpes', editoria='consumidor',
         publicada='2026-10-02T10:20:00-03:00', atualizada=None, nota=None, apoio=False,
         arte=('Golpe no Pix', 'Como usar o MED e pedir o dinheiro de volta')),
]

MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
         'setembro', 'outubro', 'novembro', 'dezembro']


def e(texto):
    return html.escape(texto or '', quote=True)


def data_br(iso, hora=True):
    d = datetime.fromisoformat(iso)
    texto = f'{d.day} de {MESES[d.month - 1]} de {d.year}'
    return f'{texto}, {d:%H}h{d:%M}' if hora else texto


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
    m['alt'] = f"Arte da Arena Diária com o texto “{m['arte'][0]}: {m['arte'][1]}”"
    m['capa_web'] = m['capa']
    m['credito'] = 'Arte: Arena Diária'
    foto = preparar_foto(m['slug'])
    if foto:
        m['capa'], m['capa_web'] = foto
        m['alt'] = IMAGENS.get(m['slug'], {}).get('alt') or m['alt']
        m['credito'] = 'Imagem ilustrativa gerada com inteligência artificial'
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
    return (f'{ESCUDO}<span class="text-xl font-black tracking-tight {cor}">Arena '
            f'<span class="{destaque}">Diária</span></span>')


def form_busca(sufixo, classes):
    return f'''<form data-busca-form role="search" action="noticias.html" method="get" class="relative {classes}">
        <label for="busca-{sufixo}" class="sr-only">Buscar notícias</label>
        <input id="busca-{sufixo}" type="search" name="q" placeholder="Buscar notícias" autocomplete="off" role="combobox" aria-autocomplete="list" aria-controls="busca-{sufixo}-lista" aria-expanded="false" class="w-full h-11 rounded-full border border-slate-300 bg-slate-50 pl-4 pr-12 text-base text-slate-900 placeholder:text-slate-500 focus:bg-white">
        <button type="submit" class="touch-target absolute right-0 top-0 text-slate-600 hover:text-teal-700" aria-label="Buscar">{LUPA}</button>
        <div id="busca-{sufixo}-lista" class="busca-resultados" hidden></div>
      </form>'''


def cabecalho(ativo):
    itens = [('inicio', './', 'Início'),
             ('futebol', './#futebol', 'Futebol'),
             ('economia', './#economia', 'Economia do esporte'),
             ('consumidor', './#consumidor', 'Consumidor'),
             ('noticias', 'noticias.html', 'Todas as notícias')]
    nav = '\n'.join(
        f'<li><a href="{href}" class="inline-flex h-11 items-center px-3 text-sm font-semibold whitespace-nowrap text-slate-700 hover:text-teal-700"'
        f'{ATUAL if chave == ativo else ""}>{rotulo}</a></li>'
        for chave, href, rotulo in itens)
    return f'''<a href="#conteudo" class="skip-link">Pular para o conteúdo</a>
  <header class="sticky top-0 z-50 bg-white border-b border-slate-200">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center gap-4">
      <a href="./" class="flex items-center gap-2 shrink-0" aria-label="Arena Diária, página inicial">{logo()}</a>
      <time id="headerLiveDate" class="hidden lg:block text-sm text-slate-600"></time>
      {form_busca('topo', 'hidden md:block ml-auto w-72')}
      <button id="buscaToggle" type="button" class="inline-flex items-center justify-center min-w-[44px] min-h-[44px] md:hidden ml-auto text-slate-700" aria-expanded="false" aria-controls="buscaPainel" aria-label="Abrir busca">{LUPA}</button>
      <a href="anuncie.html" class="hidden sm:inline-flex h-11 items-center px-4 rounded-full border border-slate-300 text-sm font-semibold text-slate-700 hover:border-teal-700 hover:text-teal-700">Anuncie</a>
    </div>
    <div id="buscaPainel" class="md:hidden border-t border-slate-200 px-4 py-3" hidden>
      {form_busca('celular', 'w-full')}
    </div>
    <nav aria-label="Editorias" class="border-t border-slate-200">
      <ul class="nav-editorias max-w-6xl mx-auto px-2 flex overflow-x-auto">
        {nav}
      </ul>
    </nav>
  </header>'''


def rodape():
    return f'''<footer class="bg-slate-900 text-slate-300 mt-16">
    <div class="max-w-6xl mx-auto px-4 py-12 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
      <div>
        <a href="./" class="flex items-center gap-2" aria-label="Arena Diária, página inicial">{logo(claro=True)}</a>
        <p class="mt-4 text-sm leading-relaxed">Notícias de futebol, economia do esporte e direitos do consumidor, com fonte em cada informação.</p>
      </div>
      <div>
        <h2 class="text-sm font-bold uppercase tracking-wide text-white">Editorias</h2>
        <ul class="mt-3 space-y-1 text-sm">
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#futebol">Futebol</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#economia">Economia do esporte</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#consumidor">Consumidor</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="noticias.html">Todas as notícias</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="feed.xml">Feed RSS</a></li>
        </ul>
      </div>
      <div>
        <h2 class="text-sm font-bold uppercase tracking-wide text-white">Institucional</h2>
        <ul class="mt-3 space-y-1 text-sm">
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="quem-somos.html">Quem somos e expediente</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="quem-somos.html#politica-editorial">Política editorial</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="contato.html">Contato</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="anuncie.html">Anuncie</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="politica-de-privacidade.html">Privacidade</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="termos-de-uso.html">Termos de uso</a></li>
          <li><button type="button" data-abrir-cookies class="py-1.5 text-left hover:text-white hover:underline">Preferências de cookies</button></li>
        </ul>
      </div>
      <div>
        <h2 class="text-sm font-bold uppercase tracking-wide text-white">Editorias</h2>
        <ul class="mt-3 space-y-1 text-sm">
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#futebol">Futebol</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#economia">Economia do esporte</a></li>
          <li><a class="inline-block py-1.5 hover:text-white hover:underline" href="./#consumidor">Consumidor</a></li>
        </ul>
      </div>
    </div>
    <div class="border-t border-slate-700">
      <p class="max-w-6xl mx-auto px-4 py-5 text-sm text-slate-400">© 2026 Arena Diária. Conteúdo jornalístico.</p>
    </div>
  </footer>

  <div id="cookieConsentBanner" role="region" aria-label="Preferências de cookies" hidden>
    <div class="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center gap-3">
      <p class="flex-1 text-sm leading-relaxed">Usamos cookies de medição de audiência e de anúncios só se você aceitar. Recusar não muda nada no que você lê. <a href="politica-de-privacidade.html#cookies">Saiba mais</a></p>
      <div class="flex gap-2">
        <button type="button" data-cookie="recusar" class="flex-1 md:flex-none h-11 px-6 rounded-full border-2 border-white text-sm font-bold hover:bg-white hover:text-slate-900">Recusar</button>
        <button type="button" data-cookie="aceitar" class="flex-1 md:flex-none h-11 px-6 rounded-full border-2 border-white text-sm font-bold hover:bg-white hover:text-slate-900">Aceitar</button>
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
        'publishingPrinciples': f'{SITE}/quem-somos.html#politica-editorial',
        'correctionsPolicy': f'{SITE}/quem-somos.html#correcoes',
        'masthead': f'{SITE}/quem-somos.html#expediente',
        'actionableFeedbackPolicy': f'{SITE}/contato.html',
        'inLanguage': 'pt-BR',
    }


def pagina(arquivo, titulo, descricao, corpo, ativo='', og_tipo='website', imagem=None, imagem_alt=None,
           extra_head='', grafo=None, robots='index, follow, max-image-preview:large'):
    url = f'{SITE}/' if arquivo == 'index.html' else f'{SITE}/{arquivo}'
    imagem = imagem or 'assets/images/og-arena-diaria.jpg'
    imagem_alt = imagem_alt or 'Arena Diária: futebol, economia do esporte e direitos do consumidor'
    grafo = [jsonld_org()] + (grafo or [])
    ld = json.dumps({'@context': 'https://schema.org', '@graph': grafo}, ensure_ascii=False, indent=1)
    doc = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(titulo)}</title>
  <meta name="description" content="{e(descricao)}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{url}">
  <meta name="theme-color" content="#0B132B">
  <link rel="icon" href="assets/images/favicon.svg" type="image/svg+xml">
  <link rel="alternate" type="application/rss+xml" title="Arena Diária: últimas notícias" href="{SITE}/feed.xml">

  <meta property="og:site_name" content="{NOME}">
  <meta property="og:locale" content="pt_BR">
  <meta property="og:type" content="{og_tipo}">
  <meta property="og:title" content="{e(titulo.replace(' | Arena Diária', ''))}">
  <meta property="og:description" content="{e(descricao)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE}/{imagem}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{e(imagem_alt)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{e(titulo.replace(' | Arena Diária', ''))}">
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
<body class="antialiased">
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
        miolo = (f'<a href="anuncie.html" data-slot="{slot}" class="block">'
                 f'<img src="assets/images/anuncios/{formato}.webp" width="{w}" height="{h}" loading="lazy" '
                 f'alt="Anuncie na Arena Diária: fale com a nossa equipe comercial" class="w-full h-auto"></a>')
    else:
        miolo = (f'<a href="anuncie.html" data-slot="{slot}" class="block p-6 text-center hover:bg-slate-50">'
                 f'<span class="block text-lg font-extrabold text-slate-900">Sua marca aqui</span>'
                 f'<span class="block mt-1 text-sm text-slate-600">Fale com a equipe comercial da Arena Diária</span></a>')
    return f'<aside class="ad-slot" aria-label="Publicidade"><span class="ad-label">Publicidade</span>{miolo}</aside>'


def billboard(slot):
    """Faixa de publicidade acima da manchete, no formato do G1: 970x250 no computador e 320x100 no celular.

    Criativos em assets/images/anuncios/billboard.webp (970x250) e billboard-mobile.webp (320x100);
    se houver billboard(.mp4|.webm) e billboard-mobile(.mp4|.webm), o portal.js toca a versão animada.
    Sem criativo, mostra o anúncio da casa (Anuncie na Arena Diária). O espaço fica reservado para não
    empurrar a página quando o anúncio carrega.
    """
    pasta = RAIZ / 'assets' / 'images' / 'anuncios'
    if (pasta / 'billboard.webp').exists():
        movel = 'billboard-mobile.webp' if (pasta / 'billboard-mobile.webp').exists() else 'billboard.webp'
        # Versão animada (vídeo do HyperFrames): o portal.js troca a imagem pelo vídeo quando ele carrega
        videos = ''.join(f' data-video-{tipo}="assets/images/anuncios/{nome}?v={VERSAO}"'
                         for tipo, nome in (('mp4', 'billboard.mp4'), ('webm', 'billboard.webm'),
                                            ('mp4-movel', 'billboard-mobile.mp4'), ('webm-movel', 'billboard-mobile.webm'))
                         if (pasta / nome).exists())
        miolo = (f'<a href="anuncie.html" data-slot="{slot}" class="billboard-link"{videos}>'
                 f'<picture><source media="(min-width: 768px)" srcset="assets/images/anuncios/billboard.webp">'
                 f'<img src="assets/images/anuncios/{movel}" width="970" height="250" '
                 f'alt="Anuncie na Arena Diária: fale com a nossa equipe comercial" class="billboard-img"></picture></a>')
    else:
        miolo = (f'<a href="anuncie.html" data-slot="{slot}" class="billboard-link billboard-casa">'
                 f'<span class="billboard-marca">Arena Diária</span>'
                 f'<span class="billboard-texto"><strong>Sua marca acima da manchete</strong>'
                 f'<span class="billboard-sub">Fale com leitores de futebol, economia do esporte e consumidor</span></span>'
                 f'<span class="billboard-cta">Anuncie aqui</span></a>')
    return (f'<aside class="billboard" aria-label="Publicidade"><span class="billboard-label">Publicidade</span>'
            f'<div class="billboard-area">{miolo}</div></aside>')


def cartao(m, tamanho='medio', carregar='lazy'):
    tit = {'grande': 'text-2xl md:text-4xl', 'medio': 'text-lg md:text-xl', 'pequeno': 'text-base'}[tamanho]
    resumo = '' if tamanho == 'pequeno' else f'<p class="mt-2 text-base text-slate-600 leading-relaxed">{e(m["resumo"])}</p>'
    prioridade = ' fetchpriority="high"' if carregar == 'eager' else ''
    return f'''<article class="card-link group">
          <div class="overflow-hidden rounded-lg bg-slate-200">
            <img src="{m['capa_web']}" width="1200" height="630" alt="" loading="{carregar}"{prioridade} class="w-full h-auto aspect-[1200/630] object-cover">
          </div>
          <div class="mt-3">{chapeu(m['editoria'])}</div>
          <h3 class="headline {tit} mt-2"><a href="{m['url']}" class="stretched">{e(m['h1'])}</a></h3>
          {resumo}
          <p class="mt-2 text-sm text-slate-600"><time datetime="{m['publicada']}">{data_curta(m['publicada'])}</time>{' · atualizada' if m['atualizada'] else ''}</p>
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


# --------------------------------------------------------------------------
# Matéria
# --------------------------------------------------------------------------
def gerar_materia(m, todas):
    autor = AUTORES[m['autor']]
    ed = EDITORIAS[m['editoria']]
    url_abs = f"{SITE}/{m['url']}"
    atual = (f' · Atualizada em <time datetime="{m["atualizada"]}">{data_br(m["atualizada"])}</time>'
             if m['atualizada'] else '')
    nota = (f'<p class="mt-8 rounded-lg border border-amber-300 bg-amber-50 p-4 text-base text-amber-900">'
            f'<strong>Nota da redação.</strong> {e(m["nota"])}</p>') if m['nota'] else ''
    fontes = ''
    if m['fontes']:
        lis = '\n'.join(f'<li><a href="{e(f)}" rel="noopener noreferrer">{e(dominio(f))}</a></li>' for f in m['fontes'])
        fontes = f'<section class="mt-10" aria-labelledby="fontes-titulo"><h2 id="fontes-titulo" class="text-lg font-extrabold text-slate-900">Fontes consultadas</h2><ul class="mt-3 list-disc pl-6 text-base text-slate-700 space-y-1">{lis}</ul></section>'
    mesmas = [o for o in todas if o is not m and o['editoria'] == m['editoria']]
    outras = [o for o in todas if o is not m and o['editoria'] != m['editoria']]
    relacionadas = (mesmas + outras)[:3]
    leia = '\n'.join(cartao(o, 'pequeno') for o in relacionadas)
    mais = '\n'.join(item_lista(o) for o in [o for o in todas if o is not m][:5])
    whats = 'https://wa.me/?text=' + quote(f"{m['h1']} {url_abs}")

    corpo = f'''  <main id="conteudo" class="max-w-6xl mx-auto px-4 py-6 lg:py-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_300px]">
    <article class="min-w-0">
      <nav aria-label="Trilha de navegação" class="text-sm text-slate-600">
        <ol class="flex flex-wrap items-center gap-x-2 gap-y-1">
          <li><a href="./" class="underline hover:text-teal-700">Início</a></li>
          <li aria-hidden="true">›</li>
          <li><a href="./#{ed['ancora']}" class="underline hover:text-teal-700">{ed['nome']}</a></li>
          <li aria-hidden="true">›</li>
          <li aria-current="page">{e(m['trilha'] or m['h1'])}</li>
        </ol>
      </nav>

      <header class="mt-6">
        {chapeu(m['editoria'])}
        <h1 class="headline text-3xl sm:text-4xl lg:text-5xl mt-3">{e(m['h1'])}</h1>
        <p class="mt-4 text-lg sm:text-xl text-slate-600 leading-relaxed">{e(m['linha_fina'])}</p>
        <div class="mt-6 pb-6 border-b border-slate-200 flex items-center gap-3">
          <img src="{autor['foto']}" width="48" height="48" alt="" class="w-12 h-12 rounded-full object-cover bg-slate-200">
          <div class="text-sm leading-relaxed">
            <p>Por <a href="quem-somos.html#{autor['id']}" class="font-semibold text-slate-900 underline hover:text-teal-700">{e(m['autor'])}</a>, {autor['cargo'].lower()}</p>
            <p class="text-slate-600">Publicada em <time datetime="{m['publicada']}">{data_br(m['publicada'])}</time>{atual} · Leitura de {m['leitura']} min</p>
          </div>
        </div>
      </header>

      <figure class="mt-6">
        <img src="{m['capa_web']}" width="1200" height="630" alt="{e(m['alt'])}" fetchpriority="high" class="w-full h-auto rounded-lg">
        <figcaption class="mt-2 text-sm text-slate-600">{m['credito']}</figcaption>
      </figure>

      {nota}

      <div class="article-body mt-8">
{m['corpo']}
      </div>

      {fontes}

      

      <div class="mt-10 flex flex-wrap items-center gap-3">
        <span class="text-sm font-bold text-slate-900">Compartilhe:</span>
        <a href="{whats}" rel="noopener noreferrer" class="inline-flex h-11 items-center px-4 rounded-full bg-emerald-700 text-white text-sm font-semibold hover:bg-emerald-800">WhatsApp</a>
        <button type="button" data-copiar-link="{url_abs}" aria-describedby="status-copiar" class="h-11 px-4 rounded-full border border-slate-300 text-sm font-semibold text-slate-700 hover:border-teal-700 hover:text-teal-700">Copiar link</button>
        <span id="status-copiar" class="text-sm text-slate-600" aria-live="polite"></span>
      </div>

      <p class="mt-6 text-sm text-slate-600">Viu um erro nesta matéria? <a href="contato.html" class="underline hover:text-teal-700">Avise a redação</a>. Corrigimos e registramos a correção aqui.</p>

      <section class="mt-12 pt-8 border-t border-slate-200" aria-labelledby="leia-tambem">
        <h2 id="leia-tambem" class="text-xl font-extrabold text-slate-900">Leia também</h2>
        <div class="mt-5 grid gap-6 sm:grid-cols-3">
{leia}
        </div>
      </section>
    </article>

    <div class="space-y-8">
      {publicidade('materia-lateral')}
      <section aria-labelledby="mais-noticias">
        <h2 id="mais-noticias" class="text-lg font-extrabold text-slate-900 border-b-2 border-slate-900 pb-2">Mais notícias</h2>
        <ul>
{mais}
        </ul>
      </section>
    </div>
  </main>'''

    grafo = [
        {'@type': 'Person', '@id': f"{SITE}/quem-somos.html#{autor['id']}", 'name': m['autor'],
         'jobTitle': autor['cargo'], 'url': f"{SITE}/quem-somos.html#{autor['id']}", 'worksFor': {'@id': ORG_ID}},
        {'@type': 'NewsArticle', '@id': f'{url_abs}#materia', 'mainEntityOfPage': url_abs,
         'headline': m['h1'], 'description': m['description'],
         'image': [{'@type': 'ImageObject', 'url': f"{SITE}/{m['capa']}", 'width': 1200, 'height': 630}],
         'datePublished': m['publicada'], 'dateModified': m['atualizada'] or m['publicada'],
         'author': {'@id': f"{SITE}/quem-somos.html#{autor['id']}"}, 'publisher': {'@id': ORG_ID},
         'articleSection': ed['nome'], 'inLanguage': 'pt-BR', 'isAccessibleForFree': True,
         'wordCount': len(re.sub(r'<[^>]+>', ' ', m['corpo']).split())},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Início', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': ed['nome'], 'item': f"{SITE}/#{ed['ancora']}"},
            {'@type': 'ListItem', 'position': 3, 'name': m['trilha'] or m['h1']}]},
    ]
    extra = '\n'.join([
        f'  <meta property="article:published_time" content="{m["publicada"]}">',
        f'  <meta property="article:modified_time" content="{m["atualizada"] or m["publicada"]}">',
        f'  <meta property="article:section" content="{ed["nome"]}">',
        f'  <meta property="article:author" content="{SITE}/quem-somos.html#{autor["id"]}">',
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
      <span class="ticker-badge px-2 py-1 rounded shrink-0">Destaques</span>
      <a id="tickerText" href="{primeiro['url']}" class="flex-1 min-w-0 truncate text-sm font-semibold hover:underline">{e(primeiro['h1'])}</a>
      <button id="tickerPausa" type="button" class="touch-target shrink-0 text-white" aria-pressed="false" aria-label="Pausar a troca de destaques"><span data-icone aria-hidden="true">❚❚</span></button>
    </div>
  </div>

  <main id="conteudo" class="max-w-6xl mx-auto px-4 py-8">
    <h1 class="sr-only">Arena Diária: notícias de futebol, economia do esporte e direitos do consumidor</h1>
    {billboard('home-topo')}

    <section aria-label="Manchetes" class="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      {cartao(destaque, 'grande', 'eager')}
      <div class="grid gap-8 content-start">
        {cartao(d2, 'pequeno')}
        {cartao(d3, 'pequeno')}
      </div>
    </section>

    <div class="mt-4 grid gap-10 lg:grid-cols-[minmax(0,1fr)_300px]">
      <div class="min-w-0">
{secoes}
      </div>

      <div class="space-y-8 pt-10">
        {publicidade('home-lateral')}
        <section aria-labelledby="escolhas">
          <h2 id="escolhas" class="text-lg font-extrabold text-slate-900 border-b-2 border-slate-900 pb-2">Escolhas da redação</h2>
          <ul>
{escolhas}
          </ul>
          <a href="noticias.html" class="mt-4 inline-flex h-11 items-center text-sm font-bold text-teal-700 underline">Ver todas as notícias</a>
        </section>
        <section aria-labelledby="fale-redacao" class="rounded-lg bg-slate-900 p-5 text-slate-200">
          <h2 id="fale-redacao" class="text-lg font-extrabold text-white">Tem uma pauta ou viu um erro?</h2>
          <p class="mt-2 text-base leading-relaxed">Escreva para a redação. Lemos todas as mensagens e corrigimos o que estiver errado.</p>
          <a href="contato.html" class="mt-4 inline-flex h-11 items-center px-5 rounded-full bg-white text-sm font-bold text-slate-900 hover:bg-teal-50">Fale com a redação</a>
        </section>
      </div>
    </div>
  </main>'''
    grafo = [{'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': f'{SITE}/', 'name': NOME, 'inLanguage': 'pt-BR',
              'publisher': {'@id': ORG_ID},
              'potentialAction': {'@type': 'SearchAction', 'target': f'{SITE}/noticias.html?q={{search_term_string}}',
                                  'query-input': 'required name=search_term_string'}}]
    pagina('index.html', 'Arena Diária: futebol, economia do esporte e consumidor',
           'Portal de notícias sobre futebol, economia do esporte e direitos do consumidor. Matérias com fonte, '
           'linguagem clara e correções transparentes.', corpo, ativo='inicio', grafo=grafo)


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
    <h1 class="headline text-3xl sm:text-4xl">Todas as notícias</h1>
    <p class="mt-3 text-lg text-slate-600">As matérias mais recentes primeiro. Busque por um tema, um time ou uma palavra.</p>
    <form action="noticias.html" method="get" role="search" class="mt-6" onsubmit="return false">
      <label for="buscaPagina" class="block text-sm font-bold text-slate-900">Buscar nas notícias</label>
      <input id="buscaPagina" type="search" name="q" autocomplete="off" class="mt-2 w-full h-12 rounded-lg border border-slate-300 px-4 text-base" placeholder="Ex.: Pix, Brasileirão, patrocínio">
    </form>
    <p id="buscaStatus" class="mt-4 text-sm text-slate-600" role="status">{len(ms)} matérias publicadas.</p>
    <ul class="mt-2">
{itens}
    </ul>
  </main>'''
    grafo = [{'@type': 'CollectionPage', 'url': f'{SITE}/noticias.html', 'name': 'Todas as notícias', 'isPartOf': {'@id': f'{SITE}/#site'},
              'mainEntity': {'@type': 'ItemList', 'itemListElement': [
                  {'@type': 'ListItem', 'position': i + 1, 'url': f"{SITE}/{m['url']}"} for i, m in enumerate(por_data)]}}]
    pagina('noticias.html', 'Todas as notícias | Arena Diária',
           'Lista completa das matérias da Arena Diária sobre futebol, economia do esporte e direitos do consumidor, '
           'da mais recente para a mais antiga.', corpo, ativo='noticias', grafo=grafo)


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

    institucional('quem-somos.html', 'Quem somos, expediente e política editorial | Arena Diária',
        'Conheça a Arena Diária: o que cobrimos, quem escreve, como checamos as informações, como corrigimos erros '
        'e como separamos publicidade de jornalismo.',
        'Quem somos', f'''
      <p class="text-lg">A Arena Diária é um portal de notícias sobre futebol, economia do esporte e direitos do consumidor. Explicamos regras, contratos e mudanças na lei que afetam quem acompanha o esporte, com fonte em cada informação.</p>

      <h2 id="o-que-cobrimos">O que cobrimos</h2>
      <ul>
        <li><strong>Futebol:</strong> competições, regulamentos e seleções.</li>
        <li><strong>Economia do esporte:</strong> patrocínios, receitas dos clubes, tributos e trabalho no setor.</li>
        <li><strong>Consumidor:</strong> pagamentos, golpes, direitos e o que muda quando a lei muda.</li>
      </ul>

      <h2 id="expediente">Expediente</h2>
      <div class="not-prose grid gap-4">
        {autores}
      </div>

      <h2 id="politica-editorial">Política editorial</h2>
      <ul>
        <li>Toda matéria se apoia em fonte primária sempre que ela existe: lei, regulamento, documento oficial ou entidade responsável. As fontes ficam listadas no fim do texto.</li>
        <li>Separamos fato de opinião. Quando houver análise, ela vem identificada como tal.</li>
        <li>Imagens ilustrativas são produzidas pela redação, algumas com auxílio de inteligência artificial, e vêm identificadas na legenda.</li>
      </ul>

      <h2 id="correcoes">Política de correções</h2>
      <p>Errou, corrigimos. Se você encontrar uma informação errada, <a href="contato.html">escreva para a redação</a>. Quando a correção muda o sentido da matéria, publicamos uma nota no próprio texto com a data e o que foi alterado.</p>

      <h2 id="publicidade">Publicidade e jornalismo</h2>
      <p>Anúncios aparecem sempre dentro de um espaço com o rótulo “Publicidade” e não interferem na pauta. Anunciantes não leem matérias antes da publicação. Veja as regras completas em <a href="anuncie.html">Anuncie</a>.</p>

      <h2 id="dados">Dados institucionais</h2>
      <p>Arena Diária Comunicação e Mídia Digital Ltda.<br>CNPJ 45.890.123/0001-90<br>Setor Hoteleiro Sul, Quadra 06, Bloco E, Asa Sul, Brasília (DF), CEP 70322-900<br>E-mail: <a href="mailto:{EMAIL}">{EMAIL}</a></p>''')

    institucional('contato.html', 'Contato: fale com a redação | Arena Diária',
        'Fale com a redação da Arena Diária: envie sugestões de pauta, avise sobre um erro, peça informações '
        'comerciais ou exerça seus direitos de privacidade.',
        'Fale com a redação', f'''
      <p class="text-lg">Sugestão de pauta, correção, publicidade ou privacidade: tudo chega pelo mesmo endereço, <a href="mailto:{EMAIL}">{EMAIL}</a>. Respondemos em dias úteis.</p>

      <form id="formContato" class="not-prose mt-8 grid gap-5 rounded-lg border border-slate-200 bg-white p-5 sm:p-6" novalidate>
        <div>
          <label for="contato-nome" class="block text-sm font-bold text-slate-900">Seu nome</label>
          <input id="contato-nome" name="nome" type="text" autocomplete="name" required class="mt-2 w-full h-12 rounded-lg border border-slate-300 px-4 text-base">
        </div>
        <div>
          <label for="contato-email" class="block text-sm font-bold text-slate-900">Seu e-mail</label>
          <input id="contato-email" name="email" type="email" autocomplete="email" inputmode="email" required class="mt-2 w-full h-12 rounded-lg border border-slate-300 px-4 text-base">
        </div>
        <div>
          <label for="contato-assunto" class="block text-sm font-bold text-slate-900">Assunto</label>
          <select id="contato-assunto" name="assunto" class="mt-2 w-full h-12 rounded-lg border border-slate-300 px-3 text-base bg-white">
            <option>Sugestão de pauta</option>
            <option>Correção de informação</option>
            <option>Publicidade</option>
            <option>Privacidade e dados pessoais</option>
            <option>Outro assunto</option>
          </select>
        </div>
        <div>
          <label for="contato-mensagem" class="block text-sm font-bold text-slate-900">Mensagem</label>
          <textarea id="contato-mensagem" name="mensagem" rows="6" required class="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3 text-base"></textarea>
        </div>
        <div>
          <button type="submit" class="h-12 px-6 rounded-full bg-teal-700 text-base font-bold text-white hover:bg-teal-800">Escrever e-mail</button>
          <p class="mt-2 text-sm text-slate-600">O botão abre o seu aplicativo de e-mail com a mensagem pronta. Nada fica guardado no site.</p>
          <p id="contatoStatus" class="mt-2 text-base font-semibold text-slate-900" role="status"></p>
        </div>
      </form>''')

    institucional('anuncie.html', 'Anuncie na Arena Diária: formatos e regras | Arena Diária',
        'Anuncie na Arena Diária: formatos disponíveis, regras de aceite e como falar com a equipe comercial. '
        'Publicidade sempre identificada e separada do jornalismo.',
        'Anuncie na Arena Diária', f'''
      <p class="text-lg">Leitores que acompanham futebol, dinheiro e direitos do consumidor. Sua marca aparece em espaço identificado como publicidade, longe do texto jornalístico.</p>

      <h2 id="formatos">Formatos</h2>
      <div class="not-prose tabela-rolavel">
        <table class="w-full text-left text-base border-collapse">
          <thead><tr class="bg-slate-100"><th class="border border-slate-200 px-3 py-2">Formato</th><th class="border border-slate-200 px-3 py-2">Tamanho</th><th class="border border-slate-200 px-3 py-2">Onde aparece</th></tr></thead>
          <tbody>
            <tr><td class="border border-slate-200 px-3 py-2">Retângulo médio</td><td class="border border-slate-200 px-3 py-2">300 × 250</td><td class="border border-slate-200 px-3 py-2">Coluna lateral da home e das matérias</td></tr>
            <tr><td class="border border-slate-200 px-3 py-2">Superbanner</td><td class="border border-slate-200 px-3 py-2">728 × 90</td><td class="border border-slate-200 px-3 py-2">Topo da home, em telas grandes</td></tr>
          </tbody>
        </table>
      </div>
      <p>Dados de audiência e preços são enviados sob pedido, com o período de referência.</p>

      <h2 id="regras">Regras de aceite</h2>
      <ul>
        <li>Seguimos o Código de Defesa do Consumidor e o Código Brasileiro de Autorregulamentação Publicitária: não aceitamos anúncio enganoso, abusivo ou de produto proibido por lei.</li>
        <li>Não aceitamos promessa de ganho fácil, renda extra garantida ou crédito sem informação de custo.</li>
        <li>Todo anúncio leva o rótulo “Publicidade”, e os links seguem marcados como patrocinados.</li>
        <li>Conteúdo patrocinado, quando houver, vem identificado no título e não é escrito pela redação.</li>
      </ul>

      <h2 id="falar">Como contratar</h2>
      <p>Escreva para <a href="mailto:{EMAIL}?subject=Publicidade">{EMAIL}</a> com o assunto “Publicidade”, o período e o formato desejado.</p>''')

    institucional('termos-de-uso.html', 'Termos de uso | Arena Diária',
        'Termos de uso da Arena Diária: natureza jornalística do portal, uso do conteúdo, responsabilidade sobre '
        'as informações, links externos e foro competente.',
        'Termos de uso', '''
      <p class="text-sm text-slate-600">Última atualização: 13 de outubro de 2026</p>

      <h2>1. O que é a Arena Diária</h2>
      <p>A Arena Diária é um veículo jornalístico de informação. Publicamos notícias, guias e reportagens sobre futebol, economia do esporte e direitos do consumidor.</p>

      <h2>2. Uso das informações</h2>
      <p>As matérias informam e não substituem orientação jurídica, financeira ou médica para o seu caso. Datas, prazos e regras podem mudar; por isso cada matéria mostra quando foi publicada e atualizada.</p>

      <h2>3. Links para outros sites</h2>
      <p>Indicamos fontes oficiais e serviços de apoio. Não respondemos pelo conteúdo nem pela disponibilidade de sites de terceiros.</p>

      <h2>4. Direitos autorais</h2>
      <p>Textos, artes e marca da Arena Diária são protegidos pela Lei nº 9.610/1998. Você pode citar trechos com crédito e link para a matéria original. A reprodução integral depende de autorização.</p>

      <h2>5. Foro</h2>
      <p>Fica eleito o foro da Comarca de Brasília (DF) para resolver questões sobre estes termos, sem prejuízo do foro do domicílio do consumidor.</p>''')

    institucional('politica-de-privacidade.html', 'Política de privacidade e cookies | Arena Diária',
        'Saiba quais dados a Arena Diária trata, para quê, por quanto tempo e como exercer seus direitos pela LGPD, '
        'incluindo a escolha sobre cookies de medição e anúncios.',
        'Política de privacidade', f'''
      <p class="text-sm text-slate-600">Última atualização: 13 de outubro de 2026 · Lei nº 13.709/2018 (LGPD)</p>

      <h2>1. Em resumo</h2>
      <p>Você lê a Arena Diária sem cadastro. Não vendemos nem cedemos dados pessoais. Cookies de medição e de anúncios só funcionam se você aceitar.</p>

      <h2>2. Quais dados tratamos</h2>
      <ul>
        <li><strong>Dados técnicos de acesso</strong>, como endereço IP e navegador, registrados pelo servidor por segurança.</li>
        <li><strong>Sua escolha sobre cookies</strong>, guardada no seu próprio navegador.</li>
        <li><strong>Dados de medição e anúncios</strong> (por exemplo, o Pixel da Meta), apenas se você aceitar os cookies.</li>
        <li><strong>O que você nos escreve</strong> por e-mail, quando decide entrar em contato.</li>
      </ul>

      <h2>3. Para que usamos</h2>
      <ul>
        <li>Manter o site no ar e protegido contra ataques.</li>
        <li>Medir a audiência e o resultado das nossas campanhas de divulgação, se você consentir.</li>
        <li>Responder às suas mensagens.</li>
      </ul>

      <h2 id="cookies">4. Cookies e como mudar sua escolha</h2>
      <p>Na primeira visita, você escolhe entre aceitar ou recusar. A escolha pode ser alterada a qualquer momento:</p>
      <p><button type="button" data-abrir-cookies class="h-11 px-5 rounded-full border border-slate-300 text-sm font-bold text-slate-900 hover:border-teal-700">Rever preferências de cookies</button></p>
      <p>As fontes do site são carregadas do Google Fonts, o que envia ao Google o endereço IP do seu navegador.</p>

      <h2>5. Seus direitos</h2>
      <p>Pelo art. 18 da LGPD, você pode pedir confirmação, acesso, correção, anonimização ou exclusão dos seus dados. Escreva para <a href="mailto:{EMAIL}?subject=Privacidade">{EMAIL}</a> com o assunto “Privacidade”.</p>''')



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
    urls += [(p, HOJE, '0.4') for p in ['quem-somos.html', 'contato.html', 'anuncie.html',
                                         'politica-de-privacidade.html', 'termos-de-uso.html']]
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
  <title>Arena Diária</title>
  <link>{SITE}/</link>
  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>Notícias de futebol, economia do esporte e direitos do consumidor.</description>
  <language>pt-BR</language>
{itens}
</channel>
</rss>
''', encoding='utf-8', newline='\n')


def gerar_llms(ms):
    linhas = '\n'.join(f"- [{m['h1']}]({SITE}/{m['url']}): {m['description']}" for m in ms)
    (RAIZ / 'llms.txt').write_text(f'''# Arena Diária

> Portal de notícias em português do Brasil sobre futebol, economia do esporte e direitos do consumidor. Cada matéria lista as fontes consultadas.

## Editorias
- Futebol: competições, regulamentos e seleções.
- Economia do esporte: patrocínios, tributos e trabalho no setor.
- Consumidor: pagamentos, golpes, direitos e mudanças na lei.

## Matérias
{linhas}

## Institucional
- [Quem somos, expediente e política editorial]({SITE}/quem-somos.html)
- [Todas as notícias]({SITE}/noticias.html)
- [Feed RSS]({SITE}/feed.xml)
- [Contato]({SITE}/contato.html)
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
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
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
<div class="marca">Arena <span>Diária</span></div>
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
    renderizar(capa_html('Portal de notícias', 'Arena Diária', 'Futebol, economia do esporte e direitos do consumidor', None),
               RAIZ / 'assets/images/og-arena-diaria.jpg')
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
