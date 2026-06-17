type ShellSection = {
  title: string;
  eyebrow: string;
  summary: string;
};

const shellSections: ShellSection[] = [
  {
    title: "Question Workspace",
    eyebrow: "Ask",
    summary: "Technician troubleshooting questions will render here once the /ask contract exists.",
  },
  {
    title: "Document Status",
    eyebrow: "Ingest",
    summary: "Maintainer document state will render here after the documents endpoint is available.",
  },
  {
    title: "Evaluation",
    eyebrow: "Measure",
    summary: "Manual evaluation results will render here after the evaluation endpoint is available.",
  },
];

export function App() {
  return (
    <main className="app-shell">
      <header className="app-header" aria-labelledby="app-title">
        <div>
          <p className="app-kicker">Technical Manual RAG</p>
          <h1 id="app-title">Technician Console</h1>
        </div>
        <span className="app-status">Frontend baseline</span>
      </header>

      <section className="workspace-grid" aria-label="Application workspaces">
        {shellSections.map((section) => (
          <article className="workspace-panel" key={section.title}>
            <p>{section.eyebrow}</p>
            <h2>{section.title}</h2>
            <span>{section.summary}</span>
          </article>
        ))}
      </section>
    </main>
  );
}
