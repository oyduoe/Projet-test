from math import log, sqrt, exp
from datetime import datetime
from scipy.stats import norm
from abc import ABC
import numpy as np
from dataclasses import dataclass, field

@dataclass
class Option(ABC):
        
    strike : float
    time_to_maturity : float
    start_date : datetime = None

    def d1(self, market) -> float:
        spot_adjusted = market.spot - market.dividende
        return (log(spot_adjusted/self.strike) + self.time_to_maturity * (market.rate + (pow(market.volatility, 2)/2)))/(market.volatility * sqrt(self.time_to_maturity))

    def d2(self, market) -> float:
        return self.d1(market) - market.volatility*sqrt(self.time_to_maturity)
    
    def compute_price(self,market, n_sim=100000):
        Z = np.random.normal(0, 1, n_sim)
        prices = market.spot * np.exp(
            (market.rate - 0.5 * pow(market.volatility, 2)) * self.time_to_maturity +
            market.volatility * np.sqrt(self.time_to_maturity) * Z
        )
        payoffs=np.array([self.payoff(S) for S in prices])
        return exp(-market.rate*self.time_to_maturity) * np.mean(payoffs)

@dataclass
class CallOption(Option):
    
    def payoff(self, price : float) -> float:
        return max(0, (price - self.strike))

@dataclass   
class PutOption(Option):
    def payoff(self, price : float) -> float:
        return max(0, (self.strike - price))

@dataclass 
class EuropeanCallOption(CallOption):
    
    def compute_price(self, market) -> float:
        spot_adjusted = market.spot - market.dividende
        return spot_adjusted * norm.cdf(self.d1(market)) - self.strike * exp(-market.rate*self.time_to_maturity)*norm.cdf(self.d2(market))

@dataclass
class EuropeanPutOption(PutOption):
    
    def compute_price(self, market):
        spot_adjusted = market.spot - market.dividende
        return -spot_adjusted * norm.cdf(-self.d1(market)) + self.strike * exp(-market.rate*self.time_to_maturity)*norm.cdf(-self.d2(market))

class AmericanCallOption(CallOption):
    pass

class AmericanPutOption(PutOption):
    pass
 
@dataclass
class BermudeanCallOption(CallOption):
    exercise_dates : list[datetime] = field(default_factory=list)

@dataclass
class BermudeanPutOption(PutOption):
    exercise_dates : list[datetime] = field(default_factory=list)

@dataclass
class DigitalCallOption(Option):
    coupon : float = 1

    def payoff(self, price : float) -> float:
        if price > self.strike:
            return self.coupon
        else:
            return 0
        
@dataclass
class DigitalPutOption(Option):
    coupon : float = 1

    def payoff(self, price : float) -> float:
        if price < self.strike:
            return self.coupon
        else:
            return 0
    