/* script.js */

document.addEventListener('DOMContentLoaded', () => {
  const sections = Array.from(document.querySelectorAll('section.scene'));
  const dotsContainer = document.querySelector('.dots-nav');
  const progressBar = document.querySelector('.scroll-progress-bar');
  const navLinks = Array.from(document.querySelectorAll('.nav-links a'));

  let currentSectionIndex = 0;
  let isScrolling = false;

  // --- 1. Dynamic Dot Navigation Setup ---
  sections.forEach((section, idx) => {
    const dot = document.createElement('div');
    dot.classList.add('dots-nav-item');
    if (idx === 0) dot.classList.add('active');
    dot.addEventListener('click', () => {
      scrollToSection(idx);
    });
    dotsContainer.appendChild(dot);
  });

  const dots = Array.from(dotsContainer.querySelectorAll('.dots-nav-item'));

  // --- Accent Colors Mapping by Scene ---
  // To match dot navigation colors with the theme of the active scene
  const sceneAccents = [
    'var(--healthy)', // Scene 1
    'var(--healthy)', // Scene 2
    'var(--dual-risk)', // Scene 3
    'var(--healthy)', // Scene 4
    'var(--healthy)', // Scene 5
    'var(--ir-risk)',   // Scene 6
    'var(--healthy)', // Scene 7
    'var(--healthy)', // Scene 8
    'var(--muted)',    // Scene 9
    'var(--healthy)', // Scene 10
    'var(--healthy)', // Scene 11
    'var(--muted)'     // Scene 12
  ];

  // --- 2. Scroll Snapping & State Update ---
  function scrollToSection(index) {
    if (index < 0 || index >= sections.length) return;
    isScrolling = true;
    currentSectionIndex = index;

    sections[index].scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });

    updateNavigationStates(index);

    setTimeout(() => {
      isScrolling = false;
    }, 850);
  }

  function updateNavigationStates(index) {
    // Top Progress Bar
    const progressPercent = (index / (sections.length - 1)) * 100;
    progressBar.style.width = `${progressPercent}%`;

    // Update Dots Active Accent
    dots.forEach((dot, idx) => {
      dot.classList.remove('active');
      dot.style.backgroundColor = '';
      if (idx === index) {
        dot.classList.add('active');
        dot.style.backgroundColor = sceneAccents[index];
      }
    });

    // Update Sticky Nav Active Header Link
    // Navigation maps scenes: Abstract (Scene 2), Method (Scene 5), Demo (Scene 6), Results (Scene 7), Questions (Scene 9)
    navLinks.forEach(link => link.classList.remove('active'));
    if (index === 1) {
      document.querySelector('a[href="#abstract"]').classList.add('active');
    } else if (index === 4) {
      document.querySelector('a[href="#method"]').classList.add('active');
    } else if (index === 5) {
      document.querySelector('a[href="#demo"]').classList.add('active');
    } else if (index === 6) {
      document.querySelector('a[href="#results"]').classList.add('active');
    } else if (index === 8) {
      document.querySelector('a[href="#questions"]').classList.add('active');
    }
  }

  // --- 3. Keyboard Snape Handler ---
  window.addEventListener('keydown', (e) => {
    if (isScrolling) return;

    if (['ArrowDown', 'ArrowRight', ' ', 'PageDown'].includes(e.key)) {
      if (currentSectionIndex < sections.length - 1) {
        e.preventDefault();
        scrollToSection(currentSectionIndex + 1);
      }
    } else if (['ArrowUp', 'ArrowLeft', 'PageUp'].includes(e.key)) {
      if (currentSectionIndex > 0) {
        e.preventDefault();
        scrollToSection(currentSectionIndex - 1);
      }
    }
  });

  // --- 4. IntersectionObserver for Natural Scrolling Sync ---
  const sceneObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && !isScrolling) {
        const activeIdx = sections.indexOf(entry.target);
        if (activeIdx !== -1) {
          currentSectionIndex = activeIdx;
          updateNavigationStates(activeIdx);
        }
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(section => sceneObserver.observe(section));

  // --- 5. Entrance Fade & Rise Animations ---
  const animObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        animObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.animate-element').forEach(el => animObserver.observe(el));

  // --- 6. Number Count-up Engine ---
  function animateValue(obj, start, end, duration, decimals = 0, prefix = '', suffix = '') {
    let startTimestamp = null;
    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      const ease = progress * (2 - progress); // easeOutQuad
      const value = start + ease * (end - start);
      obj.innerHTML = prefix + value.toFixed(decimals) + suffix;
      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };
    window.requestAnimationFrame(step);
  }

  const countObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const target = entry.target;
        const endVal = parseFloat(target.getAttribute('data-val'));
        const startVal = parseFloat(target.getAttribute('data-start') || '0');
        const decimals = parseInt(target.getAttribute('data-decimals') || '0');
        const duration = parseInt(target.getAttribute('data-duration') || '1500');
        const prefix = target.getAttribute('data-prefix') || '';
        const suffix = target.getAttribute('data-suffix') || '';
        animateValue(target, startVal, endVal, duration, decimals, prefix, suffix);
        countObserver.unobserve(target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.count-up').forEach(el => countObserver.observe(el));

  // --- 7. Initialize SVG Path Lengths for Scroll-Linked Draw ---
  const scrollPaths = document.querySelectorAll('.draw-path');
  scrollPaths.forEach(path => {
    const length = path.getTotalLength();
    path.style.strokeDasharray = length;
    path.style.strokeDashoffset = length;
  });

  // --- 8. Continuous Scroll-Linked Drawing and Chart Growing ---
  window.addEventListener('scroll', () => {
    // Scene 5 Method Architecture Scroll-Link
    const s5 = document.getElementById('scene-5');
    if (s5) {
      const rect = s5.getBoundingClientRect();
      const viewHeight = window.innerHeight;
      const totalRange = viewHeight + rect.height;
      const progress = Math.max(0, Math.min(1, (viewHeight - rect.top) / totalRange));
      const drawProgress = Math.max(0, Math.min(1, (progress - 0.2) / 0.6)); // Draw between 20% and 80% viewport progress

      const paths = s5.querySelectorAll('.draw-path');
      paths.forEach(path => {
        const length = path.getTotalLength();
        path.style.strokeDashoffset = length * (1 - drawProgress);
      });
    }

    // Scene 7 Results Chart Scroll-Link
    const s7 = document.getElementById('scene-7');
    if (s7) {
      const rect = s7.getBoundingClientRect();
      const viewHeight = window.innerHeight;
      const totalRange = viewHeight + rect.height;
      const progress = Math.max(0, Math.min(1, (viewHeight - rect.top) / totalRange));
      const barProgress = Math.max(0, Math.min(1, (progress - 0.15) / 0.5)); // Animate bars between 15% and 65% progress

      // Horizontal Bar Chart
      const bars = s7.querySelectorAll('.bar-fill');
      bars.forEach(bar => {
        const maxPct = parseFloat(bar.getAttribute('data-target-width'));
        bar.style.width = (maxPct * barProgress) + '%';
      });

      // Horizontal Negative Bar Chart
      const negBars = s7.querySelectorAll('.bar-fill-neg');
      negBars.forEach(bar => {
        const maxPct = parseFloat(bar.getAttribute('data-target-width'));
        bar.style.width = (maxPct * barProgress) + '%';
      });

      // Vertical Bar Pairs
      const vBars = s7.querySelectorAll('.v-bar-fill');
      vBars.forEach(bar => {
        const maxPct = parseFloat(bar.getAttribute('data-target-height'));
        bar.style.height = (maxPct * barProgress) + '%';
      });
    }
  });

  // --- 9. Toggle Detail Expanding Accordions (+ Technical details & FAQs) ---
  // A generic function to toggle accordion height smoothly
  window.toggleAccordion = function(buttonElement, bodySelector) {
    const parent = buttonElement.closest('.accordion-parent') || buttonElement.parentElement;
    const body = parent.querySelector(bodySelector);
    
    if (buttonElement.classList.contains('active')) {
      buttonElement.classList.remove('active');
      parent.classList.remove('active');
      body.style.maxHeight = '0';
    } else {
      buttonElement.classList.add('active');
      parent.classList.add('active');
      body.style.maxHeight = body.scrollHeight + 'px';
    }
  };

  // --- 10. Live Interactive Demo Widget (Scene 6) ---
  const profiles = {
    healthy: {
      z1: -1.4, z2: -1.3,
      score: 1.4, liverFat: 210, risk: 8,
      color: '#00C47D',
      name: '"Healthy"',
      desc: '"A generative model whose internal coordinates are mathematically anchored to real, independently verifiable clinical measurements."',
      hasRoute: false
    },
    ir: {
      z1: 1.6, z2: -0.6,
      score: 3.6, liverFat: 228, risk: 54,
      color: '#F5A623',
      name: '"IR-dominant"',
      desc: '"Clinical risk scores lose accuracy once body weight is restricted to the normal range"',
      hasRoute: true,
      waypoint: '"Fasting insulin lower"',
      routeControlX: 300,
      routeControlY: 260
    },
    steatosis: {
      z1: -0.6, z2: 1.7,
      score: 1.6, liverFat: 268, risk: 58,
      color: '#3D8EF8',
      name: '"Steatosis-dominant"',
      desc: '"Off-the-shelf confidence estimates fail exactly the patients who need them most"',
      hasRoute: true,
      waypoint: '"Triglycerides lower"',
      routeControlX: 210,
      routeControlY: 170
    },
    dual: {
      z1: 1.7, z2: 1.8,
      score: 3.3, liverFat: 286, risk: 82,
      color: '#E8394A',
      name: '"Dual-burden"',
      desc: '"Standard uncertainty estimates quietly fail the patients who need them most. A targeted correction restores their reliability — and it holds up two years later, on data the model never saw."',
      hasRoute: true,
      waypoint: '"Triglycerides lower"',
      routeControlX: 320,
      routeControlY: 160
    }
  };

  const mapSvg = document.getElementById('demo-map-svg');
  const pin = document.getElementById('demo-pin');
  const routePath = document.getElementById('demo-route');
  const waypointLabel = document.getElementById('demo-waypoint-label');
  const bannerName = document.getElementById('demo-banner-name');
  const bannerDesc = document.getElementById('demo-banner-desc');
  
  const cardValIR = document.getElementById('demo-val-ir');
  const cardValFat = document.getElementById('demo-val-fat');
  const cardValRisk = document.getElementById('demo-val-risk');

  // SVG coordinate projection
  // Maps coordinates z1 (-3 to 3) to SVG X (40 to 600)
  // Maps coordinates z2 (-3 to 3) to SVG Y (360 to 40)
  function projectX(z1) {
    return 320 + (z1 / 3) * 280;
  }
  function projectY(z2) {
    return 200 - (z2 / 3) * 160;
  }

  // Safe zone anchor center
  const safeX = projectX(-1.4);
  const safeY = projectY(-1.3);

  window.selectProfile = function(profileKey, buttonEl) {
    // Manage active buttons
    document.querySelectorAll('.demo-pill-btn').forEach(btn => {
      btn.classList.remove('active');
      btn.style.borderColor = 'var(--border)';
    });
    
    buttonEl.classList.add('active');
    
    const profile = profiles[profileKey];
    buttonEl.style.borderColor = profile.color;

    // Project coordinates
    const targetX = projectX(profile.z1);
    const targetY = projectY(profile.z2);

    // Position and show Pin
    pin.style.display = 'block';
    pin.setAttribute('cx', targetX);
    pin.setAttribute('cy', targetY);
    pin.setAttribute('fill', profile.color);

    // Update banner text
    bannerName.innerText = profile.name.replace(/"/g, '');
    bannerName.style.color = profile.color;
    bannerDesc.innerText = profile.desc.replace(/"/g, '');

    // Update metrics cards with counting animations
    animateValue(cardValIR, parseFloat(cardValIR.innerText) || 0, profile.score, 600, 1, '', '');
    animateValue(cardValFat, parseFloat(cardValFat.innerText) || 0, profile.liverFat, 600, 0, '', '');
    animateValue(cardValRisk, parseFloat(cardValRisk.innerText) || 0, profile.risk, 600, 0, '', '%');

    // Handle Intervention Route path and waypoint label
    if (profile.hasRoute) {
      routePath.style.display = 'block';
      routePath.setAttribute('stroke', profile.color);
      
      // Draw smooth curve (Quadratic Bezier) from profile position to safe zone
      const pathData = `M ${targetX} ${targetY} Q ${profile.routeControlX} ${profile.routeControlY} ${safeX} ${safeY}`;
      routePath.setAttribute('d', pathData);

      // Position waypoint label near curve midpoint
      // Q midpoint is roughly: B(0.5) = 0.25*P0 + 0.5*P1 + 0.25*P2
      const midX = 0.25 * targetX + 0.5 * profile.routeControlX + 0.25 * safeX;
      const midY = 0.25 * targetY + 0.5 * profile.routeControlY + 0.25 * safeY;

      waypointLabel.style.display = 'block';
      waypointLabel.setAttribute('x', midX);
      waypointLabel.setAttribute('y', midY - 12);
      waypointLabel.setAttribute('fill', profile.color);
      waypointLabel.textContent = profile.waypoint.replace(/"/g, '');
    } else {
      routePath.style.display = 'none';
      waypointLabel.style.display = 'none';
    }
  };
});
