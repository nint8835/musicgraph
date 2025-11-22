import { StrictMode, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import ForceGraph, { type ForceGraphMethods } from "react-force-graph-2d";
import { useKey } from "react-use";
import "./index.css";

const graphData = import.meta.glob("../graphs/*.json");
const loadedGraphData = await Promise.all(
  Object.entries(graphData).map(async ([path, resolver]) => {
    const module = await resolver();
    return [path, module.default];
  })
);
const graphDataMap: Record<string, any> = {};
loadedGraphData.forEach(([path, data]) => {
  const filename = path.split("/").pop()?.replace(".json", "") || path;
  graphDataMap[filename] = data;
});

const Graph = () => {
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [currentStep, setCurrentStep] = useState(0);

  useKey("ArrowUp", () => {
    setCurrentStep((step) =>
      Math.min(step + 1, Object.keys(graphDataMap).length - 1)
    );
  });
  useKey("ArrowDown", () => {
    setCurrentStep((step) => Math.max(step - 1, 0));
  });

  return (
    <ForceGraph
      nodeId="id"
      graphData={graphDataMap[currentStep.toString()]}
      nodeLabel={"label"}
      linkLabel={"type"}
      linkAutoColorBy={"type"}
      ref={graphRef}
      d3VelocityDecay={0.5}
    />
  );
};

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Graph />
  </StrictMode>
);
