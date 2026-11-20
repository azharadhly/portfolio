/* Background music + audio-reactive hero dots.

   The soundtrack is an original lo-fi loop generated live with the Web Audio API
   (no audio files, nothing to license): 78 BPM in A minor, warm pads, soft bass,
   a light beat, a wandering kalimba-like melody and a bit of vinyl crackle.

   Nothing plays until the visitor presses a [data-sound-toggle] button. If they
   had sound on, it picks up again on their first click on the next page.

   The halftone dots behind the hero portrait are redrawn on a canvas: every beat
   sends a ripple of growing dots outward from the figure. With the music off the
   dots breathe slowly; with reduced motion they stay still. */
(() => {
  'use strict';

  const toggles = [...document.querySelectorAll('[data-sound-toggle]')];
  const dotsHost = document.querySelector('.hero-dots');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const AC = window.AudioContext || window.webkitAudioContext;

  const store = {
    get() { try { return localStorage.getItem('sound'); } catch (e) { return null; } },
    set(v) { try { localStorage.setItem('sound', v); } catch (e) { /* private mode */ } },
  };

  /* ------------------------------------------------------------------ engine */

  const BPM = 78;
  const SIXTEENTH = 60 / BPM / 4;
  const CHORDS = [
    { bass: 45, pad: [60, 64, 67, 71] }, // Am9
    { bass: 41, pad: [57, 60, 64, 67] }, // Fmaj9
    { bass: 48, pad: [55, 59, 64, 67] }, // Cmaj7
    { bass: 43, pad: [59, 62, 64, 69] }, // G6/9
  ];
  const SCALE = [57, 60, 62, 64, 67, 69, 72, 74, 76, 79, 81]; // A minor pentatonic
  const mtof = (n) => 440 * Math.pow(2, (n - 69) / 12);

  let ctx = null;
  let sum, master, analyser, freqData, timeData, padFilter, pluckBus, drumBus, reverbSend, noiseBuf;
  let playing = false;
  let timer = 0;
  let stopTimer = 0;
  let nextTime = 0;
  let step = 0;
  let loop = 0;
  let melody = 5;

  function impulse(seconds) {
    const len = Math.floor(ctx.sampleRate * seconds);
    const buf = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let c = 0; c < 2; c++) {
      const d = buf.getChannelData(c);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3);
    }
    return buf;
  }

  function build() {
    ctx = new AC();

    // master chain: sum -> warm lowpass -> gentle compressor -> volume -> analyser -> speakers
    sum = ctx.createGain();
    const tone = ctx.createBiquadFilter();
    tone.type = 'lowpass';
    tone.frequency.value = 7200;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -20;
    comp.ratio.value = 3;
    comp.attack.value = 0.01;
    comp.release.value = 0.25;
    master = ctx.createGain();
    master.gain.value = 0;
    analyser = ctx.createAnalyser();
    analyser.fftSize = 1024;
    analyser.smoothingTimeConstant = 0.6;
    freqData = new Uint8Array(analyser.frequencyBinCount);
    timeData = new Float32Array(analyser.fftSize);
    sum.connect(tone);
    tone.connect(comp);
    comp.connect(master);
    master.connect(analyser);
    analyser.connect(ctx.destination);

    // shared room reverb
    const reverb = ctx.createConvolver();
    reverb.buffer = impulse(2.6);
    reverbSend = ctx.createGain();
    reverbSend.connect(reverb);
    const wet = ctx.createGain();
    wet.gain.value = 0.3;
    reverb.connect(wet);
    wet.connect(sum);

    // pads go through a lowpass that slowly opens and closes
    padFilter = ctx.createBiquadFilter();
    padFilter.type = 'lowpass';
    padFilter.frequency.value = 950;
    padFilter.Q.value = 0.7;
    const lfo = ctx.createOscillator();
    lfo.frequency.value = 0.07;
    const lfoDepth = ctx.createGain();
    lfoDepth.gain.value = 350;
    lfo.connect(lfoDepth);
    lfoDepth.connect(padFilter.frequency);
    lfo.start();
    const padOut = ctx.createGain();
    padFilter.connect(padOut);
    padOut.connect(sum);
    const padSend = ctx.createGain();
    padSend.gain.value = 0.6;
    padOut.connect(padSend);
    padSend.connect(reverbSend);

    // melody with a soft dotted-eighth echo
    pluckBus = ctx.createGain();
    pluckBus.connect(sum);
    const echo = ctx.createDelay(1.5);
    echo.delayTime.value = SIXTEENTH * 3;
    const echoTone = ctx.createBiquadFilter();
    echoTone.type = 'lowpass';
    echoTone.frequency.value = 2400;
    const feedback = ctx.createGain();
    feedback.gain.value = 0.32;
    const echoWet = ctx.createGain();
    echoWet.gain.value = 0.35;
    pluckBus.connect(echo);
    echo.connect(echoTone);
    echoTone.connect(feedback);
    feedback.connect(echo);
    echoTone.connect(echoWet);
    echoWet.connect(sum);
    const pluckSend = ctx.createGain();
    pluckSend.gain.value = 0.7;
    pluckBus.connect(pluckSend);
    pluckSend.connect(reverbSend);

    drumBus = ctx.createGain();
    drumBus.connect(sum);

    noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const nd = noiseBuf.getChannelData(0);
    for (let i = 0; i < nd.length; i++) nd[i] = Math.random() * 2 - 1;

    // vinyl crackle bed: faint hiss plus the odd click
    const crackle = ctx.createBuffer(1, ctx.sampleRate * 4, ctx.sampleRate);
    const cd = crackle.getChannelData(0);
    for (let i = 0; i < cd.length; i++) {
      cd[i] = (Math.random() * 2 - 1) * 0.004 + (Math.random() < 0.0004 ? (Math.random() * 2 - 1) * 0.6 : 0);
    }
    const crackleSrc = ctx.createBufferSource();
    crackleSrc.buffer = crackle;
    crackleSrc.loop = true;
    const crackleHp = ctx.createBiquadFilter();
    crackleHp.type = 'highpass';
    crackleHp.frequency.value = 900;
    const crackleGain = ctx.createGain();
    crackleGain.gain.value = 0.12;
    crackleSrc.connect(crackleHp);
    crackleHp.connect(crackleGain);
    crackleGain.connect(sum);
    crackleSrc.start();
  }

  /* voices */

  function pad(notes, t, dur) {
    notes.forEach((n) => {
      [-7, 7].forEach((detune) => {
        const o = ctx.createOscillator();
        o.type = 'sawtooth';
        o.frequency.value = mtof(n);
        o.detune.value = detune;
        const g = ctx.createGain();
        g.gain.setValueAtTime(0.0001, t);
        g.gain.linearRampToValueAtTime(0.017, t + 1.1);
        g.gain.setValueAtTime(0.017, t + dur);
        g.gain.exponentialRampToValueAtTime(0.0001, t + dur + 1.6);
        o.connect(g);
        g.connect(padFilter);
        o.start(t);
        o.stop(t + dur + 1.7);
      });
    });
  }

  function bass(n, t, dur) {
    const o = ctx.createOscillator();
    o.type = 'triangle';
    o.frequency.value = mtof(n);
    const sub = ctx.createOscillator();
    sub.type = 'sine';
    sub.frequency.value = mtof(n - 12);
    const subGain = ctx.createGain();
    subGain.gain.value = 0.8;
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 420;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(0.19, t + 0.03);
    g.gain.exponentialRampToValueAtTime(0.08, t + dur * 0.6);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(lp);
    sub.connect(subGain);
    subGain.connect(lp);
    lp.connect(g);
    g.connect(sum);
    o.start(t);
    sub.start(t);
    o.stop(t + dur + 0.05);
    sub.stop(t + dur + 0.05);
  }

  function pluck(n, t, vel) {
    const f = mtof(n);
    const body = ctx.createOscillator();
    body.type = 'sine';
    body.frequency.value = f;
    const tine = ctx.createOscillator();
    tine.type = 'triangle';
    tine.frequency.value = f * 2.003;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(0.085 * vel, t + 0.006);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 1.3);
    const g2 = ctx.createGain();
    g2.gain.setValueAtTime(0.0001, t);
    g2.gain.linearRampToValueAtTime(0.02 * vel, t + 0.004);
    g2.gain.exponentialRampToValueAtTime(0.0001, t + 0.25);
    body.connect(g);
    tine.connect(g2);
    g.connect(pluckBus);
    g2.connect(pluckBus);
    body.start(t);
    tine.start(t);
    body.stop(t + 1.4);
    tine.stop(t + 0.3);
  }

  function kick(t, vel = 1) {
    const o = ctx.createOscillator();
    o.type = 'sine';
    o.frequency.setValueAtTime(120, t);
    o.frequency.exponentialRampToValueAtTime(42, t + 0.13);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.85 * vel, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.45);
    o.connect(g);
    g.connect(drumBus);
    o.start(t);
    o.stop(t + 0.5);
  }

  function snare(t) {
    const noise = ctx.createBufferSource();
    noise.buffer = noiseBuf;
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.value = 1800;
    bp.Q.value = 0.8;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.2, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
    noise.connect(bp);
    bp.connect(g);
    g.connect(drumBus);
    const send = ctx.createGain();
    send.gain.value = 0.3;
    g.connect(send);
    send.connect(reverbSend);
    noise.start(t, Math.random() * 0.5);
    noise.stop(t + 0.2);

    const body = ctx.createOscillator();
    body.type = 'triangle';
    body.frequency.setValueAtTime(200, t);
    body.frequency.exponentialRampToValueAtTime(140, t + 0.08);
    const bg = ctx.createGain();
    bg.gain.setValueAtTime(0.11, t);
    bg.gain.exponentialRampToValueAtTime(0.001, t + 0.09);
    body.connect(bg);
    bg.connect(drumBus);
    body.start(t);
    body.stop(t + 0.1);
  }

  function hat(t, vel) {
    const noise = ctx.createBufferSource();
    noise.buffer = noiseBuf;
    const hp = ctx.createBiquadFilter();
    hp.type = 'highpass';
    hp.frequency.value = 7200;
    const g = ctx.createGain();
    g.gain.setValueAtTime(vel, t);
    g.gain.exponentialRampToValueAtTime(0.0008, t + 0.045);
    noise.connect(hp);
    hp.connect(g);
    g.connect(drumBus);
    noise.start(t, Math.random() * 0.5);
    noise.stop(t + 0.06);
  }

  /* sequencer: 4 bars of 16 steps; every fourth pass drops the drums */

  function scheduleStep(s, t) {
    const bar = s >> 4;
    const inBar = s & 15;
    const beat = inBar >> 2;
    const sub = inBar & 3;
    const chord = CHORDS[bar];
    const drums = loop % 4 !== 3;
    const swung = t + (sub === 2 ? SIXTEENTH * 0.22 : 0);

    if (inBar === 0) {
      pad(chord.pad, t, SIXTEENTH * 16);
      bass(chord.bass, t, SIXTEENTH * 6);
    }
    if (inBar === 8) bass(chord.bass, t, SIXTEENTH * 5);

    if (drums) {
      if (sub === 0 && (beat === 0 || beat === 2)) kick(t);
      if (bar === 3 && inBar === 14 && Math.random() < 0.6) kick(t, 0.6);
      if (sub === 0 && (beat === 1 || beat === 3)) snare(t);
    }
    if ((sub === 0 || sub === 2) && Math.random() > 0.08) hat(swung, sub === 0 ? 0.05 : 0.032);

    if ((sub === 0 || sub === 2) && Math.random() < (drums ? 0.3 : 0.45)) {
      const moves = [-2, -1, -1, 0, 1, 1, 2];
      melody = Math.max(2, Math.min(SCALE.length - 1, melody + moves[Math.floor(Math.random() * moves.length)]));
      pluck(SCALE[melody], swung, 0.7 + Math.random() * 0.3);
    }
  }

  function scheduler() {
    while (nextTime < ctx.currentTime + 0.15) {
      scheduleStep(step, nextTime);
      nextTime += SIXTEENTH;
      step = (step + 1) % 64;
      if (step === 0) loop++;
    }
  }

  function runScheduler() {
    if (timer) return;
    nextTime = ctx.currentTime + 0.08;
    scheduler();
    timer = setInterval(scheduler, 25);
  }

  function haltScheduler() {
    clearInterval(timer);
    timer = 0;
  }

  async function start() {
    if (!AC) return;
    if (!ctx) build();
    clearTimeout(stopTimer);
    playing = true;
    setUI();
    store.set('on');
    await ctx.resume();
    runScheduler();
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.setTargetAtTime(0.5, ctx.currentTime, 0.7);
    kickLoops();
  }

  function stop() {
    playing = false;
    setUI();
    store.set('off');
    if (!ctx) return;
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.setTargetAtTime(0, ctx.currentTime, 0.25);
    stopTimer = setTimeout(() => {
      haltScheduler();
      ctx.suspend();
    }, 1400);
  }

  // background tabs throttle timers, so pause cleanly and pick up again on return
  document.addEventListener('visibilitychange', () => {
    if (!ctx || !playing) return;
    if (document.hidden) {
      haltScheduler();
      ctx.suspend();
    } else {
      ctx.resume().then(runScheduler);
    }
  });

  /* ------------------------------------------------------------------ levels */

  const levels = { energy: 0, pulse: 0, bands: [0, 0, 0, 0], peak: 0 };
  let bassAvg = 0;
  let lastRead = -1;

  function readLevels() {
    // the buttons and the dots both ask every frame; analyse once per frame
    const now = performance.now();
    if (now - lastRead < 6) return levels;
    lastRead = now;
    if (!ctx || !playing) {
      levels.energy *= 0.9;
      levels.pulse *= 0.85;
      levels.bands = levels.bands.map((b) => b * 0.85);
      return levels;
    }
    analyser.getByteFrequencyData(freqData);
    const hz = ctx.sampleRate / analyser.fftSize;
    const avg = (lo, hi) => {
      const a = Math.max(1, Math.floor(lo / hz));
      const b = Math.max(a + 1, Math.ceil(hi / hz));
      let s = 0;
      for (let i = a; i < b; i++) s += freqData[i];
      return s / ((b - a) * 255);
    };
    const bass = avg(35, 140);
    bassAvg += (bass - bassAvg) * 0.03;
    levels.pulse = Math.max(0, Math.min(1, (bass - bassAvg * 0.92) * 5));
    levels.energy += (Math.min(1, avg(35, 4000) * 1.6) - levels.energy) * 0.2;
    levels.bands = [bass, avg(150, 500), avg(500, 2000), avg(2000, 8000)].map((v) => Math.min(1, v * 1.5));
    return levels;
  }

  function peak() {
    if (!analyser) return 0;
    analyser.getFloatTimeDomainData(timeData);
    let p = 0;
    for (let i = 0; i < timeData.length; i++) p = Math.max(p, Math.abs(timeData[i]));
    return p;
  }

  /* ------------------------------------------------------------------ UI */

  function setUI() {
    toggles.forEach((btn) => {
      btn.setAttribute('aria-pressed', String(playing));
      const text = playing ? btn.dataset.on : btn.dataset.off;
      const label = btn.querySelector('.sound-label');
      if (label) label.textContent = text;
      btn.title = text;
    });
  }

  if (!AC) {
    toggles.forEach((btn) => { btn.hidden = true; });
  } else {
    toggles.forEach((btn) => btn.addEventListener('click', () => (playing ? stop() : start())));
    setUI();

    // visitor had sound on: continue after their first interaction on this page
    if (store.get() === 'on') {
      const resume = (e) => {
        if (e.target.closest && e.target.closest('[data-sound-toggle]')) return;
        window.removeEventListener('pointerdown', resume, true);
        window.removeEventListener('keydown', resume, true);
        if (!playing) start();
      };
      window.addEventListener('pointerdown', resume, true);
      window.addEventListener('keydown', resume, true);
    }
  }

  // equalizer bars inside the sound buttons follow the music
  const bars = toggles.map((btn) => [...btn.querySelectorAll('.eq i')]);
  let barsRaf = 0;
  function drawBars() {
    const l = readLevels();
    bars.forEach((set) => set.forEach((bar, i) => {
      bar.style.transform = `scaleY(${(0.25 + l.bands[i % 4] * 0.75).toFixed(3)})`;
    }));
    const settled = !playing && l.bands.every((b) => b < 0.01);
    if (settled) {
      bars.forEach((set) => set.forEach((bar) => { bar.style.transform = ''; }));
      barsRaf = 0;
    } else {
      barsRaf = requestAnimationFrame(drawBars);
    }
  }

  /* ------------------------------------------------------------------ hero dots */

  let dotsKick = () => {};

  function initDots() {
    if (!dotsHost) return;
    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-hidden', 'true');
    dotsHost.appendChild(canvas);
    dotsHost.classList.add('is-live');
    const g = canvas.getContext('2d');

    const SPACING = 13;
    const HISTORY = 52;
    const hist = new Float32Array(HISTORY).fill(0.3);
    let pts = new Float32Array(0);
    let W = 0;
    let H = 0;
    let dpr = 1;
    let mix = 0;
    let visible = true;
    let raf = 0;
    let frameNo = 0;

    function layout() {
      const r = dotsHost.getBoundingClientRect();
      W = r.width;
      H = r.height;
      dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      // same footprint as the old CSS mask: ellipse, closest-side, centred at 50% 62%
      const cx = W / 2;
      const cy = H * 0.62;
      const rx = W / 2;
      const ry = Math.max(1, Math.min(cy, H - cy));
      const list = [];
      for (let y = SPACING / 2; y < H; y += SPACING) {
        for (let x = SPACING / 2; x < W; x += SPACING) {
          const dx = (x - cx) / rx;
          const dy = (y - cy) / ry;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < 1) list.push(x, y, d);
        }
      }
      pts = new Float32Array(list);
      draw();
    }

    function draw() {
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.clearRect(0, 0, W, H);
      g.beginPath();
      const maxR = SPACING * 0.21;
      for (let i = 0; i < pts.length; i += 3) {
        const d = pts[i + 2];
        const f = 1 - d; // linear falloff keeps the halo wide
        const v = hist[Math.min(HISTORY - 1, (d * (HISTORY - 1)) | 0)];
        const r = maxR * Math.sqrt(f) * (0.45 + v * 1.25);
        if (r < 0.35) continue;
        g.moveTo(pts[i] + r, pts[i + 1]);
        g.arc(pts[i], pts[i + 1], r, 0, Math.PI * 2);
      }
      g.globalAlpha = 0.62;
      g.fillStyle = '#D9541E';
      g.fill();
    }

    function tick(now) {
      raf = 0;
      if (!visible || document.hidden) return;
      frameNo++;
      const l = readLevels();
      mix += ((playing ? 1 : 0) - mix) * 0.05;
      const idle = 0.4 + 0.12 * Math.sin(now / 1000 * 1.3);
      const music = Math.min(1, 0.18 + l.energy * 0.55 + l.pulse * 0.9);
      // newest value at the centre; older values have travelled further out
      hist.copyWithin(1, 0);
      hist[0] = idle * (1 - mix) + music * mix;
      // idle breathing only needs ~30fps
      if (mix > 0.02 || frameNo % 2 === 0) draw();
      raf = requestAnimationFrame(tick);
    }

    dotsKick = () => {
      if (!raf && !reduceMotion && visible) raf = requestAnimationFrame(tick);
    };

    new ResizeObserver(layout).observe(dotsHost);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        if (visible) dotsKick();
      }).observe(dotsHost);
    }
    document.addEventListener('visibilitychange', () => { if (!document.hidden) dotsKick(); });
    layout();
    dotsKick();
  }

  function kickLoops() {
    if (!barsRaf) barsRaf = requestAnimationFrame(drawBars);
    dotsKick();
  }

  initDots();

  // small read-only hook, handy for debugging in the console
  window.SiteSound = {
    get playing() { return playing; },
    levels: () => ({ ...levels, bands: [...levels.bands] }),
    peak,
  };
})();
