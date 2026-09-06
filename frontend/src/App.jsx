import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [symbol, setSymbol] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [adding, setAdding] = useState(false);

  const [selectedStock, setSelectedStock] = useState(null);
  const [removing, setRemoving] = useState(false);

  const loadMarketData = async () => {
    try {
      setError("");

      const response = await fetch(
        `${API_URL}/watchlist/changes`
      );

      if (!response.ok) {
        throw new Error("Failed to load market data");
      }

      const data = await response.json();

      setMarketData(data);
    } catch (err) {
      console.error(err);

      setError(
        "Could not connect to the Market Watch backend."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadMarketData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadMarketData();
  };

  const addStock = async (event) => {
    event.preventDefault();

    if (!symbol.trim() || !companyName.trim()) {
      setError(
        "Please enter both a stock symbol and company name."
      );

      return;
    }

    try {
      setAdding(true);
      setError("");

      const params = new URLSearchParams({
        symbol: symbol.trim().toUpperCase(),
        company_name: companyName.trim(),
      });

      const response = await fetch(
        `${API_URL}/watchlist/stocks?${params.toString()}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not add stock"
        );
      }

      setSymbol("");
      setCompanyName("");

      await loadMarketData();
    } catch (err) {
      console.error(err);

      setError(
        err.message || "Could not add the stock."
      );
    } finally {
      setAdding(false);
    }
  };

  const removeStock = async () => {
    if (!selectedStock) {
      return;
    }

    const confirmed = window.confirm(
      `Remove ${selectedStock.symbol} from your watchlist?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setRemoving(true);
      setError("");

      const response = await fetch(
        `${API_URL}/watchlist/stocks/${selectedStock.id}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not remove stock"
        );
      }

      setSelectedStock(null);

      await loadMarketData();
    } catch (err) {
      console.error(err);

      setError(
        err.message || "Could not remove the stock."
      );
    } finally {
      setRemoving(false);
    }
  };

  const getAttentionClass = (level) => {
    if (level === "high") {
      return "high";
    }

    if (level === "notable") {
      return "notable";
    }

    return "normal";
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) {
      return "—";
    }

    const sign = value > 0 ? "+" : "";

    return `${sign}${value.toFixed(2)}%`;
  };

  const closeDetails = () => {
    if (!removing) {
      setSelectedStock(null);
    }
  };

  /* =======================================================
     MINI PRICE CHART
  ======================================================= */

  const buildChart = (history) => {
    if (!history || history.length < 2) {
      return null;
    }

    const width = 500;
    const height = 190;

    const paddingX = 8;
    const paddingY = 12;

    const prices = history.map(
      (point) => Number(point.price)
    );

    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);

    const range =
      maxPrice - minPrice || 1;

    const points = history.map(
      (point, index) => {

        const x =
          paddingX +
          (index /
            (history.length - 1)) *
            (width - paddingX * 2);

        const y =
          height -
          paddingY -
          ((Number(point.price) - minPrice) /
            range) *
            (height - paddingY * 2);

        return {
          x,
          y,
          price: Number(point.price),
          date: point.date,
        };
      }
    );

    const path = points
      .map(
        (point, index) =>
          `${index === 0 ? "M" : "L"} ${
            point.x
          } ${point.y}`
      )
      .join(" ");

    const firstPrice = prices[0];
    const lastPrice = prices[prices.length - 1];

    const trendUp =
      lastPrice >= firstPrice;

    return {
      width,
      height,
      path,
      points,
      minPrice,
      maxPrice,
      trendUp,
    };
  };

  if (loading) {
    return (
      <div className="loading-screen">

        <div className="loader"></div>

        <p>
          Analyzing your watchlist...
        </p>

      </div>
    );
  }

  return (
    <div className="app">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="header">

        <div className="header-left">

          <p className="eyebrow">
            MARKET WATCH
          </p>

          <h1>
            Know what deserves
            <br />
            your attention.
          </h1>

          <p className="subtitle">
            A change-first watchlist that filters market
            noise and highlights what matters.
          </p>

        </div>

        <div className="header-right">

          <button
            className="refresh-button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing
              ? "Updating..."
              : "↻ Refresh"}
          </button>

          <div className="status">

            <span className="status-dot"></span>

            Market data connected

          </div>

        </div>

      </header>


      <main>

        {/* =================================================
            ERROR
        ================================================= */}

        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}


        {/* =================================================
            MARKET DIGEST
        ================================================= */}

        <section className="digest">

          <div className="digest-content">

            <p className="section-label">
              YOUR MARKET DIGEST
            </p>

            <h2>
              {marketData?.digest?.title ||
                "Your market digest"}
            </h2>

            <p>
              {marketData?.digest?.message ||
                "Checking your watchlist for meaningful changes."}
            </p>

          </div>


          <div className="digest-stats">

            <div className="digest-stat high-stat">

              <strong>
                {marketData?.digest?.high_attention ?? 0}
              </strong>

              <span>
                Need attention
              </span>

            </div>


            <div className="digest-stat notable-stat">

              <strong>
                {marketData?.digest?.notable ?? 0}
              </strong>

              <span>
                Notable
              </span>

            </div>


            <div className="digest-stat normal-stat">

              <strong>
                {marketData?.digest?.normal ?? 0}
              </strong>

              <span>
                Quiet
              </span>

            </div>

          </div>

        </section>


        {/* =================================================
            CHANGE DETECTION
        ================================================= */}

        <section className="section">

          <div className="section-heading">

            <div>

              <p className="section-label">
                CHANGE DETECTION
              </p>

              <h2>
                What changed?
              </h2>

            </div>


            <div className="section-meta">

              <span className="tracked-count">
                {marketData?.digest?.total ?? 0} tracked
              </span>

              {marketData?.previous_check && (
                <span className="last-checked">
                  Last checked{" "}
                  {new Date(
                    marketData.previous_check
                  ).toLocaleString("en-IN", {
                    day: "numeric",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              )}

            </div>

          </div>


          {/* FIRST CHECK */}

          {marketData?.first_check && (

            <div className="baseline-message">

              <div className="baseline-icon">
                ✓
              </div>

              <div>

                <h3>
                  You're all set.
                </h3>

                <p>
                  We've saved the current market state.
                  Come back later and we'll highlight
                  meaningful changes.
                </p>

              </div>

            </div>

          )}


          {/* TOP SIGNALS */}

          {!marketData?.first_check &&
            marketData?.digest?.attention_items?.length > 0 && (

            <div className="priority-summary">

              <div className="priority-summary-header">

                <div>

                  <p className="section-label">
                    TOP SIGNALS
                  </p>

                  <h3>
                    Worth a closer look
                  </h3>

                </div>

              </div>


              <div className="priority-list">

                {marketData.digest.attention_items
                  .slice(0, 3)
                  .map((stock) => (

                    <div
                      className="priority-item"
                      key={stock.id}
                      onClick={() =>
                        setSelectedStock(stock)
                      }
                    >

                      <div className="priority-symbol">
                        {stock.symbol}
                      </div>


                      <div className="priority-info">

                        <strong>
                          {stock.company_name}
                        </strong>

                        <span>
                          {stock.reasons?.[0] ||
                            "Meaningful market activity detected"}
                        </span>

                      </div>


                      <div className="priority-score">

                        <strong>
                          {stock.attention_score}
                        </strong>

                        <span>
                          / 100
                        </span>

                      </div>

                    </div>

                  ))}

              </div>

            </div>

          )}


          {/* STOCK GRID */}

          {marketData?.stocks?.length > 0 ? (

            <div className="stock-grid">

              {marketData.stocks.map((stock) => {

                const level =
                  stock.attention_level || "normal";

                const attentionClass =
                  getAttentionClass(level);

                const hasChange =
                  stock.since_last_percent !== null &&
                  stock.since_last_percent !== undefined;

                return (

                  <article
                    className={`stock-card ${attentionClass}`}
                    key={stock.id}
                    onClick={() =>
                      setSelectedStock(stock)
                    }
                  >

                    <div className="stock-card-top">

                      <div>

                        <span className="stock-symbol">
                          {stock.symbol}
                        </span>

                        <p className="company-name">
                          {stock.company_name}
                        </p>

                      </div>


                      <div
                        className={
                          `attention-badge ${attentionClass}`
                        }
                      >

                        <span>
                          ●
                        </span>

                        {level === "high"
                          ? "Needs attention"
                          : level === "notable"
                          ? "Notable"
                          : "Normal"}

                      </div>

                    </div>


                    <div className="price-row">

                      <div>

                        <span className="price">

                          ₹
                          {stock.price?.toLocaleString(
                            "en-IN",
                            {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            }
                          )}

                        </span>


                        <span
                          className={
                            stock.daily_change_percent >= 0
                              ? "positive"
                              : "negative"
                          }
                        >

                          {formatPercent(
                            stock.daily_change_percent
                          )}

                        </span>

                      </div>


                      <div className="attention-score">

                        <span>
                          ATTENTION
                        </span>

                        <strong>
                          {stock.attention_score ?? 0}
                        </strong>

                        <small>
                          / 100
                        </small>

                      </div>

                    </div>


                    <div className="change-box">

                      <div>

                        <span className="metric-label">
                          SINCE LAST CHECK
                        </span>

                        <strong
                          className={
                            !hasChange
                              ? ""
                              : stock.since_last_percent >= 0
                              ? "positive"
                              : "negative"
                          }
                        >

                          {hasChange
                            ? formatPercent(
                                stock.since_last_percent
                              )
                            : "Baseline"}

                        </strong>

                      </div>


                      <div>

                        <span className="metric-label">
                          VOLUME
                        </span>

                        <strong>
                          {stock.volume_ratio
                            ? `${stock.volume_ratio}×`
                            : "—"}
                        </strong>

                      </div>


                      <div>

                        <span className="metric-label">
                          TYPICAL MOVE
                        </span>

                        <strong>
                          {stock.typical_daily_move
                            ? `±${stock.typical_daily_move}%`
                            : "—"}
                        </strong>

                      </div>

                    </div>


                    <div className="why-box">

                      <span className="why-label">
                        WHY THIS MATTERS
                      </span>

                      <ul>

                        {(stock.reasons || [
                          "No meaningful change detected",
                        ])
                          .slice(0, 2)
                          .map(
                            (reason, index) => (
                              <li key={index}>
                                {reason}
                              </li>
                            )
                          )}

                      </ul>

                    </div>


                    <div className="card-footer">

                      <span>
                        Latest available data
                      </span>

                      <span>
                        {stock.data_date || "—"}
                      </span>

                    </div>


                    <div className="click-hint">
                      Click for details →
                    </div>

                  </article>

                );

              })}

            </div>

          ) : (

            <div className="baseline-message">

              <div className="baseline-icon">
                +
              </div>

              <div>

                <h3>
                  Your watchlist is empty.
                </h3>

                <p>
                  Add a stock below to start tracking
                  meaningful market changes.
                </p>

              </div>

            </div>

          )}

        </section>


        {/* =================================================
            ADD STOCK
        ================================================= */}

        <section className="add-section">

          <div>

            <p className="section-label">
              WATCHLIST
            </p>

            <h2>
              Track another stock
            </h2>

            <p>
              Add a stock and we'll start monitoring
              its meaningful changes.
            </p>

          </div>


          <form
            className="add-form"
            onSubmit={addStock}
          >

            <input
              type="text"
              placeholder="Symbol"
              value={symbol}
              onChange={(event) =>
                setSymbol(event.target.value)
              }
            />


            <input
              type="text"
              placeholder="Company name"
              value={companyName}
              onChange={(event) =>
                setCompanyName(event.target.value)
              }
            />


            <button
              type="submit"
              disabled={adding}
            >

              {adding
                ? "Adding..."
                : "+ Add stock"}

            </button>

          </form>

        </section>

      </main>


      {/* =====================================================
          STOCK DETAIL MODAL
      ===================================================== */}

      {selectedStock && (

        <div
          className="detail-overlay"
          onClick={closeDetails}
        >

          <div
            className="detail-panel"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <button
              className="detail-close"
              onClick={closeDetails}
              disabled={removing}
            >
              ×
            </button>


            <p className="section-label">
              STOCK DETAILS
            </p>


            <div className="detail-title">

              <div>

                <span className="detail-symbol">
                  {selectedStock.symbol}
                </span>

                <h2>
                  {selectedStock.company_name}
                </h2>

              </div>


              <div
                className={
                  `attention-badge ${
                    getAttentionClass(
                      selectedStock.attention_level
                    )
                  }`
                }
              >

                ●{" "}
                {selectedStock.attention_level === "high"
                  ? "Needs attention"
                  : selectedStock.attention_level === "notable"
                  ? "Notable"
                  : "Normal"}

              </div>

            </div>


            <div className="detail-price">

              <strong>
                ₹
                {selectedStock.price?.toLocaleString(
                  "en-IN",
                  {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  }
                )}
              </strong>

              <span
                className={
                  selectedStock.daily_change_percent >= 0
                    ? "positive"
                    : "negative"
                }
              >

                {formatPercent(
                  selectedStock.daily_change_percent
                )}

                {" today"}

              </span>

            </div>


            {/* =================================================
                MINI PRICE CHART
            ================================================= */}

            {(() => {

              const chart = buildChart(
                selectedStock.price_history
              );

              if (!chart) {
                return null;
              }

              return (

                <div className="price-chart-section">

                  <div className="chart-header">

                    <div>

                      <span className="chart-label">
                        PRICE TREND
                      </span>

                      <strong>
                        Last 1 month
                      </strong>

                    </div>

                    <span
                      className={
                        chart.trendUp
                          ? "chart-trend positive"
                          : "chart-trend negative"
                      }
                    >
                      {chart.trendUp
                        ? "▲ Up"
                        : "▼ Down"}
                    </span>

                  </div>


                  <div className="chart-wrapper">

                    <svg
                      viewBox={`0 0 ${chart.width} ${chart.height}`}
                      preserveAspectRatio="none"
                      className={
                        `price-chart ${
                          chart.trendUp
                            ? "chart-up"
                            : "chart-down"
                        }`
                      }
                    >

                      <line
                        x1="0"
                        y1={chart.height - 1}
                        x2={chart.width}
                        y2={chart.height - 1}
                        className="chart-axis"
                      />

                      <path
                        d={chart.path}
                        className="chart-line"
                        fill="none"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />

                    </svg>

                  </div>


                  <div className="chart-range">

                    <span>
                      ₹
                      {chart.minPrice.toLocaleString(
                        "en-IN",
                        {
                          maximumFractionDigits: 0,
                        }
                      )}
                    </span>

                    <span>
                      ₹
                      {chart.maxPrice.toLocaleString(
                        "en-IN",
                        {
                          maximumFractionDigits: 0,
                        }
                      )}
                    </span>

                  </div>

                </div>

              );

            })()}


            <div className="detail-score">

              <span>
                ATTENTION SCORE
              </span>

              <strong>
                {selectedStock.attention_score ?? 0}
              </strong>

              <small>
                / 100
              </small>

            </div>


            <div className="detail-metrics">

              <div>

                <span>
                  SINCE LAST CHECK
                </span>

                <strong
                  className={
                    selectedStock.since_last_percent >= 0
                      ? "positive"
                      : "negative"
                  }
                >

                  {selectedStock.since_last_percent !== null &&
                  selectedStock.since_last_percent !== undefined
                    ? formatPercent(
                        selectedStock.since_last_percent
                      )
                    : "Baseline"}

                </strong>

              </div>


              <div>

                <span>
                  VOLUME ACTIVITY
                </span>

                <strong>
                  {selectedStock.volume_ratio
                    ? `${selectedStock.volume_ratio}×`
                    : "—"}
                </strong>

              </div>


              <div>

                <span>
                  TYPICAL MOVE
                </span>

                <strong>
                  {selectedStock.typical_daily_move
                    ? `±${selectedStock.typical_daily_move}%`
                    : "—"}
                </strong>

              </div>

            </div>


            <div className="detail-reasons">

              <p className="why-label">
                WHY THIS MATTERS
              </p>

              <ul>

                {(selectedStock.reasons || [
                  "No meaningful change detected",
                ]).map(
                  (reason, index) => (
                    <li key={index}>
                      {reason}
                    </li>
                  )
                )}

              </ul>

            </div>


            <div className="detail-data">

              <span>
                Data status
              </span>

              <strong>
                Latest available
              </strong>

              <span>
                {selectedStock.data_date || "—"}
              </span>

            </div>


            <button
              className="remove-stock-button"
              onClick={removeStock}
              disabled={removing}
            >

              {removing
                ? "Removing..."
                : `Remove ${selectedStock.symbol}`}

            </button>

          </div>

        </div>

      )}

    </div>
  );
}

export default App;