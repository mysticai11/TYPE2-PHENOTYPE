import { create } from 'zustand';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const useLmsisStore = create((set, get) => ({
  phase: 'input', // 'input', 'transition', 'map'
  activeTab: 'atlas', // 'atlas', 'pathway', 'equity', 'validation'
  researchMode: false,
  patientInputs: {},
  patientData: null,
  quadrantData: null,
  interventions: [],
  geodesicData: null,
  backendError: null,
  isSubmitting: false,

  setPhase: (phase) => set({ phase }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setResearchMode: (researchMode) => set({ researchMode }),
  setPatientInputs: (patientInputs) => set({ patientInputs }),
  setBackendError: (backendError) => set({ backendError }),

  resetStore: () => set({
    phase: 'input',
    activeTab: 'atlas',
    patientData: null,
    quadrantData: null,
    interventions: [],
    geodesicData: null,
    backendError: null,
    isSubmitting: false
  }),

  submitBiomarkers: async (values) => {
    set({ isSubmitting: true, backendError: null, patientInputs: values });
    try {
      // Parallel fetch from the FastAPI backend
      const [inferRes, cfRes, geoRes] = await Promise.all([
        axios.post(`${API_BASE}/infer`, values),
        axios.post(`${API_BASE}/quadrant_counterfactual`, values),
        axios.post(`${API_BASE}/geodesic_pathway`, values)
      ]);

      const inf = inferRes.data;
      const cf = cfRes.data;
      const geo = geoRes.data;

      // Map backend quadrant index to frontend key
      const qMap = { 0: 'mhnw', 1: 'ir_dominant', 2: 'steatosis_dominant', 3: 'dual_burden' };
      const qKey = qMap[inf.quadrant];

      const nCalibrationMap = { 0: 168, 1: 129, 2: 185, 3: 136 };

      const patientData = {
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
      };

      const quadrantData = {
        key: qKey,
        isDualBurden: qKey === 'dual_burden',
        percentile_ir: inf.ir_percentile,
        percentile_cap: inf.cap_percentile,
        n_calibration: nCalibrationMap[inf.quadrant] || 136,
        coverage_target: 0.90,
        achieved_coverage: inf.achieved_coverage,
      };

      // Assemble Interventions from quadrant counterfactual
      const mappedLevers = cf.levers.slice(0, 3).map(L => {
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

      set({
        patientData,
        quadrantData,
        interventions: mappedLevers,
        geodesicData: geo,
        phase: 'transition'
      });

      // Trigger cinematic transition
      setTimeout(() => {
        set({ phase: 'map' });
      }, 1200);

    } catch (err) {
      console.error(err);
      const msg = err?.response?.data?.detail || err?.message || 'Unknown error';
      set({
        backendError: `Backend error: ${msg}. Ensure the FastAPI server is running on port 8000.`
      });
    } finally {
      set({ isSubmitting: false });
    }
  }
}));
