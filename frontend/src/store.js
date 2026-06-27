import { create } from 'zustand';

// ── Phenotype color palette (semantic, never decorative) ──────────────────────
export const PHENOTYPE = {
  'Metabolically Healthy': {
    key: 'healthy',
    color: '#00C47D',
    dimColor: 'rgba(0,196,125,0.15)',
    pulse: false,
    bannerLabel: 'METABOLICALLY HEALTHY',
    bannerSub: 'Normal insulin & liver markers',
    quadrantLabel: 'METABOLICALLY\nHEALTHY',
    quadrant: 0,
  },
  'IR-Dominant': {
    key: 'ir',
    color: '#F5A623',
    dimColor: 'rgba(245,166,35,0.15)',
    pulse: true,
    bannerLabel: 'INSULIN RESISTANCE — LIVER NORMAL',
    bannerSub: 'Elevated insulin resistance, liver unaffected',
    quadrantLabel: 'INSULIN\nRESISTANT',
    quadrant: 1,
  },
  'Steatosis-Dominant': {
    key: 'steatosis',
    color: '#3D8EF8',
    dimColor: 'rgba(61,142,248,0.15)',
    pulse: true,
    bannerLabel: 'LIVER FAT ELEVATED — IR NORMAL',
    bannerSub: 'Hepatic fat accumulation detected',
    quadrantLabel: 'STEATOSIS\nDOMINANT',
    quadrant: 2,
  },
  'Dual-Burden': {
    key: 'dual',
    color: '#E8394A',
    dimColor: 'rgba(232,57,74,0.15)',
    pulse: true,
    bannerLabel: 'DUAL-BURDEN — NOT DETECTED BY BMI ALONE',
    bannerSub: 'Concurrent IR and liver fat in normal-BMI patient',
    quadrantLabel: 'DUAL BURDEN\nZONE',
    quadrant: 3,
  },
};

// ── Preset clinical archetypes ────────────────────────────────────────────────
export const PRESETS = [
  {
    id: 'healthy',
    label: 'Metabolically Healthy',
    bmi: 22.1,
    phenotype: 'Metabolically Healthy',
    inputs: {
      glucose: 88, insulin: 6.2, triglycerides: 82, hdl: 58,
      ast: 19, alt: 18, ggt: 14,
    },
    // Fallback map coords (used if backend offline)
    z1: -0.82, z2: -0.61,
    homaIr: 1.36, predHomaIr: 1.4,
    predCapScore: 198, capLabel: 'S0 – None',
    irPct: 12, capPct: 8,
    riskScore: 0.09, riskLo: 0.04, riskHi: 0.16,
    interventions: [],
    geodesicPath: null,
  },
  {
    id: 'ir',
    label: 'IR-Dominant',
    bmi: 21.7,
    phenotype: 'IR-Dominant',
    inputs: {
      glucose: 108, insulin: 22.4, triglycerides: 186, hdl: 38,
      ast: 24, alt: 26, ggt: 28,
    },
    z1: 1.31, z2: -0.24,
    homaIr: 5.97, predHomaIr: 6.1,
    predCapScore: 225, capLabel: 'S1 – Mild',
    irPct: 78, capPct: 31,
    riskScore: 0.64, riskLo: 0.54, riskHi: 0.74,
    interventions: [
      { name: 'Triglycerides', delta: '-104 mg/dL', pct: 0.82 },
      { name: 'Fasting Insulin', delta: '-16.2 µIU/mL', pct: 0.91 },
      { name: 'HDL Cholesterol', delta: '+20 mg/dL', pct: 0.61 },
    ],
    geodesicPath: [
      [1.31, -0.24], [0.9, -0.3], [0.45, -0.4], [0.1, -0.45], [-0.3, -0.5],
    ],
    waypoints: [
      { t: 0.4, label: '↓ Triglycerides −104 mg/dL' },
      { t: 0.75, label: '↓ Fasting Insulin −16.2 µIU/mL' },
    ],
  },
  {
    id: 'steatosis',
    label: 'Steatosis-Dominant',
    bmi: 23.1,
    phenotype: 'Steatosis-Dominant',
    inputs: {
      glucose: 94, insulin: 8.1, triglycerides: 142, hdl: 44,
      ast: 41, alt: 54, ggt: 67,
    },
    z1: -0.21, z2: 1.44,
    homaIr: 1.89, predHomaIr: 2.0,
    predCapScore: 289, capLabel: 'S3 – Severe',
    irPct: 28, capPct: 87,
    riskScore: 0.72, riskLo: 0.62, riskHi: 0.81,
    interventions: [
      { name: 'ALT', delta: '-36 U/L', pct: 0.88 },
      { name: 'GGT', delta: '-53 U/L', pct: 0.79 },
      { name: 'Triglycerides', delta: '-60 mg/dL', pct: 0.55 },
    ],
    geodesicPath: [
      [-0.21, 1.44], [-0.3, 1.0], [-0.4, 0.6], [-0.5, 0.2], [-0.55, -0.3],
    ],
    waypoints: [
      { t: 0.35, label: '↓ ALT −36 U/L' },
      { t: 0.7, label: '↓ GGT −53 U/L' },
    ],
  },
  {
    id: 'dual',
    label: 'Dual-Burden',
    bmi: 22.6,
    phenotype: 'Dual-Burden',
    inputs: {
      glucose: 114, insulin: 28.7, triglycerides: 241, hdl: 34,
      ast: 41, alt: 54, ggt: 67,
    },
    z1: 1.68, z2: 1.44,
    homaIr: 8.08, predHomaIr: 8.3,
    predCapScore: 289, capLabel: 'S3 – Severe',
    irPct: 94, capPct: 91,
    riskScore: 0.84, riskLo: 0.73, riskHi: 0.94,
    interventions: [
      { name: 'Triglycerides', delta: '-159 mg/dL', pct: 0.95 },
      { name: 'Fasting Insulin', delta: '-22.5 µIU/mL', pct: 0.97 },
      { name: 'ALT', delta: '-36 U/L', pct: 0.82 },
    ],
    geodesicPath: [
      [1.68, 1.44], [1.2, 1.0], [0.7, 0.5], [0.2, 0.1], [-0.3, -0.3],
    ],
    waypoints: [
      { t: 0.3, label: '↓ Triglycerides −159 mg/dL' },
      { t: 0.65, label: '↓ Fasting Insulin −22.5 µIU/mL' },
    ],
  },
];

// ── Population cloud (200 dots, realistic clustering) ────────────────────────
const rng = (seed) => {
  let s = seed;
  return () => { s = (s * 16807 + 0) % 2147483647; return (s - 1) / 2147483646; };
};

export const POPULATION_DOTS = (() => {
  const rand = rng(42);
  const dots = [];
  // ~120 healthy (Q3: x<0, y<0)
  for (let i = 0; i < 120; i++) {
    const angle = rand() * Math.PI * 2;
    const r = rand() * 0.7 + 0.1;
    dots.push({ x: -0.5 + Math.cos(angle) * r * 0.8, y: -0.5 + Math.sin(angle) * r * 0.6, q: 0 });
  }
  // ~35 IR-dominant (Q1: x>0, y<0)
  for (let i = 0; i < 35; i++) {
    dots.push({ x: 0.6 + (rand() - 0.5) * 0.9, y: -0.4 + (rand() - 0.5) * 0.7, q: 1 });
  }
  // ~25 steatosis (Q2: x<0, y>0)
  for (let i = 0; i < 25; i++) {
    dots.push({ x: -0.5 + (rand() - 0.5) * 0.8, y: 0.7 + (rand() - 0.5) * 0.7, q: 2 });
  }
  // ~20 dual burden (Q4: x>0, y>0)
  for (let i = 0; i < 20; i++) {
    dots.push({ x: 0.9 + (rand() - 0.5) * 0.8, y: 0.9 + (rand() - 0.5) * 0.8, q: 3 });
  }
  return dots;
})();

// ── Zustand store ─────────────────────────────────────────────────────────────
export const useStore = create((set, get) => ({
  // Phase: 'intake' | 'transitioning' | 'map'
  phase: 'intake',
  // Active preset index (0-3) or null
  activePresetIdx: null,
  // The full inference result (either from backend or preset fallback)
  result: null,
  // The form inputs (keyed by field name)
  inputs: { glucose: '', insulin: '', triglycerides: '', hdl: '', ast: '', alt: '', ggt: '' },

  setPhase: (phase) => set({ phase }),
  setActivePresetIdx: (idx) => set({ activePresetIdx: idx }),
  setResult: (result) => set({ result }),
  setInputs: (inputs) => set({ inputs }),

  // Fill inputs from a preset
  applyPreset: (idx) => {
    const preset = PRESETS[idx];
    set({
      activePresetIdx: idx,
      inputs: { ...preset.inputs },
    });
  },

  // Load result from preset (fallback when backend not available)
  loadPresetResult: (idx) => {
    const preset = PRESETS[idx];
    set({ result: preset });
  },

  // Cycle to next preset (for "Switch patient" button on Screen 2)
  cyclePreset: () => {
    const current = get().activePresetIdx ?? 0;
    const next = (current + 1) % PRESETS.length;
    set({ activePresetIdx: next, inputs: { ...PRESETS[next].inputs }, result: PRESETS[next], phase: 'map' });
  },

  // Go back to intake (prefill values)
  returnToIntake: () => {
    set({ phase: 'intake' });
  },
}));
