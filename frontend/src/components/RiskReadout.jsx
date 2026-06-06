import React from 'react';

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
