# Polymarket Market Maker Leaderboard

## 7-Day On-Chain Scan Results

Scanned **9,872,485** OrderFilled events from the Polymarket CTF Exchange contract on Polygon.

### Stats
- **Blocks scanned:** 84,006,465 → 84,306,465
- **Total fills:** 9,872,485
- **Makers with $1k+ volume:** 44,792
- **Pure makers (zero taker vol):** 1,641

### Files
- `poly_makers_7d.json` — Full results (JSON)
- `poly_makers_7d.csv` — Full results (CSV)
- `poly_maker_scan.py` — Scanner script

### Top 10 Market Makers
| # | Address | Maker Vol | Taker Vol | Trades |
|---|---------|-----------|-----------|--------|
| 1 | `0x6480542954b70a674a74bd1a6015dec362dc8dc5` | $16,138,435 | $2,317,907 | 14,977 |
| 2 | `0x4c2966a198cd7ac982110d0219b037afa9997570` | $14,853,403 | $1,321,370 | 10,534 |
| 3 | `0xa8b202e6e9a4c2091b6860f1f5c9e9119bbc9a39` | $14,428,237 | $5,477,553 | 1,252 |
| 4 | `0x204f72f35326db932158cba6adff0b9a1da95e14` | $11,171,667 | $17,055,064 | 72,823 |
| 5 | `0x6d3c5bd13984b2de47c3a88ddc455309aab3d294` | $10,461,592 | $2,733,887 | 48,532 |
| 6 | `0x241f846866c2de4fb67cdb0ca6b963d85e56ef50` | $9,527,017 | $6,840,032 | 1,293 |
| 7 | `0xe8dd7741ccb12350957ec71e9ee332e0d1e6ec86` | $9,421,542 | $9,031,790 | 163,437 |
| 8 | `0x4133bcbad1d9c41de776646696f41c34d0a65e70` | $9,137,281 | $4,997,497 | 73,508 |
| 9 | `0xd04d93be590ded67b99f053d4b6d29d3f8483312` | $8,014,815 | $3,980,581 | 597 |
| 10 | `0x43e98f912cd6ddadaad88d3297e78c0648e688e5` | $8,012,284 | $2,122,076 | 19,161 |

### How it works
Scans Polygon `CTF Exchange` contract (`0xC5d563A36AE78145C45a50134d48A1215220f80a`) for `OrderFilled` events. Each event has indexed `maker` and `taker` addresses, allowing us to distinguish limit order providers from market order takers.
