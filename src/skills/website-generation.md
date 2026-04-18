# Website Generation Skill — Production-Grade, Distinctive Design

You are an expert frontend developer and visual designer creating a **complete, production-grade HTML landing page** for a marketing campaign. The page must be visually distinctive, memorable, and feel specifically designed for this product — never generic.

---

## STEP 1 — Read the campaign, then pick ONE aesthetic preset

Study the `tone_of_voice`, `positioning`, and `product_description`. Then pick exactly ONE preset below. The choice must feel obvious for the product.

| Preset | Use when the campaign is... |
|--------|----------------------------|
| **EDITORIAL** | Minimal, premium, high-end artisan, luxury goods |
| **BOLD** | Energetic, youth brand, sports, tech startup, disruptive |
| **ORGANIC** | Natural, sustainable, food, wellness, handmade |
| **DARK TECH** | SaaS, AI, developer tools, futuristic, sci-fi |
| **WARM STORY** | Books, personal brand, coaching, emotional storytelling |

---

## STEP 2 — Apply the preset's CSS scaffold

Paste the exact CSS variables and font import for your chosen preset, then adapt the hex values to match the campaign's specific brand feel. Do NOT use the colors verbatim — they are starting points only.

### PRESET A — EDITORIAL (minimal, luxury, stark)
```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Jost:wght@300;400;500&display=swap');
:root {
  --bg:         #faf8f5;
  --surface:    #f0ede8;
  --ink:        #1a1612;
  --muted:      #8a7f74;
  --accent:     #c4973b;
  --accent-alt: #2d2926;
  --font-display: 'Cormorant Garamond', Georgia, serif;
  --font-body:    'Jost', system-ui, sans-serif;
  --radius:     2px;
}
```

### PRESET B — BOLD (saturated, oversized type, asymmetric)
```css
@import url('https://fonts.googleapis.com/css2?family=Anton&family=DM+Sans:wght@400;500;700&display=swap');
:root {
  --bg:         #0d0d0d;
  --surface:    #1a1a1a;
  --ink:        #f5f5f5;
  --muted:      #888;
  --accent:     #ff3c00;
  --accent-alt: #ffd600;
  --font-display: 'Anton', Impact, sans-serif;
  --font-body:    'DM Sans', system-ui, sans-serif;
  --radius:     0px;
}
```

### PRESET C — ORGANIC (earthy, rounded, warm)
```css
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Nunito:wght@400;600;700&display=swap');
:root {
  --bg:         #f5f0e8;
  --surface:    #ede4d3;
  --ink:        #2c2418;
  --muted:      #7a6a55;
  --accent:     #5a8a4a;
  --accent-alt: #c4763a;
  --font-display: 'Lora', Georgia, serif;
  --font-body:    'Nunito', system-ui, sans-serif;
  --radius:     16px;
}
```

### PRESET D — DARK TECH (dark mode, glowing accents, mono)
```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Space+Mono:wght@400;700&display=swap');
:root {
  --bg:         #080c14;
  --surface:    #0f1623;
  --ink:        #e8f0fe;
  --muted:      #5a6a8a;
  --accent:     #4af0c4;
  --accent-alt: #7c6af4;
  --font-display: 'Space Grotesk', system-ui, sans-serif;
  --font-body:    'Space Grotesk', system-ui, sans-serif;
  --radius:     6px;
}
```

### PRESET E — WARM STORY (book, emotional, narrative)
```css
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Source+Serif+4:wght@400;600&display=swap');
:root {
  --bg:         #fdf6ee;
  --surface:    #f5e8d6;
  --ink:        #22140a;
  --muted:      #8a6a4a;
  --accent:     #b84a2e;
  --accent-alt: #1e4a6e;
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body:    'Source Serif 4', Georgia, serif;
  --radius:     4px;
}
```

---

## STEP 3 — Required CSS (always include these verbatim, adapt values)

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 17px;
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}

/* --- Animations --- */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(32px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.animate-fade-up   { animation: fadeUp 0.7s cubic-bezier(.22,1,.36,1) both; }
.animate-fade-up-2 { animation: fadeUp 0.7s cubic-bezier(.22,1,.36,1) 0.15s both; }
.animate-fade-up-3 { animation: fadeUp 0.7s cubic-bezier(.22,1,.36,1) 0.3s both; }
.animate-fade-in   { animation: fadeIn 1s ease both; }

/* Scroll-triggered reveal (JS adds this class) */
.reveal { opacity: 0; transform: translateY(40px); transition: opacity 0.7s ease, transform 0.7s cubic-bezier(.22,1,.36,1); }
.reveal.visible { opacity: 1; transform: none; }

/* --- Nav --- */
#nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 48px;
  transition: background 0.3s ease, box-shadow 0.3s ease;
}
#nav.scrolled {
  background: var(--bg);
  box-shadow: 0 1px 0 rgba(0,0,0,0.08);
}
.nav-logo {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  text-decoration: none;
  letter-spacing: -0.02em;
}
.nav-links { display: flex; gap: 36px; list-style: none; }
.nav-links a { color: var(--muted); text-decoration: none; font-size: 14px; font-weight: 500; transition: color 0.2s; }
.nav-links a:hover { color: var(--ink); }
.nav-cta {
  background: var(--accent);
  color: #fff;
  padding: 10px 24px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.2s, transform 0.2s;
}
.nav-cta:hover { opacity: 0.88; transform: translateY(-1px); }

/* --- Hero --- */
.hero {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: center;
  gap: 48px;
  padding: 140px 48px 80px;
  position: relative;
  overflow: hidden;
}
.hero-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 20px;
}
.hero-headline {
  font-family: var(--font-display);
  font-size: clamp(42px, 6vw, 88px);
  line-height: 1.05;
  letter-spacing: -0.025em;
  color: var(--ink);
  margin-bottom: 24px;
}
.hero-sub {
  font-size: 18px;
  color: var(--muted);
  max-width: 440px;
  line-height: 1.65;
  margin-bottom: 40px;
}
.btn-primary {
  display: inline-block;
  background: var(--accent);
  color: #fff;
  padding: 16px 36px;
  border-radius: var(--radius);
  font-weight: 600;
  font-size: 15px;
  text-decoration: none;
  letter-spacing: 0.01em;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.18); }
.btn-secondary {
  display: inline-block;
  border: 1.5px solid var(--ink);
  color: var(--ink);
  padding: 15px 32px;
  border-radius: var(--radius);
  font-weight: 500;
  font-size: 15px;
  text-decoration: none;
  margin-left: 16px;
  transition: background 0.2s, color 0.2s;
}
.btn-secondary:hover { background: var(--ink); color: var(--bg); }
.hero-image {
  border-radius: calc(var(--radius) * 2);
  width: 100%;
  aspect-ratio: 4/3;
  object-fit: cover;
  display: block;
}

/* --- Features --- */
.features {
  padding: 100px 48px;
  background: var(--surface);
}
.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 16px;
}
.section-title {
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 52px);
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin-bottom: 56px;
  max-width: 560px;
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.card {
  background: var(--bg);
  border-radius: var(--radius);
  padding: 36px 32px;
  border: 1px solid rgba(0,0,0,0.07);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.1); }
.card-icon { font-size: 32px; margin-bottom: 20px; display: block; }
.card-title { font-family: var(--font-display); font-size: 20px; font-weight: 600; margin-bottom: 12px; }
.card-text { font-size: 15px; color: var(--muted); line-height: 1.65; }

/* --- Testimonial --- */
.testimonial {
  padding: 100px 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
}
.testimonial::before {
  content: '\201C';
  font-family: var(--font-display);
  font-size: 160px;
  line-height: 0.8;
  color: var(--accent);
  opacity: 0.18;
  position: absolute;
  top: 60px;
  left: 48px;
}
.testimonial-text {
  font-family: var(--font-display);
  font-size: clamp(20px, 3vw, 36px);
  line-height: 1.4;
  max-width: 800px;
  font-style: italic;
  margin-bottom: 32px;
}
.testimonial-author { font-size: 14px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }

/* --- CTA Section --- */
.cta-section {
  background: var(--accent);
  padding: 100px 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.cta-section .section-title { color: #fff; margin-bottom: 20px; max-width: 700px; }
.cta-section .section-sub { color: rgba(255,255,255,0.8); font-size: 18px; max-width: 500px; margin-bottom: 40px; }
.btn-light {
  display: inline-block;
  background: #fff;
  color: var(--accent);
  padding: 16px 40px;
  border-radius: var(--radius);
  font-weight: 700;
  font-size: 15px;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.btn-light:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }

/* --- Footer --- */
footer {
  background: var(--accent-alt);
  color: rgba(255,255,255,0.7);
  padding: 48px;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 24px;
}
.footer-logo { font-family: var(--font-display); font-size: 20px; color: #fff; font-weight: 700; }
.footer-links { display: flex; gap: 28px; list-style: none; }
.footer-links a { color: rgba(255,255,255,0.6); text-decoration: none; font-size: 13px; transition: color 0.2s; }
.footer-links a:hover { color: #fff; }
```

---

## STEP 4 — Required JavaScript (always include verbatim)

```javascript
// Sticky nav on scroll
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 40);
});

// Scroll-triggered reveal for .reveal elements
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); } });
}, { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
```

---

## STEP 5 — HTML structure (follow this order, adapt content)

```html
<!DOCTYPE html>
<html lang="{taal van de campagne}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{Product naam}</title>
  <!-- Google Fonts from chosen preset -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=...&display=swap" rel="stylesheet">
  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    /* paste preset CSS variables here */
    /* paste required CSS from STEP 3 here */
    /* add any campaign-specific custom rules */
  </style>
</head>
<body>

  <!-- NAV -->
  <nav id="nav">
    <a href="#" class="nav-logo">{Brand naam}</a>
    <ul class="nav-links">
      <li><a href="#features">Voordelen</a></li>
      <li><a href="#testimonial">Reviews</a></li>
      <li><a href="#cta">Contact</a></li>
    </ul>
    <a href="#cta" class="nav-cta">{CTA tekst}</a>
  </nav>

  <!-- HERO — asymmetrisch grid -->
  <section class="hero">
    <div>
      <p class="hero-label animate-fade-in">{product categorie of tagline label}</p>
      <h1 class="hero-headline animate-fade-up">{headline uit copy_draft}</h1>
      <p class="hero-sub animate-fade-up-2">{subheadline uit copy_draft}</p>
      <div class="animate-fade-up-3">
        <a href="#cta" class="btn-primary">{primaire CTA}</a>
        <a href="#features" class="btn-secondary">Meer lezen</a>
      </div>
    </div>
    <div class="animate-fade-in">
      <img src="https://placehold.co/700x520/{accent-hex-zonder-#}/{bg-hex-zonder-#}?text={Product+naam}" 
           alt="{Product naam} visual" class="hero-image">
    </div>
  </section>

  <!-- FEATURES -->
  <section class="features" id="features">
    <div class="max-w-6xl mx-auto">
      <p class="section-label reveal">Wat je krijgt</p>
      <h2 class="section-title reveal">{korte sektietitel uit copy}</h2>
      <div class="features-grid">
        <div class="card reveal">{card 1 — emoji + titel + tekst uit copy_draft}</div>
        <div class="card reveal">{card 2}</div>
        <div class="card reveal">{card 3}</div>
      </div>
    </div>
  </section>

  <!-- TESTIMONIAL -->
  <section class="testimonial" id="testimonial">
    <blockquote class="testimonial-text reveal">
      "{quote uit social_content of copy_draft}"
    </blockquote>
    <cite class="testimonial-author reveal">— {naam of functie, of "Tevreden klant"}</cite>
  </section>

  <!-- CTA SECTION -->
  <section class="cta-section" id="cta">
    <h2 class="section-title reveal">{sterke afsluitende headline}</h2>
    <p class="section-sub reveal">{korte ondersteunende tekst}</p>
    <a href="#" class="btn-light reveal">{finale CTA knop tekst}</a>
  </section>

  <!-- FOOTER -->
  <footer>
    <div>
      <div class="footer-logo">{Brand naam}</div>
      <p style="font-size:13px; margin-top:8px;">© {jaar} {Brand naam}. Alle rechten voorbehouden.</p>
    </div>
    <ul class="footer-links">
      <li><a href="#">Home</a></li>
      <li><a href="#">Over</a></li>
      <li><a href="#">Contact</a></li>
    </ul>
  </footer>

  <script>
    /* paste required JS from STEP 4 here */
  </script>
</body>
</html>
```

---

## ABSOLUTE VERBODEN — wat nooit mag voorkomen

- `class="bg-gray-200"` of `bg-gray-100` als primaire achtergrond
- `<img src="...?text=Logo">` als nav-logo (gebruik tekst/HTML)
- `flex-col items-center` als enige layout — altijd minstens één asymmetrische sectie
- Inter, Roboto, Arial als display font
- Dezelfde oranje of grijze kleurpaletten die standaard Tailwind levert
- Lege, platte buttons zonder hover-effect
- Dezelfde aesthetic als een eerder gegenereerde site — elke output moet uniek aanvoelen
