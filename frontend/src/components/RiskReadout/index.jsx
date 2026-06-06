export function RiskReadout({ result }) {
  if (!result) return null;

  return (
    <div className="risk-readout card">
      <h3>Inference Results</h3>
      <p><strong>IR Risk:</strong> {(result.ir_risk * 100).toFixed(1)}%</p>
      <p><strong>90% Confidence Interval:</strong> [{(result.ir_risk_lower * 100).toFixed(1)}% - {(result.ir_risk_upper * 100).toFixed(1)}%]</p>
      <p><strong>z₁ (IR Axis):</strong> {result.z1} (σ={result.z1_sigma})</p>
      <p><strong>z₂ (Lipid Axis):</strong> {result.z2} (σ={result.z2_sigma})</p>
      {result.thin_fat_flag && (
        <div className="alert-thin-fat" style={{ background: '#ffcccc', padding: '10px', borderRadius: '5px', marginTop: '10px', color: '#b30000' }}>
          <strong>⚠️ Thin-Fat Phenotype Detected!</strong> Patient has normal BMI but high metabolic risk.
        </div>
      )}
    </div>
  );
}
