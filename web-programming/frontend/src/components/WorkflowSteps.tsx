export type WorkflowStage = "upload" | "segment" | "count" | "report";

const STEPS: { key: WorkflowStage; label: string }[] = [
  { key: "upload", label: "Upload" },
  { key: "segment", label: "Segment" },
  { key: "count", label: "Count" },
  { key: "report", label: "Report" },
];

interface Props {
  stage: WorkflowStage;
}

export default function WorkflowSteps({ stage }: Props) {
  const activeIndex = STEPS.findIndex((s) => s.key === stage);

  return (
    <div className="workflow" role="list" aria-label="Analysis workflow">
      {STEPS.map((step, i) => {
        const isActive = i === activeIndex;
        const isDone = i < activeIndex;
        const className = [
          "workflow-step",
          isActive ? "active" : "",
          isDone ? "done" : "",
        ]
          .filter(Boolean)
          .join(" ");
        return (
          <div key={step.key} className={className} role="listitem">
            <span className="step-number">{i + 1}</span>
            <span>{step.label}</span>
          </div>
        );
      })}
    </div>
  );
}
