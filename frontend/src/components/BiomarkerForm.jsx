import React, { useState } from 'react';

const DEFAULTS = {
  fasting_glucose_mg_dL: 94,
  fasting_insulin_uU_mL: 10,
  triglycerides_mg_dL: 120,
  hdl_mg_dL: 50,
  ast_U_L: 25,
  alt_U_L: 25,
  ggt_U_L: 25,
  bmi: 22.5,
  waist_cm: 85,
  platelets_1000_uL: 250,
  age: 45,
  sex: 1,
  ancestry_proxy: 3
};

const RANGES = {
  fasting_glucose_mg_dL: { min: 70, max: 150, high: 126, label: "Fasting Glucose", unit: "mg/dL", ref: "Normal: 70–99" },
  fasting_insulin_uU_mL: { min: 2, max: 50, high: 30, label: "Fasting Insulin", unit: "μIU/mL", ref: "Normal: <20" },
  triglycerides_mg_dL: { min: 40, max: 300, high: 200, label: "Triglycerides", unit: "mg/dL", ref: "Normal: <150" },
  hdl_mg_dL: { min: 20, max: 100, high: 0, label: "HDL Cholesterol", unit: "mg/dL", ref: "Normal: >40" },
  ast_U_L: { min: 5, max: 100, high: 40, label: "AST", unit: "U/L", ref: "Normal: 10–40" },
  alt_U_L: { min: 1, max: 100, high: 40, label: "ALT", unit: "U/L", ref: "Normal: 5–40" },
  ggt_U_L: { min: 5, max: 150, high: 50, label: "GGT", unit: "U/L", ref: "Normal: 5–50" },
  bmi: { min: 18.5, max: 24.9, high: 25, label: "BMI", unit: "kg/m²", ref: "Normal: 18.5–24.9" },
  waist_cm: { min: 60, max: 120, high: 90, label: "Waist Circumference", unit: "cm", ref: "Normal: <90" },
  platelets_1000_uL: { min: 100, max: 500, high: 450, label: "Platelets", unit: "1000/μL", ref: "Normal: 150–450" },
  age: { min: 20, max: 80, high: 100, label: "Age", unit: "years", ref: "" },
  sex: { min: 1, max: 2, high: 3, label: "Sex", unit: "", ref: "" },
  ancestry_proxy: { min: 1, max: 6, high: 7, label: "Ancestry", unit: "", ref: "" }
};

export const BiomarkerForm = ({ onSubmit, isSubmitting, initialValues }) => {
  const [values, setValues] = useState(() => {
    return (initialValues && Object.keys(initialValues).length > 0) ? initialValues : DEFAULTS;
  });
  const [useSliders, setUseSliders] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setValues(prev => ({ ...prev, [name]: value === '' ? '' : parseFloat(value) }));
  };

  const getStatus = (name, val) => {
    if (val === '' || isNaN(val)) return 'normal';
    const range = RANGES[name];
    if (name === 'hdl_mg_dL') {
      if (val < 35) return 'high';
      if (val < 40) return 'elevated';
      return 'normal';
    }
    if (val >= range.high) return 'high';
    if (val > range.max) return 'elevated';
    return 'normal';
  };

  const renderInput = (name) => {
    const config = RANGES[name];
    const val = values[name];
    const status = getStatus(name, val);
    const wrapperClass = `input-wrapper ${status === 'elevated' ? 'elevated' : status === 'high' ? 'high' : ''}`;

    if (name === 'sex') {
      return (
        <div className="input-row" key={name}>
          <label className="input-label">{config.label}</label>
          <div className="input-wrapper">
            <select 
              name="sex" 
              value={val} 
              onChange={handleChange} 
              className="input-box" 
              style={{ width: '100%', textAlign: 'left', fontSize: '16px', border: 'none', background: 'transparent', outline: 'none' }}
            >
              <option value={1}>Male</option>
              <option value={2}>Female</option>
            </select>
          </div>
        </div>
      );
    }

    if (name === 'ancestry_proxy') {
      return (
        <div className="input-row" key={name}>
          <label className="input-label">{config.label}</label>
          <div className="input-wrapper">
            <select 
              name="ancestry_proxy" 
              value={val} 
              onChange={handleChange} 
              className="input-box" 
              style={{ width: '100%', textAlign: 'left', fontSize: '16px', border: 'none', background: 'transparent', outline: 'none' }}
            >
              <option value={3}>Non-Hispanic White</option>
              <option value={4}>Non-Hispanic Black</option>
              <option value={1}>Mexican American</option>
              <option value={2}>Other Hispanic</option>
              <option value={6}>Non-Hispanic Asian</option>
            </select>
          </div>
        </div>
      );
    }

    return (
      <div className="input-row" key={name}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <label className="input-label">{config.label}</label>
          {config.ref && <span className="input-ref" style={{ fontSize: '11px', color: '#888' }}>{config.ref}</span>}
        </div>
        <div className={wrapperClass}>
          <input 
            type="number" 
            name={name}
            value={val}
            onChange={handleChange}
            className="input-box"
            step={name === 'bmi' ? '0.1' : '1'}
          />
          <span className="input-unit">{config.unit}</span>
        </div>
        {useSliders && (
          <div style={{ marginTop: '8px', padding: '0 8px' }}>
            <input 
              type="range" 
              name={name}
              min={config.min}
              max={config.max}
              step={name === 'bmi' ? 0.1 : 1}
              value={val === '' ? config.min : val}
              onChange={handleChange}
              style={{ width: '100%', accentColor: 'var(--button-active)' }}
            />
          </div>
        )}
      </div>
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(values);
  };

  const homa_ir = ((values.fasting_glucose_mg_dL * values.fasting_insulin_uU_mL) / 405).toFixed(2);
  const tg_hdl = (values.triglycerides_mg_dL / values.hdl_mg_dL).toFixed(2);
  const ast_alt = (values.ast_U_L / values.alt_U_L).toFixed(2);

  const isFormComplete = Object.values(values).every(v => v !== '' && !isNaN(v));

  return (
    <div className="phase-1-container">
      <div className="phase-1-content">
        <div className="phase-1-header">
          <h1 className="phase-1-title" style={{ letterSpacing: '-0.03em', fontWeight: 800 }}>LMSIS</h1>
          <p className="phase-1-subtitle">Enter routine blood biomarker values to locate the patient's metabolic state.</p>
        </div>

        {/* Sliders vs Typing Toggle */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
          <label style={{ cursor: 'pointer', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', color: '#666', userSelect: 'none' }}>
            <input 
              type="checkbox" 
              checked={useSliders} 
              onChange={(e) => setUseSliders(e.target.checked)} 
              style={{ width: '16px', height: '16px', cursor: 'pointer' }}
            />
            Use Sliders for Exploration
          </label>
        </div>

        <div className="presets-panel" style={{ marginBottom: '36px', padding: '20px', backgroundColor: '#f5f4f0', borderRadius: '8px', border: '1px solid var(--input-border)' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#777', marginBottom: '12px', letterSpacing: '0.08em', fontWeight: 600 }}>Load Patient Profile Preset</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
            <button
              type="button"
              className="preset-btn"
              style={{
                padding: '12px',
                fontSize: '12px',
                textAlign: 'left',
                backgroundColor: '#ffffff',
                border: '1px solid var(--input-border)',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontFamily: 'var(--font-sans)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#fafafa'; e.currentTarget.style.borderColor = '#999'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#ffffff'; e.currentTarget.style.borderColor = 'var(--input-border)'; }}
              onClick={() => setValues({
                fasting_glucose_mg_dL: 94.0,
                fasting_insulin_uU_mL: 6.08,
                triglycerides_mg_dL: 54.5,
                hdl_mg_dL: 59.0,
                ast_U_L: 13.0,
                alt_U_L: 4.1,
                ggt_U_L: 16.0,
                bmi: 22.2,
                waist_cm: 78.8,
                platelets_1000_uL: 229.0,
                age: 30.0,
                sex: 2,
                ancestry_proxy: 4
              })}
            >
              <div style={{ fontWeight: 700, color: 'var(--territory-safe)' }}>MHNW</div>
              <div style={{ fontSize: '10px', color: '#777', marginTop: '2px' }}>Healthy Control</div>
            </button>
            <button
              type="button"
              className="preset-btn"
              style={{
                padding: '12px',
                fontSize: '12px',
                textAlign: 'left',
                backgroundColor: '#ffffff',
                border: '1px solid var(--input-border)',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontFamily: 'var(--font-sans)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#fafafa'; e.currentTarget.style.borderColor = '#999'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#ffffff'; e.currentTarget.style.borderColor = 'var(--input-border)'; }}
              onClick={() => setValues({
                fasting_glucose_mg_dL: 100.0,
                fasting_insulin_uU_mL: 6.69,
                triglycerides_mg_dL: 65.0,
                hdl_mg_dL: 59.0,
                ast_U_L: 13.0,
                alt_U_L: 4.1,
                ggt_U_L: 16.0,
                bmi: 21.4,
                waist_cm: 79.2,
                platelets_1000_uL: 221.0,
                age: 44.0,
                sex: 2,
                ancestry_proxy: 3
              })}
            >
              <div style={{ fontWeight: 700, color: 'var(--territory-ir)' }}>IR-Dominant</div>
              <div style={{ fontSize: '10px', color: '#777', marginTop: '2px' }}>Insulin Resistance</div>
            </button>
            <button
              type="button"
              className="preset-btn"
              style={{
                padding: '12px',
                fontSize: '12px',
                textAlign: 'left',
                backgroundColor: '#ffffff',
                border: '1px solid var(--input-border)',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontFamily: 'var(--font-sans)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#fafafa'; e.currentTarget.style.borderColor = '#999'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#ffffff'; e.currentTarget.style.borderColor = 'var(--input-border)'; }}
              onClick={() => setValues({
                fasting_glucose_mg_dL: 99.0,
                fasting_insulin_uU_mL: 5.45,
                triglycerides_mg_dL: 91.0,
                hdl_mg_dL: 54.0,
                ast_U_L: 17.0,
                alt_U_L: 4.2,
                ggt_U_L: 17.0,
                bmi: 23.5,
                waist_cm: 86.7,
                platelets_1000_uL: 225.0,
                age: 48.0,
                sex: 1,
                ancestry_proxy: 3
              })}
            >
              <div style={{ fontWeight: 700, color: 'var(--territory-steatosis)' }}>Steatotic</div>
              <div style={{ fontSize: '10px', color: '#777', marginTop: '2px' }}>Liver Fat Dominant</div>
            </button>
            <button
              type="button"
              className="preset-btn"
              style={{
                padding: '12px',
                fontSize: '12px',
                textAlign: 'left',
                backgroundColor: '#ffffff',
                border: '1px solid var(--input-border)',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontFamily: 'var(--font-sans)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#fafafa'; e.currentTarget.style.borderColor = '#999'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#ffffff'; e.currentTarget.style.borderColor = 'var(--input-border)'; }}
              onClick={() => setValues({
                fasting_glucose_mg_dL: 107.0,
                fasting_insulin_uU_mL: 6.63,
                triglycerides_mg_dL: 89.0,
                hdl_mg_dL: 60.0,
                ast_U_L: 18.0,
                alt_U_L: 4.1,
                ggt_U_L: 21.0,
                bmi: 23.0,
                waist_cm: 84.8,
                platelets_1000_uL: 207.0,
                age: 60.0,
                sex: 2,
                ancestry_proxy: 6
              })}
            >
              <div style={{ fontWeight: 700, color: 'var(--territory-dual)' }}>Dual-Burden</div>
              <div style={{ fontSize: '10px', color: '#777', marginTop: '2px' }}>Thin-Fat Phenotype</div>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <div className="form-group-title">Group A — Metabolic Core</div>
            {renderInput('fasting_glucose_mg_dL')}
            {renderInput('fasting_insulin_uU_mL')}
            <div className={`computed-card ${homa_ir >= 3.0 ? 'danger' : homa_ir >= 2.0 ? 'warning' : ''}`} style={{ transition: 'all 0.3s' }}>
              <div className="computed-row">
                <span className="computed-name">HOMA-IR</span>
                <span className="computed-value">{homa_ir}</span>
              </div>
              <div className="computed-desc">
                {homa_ir >= 3.0 ? 'Significantly elevated (≥3.0)' : homa_ir >= 2.0 ? 'Borderline elevated (2.0–3.0)' : 'Normal (<2.0)'}
              </div>
            </div>
          </div>

          <div className="form-group">
            <div className="form-group-title">Group B — Lipid Profile</div>
            {renderInput('triglycerides_mg_dL')}
            {renderInput('hdl_mg_dL')}
            <div className={`computed-card ${tg_hdl >= 3.0 ? 'danger' : tg_hdl >= 2.0 ? 'warning' : ''}`} style={{ transition: 'all 0.3s' }}>
              <div className="computed-row">
                <span className="computed-name">TG:HDL Ratio</span>
                <span className="computed-value">{tg_hdl}</span>
              </div>
              <div className="computed-desc">
                {tg_hdl >= 3.0 ? 'High cardiovascular risk (≥3.0)' : tg_hdl >= 2.0 ? 'Moderate cardiovascular risk (2.0–3.0)' : 'Optimal (<2.0)'}
              </div>
            </div>
          </div>

          <div className="form-group">
            <div className="form-group-title">Group C — Liver Markers</div>
            {renderInput('ast_U_L')}
            {renderInput('alt_U_L')}
            {renderInput('ggt_U_L')}
            <div className="computed-card" style={{ transition: 'all 0.3s' }}>
              <div className="computed-row">
                <span className="computed-name">AST:ALT Ratio</span>
                <span className="computed-value">{ast_alt}</span>
              </div>
              <div className="computed-desc">
                {ast_alt > 1.0 ? 'Advanced fibrosis proxy' : 'Standard'}
              </div>
            </div>
          </div>

          <div className="form-group">
            <div className="form-group-title">Group D — Body & Blood</div>
            {renderInput('bmi')}
            {renderInput('waist_cm')}
            {renderInput('platelets_1000_uL')}
          </div>

          <div className="form-group">
            <div className="form-group-title">Group E — Demographics</div>
            {renderInput('age')}
            {renderInput('sex')}
            {renderInput('ancestry_proxy')}
          </div>

          <button 
            type="submit" 
            className={`analyze-btn ${isFormComplete ? 'active' : ''} ${isSubmitting ? 'loading' : ''}`}
            disabled={!isFormComplete || isSubmitting}
            style={{ borderRadius: '6px', transition: 'all 0.3s', fontWeight: 600 }}
          >
            {isSubmitting ? 'Locating...' : 'Locate Metabolic State →'}
          </button>
        </form>
      </div>
    </div>
  );
};

