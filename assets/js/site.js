/* Adhly Azhar · portfolio
   Small, dependency-free behaviour: header state, mobile menu,
   scroll reveals, falling sticky notes, the floating work preview, screenshot lightbox
   and the contact form. */
(() => {
  'use strict';

  const root = document.documentElement;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Hero intro (CSS does the animation) */
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.add('is-loaded')));

  /* Year and today's date (on the receipt) */
  document.querySelectorAll('[data-year]').forEach((el) => {
    el.textContent = new Date().getFullYear();
  });
  const today = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Colombo' });
  document.querySelectorAll('[data-today]').forEach((el) => {
    el.textContent = today.format(new Date());
  });

  /* Header border once the page scrolls */
  const header = document.querySelector('.site-header');
  const onScroll = () => header && header.classList.toggle('is-stuck', window.scrollY > 8);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Mobile menu */
  const toggle = document.querySelector('.nav-toggle');
  const menu = document.getElementById('site-menu');
  const setMenu = (open) => {
    if (!toggle) return;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    document.body.classList.toggle('menu-open', open);
  };
  if (toggle && menu) {
    toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
    menu.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => setMenu(false)));
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') setMenu(false);
    });
  }

  /* Highlight the nav link for the section in view */
  const navLinks = [...document.querySelectorAll('.nav-links a[href^="#"]')];
  const sections = navLinks.map((a) => document.querySelector(a.getAttribute('href'))).filter(Boolean);
  if ('IntersectionObserver' in window && sections.length) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        navLinks.forEach((a) => a.classList.toggle('is-active', a.getAttribute('href') === `#${entry.target.id}`));
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    sections.forEach((s) => spy.observe(s));
  }

  /* Reveal on scroll */
  const revealItems = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
    revealItems.forEach((el) => io.observe(el));
  } else {
    revealItems.forEach((el) => el.classList.add('is-in'));
  }

  /* Work list: a small preview card follows the cursor while hovering a row */
  const preview = document.querySelector('.work-preview');
  const rows = document.querySelectorAll('.work-row[data-preview]');
  const canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (preview && rows.length && canHover) {
    const img = preview.querySelector('img');
    let x = 0, y = 0, cx = 0, cy = 0, tilt = 0, raf = 0, active = false;

    const loop = () => {
      const dx = x - cx;
      cx += dx * (reduceMotion ? 1 : 0.16);
      cy += (y - cy) * (reduceMotion ? 1 : 0.16);
      tilt += ((reduceMotion ? 0 : Math.max(-8, Math.min(8, dx * 0.08))) - tilt) * 0.2;
      preview.style.transform = `translate3d(${cx + 28}px, ${cy - preview.offsetHeight / 2}px, 0) rotate(${tilt - 3}deg)`;
      if (active || Math.abs(dx) > 0.5) raf = requestAnimationFrame(loop);
      else raf = 0;
    };

    rows.forEach((row) => {
      row.addEventListener('pointerenter', (e) => {
        img.src = row.dataset.preview;
        if (!active) {
          cx = x = e.clientX;
          cy = y = e.clientY;
        }
        active = true;
        preview.classList.add('is-visible');
        if (!raf) raf = requestAnimationFrame(loop);
      });
    });
    document.querySelector('.work-list').addEventListener('pointerleave', () => {
      active = false;
      preview.classList.remove('is-visible');
    });
    window.addEventListener('pointermove', (e) => {
      x = e.clientX;
      y = e.clientY;
    }, { passive: true });
    window.addEventListener('scroll', () => {
      if (active) {
        active = false;
        preview.classList.remove('is-visible');
      }
    }, { passive: true });
  }

  /* Sticky notes fall from above as their spot scrolls into view, then swing on their pin.
     The fall follows the scroll position, so scrolling back up lifts them off again. */
  const notes = [...document.querySelectorAll('.drop-note')];
  if (notes.length && !reduceMotion) {
    root.classList.add('notes-live');
    const items = notes.map((el, i) => {
      const paper = el.querySelector('.drop-paper');
      return {
        el,
        paper,
        r: parseFloat(getComputedStyle(paper).getPropertyValue('--r')) || 0,
        dir: i % 2 ? 1 : -1,
        landed: false
      };
    });
    let notesQueued = false;
    const placeNotes = () => {
      notesQueued = false;
      const vh = window.innerHeight;
      const drop = Math.min(320, vh * 0.42);
      items.forEach((it) => {
        const top = it.el.getBoundingClientRect().top;
        // 0 while the note's spot is below the screen, 1 once it is ~42% of a screen up
        const p = Math.min(1, Math.max(0, (vh - top) / (vh * 0.42)));
        const e = 1 - Math.pow(1 - p, 3);
        const tilt = it.r + (1 - e) * (it.dir * 26 + Math.sin(p * 9) * 7);
        it.paper.style.transform = `translate3d(0, ${(-(1 - e) * drop).toFixed(1)}px, 0) rotate(${tilt.toFixed(2)}deg)`;
        it.paper.style.opacity = Math.min(1, p * 2.5).toFixed(3);
        if (p >= 1 && !it.landed) {
          it.landed = true;
          it.el.classList.add('is-landed');
        } else if (p < 0.85 && it.landed) {
          it.landed = false;
          it.el.classList.remove('is-landed');
        }
      });
    };
    const queueNotes = () => {
      if (!notesQueued) {
        notesQueued = true;
        requestAnimationFrame(placeNotes);
      }
    };
    window.addEventListener('scroll', queueNotes, { passive: true });
    window.addEventListener('resize', queueNotes);
    placeNotes();
  }

  /* Notebook diagrams: their SVG (SMIL) animations play only while on screen.
     With reduced motion they stop on a still frame that shows every label. */
  const motions = [...document.querySelectorAll('svg.motion')].filter((svg) => typeof svg.pauseAnimations === 'function');
  if (motions.length) {
    if (reduceMotion || !('IntersectionObserver' in window)) {
      motions.forEach((svg) => {
        svg.pauseAnimations();
        svg.setCurrentTime(parseFloat(svg.dataset.still || '0'));
      });
    } else {
      const motionIo = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          entry.target.classList.toggle('is-playing', entry.isIntersecting);
          if (entry.isIntersecting) entry.target.unpauseAnimations();
          else entry.target.pauseAnimations();
        });
      }, { threshold: 0.15 });
      motions.forEach((svg) => {
        svg.pauseAnimations();
        motionIo.observe(svg);
      });
    }
  }

  /* Screenshot lightbox (case study pages) */
  const dialog = document.querySelector('.lightbox');
  const shots = [...document.querySelectorAll('[data-shot]')];
  if (dialog && shots.length && typeof dialog.showModal === 'function') {
    const img = dialog.querySelector('img');
    const caption = dialog.querySelector('figcaption');
    let index = 0;
    const show = (i) => {
      index = (i + shots.length) % shots.length;
      const shot = shots[index];
      img.src = shot.dataset.shot;
      img.alt = shot.querySelector('img').alt;
      caption.textContent = `${shot.dataset.caption || ''}  (${index + 1} of ${shots.length})`;
    };
    shots.forEach((shot, i) => shot.addEventListener('click', () => {
      show(i);
      dialog.showModal();
    }));
    dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
    dialog.querySelector('[data-prev]').addEventListener('click', () => show(index - 1));
    dialog.querySelector('[data-next]').addEventListener('click', () => show(index + 1));
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) dialog.close();
    });
    dialog.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') show(index - 1);
      if (e.key === 'ArrowRight') show(index + 1);
    });
  }

  /* Contact form (FormSubmit AJAX endpoint; the form's action is the no-JS fallback) */
  const form = document.getElementById('contact-form');
  if (form) {
    const status = form.querySelector('.form-status');
    const button = form.querySelector('button[type="submit"]');
    const setStatus = (text, kind) => {
      status.textContent = text;
      status.className = `form-status ${kind ? `is-${kind}` : ''}`;
    };
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      button.disabled = true;
      setStatus('Sending…');
      try {
        const res = await fetch(form.dataset.endpoint, {
          method: 'POST',
          headers: { Accept: 'application/json' },
          body: new FormData(form)
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || String(data.success) !== 'true') throw new Error(data.message || 'Request failed');
        form.reset();
        setStatus('Thanks! Your message is on its way. I’ll reply by email.', 'ok');
      } catch (err) {
        setStatus('Sorry, that didn’t go through. Please email me at adhlyazhar@outlook.com instead.', 'error');
      } finally {
        button.disabled = false;
      }
    });
  }
})();
