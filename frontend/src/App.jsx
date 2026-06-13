import React from 'react';
import { useLmsisStore } from './store/lmsis.store';
import { motion, AnimatePresence } from 'framer-motion';
import { BiomarkerForm } from './components/BiomarkerForm';
import { PhenotypeBanner } from './components/PhenotypeBanner';
import { AtlasScreen } from './components/AtlasScreen';
import { PathwayScreen } from './components/PathwayScreen';
import { EquityScreen } from './components/EquityScreen';
import { ValidationScreen } from './components/ValidationScreen';
import { CausalGraphPanel } from './components/CausalGraphPanel';
import { Map, Navigation, Users, Beaker, Network } from 'lucide-react';
import { BottomBar } from './components/BottomBar';

function App() {
  const {
    phase,
    activeTab,
    isSubmitting,
    researchMode,
    patientInputs,
    patientData,
    quadrantData,
    interventions,
    geodesicData,
    backendError,
    submitBiomarkers,
    resetStore,
    setActiveTab,
    setResearchMode,
    setBackendError
  } = useLmsisStore();

  return (
    <>
      {/* Backend Error Banner */}
      {backendError && (
        <div className="backend-error-banner">
          <span>⚠ {backendError}</span>
          <button onClick={() => setBackendError(null)} className="error-dismiss">✕</button>
        </div>
      )}

      <AnimatePresence mode="wait">
        {phase === 'input' && (
          <motion.div
            key="input-form"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.2, ease: 'easeOut' } }}
            style={{ width: '100%', height: '100%' }}
          >
            <BiomarkerForm onSubmit={submitBiomarkers} isSubmitting={isSubmitting} initialValues={patientInputs} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* The Cinematic Inkwell Background Transition */}
      {(phase === 'transition' || phase === 'map') && (
        <div 
          className={`inkwell-bg ${phase === 'transition' ? 'inkwell-active' : ''}`} 
          style={phase === 'map' ? { width: '300vw', height: '300vw', transition: 'width 0.5s ease-out, height 0.5s ease-out' } : {}}
        ></div>
      )}

      {phase === 'map' && (
        <div className="phase-2-container" id="phase-2-export-wrapper">
          <PhenotypeBanner quadrantKey={quadrantData?.key} />
          
          <div className="top-navigation" data-html2canvas-ignore="true">
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
            <button className={`tab-btn ${activeTab === 'causal' ? 'active' : ''}`} onClick={() => setActiveTab('causal')}>
              <Network size={16} /> Causal Network
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
            {activeTab === 'causal' && <CausalGraphPanel />}
          </div>

          <BottomBar 
            onReEnter={resetStore} 
            researchMode={researchMode} 
            setResearchMode={setResearchMode} 
          />
        </div>
      )}
    </>
  );
}

export default App;
