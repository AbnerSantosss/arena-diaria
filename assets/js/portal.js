/**
 * PORTAL IGAMING BRASIL — JAVASCRIPT PRINCIPAL
 * Interatividade, Compliance LGPD, Rastreamento e Utilitários de Imprensa
 */

document.addEventListener('DOMContentLoaded', () => {
  initLiveClockAndDate();
  initBreakingTicker();
  initMobileMenu();
  initCookieConsent();
  initDarkModeToggle();
  initSigapChecker();
  initResponsibleGamingQuiz();
  initCommercialTracking();
  initRandomAds();
});

/* 1. Relógio e Data em Tempo Real no Header */
function initLiveClockAndDate() {
  const dateElement = document.getElementById('headerLiveDate');
  if (!dateElement) return;

  const now = new Date();
  const options = { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  };
  
  // Ex: Terça-feira, 6 de outubro de 2026
  let formatted = now.toLocaleDateString('pt-BR', options);
  formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1);
  dateElement.textContent = formatted;
}

/* 2. Ticker de Plantão / Breaking News Rotativo */
function initBreakingTicker() {
  const tickerText = document.getElementById('tickerText');
  if (!tickerText) return;

  const headlines = [
    "LEI 14.790: Ministério da Fazenda conclui 1ª fase de homologação no SIGAP com recorde de conformidade",
    "FUTEBOL NACIONAL: Contratos de patrocínio máster na Série A ultrapassam R$ 600 milhões anuais",
    "INOVAÇÃO PIX: Banco Central e operadoras validam liquidação de saques em menos de 60 segundos",
    "BEM-ESTAR DIGITAL: Plataformas adotam IA preventiva para impor travas automáticas contra perdas",
    "MERCADO DE TRABALHO: Setor de tecnologia abre 25 mil vagas de engenharia, dados e compliance no país"
  ];

  let currentIndex = 0;
  setInterval(() => {
    currentIndex = (currentIndex + 1) % headlines.length;
    tickerText.style.opacity = 0;
    setTimeout(() => {
      tickerText.textContent = headlines[currentIndex];
      tickerText.style.opacity = 1;
    }, 250);
  }, 4500);
}

/* 3. Menu Mobile Acessível (Touch Targets >= 48px) */
function initMobileMenu() {
  const toggleBtn = document.getElementById('mobileMenuToggle');
  const menuDrawer = document.getElementById('mobileNavDrawer');
  const overlay = document.getElementById('mobileNavOverlay');
  const closeBtn = document.getElementById('mobileMenuClose');

  if (!toggleBtn || !menuDrawer) return;

  function openMenu() {
    menuDrawer.classList.remove('-translate-x-full');
    if (overlay) overlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    menuDrawer.classList.add('-translate-x-full');
    if (overlay) overlay.classList.add('hidden');
    document.body.style.overflow = '';
  }

  toggleBtn.addEventListener('click', openMenu);
  if (closeBtn) closeBtn.addEventListener('click', closeMenu);
  if (overlay) overlay.addEventListener('click', closeMenu);
}

/* 4. Gerenciador de Consentimento LGPD (Cookies) */
function initCookieConsent() {
  const banner = document.getElementById('cookieConsentBanner');
  if (!banner) return;

  const consent = localStorage.getItem('portal_cookie_consent');
  if (!consent) {
    banner.classList.remove('hidden');
  }

  const acceptBtn = document.getElementById('btnAcceptCookies');
  const rejectBtn = document.getElementById('btnRejectCookies');

  if (acceptBtn) {
    acceptBtn.addEventListener('click', () => {
      localStorage.setItem('portal_cookie_consent', 'accepted');
      banner.classList.add('hidden');
    });
  }

  if (rejectBtn) {
    rejectBtn.addEventListener('click', () => {
      localStorage.setItem('portal_cookie_consent', 'essential_only');
      banner.classList.add('hidden');
    });
  }
}

/* 5. Alternador de Modo Escuro / Claro */
function initDarkModeToggle() {
  const toggleBtn = document.getElementById('themeToggleBtn');
  if (!toggleBtn) return;

  const currentTheme = localStorage.getItem('portal_theme') || 'light';
  if (currentTheme === 'dark') {
    document.body.classList.add('dark-mode');
  }

  toggleBtn.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('portal_theme', isDark ? 'dark' : 'light');
  });
}

/* 6. Simulador / Verificador de Concessão SIGAP Fazenda */
function initSigapChecker() {
  const form = document.getElementById('sigapCheckerForm');
  const input = document.getElementById('sigapSearchInput');
  const resultBox = document.getElementById('sigapResultBox');

  if (!form || !input || !resultBox) return;

  // Base demonstrativa de marcas reguladas sob a Lei 14.790
  const authorizedBrands = [
    { name: "Betano", cnpj: "40.320.123/0001-44", outorga: "SIGAP nº 001/2024", dominio: "betano.bet.br", status: "Autorizada (SPA/MF)" },
    { name: "Superbet", cnpj: "48.112.987/0001-12", outorga: "SIGAP nº 002/2024", dominio: "superbet.bet.br", status: "Autorizada (SPA/MF)" },
    { name: "EstrelaBet", cnpj: "43.987.654/0001-89", outorga: "SIGAP nº 003/2024", dominio: "estrelabet.bet.br", status: "Autorizada (SPA/MF)" },
    { name: "Sportingbet", cnpj: "38.543.210/0001-56", outorga: "SIGAP nº 004/2024", dominio: "sportingbet.bet.br", status: "Autorizada (SPA/MF)" },
    { name: "KTO", cnpj: "45.678.901/0001-23", outorga: "SIGAP nº 005/2024", dominio: "kto.bet.br", status: "Autorizada (SPA/MF)" },
    { name: "Betfair", cnpj: "39.123.456/0001-78", outorga: "SIGAP nº 006/2024", dominio: "betfair.bet.br", status: "Autorizada (SPA/MF)" }
  ];

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = input.value.trim().toLowerCase();
    if (!query) return;

    const match = authorizedBrands.find(b => b.name.toLowerCase().includes(query));

    resultBox.classList.remove('hidden');
    if (match) {
      resultBox.innerHTML = `
        <div class="p-4 bg-emerald-50 border border-emerald-300 rounded-lg text-emerald-900">
          <div class="flex items-center gap-2 mb-2">
            <span class="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
            <strong class="text-emerald-800 text-sm font-bold uppercase tracking-wide">✓ Operadora Homologada no SIGAP</strong>
          </div>
          <p class="text-sm font-bold text-slate-900 text-base mb-1">${match.name} (${match.status})</p>
          <ul class="text-xs space-y-1 text-slate-700 mt-2">
            <li><strong>Domínio Licenciado:</strong> <code class="bg-emerald-100 px-1 py-0.5 rounded">${match.dominio}</code></li>
            <li><strong>Portaria Fazenda:</strong> ${match.outorga}</li>
            <li><strong>Segregação Patrimonial:</strong> Auditada e em conformidade com a Lei 14.790/2023</li>
          </ul>
        </div>
      `;
    } else {
      resultBox.innerHTML = `
        <div class="p-4 bg-amber-50 border border-amber-300 rounded-lg text-amber-900">
          <div class="flex items-center gap-2 mb-2">
            <span class="w-3 h-3 rounded-full bg-amber-500"></span>
            <strong class="text-amber-800 text-sm font-bold uppercase tracking-wide">Atenção / Não Localizada no Filtro Rápido</strong>
          </div>
          <p class="text-xs text-slate-700 leading-relaxed">
            A marca digitada não consta no índice rápido das principais operadoras ou pode estar em processo final de publicação na Portaria SPA/MF. 
            Verifique se o site oficial utiliza a terminação <strong>.bet.br</strong> e consulte o site oficial do Ministério da Fazenda.
          </p>
        </div>
      `;
    }
  });
}

/* 7. Teste de Autoavaliação de Jogo Responsável */
function initResponsibleGamingQuiz() {
  const quizForm = document.getElementById('responsibleQuizForm');
  const quizResult = document.getElementById('responsibleQuizResult');
  if (!quizForm || !quizResult) return;

  quizForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const answers = new FormData(quizForm);
    let yesCount = 0;

    for (let value of answers.values()) {
      if (value === 'yes') yesCount++;
    }

    quizResult.classList.remove('hidden');
    let message = '';
    let alertClass = '';

    if (yesCount === 0) {
      alertClass = 'bg-emerald-50 border-emerald-300 text-emerald-900';
      message = `
        <strong class="text-emerald-800 block mb-1">Perfil de Risco: Baixo / Saudável</strong>
        <p class="text-xs">Seu comportamento reflete o uso do entretenimento esportivo como lazer e diversão consciente. Continue mantendo limites rígidos de orçamento e tempo.</p>
      `;
    } else if (yesCount <= 2) {
      alertClass = 'bg-amber-50 border-amber-300 text-amber-900';
      message = `
        <strong class="text-amber-800 block mb-1">Perfil de Risco: Moderado (Atenção Recomendada)</strong>
        <p class="text-xs">Você sinalizou alguns pontos de alerta. Recomendamos ativar ferramentas de limite diário de depósito na sua operadora e estabelecer pausas periódicas.</p>
      `;
    } else {
      alertClass = 'bg-rose-50 border-rose-300 text-rose-900';
      message = `
        <strong class="text-rose-800 block mb-1">Perfil de Risco: Alto (Procure Apoio Especializado)</strong>
        <p class="text-xs">Seus hábitos sugerem potencial desequilíbrio financeiro ou emocional. Recomendamos acionar a autoexclusão temporária e contatar canais gratuitos como <strong>Jogadores Anônimos do Brasil</strong> (jogadoresanonimos.com.br).</p>
      `;
    }

    quizResult.className = `p-4 border rounded-lg mt-4 ${alertClass}`;
    quizResult.innerHTML = message;
  });
}

/* 8. Rastreamento Padronizado de Links Patrocinados (Analytics Compliance) */
function initCommercialTracking() {
  document.querySelectorAll('a[rel*="sponsored"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const partner = link.getAttribute('data-partner') || 'unknown';
      const slot = link.getAttribute('data-slot') || 'native_banner';

      if (window.gtag) {
        window.gtag('event', 'bookmaker_clicked', {
          partner_name: partner,
          slot_location: slot,
          timestamp: new Date().toISOString()
        });
      }
      console.log(`[Analytics Event] bookmaker_clicked -> Parceiro: ${partner}, Slot: ${slot}`);
    });
  });
}


/* 9. Randomize Banners */
function initRandomAds() {
  const adImages = [
    'assets/images/ad-lumea.webp',
    'assets/images/ad-voltix.webp',
    'assets/images/ad-tenis.webp'
  ];
  
  // Find all images that are currently acting as banners
  const banners = document.querySelectorAll('img[src^="assets/images/banner-ads-"]');
  
  banners.forEach(banner => {
    // Pick a random ad
    const randomAd = adImages[Math.floor(Math.random() * adImages.length)];
    banner.src = randomAd;
    banner.alt = "Anúncio do nosso parceiro";
  });
}
