import * as d3 from "d3";
import { useEffect, useRef } from "react";

export function LatentSpaceCanvas({ cohortPoints, patient, counterfactual }) {
  const svgRef = useRef();

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const { width, height } = svgRef.current.getBoundingClientRect();

    const xScale = d3.scaleLinear().domain([-3.5, 3.5]).range([60, width - 40]);
    const yScale = d3.scaleLinear().domain([-3.5, 3.5]).range([height - 40, 40]);

    svg.selectAll("*").remove();

    const xAxis = d3.axisBottom(xScale).ticks(5);
    const yAxis = d3.axisLeft(yScale).ticks(5);
    
    svg.append("g")
       .attr("transform", `translate(0, ${yScale(0)})`)
       .call(xAxis)
       .attr("opacity", 0.5);
       
    svg.append("g")
       .attr("transform", `translate(${xScale(0)}, 0)`)
       .call(yAxis)
       .attr("opacity", 0.5);

    if (cohortPoints && cohortPoints.length > 0) {
      svg.selectAll(".cohort-pt")
        .data(cohortPoints)
        .join("circle")
        .attr("class", "cohort-pt")
        .attr("cx", d => xScale(d.z1))
        .attr("cy", d => yScale(d.z2))
        .attr("r", 2)
        .attr("fill", d => d.ir_proxy ? "#D85A30" : "#1D9E75")
        .attr("opacity", 0.25);
    }

    if (patient) {
      const rx = xScale(patient.z1 + 1.96 * patient.z1_sigma) - xScale(patient.z1);
      const ry = yScale(patient.z2) - yScale(patient.z2 + 1.96 * patient.z2_sigma);

      svg.selectAll(".unc-ellipse").data([patient]).join("ellipse")
        .attr("class", "unc-ellipse")
        .attr("cx", d => xScale(d.z1))
        .attr("cy", d => yScale(d.z2))
        .attr("rx", Math.max(Math.abs(rx), 4))
        .attr("ry", Math.max(Math.abs(ry), 4))
        .attr("fill", "none")
        .attr("stroke", "#534AB7")
        .attr("stroke-width", 1.5)
        .attr("stroke-dasharray", "4 2");

      svg.selectAll(".patient-dot").data([patient]).join("circle")
        .attr("class", "patient-dot")
        .attr("cx", d => xScale(d.z1))
        .attr("cy", d => yScale(d.z2))
        .attr("r", 6)
        .attr("fill", "#534AB7");
    }

    if (patient && counterfactual) {
      const x1 = xScale(patient.z1),        y1 = yScale(patient.z2);
      const x2 = xScale(counterfactual.z1_counterfactual), y2 = yScale(patient.z2);

      svg.append("defs").append("marker")
        .attr("id", "cf-arrow-head")
        .attr("markerWidth", "8")
        .attr("markerHeight", "8")
        .attr("refX", "6")
        .attr("refY", "3")
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,0 L6,3 L0,6")
        .attr("fill", "none")
        .attr("stroke", "#BA7517")
        .attr("strokeWidth", "1.5");

      svg.selectAll(".cf-arrow").data([1]).join("line")
        .attr("class", "cf-arrow")
        .attr("x1", x1).attr("y1", y1)
        .attr("x2", x2).attr("y2", y2)
        .attr("stroke", "#BA7517")
        .attr("stroke-width", 2)
        .attr("marker-end", "url(#cf-arrow-head)");
    }

  }, [cohortPoints, patient, counterfactual]);

  return (
    <svg ref={svgRef} style={{ width: "100%", height: "420px", background: "#f8f9fa", borderRadius: "8px" }}></svg>
  );
}
