#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys, re, json, shlex
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
import numpy as np
import pandas as pd

ParamTuple = Tuple[Tuple[str, float], ...]

# --------- Error Analysis ---------
class ErrorAnalyzer:
    """Analyzes errors in sweep data where error = |y - x|"""
    
    def __init__(self, db: 'SweepDB'):
        self.db = db
        
    def calculate_series_error(self, params: ParamTuple) -> Dict[str, float]:
        """Calculate error statistics for a series"""
        if params not in self.db.series_by_params:
            raise KeyError(f"Parameters not found: {params}")
            
        sd = self.db.series_by_params[params]
        if sd.x.size == 0:
            return {"min_error": float('inf'), "max_error": float('inf'), 
                    "mean_error": float('inf'), "min_pct_error": float('inf')}
        
        # Calculate absolute errors: |y - x|
        abs_errors = np.abs(sd.y - sd.x)
        
        # Calculate percentage errors: |y - x| / |x| * 100 (avoid division by zero)
        pct_errors = np.where(sd.x != 0, (abs_errors / np.abs(sd.x)) * 100, np.inf)
        
        min_idx = np.argmin(abs_errors)
        min_pct_idx = np.argmin(pct_errors)
        
        return {
            "min_error": float(abs_errors[min_idx]),
            "min_error_x": float(sd.x[min_idx]),
            "min_error_y": float(sd.y[min_idx]),
            "max_error": float(np.max(abs_errors)),
            "mean_error": float(np.mean(abs_errors)),
            "min_pct_error": float(pct_errors[min_pct_idx]),
            "min_pct_error_x": float(sd.x[min_pct_idx]),
            "min_pct_error_y": float(sd.y[min_pct_idx]),
            "mean_pct_error": float(np.mean(pct_errors[np.isfinite(pct_errors)]))
        }
    
    def find_min_error_params(self, metric: str = "min_error") -> Tuple[ParamTuple, Dict[str, float]]:
        """Find parameter set with minimum error across all series"""
        best_params = None
        best_stats = None
        best_value = float('inf')
        
        for params in self.db.params_for_index:
            try:
                stats = self.calculate_series_error(params)
                if stats[metric] < best_value:
                    best_value = stats[metric]
                    best_params = params
                    best_stats = stats
            except Exception:
                continue
        
        if best_params is None:
            raise ValueError("No valid series found")
            
        return best_params, best_stats
    
    def filter_by_error_threshold(self, threshold: float, metric: str = "min_error",
                                  operator: str = "<=") -> List[Tuple[ParamTuple, Dict[str, float]]]:
        """Find all parameter sets within an error threshold"""
        results = []
        
        for params in self.db.params_for_index:
            try:
                stats = self.calculate_series_error(params)
                value = stats[metric]
                
                if operator == "<=":
                    matches = value <= threshold
                elif operator == "<":
                    matches = value < threshold
                elif operator == ">=":
                    matches = value >= threshold
                elif operator == ">":
                    matches = value > threshold
                elif operator == "==":
                    matches = abs(value - threshold) < 1e-10
                else:
                    raise ValueError(f"Unknown operator: {operator}")
                
                if matches:
                    results.append((params, stats))
            except Exception:
                continue
        
        return results

_param_block_re = re.compile(r"\((.*?)\)")
_xy_suffix_re   = re.compile(r"^(.*)\s([XY])$")

def _parse_params_from_header(header: str) -> ParamTuple:
    m = _param_block_re.search(header)
    if not m:
        return tuple()
    inner = m.group(1)
    pairs = []
    for piece in inner.split(","):
        piece = piece.strip()
        if not piece:
            continue
        k, v = piece.split("=", 1)
        pairs.append((k.strip(), float(v.strip())))
    return tuple(sorted(pairs, key=lambda kv: kv[0]))

def parse_params_string(s: str) -> ParamTuple:
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    pairs = []
    for piece in s.split(","):
        piece = piece.strip()
        if not piece:
            continue
        k, v = piece.split("=", 1)
        pairs.append((k.strip(), float(v.strip())))
    return tuple(sorted(pairs, key=lambda kv: kv[0]))

@dataclass
class SeriesData:
    params: ParamTuple
    x: np.ndarray
    y: np.ndarray

class SweepDB:
    def __init__(self, series: Dict[ParamTuple, SeriesData]):
        self.series_by_params: Dict[ParamTuple, SeriesData] = series
        ordered = sorted(self.series_by_params.keys())
        self.params_for_index: List[ParamTuple] = ordered
        self.index_for_params: Dict[ParamTuple, int] = {p: i for i, p in enumerate(ordered)}

    @classmethod
    def from_csv(cls, path: str, *, assume_sorted: bool = True, low_memory: bool = False) -> "SweepDB":
        df = pd.read_csv(path, low_memory=low_memory)
        groups: Dict[str, Dict[str, str]] = {}
        for col in df.columns:
            m = _xy_suffix_re.match(str(col).strip())
            if not m:
                continue
            stem, xy = m.group(1).strip(), m.group(2)
            groups.setdefault(stem, {})
            groups[stem][xy] = col

        series: Dict[ParamTuple, SeriesData] = {}
        for stem, parts in groups.items():
            if 'X' not in parts or 'Y' not in parts:
                continue
            params = _parse_params_from_header(stem)
            x = pd.to_numeric(df[parts['X']], errors="coerce").to_numpy()
            y = pd.to_numeric(df[parts['Y']], errors="coerce").to_numpy()
            mask = np.isfinite(x) & np.isfinite(y)
            x, y = x[mask], y[mask]
            if not assume_sorted or (x.size > 1 and np.any(np.diff(x) < 0)):
                idx = np.argsort(x)
                x, y = x[idx], y[idx]
            series[params] = SeriesData(params=params, x=x, y=y)

        if not series:
            print("warning: No (X,Y) pairs found. Headers must end with ' X' and ' Y'.", file=sys.stderr)
        return cls(series)

    @staticmethod
    def _closest_index(sorted_x: np.ndarray, xq: float) -> int:
        pos = np.searchsorted(sorted_x, xq)
        if pos == 0:
            return 0
        if pos >= sorted_x.size:
            return sorted_x.size - 1
        left, right = pos - 1, pos
        return right if abs(sorted_x[right] - xq) < abs(xq - sorted_x[left]) else left

    def list_series(self, limit: Optional[int] = None) -> List[Tuple[int, ParamTuple]]:
        items = [(self.index_for_params[p], p) for p in self.params_for_index]
        return items if limit is None else items[:limit]

    def query_closest_y(
        self, *, series_index: Optional[int] = None, params: Optional[ParamTuple] = None, x_query: float = 0.0
    ) -> Tuple[float, float, int, ParamTuple]:
        if (series_index is None) == (params is None):
            raise ValueError("Specify exactly one of --index or --params.")
        if params is not None:
            if params not in self.series_by_params:
                raise KeyError("Parameters not found.")
            sd = self.series_by_params[params]
        else:
            if series_index < 0 or series_index >= len(self.params_for_index):
                raise IndexError("Series index out of range.")
            sd = self.series_by_params[self.params_for_index[series_index]]  # type: ignore
            params = sd.params
        if sd.x.size == 0:
            raise ValueError("Selected series has no data.")
        i = self._closest_index(sd.x, float(x_query))
        return float(sd.x[i]), float(sd.y[i]), int(i), params  # type: ignore

# --------- Commands ---------
def cmd_list(db: SweepDB, _args: argparse.Namespace) -> None:
    if not db.params_for_index:
        print("No series available.")
        return
    for idx, p in db.list_series():
        print(f"{idx}\t" + ", ".join(f"{k}={v:g}" for k, v in p))

def cmd_show(db: SweepDB, args: argparse.Namespace) -> None:
    try:
        idx = args.index
        if idx < 0 or idx >= len(db.params_for_index):
            print("error: index out of range")
            return
        params = db.params_for_index[idx]
        sd = db.series_by_params[params]
        print("index:", idx)
        print("params:", ", ".join(f"{k}={v:g}" for k, v in params))
        print("length:", sd.x.size)
        if args.sample:
            n = min(args.sample, sd.x.size)
            print("head(x,y):")
            for i in range(n):
                print(f"  {sd.x[i]:.6g}\t{sd.y[i]:.6g}")
    except Exception as e:
        print(f"error: {e}")

def cmd_query(db: SweepDB, args: argparse.Namespace) -> None:
    try:
        if args.index is not None and args.x is None:
            print("error: --x is required when using --index")
            return
        if args.params is not None and args.x is None:
            print("error: --x is required when using --params")
            return
        if args.index is not None:
            xf, yf, i, p = db.query_closest_y(series_index=args.index, x_query=args.x)
        else:
            p = parse_params_string(args.params)
            xf, yf, i, p = db.query_closest_y(params=p, x_query=args.x)
        out = {"x_query": args.x, "x_found": xf, "y_found": yf, "row": i,
               "params": {k: v for k, v in p}}
        print(json.dumps(out, indent=2))
    except Exception as e:
        print(f"error: {e}")

def cmd_error(db: SweepDB, args: argparse.Namespace) -> None:
    """Show error statistics for a series"""
    analyzer = ErrorAnalyzer(db)
    try:
        if args.index is not None:
            if args.index < 0 or args.index >= len(db.params_for_index):
                print("error: index out of range")
                return
            params = db.params_for_index[args.index]
        else:
            params = parse_params_string(args.params)
        
        stats = analyzer.calculate_series_error(params)
        print(f"Parameters: {', '.join(f'{k}={v:g}' for k, v in params)}")
        print(f"Min Absolute Error: {stats['min_error']:.6e} at x={stats['min_error_x']:.6e}, y={stats['min_error_y']:.6e}")
        print(f"Min Percentage Error: {stats['min_pct_error']:.6f}% at x={stats['min_pct_error_x']:.6e}, y={stats['min_pct_error_y']:.6e}")
        print(f"Mean Absolute Error: {stats['mean_error']:.6e}")
        print(f"Mean Percentage Error: {stats['mean_pct_error']:.6f}%")
        print(f"Max Absolute Error: {stats['max_error']:.6e}")
    except Exception as e:
        print(f"error: {e}")

def cmd_min_error(db: SweepDB, args: argparse.Namespace) -> None:
    """Find parameters with minimum error"""
    analyzer = ErrorAnalyzer(db)
    metric = "min_pct_error" if args.percentage else "min_error"
    try:
        best_params, stats = analyzer.find_min_error_params(metric)
        print(f"Best parameters: {', '.join(f'{k}={v:g}' for k, v in best_params)}")
        print(f"Min Absolute Error: {stats['min_error']:.6e} at x={stats['min_error_x']:.6e}, y={stats['min_error_y']:.6e}")
        print(f"Min Percentage Error: {stats['min_pct_error']:.6f}% at x={stats['min_pct_error_x']:.6e}, y={stats['min_pct_error_y']:.6e}")
        print(f"Mean Absolute Error: {stats['mean_error']:.6e}")
        print(f"Mean Percentage Error: {stats['mean_pct_error']:.6f}%")
    except Exception as e:
        print(f"error: {e}")

def cmd_threshold(db: SweepDB, args: argparse.Namespace) -> None:
    """Find all parameters within error threshold"""
    pd.set_option('display.precision', 10)
    analyzer = ErrorAnalyzer(db)
    metric = "min_pct_error" if args.percentage else "min_error"
    operator = args.operator if args.operator else "<="
    try:
        results = analyzer.filter_by_error_threshold(args.threshold, metric, operator)
        print(f"Found {len(results)} series where {metric} {operator} {args.threshold}")
        for i, (params, stats) in enumerate(results[:args.limit if args.limit else len(results)], 1):
            print(f"{i}. {', '.join(f'{k}={v:g}' for k, v in params)}")
            print(f"{metric}: {stats[metric]:.6e}")
            print(f"min_pct_error: {stats['min_pct_error']:.6f}%")
            print(f"min_percent_error_x: {stats['min_pct_error_x']:.6e}")
            print(f"min_percent_error_y: {stats['min_pct_error_y']:.6e}")
            print("\n")
            if args.verbose:
                print(f"   Min Error: {stats['min_error']:.6e}, Min % Error: {stats['min_pct_error']:.6f}%")
    except Exception as e:
        print(f"error: {e}")


# --------- REPL ---------
def make_repl_parser() -> argparse.ArgumentParser:
    # exit_on_error=False prevents SystemExit on bad args
    subparser = argparse.ArgumentParser(prog="REPL", add_help=False, exit_on_error=False)
    subcmds = subparser.add_subparsers(dest="cmd")

    sp_list = subcmds.add_parser("list", add_help=False, exit_on_error=False)

    sp_show = subcmds.add_parser("show", add_help=False, exit_on_error=False)
    sp_show.add_argument("index", type=int)
    sp_show.add_argument("--sample", type=int, default=0)

    sp_query = subcmds.add_parser("query", add_help=False, exit_on_error=False)
    g = sp_query.add_mutually_exclusive_group(required=False)
    g.add_argument("--index", type=int)
    g.add_argument("--params", type=str)
    sp_query.add_argument("--x", type=float)

    sp_error = subcmds.add_parser("error", add_help=False, exit_on_error=False)
    ge = sp_error.add_mutually_exclusive_group(required=True)
    ge.add_argument("--index", type=int)
    ge.add_argument("--params", type=str)

    sp_min_error = subcmds.add_parser("min-error", add_help=False, exit_on_error=False)
    sp_min_error.add_argument("--percentage", "-p", action="store_true")

    sp_threshold = subcmds.add_parser("threshold", add_help=False, exit_on_error=False)
    sp_threshold.add_argument("value", type=float)
    sp_threshold.add_argument("--percentage", "-p", action="store_true")
    sp_threshold.add_argument("--operator", "-o", type=str, default="<=")
    sp_threshold.add_argument("--limit", "-l", type=int)
    sp_threshold.add_argument("--verbose", "-v", action="store_true")

    return subparser

def print_repl_help():
    print("Commands:")
    print("  list")
    print("  show <index> [--sample N]")
    print('  query --index <i> --x <val>')
    print('  query --params "k1=v1,k2=v2" --x <val>')
    print('  error --index <i>  OR  error --params "k1=v1,k2=v2"')
    print("  min-error [--percentage]")
    print("  threshold <value> [--percentage] [--operator <=] [--limit N] [--verbose]")
    print("  help, exit, quit")

def cmd_repl(db: SweepDB, _args: argparse.Namespace) -> None:
    print("Interactive mode.")
    print_repl_help()
    parser = make_repl_parser()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        low = line.lower()
        if low in {"exit", "quit"}:
            break
        if low in {"help", "h", "?"}:
            print_repl_help()
            continue

        argv = shlex.split(line)
        # Support `query --help` or `show --help` in REPL
        if len(argv) >= 2 and argv[1] in {"--help", "-h"}:
            if argv[0] == "query":
                print('query usage: query (--index I | --params "k=v,...") --x X')
            elif argv[0] == "show":
                print("show usage: show <index> [--sample N]")
            elif argv[0] == "list":
                print("list usage: list")
            else:
                print_repl_help()
            continue

        try:
            ns, unknown = parser.parse_known_args(argv)
            if unknown:
                print(f"warning: unknown args: {' '.join(unknown)}")
            if ns.cmd is None:
                print("error: command required. Type 'help' for options.")
                continue
            if ns.cmd == "list":
                cmd_list(db, ns)
            elif ns.cmd == "show":
                cmd_show(db, ns)
            elif ns.cmd == "query":
                # Validate required options in a friendly way
                if ns.index is None and ns.params is None:
                    print("error: provide --index or --params")
                    continue
                if ns.x is None:
                    print("error: --x is required")
                    continue
                cmd_query(db, ns)
            elif ns.cmd == "error":
                cmd_error(db, ns)
            elif ns.cmd == "min-error":
                cmd_min_error(db, ns)
            elif ns.cmd == "threshold":
                ns.threshold = ns.value  # Map positional arg to expected attr
                cmd_threshold(db, ns)
        except Exception as e:
            print(f"error: {e}")

# --------- Top-level CLI ---------
def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Sweep DB CLI: parse CSV with (X,Y) pairs keyed by parameter tuples and query via binary search.",
        exit_on_error=False
    )
    p.add_argument("csv")
    p.add_argument("--assume-sorted", action="store_true")
    p.add_argument("--low-memory", action="store_true")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("list", help="List all series with indices.", exit_on_error=False)
    p_show = sub.add_parser("show", help="Show info about a series.", exit_on_error=False)
    p_show.add_argument("index", type=int)
    p_show.add_argument("--sample", type=int, default=10)

    p_query = sub.add_parser("query", help="Query closest y for x.", exit_on_error=False)
    g = p_query.add_mutually_exclusive_group(required=False)
    g.add_argument("--index", type=int)
    g.add_argument("--params", type=str)
    p_query.add_argument("--x", type=float)

    p_error = sub.add_parser("error", help="Show error statistics for a series.", exit_on_error=False)
    ge = p_error.add_mutually_exclusive_group(required=True)
    ge.add_argument("--index", type=int)
    ge.add_argument("--params", type=str)

    p_min_error = sub.add_parser("min-error", help="Find parameters with minimum error.", exit_on_error=False)
    p_min_error.add_argument("--percentage", "-p", action="store_true", help="Use percentage error")

    p_threshold = sub.add_parser("threshold", help="Find all series within error threshold.", exit_on_error=False)
    p_threshold.add_argument("threshold", type=float, help="Error threshold value")
    p_threshold.add_argument("--percentage", "-p", action="store_true", help="Use percentage error")
    p_threshold.add_argument("--operator", "-o", type=str, default="<=", help="Comparison operator")
    p_threshold.add_argument("--limit", "-l", type=int, help="Limit number of results")
    p_threshold.add_argument("--verbose", "-v", action="store_true", help="Show detailed stats")

    sub.add_parser("repl", help="Interactive shell.", exit_on_error=False)
    return p

def main(argv: List[str]) -> None:
    parser = build_argparser()
    try:
        args, unknown = parser.parse_known_args(argv[1:])
        if unknown:
            print(f"warning: unknown args: {' '.join(unknown)}", file=sys.stderr)
    except Exception as e:
        print(f"warning: {e}. Starting interactive mode.", file=sys.stderr)
        # Fall back to REPL without exiting
        args = argparse.Namespace(csv=None, command="repl", assume_sorted=True, low_memory=False)

    if not getattr(args, "csv", None):
        print("error: CSV path is required. Example: query_database.py data/data2.csv", file=sys.stderr)
        return

    try:
        db = SweepDB.from_csv(args.csv, assume_sorted=args.assume_sorted, low_memory=args.low_memory)
    except Exception as e:
        print(f"error loading CSV: {e}")
        return

    try:
        if args.command == "list":
            cmd_list(db, args)
        elif args.command == "show":
            cmd_show(db, args)
        elif args.command == "query":
            # Friendly validation
            if args.index is None and args.params is None:
                print("error: provide --index or --params")
                return
            if args.x is None:
                print("error: --x is required")
                return
            cmd_query(db, args)
        elif args.command == "error":
            cmd_error(db, args)
        elif args.command == "min-error":
            cmd_min_error(db, args)
        elif args.command == "threshold":
            cmd_threshold(db, args)
        else:
            # default to REPL
            cmd_repl(db, args)
    except Exception as e:
        print(f"error: {e}")

if __name__ == "__main__":
    main(sys.argv)
