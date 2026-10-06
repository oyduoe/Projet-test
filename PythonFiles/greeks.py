from PythonFiles.options import EuropeanCallOption
from PythonFiles.market import Market
from PythonFiles.tree import Tree
from dataclasses import dataclass

@dataclass
class Greeks:

    tree : Tree
    epsilon : float = 0.01

    delta : float = 0
    gamma : float = 0
    vega : float = 0 
    theta : float = 0
    rho : float = 0

    def compute_greeks(self) -> None:
        self.tree.generate_tree()
        self.tree.price()
        self.price_tree = self.tree.root_node.payoff

        self.compute_delta()
        self.compute_vega()
        self.compute_gamma()
        self.compute_theta()
        self.compute_rho()

    def compute_delta(self):

        delta_s = self.epsilon * 100

        self.tree.market.spot += delta_s
        self.tree.generate_tree()
        self.tree.price()

        self.delta = (self.tree.root_node.payoff - self.price_tree)/(delta_s)
        self.tree.market.spot -= delta_s

    def compute_vega(self):
        delta_v = self.epsilon

        self.tree.market.volatility += delta_v 
        self.tree.generate_tree()
        self.tree.price()

        self.vega = (self.tree.root_node.payoff - self.price_tree)/(delta_v)
        self.tree.market.volatility -= delta_v
        
    def compute_gamma(self):
        delta_g = self.epsilon * 500

        self.tree.market.spot += delta_g
        self.tree.generate_tree()
        self.tree.price()
        price_up = self.tree.root_node.payoff

        self.tree.market.spot -= 2*delta_g
        self.tree.generate_tree()
        self.tree.price()
        price_down = self.tree.root_node.payoff

        self.gamma = (price_up - 2*self.price_tree + price_down)/(delta_g)**2
        self.tree.market.spot += delta_g

    def compute_theta(self):
        delta_t = 5 * self.epsilon

        self.tree.option.time_to_maturity -= delta_t
        tree_bis = Tree(option=self.tree.option, market=self.tree.market, nb_steps=self.tree.nb_steps, prunning_value=self.tree.prunning_value)
        tree_bis.generate_tree()
        tree_bis.price()

        self.theta = (tree_bis.root_node.payoff - self.price_tree)/(delta_t)
        self.tree.option.time_to_maturity += delta_t

    def compute_rho(self):
        delta_r = self.epsilon

        self.tree.market.rate += delta_r
        self.tree.generate_tree()
        self.tree.price()

        self.rho = (self.tree.root_node.payoff - self.price_tree)/(delta_r)
        self.tree.market.rate -= delta_r