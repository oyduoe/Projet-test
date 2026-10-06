from math import exp, sqrt, ceil
from typing import Union
from tqdm import tqdm
from dataclasses import dataclass
from functools import cached_property
from PythonFiles.market import Market
from PythonFiles.node import Node
from PythonFiles.options import EuropeanCallOption, EuropeanPutOption, AmericanCallOption, AmericanPutOption, BermudeanCallOption, BermudeanPutOption

@dataclass
class TreeMemoryAlloc():
   
    option : Union[EuropeanCallOption, EuropeanPutOption, AmericanCallOption, AmericanPutOption, BermudeanCallOption, BermudeanPutOption]
    market : Market
    nb_steps : int
    root_node : Node = None
    prunning_value : float = None

    @cached_property
    def time_delta(self) -> float:
        return self.option.time_to_maturity / self.nb_steps    

    @cached_property
    def alpha(self) -> float:
        return exp(self.market.volatility * sqrt(3 * self.time_delta)  )

    @cached_property
    def div_step(self) -> float:
        if self.market.dividende <= 0:
            return -1
        else:
            time_delta_in_days = self.time_delta * 356
            return ceil((self.market.div_date - self.option.start_date).days/time_delta_in_days)

    @cached_property
    def exercise_steps(self) -> list[int]:

        if isinstance(self.option, BermudeanCallOption) or isinstance(self.option, BermudeanPutOption):
            exercise_dates = self.option.exercise_dates
            time_delta_in_days = self.time_delta * 356
            return [ceil((ex_date - self.option.start_date).days/time_delta_in_days) for ex_date in exercise_dates]
        
        elif isinstance(self.option, AmericanCallOption) or isinstance(self.option, AmericanPutOption):
            return [i for i in range(self.nb_steps)]
        
        else:
            return []

            
    def price_tree(self):

        self.root_node = Node(price = self.market.spot)
        mid_node = self.root_node
        
        #On  génère l'arbre avec seulement les noeuds mid
        for _ in range(self.nb_steps):
            mid_node.next_mid =self.calculate_forward_node(mid_node, is_div=False)
            mid_node.next_mid.prec_node = mid_node
            mid_node = mid_node.next_mid

        print("Fin de la génération de l'arbre")
        # On compute les prices et payoff sur le dernier noeud
        k =int(6*sqrt(self.nb_steps/3))
        self._compute_last_payoff(mid_node, k)
        print("Fin de la comput des derniers payoffs")
        for i in tqdm(range(self.nb_steps-1,-1,-1), total=self.nb_steps, desc="Building tree...", leave=False):
            mid_node = mid_node.prec_node
            k = int(min(i, 6*sqrt(i/3)))
            self._compute_mid_node(mid_node, i)
            self._compute_upper_nodes(mid_node,k, i)
            self._compute_down_nodes(mid_node,k, i)
            self._destroy_nodes(mid_node.next_mid)

        return mid_node.payoff

    def _compute_last_payoff(self, node : Node, k : int):
        node.payoff = self.option.payoff(node.price)
        node_up  = node
        node_down = node
        
        for _ in range(k):
            node_down.down_node = Node(price = node_down.price / self.alpha)
            node_down.down_node.up_node = node_down
            node_down = node_down.down_node
            node_down.payoff = self.option.payoff(node_down.price)
        
        for _ in range(k):    
            node_up.up_node = Node(price = node_up.price * self.alpha)
            node_up.up_node.down_node = node_up
            node_up = node_up.up_node
            node_up.payoff = self.option.payoff(node_up.price)
    
    '''
    Permet de calculer les payoffs des noeuds du milieu
    '''
    def _compute_mid_node(self, node:Node, i:int):
        node.next_up = node.next_mid.up_node
        node.next_down = node.next_mid.down_node
        node.compute_transition_proba(alpha = self.alpha, time_delta = self.time_delta, market = self.market, dividende = self.market.dividende, is_div = False)
        node.node_payoff(i, self.option, self.exercise_steps, self.market.rate, self.time_delta)
    
    '''
    Calcul des payoff des noeuds du haut
    '''
    def _compute_upper_nodes(self, node:Node,k:int, i:int):
        for _ in range(k):
            # On cree le noeud de haut dessus
            node.up_node = Node(price = node.price * self.alpha)
            node.up_node.down_node = node
            node = node.up_node
            # On relie 
            node.next_mid = node.down_node.next_up
            node.next_down = node.down_node.next_mid
            node.next_up = node.next_mid.up_node
            # On calcule les proba et les payoff
            if (node.next_up is None):
                node.p_mid = 1.0
                node.p_down = 0.0
                node.p_up = 0.0
            else:
                node.compute_transition_proba(alpha = self.alpha, time_delta = self.time_delta, market = self.market, dividende = self.market.dividende, is_div = False)
            
            node.node_payoff(i, self.option, self.exercise_steps, self.market.rate, self.time_delta)

    '''
    Permet de calculer les payoffs des noeuds du bas
    '''
    def _compute_down_nodes(self, node:Node,k:int, i:int):
        for _ in range(k):
            # On cree le noeud de haut dessus
            node.down_node = Node(price = node.price / self.alpha)
            node.down_node.up_node = node
            node = node.down_node
            # On relie 
            node.next_mid = node.up_node.next_down
            node.next_up = node.up_node.next_mid
            node.next_down = node.next_mid.down_node
            # On calcule les proba et les payoff
            if (node.next_down is None):
                node.p_mid = 1.0
                node.p_down = 0.0
                node.p_up = 0.0
            else:
                node.compute_transition_proba(alpha = self.alpha, time_delta = self.time_delta, market = self.market, dividende = self.market.dividende, is_div = False)

            node.node_payoff(i, self.option, self.exercise_steps, self.market.rate, self.time_delta)

    def _destroy_nodes(self, node: Node):
        '''
        Fonction qui va détruire les noeuds
        '''
        node_up = node.up_node
        node_down = node.down_node

        # Détruire les nœuds au-dessus
        while node_up is not None:
            if node_up.down_node is not None:
                node_up.down_node.up_node = None
            node_up.down_node = None
            node_up.next_mid = None
            node_up.next_down = None
            node_up.next_up = None
            next_node_up = node_up.up_node
            node_up.up_node = None
            node_up = next_node_up

        # Détruire les nœuds en dessous
        while node_down is not None:
            if node_down.up_node is not None:
                node_down.up_node.down_node = None
            node_down.up_node = None
            node_down.next_mid = None
            node_down.next_down = None
            node_down.next_up = None
            next_node_down = node_down.down_node
            node_down.down_node = None
            node_down = next_node_down

        # Finalement, détruire le nœud principal
        node.up_node = None
        node.down_node = None
        node.next_mid = None
        node.next_down = None
        node.next_up = None
        node = None
        
    def calculate_forward_node(self, node : Node, is_div : bool) -> Node:
        '''
        Calcul du forward en fonction du dividende
        '''
        if is_div:
            forward_price = node.price * exp(self.market.rate * self.time_delta) - self.market.dividende
        else :
            forward_price = node.price * exp(self.market.rate * self.time_delta)
        return Node(price = forward_price)
            



    