import React from 'react';
import { ClinicalMap } from './ClinicalMap';
import { ClinicalReadoutPanel } from './ClinicalReadoutPanel';

export function AtlasScreen({ patientData, quadrantData, interventions, geodesicPath, geodesicInterventions, researchMode }) {
  return (
    <div className="main-layout">
      <ClinicalMap 
        z1={patientData?.z1} 
        z2={patientData?.z2} 
        quadrantKey={quadrantData?.key}
        researchMode={researchMode}
        isSafe={quadrantData?.key === 'mhnw'}
        geodesicPath={geodesicPath}
        interventions={geodesicInterventions}
      />
      <ClinicalReadoutPanel 
        patientData={patientData}
        quadrantData={quadrantData}
        interventions={interventions}
        researchMode={researchMode}
      />
    </div>
  );
}
