#!/usr/bin/env python3
"""
Enhanced Query Database with Error Search Capabilities
Searches for:
1. Minimum percentage error for given parameters
2. All parameter sets within an error threshold
"""
from __future__ import annotations
import argparse, sys
from typing import Dict, Tuple, List, Optional
import numpy as np
from query_database import SweepDB, ParamTuple, parse_params_string

class ErrorAnalyzer:
    """Analyzes errors in sweep data where error = |y - x|"""
    
    def __init__(self, db: SweepDB):
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
        """Find parameter set with minimum error across all series
        
        Args:
            metric: 'min_error' for absolute error, 'min_pct_error' for percentage error
        """
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
            except Exception as e:
                print(f"Warning: Error processing {params}: {e}", file=sys.stderr)
                continue
        
        if best_params is None:
            raise ValueError("No valid series found")
            
        return best_params, best_stats
    
    def filter_by_error_threshold(self, 
                                  threshold: float, 
                                  metric: str = "min_error",
                                  operator: str = "<=") -> List[Tuple[ParamTuple, Dict[str, float]]]:
        """Find all parameter sets within an error threshold
        
        Args:
            threshold: Error threshold value
            metric: Which error metric to use ('min_error', 'min_pct_error', 'mean_error', etc.)
            operator: Comparison operator ('<=', '<', '>=', '>', '==')
        """
        results = []
        
        for params in self.db.params_for_index:
            try:
                stats = self.calculate_series_error(params)
                value = stats[metric]
                
                # Apply operator
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
            except Exception as e:
                print(f"Warning: Error processing {params}: {e}", file=sys.stderr)
                continue
        
        return results
    
    def search_by_param_value(self, param_name: str, param_value: float, 
                             tolerance: float = 1e-10) -> List[Tuple[ParamTuple, Dict[str, float]]]:
        """Find all series with a specific parameter value
        
        Args:
            param_name: Name of the parameter to search for
            param_value: Value to match
            tolerance: Tolerance for floating point comparison
        """
        results = []
        
        for params in self.db.params_for_index:
            param_dict = dict(params)
            if param_name in param_dict:
                if abs(param_dict[param_name] - param_value) <= tolerance:
                    try:
                        stats = self.calculate_series_error(params)
                        results.append((params, stats))
                    except Exception as e:
                        print(f"Warning: Error processing {params}: {e}", file=sys.stderr)
                        continue
        
        return results


def print_params(params: ParamTuple) -> str:
    """Format parameters for display"""
    return ", ".join(f"{k}={v:.6g}" for k, v in params)


def print_stats(stats: Dict[str, float]) -> None:
    """Pretty print error statistics"""
    print(f"  Min Absolute Error: {stats['min_error']:.6e}")
    print(f"    at x={stats['min_error_x']:.6e}, y={stats['min_error_y']:.6e}")
    print(f"  Min Percentage Error: {stats['min_pct_error']:.6f}%")
    print(f"    at x={stats['min_pct_error_x']:.6e}, y={stats['min_pct_error_y']:.6e}")
    print(f"  Mean Absolute Error: {stats['mean_error']:.6e}")
    print(f"  Mean Percentage Error: {stats['mean_pct_error']:.6f}%")
    print(f"  Max Absolute Error: {stats['max_error']:.6e}")


def cmd_min_error(analyzer: ErrorAnalyzer, args: argparse.Namespace) -> None:
    """Find parameters with minimum error"""
    metric = "min_pct_error" if args.percentage else "min_error"
    print(f"Searching for minimum {metric}...")
    
    try:
        best_params, best_stats = analyzer.find_min_error_params(metric)
        print(f"\nBest parameters: {print_params(best_params)}")
        print_stats(best_stats)
    except Exception as e:
        print(f"Error: {e}")


def cmd_threshold(analyzer: ErrorAnalyzer, args: argparse.Namespace) -> None:
    """Find all parameters within error threshold"""
    metric = "min_pct_error" if args.percentage else "min_error"
    operator = args.operator if args.operator else "<="
    
    print(f"Searching for series where {metric} {operator} {args.threshold}...")
    
    try:
        results = analyzer.filter_by_error_threshold(args.threshold, metric, operator)
        
        if not results:
            print("No series found matching criteria.")
            return
        
        print(f"\nFound {len(results)} series:")
        for i, (params, stats) in enumerate(results, 1):
            print(f"\n{i}. {print_params(params)}")
            if args.verbose:
                print_stats(stats)
            else:
                print(f"   {metric}: {stats[metric]:.6e}" if not args.percentage 
                      else f"   {metric}: {stats[metric]:.6f}%")
    except Exception as e:
        print(f"Error: {e}")


def cmd_param_search(analyzer: ErrorAnalyzer, args: argparse.Namespace) -> None:
    """Search for specific parameter value"""
    print(f"Searching for series with {args.param_name}={args.param_value}...")
    
    try:
        results = analyzer.search_by_param_value(args.param_name, args.param_value, 
                                                tolerance=args.tolerance if args.tolerance else 1e-10)
        
        if not results:
            print(f"No series found with {args.param_name}={args.param_value}")
            return
        
        print(f"\nFound {len(results)} series:")
        for i, (params, stats) in enumerate(results, 1):
            print(f"\n{i}. {print_params(params)}")
            if args.verbose:
                print_stats(stats)
            else:
                print(f"   Min Error: {stats['min_error']:.6e}, Min % Error: {stats['min_pct_error']:.6f}%")
    except Exception as e:
        print(f"Error: {e}")


def cmd_compare(analyzer: ErrorAnalyzer, args: argparse.Namespace) -> None:
    """Compare error statistics for specific parameter sets"""
    params_list = [parse_params_string(p) for p in args.params]
    
    print(f"Comparing {len(params_list)} parameter sets...\n")
    
    for i, params in enumerate(params_list, 1):
        print(f"{i}. {print_params(params)}")
        try:
            stats = analyzer.calculate_series_error(params)
            print_stats(stats)
        except Exception as e:
            print(f"   Error: {e}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced query tool with error analysis capabilities"
    )
    parser.add_argument("csv", help="Path to CSV file")
    parser.add_argument("--assume-sorted", action="store_true", help="Assume data is sorted")
    parser.add_argument("--low-memory", action="store_true", help="Use low memory mode")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # min-error command
    p_min = subparsers.add_parser("min-error", help="Find parameters with minimum error")
    p_min.add_argument("--percentage", "-p", action="store_true", 
                      help="Use percentage error instead of absolute")
    
    # threshold command
    p_thresh = subparsers.add_parser("threshold", help="Find all series within error threshold")
    p_thresh.add_argument("threshold", type=float, help="Error threshold value")
    p_thresh.add_argument("--percentage", "-p", action="store_true",
                         help="Use percentage error")
    p_thresh.add_argument("--operator", "-o", choices=["<=", "<", ">=", ">", "=="],
                         help="Comparison operator (default: <=)")
    p_thresh.add_argument("--verbose", "-v", action="store_true",
                         help="Show detailed statistics")
    
    # param-search command
    p_param = subparsers.add_parser("param-search", help="Search by parameter value")
    p_param.add_argument("param_name", help="Parameter name (e.g., 'Nm_In_W')")
    p_param.add_argument("param_value", type=float, help="Parameter value to search for")
    p_param.add_argument("--tolerance", "-t", type=float, help="Tolerance for comparison")
    p_param.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed statistics")
    
    # compare command
    p_comp = subparsers.add_parser("compare", help="Compare error stats for specific parameter sets")
    p_comp.add_argument("params", nargs="+", 
                       help='Parameter sets in format "k1=v1,k2=v2"')
    
    args = parser.parse_args()
    
    # Load database
    print(f"Loading database from {args.csv}...")
    try:
        db = SweepDB.from_csv(args.csv, assume_sorted=args.assume_sorted, 
                             low_memory=args.low_memory)
        print(f"Loaded {len(db.params_for_index)} series.")
    except Exception as e:
        print(f"Error loading database: {e}")
        return 1
    
    analyzer = ErrorAnalyzer(db)
    
    # Execute command
    try:
        if args.command == "min-error":
            cmd_min_error(analyzer, args)
        elif args.command == "threshold":
            cmd_threshold(analyzer, args)
        elif args.command == "param-search":
            cmd_param_search(analyzer, args)
        elif args.command == "compare":
            cmd_compare(analyzer, args)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
