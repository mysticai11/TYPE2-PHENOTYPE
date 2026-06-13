import React, { useState } from 'react';
import { useLmsisStore } from '../store/lmsis.store';

export const BottomBar = ({ onReEnter, researchMode, setResearchMode, patientId }) => {
  const patientData = useLmsisStore(s => s.patientData);
  const interventions = useLmsisStore(s => s.interventions);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    if (!patientData) return;
    setIsExporting(true);
    try {
      const response = await fetch('http://localhost:8000/export_pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_data: patientData, interventions })
      });
      if (!response.ok) throw new Error('PDF export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `LMSIS_Clinical_Report_${patientId || 'Patient'}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('Failed to export PDF.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="bottom-bar">
      <div data-html2canvas-ignore="true">
        <button className="bottom-btn" onClick={onReEnter}>
          ← Re-enter values
        </button>
        <span className="separator">|</span>
        <button className="bottom-btn" onClick={handleExport} disabled={isExporting}>
          {isExporting ? 'Generating PDF...' : 'Export Clinical Report'}
        </button>
      </div>
      
      <div>
        <span>Model: DA-SS-iVAE v2.0 · NHANES 2017-18 · n=4,871</span>
        <span className="separator" data-html2canvas-ignore="true">|</span>
        <label style={{cursor: 'pointer'}} data-html2canvas-ignore="true">
          <input 
            type="checkbox" 
            checked={researchMode} 
            onChange={(e) => setResearchMode(e.target.checked)} 
            style={{marginRight: '6px', verticalAlign: 'middle'}}
          />
          Research View
        </label>
      </div>
    </div>
  );
};
