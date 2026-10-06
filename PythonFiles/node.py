from math import exp
from dataclasses import dataclass
from PythonFiles.market import Market

@dataclass
class Node():

    price : float
    payoff : float = None
    
    next_up : 'Node' = None
    next_mid : 'Node' = None
    next_down : 'Node' = None
    up_node : 'Node' = None
    down_node : 'Node' = None
    prec_node : 'Node' = None

    p_down : float = None
    p_up : float = None
    p_mid : float = None

    node_proba : float = 0
    
    def branch_triplet(self) -> None:
        '''
        Branche les noeuds fils de la node après la création du triplet
        '''
        self.next_mid.down_node = self.next_down
        self.next_mid.up_node = self.next_up
        self.next_up.down_node = self.next_mid
        self.next_down.up_node = self.next_mid
        self.next_mid.prec_node = self

    def compute_transition_proba(self, alpha : float, time_delta : int, market : Market, is_div : bool, dividende : float) -> None:
        '''
        Calcule les probabilités de transition de la node
        '''
        forward = self.next_mid.price
        if is_div:
             expectation = self.price * exp(market.rate * time_delta) - dividende
        else :
            expectation = self.next_mid.price
        
        variance = pow(self.price,2) * exp(2 * market.rate * time_delta) * (exp(pow(market.volatility, 2) * time_delta) -1) 
        
        self.p_down = ((pow(forward,-2) * (variance + pow(expectation,2)))- 1 - ((alpha+1) * ((pow(forward, -1)*expectation)-1))) / ((1 - alpha) * (pow(alpha,-2) - 1))
        self.p_up = ((pow(forward,-1)*expectation)-1-((alpha**(-1)-1)*self.p_down))/(alpha-1)
        self.p_mid = 1 - self.p_down - self.p_up

    def branch_monomial(self) -> None:
        '''
        Réalise le branchement monomial de la node s'il y a prunning
        '''
        self.p_mid = 1.0
        self.p_down = 0.0
        self.p_up = 0.0
        self.next_mid.node_proba += self.node_proba * self.p_mid

    def update_proba(self):
        '''
        Calcule les probabilités d'existance des nodes fils de la node
        '''
        self.next_up.node_proba = self.next_up.node_proba + self.node_proba * self.p_up
        self.next_mid.node_proba = self.next_mid.node_proba + self.node_proba * self.p_mid
        self.next_down.node_proba = self.next_down.node_proba + self.node_proba * self.p_down

    def node_payoff(self, step : int, option, exercise_steps : list[int], rate : float, time_delta : float) -> None:
        '''
        Calcule le payoff du noeud en fonction du type d'exercice 
        ''' 
        #Calcul de chaque prix suivant multiplié par la proba de transition
        value_up = self.next_up.payoff * self.p_up if self.next_up is not None else 0
        value_down = self.next_down.payoff * self.p_down if self.next_down is not None else 0
        value_mid = self.next_mid.payoff * self.p_mid if self.next_mid is not None else 0

        #Prix retropropagé de l'option : moyenne pondérée par les proba actualisée
        expectation = value_up + value_down + value_mid
        retro_payoff = expectation * exp(-rate * time_delta)

        #Exercice américain, on regarde s'il est avantageux d'exercer à ce timeStep
        if step in exercise_steps:
            exercise_payoff = option.payoff(self.price)
            self.payoff = max(retro_payoff, exercise_payoff)
        else:
            self.payoff = retro_payoff