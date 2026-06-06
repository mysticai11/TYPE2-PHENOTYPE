import { useState } from 'react';

export function CounterfactualControl({ onSimulate, loading, counterfactualResult, disabled }) {
  const [targetHoma, setTargetHoma] = useState(3.5);

  return (
    <div className="cf-control card">
      <h3>Counterfactual Simulation</h3>
      <div className="input-group">
        <label>Target HOMA-IR</label>
        <input 
          type="number" 
          step="0.1" 
          value={targetHoma} 
          onChange={(e) => setTargetHoma(e.target.value)} 
          disabled={disabled}
        />
      </div>
      <button onClick={() => onSimulate(targetHoma)} disabled={loading || disabled} className="submit-btn" style={{marginTop: '10px'}}>
        {loading ? "Simulating..." : "Show Shift"}
      </button>

      {counterfactualResult && (
        <div className="cf-result" style={{marginTop: '15px', padding: '10px', background: '#e6f7ff', borderRadius: '5px'}}>
          <p><strong>z₁ Counterfactual:</strong> {counterfactualResult.z1_counterfactual}</p>
          <p><strong>Δz₁ Shift:</strong> {counterfactualResult.delta_z1}</p>
        </div>
      )}
    </div>
  );
}
