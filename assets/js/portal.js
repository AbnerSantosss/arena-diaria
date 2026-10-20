/* ==========================================================================
   ARENA DIÁRIA — comportamento do portal
   Tudo aqui é aprimoramento: sem JavaScript, links, busca (noticias.html?q=)
   e formulários continuam funcionando.
   ========================================================================== */

/* Índice das matérias publicadas (usado pela busca e pela faixa de destaques).
   Ao publicar uma matéria nova, acrescente uma linha aqui. */
const MATERIAS = [
  {"titulo": "Cómo funciona el Brasileirão: todos contra todos, fechas y qué vale cada posición", "resumo": "Todos contra todos, 38 fechas y mucho en juego: mirá cómo la tabla del Brasileirão define al campeón, los cupos continentales y los descensos.", "editoria": "Fútbol", "url": "noticia-brasileirao-rodada.html"},
  {"titulo": "Selección de Brasil: los cinco títulos mundiales, la convocatoria y el papel de las inferiores", "resumo": "Del primer título en 1958 al penta en 2002: cómo se arma la Selección, cómo funciona la fecha FIFA y por qué importan las inferiores.", "editoria": "Fútbol", "url": "noticia-selecao-brasileira.html"},
  {"titulo": "Cómo funciona la Copa de Brasil: fases, desempate y cupo a la Libertadores", "resumo": "Nueve fases, 126 clubes y sin gol de visitante: mirá cómo la Copa de Brasil define quién avanza y quién va a la Libertadores.", "editoria": "Fútbol", "url": "noticia-copa-do-brasil.html"},
  {"titulo": "Cómo funciona la Libertadores: de las fases preliminares a la final a partido único", "resumo": "Fases preliminares, grupos, eliminación directa y final única: mirá el camino hasta la copa y cómo entran los brasileños a la Libertadores.", "editoria": "Fútbol", "url": "noticia-libertadores.html"},
  {"titulo": "Del sponsor principal al estadio: cómo llegan las marcas a la camiseta de tu equipo", "resumo": "Del sponsor principal de la camiseta al nombre del estadio: cómo funciona el patrocinio en el fútbol y qué sectores más invierten en los clubes brasileños.", "editoria": "Economía del deporte", "url": "noticia-patrocinios-futebol.html"},
  {"titulo": "Derechos de transmisión en el fútbol: qué dice la ley del local y cómo negocian los clubes", "resumo": "¿Quién le vende el partido a la TV? Mirá qué cambió con la ley del local y cómo los clubes negocian en bloques y discuten una liga.", "editoria": "Economía del deporte", "url": "noticia-direitos-de-transmissao.html"},
  {"titulo": "Qué es la SAF: cómo el club se vuelve empresa y qué pasa con las deudas", "resumo": "¿El club se volvió empresa? Mirá cómo funciona la SAF, qué pasa con las deudas anteriores y qué garantías le da la ley al hincha.", "editoria": "Economía del deporte", "url": "noticia-saf-sociedade-anonima-futebol.html"},
  {"titulo": "Entradas para partidos de fútbol: los derechos de quien compra el ticket", "resumo": "Entrada numerada, precio impreso, media entrada y reembolso: conocé los derechos de quien compra una entrada para el estadio.", "editoria": "Consumidor", "url": "noticia-ingressos-direitos-torcedor.html"},
  {"titulo": "Estafas con Pix: cómo protegerte y cómo pedir el dinero de vuelta por el MED", "resumo": "¿Caíste en una estafa con Pix? Mirá cómo usar el botón de contestación, cuál es el plazo del MED y qué hacer para intentar recuperar el dinero.", "editoria": "Consumidor", "url": "noticia-pix-golpes-med.html"}
];

/* E-mail que recebe as mensagens do formulário de contato. */
const EMAIL_CONTATO = 'redacao@arenadiaria.com.br';

/* ID do Pixel da Meta (Gerenciador de Eventos). Vazio = pixel desligado.
   O pixel só carrega depois que o leitor aceita os cookies. */
const META_PIXEL_ID = '1879343259722567';

const reduzMovimento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function armazenamento(acao, chave, valor) {
  try {
    if (acao === 'ler') return window.localStorage.getItem(chave);
    window.localStorage.setItem(chave, valor);
  } catch (e) {
    return null; /* navegação privada ou armazenamento bloqueado */
  }
  return null;
}

function normalizar(texto) {
  return (texto || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
}

function escaparHtml(texto) {
  const div = document.createElement('div');
  div.textContent = texto;
  return div.innerHTML;
}

function buscarMaterias(termo) {
  const palavras = normalizar(termo).split(/\s+/).filter(Boolean);
  if (!palavras.length) return [];
  return MATERIAS.filter((m) => {
    const alvo = normalizar(`${m.titulo} ${m.resumo} ${m.editoria}`);
    return palavras.every((p) => alvo.includes(p));
  });
}

/* 1. Data de hoje no cabeçalho */
function initData() {
  const alvo = document.getElementById('headerLiveDate');
  if (!alvo) return;
  const hoje = new Date();
  const texto = hoje.toLocaleDateString('es-AR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' });
  alvo.textContent = texto.charAt(0).toUpperCase() + texto.slice(1);
  alvo.setAttribute('datetime', hoje.toISOString().slice(0, 10));
}

/* 2. Busca com sugestões (o formulário envia para noticias.html?q=) */
function initBusca() {
  document.querySelectorAll('[data-busca-form]').forEach((form) => {
    const campo = form.querySelector('input[type="search"]');
    const lista = form.querySelector('.busca-resultados');
    if (!campo || !lista) return;

    const fechar = () => { lista.hidden = true; campo.setAttribute('aria-expanded', 'false'); };

    campo.addEventListener('input', () => {
      const termo = campo.value.trim();
      if (termo.length < 2) { fechar(); return; }
      const achadas = buscarMaterias(termo).slice(0, 6);
      lista.innerHTML = achadas.length
        ? achadas.map((m) => `<a href="${m.url}"><span class="block text-xs font-bold uppercase text-teal-700">${escaparHtml(m.editoria)}</span><span class="block text-sm font-semibold text-slate-900">${escaparHtml(m.titulo)}</span></a>`).join('')
        : `<p class="px-4 py-3 text-sm text-slate-600">No se encontraron notas para “${escaparHtml(termo)}”.</p>`;
      lista.hidden = false;
      campo.setAttribute('aria-expanded', 'true');
    });

    campo.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') fechar();
      if (e.key === 'ArrowDown') {
        const primeiro = lista.querySelector('a');
        if (primeiro && !lista.hidden) { e.preventDefault(); primeiro.focus(); }
      }
    });
    lista.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { fechar(); campo.focus(); }
    });
    document.addEventListener('click', (e) => { if (!form.contains(e.target)) fechar(); });
  });

  /* Botão de busca no celular abre/fecha o painel */
  const botao = document.getElementById('buscaToggle');
  const painel = document.getElementById('buscaPainel');
  if (botao && painel) {
    botao.addEventListener('click', () => {
      const abrir = painel.hidden;
      painel.hidden = !abrir;
      botao.setAttribute('aria-expanded', String(abrir));
      if (abrir) painel.querySelector('input').focus();
    });
  }
}

/* 3. Página "Todas as notícias": filtra a lista por ?q= */
function initListaNoticias() {
  const itens = document.querySelectorAll('[data-materia]');
  const aviso = document.getElementById('buscaStatus');
  const campo = document.getElementById('buscaPagina');
  if (!itens.length || !aviso) return;

  const aplicar = (termo) => {
    const palavras = normalizar(termo).split(/\s+/).filter(Boolean);
    let visiveis = 0;
    itens.forEach((item) => {
      const alvo = normalizar(item.textContent);
      const mostra = palavras.every((p) => alvo.includes(p));
      item.hidden = !mostra;
      if (mostra) visiveis++;
    });
    if (!palavras.length) aviso.textContent = `${itens.length} notas publicadas.`;
    else if (visiveis) aviso.textContent = `${visiveis} ${visiveis === 1 ? 'nota encontrada' : 'notas encontradas'} para “${termo}”.`;
    else aviso.textContent = `No se encontraron notas para “${termo}”. Probá con otra palabra.`;
  };

  const termoInicial = new URLSearchParams(window.location.search).get('q') || '';
  if (campo) {
    campo.value = termoInicial;
    campo.addEventListener('input', () => aplicar(campo.value.trim()));
  }
  aplicar(termoInicial.trim());
}

/* 4. Faixa de destaques: troca a cada 7 s, com pausa; parada se o usuário reduz movimento */
function initDestaques() {
  const link = document.getElementById('tickerText');
  const botao = document.getElementById('tickerPausa');
  // A faixa mostra só as 5 primeiras: as do fim da lista ficam fora do topo de propósito
  const destaques = MATERIAS.slice(0, 5);
  if (!link || destaques.length < 2) return;

  let indice = 0;
  let pausado = reduzMovimento;
  let timer = null;

  const mostrar = (i) => {
    const m = destaques[i];
    link.style.opacity = 0;
    setTimeout(() => {
      link.textContent = m.titulo;
      link.href = m.url;
      link.style.opacity = 1;
    }, reduzMovimento ? 0 : 250);
  };
  const iniciar = () => {
    clearInterval(timer);
    if (pausado) return;
    timer = setInterval(() => { indice = (indice + 1) % destaques.length; mostrar(indice); }, 7000);
  };
  const atualizarBotao = () => {
    if (!botao) return;
    botao.setAttribute('aria-pressed', String(pausado));
    botao.setAttribute('aria-label', pausado ? 'Reanudar el cambio de destacadas' : 'Pausar el cambio de destacadas');
    botao.querySelector('[data-icone]').textContent = pausado ? '▶' : '❚❚';
  };

  if (botao) {
    botao.addEventListener('click', () => { pausado = !pausado; atualizarBotao(); iniciar(); });
  }
  const faixa = link.closest('.ticker-container');
  if (faixa) {
    faixa.addEventListener('mouseenter', () => clearInterval(timer));
    faixa.addEventListener('mouseleave', iniciar);
    faixa.addEventListener('focusin', () => clearInterval(timer));
    faixa.addEventListener('focusout', iniciar);
  }
  atualizarBotao();
  iniciar();
}

/* 5. Consentimento de cookies (escolhas com o mesmo peso) */
function initCookies() {
  const banner = document.getElementById('cookieConsentBanner');
  if (!banner) return;
  const escolha = armazenamento('ler', 'arena_cookies');
  window.arenaConsentimento = escolha;

  const fechar = (valor) => {
    armazenamento('gravar', 'arena_cookies', valor);
    window.arenaConsentimento = valor;
    banner.hidden = true;
    document.dispatchEvent(new CustomEvent('arena:consentimento', { detail: valor }));
  };
  if (!escolha) banner.hidden = false;

  banner.querySelector('[data-cookie="aceitar"]').addEventListener('click', () => fechar('aceito'));
  banner.querySelector('[data-cookie="recusar"]').addEventListener('click', () => fechar('recusado'));

  document.querySelectorAll('[data-abrir-cookies]').forEach((b) => {
    b.addEventListener('click', () => { banner.hidden = false; banner.querySelector('button').focus(); });
  });
}

/* 6. Compartilhar e copiar link */
function initCompartilhar() {
  document.querySelectorAll('[data-copiar-link]').forEach((botao) => {
    const status = document.getElementById(botao.getAttribute('aria-describedby'));
    botao.addEventListener('click', async () => {
      const url = botao.dataset.copiarLink || window.location.href;
      try {
        if (navigator.share && window.matchMedia('(pointer: coarse)').matches) {
          await navigator.share({ title: document.title, url });
          return;
        }
        await navigator.clipboard.writeText(url);
        if (status) status.textContent = 'Enlace copiado.';
      } catch (e) {
        if (status && e.name !== 'AbortError') status.textContent = `No se pudo copiar. La dirección es ${url}`;
      }
    });
  });
}

/* 8. Formulário de contato: abre o e-mail do leitor com a mensagem pronta */
function initContato() {
  const form = document.getElementById('formContato');
  const status = document.getElementById('contatoStatus');
  if (!form || !status) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const dados = new FormData(form);
    const assunto = `[${dados.get('assunto')}] Mensaje de ${dados.get('nome')}`;
    const corpo = `${dados.get('mensagem')}\n\n—\n${dados.get('nome')}\n${dados.get('email')}`;
    window.location.href = `mailto:${EMAIL_CONTATO}?subject=${encodeURIComponent(assunto)}&body=${encodeURIComponent(corpo)}`;
    status.textContent = `Abrimos tu aplicación de correo con el mensaje listo. Si no se abrió, escribí a ${EMAIL_CONTATO}.`;
  });
}

/* 9. Cliques em publicidade (só registra se houver analytics e consentimento) */
function initPublicidade() {
  document.querySelectorAll('[data-slot]').forEach((link) => {
    link.addEventListener('click', () => {
      if (window.gtag && window.arenaConsentimento === 'aceito') {
        window.gtag('event', 'ad_click', { slot_location: link.dataset.slot });
      }
    });
  });
}

/* 10. Medição de audiência: Pixel da Meta só com consentimento */
function initMedicao() {
  const carregar = () => {
    if (!META_PIXEL_ID || window.fbq) return;
    /* eslint-disable */
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    /* eslint-enable */
    window.fbq('init', META_PIXEL_ID);
    window.fbq('track', 'PageView');
    const artigo = document.querySelector('meta[property="article:section"]');
    if (artigo) window.fbq('track', 'ViewContent', { content_category: artigo.content, content_type: 'article' });
  };
  if (window.arenaConsentimento === 'aceito') carregar();
  document.addEventListener('arena:consentimento', (e) => { if (e.detail === 'aceito') carregar(); });
}

/* 11. Billboard animado: toca o vídeo do HyperFrames por cima da imagem (que segue como base e fallback) */
function initBillboardAnimado() {
  const link = document.querySelector('.billboard-link[data-video-mp4]');
  if (!link || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const desktop = window.matchMedia('(min-width: 768px)').matches;
  const d = link.dataset;
  const fontes = desktop ? [[d.videoWebm, 'video/webm'], [d.videoMp4, 'video/mp4']]
    : [[d.videoWebmMovel, 'video/webm'], [d.videoMp4Movel, 'video/mp4']];
  const video = document.createElement('video');
  video.className = 'billboard-video';
  video.muted = true;
  video.playsInline = true;
  video.preload = 'auto';
  video.setAttribute('aria-hidden', 'true');
  fontes.filter(([src]) => src).forEach(([src, tipo]) => {
    const fonte = document.createElement('source');
    fonte.src = src;
    fonte.type = tipo;
    video.appendChild(fonte);
  });
  if (!video.children.length) return;
  let voltas = 0;
  video.addEventListener('ended', () => {
    voltas += 1;
    if (voltas < 3) setTimeout(() => video.play().catch(() => {}), 4000);
  });
  video.addEventListener('playing', () => video.classList.add('visivel'), { once: true });
  link.appendChild(video);
  video.play().catch(() => video.remove());
}

/* 12. Carrossel da home: três anúncios, com pausa no foco e suporte a movimento reduzido. */
function initCarrosselAnuncios() {
  const carrossel = document.querySelector('[data-ad-carousel]');
  if (!carrossel) return;
  const slides = [...carrossel.querySelectorAll('.billboard-slide')];
  const pontos = [...carrossel.querySelectorAll('[data-ad-goto]')];
  const anterior = carrossel.querySelector('[data-ad-prev]');
  const proximo = carrossel.querySelector('[data-ad-next]');
  const alternar = carrossel.querySelector('[data-ad-toggle]');
  if (slides.length < 2) return;

  let indice = 0;
  let pausado = reduzMovimento;
  let timer = null;
  const mostrar = (novo) => {
    indice = (novo + slides.length) % slides.length;
    slides.forEach((slide, i) => { slide.hidden = i !== indice; });
    pontos.forEach((ponto, i) => ponto.setAttribute('aria-pressed', String(i === indice)));
    carrossel.setAttribute('aria-label', `Publicidad, anuncio ${indice + 1} de ${slides.length}`);
  };
  const sincronizarBotao = () => {
    if (!alternar) return;
    alternar.setAttribute('aria-pressed', String(pausado));
    alternar.setAttribute('aria-label', pausado ? 'Reanudar anuncios' : 'Pausar anuncios');
    alternar.textContent = pausado ? '▶' : 'Ⅱ';
  };
  const iniciar = () => {
    clearInterval(timer);
    if (!pausado && !document.hidden) timer = setInterval(() => mostrar(indice + 1), 6500);
  };

  anterior?.addEventListener('click', () => { mostrar(indice - 1); iniciar(); });
  proximo?.addEventListener('click', () => { mostrar(indice + 1); iniciar(); });
  pontos.forEach((ponto) => ponto.addEventListener('click', () => {
    mostrar(Number(ponto.dataset.adGoto));
    iniciar();
  }));
  alternar?.addEventListener('click', () => {
    pausado = !pausado;
    sincronizarBotao();
    iniciar();
  });
  carrossel.addEventListener('mouseenter', () => clearInterval(timer));
  carrossel.addEventListener('mouseleave', iniciar);
  carrossel.addEventListener('focusin', () => clearInterval(timer));
  carrossel.addEventListener('focusout', (event) => {
    if (!carrossel.contains(event.relatedTarget)) iniciar();
  });
  document.addEventListener('visibilitychange', iniciar);
  mostrar(0);
  sincronizarBotao();
  iniciar();
}

document.addEventListener('DOMContentLoaded', () => {
  initData();
  initBusca();
  initListaNoticias();
  initDestaques();
  initCookies();
  initCompartilhar();
  initContato();
  initMedicao();
  initPublicidade();
  initBillboardAnimado();
  initCarrosselAnuncios();
});
