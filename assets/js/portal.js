/* ==========================================================================
   ARENA DIÁRIA — comportamento do portal
   Tudo aqui é aprimoramento: sem JavaScript, links, busca (noticias.html?q=)
   e formulários continuam funcionando.
   ========================================================================== */

/* Índice das matérias publicadas (usado pela busca e pela faixa de destaques).
   Ao publicar uma matéria nova, acrescente uma linha aqui. */
const MATERIAS = [
  {"titulo": "Como funciona o Brasileirão: pontos corridos, rodadas e o que vale cada posição", "resumo": "Pontos corridos, 38 rodadas e muito em jogo: veja como a tabela do Brasileirão define campeão, vagas continentais e rebaixados.", "editoria": "Futebol", "url": "noticia-brasileirao-rodada.html"},
  {"titulo": "Seleção Brasileira: os cinco títulos mundiais, a convocação e o papel da base", "resumo": "Do primeiro título em 1958 ao penta em 2002: como a Seleção é formada, como funciona a data FIFA e por que a base importa.", "editoria": "Futebol", "url": "noticia-selecao-brasileira.html"},
  {"titulo": "Do master ao estádio: como as marcas chegam à camisa do seu time", "resumo": "Do master da camisa ao nome do estádio: como funciona o patrocínio no futebol e quais setores mais investem nos clubes brasileiros.", "editoria": "Economia do esporte", "url": "noticia-patrocinios-futebol.html"},
  {"titulo": "Pix e apostas: o que a MP 1.394 muda para bancos e para o seu dinheiro", "resumo": "Bancos não podem mais processar pagamentos de apostas, nem por Pix. Entenda as regras da MP 1.394 e como o saldo volta para você.", "editoria": "Consumidor", "url": "noticia-pix-saque-rapido.html"},
  {"titulo": "Para onde ia o dinheiro das bets e o que a MP 1.394 faz com essas receitas", "resumo": "Esporte, turismo, segurança, educação e saúde dividiam a arrecadação das bets. Veja os percentuais da lei e o efeito da MP 1.394.", "editoria": "Economia do esporte", "url": "noticia-tributacao-saude.html"},
  {"titulo": "Lista de bets autorizadas virou registro histórico: o que mudou com a MP", "resumo": "A lista oficial de bets e o .bet.br não indicam mais quem pode operar. Veja como funciona o bloqueio e o que muda para o consumidor.", "editoria": "Consumidor", "url": "noticia-plataformas-autorizadas.html"},
  {"titulo": "Redes, buscadores e lojas de apps passam a responder por anúncios de bets", "resumo": "Redes, buscadores e lojas de apps agora respondem por anúncios de bets. Veja o que a MP 1.394 exige, as multas e como denunciar.", "editoria": "Consumidor", "url": "noticia-inteligencia-artificial.html"},
  {"titulo": "Fim das bets: o que muda para quem trabalha no setor e no entorno", "resumo": "Empresas, afiliados, influenciadores e agências perdem uma atividade com a MP 1.394. Veja as regras e os riscos de continuar.", "editoria": "Economia do esporte", "url": "noticia-geracao-empregos.html"},
  {"titulo": "Proibição das bets: o que muda com a MP 1.394 e como o saldo volta ao apostador", "resumo": "Entenda a MP 1.394/2026: o que foi proibido, as datas do cronograma oficial e como funciona a devolução do saldo aos apostadores.", "editoria": "Consumidor", "url": "noticia-proibicao-bets-brasil.html"}
];

/* E-mail que recebe as mensagens do formulário de contato. */
const EMAIL_CONTATO = 'redacao@arenadiaria.com.br';

/* ID do Pixel da Meta (Gerenciador de Eventos). Vazio = pixel desligado.
   O pixel só carrega depois que o leitor aceita os cookies. */
const META_PIXEL_ID = '';

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
  const texto = hoje.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' });
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
        : `<p class="px-4 py-3 text-sm text-slate-600">Nenhuma matéria encontrada para “${escaparHtml(termo)}”.</p>`;
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
    if (!palavras.length) aviso.textContent = `${itens.length} matérias publicadas.`;
    else if (visiveis) aviso.textContent = `${visiveis} ${visiveis === 1 ? 'matéria encontrada' : 'matérias encontradas'} para “${termo}”.`;
    else aviso.textContent = `Nenhuma matéria encontrada para “${termo}”. Tente outra palavra.`;
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
    botao.setAttribute('aria-label', pausado ? 'Retomar a troca de destaques' : 'Pausar a troca de destaques');
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

/* 6. Teste de autoavaliação (Jogo responsável) */
/* 7. Compartilhar e copiar link */
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
        if (status) status.textContent = 'Link copiado.';
      } catch (e) {
        if (status && e.name !== 'AbortError') status.textContent = `Não deu para copiar. O endereço é ${url}`;
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
    const assunto = `[${dados.get('assunto')}] Mensagem de ${dados.get('nome')}`;
    const corpo = `${dados.get('mensagem')}\n\n—\n${dados.get('nome')}\n${dados.get('email')}`;
    window.location.href = `mailto:${EMAIL_CONTATO}?subject=${encodeURIComponent(assunto)}&body=${encodeURIComponent(corpo)}`;
    status.textContent = `Abrimos o seu aplicativo de e-mail com a mensagem pronta. Se ele não abriu, escreva para ${EMAIL_CONTATO}.`;
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
});
