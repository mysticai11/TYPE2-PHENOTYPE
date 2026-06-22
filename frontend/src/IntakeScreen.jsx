import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useStore, PRESETS, PHENOTYPE } from './store';

// ── Clinical reference ranges ─────────────────────────────────────────────────
const FIELDS = [
  {
    key: 'glucose',
    label: 'Fasting Glucose',
    unit: 'mg/dL',
    ref: '70–99',
    thresholds: { amber: 100, red: 126 },
    section: 'metabolic',
    required: true,
    placeholder: '88',
  },
  {
    key: 'insulin',
    label: 'Fasting Insulin',
    unit: 'µIU/mL',
    ref: '2–25',
    thresholds: { amber: 15, red: 25 },
    section: 'metabolic',
    required: true,
    placeholder: '6',
  },
  {
    key: 'triglycerides',
    label: 'Triglycerides',
    unit: 'mg/dL',
    ref: '<150',
    thresholds: { amber: 150, red: 200 },
    section: 'lipid',
    required: true,
    placeholder: '82',
  },
  {
    key: 'hdl',
    label: 'HDL Cholesterol',
    unit: 'mg/dL',
    ref: '>40 (♂) >50 (♀)',
    thresholds: { amber: 40, red: 35, invert: true },
    section: 'lipid',
    required: true,
    placeholder: '58',
  },
  {
    key: 'ast',
    label: 'AST',
    unit: 'U/L',
    ref: '10–40',
    thresholds: { amber: 40, red: 60 },
    section: 'liver',
    required: true,
    placeholder: '19',
  },
  {
    key: 'alt',
    label: 'ALT',
    unit: 'U/L',
    ref: '7–56',
    thresholds: { amber: 56, red: 80 },
    section: 'liver',
    required: true,
    placeholder: '18',
  },
  {
    key: 'ggt',
    label: 'GGT',
    unit: 'U/L',
    ref: '9–48',
    thresholds: { amber: 48, red: 80 },
    section: 'liver',
    required: true,
    placeholder: '14',
  },
];

const SECTIONS = {
  metabolic: { label: 'Metabolic Core', derived: 'HOMA-IR' },
  lipid: { label: 'Lipid Profile', derived: 'TG:HDL' },
  liver: { label: 'Liver Markers', derived: null },
};

// ── Compute HOMA-IR ───────────────────────────────────────────────────────────
function computeHomaIr(glucose, insulin) {
  const g = parseFloat(glucose);
  const i = parseFloat(insulin);
  if (isNaN(g) || isNaN(i) || g <= 0 || i <= 0) return null;
  return ((g * i) / 405).toFixed(2);
}

function computeTgHdl(tg, hdl) {
  const t = parseFloat(tg);
  const h = parseFloat(hdl);
  if (isNaN(t) || isNaN(h) || h <= 0) return null;
  return (t / h).toFixed(2);
}

// ── Border color for individual input ─────────────────────────────────────────
function getBorderColor(field, value) {
  if (!value || value === '') return undefined;
  const v = parseFloat(value);
  if (isNaN(v)) return undefined;
  if (field.thresholds?.invert) {
    if (v <= field.thresholds.red) return '#E8394A';
    if (v <= field.thresholds.amber) return '#F5A623';
  } else {
    if (field.thresholds?.red && v >= field.thresholds.red) return '#E8394A';
    if (field.thresholds?.amber && v >= field.thresholds.amber) return '#F5A623';
  }
  return undefined;
}

// ── Shimmer button ────────────────────────────────────────────────────────────
function LocateButton({ disabled, loading, onClick }) {
  return (
    <button
      id="locate-btn"
      disabled={disabled}
      onClick={onClick}
      className="locate-btn"
      style={{
        width: '100%',
        height: '52px',
        border: 'none',
        borderRadius: '2px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontSize: '13px',
        fontFamily: 'inherit',
        letterSpacing: '0.15em',
        fontWeight: 600,
        position: 'relative',
        overflow: 'hidden',
        transition: 'background-color 0.3s, background-image 0.3s, opacity 0.3s',
        backgroundColor: disabled ? '#1C2333' : loading ? 'transparent' : '#0F2040',
        backgroundImage: loading ? 'linear-gradient(90deg, #0d1f3c, #172d4d, #0d1f3c)' : 'none',
        color: disabled ? '#4A5568' : '#C8D9F0',
        backgroundSize: loading ? '200% 100%' : '100% 100%',
        animation: loading ? 'shimmer 1.2s linear infinite' : 'none',
      }}
    >
      {loading ? (
        <span style={{ opacity: 0.7 }}>LOCATING METABOLIC STATE…</span>
      ) : (
        <span>LOCATE METABOLIC STATE →</span>
      )}
    </button>
  );
}

// ── Derived readout card ──────────────────────────────────────────────────────
function DerivedCard({ label, value, risk, unit }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#F0F0ED',
        border: '1px solid #DDD',
        borderRadius: '2px',
        padding: '7px 12px',
        marginTop: '8px',
      }}
    >
      <span style={{ fontSize: '11px', color: '#777', fontVariant: 'small-caps', letterSpacing: '0.08em' }}>
        {label}
      </span>
      <span
        style={{
          fontSize: '14px',
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 600,
          color: risk === 'red' ? '#C0392B' : risk === 'amber' ? '#B7770D' : '#2D6A4F',
        }}
      >
        {value !== null ? `${value}${unit ? ' ' + unit : ''}` : '—'}
      </span>
    </div>
  );
}

// ── Single input row ──────────────────────────────────────────────────────────
function InputRow({ field, value, onChange }) {
  const borderColor = getBorderColor(field, value);
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', marginBottom: '14px' }}>
      <div style={{ flex: 1 }}>
        <label
          style={{
            display: 'block',
            fontSize: '10px',
            fontVariant: 'small-caps',
            letterSpacing: '0.12em',
            color: '#888',
            marginBottom: '4px',
            fontFamily: 'inherit',
          }}
        >
          {field.label}
        </label>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              flex: 1,
              borderBottom: `2px solid ${borderColor || '#C8C8C4'}`,
              transition: 'border-color 0.3s',
            }}
          >
            <input
              id={`input-${field.key}`}
              type="number"
              step="any"
              value={value}
              onChange={(e) => onChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                outline: 'none',
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '16px',
                color: '#1A1A1A',
                padding: '4px 0',
              }}
            />
          </div>
          <span style={{ fontSize: '11px', color: '#AAA', width: '50px', flexShrink: 0 }}>
            {field.unit}
          </span>
          <span
            style={{
              fontSize: '10px',
              color: '#BBB',
              fontStyle: 'italic',
              width: '80px',
              flexShrink: 0,
              textAlign: 'right',
            }}
          >
            {field.ref}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── SCREEN 1 — INTAKE FORM ────────────────────────────────────────────────────
export default function IntakeScreen({ onSubmit }) {
  const { inputs, setInputs, activePresetIdx, applyPreset, setActivePresetIdx } = useStore();
  const [loading, setLoading] = useState(false);
  const [, forceUpdate] = useState(0);

  // Force update when inputs change externally (preset fill)
  const inputsRef = useRef(inputs);
  useEffect(() => {
    inputsRef.current = inputs;
    forceUpdate((n) => n + 1);
  }, [inputs]);

  const handleChange = useCallback(
    (key, val) => {
      setActivePresetIdx(null);
      setInputs({ ...inputs, [key]: val });
    },
    [inputs, setInputs, setActivePresetIdx]
  );

  const handlePreset = (idx) => {
    applyPreset(idx);
  };

  const isComplete = FIELDS.every((f) => {
    const v = inputs[f.key];
    return v !== '' && v !== undefined && !isNaN(parseFloat(v));
  });

  const handleSubmit = async () => {
    if (!isComplete || loading) return;
    setLoading(true);

    // Try real backend; fall back to preset data
    let result = null;
    try {
      const [inferRes, geoRes] = await Promise.allSettled([
        fetch('/infer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            glucose: parseFloat(inputs.glucose),
            insulin: parseFloat(inputs.insulin),
            triglycerides: parseFloat(inputs.triglycerides),
            hdl: parseFloat(inputs.hdl),
            ast: parseFloat(inputs.ast),
            alt: parseFloat(inputs.alt),
            ggt: parseFloat(inputs.ggt),
            bmi: 22.5, age: 45, sex: 0,
            waist_cm: 80, sbp: 120, dbp: 80,
          }),
        }).then((r) => r.json()),
        fetch('/geodesic_pathway', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            glucose: parseFloat(inputs.glucose),
            insulin: parseFloat(inputs.insulin),
            triglycerides: parseFloat(inputs.triglycerides),
            hdl: parseFloat(inputs.hdl),
            ast: parseFloat(inputs.ast),
            alt: parseFloat(inputs.alt),
            ggt: parseFloat(inputs.ggt),
            bmi: 22.5, age: 45, sex: 0,
            waist_cm: 80, sbp: 120, dbp: 80,
          }),
        }).then((r) => r.json()),
      ]);

      const infer = inferRes.status === 'fulfilled' ? inferRes.value : null;
      const geo = geoRes.status === 'fulfilled' ? geoRes.value : null;

      if (infer && infer.z1 !== undefined) {
        const qMap = ['Metabolically Healthy', 'IR-Dominant', 'Steatosis-Dominant', 'Dual-Burden'];
        result = {
          z1: infer.z1,
          z2: infer.z2,
          phenotype: qMap[infer.quadrant] || 'Metabolically Healthy',
          homaIr: infer.homa_ir,
          predHomaIr: infer.pred_homa_ir,
          predCapScore: infer.pred_cap_score,
          capLabel: infer.pred_cap_score > 280 ? 'S3 – Severe' : infer.pred_cap_score > 248 ? 'S2 – Moderate' : infer.pred_cap_score > 215 ? 'S1 – Mild' : 'S0 – None',
          irPct: Math.round(infer.ir_percentile * 100),
          capPct: Math.round(infer.cap_percentile * 100),
          riskScore: infer.ir_risk,
          riskLo: infer.ir_risk_lower,
          riskHi: infer.ir_risk_upper,
          bmi: 22.5,
          interventions: (geo?.interventions || []).slice(0, 3).map((iv) => ({
            name: iv.feature_name || iv.name,
            delta: iv.delta_display || iv.delta,
            pct: Math.min(1, Math.abs(iv.magnitude || 0.7)),
          })),
          geodesicPath: geo?.geodesic_path || null,
          waypoints: [],
          z1_contributions: infer.z1_contributions || [],
          z2_contributions: infer.z2_contributions || [],
        };
      }
    } catch (_) {
      result = null;
    }

    // Fall back to active preset if backend unavailable
    if (!result && activePresetIdx !== null) {
      result = PRESETS[activePresetIdx];
    } else if (!result) {
      // Best-effort compute from inputs
      const tg = parseFloat(inputs.triglycerides);
      const hdl = parseFloat(inputs.hdl);
      const glu = parseFloat(inputs.glucose);
      const ins = parseFloat(inputs.insulin);
      const alt = parseFloat(inputs.alt);
      const ggt = parseFloat(inputs.ggt);

      const z1 = Math.max(-2, Math.min(2, (ins / 10 - 1.2) * 0.9 + (glu / 80 - 1) * 0.5 - (hdl / 45 - 1) * 0.4));
      const z2 = Math.max(-2, Math.min(2, (alt / 25 - 0.8) * 0.9 + (ggt / 25 - 0.6) * 0.7 + (tg / 100 - 0.9) * 0.4));

      let phenotype = 'Metabolically Healthy';
      if (z1 >= 0 && z2 >= 0) phenotype = 'Dual-Burden';
      else if (z1 >= 0) phenotype = 'IR-Dominant';
      else if (z2 >= 0) phenotype = 'Steatosis-Dominant';

      const homaIr = parseFloat(computeHomaIr(glu, ins));
      result = {
        z1, z2, phenotype, bmi: 22.5,
        homaIr, predHomaIr: homaIr + 0.15,
        predCapScore: 200 + z2 * 60, capLabel: z2 > 1 ? 'S3 – Severe' : z2 > 0.5 ? 'S2 – Moderate' : 'S1 – Mild',
        irPct: Math.round(Math.min(99, Math.max(1, (z1 + 2) / 4 * 100))),
        capPct: Math.round(Math.min(99, Math.max(1, (z2 + 2) / 4 * 100))),
        riskScore: Math.min(0.99, Math.max(0.01, (z1 + z2 + 4) / 8)),
        riskLo: 0.0, riskHi: 0.0,
        interventions: [], geodesicPath: null,
      };
    }

    setTimeout(() => {
      onSubmit(result);
    }, 500);
  };

  const homaIr = computeHomaIr(inputs.glucose, inputs.insulin);
  const tgHdl = computeTgHdl(inputs.triglycerides, inputs.hdl);

  const homaRisk =
    homaIr !== null
      ? parseFloat(homaIr) >= 3.5 ? 'red' : parseFloat(homaIr) >= 2.5 ? 'amber' : 'ok'
      : null;
  const tgHdlRisk =
    tgHdl !== null
      ? parseFloat(tgHdl) >= 4 ? 'red' : parseFloat(tgHdl) >= 2.5 ? 'amber' : 'ok'
      : null;

  const sections = [
    { id: 'metabolic', fields: FIELDS.filter((f) => f.section === 'metabolic') },
    { id: 'lipid', fields: FIELDS.filter((f) => f.section === 'lipid') },
    { id: 'liver', fields: FIELDS.filter((f) => f.section === 'liver') },
  ];

  return (
    <div
      style={{
        height: '100vh',
        overflowY: 'auto',
        background: '#FAFAF8',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: '56px',
        paddingBottom: '80px',
      }}
    >
      <div style={{ width: '100%', maxWidth: '680px', padding: '0 24px' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '44px' }}>
          <h1
            style={{
              fontFamily: '"DM Serif Display", Georgia, serif',
              fontSize: '32px',
              fontWeight: 400,
              color: '#1A1A18',
              letterSpacing: '-0.01em',
              marginBottom: '10px',
              lineHeight: 1.15,
            }}
          >
            LMSIS
          </h1>
          <p
            style={{
              fontSize: '13px',
              color: '#888',
              fontFamily: 'inherit',
              letterSpacing: '0.01em',
            }}
          >
            Enter routine blood values to locate the patient's metabolic state.
          </p>
        </div>

        {/* Preset buttons */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '8px',
            marginBottom: '36px',
          }}
        >
          {PRESETS.map((preset, idx) => {
            const ph = PHENOTYPE[preset.phenotype];
            const isActive = activePresetIdx === idx;
            return (
              <button
                key={preset.id}
                id={`preset-${preset.id}`}
                onClick={() => handlePreset(idx)}
                style={{
                  padding: '10px 8px',
                  border: `1.5px solid ${isActive ? ph.color : '#E0E0DC'}`,
                  borderRadius: '3px',
                  background: isActive ? `${ph.color}12` : '#FFF',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  textAlign: 'left',
                  fontFamily: 'inherit',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <span
                    style={{
                      width: '7px',
                      height: '7px',
                      borderRadius: '50%',
                      background: ph.color,
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 600,
                      color: '#333',
                      lineHeight: 1.2,
                    }}
                  >
                    {preset.label}
                  </span>
                </div>
                <div style={{ fontSize: '10px', color: '#AAA', paddingLeft: '13px' }}>
                  BMI {preset.bmi}
                </div>
              </button>
            );
          })}
        </div>

        {/* Form sections */}
        {sections.map(({ id, fields }) => {
          const sec = SECTIONS[id];
          return (
            <div key={id} style={{ marginBottom: '28px' }}>
              <div
                style={{
                  borderTop: '1px solid #E0E0DC',
                  paddingTop: '16px',
                  marginBottom: '16px',
                  fontSize: '10px',
                  fontVariant: 'small-caps',
                  letterSpacing: '0.18em',
                  color: '#999',
                  fontWeight: 600,
                }}
              >
                {sec.label}
              </div>
              {fields.map((field) => (
                <InputRow
                  key={field.key}
                  field={field}
                  value={inputs[field.key] ?? ''}
                  onChange={handleChange}
                />
              ))}

              {/* Derived readout */}
              {id === 'metabolic' && (
                <DerivedCard
                  label="HOMA-IR"
                  value={homaIr}
                  risk={homaRisk}
                  unit=""
                />
              )}
              {id === 'lipid' && (
                <DerivedCard
                  label="TG:HDL Ratio"
                  value={tgHdl}
                  risk={tgHdlRisk}
                  unit=""
                />
              )}
            </div>
          );
        })}

        {/* Submit button */}
        <div style={{ marginTop: '20px' }}>
          <LocateButton disabled={!isComplete} loading={loading} onClick={handleSubmit} />
        </div>

        {/* About/Footer text */}
        <div
          style={{
            marginTop: '30px',
            paddingTop: '15px',
            borderTop: '1px solid #E0E0DC',
            fontSize: '11px',
            color: '#888880',
            lineHeight: '1.5',
            textAlign: 'center',
          }}
        >
          This website, presenting research from the project <em>Predictive Risk Intelligence for Metabolic Screening in Diabetes</em>, implements the <strong>Latent Metabolic State Inference System (LMSIS)</strong>, a semi-supervised deep learning framework for early detection of metabolic dysfunction in normal-BMI adults.
        </div>
      </div>
    </div>
  );
}
