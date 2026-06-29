/* ============================================================
   LMSIS — Interactive Presentation Script
   ============================================================ */

(function () {
  'use strict';

  /* ─── SCENE DEFINITIONS ─── */
  const SCENES = [
    { id: 'hero',          label: 'Intro' },
    { id: 'problem',       label: 'Problem' },
    { id: 'gap',           label: 'Gap' },
    { id: 'dataset',       label: 'Dataset' },
    { id: 'architecture',  label: 'Model' },
    { id: 'latent',        label: 'Latent' },
    { id: 'breakthrough',  label: 'Under the Hood' },
    { id: 'results',       label: 'Results' },
    { id: 'ablation',      label: 'Ablation' },
    { id: 'equity',        label: 'Equity' },
    { id: 'validation',    label: 'Validation' },
    { id: 'contributions', label: 'Contributions' },
    { id: 'limitations',   label: 'Limitations' },
    { id: 'footer',        label: 'Footer' },
  ];

  /* ─── PROFILE DATA ─── */
  const PROFILES = {
    healthy: {
      color: '#10b981',
      z1: 0.12, z2: 0.09,
      homa: '1.57',  cap: '188 dB/m',
      quad: 'MHNW (Healthy)',
      cov: '98.2%',
      cx: 163, cy: 310,
    },
    ir: {
      color: '#f59e0b',
      z1: 0.72, z2: 0.14,
      homa: '1.96', cap: '205 dB/m',
      quad: 'IR-Dominant',
      cov: '100%',
      cx: 435, cy: 270,
    },
    steat: {
      color: '#8b5cf6',
      z1: 0.15, z2: 0.74,
      homa: '1.61', cap: '261 dB/m',
      quad: 'Steatosis-Dominant',
      cov: '98.9%',
      cx: 180, cy: 105,
    },
    dual: {
      color: '#ef4444',
      z1: 0.78, z2: 0.80,
      homa: '4.06', cap: '285 dB/m',
      quad: 'Dual-Burden',
      cov: '90.4% (was 81.6%)',
      cx: 480, cy: 95,
    },
  };

  let currentSlideIdx = 0;

  /* ─── INIT ─── */
  document.addEventListener('DOMContentLoaded', () => {
    initHeroCanvas();
    initKeyboardNav();
    initWheelNav();
    initTouchNav();
    goToSlide(0);
  });

  /* ══════════════════════════════════════════════
     SLIDE SWITCHING
  ══════════════════════════════════════════════ */

  function goToSlide(idx) {
    if (idx < 0 || idx >= SCENES.length) return;
    currentSlideIdx = idx;

    // Update slides visibility classes
    SCENES.forEach((s, i) => {
      const el = document.getElementById(s.id);
      if (!el) return;
      if (i === idx) {
        el.classList.add('active');
        el.classList.remove('prev');
      } else if (i < idx) {
        el.classList.add('prev');
        el.classList.remove('active');
      } else {
        el.classList.remove('active', 'prev');
      }
    });

    // Update progress bar
    const prog = document.getElementById('slide-progress');
    if (prog) {
      prog.style.width = `${(idx / (SCENES.length - 1)) * 100}%`;
    }

    // Update counter
    const counter = document.getElementById('slide-counter');
    if (counter) {
      counter.textContent = `Slide ${idx + 1} / ${SCENES.length}`;
    }

    // Update dots
    document.querySelectorAll('.nav-dot').forEach((d, i) => {
      d.classList.toggle('active', i === idx);
    });

    // Update nav arrows
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    if (prevBtn) prevBtn.disabled = (idx === 0);
    if (nextBtn) nextBtn.disabled = (idx === SCENES.length - 1);

    // Trigger animations in the active slide
    const activeEl = document.getElementById(SCENES[idx].id);
    if (activeEl) {
      // 1. Animate-in elements
      activeEl.querySelectorAll('.animate-in:not(.visible)').forEach((el) => {
        el.classList.add('visible');
      });

      // 2. Count-ups
      activeEl.querySelectorAll('.count-up').forEach((el) => {
        if (!doneCountUps.has(el)) {
          doneCountUps.add(el);
          animateCountUp(el);
        }
      });

      // 3. Horizontal and Vertical Bars
      activeEl.querySelectorAll('.hbar-fill[data-w]:not([data-animated])').forEach((el) => {
        el.dataset.animated = '1';
        const w = parseFloat(el.dataset.w);
        el.style.width = '0%';
        setTimeout(() => { el.style.width = w + '%'; }, 80);
      });
      activeEl.querySelectorAll('.vbar-fill[data-h]:not([data-animated])').forEach((el) => {
        el.dataset.animated = '1';
        const h = parseFloat(el.dataset.h);
        el.style.height = '0%';
        setTimeout(() => { el.style.height = h + '%'; }, 80);
      });

      // 4. Ethnicity threshold bars
      activeEl.querySelectorAll('.eth-fill[data-w]:not([data-animated])').forEach((el) => {
        el.dataset.animated = '1';
        const w = parseFloat(el.dataset.w);
        el.style.width = '0%';
        setTimeout(() => {
          el.style.transition = 'width 1.3s cubic-bezier(0.25,1,0.5,1)';
          el.style.width = w + '%';
        }, 80);
      });
    }
  }

  /* ══════════════════════════════════════════════
     HERO CANVAS — PARTICLE NETWORK
  ══════════════════════════════════════════════ */
  function initHeroCanvas() {
    const canvas = document.getElementById('hero-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, particles, raf;

    const N_PARTICLES = 80;
    const CONNECT_DIST = 140;
    const SPEED = 0.4;

    function resize() {
      W = canvas.width = canvas.offsetWidth;
      H = canvas.height = canvas.offsetHeight;
    }

    function mkParticle() {
      return {
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * SPEED,
        vy: (Math.random() - 0.5) * SPEED,
        r: Math.random() * 1.8 + 0.6,
      };
    }

    function init() {
      resize();
      particles = Array.from({ length: N_PARTICLES }, mkParticle);
    }

    function frame() {
      ctx.clearRect(0, 0, W, H);
      particles.forEach((p) => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1;
        if (p.y < 0 || p.y > H) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(59,130,246,0.6)';
        ctx.fill();
      });
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i], b = particles[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < CONNECT_DIST) {
            const alpha = (1 - d / CONNECT_DIST) * 0.35;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = `rgba(59,130,246,${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(frame);
    }

    init();
    frame();
    window.addEventListener('resize', () => { init(); });
  }

  /* ══════════════════════════════════════════════
     ANIMATIONS & COUNTERS
  ══════════════════════════════════════════════ */
  const doneCountUps = new WeakSet();

  function animateCountUp(el) {
    const target = parseFloat(el.dataset.val || 0);
    const decimals = parseInt(el.dataset.decimals || 0);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const duration = 1400;
    const start = performance.now();

    function step(now) {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      const val = target * eased;
      el.textContent = prefix + val.toFixed(decimals) + suffix;
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* ══════════════════════════════════════════════
     FAQ ACCORDION
  ══════════════════════════════════════════════ */
  window.toggleFaq = function (header) {
    const item = header.closest('.faq-item');
    const body = item.querySelector('.faq-body');
    const isOpen = item.classList.contains('open');

    if (isOpen) {
      item.classList.remove('open');
      body.style.maxHeight = '0';
    } else {
      item.classList.add('open');
      body.style.maxHeight = body.scrollHeight + 'px';
    }
  };

  function autoOpenFaq() {
    const first = document.querySelector('.faq-item.open .faq-body');
    if (first) first.style.maxHeight = first.scrollHeight + 'px';
  }

  /* ══════════════════════════════════════════════
     INTERACTIVE METABOLIC MAP
  ══════════════════════════════════════════════ */
  window.selectProfile = function (key, btn) {
    const prof = PROFILES[key];
    if (!prof) return;

    // Update buttons
    document.querySelectorAll('.profile-btn').forEach((b) => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    // Animate pin
    const pin = document.getElementById('map-pin');
    const pinInner = document.getElementById('map-pin-inner');
    if (pin && pinInner) {
      pin.setAttribute('cx', prof.cx);
      pin.setAttribute('cy', prof.cy);
      pin.setAttribute('stroke', prof.color);
      pin.setAttribute('fill', prof.color + '22');
      pinInner.setAttribute('cx', prof.cx);
      pinInner.setAttribute('cy', prof.cy);
      pinInner.setAttribute('fill', prof.color);
      // Animate position
      pin.style.transition = 'cx 0.7s cubic-bezier(0.25,1,0.5,1), cy 0.7s cubic-bezier(0.25,1,0.5,1)';
    }

    // Draw route to safe zone
    const route = document.getElementById('map-route');
    const safeX = 163, safeY = 310;
    if (route) {
      const cpX = (prof.cx + safeX) / 2 + (prof.cy < safeY ? -60 : 60);
      const cpY = (prof.cy + safeY) / 2 + (prof.cx < safeX ? 40 : -40);
      route.setAttribute('d', `M ${prof.cx} ${prof.cy} Q ${cpX} ${cpY} ${safeX} ${safeY}`);
      route.setAttribute('stroke', prof.color);
      route.style.display = key === 'healthy' ? 'none' : '';

      // Dash animation
      const len = route.getTotalLength ? route.getTotalLength() : 200;
      route.style.strokeDasharray = len;
      route.style.strokeDashoffset = len;
      route.style.transition = 'stroke-dashoffset 1s ease';
      setTimeout(() => { route.style.strokeDashoffset = '0'; }, 50);
    }

    // Update readout
    const setText = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    setText('rv-z1', prof.z1.toFixed(2));
    setText('rv-z2', prof.z2.toFixed(2));
    setText('rv-homa', prof.homa);
    setText('rv-cap', prof.cap);
    setText('rv-quad', prof.quad);
    setText('rv-cov', prof.cov);
  };

  /* ══════════════════════════════════════════════
     NAVIGATION EVENT LISTENERS
  ══════════════════════════════════════════════ */
  let lastKeyTime = 0;
  function initKeyboardNav() {
    document.addEventListener('keydown', (e) => {
      const now = Date.now();
      if (now - lastKeyTime < 300) return;
      const key = e.key;
      if (!['ArrowDown', 'ArrowUp', 'ArrowRight', 'ArrowLeft', 'PageDown', 'PageUp', ' '].includes(key)) return;

      if (key === 'ArrowDown' || key === 'ArrowRight' || key === 'PageDown' || key === ' ') {
        e.preventDefault();
        if (currentSlideIdx < SCENES.length - 1) {
          goToSlide(currentSlideIdx + 1);
        }
        lastKeyTime = now;
      } else if (key === 'ArrowUp' || key === 'ArrowLeft' || key === 'PageUp') {
        e.preventDefault();
        if (currentSlideIdx > 0) {
          goToSlide(currentSlideIdx - 1);
        }
        lastKeyTime = now;
      }
    });

    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        goToSlide(currentSlideIdx - 1);
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        goToSlide(currentSlideIdx + 1);
      });
    }
  }

  let lastWheelTime = 0;
  function initWheelNav() {
    window.addEventListener('wheel', (e) => {
      const now = Date.now();
      if (now - lastWheelTime < 800) return;
      
      const delta = e.deltaY;
      if (Math.abs(delta) < 30) return;

      if (delta > 0) {
        if (currentSlideIdx < SCENES.length - 1) {
          goToSlide(currentSlideIdx + 1);
          lastWheelTime = now;
        }
      } else {
        if (currentSlideIdx > 0) {
          goToSlide(currentSlideIdx - 1);
          lastWheelTime = now;
        }
      }
    }, { passive: true });
  }

  let touchStartX = 0;
  let touchStartY = 0;
  function initTouchNav() {
    window.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
      touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    window.addEventListener('touchend', (e) => {
      const diffX = e.changedTouches[0].screenX - touchStartX;
      const diffY = e.changedTouches[0].screenY - touchStartY;
      
      if (Math.abs(diffX) > Math.abs(diffY)) {
        if (Math.abs(diffX) > 60) {
          if (diffX < 0) {
            if (currentSlideIdx < SCENES.length - 1) goToSlide(currentSlideIdx + 1);
          } else {
            if (currentSlideIdx > 0) goToSlide(currentSlideIdx - 1);
          }
        }
      } else {
        if (Math.abs(diffY) > 60) {
          if (diffY < 0) {
            if (currentSlideIdx < SCENES.length - 1) goToSlide(currentSlideIdx + 1);
          } else {
            if (currentSlideIdx > 0) goToSlide(currentSlideIdx - 1);
          }
        }
      }
    }, { passive: true });
  }

})();
