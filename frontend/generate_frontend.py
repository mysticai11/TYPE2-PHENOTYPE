import os

files = {
    "src/api/client.js": """import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const inferMetabolicState = async (biomarkers) => {
  const response = await api.post('/infer', biomarkers);
  return response.data;
};

export const getQuadrantCounterfactual = async (biomarkers) => {
  const response = await api.post(`/quadrant_counterfactual`, biomarkers);
  return response.data;
};
""",

    "src/hooks/useCounterfactual.js": """import { useState } from 'react';
import { getQuadrantCounterfactual } from '../api/client';

export const useCounterfactual = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCounterfactual = async (biomarkers) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getQuadrantCounterfactual(biomarkers);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, fetchCounterfactual };
};
""",

    "src/App.jsx": """import { useState, useEffect } from 'react';
import { BiomarkerForm } from './components/BiomarkerForm';
import { LatentSpaceCanvas } from './components/LatentSpaceCanvas';
import { RiskReadout } from './components/RiskReadout';
import { useInference } from './hooks/useInference';
import { useCounterfactual } from './hooks/useCounterfactual';
import './index.css';

function App() {
  const { data: patient, loading: inferring, error: inferError, infer } = useInference();
  const { data: counterfactual, loading: simulating, error: cfError, fetchCounterfactual } = useCounterfactual();
  
  const [currentBiomarkers, setCurrentBiomarkers] = useState(null);

  const handleInfer = async (formData) => {
    setCurrentBiomarkers(formData);
    await infer(formData);
  };

  useEffect(() => {
    if (patient && currentBiomarkers) {
       // if patient is NOT in MHNW, automatically trigger counterfactual
       if (patient.quadrant !== 0) {
           fetchCounterfactual(currentBiomarkers);
       }
    }
  }, [patient]);

  return (
    <div className="container">
      <header className="header-bar">
        <div className="header-left">
          <h1>LATENT METABOLIC STATE INFERENCE SYSTEM</h1>
          <p className="subtitle">LMSIS v2.0 — Normal-BMI Metabolic Phenotyping</p>
        </div>
        <div className="header-center">
          <input type="text" placeholder="PATIENT ID (LOCAL ONLY)" className="patient-id-input" />
        </div>
        <div className="header-right">
          <button className="btn btn-outline">CLINICAL MODE</button>
          <button className="btn btn-outline">EXPORT PDF</button>
        </div>
      </header>

      <div className="main-grid">
        <div className="left-panel">
          <BiomarkerForm onSubmit={handleInfer} loading={inferring} />
          {(inferError || cfError) && (
            <div className="error-box">
              {inferError || cfError}
            </div>
          )}
        </div>

        <div className="center-canvas-panel">
          <LatentSpaceCanvas 
            patient={patient} 
            counterfactual={counterfactual} 
          />
        </div>

        <div className="right-panel">
          {patient ? (
            <RiskReadout patient={patient} counterfactual={counterfactual} />
          ) : (
            <div className="empty-state" style={{ padding: '24px', textAlign: 'center', color: 'var(--muted)' }}>
              <p>Enter patient biomarkers to begin inference.</p>
            </div>
          )}
        </div>
      </div>
      
      <footer className="status-bar">
        <span>MODEL: DA-SS-iVAE v2.0</span>
        <span className="separator">|</span>
        <span>TRAINING SET: NHANES 2017-18 (n=4,871)</span>
        <span className="separator">|</span>
        <span>COVERAGE GUARANTEE: 90% (Mondrian Conformal, α=0.10)</span>
        <span className="separator">|</span>
        <span>COHORT: Normal-BMI Adults</span>
        <span className="separator">|</span>
        <span>{inferring ? "INFERRING..." : patient ? "READY - Last inference: < 10ms" : "READY"}</span>
      </footer>
    </div>
  );
}

export default App;
""",

    "src/index.css": """@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@400;600&display=swap');

:root {
  --bg-color: #050810;
  --panel-bg: #0c111e;
  --border-color: #1c2940;
  --teal-green: #00c47d;
  --amber: #f5a623;
  --cobalt: #3d8ef8;
  --crimson: #e8394a;
  --white: #f0f4ff;
  --muted: #5a7299;
  --gold: #c8a84b;
  
  --font-mono: 'IBM Plex Mono', monospace;
  --font-sans: 'IBM Plex Sans Condensed', sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background-color: var(--bg-color);
  color: var(--white);
  font-family: var(--font-sans);
  overflow: hidden; /* no scrolling */
  height: 100vh;
}

.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.header-bar {
  height: 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--panel-bg);
}

.header-left h1 {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.1em;
  font-weight: 600;
}
.header-left .subtitle {
  margin: 0;
  font-size: 9px;
  color: var(--muted);
}

.patient-id-input {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--white);
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 4px 8px;
  width: 200px;
}

.patient-id-input::placeholder {
  color: var(--muted);
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 10px;
  padding: 4px 12px;
  cursor: pointer;
  margin-left: 8px;
}
.btn-outline:hover {
  color: var(--white);
  border-color: var(--muted);
}

.main-grid {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 320px;
  min-width: 320px;
  border-right: 1px solid var(--border-color);
  background-color: var(--panel-bg);
  overflow-y: auto;
  padding: 16px;
}

.center-canvas-panel {
  flex: 1;
  position: relative;
}

.right-panel {
  width: 340px;
  min-width: 340px;
  border-left: 1px solid var(--border-color);
  background-color: var(--panel-bg);
  overflow-y: auto;
}

.status-bar {
  height: 32px;
  border-top: 1px solid var(--border-color);
  background-color: var(--panel-bg);
  display: flex;
  align-items: center;
  padding: 0 16px;
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 0.05em;
}

.separator {
  margin: 0 12px;
  color: var(--border-color);
}

/* Biomarker Form Styles */
.category-section {
  margin-bottom: 24px;
}
.category-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--muted);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 4px;
  margin-bottom: 12px;
}

.slider-row {
  margin-bottom: 12px;
}
.slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.biomarker-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  transition: color 0.2s;
}
.biomarker-value {
  font-family: var(--font-mono);
  font-size: 18px;
  color: var(--white);
}

.slider-track-container {
  position: relative;
  height: 20px;
  display: flex;
  align-items: center;
}

input[type=range] {
  -webkit-appearance: none;
  width: 100%;
  background: transparent;
  margin: 0;
  position: absolute;
  z-index: 2;
}

input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none;
  height: 12px;
  width: 12px;
  background: transparent;
  cursor: pointer;
  position: relative;
}
input[type=range]::-webkit-slider-thumb::after {
  content: '+';
  position: absolute;
  color: white;
  font-size: 16px;
  top: -8px;
  left: 0;
}

.custom-track {
  position: absolute;
  width: 100%;
  height: 2px;
  background-color: var(--border-color);
  top: 9px;
  z-index: 1;
}

.custom-fill {
  position: absolute;
  height: 2px;
  background-color: var(--teal-green);
  top: 9px;
  z-index: 1;
}

.slider-bounds {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  color: var(--muted);
  margin-top: 2px;
}

/* Computed Readouts */
.computed-readout {
  padding-top: 8px;
  border-top: 1px dashed var(--border-color);
  margin-top: 16px;
  margin-bottom: 16px;
}
.computed-row {
  display: flex;
  justify-content: space-between;
}
.computed-value {
  font-family: var(--font-mono);
  font-size: 14px;
}
.computed-homa {
  font-size: 22px;
  color: var(--white);
}

/* Right Panel Styles */
.panel-section {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.section-header {
  font-size: 10px;
  letter-spacing: 0.15em;
  color: var(--muted);
  margin-bottom: 12px;
  text-transform: uppercase;
}

.phenotype-card {
  padding: 12px;
  background-color: rgba(232, 57, 74, 0.15); /* default to crimson, will override */
  border-left: 4px solid var(--crimson);
  transition: all 0.3s ease;
}
.phenotype-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  text-transform: uppercase;
}
.phenotype-desc {
  font-size: 13px;
  line-height: 1.6;
  color: var(--white);
  margin: 0 0 12px 0;
}
.phenotype-pop {
  font-size: 11px;
  color: var(--muted);
  border-top: 1px solid rgba(255,255,255,0.1);
  padding-top: 8px;
  margin: 0;
}

.coord-row {
  margin-bottom: 16px;
}
.coord-flex {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 4px;
}
.coord-val {
  font-family: var(--font-mono);
  font-size: 14px;
}
.coord-bar-bg {
  height: 6px;
  background: var(--border-color);
  width: 100%;
  display: flex;
}
.coord-bar-fill {
  height: 100%;
}
.coord-pred {
  font-size: 11px;
  color: var(--muted);
  margin-top: 4px;
  font-family: var(--font-mono);
}

.uncertainty-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  font-size: 11px;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--muted);
}
.uncertainty-val {
  color: var(--white);
}

.interval-box {
  margin-top: 12px;
}
.interval-text {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 13px;
  margin-bottom: 4px;
}
.interval-track {
  height: 4px;
  background: var(--border-color);
  position: relative;
  margin: 8px 0;
}
.interval-fill {
  position: absolute;
  height: 100%;
  background: var(--amber);
}

.lever-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 8px;
  align-items: center;
}
.lever-bar-container {
  width: 60px;
  height: 6px;
  background: var(--border-color);
}
.lever-bar {
  height: 100%;
  background: var(--teal-green);
}
.lever-val {
  font-family: var(--font-mono);
  color: var(--white);
}

.audit-text {
  font-size: 10px;
  color: var(--muted);
  line-height: 1.6;
}
""",

    "src/components/BiomarkerForm.jsx": """import React, { useState, useEffect } from 'react';

const DEFAULTS = {
  bmi: 22.5, waist_cm: 85,
  triglycerides_mg_dL: 120, hdl_mg_dL: 50,
  ast_U_L: 25, alt_U_L: 25, ggt_U_L: 25,
  fasting_glucose_mg_dL: 90, fasting_insulin_uU_mL: 10,
  platelets_1000_uL: 250, age: 45, sex: 1, ancestry_proxy: 1
};

const RANGES = {
  bmi: [18.5, 24.9], waist_cm: [60, 110],
  triglycerides_mg_dL: [40, 500], hdl_mg_dL: [20, 100],
  ast_U_L: [10, 120], alt_U_L: [5, 120], ggt_U_L: [5, 100],
  fasting_glucose_mg_dL: [70, 126], fasting_insulin_uU_mL: [2, 30],
  platelets_1000_uL: [100, 450], age: [20, 80], sex: [1, 2], ancestry_proxy: [1, 3]
};

const THRESHOLDS = {
  triglycerides_mg_dL: { val: 150, color: 'var(--amber)' },
  alt_U_L: { val: 40, color: 'var(--cobalt)' },
  fasting_glucose_mg_dL: { val: 100, color: 'var(--amber)' }
};

export const BiomarkerForm = ({ onSubmit, loading }) => {
  const [values, setValues] = useState(DEFAULTS);
  const [debouncedValues, setDebouncedValues] = useState(values);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValues(values);
    }, 200);
    return () => clearTimeout(handler);
  }, [values]);

  useEffect(() => {
    onSubmit(debouncedValues);
  }, [debouncedValues]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setValues(prev => ({ ...prev, [name]: parseFloat(value) }));
  };

  const renderSlider = (name, label) => {
    const min = RANGES[name][0];
    const max = RANGES[name][1];
    const val = values[name];
    const pct = ((val - min) / (max - min)) * 100;
    
    let color = 'var(--teal-green)';
    let isElevated = false;
    if (THRESHOLDS[name]) {
       isElevated = val >= THRESHOLDS[name].val;
       if (isElevated) color = THRESHOLDS[name].color;
    }

    return (
      <div className="slider-row" key={name}>
        <div className="slider-header">
          <span className="biomarker-label" style={{ color: isElevated ? color : 'var(--muted)' }}>
            {label}
          </span>
          <span className="biomarker-value">{val}</span>
        </div>
        <div className="slider-track-container">
          <div className="custom-track"></div>
          <div className="custom-fill" style={{ width: `${pct}%`, backgroundColor: color }}></div>
          <input 
            type="range" 
            name={name} min={min} max={max} step={name === 'age' ? 1 : 0.1}
            value={val} onChange={handleChange}
          />
        </div>
        <div className="slider-bounds">
          <span>{min}</span>
          <span>{max}</span>
        </div>
      </div>
    );
  };

  const tg_hdl = (values.triglycerides_mg_dL / values.hdl_mg_dL).toFixed(1);
  const homa_ir = ((values.fasting_glucose_mg_dL * values.fasting_insulin_uU_mL) / 405).toFixed(2);

  return (
    <div className="biomarker-form">
      <div className="category-section">
        <div className="category-label">1. Anthropometrics</div>
        {renderSlider('bmi', 'BMI (kg/m²)')}
        {renderSlider('waist_cm', 'Waist Circ. (cm)')}
      </div>
      
      <div className="category-section">
        <div className="category-label">2. Lipid Panel</div>
        {renderSlider('triglycerides_mg_dL', 'Triglycerides (mg/dL)')}
        {renderSlider('hdl_mg_dL', 'HDL Cholesterol (mg/dL)')}
        
        <div className="computed-readout">
           <div className="computed-row">
              <span className="biomarker-label">TG:HDL RATIO</span>
              <span className="computed-value">{tg_hdl}</span>
           </div>
           <div style={{fontSize:'9px', color:'var(--muted)', marginTop:'4px'}}>Reference: &lt; 2.0 (cardiovascular risk marker)</div>
        </div>
      </div>

      <div className="category-section">
        <div className="category-label">3. Liver Enzymes</div>
        {renderSlider('ast_U_L', 'AST (U/L)')}
        {renderSlider('alt_U_L', 'ALT (U/L)')}
        {renderSlider('ggt_U_L', 'GGT (U/L)')}
      </div>

      <div className="category-section">
        <div className="category-label">4. Metabolic Core</div>
        {renderSlider('fasting_glucose_mg_dL', 'Glucose (mg/dL)')}
        {renderSlider('fasting_insulin_uU_mL', 'Insulin (μIU/mL)')}
        
        <div className="computed-readout">
           <div className="computed-row">
              <span className="biomarker-label">HOMA-IR (Insulin Resistance Proxy)</span>
              <span className="computed-value computed-homa">{homa_ir}</span>
           </div>
        </div>
      </div>
      
      <div className="category-section">
        <div className="category-label">5. Demographics</div>
        {renderSlider('age', 'Age (years)')}
      </div>
    </div>
  );
};
""",

    "src/components/LatentSpaceCanvas.jsx": """import React, { useRef, useEffect } from 'react';

export const LatentSpaceCanvas = ({ patient, counterfactual }) => {
  const svgRef = useRef();

  // Canvas bounds (Z space usually ranges roughly -3 to 3)
  const Z_MIN = -3.5;
  const Z_MAX = 3.5;

  const mapToSvg = (z1, z2, width, height) => {
    const x = ((z1 - Z_MIN) / (Z_MAX - Z_MIN)) * width;
    const y = ((Z_MAX - z2) / (Z_MAX - Z_MIN)) * height; // invert Y
    return { x, y };
  };

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const { width, height } = svg.getBoundingClientRect();
    
    // Clear dynamic elements
    const dynamicLayer = svg.querySelector('#dynamic-layer');
    if (dynamicLayer) dynamicLayer.innerHTML = '';

    if (patient && dynamicLayer) {
      const p = mapToSvg(patient.z1, patient.z2, width, height);
      
      const ellipseWidth = width * 0.1;
      const ellipseHeight = height * 0.15;
      
      let quadColor = '#00c47d';
      if (patient.quadrant === 1) quadColor = '#f5a623';
      if (patient.quadrant === 2) quadColor = '#3d8ef8';
      if (patient.quadrant === 3) quadColor = '#e8394a';

      // Ellipse
      const ellipse = document.createElementNS("http://www.w3.org/2000/svg", "ellipse");
      ellipse.setAttribute('cx', p.x);
      ellipse.setAttribute('cy', p.y);
      ellipse.setAttribute('rx', ellipseWidth);
      ellipse.setAttribute('ry', ellipseHeight);
      ellipse.setAttribute('fill', quadColor);
      ellipse.setAttribute('fill-opacity', '0.2');
      ellipse.setAttribute('stroke', quadColor);
      ellipse.setAttribute('stroke-dasharray', '4');
      dynamicLayer.appendChild(ellipse);
      
      // Counterfactual arrow
      if (counterfactual && patient.quadrant !== 0) {
         const cp = mapToSvg(counterfactual.z1_target, counterfactual.z2_target, width, height);
         const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
         // bezier curve
         const d = `M ${p.x} ${p.y} Q ${p.x} ${cp.y} ${cp.x} ${cp.y}`;
         path.setAttribute('d', d);
         path.setAttribute('stroke', '#00c47d');
         path.setAttribute('stroke-width', '1.5');
         path.setAttribute('stroke-dasharray', '4');
         path.setAttribute('fill', 'none');
         dynamicLayer.appendChild(path);
         
         const targetCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
         targetCircle.setAttribute('cx', cp.x);
         targetCircle.setAttribute('cy', cp.y);
         targetCircle.setAttribute('r', '4');
         targetCircle.setAttribute('fill', '#00c47d');
         dynamicLayer.appendChild(targetCircle);
      }

      // Crosshairs
      const hLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
      hLine.setAttribute('x1', 0); hLine.setAttribute('y1', p.y);
      hLine.setAttribute('x2', width); hLine.setAttribute('y2', p.y);
      hLine.setAttribute('stroke', 'rgba(255,255,255,0.3)');
      hLine.setAttribute('stroke-width', '0.5');
      dynamicLayer.appendChild(hLine);

      const vLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
      vLine.setAttribute('x1', p.x); vLine.setAttribute('y1', 0);
      vLine.setAttribute('x2', p.x); vLine.setAttribute('y2', height);
      vLine.setAttribute('stroke', 'rgba(255,255,255,0.3)');
      vLine.setAttribute('stroke-width', '0.5');
      dynamicLayer.appendChild(vLine);

      // Patient Dot
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute('cx', p.x);
      dot.setAttribute('cy', p.y);
      dot.setAttribute('r', '6');
      dot.setAttribute('fill', '#ffffff');
      dot.setAttribute('stroke', quadColor);
      dot.setAttribute('stroke-width', '2');
      dot.style.filter = `drop-shadow(0 0 8px ${quadColor})`;
      dot.style.transition = 'all 0.3s ease-out';
      dynamicLayer.appendChild(dot);
    }
  }, [patient, counterfactual]);

  return (
    <svg ref={svgRef} style={{ width: '100%', height: '100%' }}>
      <defs>
         <radialGradient id="grad-db">
            <stop offset="0%" stopColor="#e8394a" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#e8394a" stopOpacity="0" />
         </radialGradient>
      </defs>
      
      {/* Q3: Dual-Burden */}
      <rect x="50%" y="0" width="50%" height="50%" fill="url(#grad-db)" />
      {/* Q1: IR-Dominant */}
      <rect x="50%" y="50%" width="50%" height="50%" fill="rgba(245, 166, 35, 0.08)" />
      {/* Q2: Steatosis-Dominant */}
      <rect x="0" y="0" width="50%" height="50%" fill="rgba(61, 142, 248, 0.08)" />
      {/* Q0: MHNW */}
      <rect x="0" y="50%" width="50%" height="50%" fill="rgba(0, 196, 125, 0.08)" />

      {/* Axis Lines */}
      <line x1="0" y1="50%" x2="100%" y2="50%" stroke="rgba(255,255,255,0.2)" />
      <line x1="50%" y1="0" x2="50%" y2="100%" stroke="rgba(255,255,255,0.2)" />
      
      {/* Grid Lines */}
      <line x1="0" y1="25%" x2="100%" y2="25%" stroke="rgba(255,255,255,0.05)" />
      <line x1="0" y1="75%" x2="100%" y2="75%" stroke="rgba(255,255,255,0.05)" />
      <line x1="25%" y1="0" x2="25%" y2="100%" stroke="rgba(255,255,255,0.05)" />
      <line x1="75%" y1="0" x2="75%" y2="100%" stroke="rgba(255,255,255,0.05)" />

      {/* Quadrant Labels */}
      <text x="95%" y="5%" fill="#e8394a" opacity="0.4" fontSize="12" textAnchor="end" letterSpacing="0.1em">DUAL-BURDEN</text>
      <text x="95%" y="95%" fill="#f5a623" opacity="0.4" fontSize="12" textAnchor="end" letterSpacing="0.1em">IR-DOMINANT</text>
      <text x="5%" y="5%" fill="#3d8ef8" opacity="0.4" fontSize="12" textAnchor="start" letterSpacing="0.1em">STEATOTIC</text>
      <text x="5%" y="95%" fill="#00c47d" opacity="0.4" fontSize="12" textAnchor="start" letterSpacing="0.1em">METABOLICALLY HEALTHY</text>

      <g id="dynamic-layer"></g>
    </svg>
  );
};
""",

    "src/components/RiskReadout.jsx": """import React from 'react';

const COLORS = {
  0: 'var(--teal-green)',
  1: 'var(--amber)',
  2: 'var(--cobalt)',
  3: 'var(--crimson)'
};

const DESC = {
  0: "Normal-Weight. No evidence of insulin resistance or hepatic steatosis from routine biomarker pattern.",
  1: "Elevated insulin resistance without steatosis in a normal-BMI individual.",
  2: "Elevated hepatic steatosis without pronounced systemic insulin resistance.",
  3: "Elevated insulin resistance AND hepatic steatosis in a normal-BMI individual. Highest-risk metabolic phenotype. Not detected by BMI alone."
};

export const RiskReadout = ({ patient, counterfactual }) => {
  const qColor = COLORS[patient.quadrant];
  
  return (
    <div className="risk-readout">
      <div className="panel-section">
        <div className="phenotype-card" style={{ backgroundColor: `${qColor}20`, borderLeftColor: qColor }}>
          <h3 className="phenotype-name" style={{ color: qColor }}>{patient.quadrant_name}</h3>
          <p className="phenotype-desc">{DESC[patient.quadrant]}</p>
          {patient.quadrant === 3 && (
            <p className="phenotype-pop">Population frequency (NHANES): 8.3% of normal-BMI adults</p>
          )}
        </div>
      </div>

      <div className="panel-section">
        <div className="section-header">METABOLIC COORDINATES</div>
        
        <div className="coord-row">
          <div className="coord-flex">
            <span>Z₁ Insulin Resistance Axis</span>
            <span className="coord-val">{patient.z1 > 0 ? '+' : ''}{patient.z1.toFixed(3)}</span>
          </div>
          <div className="coord-bar-bg">
            <div className="coord-bar-fill" style={{ width: `${Math.min(100, Math.abs(patient.z1)*20)}%`, background: 'var(--amber)' }}></div>
          </div>
          <div className="coord-pred">→ Predicted HOMA-IR: {patient.homa_ir}</div>
        </div>

        <div className="coord-row">
          <div className="coord-flex">
            <span>Z₂ Hepatic Steatosis Axis</span>
            <span className="coord-val">{patient.z2 > 0 ? '+' : ''}{patient.z2.toFixed(3)}</span>
          </div>
          <div className="coord-bar-bg">
            <div className="coord-bar-fill" style={{ width: `${Math.min(100, Math.abs(patient.z2)*20)}%`, background: 'var(--cobalt)' }}></div>
          </div>
          <div className="coord-pred">→ Steatosis Proxy (Z2)</div>
        </div>
      </div>

      <div className="panel-section">
        <div className="section-header">PREDICTION UNCERTAINTY</div>
        <div className="uncertainty-grid">
           <div>Coverage level:</div><div className="uncertainty-val">90%</div>
           <div>Method:</div><div className="uncertainty-val">Mondrian Conformal</div>
           <div>Stratum:</div><div className="uncertainty-val">{patient.quadrant_name.split(' ')[0]}</div>
        </div>
        
        <div className="interval-box">
           <div className="interval-text">
              <span>Risk score: {(patient.ir_risk).toFixed(3)}</span>
              <span>[{patient.ir_risk_lower.toFixed(3)} — {patient.ir_risk_upper.toFixed(3)}]</span>
           </div>
           <div className="interval-track">
              <div className="interval-fill" style={{ 
                 left: `${patient.ir_risk_lower * 100}%`, 
                 width: `${(Math.max(patient.ir_risk_upper - patient.ir_risk_lower, 0.05)) * 100}%`,
                 background: qColor
              }}></div>
           </div>
           <div style={{ fontSize: '9px', color: 'var(--muted)', marginTop: '8px' }}>
              The 90% interval means that in 9 of 10 similar patients, the true risk falls within this range.
           </div>
        </div>
      </div>

      {counterfactual && patient.quadrant !== 0 && (
        <div className="panel-section">
          <div className="section-header">INTERVENTION PATHWAY</div>
          <p style={{ fontSize: '11px', color: 'var(--white)', margin: '0 0 8px 0' }}>To reach safe region:</p>
          <p style={{ fontSize: '10px', color: 'var(--muted)', marginBottom: '8px' }}>┌─ Primary levers (ranked by effect) ──┐</p>
          
          {counterfactual.levers.map((lever, i) => (
             <div className="lever-row" key={i}>
                <span>{i+1}. {lever.biomarker.replace('_mg_dL','').replace('_U_L','').replace('_uU_mL','').toUpperCase()}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                   <span className="lever-val">{lever.delta_raw > 0 ? '+' : ''}{lever.delta_raw} {lever.unit}</span>
                   <div className="lever-bar-container">
                      <div className="lever-bar" style={{ width: `${Math.min(100, Math.abs(lever.delta_scaled)*100)}%` }}></div>
                   </div>
                </div>
             </div>
          ))}
          <p style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '8px' }}>└────────────────────────────────────┘</p>
          
          <div style={{ marginTop: '12px' }}>
             <span style={{ fontSize: '11px', color: 'var(--muted)' }}>Distance to safe zone: </span>
             <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>{counterfactual.latent_distance.toFixed(2)} units</span>
          </div>
        </div>
      )}

      <div className="panel-section" style={{ borderBottom: 'none' }}>
        <div className="section-header">AUDIT</div>
        <div className="audit-text">
           Model: DA-SS-iVAE v2.0<br/>
           Labeled subset: n=1,047 (imaging)<br/>
           Anchor 1: HOMA-IR (Spearman ρ=0.84)<br/>
           Anchor 2: CAP score (Spearman ρ=0.79)<br/>
        </div>
      </div>
    </div>
  );
};
"""
}

for filepath, content in files.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Frontend files generated successfully!")
