import React from 'react';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

export const BottomBar = ({ onReEnter, researchMode, setResearchMode, patientId }) => {

  const handleExport = async () => {
    const element = document.getElementById('phase-2-export-wrapper');
    if (!element) return;
    
    // Simple PDF generation
    const canvas = await html2canvas(element, { backgroundColor: '#050810' });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'landscape',
      unit: 'px',
      format: [canvas.width, canvas.height]
    });
    pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
    pdf.save(`LMSIS_Clinical_Report_${patientId || 'Patient'}.pdf`);
  };

  return (
    <div className="bottom-bar">
      <div>
        <button className="bottom-btn" onClick={onReEnter}>
          ← Re-enter values
        </button>
        <span className="separator">|</span>
        <button className="bottom-btn" onClick={handleExport}>
          Export Clinical Report
        </button>
      </div>
      
      <div>
        <span>Model: DA-SS-iVAE v2.0 · NHANES 2017-18 · n=4,871</span>
        <span className="separator">|</span>
        <label style={{cursor: 'pointer'}}>
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
