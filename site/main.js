/* Casa do Caminho — interações (versão 2)
   Um IIFE só. A única dependência é o Lenis (scroll suave), e a página
   funciona sem ele. Os efeitos de scroll escrevem variáveis CSS (--p, --o);
   o desenho está em styles.css. */
(function () {
  'use strict';

  var reduzido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var limita = function (v, a, b) { return Math.min(b, Math.max(a, v)); };
  var temIO = 'IntersectionObserver' in window;

  /* ------------------------------------------------------------
     CATÁLOGO DE FOTOGRAFIAS (o visor)
     { f: 'ficheiro sem extensão', l: 'legenda' }. Os ficheiros estão em
     assets/img/ com as cópias -800 e -1400 (scripts/imagens.py).
     Um botão com data-foto="<nome>" abre o visor nessa fotografia, na
     série data-serie. As quatro divisões («Interior») são um grupo: no
     visor aparecem como separadores, para saltar de uma para outra.
     ------------------------------------------------------------ */
  // d: a divisão, que o visor mostra a negrito antes da legenda. Os dois
  // quartos e as duas casas de banho separam-se pelo que se vê nas fotos
  // (o quarto 2 é o da parede de pedra; a casa de banho 1 é a da pedra).
  // Que casa de banho é de que quarto não se sabe: confirmar com o dono.
  var CASA = [
    { f: 'quarto-flores', d: 'Quarto 1', l: 'A cama, pronta a receber' },
    { f: 'quarto-portadas', d: 'Quarto 1', l: 'A cama junto à porta-janela, com portadas de madeira' },
    { f: 'janela-granito', d: 'Quarto 1', l: 'A porta-janela aberta na parede de granito' },
    { f: 'quarto-roupeiro', d: 'Quarto 1', l: 'O roupeiro, a secretária e a porta-janela' },
    { f: 'quarto-claro', d: 'Quarto 1', l: 'O roupeiro, a televisão e a porta-janela' },
    { f: 'quarto-terraco', d: 'Quarto 2', l: 'A cama de casal, o roupeiro e a porta-janela' },
    { f: 'quarto-pedra', d: 'Quarto 2', l: 'A parede de pedra, com janela e portada' },
    { f: 'quarto-janelas', d: 'Quarto 2', l: 'Paredes de pedra, janela e porta-janela' },
    { f: 'sala-jantar', l: 'A sala: a mesa grande, entre paredes de pedra' },
    { f: 'sala-estar', l: 'A sala: os sofás, junto à parede de pedra' },
    { f: 'sala-sofa', l: 'A sala: sofá, mesa e a parede de pedra iluminada' },
    { f: 'sala-cozinha', l: 'A mesa de jantar, com a cozinha ao fundo' },
    { f: 'cozinha', l: 'A cozinha equipada' },
    { f: 'wc-pedra', d: 'Casa de banho 1', l: 'A parede de pedra e o espelho redondo' },
    { f: 'wc-espelho', d: 'Casa de banho 1', l: 'O duche e o lavatório, junto à pedra' },
    { f: 'wc-duche', d: 'Casa de banho 2', l: 'O duche de vidro e o lavatório de pousar' },
    { f: 'wc-madeira', d: 'Casa de banho 2', l: 'Paredes em tons de madeira e lavatório de pousar' },
    { f: 'alpendre-aberto', l: 'O alpendre: a mesa, a churrasqueira e o vale' },
    { f: 'mesa-posta', l: 'A mesa posta no alpendre, de frente para os campos' },
    { f: 'escadas-granito', l: 'As escadas de granito, do jardim para o alpendre' },
    { f: 'muros-escadas', l: 'O muro de granito e as escadas que sobem para a casa' },
    { f: 'alpendre', l: 'O alpendre coberto, com a churrasqueira ao fundo' },
    { f: 'hero-casa', l: 'A esquina de granito, com o telhado de telha' },
    { f: 'pergola-sol', l: 'A pérgola ao sol, à porta dos quartos' },
    { f: 'hero-pergola', l: 'A casa ao sol, debaixo da pérgola' },
    { f: 'granito-potes', l: 'Os potes de ferro em cima do muro' }
  ];
  var porNome = function (f) { return CASA.filter(function (c) { return c.f === f; })[0]; };
  var serieDe = function (lista) { return lista.map(porNome); };
  // grupo: as séries do mesmo grupo aparecem como separadores no visor
  var SERIES = {
    lafora: { nome: 'Exterior', fotos: serieDe(['mesa-posta', 'alpendre-aberto', 'muros-escadas', 'escadas-granito', 'pergola-sol', 'hero-pergola', 'alpendre', 'hero-casa', 'granito-potes']) },
    quartos: { grupo: 1, nome: 'Os quartos', fotos: serieDe(['quarto-flores', 'quarto-portadas', 'quarto-roupeiro', 'quarto-claro', 'quarto-terraco', 'quarto-pedra', 'quarto-janelas']) },
    sala: { grupo: 1, nome: 'A sala', fotos: serieDe(['sala-jantar', 'sala-sofa', 'sala-estar', 'sala-cozinha']) },
    cozinha: { grupo: 1, nome: 'A cozinha', fotos: serieDe(['cozinha', 'sala-cozinha']) },
    banho: { grupo: 1, nome: 'As casas de banho', fotos: serieDe(['wc-pedra', 'wc-espelho', 'wc-duche', 'wc-madeira']) }
  };
  $$('[data-conta]').forEach(function (el) { var s = SERIES[el.dataset.conta]; if (s) el.textContent = s.fotos.length; });

  var img = function (f, t) { return 'assets/img/' + f + (t ? '-' + t : '') + '.jpg'; };

  /* ------------------------------------------------------------
     SCROLL SUAVE (Lenis, do jsDelivr). Sem ele, ou com movimento
     reduzido, fica o scroll normal. O menu e o visor param-no.
     ------------------------------------------------------------ */
  var lenis = null;
  if (window.Lenis && !reduzido) {
    lenis = new window.Lenis({ lerp: 0.1, anchors: true, autoRaf: true });
  }
  function bloqueia(sim) {
    document.body.style.overflow = sim ? 'hidden' : '';
    if (lenis) { if (sim) lenis.stop(); else lenis.start(); }
  }

  /* ------------------------------------------------------------
     TOPO: sólido assim que se desce (o painel do hero tem texto por
     baixo); esconde-se a descer e volta a subir.
     ------------------------------------------------------------ */
  var topo = $('#topo'), menu = $('#menu');
  var ultimoY = window.scrollY;
  function atualizaTopo() {
    var y = window.scrollY;
    var limite = 60;
    topo.classList.toggle('is-solido', y > limite);
    if (!topo.classList.contains('menu-aberto')) topo.classList.toggle('is-escondido', y > ultimoY && y > limite + 200);
    ultimoY = y;
  }
  function fechaMenu() {
    topo.classList.remove('menu-aberto');
    menu.setAttribute('aria-expanded', 'false');
    menu.setAttribute('aria-label', 'Abrir o menu');
    bloqueia(false);
  }
  menu.addEventListener('click', function () {
    var aberto = topo.classList.toggle('menu-aberto');
    menu.setAttribute('aria-expanded', aberto);
    menu.setAttribute('aria-label', aberto ? 'Fechar o menu' : 'Abrir o menu');
    bloqueia(aberto);
  });
  $$('#nav a').forEach(function (a) { a.addEventListener('click', function () { if (topo.classList.contains('menu-aberto')) fechaMenu(); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && topo.classList.contains('menu-aberto')) { fechaMenu(); menu.focus(); } });

  // ligação ativa no menu
  var ligacoes = $$('.nav ul a');
  if (temIO) {
    var ioNav = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        ligacoes.forEach(function (a) { a.classList.toggle('is-ativo', a.getAttribute('href') === '#' + e.target.id); });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    ['casa', 'exterior', 'interior', 'arredores'].forEach(function (id) { var s = document.getElementById(id); if (s) ioNav.observe(s); });
  }

  /* ------------------------------------------------------------
     HERO: o título entra palavra a palavra.
     ------------------------------------------------------------ */
  $$('[data-palavras]').forEach(function (el) {
    var k = 0;
    (function parte(no) {
      Array.prototype.slice.call(no.childNodes).forEach(function (n) {
        if (n.nodeType === 1) { parte(n); return; }
        if (n.nodeType !== 3) return;
        var frag = document.createDocumentFragment();
        n.textContent.split(/(\s+)/).forEach(function (b) {
          if (!b) return;
          if (/^\s+$/.test(b)) { frag.appendChild(document.createTextNode(' ')); return; }
          var fora = document.createElement('span'), dentro = document.createElement('span');
          fora.className = 'pal'; dentro.textContent = b;
          dentro.style.animationDelay = (0.25 + k++ * 0.075).toFixed(3) + 's';
          fora.appendChild(dentro); frag.appendChild(fora);
        });
        no.replaceChild(frag, n);
      });
    })(el);
  });

  /* ------------------------------------------------------------
     APARECER AO DESCER (.reveal) e FOTOS QUE SE REVELAM ([data-revela])
     ------------------------------------------------------------ */
  function aoEntrar(lista, margem) {
    if (reduzido || !temIO) { lista.forEach(function (el) { el.classList.add('is-visivel'); }); return; }
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('is-visivel');
        io.unobserve(e.target);
      });
    }, { rootMargin: margem, threshold: 0.08 });
    lista.forEach(function (el) { io.observe(el); });
  }
  $$('.reveal').forEach(function (el, i) { el.style.transitionDelay = ((i % 4) * 0.08) + 's'; });
  aoEntrar($$('.reveal'), '0px 0px -8% 0px');
  aoEntrar($$('[data-revela]'), '0px 0px -10% 0px');

  /* ------------------------------------------------------------
     TONS: o fundo da página toma o tom da secção que está no meio do
     ecrã (data-fundo; a transição está no CSS do body).
     ------------------------------------------------------------ */
  var comTom = $$('[data-fundo]');
  if (comTom.length && temIO) {
    document.documentElement.setAttribute('data-fundo', 'papel');
    var ioTom = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) document.documentElement.setAttribute('data-fundo', e.target.getAttribute('data-fundo')); });
    }, { rootMargin: '-50% 0px -50% 0px' });
    comTom.forEach(function (s) { ioTom.observe(s); });
  }

  /* ------------------------------------------------------------
     TEXTO QUE SE ACENDE ([data-acende]): cada palavra passa de apagada
     a acesa à medida que a frase sobe no ecrã. O texto continua inteiro
     para leitores de ecrã.
     ------------------------------------------------------------ */
  function partePalavras(no) {
    Array.prototype.slice.call(no.childNodes).forEach(function (n) {
      if (n.nodeType === 1) { partePalavras(n); return; }
      if (n.nodeType !== 3) return;
      var frag = document.createDocumentFragment();
      n.textContent.split(/(\s+)/).forEach(function (b) {
        if (!b) return;
        if (/^\s+$/.test(b)) { frag.appendChild(document.createTextNode(b)); return; }
        var s = document.createElement('span');
        s.className = 'p'; s.textContent = b;
        frag.appendChild(s);
      });
      no.replaceChild(frag, n);
    });
  }
  var acende = reduzido ? [] : $$('[data-acende]').map(function (el) {
    partePalavras(el);
    return { el: el, ps: $$('.p', el) };
  });
  var MIN_ACESO = 0.15, JANELA = 4;
  function atualizaAcende(vh) {
    acende.forEach(function (a) {
      var r = a.el.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) return;
      var p = limita((vh * 0.88 - r.top) / (vh * 0.42 + r.height), 0, 1);
      var n = a.ps.length, pos = p * (n + JANELA);
      a.ps.forEach(function (s, k) {
        s.style.setProperty('--o', (MIN_ACESO + (1 - MIN_ACESO) * limita((pos - k) / JANELA, 0, 1)).toFixed(3));
      });
    });
  }

  /* ------------------------------------------------------------
     FOTO QUE CRESCE (#cresce): a secção tem 260vh e o palco fica preso;
     --p vai de 0 a 1 nos primeiros 70% do percurso.
     ------------------------------------------------------------ */
  var cresce = $('#cresce');
  var suave = function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  function atualizaCresce(vh) {
    if (!cresce || reduzido) return;
    var r = cresce.getBoundingClientRect();
    if (r.bottom < -50 || r.top > vh + 50) return;
    var percurso = Math.max(1, r.height - vh);
    cresce.style.setProperty('--p', suave(limita(-r.top / (percurso * 0.7), 0, 1)).toFixed(4));
  }

  /* ------------------------------------------------------------
     PARALLAX ([data-parallax]): a foto de abertura do «Interior».
     ------------------------------------------------------------ */
  var parallax = reduzido ? [] : $$('[data-parallax]');
  function atualizaParallax(vh) {
    parallax.forEach(function (el) {
      var r = el.parentNode.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) return;
      var p = limita((r.top + r.height / 2 - vh / 2) / (vh / 2 + r.height / 2), -1, 1);
      el.style.transform = 'translate3d(0,' + (-p * r.height * 0.07).toFixed(1) + 'px,0)';
    });
  }

  /* ------------------------------------------------------------
     RESERVAR: a foto entra recortada em arco e abre-se até ocupar a
     secção. --p vai de 0 (a secção a entrar) a 1 (já enquadrada).
     ------------------------------------------------------------ */
  var reservar = $('#reservar');
  if (reservar && !reduzido) reservar.style.setProperty('--p', '0');
  function atualizaReservar(vh) {
    if (!reservar || reduzido) return;
    var r = reservar.getBoundingClientRect();
    if (r.top > vh + 50 || r.bottom < -50) return;
    reservar.style.setProperty('--p', limita((vh - r.top) / (vh * 0.85), 0, 1).toFixed(3));
  }

  /* ------------------------------------------------------------
     RESERVAR fixo no telemóvel: depois do hero, até chegar às reservas.
     ------------------------------------------------------------ */
  var cta = $('#ctaFixo');
  function atualizaCta(vh) {
    var r = reservar.getBoundingClientRect();
    cta.classList.toggle('is-visivel', window.scrollY > vh * 0.9 && r.top > vh * 0.6 && !topo.classList.contains('menu-aberto'));
  }

  /* ------------------------------------------------------------
     CICLO DE SCROLL
     ------------------------------------------------------------ */
  var pedido = false;
  function quadro() {
    pedido = false;
    var vh = window.innerHeight;
    atualizaTopo();
    atualizaAcende(vh);
    atualizaCresce(vh);
    atualizaParallax(vh);
    atualizaReservar(vh);
    atualizaCta(vh);
  }
  function pede() { if (!pedido) { pedido = true; requestAnimationFrame(quadro); } }
  window.addEventListener('scroll', pede, { passive: true });
  window.addEventListener('resize', pede);
  window.addEventListener('load', pede);
  quadro();

  /* ------------------------------------------------------------
     ACORDEÃO DAS DIVISÕES: a abertura ao passar o rato é CSS. Aqui, o
     teclado e o toque: sem rato, o primeiro toque abre o painel e o
     segundo abre o visor.
     ------------------------------------------------------------ */
  var paineis = $$('.acordeao__painel');
  paineis.forEach(function (p) {
    var abrePainel = function () { paineis.forEach(function (o) { o.classList.toggle('is-aberto', o === p); }); };
    p.addEventListener('focus', abrePainel);
    p.addEventListener('mouseenter', abrePainel);
    // no toque, o foco e o mouseenter chegam antes do click e já abrem o
    // painel: conta como estava quando o dedo tocou
    var antes = null;
    p.addEventListener('pointerdown', function (e) { antes = e.pointerType === 'mouse' ? null : p.classList.contains('is-aberto'); });
    p.addEventListener('click', function (e) {
      var fechado = antes === null ? !p.classList.contains('is-aberto') : !antes;
      var toque = antes !== null || !window.matchMedia('(hover: hover)').matches;
      antes = null;
      if (toque && fechado) {
        abrePainel();
        e.preventDefault();
        e.stopImmediatePropagation();
      }
    });
  });

  /* ------------------------------------------------------------
     VISOR
     ------------------------------------------------------------ */
  var visor = $('#visor');
  var vImg = $('#visorImg'), vLeg = $('#visorLegenda');
  var vConta = $('#visorConta'), vTit = $('#visorTitulo'), vMini = $('#visorMini');
  var serie = [], atual = 0, origem = null;

  function mostra(i) {
    atual = (i + serie.length) % serie.length;
    var foto = serie[atual];
    vImg.classList.add('is-a-mudar');
    var nova = new Image();
    nova.onload = nova.onerror = function () {
      vImg.src = nova.src;
      vImg.alt = (foto.d ? foto.d + ': ' : '') + foto.l;
      vImg.classList.remove('is-a-mudar');
    };
    nova.src = window.innerWidth > 900 ? img(foto.f) : img(foto.f, 1400);
    vLeg.textContent = '';
    if (foto.d) {
      var d = document.createElement('b');
      d.textContent = foto.d;
      vLeg.appendChild(d);
    }
    vLeg.appendChild(document.createTextNode(foto.l));
    vConta.textContent = String(atual + 1).padStart(2, '0') + ' / ' + String(serie.length).padStart(2, '0');
    $$('button', vMini).forEach(function (b, k) {
      b.classList.toggle('is-atual', k === atual);
      if (k === atual) b.scrollIntoView({ block: 'nearest', inline: 'center', behavior: reduzido ? 'auto' : 'smooth' });
    });
    var s = serie[(atual + 1) % serie.length];
    (new Image()).src = window.innerWidth > 900 ? img(s.f) : img(s.f, 1400);
  }
  var vAbas = $('#visorAbas');
  function abas(nome) {
    var c = SERIES[nome];
    visor.classList.toggle('tem-abas', !!c.grupo);
    if (!c.grupo) { vAbas.hidden = true; vAbas.innerHTML = ''; return; }
    vAbas.hidden = false;
    vAbas.innerHTML = Object.keys(SERIES).filter(function (k) { return SERIES[k].grupo === c.grupo; }).map(function (k) {
      return '<button type="button" data-aba="' + k + '"' + (k === nome ? ' aria-current="true" class="is-atual"' : '') + '>' +
        SERIES[k].nome + '<span>' + SERIES[k].fotos.length + '</span></button>';
    }).join('');
    $$('button', vAbas).forEach(function (b) { b.addEventListener('click', function () { abre(b.dataset.aba, 0); b.focus(); }); });
  }
  function abre(nome, i) {
    var c = SERIES[nome];
    if (!c || !c.fotos.length) return;
    var jaAberto = !visor.hidden;
    if (!jaAberto) origem = document.activeElement;
    serie = c.fotos;
    vTit.textContent = c.nome;
    abas(nome);
    vMini.innerHTML = serie.map(function (f, k) {
      return '<button type="button" aria-label="Fotografia ' + (k + 1) + '"><img src="' + img(f.f, 800) + '" alt="" loading="lazy"></button>';
    }).join('');
    $$('button', vMini).forEach(function (b, k) { b.addEventListener('click', function () { mostra(k); }); });
    if (!jaAberto) {
      visor.hidden = false;
      bloqueia(true);
      requestAnimationFrame(function () { visor.classList.add('is-aberto'); });
    }
    mostra(i || 0);
    if (!jaAberto) $('#visorFechar').focus();
  }
  function fecha() {
    visor.classList.remove('is-aberto');
    bloqueia(false);
    setTimeout(function () { visor.hidden = true; vImg.src = ''; }, reduzido ? 0 : 450);
    if (origem) origem.focus({ preventScroll: true });
  }
  $('#visorFechar').addEventListener('click', fecha);
  $('#visorAnt').addEventListener('click', function () { mostra(atual - 1); });
  $('#visorSeg').addEventListener('click', function () { mostra(atual + 1); });
  document.addEventListener('keydown', function (e) {
    if (visor.hidden) return;
    if (e.key === 'Escape') fecha();
    else if (e.key === 'ArrowLeft') mostra(atual - 1);
    else if (e.key === 'ArrowRight') mostra(atual + 1);
    else if (e.key === 'Tab') {
      var foc = $$('button', visor).filter(function (b) { return b.offsetParent !== null; });
      var primeiro = foc[0], ultimo = foc[foc.length - 1];
      if (e.shiftKey && document.activeElement === primeiro) { e.preventDefault(); ultimo.focus(); }
      else if (!e.shiftKey && document.activeElement === ultimo) { e.preventDefault(); primeiro.focus(); }
    }
  });
  var toqueX = null;
  $('#visorPalco').addEventListener('touchstart', function (e) { toqueX = e.touches[0].clientX; }, { passive: true });
  $('#visorPalco').addEventListener('touchend', function (e) {
    if (toqueX === null) return;
    var dx = e.changedTouches[0].clientX - toqueX;
    if (Math.abs(dx) > 45) mostra(atual + (dx < 0 ? 1 : -1));
    toqueX = null;
  });
  $('#visorPalco').addEventListener('click', function (e) { if (e.target === e.currentTarget) fecha(); });

  $$('[data-foto]').forEach(function (b) {
    b.addEventListener('click', function () {
      var nome = b.dataset.serie || 'lafora';
      var k = SERIES[nome].fotos.map(function (f) { return f.f; }).indexOf(b.dataset.foto);
      abre(nome, Math.max(0, k));
    });
  });

  var ano = $('#ano');
  if (ano) ano.textContent = new Date().getFullYear();
})();
