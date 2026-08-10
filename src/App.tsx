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

const BASEMAP = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

function DeckGLOverlay(props: MapboxOverlayProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

interface StepView { longitude: number; latitude: number; zoom: number; pitch: number; bearing: number }

const STEP_VIEWS: StepView[] = [
  { longitude: -87.7043, latitude: 41.8452, zoom: 15.05, pitch: 50, bearing: -20 },
  { longitude: -87.7046, latitude: 41.846, zoom: 15.35, pitch: 48, bearing: -18 },
  { longitude: -87.7048, latitude: 41.8455, zoom: 15.3, pitch: 48, bearing: -18 },
  { longitude: -87.7055, latitude: 41.8452, zoom: 15.4, pitch: 48, bearing: -14 },
  { longitude: -87.7051, latitude: 41.8455, zoom: 15.35, pitch: 50, bearing: -18 },
  { longitude: -87.7051, latitude: 41.8452, zoom: 15.6, pitch: 56, bearing: -28 },
  { longitude: -87.7049, latitude: 41.8452, zoom: 15.45, pitch: 56, bearing: -24 },
  { longitude: -87.7055, latitude: 41.8456, zoom: 15.8, pitch: 35, bearing: -8 },
];

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
  const [pick, setPick] = useState<PickInfo>({
    title: 'Click a person or map element',
    desc: 'Actor identity, needs and intervention meaning appear here on demand.',
  });
  const [frame, setFrame] = useState(0);
  const mapRef = useRef<MapRef>(null);

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

  /* entering the feedback stage: everyone re-evaluates their route immediately */
  useEffect(() => {
    if (step >= 6) reevaluateRoutes(pedsRef.current, step, pipeline.treeShare, pipeline.benchShare);
  }, [step, pipeline]);

  /* camera follows the pipeline step */
  useEffect(() => {
    const v = STEP_VIEWS[step];
    mapRef.current?.flyTo({
      center: [v.longitude, v.latitude],
      zoom: v.zoom, pitch: v.pitch, bearing: v.bearing,
      duration: 1700, essential: true,
    });
  }, [step]);

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
    for (const id of ['building', 'building-top']) {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', 'none');
    }
    const firstSymbol = map.getStyle().layers?.find(l => l.type === 'symbol')?.id;
    map.addLayer({
      id: '3d-buildings', type: 'fill-extrusion',
      source: 'carto', 'source-layer': 'building', minzoom: 13,
      paint: {
        'fill-extrusion-color': '#28313c',
        'fill-extrusion-height': ['coalesce', ['get', 'render_height'], 12],
        'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
        'fill-extrusion-opacity': 0.88,
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

  return (
    <div className="app">
      <div className="world">
        <Map
          ref={mapRef}
          initialViewState={STEP_VIEWS[0]}
          mapStyle={BASEMAP}
          onLoad={onMapLoad}
          attributionControl={false}
        >
          <DeckGLOverlay layers={layers} />
        </Map>
      </div>

      <header className="header">
        <div className="brand">
          <span className="logo">POLIS</span>
          <span className="sub">sense · negotiate · govern — multi-agent planning on real geography</span>
        </div>
        <div className="right">
          <span className="badge">{SCENARIO.name}</span>
          <button className="exportBtn" onClick={exportRun}>⤓ Export run</button>
        </div>
      </header>

      <aside className="leftDock">
        <div className="card">
          <div className="k">Budget</div>
          <div className="metricBig">${budget.toFixed(1)}M</div>
          <input className="slider" type="range" min={8} max={40} step={1} value={budget}
            onChange={e => setBudget(+e.target.value)} />
          <div className="paramRow"><span>Used</span><span className="paramVal">{step >= 4 ? `$${pipeline.used}M` : '—'}</span></div>
        </div>
        <div className="card">
          <div className="k">Equity floor</div>
          <div className="metricBig">{floor.toFixed(2)}</div>
          <input className="slider" type="range" min={35} max={90} step={5} value={floor * 100}
            onChange={e => setFloor(+e.target.value / 100)} />
          <div className="hint">Minimum access level every protected group must reach. Raise it and watch the Orchestrator reallocate.</div>
        </div>
        <div className="card">
          <button className="primary" onClick={() => setAutoPlay(a => !a)}>
            {autoPlay ? '❚❚ Pause' : '▶ Run pipeline'}
          </button>
          <div className="row" style={{ marginTop: 8 }}>
            <button className="secondary" onClick={() => { setAutoPlay(false); setStepRaw(0); metricsRef.current.reset(); resetRoutes(pedsRef.current); }}>Reset</button>
            <button className="secondary" onClick={() => { setAutoPlay(false); setStep(step + 1); }}>Step</button>
          </div>
        </div>
        <div className="card">
          <div className="k">Sim speed</div>
          <div className="row">
            {[0.5, 1, 1.6, 2.5].map(s => (
              <button key={s} className={`secondary ${simSpeed === s ? 'on' : ''}`} onClick={() => setSimSpeed(s)}>{s}×</button>
            ))}
          </div>
        </div>
      </aside>

      <section className="topCenter">
        <div className="stageMeta">{copy.meta}</div>
        <div className="stageTitle">{copy.title}</div>
        <div className="stageText">{copy.text}</div>
        <div className="stepPills">
          {STEP_NAMES.map((n, i) => (
            <button key={n} className={`stepPill ${i === step ? 'active' : ''}`}
              onClick={() => { setAutoPlay(false); setStep(i); }}>{i}·{n}</button>
          ))}
        </div>
      </section>

      <aside className="rightDock">
        <div className="card">
          <div className="k">View</div>
          <div className="toggleBar">
            {(['mobility', 'conflict', 'equity'] as ViewMode[]).map(v => (
              <button key={v} className={`toggle ${viewMode === v ? 'active' : ''}`} onClick={() => setViewMode(v)}>
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
                  <div className="agentState">{state}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card">
          <div className="k">Decision trace</div>
          <div className="trace">
            {traceLines.length === 0 && <div className="traceEmpty">Step through the pipeline to see each agent's evidence → conclusion.</div>}
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
          <div className="liveNote">Red — protected groups · grey — general population. Heat exposure share of walking time.</div>
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
          <div className="bottomSub">{copy.state}</div>
        </div>
        <div className="timeline">
          <input type="range" min={0} max={7} step={1} value={step}
            onChange={e => { setAutoPlay(false); setStep(+e.target.value); }} />
          <div className="labels">
            {STEP_NAMES.map((n, i) => (
              <div key={n} className={`labelStep ${i === step ? 'active' : ''}`}>{n}</div>
            ))}
          </div>
        </div>
        <div className="controls">
          <button className="ctrl" onClick={() => { setAutoPlay(false); setStep(step - 1); }}>←</button>
          <button className="ctrl" onClick={() => setAutoPlay(a => !a)}>{autoPlay ? '❚❚' : '▶'}</button>
          <button className="ctrl" onClick={() => { setAutoPlay(false); setStep(step + 1); }}>→</button>
        </div>
      </footer>
    </div>
  );
}
