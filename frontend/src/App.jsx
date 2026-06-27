import React, { useState, useCallback } from 'react';
import IntakeScreen from './IntakeScreen';
import { MapScreen } from './MapScreen';
import { useStore, PRESETS } from './store';

// ── Transition Orchestrator ───────────────────────────────────────────────────
// animStage timeline:
//   0  = intake visible
//   1  = (0-200ms)  white form fades to 0%
//   2  = (200-500ms) dark fill expands from center
//   3  = (500-800ms) empty map appears (territories + population, no pin)
//   4  = (800-1000ms) patient pin drops and bounces
//   5  = (1000-1200ms) banner slides down, panel slides in, route draws

export default function App() {
  // phase: 'intake' | 'transitioning' | 'map'
  const [phase, setPhase] = useState('intake');
  const [animStage, setAnimStage] = useState(0);
  const [result, setResult] = useState(null);
  const [intakeOpacity, setIntakeOpacity] = useState(1);
  const [darkFillScale, setDarkFillScale] = useState(0);

  const { cyclePreset, activePresetIdx, inputs } = useStore();

  // Starts the 1.2s non-skippable transition sequence
  const startTransition = useCallback((inferResult) => {
    setResult(inferResult);
    setPhase('transitioning');

    // Stage 1: form fades (0-200ms)
    setAnimStage(1);
    setTimeout(() => setIntakeOpacity(0), 0);

    // Stage 2: dark fill from center (200-500ms)
    setTimeout(() => {
      setAnimStage(2);
      setDarkFillScale(1);
    }, 200);

    // Stage 3: empty map — territories + population (500-800ms)
    setTimeout(() => {
      setAnimStage(3);
      setPhase('map');
    }, 500);

    // Stage 4: pin drops (800-1000ms)
    setTimeout(() => {
      setAnimStage(4);
    }, 800);

    // Stage 5: banner + panel + route (1000-1200ms)
    setTimeout(() => {
      setAnimStage(5);
    }, 1000);
  }, []);

  const handleBack = useCallback(() => {
    setPhase('intake');
    setAnimStage(0);
    setIntakeOpacity(1);
    setDarkFillScale(0);
  }, []);

  const handleSwitch = useCallback(() => {
    const nextIdx = ((activePresetIdx ?? 0) + 1) % PRESETS.length;
    useStore.getState().applyPreset(nextIdx);
    useStore.getState().setActivePresetIdx(nextIdx);
    const nextResult = PRESETS[nextIdx];
    setResult(nextResult);
    // No transition on switch — just update result
  }, [activePresetIdx]);

  return (
    <>
      {/* ── Intake screen layer ── */}
      {(phase === 'intake' || phase === 'transitioning') && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            opacity: intakeOpacity,
            transition: 'opacity 0.2s linear',
            pointerEvents: phase === 'transitioning' ? 'none' : 'auto',
            zIndex: phase === 'transitioning' ? 20 : 10,
          }}
        >
          <IntakeScreen onSubmit={startTransition} />
        </div>
      )}

      {/* ── Dark radial fill overlay (stage 2) ── */}
      {phase === 'transitioning' && animStage >= 2 && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: '#050810',
            zIndex: 30,
            transform: `scale(${darkFillScale})`,
            transformOrigin: 'center center',
            borderRadius: darkFillScale < 1 ? '50%' : '0',
            transition: 'transform 0.3s cubic-bezier(0.4,0,0.2,1), border-radius 0.3s',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* ── Map screen layer ── */}
      {(phase === 'map' || (phase === 'transitioning' && animStage >= 3)) && result && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            opacity: animStage >= 3 ? 1 : 0,
            transition: 'opacity 0.3s linear',
            zIndex: 40,
          }}
        >
          <MapScreen
            result={result}
            animStage={animStage}
            onBack={handleBack}
            onSwitch={handleSwitch}
          />
        </div>
      )}
    </>
  );
}
