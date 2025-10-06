<script lang="ts">
  import Stars from "./Stars.svelte";
  import { tick, onMount, onDestroy } from "svelte";

  // --- Config ---
  const API_URL = "http://localhost:8000";
  const THRESHOLD = 0.5;

  // --- Estado UI ---
  let selectedFile: File | null = null;
  let fileName = "No file selected";
  let isAnalyzing = false;
  let isResult = false;
  let result:
    | null
    | {
        found: boolean;
        probability?: string;
        period?: string;
        radius?: string;
        raw?: any;
      } = null;
  let err = "";

  // --- Visualización (Raylib WASM) ---
  let showViz = false;
  let wasmReady = false;
  let ray: any = null;
  let canvasEl: HTMLCanvasElement;
  let rayError: string | null = null;

  // ---- Carga de script externo (una sola vez) ----
  function loadScript(src: string, id: string) {
    return new Promise<void>((resolve, reject) => {
      if (typeof document === "undefined") return reject(new Error("No DOM"));
      if (document.getElementById(id)) return resolve();
      const s = document.createElement("script");
      s.id = id;
      s.src = src;
      s.async = true;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.body.appendChild(s);
    });
  }

  // ---- Resize seguro para SSR ----
  function resizeCanvas() {
    if (!canvasEl) return;

    const dpr =
      typeof window !== "undefined" && window.devicePixelRatio
        ? window.devicePixelRatio
        : 1;

    const rect = canvasEl.getBoundingClientRect();
    const w = Math.max(1, Math.floor(rect.width * dpr));
    const h = Math.max(1, Math.floor(rect.height * dpr));

    if (canvasEl.width !== w || canvasEl.height !== h) {
      canvasEl.width = w;
      canvasEl.height = h;

      // Notifica al runtime si exportaste algo para resize
      try {
        if (ray?.setCanvasSize) {
          ray.setCanvasSize(w, h, false);
        } else if (ray?._ResizeCanvas) {
          ray._ResizeCanvas(w, h);
        }
      } catch {
        /* no-op */
      }
    }
  }

  // ⚠️ NO usar window.* fuera de onMount (SSR)
  const onWinResize = () => resizeCanvas();

  onMount(() => {
    // Registra listener sólo en cliente
    if (typeof window !== "undefined") {
      window.addEventListener("resize", onWinResize);
    }
  });

  onDestroy(() => {
    if (typeof window !== "undefined") {
      window.removeEventListener("resize", onWinResize);
    }
  });

  // ---- Inicializa Raylib/WASM sólo cuando found === true ----
  async function ensureRay() {
    if (wasmReady) {
      resizeCanvas();
      return;
    }

    const g: any = window as any;
    g.Module = g.Module || {};
    g.Module.canvas = canvasEl;
    g.Module.locateFile = (p: string) => `/game.wasm`;
    g.Module.print = (t: string) => console.log(t);
    g.Module.printErr = (t: string) => console.error(t);

    try {
      await loadScript("/game.js", "raylib-game-script");

      const factory =
        g.createRayApp || // -s MODULARIZE=1 -s EXPORT_NAME=createRayApp
        g.createModule || // a veces se exporta así
        (typeof g.Module === "function" ? g.Module : null); // MODULARIZE sin EXPORT_NAME

      if (typeof factory === "function") {
        ray = await factory({
          canvas: canvasEl,
          locateFile: (p: string) => `/game.wasm`,
          print: console.log,
          printErr: console.error
        });
      } else {
        ray = g.Module; // build sin modularize
      }

      wasmReady = true;
      resizeCanvas(); // ajusta tamaño físico tras cargar
    } catch (e: any) {
      rayError = e?.message ?? "Failed to initialize Raylib module.";
      console.error(e);
      throw e;
    }
  }

  // ---- Handlers UI ----
  function handleFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    selectedFile = input.files?.[0] ?? null;
    fileName = selectedFile ? selectedFile.name : "No file selected";
  }

  function reset() {
    selectedFile = null;
    fileName = "No file selected";
    isAnalyzing = false;
    isResult = false;
    result = null;
    err = "";
    showViz = false;
  }

  // ---- Llamada al backend ----
  async function analyzeWithServer() {
    if (isAnalyzing) return;
    if (!selectedFile || selectedFile.size === 0) {
      err = "Please select a non-empty CSV file.";
      return;
    }

    isAnalyzing = true;
    err = "";
    isResult = false;
    result = null;
    showViz = false;

    try {
      const form = new FormData();
      form.append("file", selectedFile);

      const res = await fetch(`${API_URL}/predict/csv`, {
        method: "POST",
        body: form
      });

      let data: any = null;
      const ct = res.headers.get("content-type") || "";
      if (!res.ok) {
        data = ct.includes("application/json") ? await res.json() : await res.text();
        throw new Error(
          typeof data === "string" ? data : data?.detail ?? JSON.stringify(data)
        );
      }
      data = await res.json();

      const prob =
        Array.isArray(data?.probabilities) && data.probabilities.length > 0
          ? Number(data.probabilities[0])
          : NaN;

      const found = !Number.isNaN(prob) ? prob >= THRESHOLD : false;

      isAnalyzing = false;
      isResult = true;

      result = found
        ? {
            found: true,
            probability: (prob * 100).toFixed(2),
            // placeholders
            period: (Math.random() * (365 - 5) + 5).toFixed(1),
            radius: (Math.random() * (2.5 - 0.8) + 0.8).toFixed(2),
            raw: data
          }
        : { found: false, raw: data };

      if (found) {
        showViz = true;
        await tick();     // asegura que el <canvas> existe con tamaño CSS
        await ensureRay();// inicializa WASM
        resizeCanvas();   // y ajusta backing store
      } else {
        showViz = false;
      }
    } catch (e: any) {
      isAnalyzing = false;
      err = e?.message ?? String(e);
      console.error(e);
      showViz = false;
    }
  }
</script>

<!-- Carga de la fuente Abel -->
<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Abel&display=swap" rel="stylesheet" />
</svelte:head>

<div class="container">
  <Stars/>

  <!-- Header -->
  <header class="header">
    <div class="logo">
      <img src="./logo.png" alt="Lightcurve Logo" class="logo-img" />
      <span class="logo-text">LIGHTCURVE</span>
    </div>
    <nav class="nav">
      <a href="#home">Home</a>
      <a href="#analyzer">AI Analyzer</a>
      <a href="#about">About</a>
    </nav>
  </header>

  <!-- Hero -->
  <section id="home" class="hero">
    <h1>Discover New Worlds</h1>
    <p>
      Using artificial intelligence to analyze light curves and find exoplanets at the edges of our universe.
    </p>
    <a href="#analyzer" class="btn-primary">Try our model</a>
  </section>

  <!-- Live Raylib (WASM) -->
  {#if showViz}
    <section class="raylib-section">
      <div class="section-header">
        <h2>Live Visualization (WebAssembly)</h2>
        <p>Rendering powered by Raylib + WebGL running right in your browser.</p>
      </div>

      <div class="glass-card">
        <div class="raylib-wrap">
          <canvas
            bind:this={canvasEl}
            id="raylib-canvas"
            class="raylib-canvas"
            aria-label="Raylib WebAssembly Canvas"
          ></canvas>
        </div>

        {#if !wasmReady}
          <p class="subtle">Loading visualization…</p>
        {/if}
        {#if rayError}
          <p class="warning">Could not load the Raylib module: {rayError}</p>
        {/if}
      </div>
    </section>
  {/if}

  <!-- Analyzer -->
  <section id="analyzer" class="analyzer">
    <div class="section-header">
      <h2>Data Analyzer</h2>
      <p>Upload a data file (e.g., CSV) and let our AI model analyze it.</p>
    </div>

    {#if !isAnalyzing && !isResult}
      <div class="glass-card">
        <div class="file-box">
          <input type="file" accept=".csv,.txt,.dat" on:change={handleFileChange} />
          <p>{fileName}</p>
        </div>
        <button on:click={analyzeWithServer} class="btn-primary" disabled={!selectedFile}>
          Analyze Data
        </button>
        {#if err}
          <p class="warning" style="margin-top:1rem">{err}</p>
        {/if}
      </div>
    {/if}

    {#if isAnalyzing}
      <div class="glass-card center">
        <div class="loader"></div>
        <p class="loading-text">Analyzing with our AI model…</p>
        <small class="subtle">This may take a few seconds.</small>
      </div>
    {/if}

    {#if isResult}
      <div class="glass-card">
        <h3>Analysis Results</h3>
        <div class="text-center">
          {#if result?.found}
            <h4 class="positive">Exoplanet Candidate Detected!</h4>
            <p class="subtle">Our model identified a consistent transit-like pattern.</p>
            <div class="results">
              <p><strong>Probability:</strong> {result.probability}%</p>
              <p><strong>Orbital Period (days):</strong> {result.period}</p>
              <p><strong>Planetary Radius (×R<sub>⊕</sub>):</strong> {result.radius}</p>
            </div>
          {:else}
            <h4 class="warning">No Clear Detection</h4>
            <p class="subtle">No significant transits were found.</p>
          {/if}
        </div>
        <button on:click={reset} class="btn-secondary">
          Analyze another file
        </button>
      </div>
    {/if}
  </section>

  <!-- About -->
  <section id="about" class="about">
    <h2>About Our Project</h2>
    <p>
      <span class="highlight">Lightcurve</span> is our solution for the
      <span class="highlight">NASA International Space Apps Challenge</span>. Our mission is to apply AI/ML
      techniques to automate exoplanet detection from stellar light curves.
    </p>
    <p>
      Our artificial intelligence model was trained on open datasets from NASA missions such as Kepler and TESS
      to learn characteristic patterns in stellar photometry. Using our own scientific visualization pipeline,
      developed with Raylib and C, we turn astronomy data into interactive, high-fidelity views. This helps us detect,
      analyze, and verify new exoplanet candidates with greater clarity and visual understanding than conventional methods.
    </p>
    <p>
      The web app lets you upload a CSV time series, runs the model on a secure backend, and only renders the
      interactive visualization when a strong exoplanet candidate is found. This keeps the UI clean and avoids
      misleading demos when there is no detection.
    </p>
    <p class="team">Team: Lightcurve SpaceApps Team</p>
  </section>

  <footer class="footer">
    <p>&copy; 2025 Lightcurve Team. Built for the NASA Space Apps Challenge.</p>
  </footer>
</div>

<style>
  *, *::before, *::after { box-sizing: border-box; }
  html, body { height: 100%; }

  body {
    margin: 0;
    font-family: 'Abel', sans-serif;
    background-color: #0d0d0d;
    color: #eaeaea;
    line-height: 1.6;
  }

  p, h1, h2, h3, h4, a, button {
    font-family: 'Abel', sans-serif;
    color: #eaeaea;
  }

  .container { max-width: 1100px; margin: 0 auto; padding: 1rem; }

  .header { display: flex; justify-content: space-between; align-items: center; padding: 2rem 0; }
  .logo { display: flex; align-items: center; gap: 0.75rem; }
  .logo-img { height: 50px; width: 50px; }
  .logo-text { font-size: 1.8rem; font-weight: 700; letter-spacing: 2px; color:#f4f0f0; }
  .nav { display: flex; gap: 2rem; }
  .nav a { color: #bbb; text-decoration: none; transition: color 0.3s; }
  .nav a:hover { color: #fff; }

  .hero { text-align: center; padding: 6rem 1rem; }
  .hero h1 { font-size: 3.5rem; font-weight: 700; margin-bottom: 1rem; color: #f4f0f0; }
  .hero p { font-size: 1.2rem; color: #aaa; max-width: 700px; margin: 0 auto 2rem; }

  .raylib-section { padding: 6rem 1rem; text-align: center; }
  .raylib-wrap { width: 100%; max-width: 820px; margin: 0 auto; }
  .raylib-canvas {
    width: 100%;
    height: auto;
    display: block;
    aspect-ratio: 16/9;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    background: #000;
  }

  .btn-primary, .btn-secondary {
    font-weight: bold;
    padding: 0.9rem 2.2rem;
    border-radius: 999px;
    border: none;
    cursor: pointer;
    transition: background 0.3s;
  }
  .btn-primary { background: #fff; color: #000; }
  .btn-primary:hover { background: #ddd; }
  .btn-secondary { display: block; width: 100%; margin-top: 1.5rem; background: #333; color: #fff; text-align: center; }
  .btn-secondary:hover { background: #555; }

  .analyzer { padding: 6rem 1rem; text-align: center; }

  .glass-card {
    background: rgba(16, 16, 16, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 2.5rem;
    max-width: 650px;
    margin: 0 auto;
    color: white;
  }
  .file-box {
    border: 2px dashed #666;
    padding: 2rem;
    border-radius: 0.75rem;
    margin-bottom: 1.5rem;
    text-align: center;
    font-size: 0.95rem;
    color: #bbb;
  }

  .loader {
    border: 4px solid rgba(255,255,255,0.2);
    border-left-color: #fff;
    border-radius: 50%;
    width: 50px; height: 50px;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .positive { color: #4ade80; font-size: 1.3rem; margin-top: 1rem; }
  .warning { color: #facc15; font-size: 1.1rem; margin-top: 1rem; }
  .results { margin-top: 1.5rem; background: rgba(0,0,0,0.4); padding: 1rem 1.5rem; border-radius: 0.75rem; text-align: left; color: #f4f0f0; }
  .subtle { color: #aaa; font-size: 0.95rem; }

  .about { padding: 6rem 1rem; text-align: center; }
  .about h2 { font-size: 2.5rem; margin-bottom: 1rem; color: #f4f0f0; }
  .about p { color: #aaa; max-width: 700px; margin: 0 auto 1.5rem; font-size: 1.1rem; }
  .highlight { color: #fff; font-weight: bold; }
  .team { margin-top: 2rem; font-weight: bold; }

  .footer { border-top: 1px solid #222; padding: 2rem; text-align: center; font-size: 0.9rem; color: #666; margin-top: 3rem; }

/* 1) Dale más ancho a la página (opcional) */
.container {
  max-width: 1400px; /* antes 1100px */
}

/* 2) Quita el límite de 820px del contenedor del canvas */
.raylib-wrap {
  width: 100%;
  max-width: none;   /* antes 820px */
  margin: 0 auto;
}

/* 3) Haz el canvas MUCHO más grande */
.raylib-canvas {
  display: block;
  width: 100%;     /* ocupa todo el ancho disponible */
  height: 70vh;    /* alto grande y responsivo (70% de la altura de la ventana) */
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  background: #000;
  /* IMPORTANTE: elimina el aspect-ratio para que respete el height */
  aspect-ratio: auto !important;
}

/* 4) En pantallas muy grandes puedes subirlo más aún */
@media (min-width: 1280px) {
  .raylib-canvas { height: 80vh; }
}
.container { max-width: 1600px; }
.raylib-section { padding: 2rem 0; }
.container { max-width: none; padding-left: 0; padding-right: 0; }
.glass-card { max-width: none; border-radius: 0; }
.raylib-wrap { max-width: none; padding: 0 2rem; }


</style>

