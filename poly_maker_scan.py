"""
Polymarket Market Maker Scanner
================================
Scans Polygon CTF Exchange contract for OrderFilled events.
Extracts maker addresses + volume, filters for $1000+ makers.

Event: OrderFilled(bytes32 indexed orderHash, address indexed maker, address indexed taker,
                   uint256 makerAssetId, uint256 takerAssetId,
                   uint256 makerAmountFilled, uint256 takerAmountFilled, uint256 fee)
Contract: 0xC5d563A36AE78145C45a50134d48A1215220f80a (Polygon)

Usage:
  python3 poly_maker_scan.py --blocks 50000   # ~1 day of blocks
  python3 poly_maker_scan.py --blocks 500000  # ~10 days
"""

import urllib.request, json, time, sys, argparse
from collections import defaultdict

RPC = "https://rpc-mainnet.matic.quiknode.pro"
CTF_EXCHANGE = "0xC5d563A36AE78145C45a50134d48A1215220f80a"
ORDER_FILLED_TOPIC = "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6"
USDC_DECIMALS = 1e6

# Polygon: ~2 seconds per block, ~43200 blocks/day
BLOCKS_PER_DAY = 43200
MAX_BLOCKS_PER_REQUEST = 2000  # Safe limit for free RPC


def rpc_call(method, params, retries=3):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                RPC,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                result = json.load(r)
                if "error" in result:
                    raise Exception(f"RPC error: {result['error']}")
                return result["result"]
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def decode_log(log):
    """Extract maker, taker, makerAmount, takerAmount from OrderFilled log."""
    topics = log["topics"]
    data = log["data"][2:]  # strip 0x

    # topics[1] = orderHash (bytes32)
    # topics[2] = maker address (indexed)
    # topics[3] = taker address (indexed)
    maker = "0x" + topics[2][-40:]
    taker = "0x" + topics[3][-40:]

    # data words (each 32 bytes = 64 hex chars):
    # [0] = makerAssetId
    # [1] = takerAssetId
    # [2] = makerAmountFilled  ← USDC amount maker put in
    # [3] = takerAmountFilled  ← USDC amount taker put in
    # [4] = fee
    words = [data[i * 64:(i + 1) * 64] for i in range(len(data) // 64)]
    if len(words) < 4:
        return None

    maker_amount = int(words[2], 16) / USDC_DECIMALS
    taker_amount = int(words[3], 16) / USDC_DECIMALS
    fee = int(words[4], 16) / USDC_DECIMALS if len(words) > 4 else 0

    return {
        "maker": maker.lower(),
        "taker": taker.lower(),
        "maker_amount": maker_amount,
        "taker_amount": taker_amount,
        "fee": fee,
        "block": int(log["blockNumber"], 16),
        "tx": log["transactionHash"],
    }


def fetch_logs_range(from_block, to_block):
    """Fetch OrderFilled logs for a block range."""
    return rpc_call("eth_getLogs", [{
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
        "address": CTF_EXCHANGE,
        "topics": [ORDER_FILLED_TOPIC],
    }])


def enrich_with_polymarket_name(address):
    """Get display name from Polymarket data API."""
    try:
        url = f"https://data-api.polymarket.com/activity?user={address}&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.load(r)
        if data:
            return data[0].get("name") or data[0].get("pseudonym") or ""
        return ""
    except:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Polymarket Maker Scanner")
    parser.add_argument("--blocks", type=int, default=50000,
                        help="Number of recent blocks to scan (default: 50000 = ~1 day)")
    parser.add_argument("--min-volume", type=float, default=1000,
                        help="Minimum maker volume in USD (default: 1000)")
    parser.add_argument("--no-enrich", action="store_true",
                        help="Skip Polymarket name lookup (faster)")
    parser.add_argument("--output", type=str, default=None,
                        help="Save results to JSON file")
    args = parser.parse_args()

    print(f"🔍 Polymarket Maker Scanner")
    print(f"   Contract: {CTF_EXCHANGE}")
    print(f"   Blocks to scan: {args.blocks:,} (~{args.blocks/BLOCKS_PER_DAY:.1f} days)")
    print(f"   Min volume filter: ${args.min_volume:,.0f}")
    print()

    # Get latest block
    latest = int(rpc_call("eth_blockNumber", []), 16)
    from_block = latest - args.blocks
    print(f"   Block range: {from_block:,} → {latest:,}")
    print()

    # Scan in chunks
    makers = defaultdict(lambda: {
        "volume_as_maker": 0.0,
        "volume_as_taker": 0.0,
        "trade_count": 0,
        "fee_paid": 0.0,
        "markets": set(),
        "first_block": 99999999,
        "last_block": 0,
    })

    total_logs = 0
    chunk = from_block
    chunk_count = 0
    total_chunks = (args.blocks + MAX_BLOCKS_PER_REQUEST - 1) // MAX_BLOCKS_PER_REQUEST

    while chunk < latest:
        end = min(chunk + MAX_BLOCKS_PER_REQUEST - 1, latest)
        chunk_count += 1

        try:
            logs = fetch_logs_range(chunk, end)
            total_logs += len(logs)

            for log in logs:
                decoded = decode_log(log)
                if not decoded:
                    continue

                m = decoded["maker"]
                makers[m]["volume_as_maker"] += decoded["maker_amount"]
                makers[m]["trade_count"] += 1
                makers[m]["fee_paid"] += decoded["fee"]
                makers[m]["first_block"] = min(makers[m]["first_block"], decoded["block"])
                makers[m]["last_block"] = max(makers[m]["last_block"], decoded["block"])

                # Also track who is taker (for later analysis)
                t = decoded["taker"]
                makers[t]["volume_as_taker"] += decoded["taker_amount"]

            if chunk_count % 10 == 0 or chunk_count == total_chunks:
                pct = chunk_count / total_chunks * 100
                print(f"   Progress: {pct:.0f}% | chunks: {chunk_count}/{total_chunks} | "
                      f"logs: {total_logs:,} | unique makers: {len(makers):,}", flush=True)

        except Exception as e:
            print(f"   ⚠️  Error at block {chunk}: {e} — retrying...", flush=True)
            time.sleep(3)
            continue

        chunk = end + 1
        time.sleep(0.05)  # Be nice to RPC

    print(f"\n✅ Scan complete: {total_logs:,} fills | {len(makers):,} unique addresses")

    # Filter by maker volume
    qualified = {
        addr: data for addr, data in makers.items()
        if data["volume_as_maker"] >= args.min_volume
    }
    print(f"   Makers with ${args.min_volume:,.0f}+ volume: {len(qualified):,}")

    # Sort by maker volume
    sorted_makers = sorted(
        qualified.items(),
        key=lambda x: x[1]["volume_as_maker"],
        reverse=True
    )

    # Enrich with Polymarket names
    if not args.no_enrich:
        print(f"\n🔎 Fetching Polymarket names for top 100 makers...")
        for i, (addr, data) in enumerate(sorted_makers[:100]):
            name = enrich_with_polymarket_name(addr)
            data["name"] = name
            if (i + 1) % 10 == 0:
                print(f"   {i+1}/100 done...", flush=True)
            time.sleep(0.1)

    # Print leaderboard
    print(f"\n{'='*70}")
    print(f"{'MARKET MAKER LEADERBOARD':^70}")
    print(f"{'='*70}")
    print(f"{'#':<4} {'Address':<44} {'Maker Vol':>12} {'Trades':>8} {'Name'}")
    print(f"{'-'*70}")

    for rank, (addr, data) in enumerate(sorted_makers[:50], 1):
        name = data.get("name", "")
        print(f"{rank:<4} {addr:<44} ${data['volume_as_maker']:>10,.0f} "
              f"{data['trade_count']:>8,}  {name}")

    # Save results
    output_data = {
        "scan_info": {
            "from_block": from_block,
            "to_block": latest,
            "blocks_scanned": args.blocks,
            "total_fills": total_logs,
            "unique_addresses": len(makers),
            "qualified_makers": len(qualified),
        },
        "makers": [
            {
                "rank": rank,
                "address": addr,
                "volume_as_maker": round(data["volume_as_maker"], 2),
                "volume_as_taker": round(data["volume_as_taker"], 2),
                "trade_count": data["trade_count"],
                "fee_paid": round(data["fee_paid"], 4),
                "name": data.get("name", ""),
                "first_block": data["first_block"],
                "last_block": data["last_block"],
            }
            for rank, (addr, data) in enumerate(sorted_makers, 1)
        ]
    }

    output_file = args.output or f"/tmp/poly_makers_{from_block}_{latest}.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n💾 Saved to {output_file}")


if __name__ == "__main__":
    main()
