import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [status, setStatus] = useState(null);
  const [latest, setLatest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [monitoring, setMonitoring] = useState(false);
  const [error, setError] = useState("");

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const [statusResponse, latestResponse] =
        await Promise.all([
          axios.get(`${API_URL}/status`),
          axios.get(`${API_URL}/latest`)
        ]);

      setStatus(statusResponse.data);
      setLatest(latestResponse.data);

    } catch (error) {
      console.error(error);
      setError("Unable to connect to the monitoring backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const runMonitoring = async () => {
    try {
      setMonitoring(true);
      setError("");

      await axios.post(`${API_URL}/monitor`);

      await loadDashboard();

    } catch (error) {
      console.error(error);
      setError("Monitoring cycle failed.");
    } finally {
      setMonitoring(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loader"></div>
        <h2>Loading Intelligence Dashboard...</h2>
      </div>
    );
  }

  const changes =
    latest?.changes?.data?.summary || {};

  const insight =
    latest?.ai_insight?.data || {};

  const entries =
    latest?.snapshot?.data?.changelog_entries || [];

  const changeData =
    latest?.changes?.data || {};

  const health =
    status?.status || "unknown";

  return (
    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div className="brand">

          <div className="logo">
            ⚡
          </div>

          <div>
            <h1>
              Self-Healing Intelligence
            </h1>

            <p>
              AI-Powered Web Monitoring System
            </p>
          </div>

        </div>

        <div className="header-actions">

          <div
            className={`health-badge ${health}`}
          >
            <span className="pulse"></span>

            {health.toUpperCase()}
          </div>

          <button
            className="monitor-button"
            onClick={runMonitoring}
            disabled={monitoring}
          >
            {monitoring ? (
              <>
                <span className="button-loader"></span>
                Monitoring...
              </>
            ) : (
              <>
                ▶ Run Monitoring
              </>
            )}
          </button>

        </div>

      </header>

      {/* ERROR */}

      {error && (
        <div className="error">
          ⚠ {error}
        </div>
      )}

      {/* STATUS CARDS */}

      <section className="status-grid">

        <div className="stat-card">

          <div className="stat-icon health-icon">
            ♥
          </div>

          <div>
            <p>System Health</p>

            <h2
              className={
                health === "healthy"
                  ? "text-success"
                  : "text-danger"
              }
            >
              {health.toUpperCase()}
            </h2>
          </div>

        </div>

        <div className="stat-card">

          <div className="stat-icon">
            ▤
          </div>

          <div>
            <p>Records</p>

            <h2>
              {status?.record_count || 0}
            </h2>
          </div>

        </div>

        <div className="stat-card">

          <div className="stat-icon new-icon">
            +
          </div>

          <div>
            <p>New Changes</p>

            <h2>
              {changes.new || 0}
            </h2>
          </div>

        </div>

        <div className="stat-card">

          <div className="stat-icon modified-icon">
            ↻
          </div>

          <div>
            <p>Modified</p>

            <h2>
              {changes.modified || 0}
            </h2>
          </div>

        </div>

        <div className="stat-card">

          <div className="stat-icon missing-icon">
            !
          </div>

          <div>
            <p>Missing</p>

            <h2>
              {changes.missing_from_latest_snapshot || 0}
            </h2>
          </div>

        </div>

      </section>

      <div className="dashboard-grid">

        {/* AI INSIGHT */}

        <section className="panel insight-panel">

          <div className="panel-header">

            <div>
              <p className="section-label">
                ARTIFICIAL INTELLIGENCE
              </p>

              <h2>
                AI Insight
              </h2>
            </div>

            <div
              className={`impact-badge impact-${(
                insight.overall_impact ||
                "low"
              ).toLowerCase()}`}
            >
              {(insight.overall_impact ||
                "low").toUpperCase()}
            </div>

          </div>

          <p className="insight-summary">
            {insight.summary ||
              "No AI insight available yet."}
          </p>

          {insight.categories &&
            insight.categories.length > 0 && (

            <div className="categories">

              {insight.categories.map(
                (category, index) => (

                  <span
                    key={index}
                    className="category"
                  >
                    {typeof category === "string"
                      ? category
                      : JSON.stringify(category)}
                  </span>

                )
              )}

            </div>

          )}

        </section>

        {/* CHANGE SUMMARY */}

        <section className="panel change-panel">

          <p className="section-label">
            CHANGE DETECTION
          </p>

          <h2>
            Latest Analysis
          </h2>

          <div className="change-list">

            <div className="change-row">

              <span className="change-dot new-dot"></span>

              <span>
                New entries
              </span>

              <strong>
                {changes.new || 0}
              </strong>

            </div>

            <div className="change-row">

              <span className="change-dot modified-dot"></span>

              <span>
                Modified entries
              </span>

              <strong>
                {changes.modified || 0}
              </strong>

            </div>

            <div className="change-row">

              <span className="change-dot missing-dot"></span>

              <span>
                Missing entries
              </span>

              <strong>
                {changes.missing_from_latest_snapshot || 0}
              </strong>

            </div>

            <div className="change-row">

              <span className="change-dot unchanged-dot"></span>

              <span>
                Unchanged
              </span>

              <strong>
                {changes.unchanged || 0}
              </strong>

            </div>

          </div>

        </section>

      </div>

      {/* LATEST CHANGES */}

      <section className="panel entries-panel">

        <div className="panel-header">

          <div>
            <p className="section-label">
              LIVE DATA
            </p>

            <h2>
              Latest Changelog Entries
            </h2>
          </div>

          <span className="entry-count">
            {entries.length} RECORDS
          </span>

        </div>

        <div className="entries">

          {entries.length === 0 ? (

            <div className="empty-state">
              No changelog entries available.
            </div>

          ) : (

            entries.map((entry, index) => (

              <article
                className="entry"
                key={entry.url || index}
              >

                <div className="entry-number">
                  {String(index + 1).padStart(2, "0")}
                </div>

                <div className="entry-content">

                  <h3>
                    {entry.title}
                  </h3>

                  <p>
                    {entry.description}
                  </p>

                  <a
                    href={entry.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    View Change →
                  </a>

                </div>

              </article>

            ))

          )}

        </div>

      </section>

      {/* FOOTER */}

      <footer className="footer">

        <span>
          Self-Healing Intelligence System
        </span>

        <span>
          Last scraped:{" "}
          {status?.last_scraped_at
            ? new Date(
                status.last_scraped_at
              ).toLocaleString()
            : "Unknown"}
        </span>

      </footer>

    </div>
  );
}

export default App;