from math import exp, sqrt, ceil
from typing import Union
from dataclasses import dataclass
from functools import cached_property
from PythonFiles.market import Market
from PythonFiles.node import Node
from PythonFiles.options import EuropeanCallOption, EuropeanPutOption, AmericanCallOption, AmericanPutOption, BermudeanCallOption, BermudeanPutOption

@dataclass
class Tree():
   
    option : Union[EuropeanCallOption, EuropeanPutOption, AmericanCallOption, AmericanPutOption, BermudeanCallOption, BermudeanPutOption]
    market : Market
    nb_steps : int
    root_node : Node = None
    last_node : Node = None
    
    prunning_value : float = None

    ''' --------------------------------------------------------------------------------------------------------------------------------- '''
    '''                                                     Section Attributs calculés                                                            '''
    ''' --------------------------------------------------------------------------------------------------------------------------------- '''

    @cached_property
    def time_delta(self) -> float:
        return self.option.time_to_maturity / self.nb_steps    

    @cached_property
    def alpha(self) -> float:
        return exp(self.market.volatility * sqrt(3 * self.time_delta)  )

    @cached_property
    def div_step(self) -> float:
        '''
        Définit le timeStep auquel le détachement du dividende va avoir lieu en fonction des dates
        '''
        if self.market.dividende <= 0:
            return -1
        else:
            time_delta_in_days = self.time_delta * 365
            return ceil((self.market.div_date - self.option.start_date).days/time_delta_in_days)

    @cached_property
    def exercise_steps(self) -> list[int]:
        '''
        Définit une liste qui contient tous les timeSteps où l'option peut être exécutée
        '''
        if isinstance(self.option, BermudeanCallOption) or isinstance(self.option, BermudeanPutOption):
            exercise_dates = self.option.exercise_dates
            time_delta_in_days = self.time_delta * 365
            return [ceil((ex_date - self.option.start_date).days/time_delta_in_days) for ex_date in exercise_dates]
        
        elif isinstance(self.option, AmericanCallOption) or isinstance(self.option, AmericanPutOption):
            return [i for i in range(self.nb_steps)]
        
        else:
            return []
    
    ''' --------------------------------------------------------------------------------------------------------------------------------- '''
    '''                                              Section Génération de l'arbre                                                        '''
    ''' --------------------------------------------------------------------------------------------------------------------------------- '''

    def generate_tree(self):
        '''
        Fonction qui permet de générer l'abre colonne par colonne
        '''
        #Initialisation de la root avec le prix spot
        self.root_node = Node(price = self.market.spot, node_proba = 1)
        mid_node = self.root_node
        #On itère sur le tronc
        for step in range(1,self.nb_steps+1):
            is_div = True if step == self.div_step else False
            mid_node = self._build_column(mid_node, is_div)
        #On enregistre la dernière node du tronc pour ne pas à avoir à reparcourir l'arbre pour le pricing
        self.last_node = mid_node
        
    
    def _build_column(self, mid_node : Node, is_div : bool):
        '''
        Fonction qui génere une colonne de noeud
        '''
        #On construit le triplet depuis le tronc
        self._build_triplet(mid_node, is_div)

        upper_node = mid_node.up_node
        down_node = mid_node.down_node

        #En itérant vers le bas
        while down_node is not None:
            down_node = self._compute_down_nodes(down_node, is_div)
            
         #En itérant vers le haut
        while upper_node is not None:
            upper_node = self._compute_upper_nodes(upper_node, is_div)
            
        return mid_node.next_mid

    def _build_triplet(self, node : Node, is_div : bool):
        '''
        Génération des 3 noeuds fils depuis le noeud central à chaque colonne
        '''
        node.next_mid = self.calculate_forward_node(node, is_div)
        node.next_up = Node(price = node.next_mid.price * self.alpha)
        node.next_down = Node(price = node.next_mid.price / self.alpha)
        #Branchements des nouveaux noeuds entre eux
        node.branch_triplet()
        #On calcule les proba de transitions dans les états suivants
        node.compute_transition_proba(self.alpha, self.time_delta, self.market, is_div, self.market.dividende)
        #On calcule les proba d'existence des nouveaux noeuds
        node.update_proba()

    def _find_mid(self, node: Node, candidate_mid: Node, direction: str) -> Node:
        '''
        Cherche le prochain noeud mid qui est le plus proche du prix forward dans les deux directions au moment du lachement du dividende
        '''
        #Valeur attendue du forward
        forward_value = node.price * exp(self.market.rate * self.time_delta) - self.market.dividende
        while True:
            #On cherche vers le bas
            if direction == "down":
                next_price = candidate_mid.price / self.alpha
                condition = forward_value > (candidate_mid.price + next_price) / 2
            #On cherche vers le haut
            else:
                next_price = candidate_mid.price * self.alpha
                condition = forward_value < (candidate_mid.price + next_price) / 2
            #Si le candidat est le plus proche du forward on arrête la boucle
            if condition:
                return candidate_mid
            else:
                future_mid_node = Node(price=next_price)
                if direction == "down":
                    future_mid_node.up_node = candidate_mid
                    candidate_mid.down_node = future_mid_node
                else:
                    future_mid_node.down_node = candidate_mid
                    candidate_mid.up_node = future_mid_node

                candidate_mid = future_mid_node       

    def _compute_upper_nodes(self, node : Node, is_div : bool) -> Node:
        '''
        Calcule la prochaine up nodes en prenant en compte le lachement du dividende et le prunning
        Symétrique à "_compute_down_nodes"
        '''
        #Trouver le prochain noeud mid si le dividendes tombent à ce timeStep
        if is_div:
            candidate_mid = node.down_node.next_up
            node.next_mid = self._find_mid(node, candidate_mid, "up")
            node.next_down = node.next_mid.down_node
        else:
            node.next_mid = node.down_node.next_up
            node.next_down = node.down_node.next_mid

        #Si pas de prunning : on créer le noeud down fils et on calcule les proba
        if node.node_proba > self.prunning_value :
            node.next_up = Node(price = node.next_mid.price * self.alpha)
            #Calcul des proba de transition
            node.compute_transition_proba(self.alpha, self.time_delta, self.market, is_div, self.market.dividende)
            #Calcul des proba d'existance des noeuds fils
            node.update_proba()
            node.next_up.down_node = node.next_mid
            node.next_mid.up_node = node.next_up
            
            return node.up_node
        else :
            #If prunning : monomial branching = 100% proba mid
            node.branch_monomial()
            return None

    def _compute_down_nodes(self, node : Node, is_div : bool)-> Node:
        '''
        Calcule la prochaine down nodes en prenant en compte le lachement du dividende et le prunning
        Symétrique à "_compute_upper_nodes"
        '''
        #Trouver le prochain noeud mid si le dividendes tombent à ce timeStep
        if is_div:
            candidate_mid = node.up_node.next_down
            node.next_mid = self._find_mid(node, candidate_mid, "down")
            node.next_up = node.next_mid.up_node
            
        else:
            node.next_mid = node.up_node.next_down
            node.next_up = node.up_node.next_mid

        #Si pas de prunning : on créer le noeud down fils et on calcule les proba
        if node.node_proba > self.prunning_value :
            node.next_down = Node(price = node.next_mid.price / self.alpha)
            #Calcul des proba de transition
            node.compute_transition_proba(self.alpha, self.time_delta, self.market, is_div, self.market.dividende)

            #Calcul des proba d'existance des noeuds fils
            node.update_proba()

            node.next_down.up_node = node.next_mid
            node.next_mid.down_node = node.next_down
            return node.down_node
        
        #Si prunning : branchement monomial
        else :
            node.branch_monomial()
            return None
    
    def calculate_forward_node(self, node : Node, is_div : bool) -> Node:
        '''
        Calcul du forward en fonction du dividende
        '''
        if is_div:
            forward_price = node.price * exp(self.market.rate * self.time_delta) - self.market.dividende
        else :
            forward_price = node.price * exp(self.market.rate * self.time_delta)
        return Node(price = forward_price)

    ''' --------------------------------------------------------------------------------------------------------------------------------- '''
    '''                                              Section pricing de l'option                                                          '''
    ''' --------------------------------------------------------------------------------------------------------------------------------- '''

    def price(self) -> None:
        '''
        Pricer l'option avec l'arbre par mouvement backward
        '''
        last_node = self.last_node
        #Calcul du payoff de la dernière colonne
        self._compute_final_payoff(last_node)
        step = self.nb_steps - 1
        trunc_node = last_node.prec_node

        #Itération sur les noeuds du tronc en backward
        while trunc_node is not None:
            self._retro_payoff(trunc_node, step)
            trunc_node = trunc_node.prec_node
            step-=1

    def _compute_final_payoff(self, trunc_node : Node) -> None: 
        '''
        Calcule le payoff de l'option sur la dernière colonne
        '''       
        this_up = trunc_node
        this_down = trunc_node

        #Itération vers les noeuds supérieurs
        while this_up is not None:
            this_up.payoff = self.option.payoff(this_up.price)
            this_up = this_up.up_node
        
        #Itération vers les noeuds inférieurs
        while this_down is not None:
            this_down.payoff = self.option.payoff(this_down.price)
            this_down = this_down.down_node

    def _retro_payoff(self, trunc_node : Node, step : int) -> None:
        '''
        Calcule le prix de l'option sur la colonne par rétropropagation
        '''
        this_up = trunc_node
        this_down = trunc_node

        #Itération vers les noeuds supérieurs
        while this_up is not None:
            this_up.node_payoff(step, self.option, self.exercise_steps, self.market.rate, self.time_delta)
            this_up = this_up.up_node

        #Itération vers les noeuds inférieurs
        while this_down is not None:
            this_down.node_payoff(step, self.option, self.exercise_steps, self.market.rate, self.time_delta)
            this_down =this_down.down_node