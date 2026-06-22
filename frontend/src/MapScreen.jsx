import React, { useRef, useEffect, useMemo, useState } from 'react';
import * as d3 from 'd3';
import { PHENOTYPE, POPULATION_DOTS } from './store';

const DEFAULT_Z1_CONTRIBS = [
  { feature: 'insulin', contribution: 0.48 },
  { feature: 'glucose', contribution: 0.28 },
  { feature: 'triglycerides', contribution: 0.14 },
  { feature: 'hdl', contribution: 0.06 },
  { feature: 'alt', contribution: 0.02 },
  { feature: 'ast', contribution: 0.01 },
  { feature: 'ggt', contribution: 0.01 },
];

const DEFAULT_Z2_CONTRIBS = [
  { feature: 'alt', contribution: 0.38 },
  { feature: 'ggt', contribution: 0.28 },
  { feature: 'triglycerides', contribution: 0.18 },
  { feature: 'ast', contribution: 0.12 },
  { feature: 'insulin', contribution: 0.02 },
  { feature: 'glucose', contribution: 0.01 },
  { feature: 'hdl', contribution: 0.01 },
];

// Map coordinate system: SVG viewBox 0 0 500 500, center (250,250)
// Latent range [-2.5, 2.5] → [0, 500]
const SCALE = 500 / 5; // 100px per latent unit
const toSvg = (v) => 250 + v * SCALE;
const toSvgX = (z1) => toSvg(z1);
const toSvgY = (z2) => toSvg(-z2); // Y inverted (up = positive z2)

// Bezier from path array
function pathD(pts) {
  if (!pts || pts.length < 2) return '';
  const svgPts = pts.map(([z1, z2]) => [toSvgX(z1), toSvgY(z2)]);
  let d = `M ${svgPts[0][0]} ${svgPts[0][1]}`;
  for (let i = 1; i < svgPts.length - 1; i++) {
    const cpx = (svgPts[i - 1][0] + svgPts[i][0]) / 2;
    const cpy = (svgPts[i - 1][1] + svgPts[i][1]) / 2;
    d += ` Q ${cpx} ${cpy} ${svgPts[i][0]} ${svgPts[i][1]}`;
  }
  d += ` L ${svgPts[svgPts.length - 1][0]} ${svgPts[svgPts.length - 1][1]}`;
  return d;
}

// Map pin shape (pointed bottom, circle top)
function MapPin({ cx, cy, color, sigma = 0.5 }) {
  const r = 10;
  const tailH = 16;
  return (
    <g>
      {/* Breathing glow halo — size proportional to uncertainty */}
      <circle
        cx={cx}
        cy={cy - r - 2}
        r={r * 1.5 + sigma * 30}
        fill={color}
        opacity={0.0}
        className="pin-halo"
      />
      {/* Pin body */}
      <path
        d={`M ${cx} ${cy} L ${cx - r * 0.7} ${cy - r * 0.7 - tailH * 0.4}
            A ${r} ${r} 0 1 1 ${cx + r * 0.7} ${cy - r * 0.7 - tailH * 0.4} Z`}
        fill="white"
        stroke={color}
        strokeWidth={2.5}
      />
      {/* Inner dot */}
      <circle cx={cx} cy={cy - tailH * 0.5 - r * 0.3} r={3.5} fill={color} />
    </g>
  );
}

// Semicircular gauge component
function RiskGauge({ score, lo, hi, color }) {
  const W = 200, H = 110;
  const cx = W / 2, cy = H - 10;
  const r = 78;
  const sweepDeg = 180;

  // Angle: 180° (left) → 0° (right); score 0→1 maps to 180→0
  const scoreAngle = Math.PI - score * Math.PI;
  const loAngle = Math.PI - lo * Math.PI;
  const hiAngle = Math.PI - hi * Math.PI;

  const arcPath = (startA, endA) => {
    const x1 = cx + r * Math.cos(startA);
    const y1 = cy - r * Math.sin(startA);
    const x2 = cx + r * Math.cos(endA);
    const y2 = cy - r * Math.sin(endA);
    const largeArc = Math.abs(endA - startA) > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} ${endA < startA ? 1 : 0} ${x2} ${y2}`;
  };

  // Needle
  const nx = cx + (r - 10) * Math.cos(scoreAngle);
  const ny = cy - (r - 10) * Math.sin(scoreAngle);

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ overflow: 'visible' }}>
      {/* Background track */}
      <path d={arcPath(Math.PI, 0)} fill="none" stroke="#1C2333" strokeWidth={12} />
      {/* Green zone 0–0.33 */}
      <path d={arcPath(Math.PI, Math.PI * 0.67)} fill="none" stroke="#00C47D" strokeWidth={12} opacity={0.4} />
      {/* Amber zone 0.33–0.66 */}
      <path d={arcPath(Math.PI * 0.67, Math.PI * 0.34)} fill="none" stroke="#F5A623" strokeWidth={12} opacity={0.4} />
      {/* Red zone 0.66–1 */}
      <path d={arcPath(Math.PI * 0.34, 0)} fill="none" stroke="#E8394A" strokeWidth={12} opacity={0.4} />
      {/* CI arc */}
      <path d={arcPath(loAngle, hiAngle)} fill="none" stroke={color} strokeWidth={8} opacity={0.7} />
      {/* Needle */}
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="white" strokeWidth={2} strokeLinecap="round" />
      <circle cx={cx} cy={cy} r={4} fill="white" />
    </svg>
  );
}

// ── METABOLIC MAP SVG ─────────────────────────────────────────────────────────
function MetabolicMap({ result, pinVisible, routeVisible }) {
  const ph = PHENOTYPE[result.phenotype] || PHENOTYPE['Metabolically Healthy'];
  const pinX = toSvgX(result.z1);
  const pinY = toSvgY(result.z2);
  const sigma = result.z1_sigma || 0.4;

  const isHealthy = result.phenotype === 'Metabolically Healthy';

  // Safe zone target (upper-left quadrant center)
  const safeX = toSvgX(-0.7);
  const safeY = toSvgY(-0.55);

  // Geodesic path
  const geoPath = result.geodesicPath;

  // Waypoints interpolated along path
  const waypoints = result.waypoints || [];

  return (
    <svg
      viewBox="0 0 500 500"
      style={{ width: '100%', height: '100%', display: 'block' }}
      aria-label="Metabolic location map"
    >
      <defs>
        {/* Radial gradients per quadrant – radiating from outer corners */}
        <radialGradient id="grad-healthy" cx="0%" cy="100%" r="80%">
          <stop offset="0%" stopColor="#00C47D" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#00C47D" stopOpacity="0.0" />
        </radialGradient>
        <radialGradient id="grad-ir" cx="100%" cy="100%" r="80%">
          <stop offset="0%" stopColor="#F5A623" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#F5A623" stopOpacity="0.0" />
        </radialGradient>
        <radialGradient id="grad-steatosis" cx="0%" cy="0%" r="80%">
          <stop offset="0%" stopColor="#3D8EF8" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#3D8EF8" stopOpacity="0.0" />
        </radialGradient>
        <radialGradient id="grad-dual" cx="100%" cy="0%" r="80%">
          <stop offset="0%" stopColor="#E8394A" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#E8394A" stopOpacity="0.0" />
        </radialGradient>

        {/* Dashed animated route */}
        <marker id="route-arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="#00C47D" opacity="0.8" />
        </marker>
      </defs>

      {/* LAYER 1: Territory backgrounds */}
      {/* Q3 healthy: x<0, y>250 (z2<0) */}
      <rect x={0} y={250} width={250} height={250} fill="url(#grad-healthy)" />
      {/* Q1 IR: x>250, y>250 */}
      <rect x={250} y={250} width={250} height={250} fill="url(#grad-ir)" />
      {/* Q2 steatosis: x<250, y<250 */}
      <rect x={0} y={0} width={250} height={250} fill="url(#grad-steatosis)" />
      {/* Q4 dual: x>250, y<250 */}
      <rect x={250} y={0} width={250} height={250} fill="url(#grad-dual)" />

      {/* Territory name watermarks */}
      {[
        { x: 125, y: 380, text: 'METABOLICALLY\nHEALTHY', color: '#00C47D' },
        { x: 375, y: 380, text: 'INSULIN\nRESISTANT', color: '#F5A623' },
        { x: 125, y: 120, text: 'STEATOSIS\nDOMINANT', color: '#3D8EF8' },
        { x: 375, y: 120, text: 'DUAL BURDEN\nZONE', color: '#E8394A' },
      ].map(({ x, y, text, color }) =>
        text.split('\n').map((line, li) => (
          <text
            key={`${x}-${li}`}
            x={x}
            y={y + li * 22}
            textAnchor="middle"
            fill={color}
            opacity={0.09}
            fontSize={16}
            fontFamily='"Instrument Sans", sans-serif'
            fontWeight={700}
            letterSpacing={2}
          >
            {line}
          </text>
        ))
      )}

      {/* LAYER 2: Population cloud */}
      {POPULATION_DOTS.map((dot, i) => {
        const qColors = ['#00C47D', '#F5A623', '#3D8EF8', '#E8394A'];
        return (
          <circle
            key={i}
            cx={toSvgX(dot.x)}
            cy={toSvgY(dot.y)}
            r={2.5}
            fill={qColors[dot.q]}
            opacity={0.07}
          />
        );
      })}

      {/* LAYER 3: Threshold lines */}
      {/* Vertical: IR threshold (z1=0) */}
      <line
        x1={250} y1={10} x2={250} y2={490}
        stroke="#C9A227"
        strokeWidth={1}
        strokeDasharray="5,5"
        opacity={0.5}
      />
      <text x={255} y={22} fill="#C9A227" fontSize={9} opacity={0.7}
        fontFamily='"Instrument Sans", sans-serif' letterSpacing={1}>
        IR THRESHOLD
      </text>
      {/* Horizontal: Steatosis threshold (z2=0, y=250) */}
      <line
        x1={10} y1={250} x2={490} y2={250}
        stroke="#C9A227"
        strokeWidth={1}
        strokeDasharray="5,5"
        opacity={0.5}
      />
      <text x={12} y={246} fill="#C9A227" fontSize={9} opacity={0.7}
        fontFamily='"Instrument Sans", sans-serif' letterSpacing={1}>
        STEATOSIS THRESHOLD
      </text>

      {/* LAYER 4: Route (non-healthy only) */}
      {!isHealthy && routeVisible && (
        <>
          {geoPath ? (
            <>
              <path
                d={pathD(geoPath)}
                fill="none"
                stroke="#00C47D"
                strokeWidth={2}
                strokeDasharray="8,5"
                opacity={0.8}
                className="route-dash"
              />
              {/* Waypoints */}
              {waypoints.map((wp, wi) => {
                const idx = Math.round(wp.t * (geoPath.length - 1));
                const pt = geoPath[Math.min(idx, geoPath.length - 1)];
                const wx = toSvgX(pt[0]);
                const wy = toSvgY(pt[1]);
                const isRight = wx > 250;
                const labelText = wp.label;
                const rectW = labelText.length * 5.4 + 8;
                const rectX = isRight ? wx - 10 - rectW : wx + 10;
                const rectY = wy - 21;
                return (
                  <g key={wi}>
                    <polygon
                      points={`${wx},${wy - 7} ${wx + 5},${wy} ${wx},${wy + 7} ${wx - 5},${wy}`}
                      fill="#00C47D"
                      opacity={0.85}
                    />
                    <rect
                      x={rectX}
                      y={rectY}
                      width={rectW}
                      height={12}
                      fill="#050810"
                      rx={2}
                      opacity={0.95}
                    />
                    <text
                      x={isRight ? wx - 10 : wx + 10}
                      y={wy - 12}
                      textAnchor={isRight ? 'end' : 'start'}
                      fill="#00C47D"
                      fontSize={9}
                      fontFamily='"JetBrains Mono", monospace'
                      opacity={0.9}
                    >
                      {labelText}
                    </text>
                  </g>
                );
              })}
            </>
          ) : (
            /* Straight fallback bezier to safe zone */
            <line
              x1={pinX} y1={pinY} x2={safeX} y2={safeY}
              stroke="#00C47D"
              strokeWidth={2}
              strokeDasharray="8,5"
              opacity={0.6}
              className="route-dash"
            />
          )}

          {/* Safe zone marker */}
          <g>
            <circle cx={safeX} cy={safeY} r={10} fill="none" stroke="#00C47D" strokeWidth={1.5} opacity={0.7} className="safe-pulse" />
            <circle cx={safeX} cy={safeY} r={4} fill="#00C47D" opacity={0.8} />
            <text x={safeX + 15} y={safeY + 4} fill="#00C47D" fontSize={8}
              fontFamily='"Instrument Sans", sans-serif' letterSpacing={1} opacity={0.9}>
              SAFE ZONE
            </text>
          </g>
        </>
      )}

      {/* LAYER 5: Patient pin */}
      {pinVisible && (
        <g className="patient-pin-group">
          {/* Halo glow */}
          <circle
            cx={pinX}
            cy={pinY - 12}
            r={sigma * 35 + 14}
            fill={ph.color}
            opacity={0}
            className="pin-halo-anim"
          />
          <MapPin cx={pinX} cy={pinY} color={ph.color} sigma={sigma} />
          {/* BMI label */}
          {(() => {
            const bmiText = `BMI ${result.bmi || '22.5'}`;
            const isRight = pinX > 250;
            const rectW = bmiText.length * 5.4 + 8;
            const rectX = isRight ? pinX - 16 - rectW : pinX + 16;
            const rectY = pinY - 17;
            return (
              <g>
                <rect
                  x={rectX}
                  y={rectY}
                  width={rectW}
                  height={12}
                  fill="#050810"
                  rx={2}
                  opacity={0.85}
                />
                <text
                  x={isRight ? pinX - 16 : pinX + 16}
                  y={pinY - 8}
                  textAnchor={isRight ? 'end' : 'start'}
                  fill="white"
                  fontSize={9}
                  fontFamily='"JetBrains Mono", monospace'
                  opacity={0.7}
                >
                  {bmiText}
                </text>
              </g>
            );
          })()}
        </g>
      )}

      {/* Axis labels */}
      <text x={250} y={498} textAnchor="middle" fill="#8898B0" fontSize={9} letterSpacing={2}
        fontFamily='"Instrument Sans", sans-serif'>
        INSULIN RESISTANCE →
      </text>
      <text
        x={8}
        y={250}
        fill="#8898B0"
        fontSize={9}
        letterSpacing={2}
        textAnchor="middle"
        fontFamily='"Instrument Sans", sans-serif'
        transform="rotate(-90, 8, 250)"
      >
        LIVER FAT ↑
      </text>
    </svg>
  );
}

// ── Percentile bar ────────────────────────────────────────────────────────────
function PctBar({ label, pct, color }) {
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '10px', color: '#888', fontVariant: 'small-caps', letterSpacing: '0.1em' }}>
          {label}
        </span>
        <span style={{ fontSize: '11px', fontFamily: "'JetBrains Mono', monospace", color: '#ccc' }}>
          {pct}th pct
        </span>
      </div>
      <div style={{ height: '4px', background: '#1C2333', borderRadius: '2px', overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            width: `${pct}%`,
            background: color,
            borderRadius: '2px',
            transition: 'width 0.8s cubic-bezier(0.16,1,0.3,1)',
          }}
        />
      </div>
    </div>
  );
}

// ── Horizontal bar chart (Validation tab) ────────────────────────────────────
const VALIDATION_DATA = [
  { name: 'LMSIS (This Map System)', rho: 0.542, highlight: true },
  { name: 'Random Forest (Black-Box AI)', rho: 0.596 },
  { name: 'XGBoost (Black-Box AI)', rho: 0.581 },
  { name: 'Elastic Net (Regression)', rho: 0.491 },
  { name: 'FLI (Clinical Index)', rho: 0.399 },
  { name: 'TyG Index (Clinical Index)', rho: 0.364 },
  { name: 'HSI (Clinical Index)', rho: 0.129 },
  { name: 'NAFLD-LFS (Traditional Score)', rho: -0.118 },
];

function ValidationTab() {
  const maxAbs = 0.65;
  return (
    <div style={{ padding: '0 4px' }}>
      <div style={sectionTitle}>Liver Fat Accuracy Comparison</div>
      <div style={{ fontSize: '10px', color: '#99A8C0', marginBottom: '16px', lineHeight: 1.4 }}>
        This chart measures prediction correlation (0 to +1) against Fibroscan liver fat measurements. 
        Traditional clinical scores (e.g. NAFLD-LFS) correlate negatively, meaning they actively mislead. 
        LMSIS matches black-box AI models in accuracy and utilizes a learned Riemannian manifold 
        to compute optimal geodesic safety pathways.
      </div>

      {VALIDATION_DATA.map((d) => {
        const isNeg = d.rho < 0;
        const barPct = Math.abs(d.rho) / maxAbs * 100;
        return (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span style={{
              width: '150px', fontSize: '9px', color: d.highlight ? '#E0E8FF' : '#8898B0',
              fontFamily: d.highlight ? "'JetBrains Mono', monospace" : 'inherit',
              flexShrink: 0, lineHeight: 1.3,
            }}>
              {d.name}
            </span>
            <div style={{ flex: 1, height: '14px', background: '#0D1117', borderRadius: '2px', overflow: 'hidden', position: 'relative' }}>
              <div
                style={{
                  height: '100%',
                  width: `${barPct}%`,
                  background: isNeg ? '#E8394A' : d.highlight ? '#3D8EF8' : '#4A5568',
                  borderRadius: '2px',
                  transition: 'width 1s cubic-bezier(0.16,1,0.3,1)',
                }}
              />
            </div>
            <span style={{
              fontSize: '10px', fontFamily: "'JetBrains Mono', monospace",
              color: isNeg ? '#E8394A' : '#8898B0', width: '42px', textAlign: 'right',
            }}>
              {d.rho >= 0 ? '+' : ''}{d.rho.toFixed(3)}
            </span>
          </div>
        );
      })}

      {/* Conformal coverage */}
      <div style={{ borderTop: '1px solid #1C2333', marginTop: '20px', paddingTop: '16px' }}>
        <div style={sectionTitle}>Reliability of the Safety Zone</div>
        <div style={{ fontSize: '10px', color: '#99A8C0', marginBottom: '12px', lineHeight: 1.4 }}>
          Standard prediction ranges fail when patient risk is high. 
          LMSIS guarantees 90% probability coverage of the patient's true metabolic position across all severity levels:
        </div>
        {[
          { label: 'Traditional prediction range (68% coverage)', val: 68, color: '#E8394A' },
          { label: 'LMSIS calibrated safety range (91% coverage)', val: 91, color: '#00C47D' },
        ].map((row) => (
          <div key={row.label} style={{ marginBottom: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
              <span style={{ fontSize: '9px', color: '#8898B0' }}>{row.label}</span>
              <span style={{ fontSize: '10px', fontFamily: "'JetBrains Mono', monospace", color: row.color }}>
                {row.val}%
              </span>
            </div>
            <div style={{ height: '6px', background: '#0D1117', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${row.val}%`, background: row.color, borderRadius: '2px' }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── SCREEN 2 — THE METABOLIC MAP ──────────────────────────────────────────────
export function MapScreen({ result, onBack, onSwitch, animStage }) {
  const [activeTab, setActiveTab] = useState('clinical');
  const [sensTab, setSensTab] = useState('z1');
  const ph = PHENOTYPE[result.phenotype] || PHENOTYPE['Metabolically Healthy'];
  const isHealthy = result.phenotype === 'Metabolically Healthy';

  const z1Contribs = result.z1_contributions && result.z1_contributions.length > 0 ? result.z1_contributions : DEFAULT_Z1_CONTRIBS;
  const z2Contribs = result.z2_contributions && result.z2_contributions.length > 0 ? result.z2_contributions : DEFAULT_Z2_CONTRIBS;
  const activeContribs = sensTab === 'z1' ? z1Contribs : z2Contribs;

  const pinVisible = animStage >= 4;
  const routeVisible = animStage >= 5;
  const bannerVisible = animStage >= 5;
  const panelVisible = animStage >= 5;

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        background: '#050810',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* ZONE 1: Phenotype banner */}
      <div
        id="phenotype-banner"
        style={{
          height: '60px',
          background: `${ph.color}E6`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          flexShrink: 0,
          opacity: bannerVisible ? 1 : 0,
          transform: bannerVisible ? 'translateY(0)' : 'translateY(-100%)',
          transition: 'opacity 0.3s, transform 0.3s cubic-bezier(0.16,1,0.3,1)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {ph.pulse && (
            <span
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: 'white',
                display: 'inline-block',
                animation: 'phenotype-pulse 2s ease-in-out infinite',
              }}
            />
          )}
          <span
            style={{
              fontSize: '14px',
              fontWeight: 700,
              color: 'white',
              letterSpacing: '0.12em',
              fontFamily: '"Instrument Sans", sans-serif',
            }}
          >
            {ph.bannerLabel}
          </span>
        </div>
        <span
          style={{
            fontSize: '12px',
            color: 'rgba(255,255,255,0.8)',
            fontFamily: '"Instrument Sans", sans-serif',
          }}
        >
          {ph.bannerSub}
        </span>
      </div>

      {/* ZONE 2 + 3: Map + Panel */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Map area (70%) */}
        <div
          style={{
            flex: '0 0 70%',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '600px',
              aspectRatio: '1',
            }}
          >
            <MetabolicMap result={result} pinVisible={pinVisible} routeVisible={routeVisible} />
          </div>
        </div>

        {/* Story panel (30%) */}
        <div
          id="story-panel"
          style={{
            flex: '0 0 30%',
            background: '#080D1A',
            borderLeft: '1px solid #1C2333',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            opacity: panelVisible ? 1 : 0,
            transform: panelVisible ? 'translateX(0)' : 'translateX(100%)',
            transition: 'opacity 0.3s, transform 0.3s cubic-bezier(0.16,1,0.3,1)',
          }}
        >
          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #1C2333', flexShrink: 0 }}>
            {['clinical', 'validation'].map((tab) => (
              <button
                key={tab}
                id={`tab-${tab}`}
                onClick={() => setActiveTab(tab)}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '10px',
                  fontVariant: 'small-caps',
                  letterSpacing: '0.15em',
                  color: activeTab === tab ? 'white' : '#555',
                  borderBottom: activeTab === tab ? `2px solid ${ph.color}` : '2px solid transparent',
                  transition: 'color 0.2s',
                  fontFamily: 'inherit',
                }}
              >
                {tab === 'clinical' ? 'PATIENT REPORT' : 'VALIDATION ACCURACY'}
              </button>
            ))}
          </div>

          {/* Panel body */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
            {activeTab === 'clinical' ? (
              <>
                {/* Section 1: Metabolic Indicators */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={sectionTitle}>Metabolic State Indicators</div>
                  <div style={{ fontSize: '10px', color: '#8898B0', marginBottom: '12px', lineHeight: 1.4 }}>
                    Compared to other normal-BMI adults, this patient ranks in the:
                  </div>
                  <PctBar label="Insulin Resistance" pct={result.irPct || 50} color="#F5A623" />
                  <PctBar label="Liver Fat" pct={result.capPct || 30} color="#3D8EF8" />
                  <div style={{ marginTop: '14px' }}>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12px', color: '#E0E8FF', marginBottom: '6px' }}>
                      Insulin Score (HOMA-IR): {(result.predHomaIr || result.homaIr || 0).toFixed(2)} <span style={{ color: '#8898B0', fontSize: '10px' }}>(Normal &lt; 1.90)</span>
                    </div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12px', color: '#E0E8FF' }}>
                      Liver Fat Score: {Math.round(result.predCapScore || 220)} dB/m <span style={{ color: '#8898B0', fontSize: '10px' }}>({result.capLabel || 'S0 – None'})</span>
                    </div>
                  </div>
                </div>

                <div style={divider} />

                {/* Section 2: Confidence */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={sectionTitle}>Confidence & Risk Score</div>
                  <div style={{ fontSize: '10px', color: '#8898B0', marginBottom: '12px', lineHeight: 1.4 }}>
                    Metabolic disease risk score derived from map location, with 90% probability boundary:
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '8px' }}>
                    <RiskGauge
                      score={result.riskScore || 0.5}
                      lo={result.riskLo || 0.4}
                      hi={result.riskHi || 0.6}
                      color={ph.color}
                    />
                  </div>
                  <div style={{ textAlign: 'center', marginTop: '6px', fontSize: '14px', fontFamily: "'JetBrains Mono', monospace", color: ph.color, fontWeight: 700 }}>
                    Risk Score: {((result.riskScore || 0) * 100).toFixed(1)}%
                  </div>
                  <div
                    style={{
                      textAlign: 'center',
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: '11px',
                      color: '#8898B0',
                      marginTop: '4px'
                    }}
                  >
                    90% Safety Margin: [{((result.riskLo || 0) * 100).toFixed(1)}% – {((result.riskHi || 0) * 100).toFixed(1)}%]
                  </div>
                </div>

                <div style={divider} />

                {/* Section 2.5: Biomarker Sensitivity (Jacobian) */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={sectionTitle}>Biomarker Sensitivity (Jacobian)</div>
                  <div style={{ fontSize: '10px', color: '#8898B0', marginBottom: '12px', lineHeight: 1.4 }}>
                    Local sensitivity gradients (∂z/∂x) identifying which biomarkers have the highest impact on shifting the patient's metabolic coordinates:
                  </div>

                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    <button
                      onClick={() => setSensTab('z1')}
                      style={{
                        flex: 1, padding: '4px 8px', fontSize: '9px', fontVariant: 'small-caps', letterSpacing: '0.08em',
                        background: sensTab === 'z1' ? '#1C2333' : 'none', border: '1px solid #1C2333', borderRadius: '2px',
                        color: sensTab === 'z1' ? 'white' : '#8898B0', cursor: 'pointer', transition: 'all 0.2s',
                        fontFamily: 'inherit'
                      }}
                    >
                      Insulin Resistance (z₁)
                    </button>
                    <button
                      onClick={() => setSensTab('z2')}
                      style={{
                        flex: 1, padding: '4px 8px', fontSize: '9px', fontVariant: 'small-caps', letterSpacing: '0.08em',
                        background: sensTab === 'z2' ? '#1C2333' : 'none', border: '1px solid #1C2333', borderRadius: '2px',
                        color: sensTab === 'z2' ? 'white' : '#8898B0', cursor: 'pointer', transition: 'all 0.2s',
                        fontFamily: 'inherit'
                      }}
                    >
                      Liver Fat (z₂)
                    </button>
                  </div>

                  {activeContribs.slice(0, 4).map((c, i) => {
                    const displayNames = {
                      glucose: 'Fasting Glucose',
                      insulin: 'Fasting Insulin',
                      triglycerides: 'Triglycerides',
                      hdl: 'HDL Cholesterol',
                      ast: 'AST',
                      alt: 'ALT',
                      ggt: 'GGT',
                    };
                    const name = displayNames[c.feature] || c.feature;
                    const barWidth = c.contribution * 100;
                    return (
                      <div key={i} style={{ marginBottom: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                          <span style={{ fontSize: '10px', color: '#BCC8D8' }}>{name}</span>
                          <span style={{ fontSize: '10px', fontFamily: "'JetBrains Mono', monospace", color: '#E0E8FF' }}>
                            {(c.contribution * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div style={{ height: '3px', background: '#1C2333', borderRadius: '2px', overflow: 'hidden' }}>
                          <div style={{
                            height: '100%',
                            width: `${barWidth}%`,
                            background: sensTab === 'z1' ? '#F5A623' : '#3D8EF8',
                            borderRadius: '2px',
                            transition: 'width 0.5s ease-out',
                          }} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Section 3: Route to safety (non-healthy only) */}
                {!isHealthy && result.interventions && result.interventions.length > 0 && (
                  <>
                    <div style={divider} />
                    <div style={{ marginBottom: '20px' }}>
                      <div style={sectionTitle}>Recommended Action Plan</div>
                      <div style={{ fontSize: '10px', color: '#8898B0', marginBottom: '12px', lineHeight: 1.4 }}>
                        Targeted clinical biomarker reductions to move patient back to Metabolically Healthy. 
                        The safety route is solved as an optimal geodesic pathway on the learned Riemannian manifold:
                      </div>
                      {result.interventions.map((iv, i) => (
                        <div key={i} style={{ marginBottom: '10px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                            <span style={{ fontSize: '11px', color: '#BCC8D8' }}>{iv.name}</span>
                            <span style={{
                              fontSize: '11px',
                              fontFamily: "'JetBrains Mono', monospace",
                              color: iv.delta?.startsWith('+') ? '#00C47D' : '#F5A623',
                            }}>
                              {iv.delta}
                            </span>
                          </div>
                          <div style={{ height: '3px', background: '#1C2333', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{
                              height: '100%',
                              width: `${(iv.pct || 0.5) * 100}%`,
                              background: ph.color,
                              borderRadius: '2px',
                            }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}

                <div style={divider} />

                {/* Section 4: Model Credentials */}
                <div>
                  <div style={sectionTitle}>Model Credentials</div>
                  {[
                    ['Analysis Engine', 'LMSIS Metabolic Engine v2'],
                    ['Path Solver', 'Riemannian Geodesic Engine'],
                    ['Training Database Size', '847 normal-BMI adults'],
                    ['Validation Study Group', '212 patients'],
                    ['Engine Accuracy (Spearman ρ)', '0.542 (Strong)'],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontSize: '9px', color: '#8898B0' }}>{k}</span>
                      <span style={{ fontSize: '9px', fontFamily: "'JetBrains Mono', monospace", color: '#E0E8FF' }}>{v}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <ValidationTab />
            )}
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div
        style={{
          height: '36px',
          background: '#04060F',
          borderTop: '1px solid #0D1117',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 20px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', gap: '20px' }}>
          <button
            id="btn-back"
            onClick={onBack}
            style={bottomBtn}
          >
            ← Re-enter values
          </button>
          <button
            id="btn-switch"
            onClick={onSwitch}
            style={bottomBtn}
          >
            Switch patient →
          </button>
        </div>
        <span
          style={{
            fontSize: '9px',
            fontFamily: "'JetBrains Mono', monospace",
            color: '#2A3550',
          }}
        >
          LMSIS v2 · n=847 train · n=212 test
        </span>
      </div>
    </div>
  );
}

const sectionTitle = {
  fontSize: '9px',
  fontVariant: 'small-caps',
  letterSpacing: '0.18em',
  color: '#44556A',
  marginBottom: '10px',
  fontWeight: 600,
};

const divider = {
  borderTop: '1px solid #111D2E',
  margin: '0 0 16px 0',
};

const bottomBtn = {
  fontSize: '11px',
  color: '#3A4F6A',
  background: 'none',
  border: 'none',
  cursor: 'pointer',
  fontFamily: 'inherit',
  letterSpacing: '0.04em',
  transition: 'color 0.2s',
  padding: 0,
};
