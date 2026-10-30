
import { useState } from "react";
import {
  Search,
  Globe,
  BrainCircuit,
  FileText,
  ShieldCheck,
  LoaderCircle,
  AlertCircle,
  ArrowUpRight,
  ChevronDown,
} from "lucide-react";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function handleResearch(event) {
    event.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Research request failed.");
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot connect to the backend. Make sure FastAPI is running on port 8000."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  function copyAnswer() {
    if (result?.short_answer) {
      navigator.clipboard.writeText(result.short_answer);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><BrainCircuit size={23} /></div>
          <div>
            <strong>Research Agent</strong>
            <span>AI-powered research</span>
          </div>
        </div>

        <div className="side-label">WORKSPACE</div>
        <div className="nav-item active">
          <Search size={18} /> Research
        </div>
        <div className="side-label tools-label">AGENT CAPABILITIES</div>
        <div className="capability"><Globe size={17} /> Web search</div>
        <div className="capability"><FileText size={17} /> Source analysis</div>
        <div className="capability"><ShieldCheck size={17} /> Evidence evaluation</div>

        <div className="sidebar-bottom">
          <span className="status-dot" />
          <span>Research workspace</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <span>Workspace / Research</span>
          <div className="system-status"><span className="status-dot" /> AI Agent</div>
        </header>

        <section className="hero">
          <div className="eyebrow"><span /> LANGGRAPH RESEARCH WORKFLOW</div>
          <h1>Research anything.<br /><span>Understand everything.</span></h1>
          <p>
            Ask a research question. The agent searches the web, evaluates
            evidence, and builds a structured answer with sources.
          </p>

          <form className="research-form" onSubmit={handleResearch}>
            <Search size={20} />
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="What would you like to research?"
              rows={2}
              required
            />
            <button type="submit" disabled={loading || !question.trim()}>
              {loading ? <LoaderCircle className="spin" size={18} /> : <Search size={18} />}
              {loading ? "Researching" : "Research"}
            </button>
          </form>
          <div className="input-hint">Ask a specific question for more useful findings.</div>
        </section>

        {loading && (
          <section className="loading-panel">
            <LoaderCircle className="spin" size={26} />
            <div>
              <strong>Research in progress</strong>
              <p>The agent is searching, collecting evidence, and evaluating sources.</p>
            </div>
          </section>
        )}

        {error && (
          <div className="error-panel">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <section className="results">
            <div className="results-heading">
              <div>
                <div className="section-kicker">RESEARCH REPORT</div>
                <h2>Research findings</h2>
              </div>
              <button className="secondary-button" onClick={copyAnswer}>
                Copy answer
              </button>
            </div>

            <div className="answer-card">
              <div className="card-heading">
                <BrainCircuit size={19} />
                <strong>Executive answer</strong>
                <span className={`confidence ${String(result.confidence || "low").toLowerCase()}`}>
                  {result.confidence || "Unknown"} confidence
                </span>
              </div>
              <p className="short-answer">{result.short_answer}</p>

              {result.key_findings?.length > 0 && (
                <>
                  <h3>Key findings</h3>
                  <ul className="findings-list">
                    {result.key_findings.map((finding, index) => (
                      <li key={index}>{finding}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>

            <div className="section-heading">
              <h3>Research execution</h3>
              <span>{result.execution_trace?.length || 0} events</span>
            </div>
            <div className="trace-list">
              {result.execution_trace?.map((event, index) => (
                <div className="trace-row" key={index}>
                  <div className={`trace-icon ${event.status === "failed" ? "failed" : ""}`}>
                    {event.status === "failed" ? <AlertCircle size={17} /> : <ShieldCheck size={17} />}
                  </div>
                  <div className="trace-copy">
                    <strong>{event.tool}</strong>
                    <p>{event.message}</p>
                  </div>
                  <span className={`trace-status ${event.status}`}>{event.status}</span>
                </div>
              ))}
            </div>

            <div className="section-heading">
              <h3>Sources</h3>
              <span>{result.sources_used?.length || 0} sources</span>
            </div>
            <div className="sources-grid">
              {result.sources_used?.map((source, index) => (
                <article className="source-card" key={`${source.url}-${index}`}>
                  <div className="source-number">SOURCE {String(index + 1).padStart(2, "0")}</div>
                  <h4>{source.title || "Untitled source"}</h4>
                  <p>{source.snippet || "No preview available."}</p>
                  <a href={source.url} target="_blank" rel="noreferrer">
                    Open source <ArrowUpRight size={15} />
                  </a>
                </article>
              ))}
              {(!result.sources_used || result.sources_used.length === 0) && (
                <p className="empty-state">No sources were validated for this answer.</p>
              )}
            </div>

            {[
              ["Assumptions", result.assumptions],
              ["Limitations", result.limitations],
              ["Suggested next steps", result.suggested_next_steps],
            ].map(([title, items]) =>
              items?.length ? (
                <details className="detail-section" key={title} open={title === "Limitations"}>
                  <summary>{title}<ChevronDown size={17} /></summary>
                  <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul>
                </details>
              ) : null
            )}
          </section>
        )}

        {!result && !loading && !error && (
          <section className="welcome-panel">
            <div className="welcome-icon"><FileText size={23} /></div>
            <h3>Your research starts here</h3>
            <p>Your report will include findings, source links, execution events, confidence, and limitations.</p>
          </section>
        )}

        <footer>AI Research Agent · Evidence first, answers second</footer>
      </main>
    </div>
  );
}

export default App;
