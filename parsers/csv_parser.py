"""
CSV parser for Cadence simulation data.
Handles the complex format with repeating X,Y column pairs containing sweep parameters.
"""
import csv
import re
from typing import Dict, List, Tuple, Any
import numpy as np


class CadenceCSVParser:
    """
    Parser for Cadence simulation CSV files with sweep parameters.
    
    CSV Format:
    - Headers contain signal path and sweep parameters: "/I4/Out (Nm_In_W=2.4e-07,Nm_Out_W=2.4e-07) X"
    - Columns come in X,Y pairs
    - Each pair represents a different sweep configuration
    """
    
    def __init__(self, csv_path: str):
        """
        Initialize parser with CSV file path.
        
        Args:
            csv_path: Path to CSV file
        """
        self.csv_path = csv_path
        self.headers = []
        self.data = []
        
    def parse(self) -> Dict[str, Any]:
        """
        Parse the CSV file and extract structured data.
        
        Returns:
            Dictionary containing:
                - sweep_params: List of sweep parameter names
                - data_series: List of dictionaries, each containing:
                    - signal_path: Signal path (e.g., '/I4/Out')
                    - sweep_values: Dict of parameter names to values
                    - x_values: List of X values
                    - y_values: List of Y values
        """
        # Read CSV file
        with open(self.csv_path, 'r') as f:
            reader = csv.reader(f)
            self.headers = next(reader)
            self.data = list(reader)
        
        # Parse headers to extract sweep information
        parsed_headers = self._parse_headers()
        
        # Extract all unique sweep parameter names
        sweep_params = set()
        for header_info in parsed_headers:
            if header_info['sweep_params']:
                sweep_params.update(header_info['sweep_params'].keys())
        
        # Organize data by series
        data_series = []
        for i in range(0, len(parsed_headers), 2):
            if i + 1 >= len(parsed_headers):
                break
                
            x_header = parsed_headers[i]
            y_header = parsed_headers[i + 1]
            
            # Verify this is an X,Y pair
            if x_header['axis'] != 'X' or y_header['axis'] != 'Y':
                continue
            
            # Extract data values
            x_values = self._extract_column(i)
            y_values = self._extract_column(i + 1)
            
            series = {
                'signal_path': x_header['signal_path'],
                'sweep_values': x_header['sweep_params'],
                'x_values': x_values,
                'y_values': y_values
            }
            data_series.append(series)
        
        return {
            'sweep_params': list(sweep_params),
            'data_series': data_series
        }
    
    def _parse_headers(self) -> List[Dict[str, Any]]:
        """
        Parse column headers to extract signal path, sweep parameters, and axis.
        
        Example header: "/I4/Out (Nm_In_W=2.4e-07,Nm_Out_W=2.4e-07) X"
        
        Returns:
            List of dictionaries with parsed header information
        """
        parsed = []
        
        for header in self.headers:
            # Pattern: signal_path (param1=value1,param2=value2,...) axis
            pattern = r'([^\(]+)\s*\(([^\)]*)\)\s*([XY])'
            match = re.match(pattern, header.strip())
            
            if match:
                signal_path = match.group(1).strip()
                params_str = match.group(2).strip()
                axis = match.group(3).strip()
                
                # Parse sweep parameters
                sweep_params = {}
                if params_str:
                    param_pairs = params_str.split(',')
                    for pair in param_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            try:
                                sweep_params[name.strip()] = float(value.strip())
                            except ValueError:
                                sweep_params[name.strip()] = value.strip()
                
                parsed.append({
                    'signal_path': signal_path,
                    'sweep_params': sweep_params,
                    'axis': axis
                })
            else:
                # Simple header without sweep params
                parsed.append({
                    'signal_path': header.strip(),
                    'sweep_params': {},
                    'axis': None
                })
        
        return parsed
    
    def _extract_column(self, col_index: int) -> List[float]:
        """
        Extract data from a specific column.
        
        Args:
            col_index: Column index
            
        Returns:
            List of float values
        """
        values = []
        for row in self.data:
            if col_index < len(row):
                try:
                    value = float(row[col_index])
                    values.append(value)
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    pass
        return values
    
    def calculate_error_percentage(self, x_values: List[float], y_values: List[float], 
                                   expected_ratio: float = 1.0) -> float:
        """
        Calculate average percentage error between Y and X values.
        
        For current mirrors, we expect Y/X ≈ expected_ratio (typically 1.0 for 1:1 mirror)
        
        Args:
            x_values: Input values (e.g., input current)
            y_values: Output values (e.g., output current)
            expected_ratio: Expected Y/X ratio
            
        Returns:
            Average percentage error
        """
        if not x_values or not y_values or len(x_values) != len(y_values):
            return float('inf')
        
        errors = []
        for x, y in zip(x_values, y_values):
            if x != 0:
                expected_y = x * expected_ratio
                error = abs(y - expected_y) / expected_y * 100
                errors.append(error)
        
        return np.mean(errors) if errors else float('inf')
    
    def calculate_gain(self, x_values: List[float], y_values: List[float]) -> float:
        """
        Calculate gain (Y/X ratio).
        
        Args:
            x_values: Input values
            y_values: Output values
            
        Returns:
            Average gain
        """
        if not x_values or not y_values or len(x_values) != len(y_values):
            return 0.0
        
        gains = []
        for x, y in zip(x_values, y_values):
            if x != 0:
                gains.append(y / x)
        
        return np.mean(gains) if gains else 0.0
