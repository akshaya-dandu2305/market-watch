# Market Watch 📈

> A change-first market watchlist that filters market noise and highlights what deserves attention.

Market Watch is a full-stack web application designed to answer a simple question:

**"What actually changed since I last checked?"**

Instead of only displaying stock prices, Market Watch tracks changes between user check-ins, evaluates their significance, and presents a prioritized market digest.

---

## ✨ Features

### 📋 Smart Watchlist
- Add stocks using their ticker symbols
- Remove stocks from the watchlist
- Persist watchlist data using SQLite
- Automatically retrieve market information

### 🔄 Since Last Checked
Market Watch maintains a checkpoint for the watchlist.

When the user checks again, the application compares the latest market data against the previous checkpoint and identifies what changed.

### 🎯 Attention Score

Each stock receives an **Attention Score from 0–100** based on multiple signals:

- Change since the previous check
- Daily price movement
- Trading volume compared with recent average
- Whether the current movement is unusual compared with the stock's typical movement

This helps distinguish meaningful movement from ordinary market noise.

### 🧠 Market Digest

Instead of making the user scan every stock, the application summarizes:

- Stocks needing attention
- Notable changes
- Quiet stocks
- Biggest movers
- Important signals
- Reasons behind the attention score

### 📊 Stock Details

Clicking a stock opens a detailed view containing:

- Current price
- Daily change
- Change since last check
- Day high / low
- Trading volume
- Average volume
- Volume ratio
- Typical daily movement
- Attention score
- Recent price history
- Explanation of detected signals

### ⚠️ Data Awareness

The application explicitly labels market data as **latest available** rather than pretending that the data is guaranteed to be real-time.

This is important because external market-data providers may introduce delays or temporary availability issues.

---

## 🖥️ Application Overview

The application follows a change-first workflow:

```text
User opens Market Watch
        ↓
Market data is retrieved
        ↓
Previous checkpoint is loaded
        ↓
Current data is compared with previous data
        ↓
Attention signals are calculated
        ↓
Market Digest is generated
        ↓
User sees what deserves attention
