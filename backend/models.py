from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="My Watchlist")

    stocks = relationship(
        "Stock",
        back_populates="watchlist",
        cascade="all, delete-orphan"
    )

    checkpoint = relationship(
        "WatchlistCheckpoint",
        back_populates="watchlist",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    company_name = Column(String, nullable=False)

    watchlist_id = Column(
        Integer,
        ForeignKey("watchlists.id")
    )

    watchlist = relationship(
        "Watchlist",
        back_populates="stocks"
    )

    snapshots = relationship(
        "MarketSnapshot",
        back_populates="stock",
        cascade="all, delete-orphan"
    )


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    stock_id = Column(
        Integer,
        ForeignKey("stocks.id")
    )

    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    stock = relationship(
        "Stock",
        back_populates="snapshots"
    )


class WatchlistCheckpoint(Base):
    __tablename__ = "watchlist_checkpoints"

    id = Column(Integer, primary_key=True, index=True)

    watchlist_id = Column(
        Integer,
        ForeignKey("watchlists.id"),
        unique=True
    )

    last_checked_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    watchlist = relationship(
        "Watchlist",
        back_populates="checkpoint"
    )