from datetime import datetime
import time
import numpy as np
from PythonFiles.options import Option, EuropeanCallOption, EuropeanPutOption, AmericanCallOption, AmericanPutOption, BermudeanCallOption, BermudeanPutOption, DigitalCallOption, DigitalPutOption
from PythonFiles.visualisation import visualize_tree
from PythonFiles.market import Market
from PythonFiles.tree import Tree
from PythonFiles.treeMemoryAlloc import TreeMemoryAlloc
from PythonFiles.greeks import Greeks

def generate_and_price(market, option, nb_steps : int, prunning : float, visualise : bool = False, greeks : bool = False):
    '''
    Fonction qui permet de générer le prix d'une option avec un arbre. Possibilité de plot l'arbre et de calculer les grecs
    '''
    tree = Tree(market=market, option=option, nb_steps=nb_steps, prunning_value=prunning)
    start=time.time()
    tree.generate_tree()
    timer_generate = round(time.time()-start,5)
    start=time.time()
    tree.price()
    timer_price = round(time.time()-start,5)

    price = tree.root_node.payoff
    close_formula_price = option.compute_price(market)
    
    fig, greeks_dict = None, None
    if visualise and nb_steps < 25:
        fig = visualize_tree(tree,nb_steps)
    if greeks:
        greeks_obj = Greeks(epsilon=0.01, tree=tree)
        greeks_obj.compute_greeks()
        greeks_dict = {"Delta" : greeks_obj.delta, "Gamma" : greeks_obj.gamma, "Vega" : greeks_obj.vega, "Theta" : greeks_obj.theta, "Rho" : greeks_obj.rho}
    print("-----------------------------------------------")

    info_dict = {"Price" : price, "Benchmark Price" : close_formula_price, "Time Generate" : timer_generate, "Time Price" : timer_price}
    return info_dict, greeks_dict, fig

def price_tree_memory(market, option, nb_steps : int, prunning : float):
    '''
    Fonction qui permet de générer le prix d'une option avec un arbre gérant l'allocation de mémoire
    '''
    tree_memory = TreeMemoryAlloc(market=market, option=option, nb_steps=nb_steps, prunning_value=prunning)
    start=time.time()
    price = tree_memory.price_tree()
    timer_price = round(time.time()-start,5)
    close_formula_price = option.compute_price(market)
    return price, timer_price

def calculate_prices_range(steps : list, market : Market, option : Option):
    '''
    Fonction permettant de calculer le temps d'exécution et le prix pour un nombre de step donné
    '''
    prices = []
    execution_times = []
    
    for step in steps:
        tree = Tree(market = market, option=option, nb_steps=int(step), prunning_value=1e-10)
        start=time.time()
        tree.generate_tree()
        tree.price()
        temps_exec = round(time.time()-start,5)

        prices.append(tree.root_node.payoff)         
        execution_times.append(temps_exec)  

    prices_array = np.array(prices)
    execution_times_array = np.array(execution_times)
    return (prices_array, execution_times_array)

############# Fonctions qui permettent de créer les instances de classe depuis le fichier excel
def make_market_from_input(sheet, spot : float = 0) -> Market:
    '''
    Fonction permettant de créer un marché depuis les paramètres de la feuille
    '''
    if(spot == 0):
        spot: float = sheet.range('ISpot').value
    volatility: float = sheet.range('IVol').value
    risk_free_rate: float = sheet.range('IRate').value
    dividende: float = sheet.range('IDiv').value
    div_date: datetime = sheet.range('IDivDate').value
    market = Market(spot=spot, volatility=volatility, rate=risk_free_rate, dividende=dividende, div_date=div_date)
    return market

def make_option_from_input(sheet, strike : float = 0) -> Option:
    '''
    Fonction permettant de créer une option depuis les paramètres de la feuille excel
    '''
    # Paramètres de l'option
    start_date: datetime = sheet.range('IStartDate').value
    maturity: float = sheet.range('IMaturity').value
    if(strike==0): # Cas ou aucun strike n'est entré en paramètre
        strike: float = sheet.range('IStrike').value   
    option_type: str = sheet.range('IOptionType').value
    exercise: float = sheet.range('IExerciseType').value
    match (exercise):
        case "European":
                if option_type == "Call":
                    option = EuropeanCallOption(time_to_maturity=maturity, strike=strike, start_date=start_date)
                else:
                    option = EuropeanPutOption(time_to_maturity=maturity, strike=strike, start_date=start_date)
        case "American":
            if option_type == "Call":
                option = AmericanCallOption(time_to_maturity=maturity, strike=strike, start_date=start_date)
            else:
                option = AmericanPutOption(time_to_maturity=maturity, strike=strike, start_date=start_date)
    return option

def make_tree_from_input(sheet, mkt:Market, opt:Option, nb_steps:int = 0) -> Tree:
    '''
    Fonction permettant de créer un marché depuis les paramètres de la feuille ou avec un step en particulier
    '''
    if(nb_steps==0):
        nb_steps: int = int(sheet.range('INbSteps').value)
    prunning : float = sheet.range('IPrunningTreshold').value
    return Tree(option = opt, market = mkt, nb_steps = nb_steps, prunning_value = prunning)
