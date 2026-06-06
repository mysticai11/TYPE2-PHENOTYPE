import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

export function PathwayScreen({ geodesicData, patientData }) {
  if (!geodesicData || !patientData) return <div style={{padding: '24px'}}>Loading pathway data...</div>;

  const { euclidean_distance, geodesic_distance, geodesic_path, euclidean_path, interventions } = geodesicData;

  // Format data for chart
  const chartData = geodesic_path.map((pt, i) => ({
    step: i,
    geo_z1: pt[0],
    geo_z2: pt[1],
    euclid_z1: euclidean_path[i]?.[0],
    euclid_z2: euclidean_path[i]?.[1],
  }));

  const formatDelta = (val) => val > 0 ? `+${val}` : val;

  return (
    <div className="pathway-container" style={{ padding: '24px', display: 'flex', gap: '24px', height: '100%', overflow: 'hidden' }}>
      
      {/* Left panel: Chart */}
      <div className="chart-panel" style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', margin: '0 0 16px 0', fontSize: '24px' }}>Riemannian Pathway</h2>
        <div style={{ display: 'flex', gap: '24px', marginBottom: '24px', backgroundColor: 'var(--border)', padding: '16px', borderRadius: '8px' }}>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Euclidean Distance</div>
            <div style={{ fontSize: '20px', fontFamily: 'var(--font-mono)' }}>{euclidean_distance.toFixed(3)}</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Geodesic Distance</div>
            <div style={{ fontSize: '20px', fontFamily: 'var(--font-mono)', color: 'var(--territory-steatosis)' }}>{geodesic_distance.toFixed(3)}</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Curvature Penalty</div>
            <div style={{ fontSize: '20px', fontFamily: 'var(--font-mono)' }}>{((geodesic_distance/euclidean_distance - 1) * 100).toFixed(1)}%</div>
          </div>
        </div>
        
        <div style={{ flex: 1, minHeight: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2940" />
              <XAxis dataKey="geo_z1" type="number" name="Insulin Resistance (Z1)" domain={[-3, 3]} stroke="var(--text-muted)" />
              <YAxis dataKey="geo_z2" type="number" name="Hepatic Steatosis (Z2)" domain={[-3, 3]} stroke="var(--text-muted)" />
              <Tooltip contentStyle={{ backgroundColor: 'var(--bg-panel)', borderColor: 'var(--border)' }} />
              <Legend />
              <ReferenceLine x={0} stroke="var(--text-muted)" strokeDasharray="3 3" />
              <ReferenceLine y={0} stroke="var(--text-muted)" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="geo_z2" stroke="var(--territory-steatosis)" name="Geodesic Path" dot={false} strokeWidth={3} />
              <Line type="monotone" dataKey="euclid_z2" stroke="var(--text-muted)" name="Euclidean (Linear)" strokeDasharray="5 5" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Right panel: Interventions */}
      <div className="interventions-panel" style={{ flex: 1, backgroundColor: 'var(--bg-panel)', padding: '24px', borderRadius: '8px', overflowY: 'auto' }}>
        <h3 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '24px', borderBottom: '1px solid var(--border)', paddingBottom: '16px' }}>
          Stepwise Clinical Changes
        </h3>
        {interventions.map((step, i) => (
          <div key={i} style={{ marginBottom: '24px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Phase {i + 1} ({(step.progress * 100).toFixed(0)}% recovery)
            </div>
            {Object.entries(step.biomarker_deltas).map(([bm, delta]) => (
              <div key={bm} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '13px' }}>
                <span style={{ color: '#ccc' }}>{bm.replace(/_/g, ' ')}</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: delta < 0 ? 'var(--territory-safe)' : 'var(--territory-dual)' }}>
                  {formatDelta(delta)}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
