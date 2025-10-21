"""
Database models for storing Cadence circuit simulation data.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between simulations and categories
simulation_categories = Table(
    'simulation_categories',
    Base.metadata,
    Column('simulation_id', Integer, ForeignKey('simulations.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)


class Simulation(Base):
    """
    Main simulation record containing metadata about a circuit simulation run.
    """
    __tablename__ = 'simulations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    circuit_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Simulation assumptions
    vdd = Column(Float)  # Supply voltage
    vt = Column(Float)   # Threshold voltage
    temperature = Column(Float)
    
    # Relationships
    parameters = relationship("SimulationParameter", back_populates="simulation", cascade="all, delete-orphan")
    sweep_configs = relationship("SweepConfiguration", back_populates="simulation", cascade="all, delete-orphan")
    data_series = relationship("DataSeries", back_populates="simulation", cascade="all, delete-orphan")
    optimization_metrics = relationship("OptimizationMetric", back_populates="simulation", cascade="all, delete-orphan")
    categories = relationship("Category", secondary=simulation_categories, back_populates="simulations")
    
    def __repr__(self):
        return f"<Simulation(name='{self.name}', circuit='{self.circuit_name}')>"


class Category(Base):
    """
    Categories for organizing simulations.
    """
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # Relationships
    simulations = relationship("Simulation", secondary=simulation_categories, back_populates="categories")
    
    def __repr__(self):
        return f"<Category(name='{self.name}')>"


class SimulationParameter(Base):
    """
    Fixed parameters for a simulation (e.g., Iref=100uA, Vov=0.2V, L=540n).
    """
    __tablename__ = 'simulation_parameters'
    
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'), nullable=False)
    parameter_name = Column(String(100), nullable=False, index=True)
    parameter_value = Column(Float, nullable=False)
    unit = Column(String(20))  # e.g., 'uA', 'V', 'nm'
    
    # Relationships
    simulation = relationship("Simulation", back_populates="parameters")
    
    def __repr__(self):
        return f"<SimulationParameter(name='{self.parameter_name}', value={self.parameter_value} {self.unit})>"


class SweepConfiguration(Base):
    """
    Configuration for swept parameters in a simulation.
    Each sweep parameter can have multiple values.
    """
    __tablename__ = 'sweep_configurations'
    
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'), nullable=False)
    parameter_name = Column(String(100), nullable=False, index=True)  # e.g., 'Nm_In_W', 'Nm_Out_W'
    
    # Relationships
    simulation = relationship("Simulation", back_populates="sweep_configs")
    values = relationship("SweepValue", back_populates="sweep_config", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SweepConfiguration(parameter='{self.parameter_name}')>"


class SweepValue(Base):
    """
    Individual values for a swept parameter.
    """
    __tablename__ = 'sweep_values'
    
    id = Column(Integer, primary_key=True)
    sweep_config_id = Column(Integer, ForeignKey('sweep_configurations.id'), nullable=False)
    value = Column(Float, nullable=False)
    
    # Relationships
    sweep_config = relationship("SweepConfiguration", back_populates="values")
    
    def __repr__(self):
        return f"<SweepValue(value={self.value})>"


class DataSeries(Base):
    """
    A series of data points for a specific combination of sweep parameters.
    Represents one X,Y column pair in the CSV.
    """
    __tablename__ = 'data_series'
    
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'), nullable=False)
    signal_path = Column(String(255), nullable=False)  # e.g., '/I4/Out'
    
    # Relationships
    simulation = relationship("Simulation", back_populates="data_series")
    sweep_params = relationship("DataSeriesSweepParam", back_populates="data_series", cascade="all, delete-orphan")
    data_points = relationship("DataPoint", back_populates="data_series", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DataSeries(signal='{self.signal_path}')>"


class DataSeriesSweepParam(Base):
    """
    Links a data series to its specific sweep parameter values.
    """
    __tablename__ = 'data_series_sweep_params'
    
    id = Column(Integer, primary_key=True)
    data_series_id = Column(Integer, ForeignKey('data_series.id'), nullable=False)
    parameter_name = Column(String(100), nullable=False)  # e.g., 'Nm_In_W'
    parameter_value = Column(Float, nullable=False)
    
    # Relationships
    data_series = relationship("DataSeries", back_populates="sweep_params")
    
    def __repr__(self):
        return f"<DataSeriesSweepParam(name='{self.parameter_name}', value={self.parameter_value})>"


class DataPoint(Base):
    """
    Individual data points in a series.
    X is typically input (e.g., input current), Y is output (e.g., output current).
    """
    __tablename__ = 'data_points'
    
    id = Column(Integer, primary_key=True)
    data_series_id = Column(Integer, ForeignKey('data_series.id'), nullable=False, index=True)
    x_value = Column(Float, nullable=False)
    y_value = Column(Float, nullable=False)
    sequence = Column(Integer)  # To maintain order of points
    
    # Relationships
    data_series = relationship("DataSeries", back_populates="data_points")
    
    def __repr__(self):
        return f"<DataPoint(x={self.x_value}, y={self.y_value})>"


class OptimizationMetric(Base):
    """
    Calculated optimization metrics for a simulation or data series.
    E.g., percentage error, gain, bandwidth, etc.
    """
    __tablename__ = 'optimization_metrics'
    
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'), nullable=False, index=True)
    data_series_id = Column(Integer, ForeignKey('data_series.id'), nullable=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)  # e.g., 'error_percentage', 'gain_db'
    metric_value = Column(Float, nullable=False, index=True)
    unit = Column(String(20))
    
    # Relationships
    simulation = relationship("Simulation", back_populates="optimization_metrics")
    
    def __repr__(self):
        return f"<OptimizationMetric(name='{self.metric_name}', value={self.metric_value})>"
