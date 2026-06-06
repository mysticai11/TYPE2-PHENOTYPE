import React, { useRef, useEffect } from 'react';

export const LatentSpaceCanvas = ({ patient, counterfactual }) => {
  const svgRef = useRef();

  // Canvas bounds (Z space usually ranges roughly -3 to 3)
  const Z_MIN = -3.5;
  const Z_MAX = 3.5;

  const mapToSvg = (z1, z2, width, height) => {
    const x = ((z1 - Z_MIN) / (Z_MAX - Z_MIN)) * width;
    const y = ((Z_MAX - z2) / (Z_MAX - Z_MIN)) * height; // invert Y
    return { x, y };
  };

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const { width, height } = svg.getBoundingClientRect();
    
    // Clear dynamic elements
    const dynamicLayer = svg.querySelector('#dynamic-layer');
    if (dynamicLayer) dynamicLayer.innerHTML = '';

    if (patient && dynamicLayer) {
      const p = mapToSvg(patient.z1, patient.z2, width, height);
      
      const ellipseWidth = width * 0.1;
      const ellipseHeight = height * 0.15;
      
      let quadColor = '#00c47d';
      if (patient.quadrant === 1) quadColor = '#f5a623';
      if (patient.quadrant === 2) quadColor = '#3d8ef8';
      if (patient.quadrant === 3) quadColor = '#e8394a';

      // Ellipse
      const ellipse = document.createElementNS("http://www.w3.org/2000/svg", "ellipse");
      ellipse.setAttribute('cx', p.x);
      ellipse.setAttribute('cy', p.y);
      ellipse.setAttribute('rx', ellipseWidth);
      ellipse.setAttribute('ry', ellipseHeight);
      ellipse.setAttribute('fill', quadColor);
      ellipse.setAttribute('fill-opacity', '0.2');
      ellipse.setAttribute('stroke', quadColor);
      ellipse.setAttribute('stroke-dasharray', '4');
      dynamicLayer.appendChild(ellipse);
      
      // Counterfactual arrow
      if (counterfactual && patient.quadrant !== 0) {
         const cp = mapToSvg(counterfactual.z1_target, counterfactual.z2_target, width, height);
         const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
         // bezier curve
         const d = `M ${p.x} ${p.y} Q ${p.x} ${cp.y} ${cp.x} ${cp.y}`;
         path.setAttribute('d', d);
         path.setAttribute('stroke', '#00c47d');
         path.setAttribute('stroke-width', '1.5');
         path.setAttribute('stroke-dasharray', '4');
         path.setAttribute('fill', 'none');
         dynamicLayer.appendChild(path);
         
         const targetCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
         targetCircle.setAttribute('cx', cp.x);
         targetCircle.setAttribute('cy', cp.y);
         targetCircle.setAttribute('r', '4');
         targetCircle.setAttribute('fill', '#00c47d');
         dynamicLayer.appendChild(targetCircle);
      }

      // Crosshairs
      const hLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
      hLine.setAttribute('x1', 0); hLine.setAttribute('y1', p.y);
      hLine.setAttribute('x2', width); hLine.setAttribute('y2', p.y);
      hLine.setAttribute('stroke', 'rgba(255,255,255,0.3)');
      hLine.setAttribute('stroke-width', '0.5');
      dynamicLayer.appendChild(hLine);

      const vLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
      vLine.setAttribute('x1', p.x); vLine.setAttribute('y1', 0);
      vLine.setAttribute('x2', p.x); vLine.setAttribute('y2', height);
      vLine.setAttribute('stroke', 'rgba(255,255,255,0.3)');
      vLine.setAttribute('stroke-width', '0.5');
      dynamicLayer.appendChild(vLine);

      // Patient Dot
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute('cx', p.x);
      dot.setAttribute('cy', p.y);
      dot.setAttribute('r', '6');
      dot.setAttribute('fill', '#ffffff');
      dot.setAttribute('stroke', quadColor);
      dot.setAttribute('stroke-width', '2');
      dot.style.filter = `drop-shadow(0 0 8px ${quadColor})`;
      dot.style.transition = 'all 0.3s ease-out';
      dynamicLayer.appendChild(dot);
    }
  }, [patient, counterfactual]);

  return (
    <svg ref={svgRef} style={{ width: '100%', height: '100%' }}>
      <defs>
         <radialGradient id="grad-db">
            <stop offset="0%" stopColor="#e8394a" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#e8394a" stopOpacity="0" />
         </radialGradient>
      </defs>
      
      {/* Q3: Dual-Burden */}
      <rect x="50%" y="0" width="50%" height="50%" fill="url(#grad-db)" />
      {/* Q1: IR-Dominant */}
      <rect x="50%" y="50%" width="50%" height="50%" fill="rgba(245, 166, 35, 0.08)" />
      {/* Q2: Steatosis-Dominant */}
      <rect x="0" y="0" width="50%" height="50%" fill="rgba(61, 142, 248, 0.08)" />
      {/* Q0: MHNW */}
      <rect x="0" y="50%" width="50%" height="50%" fill="rgba(0, 196, 125, 0.08)" />

      {/* Axis Lines */}
      <line x1="0" y1="50%" x2="100%" y2="50%" stroke="rgba(255,255,255,0.2)" />
      <line x1="50%" y1="0" x2="50%" y2="100%" stroke="rgba(255,255,255,0.2)" />
      
      {/* Grid Lines */}
      <line x1="0" y1="25%" x2="100%" y2="25%" stroke="rgba(255,255,255,0.05)" />
      <line x1="0" y1="75%" x2="100%" y2="75%" stroke="rgba(255,255,255,0.05)" />
      <line x1="25%" y1="0" x2="25%" y2="100%" stroke="rgba(255,255,255,0.05)" />
      <line x1="75%" y1="0" x2="75%" y2="100%" stroke="rgba(255,255,255,0.05)" />

      {/* Quadrant Labels */}
      <text x="95%" y="5%" fill="#e8394a" opacity="0.4" fontSize="12" textAnchor="end" letterSpacing="0.1em">DUAL-BURDEN</text>
      <text x="95%" y="95%" fill="#f5a623" opacity="0.4" fontSize="12" textAnchor="end" letterSpacing="0.1em">IR-DOMINANT</text>
      <text x="5%" y="5%" fill="#3d8ef8" opacity="0.4" fontSize="12" textAnchor="start" letterSpacing="0.1em">STEATOTIC</text>
      <text x="5%" y="95%" fill="#00c47d" opacity="0.4" fontSize="12" textAnchor="start" letterSpacing="0.1em">METABOLICALLY HEALTHY</text>

      <g id="dynamic-layer"></g>
    </svg>
  );
};
