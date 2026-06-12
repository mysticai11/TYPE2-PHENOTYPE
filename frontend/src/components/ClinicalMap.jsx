import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Fallback synthetic population if /cohort is unavailable
const generateFallbackPopulation = () => {
  const pts = [];
  for (let i = 0; i < 300; i++) {
    const z1 = d3.randomNormal(-0.5, 1.2)();
    const z2 = d3.randomNormal(-0.5, 1.2)();
    let quadrant = 0;
    if (z1 >= 0 && z2 >= 0) quadrant = 3;
    else if (z1 >= 0) quadrant = 1;
    else if (z2 >= 0) quadrant = 2;
    pts.push({ z1, z2, quadrant });
  }
  return pts;
};

const QUADRANT_COLORS = {
  0: 'var(--territory-safe)',
  1: 'var(--territory-ir)',
  2: 'var(--territory-steatosis)',
  3: 'var(--territory-dual)',
};

export const ClinicalMap = ({ z1, z2, quadrantKey, researchMode, isSafe, geodesicPath, interventions }) => {
  const svgRef = useRef(null);
  const [cohortData, setCohortData] = useState(null);

  // Fetch real NHANES training coordinates from /cohort on mount
  useEffect(() => {
    axios.get(`${API_BASE}/cohort`)
      .then(r => setCohortData(r.data))
      .catch(() => setCohortData(generateFallbackPopulation().map((p, i) => ({
        z1: p.z1, z2: p.z2, quadrant: p.quadrant
      }))));
  }, []);

  const quadrantKeyToIdx = { mhnw: 0, ir_dominant: 1, steatosis_dominant: 2, dual_burden: 3 };

  useEffect(() => {
    if (!svgRef.current || z1 === undefined || z2 === undefined || cohortData === null) return;

    const width = 800;
    const height = 800;
    const margin = { top: 40, right: 40, bottom: 60, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const xScale = d3.scaleLinear().domain([-3, 3]).range([0, innerWidth]);
    const yScale = d3.scaleLinear().domain([-3, 3]).range([innerHeight, 0]);

    const defs = svg.append('defs');

    const territoryColors = {
      mhnw: 'var(--territory-safe)',
      ir_dominant: 'var(--territory-ir)',
      steatosis_dominant: 'var(--territory-steatosis)',
      dual_burden: 'var(--territory-dual)',
    };

    // Radial gradients for territories
    Object.entries(territoryColors).forEach(([key, color]) => {
      const grad = defs.append('radialGradient')
        .attr('id', `grad-${key}`)
        .attr('cx', key.includes('ir') || key === 'dual_burden' ? '100%' : '0%')
        .attr('cy', key.includes('steatosis') || key === 'dual_burden' ? '0%' : '100%')
        .attr('r', '100%');
      grad.append('stop').attr('offset', '0%').attr('stop-color', color).attr('stop-opacity', 0.15);
      grad.append('stop').attr('offset', '100%').attr('stop-color', color).attr('stop-opacity', 0);
    });

    // Patient pin drop shadow
    const shadow = defs.append('filter').attr('id', 'drop-shadow')
      .attr('x', '-20%').attr('y', '-20%').attr('width', '140%').attr('height', '140%');
    const pColor = territoryColors[quadrantKey] || territoryColors.mhnw;
    shadow.append('feDropShadow').attr('dx', 0).attr('dy', 4).attr('stdDeviation', 4)
      .attr('flood-color', pColor).attr('flood-opacity', 0.4);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // LAYER 1: Territory backgrounds
    const cx = xScale(0);
    const cy = yScale(0);
    g.append('rect').attr('x', 0).attr('y', 0).attr('width', cx).attr('height', cy).attr('fill', 'url(#grad-steatosis_dominant)');
    g.append('text').attr('x', 20).attr('y', 40).attr('class', 'territory-label').text('FATTY LIVER RISK');
    g.append('rect').attr('x', cx).attr('y', 0).attr('width', innerWidth - cx).attr('height', cy).attr('fill', 'url(#grad-dual_burden)');
    g.append('text').attr('x', innerWidth - 20).attr('y', 40).attr('text-anchor', 'end').attr('class', 'territory-label').text('DUAL BURDEN ZONE');
    g.append('rect').attr('x', 0).attr('y', cy).attr('width', cx).attr('height', innerHeight - cy).attr('fill', 'url(#grad-mhnw)');
    g.append('text').attr('x', 20).attr('y', innerHeight - 40).attr('class', 'territory-label').text('METABOLICALLY HEALTHY');
    g.append('rect').attr('x', cx).attr('y', cy).attr('width', innerWidth - cx).attr('height', innerHeight - cy).attr('fill', 'url(#grad-ir_dominant)');
    g.append('text').attr('x', innerWidth - 20).attr('y', innerHeight - 40).attr('text-anchor', 'end').attr('class', 'territory-label').text('INSULIN RESISTANT');

    // LAYER 2: Density contours from real/fallback cohort
    const contourGen = d3.contourDensity()
      .x(d => xScale(d.z1)).y(d => yScale(d.z2))
      .size([innerWidth, innerHeight]).bandwidth(40);
    const densityData = contourGen(cohortData);
    g.append('g').attr('opacity', 0.06).selectAll('path').data(densityData).enter().append('path')
      .attr('d', d3.geoPath()).attr('fill', 'none').attr('stroke', '#fff').attr('stroke-width', 0.5);

    // LAYER 3: Grid and axes
    g.append('g').attr('class', 'grid').attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).tickSize(-innerHeight).tickFormat('').ticks(10))
      .attr('stroke-opacity', 0.05);
    g.append('g').attr('class', 'grid')
      .call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat('').ticks(10))
      .attr('stroke-opacity', 0.05);

    // Threshold lines (gold)
    g.append('line').attr('x1', cx).attr('x2', cx).attr('y1', 0).attr('y2', innerHeight)
      .attr('stroke', 'var(--gold-threshold)').attr('stroke-width', 1).attr('opacity', 0.4);
    g.append('line').attr('x1', 0).attr('x2', innerWidth).attr('y1', cy).attr('y2', cy)
      .attr('stroke', 'var(--gold-threshold)').attr('stroke-width', 1).attr('opacity', 0.4);

    // Axis labels
    svg.append('text').attr('x', width / 2).attr('y', height - 10).attr('text-anchor', 'middle')
      .attr('fill', 'var(--text-muted)').style('font-size', '11px').style('letter-spacing', '0.15em')
      .text('INSULIN RESISTANT →');
    svg.append('text').attr('transform', 'rotate(-90)').attr('x', -height / 2).attr('y', 20)
      .attr('text-anchor', 'middle').attr('fill', 'var(--text-muted)')
      .style('font-size', '11px').style('letter-spacing', '0.15em').text('LIVER FAT ↑');

    // LAYER 4: Real NHANES cohort dots
    g.selectAll('.pop-dot').data(cohortData).enter().append('circle')
      .attr('class', 'pop-dot')
      .attr('cx', d => xScale(d.z1)).attr('cy', d => yScale(d.z2))
      .attr('r', researchMode ? 4 : 3)
      .attr('fill', d => researchMode ? (QUADRANT_COLORS[d.quadrant] || '#fff') : '#fff')
      .attr('opacity', researchMode ? 0.3 : 0.05);

    // LAYER 5: Geodesic pathway (real) or Euclidean fallback
    const px = xScale(z1);
    const py = yScale(z2);
    const patientGroup = g.append('g');

    if (!isSafe) {
      const lineGen = d3.line().x(d => xScale(d[0])).y(d => yScale(d[1])).curve(d3.curveCatmullRom);

      if (geodesicPath && geodesicPath.length > 1) {
        // Real Riemannian geodesic path from backend
        patientGroup.append('path')
          .datum(geodesicPath)
          .attr('d', lineGen)
          .attr('fill', 'none').attr('stroke', 'var(--territory-safe)').attr('stroke-width', 3)
          .attr('class', 'route-path').style('filter', 'drop-shadow(0 0 4px var(--territory-safe))');

        // Destination marker (the safe-zone target point)
        const dest = geodesicPath[geodesicPath.length - 1];
        patientGroup.append('circle')
          .attr('cx', xScale(dest[0])).attr('cy', yScale(dest[1])).attr('r', 6)
          .attr('fill', 'none').attr('stroke', 'var(--territory-safe)').attr('stroke-width', 2);

        // Top-2 intervention waypoints from geodesic
        const waypointSteps = interventions && interventions.length > 0
          ? [
              interventions[Math.floor(interventions.length * 0.35)],
              interventions[Math.floor(interventions.length * 0.70)],
            ].filter(Boolean)
          : [];

        waypointSteps.forEach((wp) => {
          if (!wp || !wp.z) return;
          const wx = xScale(wp.z[0]);
          const wy = yScale(wp.z[1]);
          const topBiomarker = wp.biomarker_deltas
            ? Object.entries(wp.biomarker_deltas).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0]
            : null;
          const label = topBiomarker
            ? `◆ ${topBiomarker[0].replace(/_mg_dL|_U_L|_uU_mL/g, '').replace(/_/g, ' ').toUpperCase()} ${topBiomarker[1] > 0 ? '+' : ''}${topBiomarker[1].toFixed(1)}`
            : '◆ Waypoint';
          patientGroup.append('rect')
            .attr('x', wx - 4).attr('y', wy - 4).attr('width', 8).attr('height', 8)
            .attr('transform', `rotate(45 ${wx} ${wy})`).attr('fill', 'var(--territory-safe)');
          patientGroup.append('text').attr('x', wx + 12).attr('y', wy + 4)
            .attr('fill', 'var(--white-data)').style('font-size', '10px').text(label);
        });

      } else {
        // Euclidean fallback
        const destX = xScale(-0.5), destY = yScale(-0.5);
        const path = d3.path();
        path.moveTo(px, py);
        path.quadraticCurveTo(px - (px - destX), py, destX, destY);
        patientGroup.append('path').attr('d', path.toString()).attr('fill', 'none')
          .attr('stroke', 'var(--territory-safe)').attr('stroke-width', 3)
          .attr('class', 'route-path').style('filter', 'drop-shadow(0 0 4px var(--territory-safe))');
        patientGroup.append('circle').attr('cx', destX).attr('cy', destY).attr('r', 6)
          .attr('fill', 'none').attr('stroke', 'var(--territory-safe)').attr('stroke-width', 2);
        patientGroup.append('text').attr('x', (px + destX) / 2 + 12).attr('y', (py + destY) / 2 + 4)
          .attr('fill', 'var(--white-data)').style('font-size', '10px').text('◆ Moderate intervention');
      }
    }

    // LAYER 6: Patient pin
    patientGroup.append('line').attr('x1', px).attr('x2', px).attr('y1', py).attr('y2', innerHeight)
      .attr('stroke', '#fff').attr('stroke-width', 1).attr('stroke-dasharray', '4 4').attr('opacity', 0).attr('class', 'crosshair');
    patientGroup.append('line').attr('x1', 0).attr('x2', px).attr('y1', py).attr('y2', py)
      .attr('stroke', '#fff').attr('stroke-width', 1).attr('stroke-dasharray', '4 4').attr('opacity', 0).attr('class', 'crosshair');

    patientGroup.append('circle').attr('cx', px).attr('cy', py).attr('r', 35)
      .attr('fill', pColor).attr('class', 'halo-breathe');

    const pinGroup = patientGroup.append('g').attr('class', 'pin-drop')
      .attr('transform', `translate(${px},${py})`).style('cursor', 'pointer')
      .on('mouseenter', () => g.selectAll('.crosshair').attr('opacity', 0.2))
      .on('mouseleave', () => g.selectAll('.crosshair').attr('opacity', 0));

    pinGroup.append('ellipse').attr('cx', 0).attr('cy', 8).attr('rx', 6).attr('ry', 3)
      .attr('fill', pColor).attr('opacity', 0.4);
    pinGroup.append('path')
      .attr('d', 'M0,-24 C8,-24 12,-16 12,-10 C12,-2 0,4 0,4 C0,4 -12,-2 -12,-10 C-12,-16 -8,-24 0,-24 Z')
      .attr('fill', '#fff').attr('stroke', pColor).attr('stroke-width', 2)
      .style('filter', 'url(#drop-shadow)');
    pinGroup.append('circle').attr('cx', 0).attr('cy', -14).attr('r', 4).attr('fill', pColor);

    if (researchMode) {
      pinGroup.append('text').attr('y', -30).attr('text-anchor', 'middle')
        .attr('fill', '#fff').style('font-family', 'var(--font-mono)').style('font-size', '10px')
        .text(`[${z1.toFixed(2)}, ${z2.toFixed(2)}]`);
      patientGroup.append('ellipse').attr('cx', px).attr('cy', py).attr('rx', 60).attr('ry', 45)
        .attr('fill', 'none').attr('stroke', pColor).attr('stroke-dasharray', '2 2');
    }

  }, [z1, z2, quadrantKey, researchMode, isSafe, cohortData, geodesicPath, interventions]);

  return (
    <div className="map-container">
      <svg ref={svgRef} className="map-svg" viewBox="0 0 800 800"></svg>
    </div>
  );
};
