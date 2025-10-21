"""
Data ingestion module for importing simulation data into the database.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from database import (
    get_database,
    Simulation,
    Category,
    SimulationParameter,
    SweepConfiguration,
    SweepValue,
    DataSeries,
    DataSeriesSweepParam,
    DataPoint,
    OptimizationMetric
)
from parsers import CadenceCSVParser


class SimulationImporter:
    """
    Import simulation data from CSV files into the database.
    """
    
    def __init__(self):
        """Initialize the importer."""
        self.db = get_database()
    
    def import_from_csv(
        self,
        csv_path: str,
        simulation_name: str,
        circuit_name: str,
        description: str = "",
        categories: List[str] = None,
        fixed_parameters: Dict[str, tuple] = None,
        assumptions: Dict[str, float] = None,
        calculate_metrics: bool = True
    ) -> Simulation:
        """
        Import simulation data from a Cadence CSV file.
        
        Args:
            csv_path: Path to CSV file
            simulation_name: Descriptive name for the simulation
            circuit_name: Name of the circuit being simulated
            description: Detailed description of the simulation
            categories: List of category names to assign
            fixed_parameters: Dict of parameter name -> (value, unit)
            assumptions: Dict of assumption values (vdd, vt, temperature)
            calculate_metrics: Whether to calculate optimization metrics
            
        Returns:
            Dictionary with simulation info (id, name, circuit_name, description)
        """
        # Parse CSV
        parser = CadenceCSVParser(csv_path)
        parsed_data = parser.parse()
        
        # Create session
        with self.db.get_session() as session:
            # Create simulation record
            simulation = Simulation(
                name=simulation_name,
                circuit_name=circuit_name,
                description=description,
                created_at=datetime.utcnow()
            )
            
            # Add assumptions
            if assumptions:
                simulation.vdd = assumptions.get('vdd')
                simulation.vt = assumptions.get('vt')
                simulation.temperature = assumptions.get('temperature')
            
            session.add(simulation)
            session.flush()  # Get simulation ID
            
            # Add categories
            if categories:
                for cat_name in categories:
                    category = session.query(Category).filter_by(name=cat_name).first()
                    if not category:
                        category = Category(name=cat_name)
                        session.add(category)
                    simulation.categories.append(category)
            
            # Add fixed parameters
            if fixed_parameters:
                for param_name, (param_value, unit) in fixed_parameters.items():
                    param = SimulationParameter(
                        simulation_id=simulation.id,
                        parameter_name=param_name,
                        parameter_value=param_value,
                        unit=unit
                    )
                    session.add(param)
            
            # Add sweep configurations
            sweep_configs = {}
            for param_name in parsed_data['sweep_params']:
                sweep_config = SweepConfiguration(
                    simulation_id=simulation.id,
                    parameter_name=param_name
                )
                session.add(sweep_config)
                session.flush()
                sweep_configs[param_name] = sweep_config
                
                # Collect all unique values for this parameter
                unique_values = set()
                for series in parsed_data['data_series']:
                    if param_name in series['sweep_values']:
                        unique_values.add(series['sweep_values'][param_name])
                
                # Add sweep values
                for value in sorted(unique_values):
                    sweep_value = SweepValue(
                        sweep_config_id=sweep_config.id,
                        value=value
                    )
                    session.add(sweep_value)
            
            # Add data series and points
            for series_data in parsed_data['data_series']:
                data_series = DataSeries(
                    simulation_id=simulation.id,
                    signal_path=series_data['signal_path']
                )
                session.add(data_series)
                session.flush()
                
                # Add sweep parameter values for this series
                for param_name, param_value in series_data['sweep_values'].items():
                    sweep_param = DataSeriesSweepParam(
                        data_series_id=data_series.id,
                        parameter_name=param_name,
                        parameter_value=param_value
                    )
                    session.add(sweep_param)
                
                # Add data points
                x_values = series_data['x_values']
                y_values = series_data['y_values']
                
                for seq, (x, y) in enumerate(zip(x_values, y_values)):
                    point = DataPoint(
                        data_series_id=data_series.id,
                        x_value=x,
                        y_value=y,
                        sequence=seq
                    )
                    session.add(point)
                
                # Calculate metrics for this series
                if calculate_metrics and x_values and y_values:
                    # Error percentage (for current mirrors)
                    error_pct = parser.calculate_error_percentage(x_values, y_values)
                    if error_pct != float('inf'):
                        metric = OptimizationMetric(
                            simulation_id=simulation.id,
                            data_series_id=data_series.id,
                            metric_name='error_percentage',
                            metric_value=error_pct,
                            unit='%'
                        )
                        session.add(metric)
                    
                    # Gain
                    gain = parser.calculate_gain(x_values, y_values)
                    metric = OptimizationMetric(
                        simulation_id=simulation.id,
                        data_series_id=data_series.id,
                        metric_name='gain',
                        metric_value=gain,
                        unit='ratio'
                    )
                    session.add(metric)
            
            session.commit()
            
            # Get a simple dict with the simulation info before closing session
            result = {
                'id': simulation.id,
                'name': simulation.name,
                'circuit_name': simulation.circuit_name,
                'description': simulation.description
            }
            
        return result
    
    def add_category(self, name: str, description: str = "") -> Category:
        """
        Add a new category.
        
        Args:
            name: Category name
            description: Category description
            
        Returns:
            Created Category object
        """
        with self.db.get_session() as session:
            category = Category(name=name, description=description)
            session.add(category)
            session.commit()
            session.refresh(category)
            return category
    
    def assign_category(self, simulation_id: int, category_name: str):
        """
        Assign a category to a simulation.
        
        Args:
            simulation_id: Simulation ID
            category_name: Category name
        """
        with self.db.get_session() as session:
            simulation = session.query(Simulation).get(simulation_id)
            if not simulation:
                raise ValueError(f"Simulation {simulation_id} not found")
            
            category = session.query(Category).filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                session.add(category)
            
            if category not in simulation.categories:
                simulation.categories.append(category)
            
            session.commit()
