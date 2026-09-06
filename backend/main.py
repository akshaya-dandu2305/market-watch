from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal
from models import (
    Watchlist,
    Stock,
    MarketSnapshot,
    WatchlistCheckpoint,
)
from market_data import get_stock_data


app = FastAPI(
    title="Market Watch API",
    description="A change-first market watchlist API",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HELPERS
# =========================================================

def get_or_create_watchlist(db):
    watchlist = db.query(Watchlist).first()

    if not watchlist:
        watchlist = Watchlist(
            name="My Watchlist"
        )

        db.add(watchlist)
        db.commit()
        db.refresh(watchlist)

    return watchlist


def calculate_attention_score(
    since_last_percent,
    daily_change_percent,
    volume_ratio,
    unusual_ratio,
):
    score = 0
    reasons = []

    # -----------------------------------------------------
    # Change since last check
    # -----------------------------------------------------

    if since_last_percent is not None:

        absolute_change = abs(
            since_last_percent
        )

        if absolute_change >= 3:

            score += 30

            direction = (
                "up"
                if since_last_percent > 0
                else "down"
            )

            reasons.append(
                f"Price moved {absolute_change:.2f}% "
                f"{direction} since your last check."
            )

        elif absolute_change >= 2:

            score += 20

            reasons.append(
                f"Price changed {absolute_change:.2f}% "
                f"since your last check."
            )

        elif absolute_change >= 1:

            score += 10

            reasons.append(
                f"Price moved {absolute_change:.2f}% "
                f"since your last check."
            )

    # -----------------------------------------------------
    # Daily movement
    # -----------------------------------------------------

    if daily_change_percent is not None:

        absolute_daily = abs(
            daily_change_percent
        )

        if absolute_daily >= 3:

            score += 20

            reasons.append(
                f"Today's move is "
                f"{absolute_daily:.2f}%."
            )

        elif absolute_daily >= 2:

            score += 10

            reasons.append(
                f"Today's move reached "
                f"{absolute_daily:.2f}%."
            )

    # -----------------------------------------------------
    # Volume activity
    # -----------------------------------------------------

    if volume_ratio is not None:

        if volume_ratio >= 2:

            score += 25

            reasons.append(
                f"Trading volume is "
                f"{volume_ratio:.2f}× "
                f"the recent average."
            )

        elif volume_ratio >= 1.5:

            score += 15

            reasons.append(
                f"Trading volume is elevated at "
                f"{volume_ratio:.2f}× "
                f"the recent average."
            )

    # -----------------------------------------------------
    # Unusual movement
    # -----------------------------------------------------

    if unusual_ratio is not None:

        if unusual_ratio >= 2:

            score += 20

            reasons.append(
                "Today's price movement is unusually "
                "large compared with its typical daily move."
            )

        elif unusual_ratio >= 1.5:

            score += 10

            reasons.append(
                "Today's price movement is above "
                "the stock's typical daily range."
            )

    # -----------------------------------------------------
    # Cap score
    # -----------------------------------------------------

    score = min(score, 100)

    # -----------------------------------------------------
    # Attention level
    # -----------------------------------------------------

    if score >= 80:

        level = "high"

    elif score >= 50:

        level = "notable"

    else:

        level = "normal"

    if not reasons:

        reasons.append(
            "No meaningful change detected."
        )

    return score, level, reasons


def build_stock_result(
    stock,
    data,
    since_last_percent=None,
):
    attention_score, attention_level, reasons = (
        calculate_attention_score(
            since_last_percent=since_last_percent,
            daily_change_percent=data.get(
                "change_percent"
            ),
            volume_ratio=data.get(
                "volume_ratio"
            ),
            unusual_ratio=data.get(
                "unusual_ratio"
            ),
        )
    )

    return {
        "id": stock.id,

        "symbol": stock.symbol,

        "company_name": stock.company_name,

        "price": data.get(
            "price"
        ),

        "previous_close": data.get(
            "previous_close"
        ),

        "daily_change": data.get(
            "change"
        ),

        "daily_change_percent": data.get(
            "change_percent"
        ),

        "day_high": data.get(
            "day_high"
        ),

        "day_low": data.get(
            "day_low"
        ),

        "volume": data.get(
            "volume"
        ),

        "average_volume": data.get(
            "average_volume"
        ),

        "volume_ratio": data.get(
            "volume_ratio"
        ),

        "typical_daily_move": data.get(
            "typical_daily_move"
        ),

        "unusual_ratio": data.get(
            "unusual_ratio"
        ),

        "since_last_percent": (
            round(
                since_last_percent,
                2
            )
            if since_last_percent is not None
            else None
        ),

        "attention_score": attention_score,

        "attention_level": attention_level,

        "reasons": reasons,

        "data_date": data.get(
            "data_date"
        ),

        "data_status": data.get(
            "data_status",
            "latest_available",
        ),

        # -------------------------------------------------
        # NEW: price history for the frontend chart
        # -------------------------------------------------

        "price_history": data.get(
            "price_history",
            [],
        ),
    }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Market Watch API is running",
        "status": "ok",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# =========================================================
# GET WATCHLIST
# =========================================================

@app.get("/watchlist")
def get_watchlist():

    db = SessionLocal()

    try:

        watchlist = get_or_create_watchlist(
            db
        )

        return {
            "id": watchlist.id,

            "name": watchlist.name,

            "stocks": [
                {
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                }

                for stock in watchlist.stocks
            ],
        }

    finally:

        db.close()


# =========================================================
# ADD STOCK
# =========================================================

@app.post("/watchlist/stocks")
def add_stock(
    symbol: str,
    company_name: str,
):

    db = SessionLocal()

    try:

        watchlist = get_or_create_watchlist(
            db
        )

        symbol = symbol.strip().upper()

        company_name = company_name.strip()

        if not symbol or not company_name:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Symbol and company name "
                    "are required."
                ),
            )

        existing = (
            db.query(Stock)
            .filter(
                Stock.watchlist_id
                == watchlist.id,
                Stock.symbol
                == symbol,
            )
            .first()
        )

        if existing:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"{symbol} is already "
                    "in your watchlist."
                ),
            )

        # Validate market data before adding.

        market_symbol = symbol

        if not market_symbol.endswith(
            ".NS"
        ):

            market_symbol = (
                f"{market_symbol}.NS"
            )

        try:

            get_stock_data(
                market_symbol
            )

        except Exception as exc:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not find market data "
                    f"for {symbol}: {str(exc)}"
                ),
            )

        stock = Stock(
            symbol=symbol,
            company_name=company_name,
            watchlist_id=watchlist.id,
        )

        db.add(stock)

        db.commit()

        db.refresh(stock)

        return {
            "message": (
                "Stock added successfully."
            ),

            "stock": {
                "id": stock.id,
                "symbol": stock.symbol,
                "company_name": stock.company_name,
            },
        }

    finally:

        db.close()


# =========================================================
# DELETE / REMOVE STOCK
# =========================================================

@app.delete(
    "/watchlist/stocks/{stock_id}"
)
def delete_stock(stock_id: int):

    db = SessionLocal()

    try:

        stock = (
            db.query(Stock)
            .filter(
                Stock.id == stock_id
            )
            .first()
        )

        if not stock:

            raise HTTPException(
                status_code=404,
                detail="Stock not found.",
            )

        symbol = stock.symbol

        db.delete(stock)

        db.commit()

        return {
            "message": (
                f"{symbol} removed from "
                "your watchlist."
            ),

            "stock_id": stock_id,
        }

    finally:

        db.close()


# =========================================================
# GET MARKET DATA FOR ONE STOCK
# =========================================================

@app.get("/market/{symbol}")
def get_market(symbol: str):

    symbol = symbol.strip().upper()

    market_symbol = symbol

    if not market_symbol.endswith(
        ".NS"
    ):

        market_symbol = (
            f"{market_symbol}.NS"
        )

    try:

        data = get_stock_data(
            market_symbol
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return data


# =========================================================
# GET CURRENT MARKET DATA
# =========================================================

@app.get("/watchlist/market")
def get_watchlist_market():

    db = SessionLocal()

    try:

        watchlist = get_or_create_watchlist(
            db
        )

        results = []

        for stock in watchlist.stocks:

            market_symbol = stock.symbol

            if not market_symbol.endswith(
                ".NS"
            ):

                market_symbol = (
                    f"{market_symbol}.NS"
                )

            try:

                data = get_stock_data(
                    market_symbol
                )

                snapshot = MarketSnapshot(
                    stock_id=stock.id,
                    price=data["price"],
                    volume=data["volume"],
                    timestamp=datetime.utcnow(),
                )

                db.add(snapshot)

                results.append({
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    **data,
                })

            except Exception as exc:

                results.append({
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    "error": str(exc),
                })

        db.commit()

        return {
            "stocks": results
        }

    finally:

        db.close()


# =========================================================
# WATCHLIST CHANGE DETECTION
# =========================================================

@app.get("/watchlist/changes")
def get_watchlist_changes():

    db = SessionLocal()

    try:

        watchlist = get_or_create_watchlist(
            db
        )

        checkpoint = (
            db.query(
                WatchlistCheckpoint
            )
            .filter(
                WatchlistCheckpoint.watchlist_id
                == watchlist.id
            )
            .first()
        )

        previous_checkpoint = (
            checkpoint.last_checked_at
            if checkpoint
            else None
        )

        first_check = (
            checkpoint is None
        )

        stocks_result = []

        for stock in watchlist.stocks:

            market_symbol = stock.symbol

            if not market_symbol.endswith(
                ".NS"
            ):

                market_symbol = (
                    f"{market_symbol}.NS"
                )

            try:

                data = get_stock_data(
                    market_symbol
                )

                current_price = data["price"]

                since_last_percent = None

                # ---------------------------------------------
                # Find previous snapshot
                # ---------------------------------------------

                if previous_checkpoint:

                    previous_snapshot = (
                        db.query(
                            MarketSnapshot
                        )
                        .filter(
                            MarketSnapshot.stock_id
                            == stock.id
                        )
                        .filter(
                            MarketSnapshot.timestamp
                            <= previous_checkpoint
                        )
                        .order_by(
                            MarketSnapshot.timestamp.desc()
                        )
                        .first()
                    )

                    if previous_snapshot:

                        if (
                            previous_snapshot.price
                            and
                            previous_snapshot.price != 0
                        ):

                            since_last_percent = (
                                (
                                    current_price
                                    - previous_snapshot.price
                                )
                                /
                                previous_snapshot.price
                            ) * 100

                result = build_stock_result(
                    stock=stock,
                    data=data,
                    since_last_percent=(
                        since_last_percent
                    ),
                )

                stocks_result.append(
                    result
                )

                # ---------------------------------------------
                # Save current snapshot
                # ---------------------------------------------

                snapshot = MarketSnapshot(
                    stock_id=stock.id,
                    price=current_price,
                    volume=data.get(
                        "volume"
                    ),
                    timestamp=datetime.utcnow(),
                )

                db.add(snapshot)

            except Exception as exc:

                stocks_result.append({
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,

                    "price": None,

                    "daily_change_percent": None,

                    "since_last_percent": None,

                    "attention_score": 0,

                    "attention_level": "normal",

                    "reasons": [
                        "Market data is currently unavailable."
                    ],

                    "data_date": None,

                    "data_status": "unavailable",

                    "price_history": [],

                    "error": str(exc),
                })

        # =====================================================
        # UPDATE CHECKPOINT
        # =====================================================

        current_checkpoint_time = (
            datetime.utcnow()
        )

        if checkpoint:

            checkpoint.last_checked_at = (
                current_checkpoint_time
            )

        else:

            checkpoint = WatchlistCheckpoint(
                watchlist_id=watchlist.id,
                last_checked_at=(
                    current_checkpoint_time
                ),
            )

            db.add(checkpoint)

        db.commit()

        # =====================================================
        # DIGEST STATISTICS
        # =====================================================

        high_attention = sum(
            1
            for stock in stocks_result
            if stock.get(
                "attention_level"
            ) == "high"
        )

        notable = sum(
            1
            for stock in stocks_result
            if stock.get(
                "attention_level"
            ) == "notable"
        )

        normal = sum(
            1
            for stock in stocks_result
            if stock.get(
                "attention_level"
            ) == "normal"
        )

        meaningful_changes = sum(
            1
            for stock in stocks_result
            if stock.get(
                "attention_score",
                0
            ) >= 50
        )

        total = len(
            stocks_result
        )

        # =====================================================
        # TOP ATTENTION ITEMS
        # =====================================================

        attention_items = sorted(
            stocks_result,

            key=lambda stock:
                stock.get(
                    "attention_score",
                    0
                ),

            reverse=True,
        )

        attention_items = [
            stock

            for stock in attention_items

            if stock.get(
                "attention_score",
                0
            ) >= 20
        ][:3]

        # =====================================================
        # BIGGEST MOVERS
        # =====================================================

        biggest_movers = sorted(
            [
                stock

                for stock in stocks_result

                if stock.get(
                    "since_last_percent"
                ) is not None
            ],

            key=lambda stock:
                abs(
                    stock.get(
                        "since_last_percent",
                        0
                    )
                ),

            reverse=True,
        )[:3]

        # =====================================================
        # DIGEST MESSAGE
        # =====================================================

        if first_check:

            digest_title = (
                "Baseline saved."
            )

            digest_message = (
                "We've saved the current market "
                "state. Your next check will show "
                "what changed."
            )

        elif high_attention > 0:

            digest_title = (
                f"{high_attention} stock"
                f"{'s' if high_attention != 1 else ''} "
                "need your attention."
            )

            digest_message = (
                "Large or unusual movements were "
                "detected since your last check."
            )

        elif notable > 0:

            digest_title = (
                f"{notable} notable change"
                f"{'s' if notable != 1 else ''} "
                "detected."
            )

            digest_message = (
                "A few stocks moved enough to "
                "deserve a closer look."
            )

        else:

            digest_title = (
                "Nothing significant changed."
            )

            digest_message = (
                "Your watchlist is relatively "
                "quiet since the last check."
            )

        # =====================================================
        # DIGEST
        # =====================================================

        digest = {

            "title": digest_title,

            "message": digest_message,

            "high_attention":
                high_attention,

            "notable":
                notable,

            "normal":
                normal,

            "meaningful_changes":
                meaningful_changes,

            "total":
                total,

            "attention_items":
                attention_items,

            "biggest_movers":
                biggest_movers,

            "first_check":
                first_check,

            "previous_check": (
                previous_checkpoint.isoformat()
                if previous_checkpoint
                else None
            ),

            "current_check": (
                current_checkpoint_time.isoformat()
            ),
        }

        return {

            "first_check":
                first_check,

            "previous_check": (
                previous_checkpoint.isoformat()
                if previous_checkpoint
                else None
            ),

            "current_check": (
                current_checkpoint_time.isoformat()
            ),

            "digest":
                digest,

            "stocks":
                stocks_result,
        }

    finally:

        db.close()