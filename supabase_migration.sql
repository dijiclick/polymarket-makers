-- Polymarket Market Maker Analyzer - Supabase Migration
-- Run this in Supabase SQL Editor first

CREATE TABLE IF NOT EXISTS market_makers (
    id BIGSERIAL PRIMARY KEY,
    address TEXT NOT NULL UNIQUE,
    rank INTEGER,
    name TEXT DEFAULT '',
    pseudonym TEXT DEFAULT '',
    
    -- Volume metrics
    total_volume NUMERIC DEFAULT 0,
    buy_volume NUMERIC DEFAULT 0,
    sell_volume NUMERIC DEFAULT 0,
    buy_ratio NUMERIC DEFAULT 0,
    
    -- Trade counts
    total_trades INTEGER DEFAULT 0,
    buy_trades INTEGER DEFAULT 0,
    sell_trades INTEGER DEFAULT 0,
    total_fees NUMERIC DEFAULT 0,
    
    -- Market diversity
    num_markets INTEGER DEFAULT 0,
    avg_investment_per_market NUMERIC DEFAULT 0,
    
    -- Spread & pricing
    avg_spread NUMERIC DEFAULT 0,
    price_std NUMERIC DEFAULT 0,
    
    -- Behavior
    trades_per_day NUMERIC DEFAULT 0,
    top_counterparty_pct NUMERIC DEFAULT 0,
    
    -- Classification
    maker_type TEXT DEFAULT '',          -- TWO_SIDED_MM, BUY_HEAVY, SELL_HEAVY, etc.
    algo_fingerprint TEXT DEFAULT '',    -- HIGH_FREQ_SPREADER, CONCENTRATED_BOT, etc.
    
    -- Per-market breakdown (top 10 markets)
    top_markets JSONB DEFAULT '[]',
    
    -- Scan metadata
    scan_from_block BIGINT,
    scan_to_block BIGINT,
    scanned_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_mm_address ON market_makers(address);
CREATE INDEX IF NOT EXISTS idx_mm_volume ON market_makers(total_volume DESC);
CREATE INDEX IF NOT EXISTS idx_mm_algo ON market_makers(algo_fingerprint);
CREATE INDEX IF NOT EXISTS idx_mm_type ON market_makers(maker_type);
CREATE INDEX IF NOT EXISTS idx_mm_spread ON market_makers(avg_spread);
CREATE INDEX IF NOT EXISTS idx_mm_markets ON market_makers(num_markets DESC);

-- RLS
ALTER TABLE market_makers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow public read" ON market_makers;
CREATE POLICY "Allow public read" ON market_makers FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON market_makers;
CREATE POLICY "Allow service write" ON market_makers FOR ALL USING (true);
