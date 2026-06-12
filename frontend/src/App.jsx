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
  const [backendError, setBackendError] = useState(null);

  const handleSubmit = async (values) => {
    setIsSubmitting(true);
    setBackendError(null);
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

      // Quadrant key from backend quadrant index
      const qMap = { 0: 'mhnw', 1: 'ir_dominant', 2: 'steatosis_dominant', 3: 'dual_burden' };
      const qKey = qMap[inf.quadrant];

      // Use real anchor predictions from backend (not linear approximation)
      setPatientData({
        z1: inf.z1,
        z2: inf.z2,
        z1_sigma: inf.z1_sigma,
        z2_sigma: inf.z2_sigma,
        pred_homa_ir: inf.pred_homa_ir,
        pred_cap: inf.pred_cap_score,
        risk_score: inf.ir_risk,
        coverage_lb: inf.ir_risk_lower,
        coverage_ub: inf.ir_risk_upper,
        recon_mse: inf.recon_mse,
        in_distribution: inf.in_distribution,
      });

      const nCalibrationMap = { 0: 168, 1: 129, 2: 185, 3: 136 };

      setQuadrantData({
        key: qKey,
        isDualBurden: qKey === 'dual_burden',
        percentile_ir: inf.ir_percentile,    // real cohort percentile rank
        percentile_cap: inf.cap_percentile,  // real cohort percentile rank
        n_calibration: nCalibrationMap[inf.quadrant] || 136,
        coverage_target: 0.90,
        achieved_coverage: inf.achieved_coverage,
      });

      // Assemble Interventions from quadrant counterfactual
      const mappedLevers = cf.levers.slice(0, 3).map(L => {
        const isDecrease = L.delta_raw < 0;
        const current = values[L.biomarker] || 0;
        return {
          name: L.biomarker.replace('_mg_dL','').replace('_U_L','').replace('_uU_mL','').replace(/_/g,' ').toUpperCase(),
          diff: parseFloat(L.delta_raw.toFixed(1)),
          unit: L.unit,
          current: current,
          target: current + L.delta_raw,
          maxScale: current * 1.5
        };
      });
      setInterventions(mappedLevers);

      // Trigger cinematic transition
      setPhase('transition');
      setTimeout(() => { setPhase('map'); }, 1200);

    } catch (err) {
      console.error(err);
      const msg = err?.response?.data?.detail || err?.message || 'Unknown error';
      setBackendError(`Backend error: ${msg}. Ensure the FastAPI server is running on port 8000.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReEnter = () => {
    setPhase('input');
    setBackendError(null);
  };

  return (
    <>
      {/* Backend Error Banner */}
      {backendError && (
        <div className="backend-error-banner">
          <span>⚠ {backendError}</span>
          <button onClick={() => setBackendError(null)} className="error-dismiss">✕</button>
        </div>
      )}
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
                geodesicPath={geodesicData?.geodesic_path}
                geodesicInterventions={geodesicData?.interventions}
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
