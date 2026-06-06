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
  ancestry_proxy: 1
};

const RANGES = {
  fasting_glucose_mg_dL: { min: 70, max: 99, high: 126, label: "Fasting Glucose", unit: "mg/dL", ref: "Normal: 70–99" },
  fasting_insulin_uU_mL: { min: 2, max: 20, high: 30, label: "Fasting Insulin", unit: "μIU/mL", ref: "Normal: <20" },
  triglycerides_mg_dL: { min: 40, max: 150, high: 200, label: "Triglycerides", unit: "mg/dL", ref: "Normal: <150" },
  hdl_mg_dL: { min: 40, max: 100, high: 0, label: "HDL Cholesterol", unit: "mg/dL", ref: "Normal: >40" },
  ast_U_L: { min: 10, max: 40, high: 100, label: "AST", unit: "U/L", ref: "Normal: 10–40" },
  alt_U_L: { min: 5, max: 40, high: 100, label: "ALT", unit: "U/L", ref: "Normal: 5–40" },
  ggt_U_L: { min: 5, max: 50, high: 100, label: "GGT", unit: "U/L", ref: "Normal: 5–50" },
  bmi: { min: 18.5, max: 24.9, high: 30, label: "BMI", unit: "kg/m²", ref: "Normal: 18.5–24.9" },
  waist_cm: { min: 60, max: 90, high: 110, label: "Waist Circumference", unit: "cm", ref: "Normal: <90" },
  platelets_1000_uL: { min: 150, max: 450, high: 500, label: "Platelets", unit: "1000/μL", ref: "Normal: 150–450" },
  age: { min: 20, max: 80, high: 100, label: "Age", unit: "years", ref: "" },
  sex: { min: 1, max: 2, high: 3, label: "Sex (1=M, 2=F)", unit: "", ref: "" },
  ancestry_proxy: { min: 1, max: 3, high: 4, label: "Ancestry", unit: "code", ref: "" }
};

export const BiomarkerForm = ({ onSubmit, isSubmitting }) => {
  const [values, setValues] = useState(DEFAULTS);

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

    return (
      <div className="input-row" key={name}>
        <label className="input-label">{config.label}</label>
        <div className={wrapperClass}>
          <input 
            type="number" 
            name={name}
            value={val}
            onChange={handleChange}
            className="input-box"
          />
          <span className="input-unit">{config.unit}</span>
          <span className="input-ref">{config.ref}</span>
        </div>
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
          <h1 className="phase-1-title">LMSIS</h1>
          <p className="phase-1-subtitle">Enter routine blood biomarker values to locate the patient's metabolic state.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <div className="form-group-title">Group A — Metabolic Core</div>
            {renderInput('fasting_glucose_mg_dL')}
            {renderInput('fasting_insulin_uU_mL')}
            <div className={`computed-card ${homa_ir >= 3.0 ? 'danger' : homa_ir >= 2.0 ? 'warning' : ''}`}>
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
            <div className={`computed-card ${tg_hdl >= 3.0 ? 'danger' : tg_hdl >= 2.0 ? 'warning' : ''}`}>
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
            <div className="computed-card">
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
          >
            {isSubmitting ? 'Locating...' : 'Locate Metabolic State →'}
          </button>
        </form>
      </div>
    </div>
  );
};
