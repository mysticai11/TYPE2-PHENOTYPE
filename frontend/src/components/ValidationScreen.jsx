import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';

export function ValidationScreen() {
  const benchmarkData = [
    { name: 'DA-SS-iVAE (Z2)', rho: 0.576 },
    { name: 'FLI', rho: 0.447 },
    { name: 'TyG Index', rho: 0.358 },
    { name: 'HSI', rho: 0.111 },
    { name: 'NAFLD-LFS', rho: -0.069 },
  ];

  const drugData = [
    { name: 'Statin', effect: -0.869, axis: 'Z2 (Steatosis)', pval: 'p < 1e-21' },
    { name: 'Fibrate', effect: -1.000, axis: 'Z2 (Steatosis)', pval: 'p < 1e-10' },
    { name: 'Metformin', effect: -1.000, axis: 'Z1 (IR)', pval: 'p < 1e-21' },
  ];

  return (
    <div className="validation-container" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ fontFamily: 'var(--font-display)', margin: 0, fontSize: '28px' }}>Scientific Validation</h2>
      
      <div style={{ display: 'flex', gap: '24px' }}>
        
        {/* Left: Benchmark Demolition */}
        <div style={{ flex: 1, backgroundColor: 'var(--bg-panel)', padding: '20px', borderRadius: '8px' }}>
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-primary)', marginBottom: '8px' }}>Benchmark Demolition</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '24px' }}>
            Predicting FibroScan CAP (Liver Fat) in Normal-BMI Adults. 
            NAFLD-LFS actively inverts risk rankings in this population.
          </p>
          <div style={{ height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={benchmarkData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c2940" horizontal={false} />
                <XAxis type="number" domain={[-0.2, 0.7]} stroke="var(--text-muted)" tickFormatter={(v) => v.toFixed(1)} />
                <YAxis dataKey="name" type="category" stroke="var(--text-muted)" width={100} tick={{fontSize: 12}} />
                <Tooltip contentStyle={{ backgroundColor: 'var(--bg-panel)', borderColor: 'var(--border)' }} cursor={{fill: 'rgba(255,255,255,0.05)'}} />
                <ReferenceLine x={0} stroke="#4a6380" />
                <Bar dataKey="rho" name="Spearman Correlation (ρ)">
                  {benchmarkData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.rho < 0 ? '#e8394a' : (entry.name.includes('DA-SS-iVAE') ? 'var(--territory-steatosis)' : '#4a6380')} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Pharmacological Double Dissociation */}
        <div style={{ flex: 1, backgroundColor: 'var(--bg-panel)', padding: '20px', borderRadius: '8px' }}>
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-primary)', marginBottom: '8px' }}>Pharmacological Double Dissociation</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '24px' }}>
            Causal confirmation of the latent axes via Propensity Score Matched drug cohorts.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {drugData.map((drug, i) => (
              <div key={i} style={{ padding: '16px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--white-data)' }}>{drug.name}</span>
                  <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{drug.pval}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Primary Action:</span>
                  <span style={{ color: drug.axis.includes('Z2') ? 'var(--territory-steatosis)' : 'var(--territory-ir)' }}>
                    Massive drop in {drug.axis}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginTop: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Off-Target Action:</span>
                  <span style={{ color: 'var(--text-muted)' }}>Identical to control (p {'>'} 0.05)</span>
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '24px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            * This proves Z1 and Z2 are not arbitrary rotations, but discrete, pharmacologically responsive biological vectors.
          </div>
        </div>

      </div>
    </div>
  );
}
