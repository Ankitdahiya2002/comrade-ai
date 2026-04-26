# Comrade AI Research Documentation

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Comrade AI — The Future of Intelligent Collaboration</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:      #0A0C14;
      --bg2:     #111420;
      --bg3:     #181C2E;
      --card:    #1C2035;
      --accent:  #5B6EF5;
      --accent2: #8B5CF6;
      --accent3: #22D3EE;
      --accent4: #F472B6;
      --text:    #F0F2FF;
      --muted:   #8B92B8;
      --border:  rgba(91,110,245,0.2);
    }

    html { scroll-behavior: smooth; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'DM Sans', sans-serif;
      line-height: 1.6;
      overflow-x: hidden;
    }

    h1, h2, h3, .brand { font-family: 'Syne', sans-serif; }

    /* ── NAV ── */
    nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      display: flex; align-items: center; justify-content: space-between;
      padding: 1rem 2.5rem;
      background: rgba(10,12,20,0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }
    .nav-brand {
      font-family: 'Syne', sans-serif;
      font-size: 1.25rem; font-weight: 800;
      background: linear-gradient(135deg,#5B6EF5,#22D3EE);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .nav-links { display: flex; gap: 2rem; list-style: none; }
    .nav-links a {
      color: var(--muted); text-decoration: none; font-size: .9rem;
      transition: color .2s;
    }
    .nav-links a:hover { color: var(--text); }
    .nav-cta {
      background: linear-gradient(135deg,#5B6EF5,#8B5CF6);
      color: #fff; border: none; padding: 9px 22px;
      border-radius: 10px; font-size: .875rem; font-weight: 500;
      cursor: pointer; font-family: 'DM Sans', sans-serif;
      transition: transform .2s, box-shadow .2s;
    }
    .nav-cta:hover { transform: translateY(-1px); box-shadow: 0 8px 28px rgba(91,110,245,.4); }

    /* ── HERO ── */
    .hero {
      min-height: 100vh;
      display: grid; place-items: center;
      position: relative; overflow: hidden;
      padding: 7rem 2rem 4rem;
    }
    .hero-bg { position: absolute; inset: 0; pointer-events: none; }
    .hero-content { position: relative; z-index: 2; text-align: center; max-width: 860px; }

    .badge {
      display: inline-flex; align-items: center; gap: 8px;
      background: rgba(91,110,245,0.12);
      border: 1px solid var(--border);
      border-radius: 999px; padding: 6px 18px;
      font-size: 12px; color: var(--accent3);
      margin-bottom: 2rem; letter-spacing: .06em;
      text-transform: uppercase;
    }
    .badge-dot {
      width: 6px; height: 6px;
      background: var(--accent3); border-radius: 50%;
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%,100% { opacity:1; transform:scale(1); }
      50%      { opacity:.4; transform:scale(.7); }
    }

    h1 {
      font-size: clamp(3rem, 7.5vw, 5.5rem);
      font-weight: 800; line-height: 1.08;
      letter-spacing: -.035em; margin-bottom: 1.5rem;
    }
    .grad {
      background: linear-gradient(135deg,#5B6EF5 0%,#8B5CF6 50%,#22D3EE 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .hero p {
      font-size: 1.15rem; color: var(--muted);
      max-width: 580px; margin: 0 auto 2.5rem; font-weight: 300;
    }
    .cta-row { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }

    .btn-primary {
      background: linear-gradient(135deg,#5B6EF5,#8B5CF6);
      color: #fff; border: none; padding: 15px 36px;
      border-radius: 12px; font-size: 15px; font-weight: 500;
      cursor: pointer; font-family: 'DM Sans', sans-serif;
      transition: transform .2s, box-shadow .2s;
    }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 14px 44px rgba(91,110,245,.45); }

    .btn-outline {
      background: transparent; color: var(--text);
      border: 1px solid var(--border); padding: 15px 36px;
      border-radius: 12px; font-size: 15px;
      cursor: pointer; font-family: 'DM Sans', sans-serif;
      transition: border-color .2s, background .2s;
    }
    .btn-outline:hover { border-color: var(--accent); background: rgba(91,110,245,.08); }

    /* hero stats */
    .hero-stats {
      display: flex; gap: 3rem; justify-content: center;
      margin-top: 3.5rem; flex-wrap: wrap;
    }
    .stat-item { text-align: center; }
    .stat-num {
      font-family: 'Syne', sans-serif;
      font-size: 2rem; font-weight: 800;
      background: linear-gradient(135deg,#5B6EF5,#22D3EE);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .stat-label { font-size: .8rem; color: var(--muted); margin-top: .2rem; }

    /* ── MODELS STRIP ── */
    .models-strip {
      background: var(--bg2);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      padding: 1.4rem 2rem;
      display: flex; justify-content: center;
      gap: 2.5rem; flex-wrap: wrap; align-items: center;
    }
    .model-pill { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); }
    .model-pill strong { color: var(--text); font-weight: 500; }
    .m-dot { width: 8px; height: 8px; border-radius: 50%; }
    .strip-sep { color: rgba(255,255,255,.12); font-size: 1.2rem; }

    /* ── SECTIONS ── */
    section { padding: 5.5rem 2rem; }
    .inner { max-width: 1100px; margin: 0 auto; }

    .section-label {
      font-size: 11px; letter-spacing: .18em;
      text-transform: uppercase; color: var(--accent);
      margin-bottom: .75rem;
    }
    .section-title {
      font-size: clamp(1.9rem, 4vw, 2.8rem);
      font-weight: 800; letter-spacing: -.025em;
      margin-bottom: 1rem; line-height: 1.15;
    }
    .section-sub {
      color: var(--muted); font-size: 1.05rem;
      max-width: 520px; font-weight: 300;
    }

    /* ── ARCH SECTION ── */
    .arch-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem; margin-top: 3rem;
    }
    @media(max-width:680px){ .arch-grid{ grid-template-columns:1fr; } }

    .arch-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px; padding: 2rem;
      transition: border-color .3s, transform .3s;
    }
    .arch-card:hover { border-color: rgba(91,110,245,.5); transform: translateY(-4px); }
    .arch-icon {
      width: 48px; height: 48px; border-radius: 12px;
      display: flex; align-items: center; justify-content: center;
      margin-bottom: 1.25rem;
    }
    .arch-card h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: .5rem; }
    .arch-card p { font-size: .9rem; color: var(--muted); line-height: 1.75; }
    .tag {
      display: inline-block;
      background: rgba(34,211,238,.1); color: var(--accent3);
      border-radius: 6px; padding: 3px 10px;
      font-size: 11px; font-weight: 500; margin-top: .75rem;
    }

    /* ── DATA FEATURES ── */
    .alt-bg { background: var(--bg2); }

    .features-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit,minmax(280px,1fr));
      gap: 1.5rem; margin-top: 3rem;
    }
    .feat-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px; padding: 1.75rem;
      transition: border-color .3s, transform .3s;
    }
    .feat-card:hover { border-color: rgba(91,110,245,.4); transform: translateY(-3px); }
    .feat-num {
      font-family: 'Syne', sans-serif;
      font-size: 2.4rem; font-weight: 800;
      color: rgba(91,110,245,.18);
      letter-spacing: -.04em; margin-bottom: 1rem;
    }
    .feat-card h3 { font-size: 1rem; font-weight: 600; margin-bottom: .5rem; }
    .feat-card p { font-size: .875rem; color: var(--muted); line-height: 1.75; }

    /* ── CREATIVE SECTION ── */
    .creative-showcase {
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 24px; padding: 2.5rem;
      margin-top: 3rem; text-align: center;
    }
    .style-pills {
      display: flex; flex-wrap: wrap; gap: 10px;
      justify-content: center; margin: 1.5rem 0;
    }
    .style-pill {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 999px; padding: 8px 22px;
      font-size: 13px; cursor: pointer;
      transition: all .2s; color: var(--muted);
      font-family: 'DM Sans', sans-serif;
    }
    .style-pill:hover,
    .style-pill.active {
      background: linear-gradient(135deg,#5B6EF5,#8B5CF6);
      color: #fff; border-color: transparent;
    }
    .creative-hint { color: var(--muted); font-size: .875rem; }

    /* ── SECURITY SECTION ── */
    .security-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3rem; margin-top: 3rem; align-items: center;
    }
    @media(max-width:680px){ .security-row{ grid-template-columns:1fr; } }

    .sec-list { list-style: none; display: flex; flex-direction: column; gap: 1.25rem; }
    .sec-list li { display: flex; align-items: flex-start; gap: 14px; }
    .sec-list li > div:last-child { font-size: .9rem; color: var(--muted); }
    .sec-list li strong { color: var(--text); display: block; font-size: .95rem; margin-bottom: .2rem; }
    .check {
      width: 24px; height: 24px; min-width: 24px;
      background: rgba(91,110,245,.12);
      border-radius: 50%; border: 1px solid rgba(91,110,245,.3);
      display: flex; align-items: center; justify-content: center;
      margin-top: 2px;
    }

    /* ── OPERATIONAL FEATURES ── */
    .ops-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit,minmax(200px,1fr));
      gap: 1.25rem; margin-top: 3rem;
    }
    .ops-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px; padding: 1.5rem;
      transition: border-color .3s;
    }
    .ops-card:hover { border-color: rgba(91,110,245,.4); }
    .ops-card h4 { font-size: .95rem; font-weight: 600; margin: .75rem 0 .4rem; }
    .ops-card p { font-size: .82rem; color: var(--muted); line-height: 1.7; }

    /* ── CTA SECTION ── */
    .cta-section {
      text-align: center;
      background: radial-gradient(ellipse 80% 60% at 50% 50%,
        rgba(91,110,245,.12) 0%, transparent 70%);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      padding: 7rem 2rem;
    }
    .cta-section h2 {
      font-size: clamp(2.2rem,5vw,3.5rem);
      font-weight: 800; letter-spacing: -.03em;
      margin-bottom: 1rem; line-height: 1.1;
    }
    .cta-section p { color: var(--muted); max-width: 480px; margin: 0 auto 2.5rem; font-weight: 300; }

    /* ── FOOTER ── */
    footer {
      background: var(--bg2);
      border-top: 1px solid var(--border);
      padding: 3rem 2rem; text-align: center;
    }
    .footer-brand {
      font-family: 'Syne', sans-serif;
      font-size: 1.5rem; font-weight: 800;
      margin-bottom: .5rem;
    }
    footer .footer-sub { color: var(--muted); font-size: .875rem; }
    footer .footer-copy { color: rgba(139,146,184,.4); font-size: .8rem; margin-top: .5rem; }

    /* ── RESPONSIVE NAV ── */
    @media(max-width:768px){
      .nav-links { display: none; }
      nav { padding: 1rem 1.5rem; }
    }
  </style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="nav-brand">Comrade AI</div>
  <ul class="nav-links">
    <li><a href="#architecture">Architecture</a></li>
    <li><a href="#data">Data Intelligence</a></li>
    <li><a href="#creative">Creative AI</a></li>
    <li><a href="#security">Security</a></li>
  </ul>
  <button class="nav-cta">Get Early Access</button>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-bg">
    <svg width="100%" height="100%" viewBox="0 0 1400 800"
         preserveAspectRatio="xMidYMid slice"
         xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="hg1" cx="28%" cy="45%">
          <stop offset="0%" stop-color="#5B6EF5" stop-opacity=".32"/>
          <stop offset="100%" stop-color="#5B6EF5" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="hg2" cx="72%" cy="58%">
          <stop offset="0%" stop-color="#8B5CF6" stop-opacity=".26"/>
          <stop offset="100%" stop-color="#8B5CF6" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="hg3" cx="52%" cy="18%">
          <stop offset="0%" stop-color="#22D3EE" stop-opacity=".18"/>
          <stop offset="100%" stop-color="#22D3EE" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <ellipse cx="392" cy="360" rx="480" ry="340" fill="url(#hg1)"/>
      <ellipse cx="1008" cy="464" rx="440" ry="300" fill="url(#hg2)"/>
      <ellipse cx="700" cy="144" rx="360" ry="240" fill="url(#hg3)"/>

      <!-- grid lines -->
      <g stroke="#5B6EF5" stroke-width="0.4" opacity="0.1">
        <line x1="0" y1="400" x2="1400" y2="400"/>
        <line x1="700" y1="0" x2="700" y2="800"/>
        <circle cx="700" cy="400" r="160" fill="none"/>
        <circle cx="700" cy="400" r="300" fill="none"/>
        <circle cx="700" cy="400" r="460" fill="none"/>
        <circle cx="700" cy="400" r="620" fill="none"/>
      </g>

      <!-- node dots -->
      <g fill="#5B6EF5" opacity=".5">
        <circle cx="210" cy="160" r="2.5"/>
        <circle cx="480" cy="90" r="2"/>
        <circle cx="820" cy="130" r="2.5"/>
        <circle cx="1120" cy="220" r="2"/>
        <circle cx="160" cy="560" r="2.5"/>
        <circle cx="400" cy="640" r="2"/>
        <circle cx="880" cy="660" r="2.5"/>
        <circle cx="1180" cy="500" r="2"/>
        <circle cx="320" cy="350" r="1.5"/>
        <circle cx="1060" cy="310" r="1.5"/>
        <circle cx="600" cy="680" r="2"/>
        <circle cx="1000" cy="100" r="2"/>
      </g>
      <g fill="#22D3EE" opacity=".35">
        <circle cx="560" cy="200" r="1.5"/>
        <circle cx="840" cy="300" r="1.5"/>
        <circle cx="1240" cy="360" r="2"/>
        <circle cx="120" cy="400" r="1.5"/>
        <circle cx="700" cy="520" r="1.5"/>
      </g>

      <!-- connectors -->
      <g stroke="#22D3EE" stroke-width="0.5" opacity=".18" fill="none">
        <line x1="210" y1="160" x2="480" y2="90"/>
        <line x1="480" y1="90" x2="820" y2="130"/>
        <line x1="820" y1="130" x2="1120" y2="220"/>
        <line x1="160" y1="560" x2="400" y2="640"/>
        <line x1="400" y1="640" x2="880" y2="660"/>
        <line x1="210" y1="160" x2="320" y2="350"/>
        <line x1="1120" y1="220" x2="1180" y2="500"/>
        <line x1="880" y1="660" x2="1180" y2="500"/>
        <line x1="560" y1="200" x2="840" y2="300"/>
        <line x1="840" y1="300" x2="1060" y2="310"/>
      </g>
    </svg>
  </div>

  <div class="hero-content">
    <div class="badge">
      <span class="badge-dot"></span>
      Dual-Engine AI Architecture — Now Live
    </div>
    <h1>The Future of<br><span class="grad">Intelligent Collaboration</span></h1>
    <p>A high-fidelity platform where researchers, analysts, and creators harness state-of-the-art AI — built for enterprise-grade reliability and creative synthesis.</p>
    <div class="cta-row">
      <button class="btn-primary">Start for Free</button>
      <button class="btn-outline">Watch Demo</button>
    </div>
    <div class="hero-stats">
      <div class="stat-item">
        <div class="stat-num">3</div>
        <div class="stat-label">AI Engines</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">99.9%</div>
        <div class="stat-label">Uptime SLA</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">4K</div>
        <div class="stat-label">Image Output</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">RLS</div>
        <div class="stat-label">Row-Level Security</div>
      </div>
    </div>
  </div>
</section>

<!-- MODELS STRIP -->
<div class="models-strip">
  <div class="model-pill">
    <div class="m-dot" style="background:#5B6EF5"></div>
    <strong>Zappes 3.5</strong> Primary Reasoning
  </div>
  <span class="strip-sep">|</span>
  <div class="model-pill">
    <div class="m-dot" style="background:#22D3EE"></div>
    <strong>storm pro</strong> High-Throughput
  </div>
  <span class="strip-sep">|</span>
  <div class="model-pill">
    <div class="m-dot" style="background:#F472B6"></div>
    <strong>graphica 3.0 AI</strong> Image Synthesis
  </div>
  <span class="strip-sep">|</span>
  <div class="model-pill">
    <div class="m-dot" style="background:#22c55e; animation: pulse 2s infinite"></div>
    <strong>Auto Fallback</strong> Always On
  </div>
</div>

<!-- ARCHITECTURE -->
<section id="architecture">
  <div class="inner">
    <div class="section-label">Core Architecture</div>
    <div class="section-title">Dual-Engine AI Power</div>
    <p class="section-sub">Intelligent routing ensures maximum uptime — if one model is unavailable, the other takes over instantly with zero disruption.</p>

    <!-- Architecture SVG diagram -->
    <div style="margin-top:2.5rem; background:var(--card); border:1px solid var(--border); border-radius:20px; padding:2rem;">
      <svg width="100%" viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5"
                  markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
                  stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </marker>
        </defs>

        <!-- User Request -->
        <rect x="260" y="16" width="160" height="56" rx="12"
              fill="#111420" stroke="#5B6EF5" stroke-width="1"/>
        <text x="340" y="42" text-anchor="middle"
              font-family="Syne,sans-serif" font-size="13" font-weight="700" fill="#F0F2FF">User Request</text>
        <text x="340" y="60" text-anchor="middle"
              font-family="DM Sans,sans-serif" font-size="11" fill="#8B92B8">Incoming query</text>

        <!-- Smart Router -->
        <rect x="252" y="108" width="176" height="56" rx="12"
              fill="#111420" stroke="#22D3EE" stroke-width="1.5"/>
        <text x="340" y="134" text-anchor="middle"
              font-family="Syne,sans-serif" font-size="13" font-weight="700" fill="#22D3EE">Smart Router</text>
        <text x="340" y="152" text-anchor="middle"
              font-family="DM Sans,sans-serif" font-size="11" fill="#8B92B8">Intelligent dispatch</text>

        <!-- Connector top -->
        <line x1="340" y1="72" x2="340" y2="108"
              stroke="#22D3EE" stroke-width="1" marker-end="url(#arr)"/>

        <!-- Claude -->
        <rect x="44" y="200" width="160" height="56" rx="12"
              fill="#111420" stroke="#5B6EF5" stroke-width="1"/>
        <text x="124" y="225" text-anchor="middle"
              font-family="Syne,sans-serif" font-size="12" font-weight="700" fill="#5B6EF5">Zappes 3.5</text>
        <text x="124" y="243" text-anchor="middle"
              font-family="DM Sans,sans-serif" font-size="10" fill="#8B92B8">Primary · Reasoning</text>

        <!-- Gemini -->
        <rect x="260" y="200" width="160" height="56" rx="12"
              fill="#111420" stroke="#8B5CF6" stroke-width="1"/>
        <text x="340" y="225" text-anchor="middle"
              font-family="Syne,sans-serif" font-size="12" font-weight="700" fill="#8B5CF6">storm pro</text>
        <text x="340" y="243" text-anchor="middle"
              font-family="DM Sans,sans-serif" font-size="10" fill="#8B92B8">Fallback · Speed</text>

        <!-- graphica 3.0 -->
        <rect x="476" y="200" width="160" height="56" rx="12"
              fill="#111420" stroke="#F472B6" stroke-width="1"/>
        <text x="556" y="225" text-anchor="middle"
              font-family="Syne,sans-serif" font-size="12" font-weight="700" fill="#F472B6">graphica 3.0 AI</text>
        <text x="556" y="243" text-anchor="middle"
              font-family="DM Sans,sans-serif" font-size="10" fill="#8B92B8">Visual · Creative</text>

        <!-- Connectors down -->
        <line x1="300" y1="168" x2="190" y2="200"
              stroke="#5B6EF5" stroke-width="1" marker-end="url(#arr)"/>
        <line x1="340" y1="164" x2="340" y2="200"
              stroke="#8B5CF6" stroke-width="1" marker-end="url(#arr)"/>
        <line x1="380" y1="168" x2="490" y2="200"
              stroke="#F472B6" stroke-width="1" marker-end="url(#arr)"/>
      </svg>
    </div>

    <div class="arch-grid">
      <div class="arch-card">
        <div class="arch-icon" style="background:rgba(91,110,245,.14)">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="#5B6EF5" stroke-width="1.5"/>
            <circle cx="12" cy="12" r="3" fill="#5B6EF5"/>
            <line x1="12" y1="3" x2="12" y2="9" stroke="#5B6EF5" stroke-width="1.5"/>
            <line x1="12" y1="15" x2="12" y2="21" stroke="#5B6EF5" stroke-width="1.5"/>
            <line x1="3" y1="12" x2="9" y2="12" stroke="#5B6EF5" stroke-width="1.5"/>
            <line x1="15" y1="12" x2="21" y2="12" stroke="#5B6EF5" stroke-width="1.5"/>
          </svg>
        </div>
        <h3>Zappes 3.5</h3>
        <p>Our primary reasoning engine. Optimized for complex coding, logical analysis, and structured responses requiring deep contextual understanding and nuanced output.</p>
        <span class="tag">Primary Engine</span>
      </div>
      <div class="arch-card">
        <div class="arch-icon" style="background:rgba(34,211,238,.1)">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <polygon points="13,2 3,14 12,14 11,22 21,10 12,10"
                     stroke="#22D3EE" stroke-width="1.5" stroke-linejoin="round"/>
          </svg>
        </div>
        <h3>storm pro</h3>
        <p>Hyper-fast fallback model for rapid ideation and large-scale context processing. Seamlessly activates the moment maximum throughput is required.</p>
        <span class="tag" style="background:rgba(34,211,238,.1);color:#22D3EE">Auto Fallback</span>
      </div>
    </div>
  </div>
</section>

<!-- DATA INTELLIGENCE -->
<section id="data" class="alt-bg">
  <div class="inner">
    <div class="section-label">Data Intelligence</div>
    <div class="section-title">Analyze Any Format,<br>Instantly</div>
    <p class="section-sub">Native support for documents, spreadsheets, and raw data — the AI understands structure, context, and meaning across every file type.</p>

    <div class="features-grid">
      <!-- PDF -->
      <div class="feat-card">
        <svg width="44" height="44" viewBox="0 0 44 44" fill="none" style="margin-bottom:1rem">
          <rect width="44" height="44" rx="11" fill="rgba(244,72,182,.1)"/>
          <rect x="12" y="9" width="20" height="27" rx="3" stroke="#F472B6" stroke-width="1.2"/>
          <line x1="16" y1="15" x2="28" y2="15" stroke="#F472B6" stroke-width="1"/>
          <line x1="16" y1="20" x2="28" y2="20" stroke="#F472B6" stroke-width="1"/>
          <line x1="16" y1="25" x2="24" y2="25" stroke="#F472B6" stroke-width="1"/>
          <rect x="22" y="27" width="12" height="9" rx="2" fill="rgba(244,72,182,.2)" stroke="#F472B6" stroke-width=".8"/>
          <text x="28" y="34" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="5" font-weight="600" fill="#F472B6">PDF</text>
        </svg>
        <div class="feat-num">01</div>
        <h3>PDF Extraction</h3>
        <p>Intelligently parses PDFs with page awareness and structural context. Deep document interrogation across hundreds of pages with semantic understanding.</p>
      </div>

      <!-- Excel -->
      <div class="feat-card">
        <svg width="44" height="44" viewBox="0 0 44 44" fill="none" style="margin-bottom:1rem">
          <rect width="44" height="44" rx="11" fill="rgba(34,211,238,.1)"/>
          <rect x="9" y="11" width="26" height="23" rx="3" stroke="#22D3EE" stroke-width="1.2"/>
          <line x1="9" y1="17" x2="35" y2="17" stroke="#22D3EE" stroke-width=".8"/>
          <line x1="9" y1="23" x2="35" y2="23" stroke="#22D3EE" stroke-width=".8"/>
          <line x1="18" y1="17" x2="18" y2="34" stroke="#22D3EE" stroke-width=".8"/>
          <line x1="27" y1="17" x2="27" y2="34" stroke="#22D3EE" stroke-width=".8"/>
          <rect x="20" y="19" width="5" height="3" rx="1" fill="rgba(34,211,238,.4)"/>
          <rect x="29" y="25" width="4" height="3" rx="1" fill="rgba(34,211,238,.3)"/>
        </svg>
        <div class="feat-num">02</div>
        <h3>Excel &amp; CSV Analysis</h3>
        <p>Native .xlsx, .xls, and .csv support. Perform trend analysis, statistical summaries, and data cleaning tasks directly from your spreadsheets.</p>
      </div>

      <!-- Text -->
      <div class="feat-card">
        <svg width="44" height="44" viewBox="0 0 44 44" fill="none" style="margin-bottom:1rem">
          <rect width="44" height="44" rx="11" fill="rgba(91,110,245,.1)"/>
          <line x1="10" y1="14" x2="34" y2="14" stroke="#5B6EF5" stroke-width="1.3"/>
          <line x1="10" y1="20" x2="34" y2="20" stroke="#5B6EF5" stroke-width="1.3"/>
          <line x1="10" y1="26" x2="34" y2="26" stroke="#5B6EF5" stroke-width="1.3"/>
          <line x1="10" y1="32" x2="24" y2="32" stroke="#5B6EF5" stroke-width="1.3"/>
          <circle cx="32" cy="32" r="5" fill="rgba(91,110,245,.2)" stroke="#5B6EF5" stroke-width="1"/>
          <line x1="30" y1="32" x2="34" y2="32" stroke="#5B6EF5" stroke-width="1"/>
          <line x1="32" y1="30" x2="32" y2="34" stroke="#5B6EF5" stroke-width="1"/>
        </svg>
        <div class="feat-num">03</div>
        <h3>Plain Text Processing</h3>
        <p>High-speed extraction for log files, research notes, and large text datasets. Handles millions of tokens with precision and context retention.</p>
      </div>
    </div>
  </div>
</section>

<!-- CREATIVE ARTS -->
<section id="creative">
  <div class="inner">
    <div class="section-label">Creative Arts &amp; Synthesis</div>
    <div class="section-title">From Text to<br>Visual Masterpiece</div>
    <p class="section-sub">Powered by graphica 3.0 AI — transform descriptions into cinematic 4K-ready visuals with full artistic style control and iterative refinement.</p>

    <div class="creative-showcase">
      <!-- Style preset preview gallery -->
      <svg width="100%" viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="cg1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#5B6EF5" stop-opacity=".35"/>
            <stop offset="100%" stop-color="#8B5CF6" stop-opacity=".12"/>
          </linearGradient>
          <linearGradient id="cg2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#22D3EE" stop-opacity=".35"/>
            <stop offset="100%" stop-color="#5B6EF5" stop-opacity=".12"/>
          </linearGradient>
          <linearGradient id="cg3" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#F472B6" stop-opacity=".35"/>
            <stop offset="100%" stop-color="#8B5CF6" stop-opacity=".12"/>
          </linearGradient>
          <linearGradient id="cg4" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#22c55e" stop-opacity=".35"/>
            <stop offset="100%" stop-color="#22D3EE" stop-opacity=".12"/>
          </linearGradient>
        </defs>

        <!-- Card 1 - Ghibli -->
        <rect x="20" y="20" width="135" height="160" rx="14" fill="url(#cg1)" stroke="rgba(91,110,245,.4)" stroke-width="1"/>
        <ellipse cx="88" cy="75" rx="28" ry="20" fill="rgba(91,110,245,.25)"/>
        <ellipse cx="88" cy="90" rx="20" ry="10" fill="rgba(91,110,245,.35)"/>
        <rect x="60" y="100" width="56" height="30" rx="4" fill="rgba(91,110,245,.2)"/>
        <circle cx="80" cy="108" r="6" fill="rgba(91,110,245,.4)"/>
        <circle cx="96" cy="105" r="4" fill="rgba(91,110,245,.35)"/>
        <text x="88" y="165" text-anchor="middle" font-family="Syne,sans-serif" font-size="12" font-weight="700" fill="#8B92B8">Studio Ghibli</text>

        <!-- Card 2 - Anime -->
        <rect x="170" y="20" width="135" height="160" rx="14" fill="url(#cg2)" stroke="rgba(34,211,238,.4)" stroke-width="1"/>
        <circle cx="238" cy="72" r="22" fill="rgba(34,211,238,.2)" stroke="rgba(34,211,238,.5)" stroke-width="1"/>
        <line x1="220" y1="68" x2="228" y2="74" stroke="#22D3EE" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="248" y1="68" x2="256" y2="74" stroke="#22D3EE" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M228 82 Q238 90 248 82" stroke="#22D3EE" stroke-width="1" fill="none"/>
        <rect x="218" y="100" width="40" height="6" rx="3" fill="rgba(34,211,238,.5)"/>
        <rect x="222" y="111" width="32" height="5" rx="2.5" fill="rgba(34,211,238,.3)"/>
        <text x="238" y="165" text-anchor="middle" font-family="Syne,sans-serif" font-size="12" font-weight="700" fill="#8B92B8">Anime</text>

        <!-- Card 3 - Photorealistic -->
        <rect x="320" y="20" width="135" height="160" rx="14" fill="url(#cg3)" stroke="rgba(244,72,182,.4)" stroke-width="1"/>
        <rect x="344" y="44" width="87" height="60" rx="6" fill="rgba(244,72,182,.15)" stroke="rgba(244,72,182,.3)" stroke-width=".8"/>
        <circle cx="388" cy="74" r="20" fill="rgba(244,72,182,.25)" stroke="rgba(244,72,182,.5)" stroke-width="1"/>
        <line x1="388" y1="104" x2="388" y2="120" stroke="rgba(244,72,182,.4)" stroke-width="1"/>
        <line x1="372" y1="112" x2="404" y2="112" stroke="rgba(244,72,182,.4)" stroke-width="1"/>
        <text x="388" y="165" text-anchor="middle" font-family="Syne,sans-serif" font-size="12" font-weight="700" fill="#8B92B8">Photorealistic</text>

        <!-- Card 4 - Pixel Art -->
        <rect x="470" y="20" width="135" height="160" rx="14" fill="url(#cg4)" stroke="rgba(34,197,94,.4)" stroke-width="1"/>
        <g fill="rgba(34,197,94,.7)">
          <rect x="506" y="52" width="12" height="12"/>
          <rect x="521" y="52" width="12" height="12"/>
          <rect x="536" y="52" width="12" height="12"/>
          <rect x="506" y="67" width="12" height="12" fill="rgba(34,197,94,.4)"/>
          <rect x="521" y="67" width="12" height="12" fill="rgba(34,197,94,.85)"/>
          <rect x="536" y="67" width="12" height="12" fill="rgba(34,197,94,.6)"/>
          <rect x="506" y="82" width="12" height="12" fill="rgba(34,197,94,.9)"/>
          <rect x="521" y="82" width="12" height="12" fill="rgba(34,197,94,.35)"/>
          <rect x="536" y="82" width="12" height="12" fill="rgba(34,197,94,.5)"/>
          <rect x="513" y="97" width="12" height="12" fill="rgba(34,197,94,.6)"/>
          <rect x="528" y="97" width="12" height="12" fill="rgba(34,197,94,.8)"/>
        </g>
        <text x="538" y="165" text-anchor="middle" font-family="Syne,sans-serif" font-size="12" font-weight="700" fill="#8B92B8">Pixel Art</text>
      </svg>

      <div class="style-pills">
        <div class="style-pill active">Studio Ghibli</div>
        <div class="style-pill">Anime</div>
        <div class="style-pill">Photorealistic</div>
        <div class="style-pill">Pixel Art</div>
        <div class="style-pill">Cinematic 4K</div>
        <div class="style-pill">Watercolor</div>
        <div class="style-pill">Oil Painting</div>
      </div>
      <p class="creative-hint">Refine and evolve generated images through contextual conversation</p>
    </div>
  </div>
</section>

<!-- SECURITY -->
<section id="security" class="alt-bg">
  <div class="inner">
    <div class="section-label">Enterprise-Grade Security</div>
    <div class="section-title">Built for Trust at Scale</div>
    <div class="security-row">
      <ul class="sec-list">
        <li>
          <div class="check">
            <svg width="10" height="10" viewBox="0 0 10 10">
              <polyline points="2,5 4.5,7.5 8,2.5" stroke="#5B6EF5" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <strong>Google OAuth + Mobile OTP</strong>
            Multi-layered authentication with Twilio-based verification for every login attempt.
          </div>
        </li>
        <li>
          <div class="check">
            <svg width="10" height="10" viewBox="0 0 10 10">
              <polyline points="2,5 4.5,7.5 8,2.5" stroke="#5B6EF5" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <strong>Isolated Multi-Tenant Projects</strong>
            Each workspace is fully sandboxed — no data bleeds between research streams or teams.
          </div>
        </li>
        <li>
          <div class="check">
            <svg width="10" height="10" viewBox="0 0 10 10">
              <polyline points="2,5 4.5,7.5 8,2.5" stroke="#5B6EF5" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <strong>Supabase RLS Encryption</strong>
            Row-level security policies ensure your data and chat history are encrypted and inaccessible to unauthorized parties.
          </div>
        </li>
        <li>
          <div class="check">
            <svg width="10" height="10" viewBox="0 0 10 10">
              <polyline points="2,5 4.5,7.5 8,2.5" stroke="#5B6EF5" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <strong>Admin Command Center</strong>
            Centralized user oversight and platform configuration with full audit trails and access logs.
          </div>
        </li>
      </ul>

      <!-- Security SVG diagram -->
      <svg width="100%" viewBox="0 0 320 300" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="secglow" cx="50%" cy="50%">
            <stop offset="0%" stop-color="#5B6EF5" stop-opacity=".22"/>
            <stop offset="100%" stop-color="#5B6EF5" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <circle cx="160" cy="150" r="130" fill="url(#secglow)"/>
        <circle cx="160" cy="150" r="110" fill="none" stroke="rgba(91,110,245,.12)" stroke-width="1" stroke-dasharray="5 5"/>
        <circle cx="160" cy="150" r="78" fill="none" stroke="rgba(91,110,245,.2)" stroke-width="1" stroke-dasharray="4 4"/>
        <circle cx="160" cy="150" r="44" fill="rgba(91,110,245,.08)" stroke="rgba(91,110,245,.35)" stroke-width="1"/>
        <!-- shield icon center -->
        <path d="M160 128 L175 136 L175 152 Q175 165 160 172 Q145 165 145 152 L145 136 Z"
              fill="rgba(91,110,245,.2)" stroke="#5B6EF5" stroke-width="1" stroke-linejoin="round"/>
        <polyline points="154,150 158,155 168,143"
                  stroke="#5B6EF5" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>

        <!-- Outer nodes -->
        <circle cx="160" cy="40" r="22" fill="#1C2035" stroke="rgba(34,211,238,.5)" stroke-width="1"/>
        <text x="160" y="38" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" font-weight="500" fill="#22D3EE">Google</text>
        <text x="160" y="50" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" fill="#22D3EE">OAuth</text>

        <circle cx="271" cy="95" r="22" fill="#1C2035" stroke="rgba(244,72,182,.5)" stroke-width="1"/>
        <text x="271" y="93" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" font-weight="500" fill="#F472B6">Twilio</text>
        <text x="271" y="105" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" fill="#F472B6">OTP</text>

        <circle cx="258" cy="215" r="22" fill="#1C2035" stroke="rgba(139,92,246,.5)" stroke-width="1"/>
        <text x="258" y="213" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" font-weight="500" fill="#8B5CF6">Supabase</text>
        <text x="258" y="225" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" fill="#8B5CF6">RLS</text>

        <circle cx="62" cy="215" r="22" fill="#1C2035" stroke="rgba(34,197,94,.5)" stroke-width="1"/>
        <text x="62" y="213" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" font-weight="500" fill="#22c55e">Multi-</text>
        <text x="62" y="225" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" fill="#22c55e">tenant</text>

        <circle cx="49" cy="95" r="22" fill="#1C2035" stroke="rgba(251,191,36,.5)" stroke-width="1"/>
        <text x="49" y="93" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" font-weight="500" fill="#fbbf24">Admin</text>
        <text x="49" y="105" text-anchor="middle" font-family="DM Sans,sans-serif" font-size="9" fill="#fbbf24">Audit</text>

        <!-- Dashed connectors -->
        <line x1="160" y1="62" x2="160" y2="106" stroke="rgba(34,211,238,.3)" stroke-width="1" stroke-dasharray="3 2"/>
        <line x1="250" y1="113" x2="204" y2="138" stroke="rgba(244,72,182,.3)" stroke-width="1" stroke-dasharray="3 2"/>
        <line x1="238" y1="200" x2="200" y2="178" stroke="rgba(139,92,246,.3)" stroke-width="1" stroke-dasharray="3 2"/>
        <line x1="82" y1="200" x2="124" y2="178" stroke="rgba(34,197,94,.3)" stroke-width="1" stroke-dasharray="3 2"/>
        <line x1="70" y1="113" x2="120" y2="138" stroke="rgba(251,191,36,.3)" stroke-width="1" stroke-dasharray="3 2"/>
      </svg>
    </div>
  </div>
</section>

<!-- OPERATIONAL FEATURES -->
<section>
  <div class="inner">
    <div class="section-label">Operational Features</div>
    <div class="section-title">Everything You Need<br>to Move Fast</div>
    <p class="section-sub">From project isolation to trending dashboards — Comrade AI handles the infrastructure so you can focus on the work.</p>
    <div class="ops-grid">
      <div class="ops-card">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="rgba(91,110,245,.12)"/>
          <rect x="7" y="9" width="8" height="14" rx="2" stroke="#5B6EF5" stroke-width="1.1"/>
          <rect x="17" y="13" width="8" height="10" rx="2" stroke="#5B6EF5" stroke-width="1.1"/>
        </svg>
        <h4>Project Workspaces</h4>
        <p>Manage multiple research streams independently with full data isolation between projects.</p>
      </div>
      <div class="ops-card">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="rgba(34,211,238,.1)"/>
          <path d="M16 7 L19.5 13.5 L27 14.5 L21.5 19.8 L23 27 L16 23.3 L9 27 L10.5 19.8 L5 14.5 L12.5 13.5 Z" stroke="#22D3EE" stroke-width="1.1" fill="none" stroke-linejoin="round"/>
        </svg>
        <h4>Trending Dashboards</h4>
        <p>Stay inspired with daily rotating prompt recommendations curated by topic and domain.</p>
      </div>
      <div class="ops-card">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="rgba(244,72,182,.1)"/>
          <circle cx="16" cy="14" r="5" stroke="#F472B6" stroke-width="1.1"/>
          <path d="M8 25 Q8 20 16 20 Q24 20 24 25" stroke="#F472B6" stroke-width="1.1" fill="none"/>
          <circle cx="22" cy="12" r="3" stroke="#F472B6" stroke-width=".9"/>
          <line x1="25" y1="9" x2="28" y2="7" stroke="#F472B6" stroke-width="1"/>
        </svg>
        <h4>Admin Command Center</h4>
        <p>Centralized management for user oversight, platform configuration, and usage analytics.</p>
      </div>
      <div class="ops-card">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="rgba(139,92,246,.1)"/>
          <rect x="7" y="7" width="18" height="18" rx="3" stroke="#8B5CF6" stroke-width="1.1"/>
          <line x1="7" y1="13" x2="25" y2="13" stroke="#8B5CF6" stroke-width=".8"/>
          <line x1="13" y1="13" x2="13" y2="25" stroke="#8B5CF6" stroke-width=".8"/>
        </svg>
        <h4>Chat History</h4>
        <p>All conversations and project metadata are encrypted and stored securely for future reference.</p>
      </div>
      <div class="ops-card">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="rgba(34,197,94,.1)"/>
          <polygon points="16,6 26,11 26,21 16,26 6,21 6,11" stroke="#22c55e" stroke-width="1.1" fill="none" stroke-linejoin="round"/>
          <circle cx="16" cy="16" r="4" stroke="#22c55e" stroke-width="1"/>
        </svg>
        <h4>Auto Fallback</h4>
        <p>Intelligent routing ensures 99.9% uptime. One engine down? The other activates in milliseconds.</p>
      </div>
    </div>
  </div>
</section>

<!-- CTA -->
<div class="cta-section">
  <div class="section-label" style="text-align:center">Get Started Today</div>
  <h2>Ready to collaborate<br>with <span class="grad">Comrade AI?</span></h2>
  <p>Join researchers, analysts, and creators already building the future with intelligent AI collaboration tools.</p>
  <div class="cta-row">
    <button class="btn-primary" style="padding:16px 44px;font-size:16px">Get Early Access</button>
    <button class="btn-outline" style="padding:16px 44px;font-size:16px">Read the Docs</button>
  </div>
</div>

<!-- FOOTER -->
<footer>
  <div class="footer-brand">Comrade AI</div>
  <p class="footer-sub">The Future of Intelligent Collaboration &nbsp;·&nbsp; Built on Claude, Gemini &amp; graphica 3.0 AI</p>
  <p class="footer-copy">© 2026 Comrade AI. All rights reserved.</p>
</footer>

<script>
  // Style pill toggle
  document.querySelectorAll('.style-pill').forEach(pill => {
    pill.addEventListener('click', function() {
      document.querySelectorAll('.style-pill').forEach(p => p.classList.remove('active'));
      this.classList.add('active');
    });
  });

  // Smooth nav link scroll
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(a.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  // Subtle parallax on hero background
  const heroBg = document.querySelector('.hero-bg');
  if (heroBg) {
    window.addEventListener('mousemove', e => {
      const x = (e.clientX / window.innerWidth - 0.5) * 20;
      const y = (e.clientY / window.innerHeight - 0.5) * 20;
      heroBg.style.transform = `translate(${x}px, ${y}px)`;
    });
  }

  // Intersection observer for fade-in cards
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.arch-card, .feat-card, .ops-card').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(24px)';
    card.style.transition = 'opacity .5s ease, transform .5s ease, border-color .3s';
    observer.observe(card);
  });
</script>
</body>
</html>
