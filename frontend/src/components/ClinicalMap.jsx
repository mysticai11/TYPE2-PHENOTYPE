import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

// Simulated population sample for rendering the background cloud
const generatePopulation = () => {
  const pts = [];
  for (let i = 0; i < 400; i++) {
    // Skew towards MHNW (-Z1, -Z2)
    const z1 = d3.randomNormal(-0.5, 1.2)();
    const z2 = d3.randomNormal(-0.5, 1.2)();
    let q = 'mhnw';
    if (z1 >= 0 && z2 >= 0) q = 'dual_burden';
    else if (z1 >= 0) q = 'ir_dominant';
    else if (z2 >= 0) q = 'steatosis_dominant';
    pts.push({ z1, z2, q });
  }
  return pts;
};

const popData = generatePopulation();

export const ClinicalMap = ({ z1, z2, quadrantKey, researchMode, isSafe }) => {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || z1 === undefined || z2 === undefined) return;

    const width = 800;
    const height = 800;
    const margin = { top: 40, right: 40, bottom: 60, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // clear

    const xScale = d3.scaleLinear().domain([-3, 3]).range([0, innerWidth]);
    const yScale = d3.scaleLinear().domain([-3, 3]).range([innerHeight, 0]);

    // Defs for gradients
    const defs = svg.append("defs");
    
    const colors = {
      mhnw: "var(--territory-safe)",
      ir_dominant: "var(--territory-ir)",
      steatosis_dominant: "var(--territory-steatosis)",
      dual_burden: "var(--territory-dual)"
    };

    // Radial gradient for territories
    Object.entries(colors).forEach(([key, color]) => {
      const grad = defs.append("radialGradient")
        .attr("id", `grad-${key}`)
        .attr("cx", key.includes('ir') || key === 'dual_burden' ? "100%" : "0%")
        .attr("cy", key.includes('steatosis') || key === 'dual_burden' ? "0%" : "100%")
        .attr("r", "100%");
      grad.append("stop").attr("offset", "0%").attr("stop-color", color).attr("stop-opacity", 0.15);
      grad.append("stop").attr("offset", "100%").attr("stop-color", color).attr("stop-opacity", 0);
    });

    // Patient Drop Shadow
    const shadow = defs.append("filter").attr("id", "drop-shadow").attr("x", "-20%").attr("y", "-20%").attr("width", "140%").attr("height", "140%");
    shadow.append("feDropShadow").attr("dx", 0).attr("dy", 4).attr("stdDeviation", 4).attr("flood-color", colors[quadrantKey] || colors.mhnw).attr("flood-opacity", 0.4);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // LAYER 1: Territory Backgrounds
    const cx = xScale(0);
    const cy = yScale(0);
    
    // Top-Left (Steatosis)
    g.append("rect").attr("x", 0).attr("y", 0).attr("width", cx).attr("height", cy).attr("fill", "url(#grad-steatosis_dominant)");
    g.append("text").attr("x", 20).attr("y", 40).attr("class", "territory-label").text("FATTY LIVER RISK");
    
    // Top-Right (Dual)
    g.append("rect").attr("x", cx).attr("y", 0).attr("width", innerWidth - cx).attr("height", cy).attr("fill", "url(#grad-dual_burden)");
    g.append("text").attr("x", innerWidth - 20).attr("y", 40).attr("text-anchor", "end").attr("class", "territory-label").text("DUAL BURDEN ZONE");
    
    // Bottom-Left (MHNW)
    g.append("rect").attr("x", 0).attr("y", cy).attr("width", cx).attr("height", innerHeight - cy).attr("fill", "url(#grad-mhnw)");
    g.append("text").attr("x", 20).attr("y", innerHeight - 40).attr("class", "territory-label").text("METABOLICALLY HEALTHY");
    
    // Bottom-Right (IR)
    g.append("rect").attr("x", cx).attr("y", cy).attr("width", innerWidth - cx).attr("height", innerHeight - cy).attr("fill", "url(#grad-ir_dominant)");
    g.append("text").attr("x", innerWidth - 20).attr("y", innerHeight - 40).attr("text-anchor", "end").attr("class", "territory-label").text("INSULIN RESISTANT");

    // LAYER 2: Terrain Contours (Simulated)
    const contourGen = d3.contourDensity()
      .x(d => xScale(d.z1))
      .y(d => yScale(d.z2))
      .size([innerWidth, innerHeight])
      .bandwidth(40);
    
    const densityData = contourGen(popData);
    const contourGroup = g.append("g").attr("opacity", 0.06);
    contourGroup.selectAll("path").data(densityData).enter().append("path")
      .attr("d", d3.geoPath())
      .attr("fill", "none")
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.5);

    // LAYER 3: Grid and Axes
    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).tickSize(-innerHeight).tickFormat("").ticks(10))
      .attr("stroke-opacity", 0.05);

    g.append("g")
      .attr("class", "grid")
      .call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat("").ticks(10))
      .attr("stroke-opacity", 0.05);

    // Threshold lines (Gold)
    g.append("line").attr("x1", cx).attr("x2", cx).attr("y1", 0).attr("y2", innerHeight)
      .attr("stroke", "var(--gold-threshold)").attr("stroke-width", 1).attr("opacity", 0.4);
    g.append("line").attr("x1", 0).attr("x2", innerWidth).attr("y1", cy).attr("y2", cy)
      .attr("stroke", "var(--gold-threshold)").attr("stroke-width", 1).attr("opacity", 0.4);

    // Axis Labels
    svg.append("text")
      .attr("x", width / 2).attr("y", height - 10)
      .attr("text-anchor", "middle").attr("fill", "var(--text-muted)")
      .style("font-size", "11px").style("letter-spacing", "0.15em")
      .text("INSULIN RESISTANT →");
    
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2).attr("y", 20)
      .attr("text-anchor", "middle").attr("fill", "var(--text-muted)")
      .style("font-size", "11px").style("letter-spacing", "0.15em")
      .text("LIVER FAT ↑");

    // LAYER 4: Population Sample
    g.selectAll(".pop-dot").data(popData).enter().append("circle")
      .attr("class", "pop-dot")
      .attr("cx", d => xScale(d.z1)).attr("cy", d => yScale(d.z2))
      .attr("r", researchMode ? 4 : 3)
      .attr("fill", d => researchMode ? colors[d.q] : "#fff")
      .attr("opacity", researchMode ? 0.3 : 0.05);

    // LAYER 5: Patient Data
    const px = xScale(z1);
    const py = yScale(z2);
    const pColor = colors[quadrantKey] || colors.mhnw;

    const patientGroup = g.append("g");

    // Counterfactual Route (only if not safe)
    if (!isSafe) {
      const destX = xScale(-0.5);
      const destY = yScale(-0.5);

      // Bezier curve
      const dx = px - destX;
      const dy = py - destY;
      const path = d3.path();
      path.moveTo(px, py);
      path.quadraticCurveTo(px - dx, py, destX, destY);

      patientGroup.append("path")
        .attr("d", path.toString())
        .attr("fill", "none")
        .attr("stroke", "var(--territory-safe)")
        .attr("stroke-width", 3)
        .attr("class", "route-path")
        .style("filter", "drop-shadow(0 0 4px var(--territory-safe))");

      // Safe Zone Marker
      patientGroup.append("circle")
        .attr("cx", destX).attr("cy", destY).attr("r", 6)
        .attr("fill", "none").attr("stroke", "var(--territory-safe)").attr("stroke-width", 2);
      
      // Waypoint (mid)
      const midX = path.moveTo(px,py), len = 100; // rough mid calculation for visual
      patientGroup.append("rect")
        .attr("x", (px + destX)/2 - 4).attr("y", (py + destY)/2 - 4)
        .attr("width", 8).attr("height", 8)
        .attr("transform", `rotate(45 ${(px + destX)/2} ${(py + destY)/2})`)
        .attr("fill", "var(--territory-safe)");
        
      patientGroup.append("text")
        .attr("x", (px + destX)/2 + 12).attr("y", (py + destY)/2 + 4)
        .attr("fill", "var(--white-data)").style("font-size", "10px")
        .text("◆ Moderate intervention required");
    }

    // Crosshairs
    patientGroup.append("line").attr("x1", px).attr("x2", px).attr("y1", py).attr("y2", innerHeight)
      .attr("stroke", "#fff").attr("stroke-width", 1).attr("stroke-dasharray", "4 4").attr("opacity", 0).attr("class", "crosshair");
    patientGroup.append("line").attr("x1", 0).attr("x2", px).attr("y1", py).attr("y2", py)
      .attr("stroke", "#fff").attr("stroke-width", 1).attr("stroke-dasharray", "4 4").attr("opacity", 0).attr("class", "crosshair");

    // Halo
    patientGroup.append("circle")
      .attr("cx", px).attr("cy", py).attr("r", 35)
      .attr("fill", pColor).attr("class", "halo-breathe");

    // Pin Drop Wrapper
    const pinGroup = patientGroup.append("g")
      .attr("class", "pin-drop")
      .attr("transform", `translate(${px},${py})`)
      .style("cursor", "pointer")
      .on("mouseenter", () => g.selectAll(".crosshair").attr("opacity", 0.2))
      .on("mouseleave", () => g.selectAll(".crosshair").attr("opacity", 0));

    // Pin Shadow
    pinGroup.append("ellipse").attr("cx", 0).attr("cy", 8).attr("rx", 6).attr("ry", 3).attr("fill", pColor).attr("opacity", 0.4);

    // Map Pin SVG Shape
    pinGroup.append("path")
      .attr("d", "M0,-24 C8,-24 12,-16 12,-10 C12,-2 0,4 0,4 C0,4 -12,-2 -12,-10 C-12,-16 -8,-24 0,-24 Z")
      .attr("fill", "#fff")
      .attr("stroke", pColor)
      .attr("stroke-width", 2)
      .style("filter", "url(#drop-shadow)");

    pinGroup.append("circle")
      .attr("cx", 0).attr("cy", -14).attr("r", 4)
      .attr("fill", pColor);

    if (researchMode) {
      pinGroup.append("text").attr("y", -30).attr("text-anchor", "middle")
        .attr("fill", "#fff").style("font-family", "var(--font-mono)").style("font-size", "10px")
        .text(`[${z1.toFixed(2)}, ${z2.toFixed(2)}]`);
      
      // Ellipse boundary
      patientGroup.append("ellipse")
        .attr("cx", px).attr("cy", py)
        .attr("rx", 60).attr("ry", 45) // simulated boundary
        .attr("fill", "none").attr("stroke", pColor).attr("stroke-dasharray", "2 2");
    }

  }, [z1, z2, quadrantKey, researchMode, isSafe]);

  return (
    <div className="map-container">
      <svg ref={svgRef} className="map-svg" viewBox="0 0 800 800"></svg>
    </div>
  );
};
