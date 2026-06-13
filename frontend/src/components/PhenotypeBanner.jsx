import React from 'react';

const PHENOTYPES = {
  mhnw: {
    title: "✓ METABOLICALLY HEALTHY",
    desc: "Normal IR and Liver Function",
    color: "var(--territory-safe)",
    pulse: false
  },
  ir_dominant: {
    title: "▲ INSULIN RESISTANT PHENOTYPE",
    desc: "Elevated IR without Steatosis",
    color: "var(--territory-ir)",
    pulse: false
  },
  steatosis_dominant: {
    title: "▲ STEATOSIS-DOMINANT PHENOTYPE",
    desc: "Isolated Liver Fat Accumulation",
    color: "var(--territory-steatosis)",
    pulse: false
  },
  dual_burden: {
    title: "⬤ DUAL-BURDEN PHENOTYPE",
    desc: "Thin-Fat / MUHNW · Highest Risk",
    color: "var(--territory-dual)",
    pulse: true
  }
};

export const PhenotypeBanner = ({ quadrantKey }) => {
  if (!quadrantKey) return null;
  const data = PHENOTYPES[quadrantKey] || PHENOTYPES.mhnw;

  return (
    <div className="phenotype-banner" style={{ backgroundColor: data.color }}>
      <span className={`banner-dot ${data.pulse ? 'pulse' : ''}`}>
        {data.title.charAt(0)}
      </span>
      {data.title.slice(2)} <span style={{opacity: 0.7, margin: '0 16px'}}>·</span> <span style={{opacity: 0.85, textTransform: 'none', fontFamily: 'var(--font-sans)', fontSize: '18px'}}>{data.desc}</span>
    </div>
  );
};
