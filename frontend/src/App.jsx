import React, { useState } from 'react';
import axios from 'axios';
import { BiomarkerForm } from './components/BiomarkerForm';
import { PhenotypeBanner } from './components/PhenotypeBanner';
import { ClinicalMap } from './components/ClinicalMap';
import { ClinicalReadoutPanel } from './components/ClinicalReadoutPanel';
import { AtlasScreen } from './components/AtlasScreen';
import { PathwayScreen } from './components/PathwayScreen';
import { EquityScreen } from './components/EquityScreen';
import { ValidationScreen } from './components/ValidationScreen';
import { FileDown, Beaker, Map, Navigation, Users } from 'lucide-react';
import { BottomBar } from './components/BottomBar';

const API_BASE = 'http://localhost:8000';

function App() {
  const [phase, setPhase] = useState('input'); // 'input', 'transition', 'map'
  const [activeTab, setActiveTab] = useState('atlas'); // 'atlas', 'pathway', 'equity', 'validation'
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [researchMode, setResearchMode] = useState(false);
  
  const [patientData, setPatientData] = useState(null);
  const [quadrantData, setQuadrantData] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [geodesicData, setGeodesicData] = useState(null);

  const handleSubmit = async (values) => {
    setIsSubmitting(true);
    try {
      // Parallel fetch
      const [inferRes, cfRes, geoRes] = await Promise.all([
        axios.post(`${API_BASE}/infer`, values),
        axios.post(`${API_BASE}/quadrant_counterfactual`, values),
        axios.post(`${API_BASE}/geodesic_pathway`, values)
      ]);

      const inf = inferRes.data;
      const cf = cfRes.data;
      const geo = geoRes.data;
      setGeodesicData(geo);

      // Determine Quadrant Key based on backend 'quadrant' index
      const qMap = {
        0: 'mhnw',
        1: 'ir_dominant',
        2: 'steatosis_dominant',
        3: 'dual_burden'
      };
      const qKey = qMap[inf.quadrant];

      // Assemble Data
      setPatientData({
        z1: inf.z1,
        z2: inf.z2,
        pred_homa_ir: inf.homa_ir,
        pred_cap: 220 + (inf.z2 * 30), // Approx CAP translation for display
        risk_score: inf.ir_risk,
        coverage_lb: inf.ir_risk_lower,
        coverage_ub: inf.ir_risk_upper
      });

      setQuadrantData({
        key: qKey,
        isDualBurden: qKey === 'dual_burden',
        percentile_ir: Math.max(1, Math.min(99, Math.round(50 + (inf.z1 * 20)))), // Synthetic percentile map
        percentile_cap: Math.max(1, Math.min(99, Math.round(50 + (inf.z2 * 20)))),
        n_calibration: qKey === 'dual_burden' ? 246 : 171,
        coverage_target: 0.90
      });

      // Assemble Interventions
      const mappedLevers = cf.levers.slice(0, 3).map(L => {
        const isDecrease = L.delta_raw < 0;
        const current = values[L.biomarker] || 0;
        return {
          name: L.biomarker.replace('_mg_dL', '').replace('_U_L', '').replace('_uU_mL', '').replace(/_/g, ' ').toUpperCase(),
          diff: parseFloat(L.delta_raw.toFixed(1)),
          unit: L.unit,
          current: current,
          target: current + L.delta_raw,
          maxScale: current * 1.5 // for proportional bar rendering
        };
      });
      setInterventions(mappedLevers);

      // Trigger cinematic transition
      setPhase('transition');
      setTimeout(() => {
        setPhase('map');
      }, 1200);

    } catch (err) {
      console.error(err);
      alert("Error reaching LMSIS backend.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReEnter = () => {
    setPhase('input');
  };

  return (
    <>
      {phase === 'input' && (
        <BiomarkerForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
      )}

      {/* The Cinematic Inkwell */}
      {(phase === 'transition' || phase === 'map') && (
        <div className={`inkwell-bg ${phase === 'transition' ? 'inkwell-active' : ''}`} style={phase === 'map' ? {width: '300vw', height: '300vw'} : {}}></div>
      )}

      {phase === 'map' && (
        <div className="phase-2-container" id="phase-2-export-wrapper">
          <PhenotypeBanner quadrantKey={quadrantData?.key} />
          
          <div className="top-navigation">
            <button className={`tab-btn ${activeTab === 'atlas' ? 'active' : ''}`} onClick={() => setActiveTab('atlas')}>
              <Map size={16} /> Metabolic Atlas
            </button>
            <button className={`tab-btn ${activeTab === 'pathway' ? 'active' : ''}`} onClick={() => setActiveTab('pathway')}>
              <Navigation size={16} /> Geodesic Pathway
            </button>
            <button className={`tab-btn ${activeTab === 'equity' ? 'active' : ''}`} onClick={() => setActiveTab('equity')}>
              <Users size={16} /> Ancestral Equity
            </button>
            <button className={`tab-btn ${activeTab === 'validation' ? 'active' : ''}`} onClick={() => setActiveTab('validation')}>
              <Beaker size={16} /> Validation
            </button>
          </div>

          <div className="tab-content-container">
            {activeTab === 'atlas' && (
              <AtlasScreen 
                patientData={patientData} 
                quadrantData={quadrantData} 
                interventions={interventions} 
                researchMode={researchMode} 
              />
            )}
            {activeTab === 'pathway' && <PathwayScreen geodesicData={geodesicData} patientData={patientData} />}
            {activeTab === 'equity' && <EquityScreen patientData={patientData} />}
            {activeTab === 'validation' && <ValidationScreen />}
          </div>

          <BottomBar 
            onReEnter={handleReEnter} 
            researchMode={researchMode} 
            setResearchMode={setResearchMode} 
          />
        </div>
      )}
    </>
  );
}

export default App;
