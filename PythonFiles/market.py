from datetime import datetime
from dataclasses import dataclass

@dataclass
class Market():
    
    spot : float
    volatility : float
    rate : float
    dividende : float = 0
    div_date : datetime = None