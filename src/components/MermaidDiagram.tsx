import { useEffect, useRef } from "react";
import mermaid from "mermaid";

interface MermaidDiagramProps {
  chart: string;
}

mermaid.initialize({
  startOnLoad: true,
  theme: "default",
  securityLevel: "loose",
});

export function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      mermaid.render("mermaid-diagram", chart).then(({ svg }) => {
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      });
    }
  }, [chart]);

  return <div ref={containerRef} className="mermaid-diagram overflow-auto" />;
}
