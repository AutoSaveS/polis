import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { MapboxOverlay, type MapboxOverlayProps } from '@deck.gl/mapbox';
import { Map, useControl, type MapRef } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

import { SCENARIO } from './scenario';
import { computePipeline } from './pipeline';
import { stepCopy, STEP_NAMES } from './copy';
import {
  createPeds, createCars, tickSim, resetRoutes, reevaluateRoutes, Metrics,
} from './sim';
import { buildLayers, makeHeatPoints, type PickInfo, type ViewMode } from './mapLayers';
import './App.css';

const BASEMAP = './carto-dark-style.json';

function DeckGLOverlay(props: MapboxOverlayProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

interface StepView { longitude: number; latitude: number; zoom: number; pitch: number; bearing: number }

/* The trail runs east–west: a small bearing keeps it diagonal across the
   widescreen frame instead of compressed into a vertical column, and closer
   zooms make the extruded buildings actually read as 3D. */
const STEP_VIEWS: StepView[] = [
  { longitude: -87.67050, latitude: 41.78769, zoom: 15.05, pitch: 52, bearing: -24 },
  { longitude: -87.67200, latitude: 41.78770, zoom: 15.25, pitch: 50, bearing: -24 },
  { longitude: -87.67190, latitude: 41.78771, zoom: 15.08, pitch: 47, bearing: -24 },
  { longitude: -87.67240, latitude: 41.78770, zoom: 15.50, pitch: 48, bearing: -26 },
  { longitude: -87.67100, latitude: 41.78770, zoom: 15.20, pitch: 50, bearing: -24 },
  { longitude: -87.67000, latitude: 41.78771, zoom: 15.60, pitch: 57, bearing: -30 },
  { longitude: -87.66950, latitude: 41.78772, zoom: 15.45, pitch: 56, bearing: -26 },
  { longitude: -87.67060, latitude: 41.78785, zoom: 15.55, pitch: 38, bearing: -18 },
];

const CONTEXT_VIEW: StepView = { longitude: -87.67050, latitude: 41.78769, zoom: 14.90, pitch: 50, bearing: -24 };
const CLOSING_VIEW: StepView = { longitude: -87.67050, latitude: 41.78769, zoom: 14.50, pitch: 45, bearing: -28 };

const RECORD_CUES = [0, 4, 10, 16, 22, 28, 34, 41, 48, 56];
const RECORD_LABELS = ['Title', 'World model', 'Demand', 'Conflict', 'Equity', 'Orchestration', 'Design', 'Feedback', 'Review', 'Closing'];

const AGENTS = [
  { key: 'demand', short: 'D', name: 'Demand', cls: 'demand' },
  { key: 'conflict', short: 'C', name: 'Conflict', cls: 'conflict' },
  { key: 'equity', short: 'E', name: 'Equity', cls: 'equity' },
  { key: 'orch', short: 'O', name: 'Orchestrator', cls: 'orch' },
];

export default function App() {
  const [step, setStepRaw] = useState(0);
  const [budget, setBudget] = useState(22);
  const [floor, setFloor] = useState(0.75);
  const [viewMode, setViewMode] = useState<ViewMode>('mobility');
  const [simSpeed, setSimSpeed] = useState(1);
  const [autoPlay, setAutoPlay] = useState(false);
  const [recordMode, setRecordMode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [recordElapsed, setRecordElapsed] = useState(0);
  const [pick, setPick] = useState<PickInfo>({
    title: 'Click any person or element',
    desc: '',
  });
  const [frame, setFrame] = useState(0);
  const mapRef = useRef<MapRef>(null);
  const recordCueRef = useRef(-1);

  const pedsRef = useRef(createPeds());
  const carsRef = useRef(createCars());
  const metricsRef = useRef(new Metrics());
  const simRef = useRef({ step: 0, treeShare: 0, benchShare: 0, heatFactor: 1, simSpeed: 1 });

  const params = useMemo(() => ({ budget, floor }), [budget, floor]);
  const pipeline = useMemo(() => computePipeline(params), [params]);
  const hf = step >= 6 ? pipeline.heatFactor : 1;
  const heatPoints = useMemo(() => makeHeatPoints(hf), [hf]);
  const copy = stepCopy(step, pipeline, params);

  useEffect(() => {
    simRef.current = {
      step,
      treeShare: pipeline.treeShare,
      benchShare: pipeline.benchShare,
      heatFactor: hf,
      simSpeed,
    };
  }, [step, pipeline, hf, simSpeed]);

  const setStep = useCallback((v: number) => {
    setStepRaw(prev => {
      const next = Math.max(0, Math.min(7, v));
      if (next < 6 && prev >= 6) resetRoutes(pedsRef.current);
      return next;
    });
  }, []);

  const flyTo = useCallback((v: StepView, duration = 1500) => {
    mapRef.current?.flyTo({
      center: [v.longitude, v.latitude], zoom: v.zoom,
      pitch: v.pitch, bearing: v.bearing, duration, essential: true,
    });
  }, []);

  const cancelRecord = useCallback(() => {
    setRecordMode(false);
    setCountdown(0);
    setRecordElapsed(0);
    recordCueRef.current = -1;
    setPick({ title: 'Click any person or element', desc: '' });
    // settle the camera on the current step instead of a half-finished cue flight
    flyTo(STEP_VIEWS[simRef.current.step], 900);
  }, [flyTo]);

  const startRecord = useCallback(() => {
    if (recordMode) return;
    setAutoPlay(false);
    setBudget(22);
    setFloor(0.75);
    setViewMode('mobility');
    setSimSpeed(1);
    setStepRaw(0);
    metricsRef.current.reset();
    resetRoutes(pedsRef.current);
    setPick({
      title: 'Frozen New ERA Trail case inputs',
      desc: 'Illustrative demonstrator values, not resident results.',
    });
    flyTo(STEP_VIEWS[0], 900);
    recordCueRef.current = -1;
    setRecordElapsed(0);
    setCountdown(3);
    setRecordMode(true);
  }, [flyTo, recordMode]);

  /* One-click, deterministic 60 s cue mode. Screen capture remains external. */
  useEffect(() => {
    if (!recordMode) return;
    if (countdown > 0) {
      const timer = window.setTimeout(() => setCountdown(v => Math.max(0, v - 1)), 1000);
      return () => window.clearTimeout(timer);
    }

    const startedAt = performance.now();
    const tick = () => {
      const elapsed = Math.min(60, (performance.now() - startedAt) / 1000);
      setRecordElapsed(elapsed);
      let cue = 0;
      for (let i = 0; i < RECORD_CUES.length; i++) if (elapsed >= RECORD_CUES[i]) cue = i;
      if (cue !== recordCueRef.current) {
        recordCueRef.current = cue;
        if (cue === 1) flyTo(CONTEXT_VIEW, 1600);
        if (cue >= 2 && cue <= 8) {
          const nextStep = cue - 1;
          setStep(nextStep);
          setViewMode(nextStep === 2 ? 'conflict' : nextStep === 3 ? 'equity' : 'mobility');
        }
        if (cue === 9) flyTo(CLOSING_VIEW, 1700);
      }
      if (elapsed >= 60) {
        window.clearInterval(timer);
        window.setTimeout(cancelRecord, 1000);
      }
    };
    tick();
    const timer = window.setInterval(tick, 100);
    return () => window.clearInterval(timer);
  }, [recordMode, countdown, cancelRecord, flyTo, setStep]);

  useEffect(() => {
    if (!recordMode) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') cancelRecord(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [recordMode, cancelRecord]);

  /* entering the feedback stage: everyone re-evaluates their route immediately */
  useEffect(() => {
    if (step >= 6) reevaluateRoutes(pedsRef.current, step, pipeline.treeShare, pipeline.benchShare);
  }, [step, pipeline]);

  /* camera follows the pipeline step */
  useEffect(() => {
    const v = STEP_VIEWS[step];
    flyTo(v, 1700);
  }, [step, flyTo]);

  /* single animation loop — movers always alive, metrics measured per frame */
  useEffect(() => {
    let raf = 0;
    let last = 0;
    const loop = (now: number) => {
      const dt = last ? Math.min(50, now - last) : 16;
      last = now;
      const s = simRef.current;
      tickSim(pedsRef.current, carsRef.current, dt, now, s);
      metricsRef.current.tick(dt * s.simSpeed, pedsRef.current, s.heatFactor);
      setFrame(f => f + 1);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  /* autoplay steps through the pipeline */
  useEffect(() => {
    if (!autoPlay) return;
    const t = setInterval(() => {
      setStepRaw(prev => {
        if (prev >= 7) { setAutoPlay(false); return prev; }
        return prev + 1;
      });
    }, 3000);
    return () => clearInterval(t);
  }, [autoPlay]);

  const onMapLoad = useCallback((e: { target: ReturnType<MapRef['getMap']> }) => {
    const map = e.target;
    (window as unknown as { __map: typeof map }).__map = map; // debug handle
    if (!map.getSource('carto')) return;

    for (const id of ['building', 'building-top']) {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', 'none');
    }
    if (map.getLayer('buildings-3d')) return;

    const firstSymbol = map.getStyle().layers?.find(layer => layer.type === 'symbol')?.id;
    map.addLayer({
      id: 'buildings-3d',
      type: 'fill-extrusion',
      source: 'carto',
      'source-layer': 'building',
      minzoom: 13,
      filter: ['!=', ['get', 'hide_3d'], true],
      paint: {
        'fill-extrusion-color': '#3a444e',
        'fill-extrusion-height': [
          'interpolate', ['linear'], ['zoom'],
          13, 0,
          14.5, ['coalesce', ['get', 'render_height'], 6],
        ],
        'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
        'fill-extrusion-opacity': 0.9,
      },
    }, firstSymbol);
  }, []);

  const layers = useMemo(() => buildLayers({
    step, viewMode, pipeline,
    peds: pedsRef.current, cars: carsRef.current,
    heatPoints, frame, onPick: setPick,
  }), [step, viewMode, pipeline, heatPoints, frame]);

  const exportRun = useCallback(() => {
    const m = metricsRef.current;
    const data = {
      tool: 'POLIS research prototype · deck.gl',
      exportedAt: new Date().toISOString(),
      scenario: SCENARIO.name,
      params: { budget, equityFloor: floor },
      pipeline: {
        conflicts: pipeline.conflicts, flags: pipeline.flags, decisions: pipeline.decisions,
        budgetUsed: pipeline.used, treesBuilt: pipeline.treeCount,
        benchesBuilt: pipeline.benchCount, heatFactor: pipeline.heatFactor,
      },
      liveMetrics: {
        simSeconds: +(m.simMs / 1000).toFixed(1),
        heatExposureProtected: +m.rate(m.expP).toFixed(4),
        heatExposureGeneral: +m.rate(m.expG).toFixed(4),
        greenRouteAdoption: +m.adoption(pedsRef.current).toFixed(4),
        history: m.history,
      },
      trace: pipeline.trace,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `polis_run_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }, [pipeline, budget, floor]);

  const m = metricsRef.current;
  const activeAgentIdx = step >= 1 && step <= 4 ? step - 1 : -1;
  const traceLines: Array<{ cls: string; html: string }> = [];
  const traceCls: Record<number, string> = { 1: 'demand', 2: 'conflict', 3: 'equity', 4: 'orch', 5: 'design' };
  for (let s = 1; s <= Math.min(step, 5); s++) {
    for (const line of pipeline.trace[s] ?? []) traceLines.push({ cls: traceCls[s], html: line });
  }

  const H = m.history;
  const sparkP = H.length > 1 ? H.map((h, i) => `${(i / (H.length - 1)) * 300},${34 - h.p * 30 - 2}`).join(' ') : '';
  const sparkG = H.length > 1 ? H.map((h, i) => `${(i / (H.length - 1)) * 300},${34 - h.g * 30 - 2}`).join(' ') : '';
  const recordShot = RECORD_CUES.reduce((active, cue, i) => recordElapsed >= cue ? i : active, 0);

  return (
    <div className={`app ${recordMode ? 'recording' : ''}`}>
      <div className="world">
        <Map
          ref={mapRef}
          initialViewState={STEP_VIEWS[0]}
          mapStyle={BASEMAP}
          onLoad={onMapLoad}
          onStyleData={(e) => { (window as unknown as { __map: unknown }).__map = e.target; }}
          onError={(e) => console.error('map error:', e.error?.message ?? e)}
          attributionControl={false}
        >
          <DeckGLOverlay layers={layers} />
        </Map>
      </div>

      <header className="header">
        <div className="brand">
          <span className="logo">POLIS</span>
          <span className="sub">multi-agent planning on real geography</span>
        </div>
        <div className="right">
          <span className="badge">{SCENARIO.name}</span>
          <button className="recordBtn" onClick={startRecord} disabled={recordMode} title="Run the 60-second recording cue sequence">
            {recordMode ? `REC ${Math.floor(recordElapsed / 60).toString().padStart(2, '0')}:${Math.floor(recordElapsed % 60).toString().padStart(2, '0')}` : 'Record'}
          </button>
          <button className="exportBtn" onClick={exportRun} disabled={recordMode}>Export</button>
        </div>
      </header>

      <aside className="leftDock">
        <div className="card">
          <div className="k">Budget</div>
          <div className="metricBig">${budget.toFixed(1)}M</div>
          <input className="slider" type="range" min={8} max={40} step={1} value={budget}
            disabled={recordMode} onChange={e => setBudget(+e.target.value)} />
          <div className="paramRow"><span>Used</span><span className="paramVal">{step >= 4 ? `$${pipeline.used}M` : '—'}</span></div>
        </div>
        <div className="card">
          <div className="k">Equity floor</div>
          <div className="metricBig">{floor.toFixed(2)}</div>
          <input className="slider" type="range" min={35} max={90} step={5} value={floor * 100}
            disabled={recordMode} onChange={e => setFloor(+e.target.value / 100)} />
        </div>
        <div className="card">
          <button className="primary" disabled={recordMode} onClick={() => setAutoPlay(a => !a)}>
            {autoPlay ? 'Pause' : 'Run pipeline'}
          </button>
          <div className="row" style={{ marginTop: 8 }}>
            <button className="secondary" disabled={recordMode} onClick={() => { setAutoPlay(false); setStepRaw(0); metricsRef.current.reset(); resetRoutes(pedsRef.current); }}>Reset</button>
            <button className="secondary" disabled={recordMode} onClick={() => { setAutoPlay(false); setStep(step + 1); }}>Step</button>
          </div>
        </div>
        <div className="card">
          <div className="k">Sim speed</div>
          <div className="row">
            {[0.5, 1, 1.6, 2.5].map(s => (
              <button key={s} className={`secondary ${simSpeed === s ? 'on' : ''}`} disabled={recordMode} onClick={() => setSimSpeed(s)}>{s}×</button>
            ))}
          </div>
        </div>
      </aside>

      <section className="topCenter">
        <div className="stageMeta">{copy.meta}</div>
        <div className="stageTitle">{copy.title}</div>
        <div className="stageText">{copy.text}</div>
      </section>
      {step === 2 && (
        <div className="conflictChip">{pipeline.conflicts.length} conflicts detected</div>
      )}

      <aside className="rightDock">
        <div className="card">
          <div className="k">View</div>
          <div className="toggleBar">
            {(['mobility', 'conflict', 'equity'] as ViewMode[]).map(v => (
              <button key={v} className={`toggle ${viewMode === v ? 'active' : ''}`} disabled={recordMode} onClick={() => setViewMode(v)}>
                {v[0].toUpperCase() + v.slice(1)}
              </button>
            ))}
          </div>
          <div className="legend"><span className="legendLbl">Heat</span><span className="legendBar heat" /></div>
          <div className="legend"><span className="legendLbl">Vulnerability</span><span className="legendBar vul" /></div>
        </div>

        <div className="card">
          <div className="k">Agent pipeline</div>
          <div className="agentBar">
            {AGENTS.map((a, i) => {
              const state = i === activeAgentIdx ? 'active' : (activeAgentIdx > i || step > 4) ? 'done' : 'idle';
              return (
                <div key={a.key} className={`agent ${a.cls} ${state}`}>
                  <div className="agentIcon">{a.short}</div>
                  <div className="agentName">{a.name}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card">
          <div className="k">Decision trace</div>
          <div className="trace">
            {traceLines.length === 0 && <div className="traceEmpty">Run the pipeline to see evidence → conclusion.</div>}
            {traceLines.map((t, i) => (
              <div key={i} className={`traceLine ${t.cls}`} dangerouslySetInnerHTML={{ __html: t.html }} />
            ))}
          </div>
        </div>

        <div className="card">
          <div className="k">Live metrics · measured from moving agents</div>
          <div className="liveGrid">
            <div className="stat"><div className="sK">Heat exposure · protected</div><div className="sV red">{m.expP.total ? `${(m.rate(m.expP) * 100).toFixed(1)}%` : '—'}</div></div>
            <div className="stat"><div className="sK">Heat exposure · general</div><div className="sV">{m.expG.total ? `${(m.rate(m.expG) * 100).toFixed(1)}%` : '—'}</div></div>
            <div className="stat"><div className="sK">Green route use</div><div className="sV mint">{step >= 6 ? `${(m.adoption(pedsRef.current) * 100).toFixed(0)}%` : '—'}</div></div>
            <div className="stat"><div className="sK">Sim time</div><div className="sV">{(m.simMs / 1000).toFixed(1)}s</div></div>
          </div>
          <svg className="spark" viewBox="0 0 300 34" preserveAspectRatio="none">
            {sparkG && <polyline points={sparkG} fill="none" stroke="#8E8E93" strokeWidth={1.4} opacity={0.7} />}
            {sparkP && <polyline points={sparkP} fill="none" stroke="#E15857" strokeWidth={1.8} />}
          </svg>
        </div>

        <div className="card">
          <div className="k">Stage state</div>
          <div className="scenePanel">
            {copy.stats.map(([k, v]) => (
              <div className="stat" key={String(k)}><div className="sK">{k}</div><div className="sV">{v}</div></div>
            ))}
          </div>
        </div>
      </aside>

      <div className="bottomLeft card">
        <div className="pickK">Inspector</div>
        <div className="pickT">{pick.title}</div>
        <div className="pickD">{pick.desc}</div>
      </div>

      <footer className="bottomBar">
        <div>
          <div className="bottomTitle">{step + 1} · {copy.title}</div>
        </div>
        <div className="timeline">
          <input type="range" min={0} max={7} step={1} value={step}
            disabled={recordMode} onChange={e => { setAutoPlay(false); setStep(+e.target.value); }} />
          <div className="labels">
            {STEP_NAMES.map((n, i) => (
              <div key={n} className={`labelStep ${i === step ? 'active' : ''}`}>{n}</div>
            ))}
          </div>
        </div>
        <div className="controls">
          <button className="ctrl" disabled={recordMode} onClick={() => { setAutoPlay(false); setStep(step - 1); }}>←</button>
          <button className="ctrl" disabled={recordMode} onClick={() => setAutoPlay(a => !a)}>{autoPlay ? '❚❚' : '▶'}</button>
          <button className="ctrl" disabled={recordMode} onClick={() => { setAutoPlay(false); setStep(step + 1); }}>→</button>
        </div>
      </footer>

      {recordMode && countdown > 0 && (
        <div className="recordCountdown" aria-live="polite">
          <div className="countNumber">{countdown}</div>
          <div className="countLabel">Recording cue mode</div>
          <div className="countHint">Start screen capture now · Esc cancels</div>
        </div>
      )}
      {recordMode && countdown === 0 && recordShot === 0 && (
        <div className="recordTitle">
          <div className="recordKicker">Interactive workflow demonstrator</div>
          <div className="recordName">POLIS</div>
          <div className="recordThesis">Provenance-aware AI decision support for equitable green infrastructure planning</div>
          <div className="recordChain">Needs → evidence → rules → geometry → review</div>
        </div>
      )}
      {recordMode && countdown === 0 && recordShot === 1 && (
        <div className="recordContext">
          <span>Suzhou pocket retrofit</span><span>London brownfield retrofit</span><span className="selected">Chicago · New ERA Trail selected</span>
        </div>
      )}
      {recordMode && countdown === 0 && recordShot === 6 && (
        <div className="recordDomains">Vegetation <b>·</b> Hardscape <b>·</b> Hydrology <b>·</b> Furniture <b>·</b> Activity <b>·</b> Ecology</div>
      )}
      {recordMode && countdown === 0 && recordShot === 7 && (
        <div className="recordDomains">Access <b>·</b> Solar <b>·</b> Thermal <b>·</b> Green <b>·</b> Ecology <b>·</b> Budget</div>
      )}
      {recordMode && countdown === 0 && recordShot === 9 && (
        <div className="recordClosing">
          <div className="recordName">POLIS</div>
          <div className="recordThesis">Keeping planning commitments inspectable</div>
          <div className="recordChain">Workflow demonstrator · not completed case-study results</div>
        </div>
      )}
      {recordMode && countdown === 0 && <div className="recordShotLabel">SHOT {recordShot + 1}/10 · {RECORD_LABELS[recordShot]}</div>}
    </div>
  );
}
