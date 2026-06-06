import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

export function EquityScreen({ patientData }) {
  // Hardcoded results from ancestry_bias.py and conformal_ancestry.py for the presentation
  
  const thresholdData = [
    { name: 'Universal Clinical Cutoff', threshold: 2.5, fill: '#666' },
    { name: 'Non-Hispanic White', threshold: 1.75, ci_low: 1.57, ci_high: 1.96, fill: '#00c47d' },
    { name: 'Non-Hispanic Black', threshold: 1.56, ci_low: 0.22, ci_high: 2.18, fill: '#f5a623' },
    { name: 'Non-Hispanic Asian', threshold: 1.30, ci_low: 0.65, ci_high: 1.51, fill: '#3d8ef8' },
  ];

  const coverageData = [
    { name: 'Non-Hispanic White', marginal: 84.6, mondrian: 92.3 },
    { name: 'Non-Hispanic Black', marginal: 90.9, mondrian: 90.9 },
    { name: 'Non-Hispanic Asian', marginal: 92.2, mondrian: 92.2 },
  ];

  return (
    <div className="equity-container" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ fontFamily: 'var(--font-display)', margin: 0, fontSize: '28px' }}>Ancestral Threshold Bias & Equity</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '14px', maxWidth: '800px', lineHeight: '1.6' }}>
        The universal HOMA-IR clinical threshold of 2.5 systematically discriminates against certain demographics. 
        Because the joint distribution of biomarkers varies by ancestry, applying a single threshold causes massive 
        inequities in risk detection. This dashboard visualizes the "Fair" HOMA-IR threshold for each group—the exact 
        value at which they cross the mathematical risk boundary $\tau_1$.
      </p>

      <div style={{ display: 'flex', gap: '24px', height: '350px' }}>
        <div style={{ flex: 1, backgroundColor: 'var(--bg-panel)', padding: '20px', borderRadius: '8px' }}>
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-primary)', marginBottom: '16px' }}>True Risk Threshold by Ancestry</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={thresholdData} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2940" horizontal={false} />
              <XAxis type="number" domain={[0, 3]} stroke="var(--text-muted)" />
              <YAxis dataKey="name" type="category" stroke="var(--text-muted)" width={120} tick={{fontSize: 12}} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--bg-panel)', borderColor: 'var(--border)' }} />
              <ReferenceLine x={2.5} stroke="#e8394a" strokeDasharray="5 5" label={{ position: 'top', value: 'Current Clinical Cutoff (2.5)', fill: '#e8394a', fontSize: 12 }} />
              <Bar dataKey="threshold" fill="#8884d8" radius={[0, 4, 4, 0]}>
                {thresholdData.map((entry, index) => (
                  <cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{ width: '300px', backgroundColor: 'var(--bg-panel)', padding: '20px', borderRadius: '8px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>Critical Finding</div>
          <div style={{ fontSize: '36px', fontFamily: 'var(--font-display)', color: 'var(--territory-dual)', marginBottom: '16px' }}>40.9%</div>
          <div style={{ fontSize: '14px', lineHeight: '1.5', color: 'var(--text-primary)' }}>
            of Non-Hispanic Asian Americans in this normal-BMI cohort are misclassified as insulin-sensitive by the universal threshold. Their true risk threshold is ~1.30.
          </div>
        </div>
      </div>

      <div style={{ flex: 1, backgroundColor: 'var(--bg-panel)', padding: '20px', borderRadius: '8px' }}>
        <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-primary)', marginBottom: '16px' }}>Mondrian Conformal Coverage Restoration</h3>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '24px' }}>
          Standard Marginal Conformal Prediction fails to protect the Non-Hispanic White subgroup (coverage drops to 84.6% despite a 90% target). 
          Mondrian Conformal Prediction perfectly restores coverage across all ancestral lines.
        </p>
        <div style={{ height: '250px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={coverageData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2940" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-muted)" />
              <YAxis domain={[70, 100]} stroke="var(--text-muted)" />
              <Tooltip contentStyle={{ backgroundColor: 'var(--bg-panel)', borderColor: 'var(--border)' }} />
              <Legend />
              <ReferenceLine y={90} stroke="var(--territory-safe)" strokeDasharray="3 3" label={{ position: 'top', value: 'Target Coverage (90%)', fill: 'var(--territory-safe)', fontSize: 12 }} />
              <Bar dataKey="marginal" name="Marginal Coverage %" fill="#4a6380" radius={[4, 4, 0, 0]} />
              <Bar dataKey="mondrian" name="Mondrian Coverage %" fill="var(--territory-steatosis)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
