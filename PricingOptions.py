import xlwings as xw
import numpy as np
import pandas as pd
import time
from tqdm import tqdm
from PythonFiles.tree import Tree
from PythonFiles.greeks import Greeks
from PythonFiles.utils import make_market_from_input, make_option_from_input, make_tree_from_input, calculate_prices_range, price_tree_memory
from PythonFiles.visualisation import plot_price_convergence, plot_execution_time, plot_gap, plot_gap_step, plot_greek

def main():
    '''
    Permet de calculer le prix de l'option avec arbre trinomial depuis python en prenant les paramètres excels
    '''
    try:
        wb = xw.Book.caller() # Script exécuté depuis excel
    except:
        wb = xw.Book("PricingOptions.xlsm")   # Script exécuté depuis python
    # Accéder à la première feuille
    sheet_pricer = wb.sheets["Interface"]
    # Initialisation des classes
    mkt = make_market_from_input(sheet_pricer)
    option = make_option_from_input(sheet_pricer)
    tree = make_tree_from_input(sheet_pricer, mkt, option)

    start=time.time()
    tree.generate_tree()
    generate_time = time.time() - start

    start=time.time()
    tree.price()
    price_time = time.time() - start

    sheet_pricer.range('IPythonPrice').value = tree.root_node.payoff
    sheet_pricer.range('IPythonTimeTree').value = generate_time
    sheet_pricer.range('IPythonPriceTime').value = price_time

@xw.sub
def python_price():
    '''
    Création d'un sub excel avec xlwings permettant de calculer un prix 
    '''
    try:
        wb = xw.Book.caller() # Script exécuté depuis excel
    except:
        wb = xw.Book("PricingOptions.xlsm")   # Script exécuté depuis python
    # Accéder à la première feuille
    sheet_pricer = wb.sheets["Interface"]
    # Initialisation des classes
    mkt = make_market_from_input(sheet_pricer)
    option = make_option_from_input(sheet_pricer)
    tree = make_tree_from_input(sheet_pricer, mkt, option)

    start=time.time()
    tree.generate_tree()
    generate_time = time.time() - start

    start=time.time()
    tree.price()
    price_time = time.time() - start
    
    sheet_pricer.range('IPythonPrice').value = tree.root_node.payoff
    sheet_pricer.range('IPythonTimeTree').value = generate_time
    sheet_pricer.range('IPythonPriceTime').value = price_time

@xw.sub
def python_tree_memory_price():
    '''
    Création d'un sub excel avec xlwings permettant de calculer un prix 
    '''
    try:
        wb = xw.Book.caller() # Script exécuté depuis excel
    except:
        wb = xw.Book("PricingOptions.xlsm")   # Script exécuté depuis python
    # Accéder à la première feuille
    sheet_pricer = wb.sheets["Interface"]
    # Initialisation des classes
    mkt = make_market_from_input(sheet_pricer)
    option = make_option_from_input(sheet_pricer)

    if (mkt.dividende > 0): # Indisponible avec dividende pour l'instant
        sheet_pricer.range('IPythonPriceTreeMemory').value = "N/A"
        sheet_pricer.range('IPythonTimeTreeMemory').value = "N/A"
        wb.app.api.Application.Run('MsgBox "Le pricing avec allocation de mémoire est indisponible avec dividende"')
        return
    
    nb_steps: int = int(sheet_pricer.range('INbSteps').value)
    prunning : float = sheet_pricer.range('IPrunningTreshold').value
    price, timer = price_tree_memory(mkt,option,nb_steps  , prunning)
    
    sheet_pricer.range('IPythonPriceTreeMemory').value = price
    sheet_pricer.range('IPythonTimeTreeMemory').value = timer

@xw.sub
def generate_python_graphs():
    '''
    Création d'un sub excel avec xlwings permettant de générer les graphiques de convergence
    '''
    try:
        wb = xw.Book.caller() # Script exécuté depuis excel
    except:
        wb = xw.Book("PricingOptions.xlsm")   # Script exécuté depuis python
    sheet_pricer = wb.sheets["Interface"]
    sheet_conv = wb.sheets["Convergence Study"]
    
    # Initialisation des classes
    mkt = make_market_from_input(sheet_pricer)
    option = make_option_from_input(sheet_pricer)
    steps = sheet_conv.range('StepRange').options(np.ndarray).value
    prices,execution_times = calculate_prices_range(steps, mkt, option)

    bs_price = option.compute_price(mkt)
    gap = bs_price - prices
    gap_step = gap * steps

    fig_conv = plot_price_convergence(steps, prices, bs_price)
    fig_time = plot_execution_time(steps, execution_times)
    fig_gap = plot_gap(steps, gap)
    fig_gap_step = plot_gap_step(steps, gap_step)
    
    sheet_conv.pictures.add(fig_conv, name='Picture 1', update=True)
    sheet_conv.pictures.add(fig_time, name='Picture 2', update=True)
    sheet_conv.pictures.add(fig_gap, name='Picture 7', update=True)
    sheet_conv.pictures.add(fig_gap_step, name='Picture 8', update = True)

@xw.sub
def generate_greeks_graphs():
    '''
    Création d'un sub excel avec xlwings permettant de générer les graphiques des grecs
    '''
    try:
        wb = xw.Book.caller() # Script exécuté depuis excel
    except:
        wb = xw.Book("PricingOptions.xlsm")   # Script exécuté depuis python
    sheet_pricer = wb.sheets["Interface"]
    sheet_greeks = wb.sheets["Greeks"]
    # Initialisation des classes
    greeks = []
    opt = make_option_from_input(sheet_pricer)
    spots = np.arange(int(opt.strike/2), int(opt.strike*1.5), 5)
    for spot in tqdm(spots): # On calcule les grecs pour chaque spot
        mkt = make_market_from_input(sheet_pricer, spot)
        tree = Tree(opt, mkt, nb_steps = 100, prunning_value = 10^-7)
        tree.generate_tree()
        tree.price()
        greek = Greeks(epsilon=0.01, tree=tree)
        greek.compute_greeks()
        greeks.append({'Delta':greek.delta, 'Gamma':greek.gamma, 'Vega':greek.vega, 'Theta':greek.theta,'Rho':greek.rho})
    df_greeks = pd.DataFrame(greeks)
    df_greeks['Spot'] = spots
    # Récupération des figures des grecks
    fig_delta = plot_greek(df_greeks, 'Delta', 'blue')
    fig_gamma = plot_greek(df_greeks, 'Gamma', 'green')
    fig_vega = plot_greek(df_greeks, 'Vega', 'red')
    fig_theta = plot_greek(df_greeks, 'Theta', 'purple')
    fig_rho = plot_greek(df_greeks, 'Rho', 'orange')

    sheet_greeks.pictures.add(fig_delta, name='Chart 1', update=True)
    sheet_greeks.pictures.add(fig_gamma, name='Chart 2', update=True)
    sheet_greeks.pictures.add(fig_vega, name='Chart 3', update=True)
    sheet_greeks.pictures.add(fig_theta, name='Chart 4', update = True)
    sheet_greeks.pictures.add(fig_rho, name='Chart 5', update = True)
    
if __name__ == "__main__":
    main()
    
