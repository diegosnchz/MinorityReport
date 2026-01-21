"""
Training module - Scripts for training OracleNet and related models
"""

from .train_oracle import train_oracle_net
from .train_graphsage_minibatch import train_graphsage_minibatch

__all__ = ["train_oracle_net", "train_graphsage_minibatch"]
