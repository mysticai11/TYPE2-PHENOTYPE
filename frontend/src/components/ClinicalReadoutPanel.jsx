import React from 'react';

export const ClinicalReadoutPanel = ({ patientData, quadrantData, interventions, researchMode }) => {
  if (!patientData || !quadrantData) return null;

  const { z1, z2, pred_homa_ir, pred_cap, risk_score, coverage_lb, coverage_ub, recon_mse, in_distribution } = patientData;
  const { isDualBurden, percentile_ir, percentile_cap, n_calibration, coverage_target, achieved_coverage } = quadrantData;

  const getSteatosisGrade = (cap) => {
    if (cap < 248) return 'S0 (Normal)';
    if (cap < 268) return 'S1 (Mild steatosis)';
    if (cap < 280) return 'S2 (Moderate steatosis)';
    return 'S3 (Severe steatosis)';
  };

  const getRiskZone = (score) => {
    if (score < 0.40) return { name: 'Safe', color: 'var(--territory-safe)' };
    if (score < 0.65) return { name: 'Caution', color: 'var(--amber)' };
    return { name: 'Danger', color: 'var(--crimson)' };
  };

  const zone = getRiskZone(risk_score);
  
  // Calculate arc mapping for gauge
  // Needle angle from -90 to +90
  const needleAngle = (risk_score * 180) - 90;
  const arcStart = (coverage_lb * 180) - 90;
  const arcEnd = (coverage_ub * 180) - 90;
  const arcWidth = Math.max(2, arcEnd - arcStart);

  return (
    <div className="right-panel">
      
      {/* SECTION 1: Location Card */}
      <div className="panel-section">
        <div className="section-title">Your Metabolic Location</div>
        
        <div className="percentile-row">
          <div className="percentile-label">
            <span>Insulin Resistance</span>
            <span style={{fontFamily: 'var(--font-mono)'}}>{percentile_ir}th percentile</span>
          </div>
          <div className="percentile-track">
            <div className="percentile-fill" style={{width: `${percentile_ir}%`}}></div>
          </div>
        </div>

        <div className="percentile-row">
          <div className="percentile-label">
            <span>Liver Fat Risk</span>
            <span style={{fontFamily: 'var(--font-mono)'}}>{percentile_cap}th percentile</span>
          </div>
          <div className="percentile-track">
            <div className="percentile-fill" style={{width: `${percentile_cap}%`}}></div>
          </div>
        </div>

        <div className="clinical-pred" style={{marginTop: '24px'}}>
          <span>Predicted HOMA-IR</span>
          <span>{pred_homa_ir.toFixed(1)}</span>
        </div>
        <div className="clinical-pred">
          <span>Predicted Liver Fat</span>
          <span>{pred_cap.toFixed(0)} dB/m</span>
        </div>
        <div style={{fontSize: '11px', color: 'var(--text-muted)', textAlign: 'right', marginTop: '4px'}}>
          ({getSteatosisGrade(pred_cap)})
        </div>
      </div>

      {/* SECTION 2: Safety Gauge */}
      <div className="panel-section">
        <div className="section-title">Safety Gauge</div>
        
        <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', padding: '0 16px'}}>
          <span>Safe</span>
          <span>Caution</span>
          <span>Danger</span>
        </div>
        
        <div className="speedometer">
          {/* Gauge Background SVG */}
          <svg width="100%" height="80" viewBox="0 0 200 100" preserveAspectRatio="none">
            {/* Zones */}
            <path d="M 10 90 A 80 80 0 0 1 70 20" fill="none" stroke="var(--territory-safe)" strokeWidth="4" opacity="0.3"/>
            <path d="M 70 20 A 80 80 0 0 1 130 20" fill="none" stroke="var(--amber)" strokeWidth="4" opacity="0.3"/>
            <path d="M 130 20 A 80 80 0 0 1 190 90" fill="none" stroke="var(--crimson)" strokeWidth="4" opacity="0.3"/>
            
            {/* Confidence Arc */}
            <g transform="translate(100, 90)">
              <path 
                d={`M ${-80 * Math.cos(arcStart * Math.PI / 180)} ${80 * Math.sin(arcStart * Math.PI / 180)} A 80 80 0 0 1 ${-80 * Math.cos(arcEnd * Math.PI / 180)} ${80 * Math.sin(arcEnd * Math.PI / 180)}`}
                fill="none" stroke={zone.color} strokeWidth="8"
              />
              {/* Needle */}
              <line 
                x1="0" y1="0" 
                x2={-75 * Math.cos(needleAngle * Math.PI / 180)} 
                y2={80 * Math.sin(needleAngle * Math.PI / 180)} 
                stroke="var(--white-data)" strokeWidth="2"
              />
              <circle cx="0" cy="0" r="4" fill="var(--white-data)" />
            </g>
          </svg>
          
          <div style={{textAlign: 'center', marginTop: '-10px'}}>
            <div style={{fontSize: '13px', color: 'var(--text-muted)'}}>Risk Score: <span style={{color: 'var(--white-data)', fontFamily: 'var(--font-mono)'}}>{risk_score.toFixed(2)}</span></div>
            <div style={{fontSize: '11px', fontFamily: 'var(--font-mono)', marginTop: '4px'}}>
              [ {coverage_lb.toFixed(2)} ────── {coverage_ub.toFixed(2)} ]
            </div>
            <div style={{fontSize: '10px', color: 'var(--text-muted)'}}>90% confidence range</div>
          </div>
        </div>
      </div>

      {/* SECTION 3: Intervention Targets */}
      <div className="panel-section">
        <div className="section-title">To Reach Safety — Top Levers</div>
        
        {interventions && interventions.length > 0 ? (
          interventions.map((inv, idx) => (
            <div key={idx} className="intervention-row">
              <div className="intervention-header">
                <span style={{color: 'var(--text-muted)'}}>{idx+1}. {inv.name}</span>
                <span className="intervention-change">{inv.diff < 0 ? '↓' : '↑'} {Math.abs(inv.diff)} {inv.unit}</span>
              </div>
              <div className="intervention-bars">
                <div className="intervention-bar current" style={{width: `${Math.min(100, (inv.current / inv.maxScale) * 100)}%`}}></div>
                <div className="intervention-bar target" style={{width: `${Math.min(100, (inv.target / inv.maxScale) * 100)}%`}}></div>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--text-muted)'}}>
                <span>current</span>
                <span>target</span>
              </div>
            </div>
          ))
        ) : (
          <div style={{fontSize: '13px', color: 'var(--text-muted)'}}>Patient is in the safe zone. No acute metabolic interventions required.</div>
        )}
        <div style={{ marginTop: '16px', fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4', fontStyle: 'italic' }}>
          *Clinical Simulation: The levers above project the biomarker changes required to transition the patient's latent metabolic coordinate into the safe zone, based on the model's learned representation. This is a model finding, not a direct clinical prescription.
        </div>
      </div>

      {/* SECTION 4: Model Confidence */}
      <div className="panel-section" style={{borderBottom: 'none'}}>
        <div className="section-title">Model Confidence</div>
        
        <div className="conf-row">
          <span>Within training range</span>
          <span className="conf-val" style={{color: in_distribution ? 'var(--territory-safe)' : 'var(--crimson)'}}>
            {in_distribution ? '✓' : '⚠ Out of Distribution'}
          </span>
        </div>
        <div className="conf-row">
          <span>Calibration stratum</span>
          <span className="conf-val" style={{fontFamily: 'var(--font-sans)', color: isDualBurden ? 'var(--territory-dual)' : 'var(--white-data)'}}>
            {isDualBurden ? 'Dual-Burden' : 'Standard'}
          </span>
        </div>
        <div className="conf-row">
          <span>Coverage guarantee</span>
          <span className="conf-val">{(coverage_target * 100).toFixed(0)}%</span>
        </div>
        <div className="conf-row">
          <span>Similar patients in data</span>
          <span className="conf-val">{n_calibration || 219}</span>
        </div>

        {researchMode && (
          <div style={{marginTop: '24px', paddingTop: '16px', borderTop: '1px dashed var(--border)'}}>
            <div className="section-title">Research Telemetry</div>
            <div className="conf-row"><span>Z1 (IR)</span><span className="conf-val">{z1.toFixed(3)}</span></div>
            <div className="conf-row"><span>Z2 (Steatosis)</span><span className="conf-val">{z2.toFixed(3)}</span></div>
            <div className="conf-row"><span>Recon MSE</span><span className="conf-val">{recon_mse.toFixed(5)}</span></div>
            <div className="conf-row"><span>Achieved Coverage</span><span className="conf-val">{(achieved_coverage * 100).toFixed(1)}%</span></div>
          </div>
        )}
      </div>
      
    </div>
  );
};
