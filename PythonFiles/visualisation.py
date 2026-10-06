import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from PythonFiles.tree import Tree

def visualize_tree(tree : Tree, nb_steps):
    '''
    Création de l'affichage du prix de chaque branche de l'arbre
    '''
    G = nx.DiGraph()  
    node_labels = {}
    pos = {}

    def add_edges_by_level(node, level=0, parent=None, pos_y=0):
        if node is None:
            return
        node_label = f"{round(node.price, 2)}"
        node_id = f"{level}_{round(node.price, 2)}"
        node_labels[node_id] = node_label

        G.add_node(node_id, level=level)
        if parent:
            G.add_edge(parent, node_id)
        pos[node_id] = (level, pos_y)
        add_edges_by_level(node.next_up, level+1, node_id, pos_y+1)
        add_edges_by_level(node.next_mid, level+1, node_id, pos_y)
        add_edges_by_level(node.next_down, level+1, node_id, pos_y-1)

    add_edges_by_level(tree.root_node, 0)
    fig = plt.figure(figsize=(15, 10))
    nx.draw(G, pos, labels=node_labels, with_labels=True, node_size=1000, node_color="lightblue", font_size=8, font_color="black", font_weight='bold', arrowsize=10)
    plt.title("Arbre Trinomial")
    return fig

def plot_price_convergence(steps, prices_array, bs_price):
    '''
    Affiche la convergence de l'arbre binomial avec Black-Scholes en utilisant Seaborn
    '''
    plt.figure(figsize=(10, 6))  
    sns.lineplot(x=steps, y=prices_array, label='Computed Prices')  
    plt.axhline(y=bs_price, color='r', linestyle='--', label=f'BS Price: {round(bs_price, 2)}')  
    plt.title('Price Convergence towards Black-Scholes')
    plt.xlabel('Steps')
    plt.ylabel('Price (€)')
    plt.legend()
    plt.tight_layout()
    fig = plt.gcf()
    return fig

def plot_execution_time(steps, execution_time):
    '''
    Affiche le temps d'éxécution de l'arbre vs le nombre de pas en utilisant Seaborn
    '''
    plt.figure(figsize=(12, 6)) 
    sns.lineplot(x=steps, y=execution_time, color='green', label='Execution Time')  
    plt.title('Execution Time vs Steps')
    plt.xlabel('Steps')
    plt.ylabel('Execution Time (seconds)')
    plt.legend()
    plt.tight_layout()
    fig = plt.gcf()
    return fig

def plot_gap(steps, gap):
    '''
    Affiche la diminution de l'erreur avec le nombre de pas en utilisant Seaborn
    '''
    plt.figure(figsize=(12, 6)) 
    sns.lineplot(x=steps, y=gap, color='purple', label='Difference (BS Price - Computed Prices)')
    plt.axhline(y=0, color='black', linestyle='--')
    plt.title('Difference (BS Price - Computed Prices) vs Steps')
    plt.xlabel('Steps')
    plt.ylabel('Difference')
    plt.legend()
    plt.tight_layout()
    fig = plt.gcf()
    return fig

def plot_gap_step(steps, gap_step):
    '''
    Affiche la différence multipliée par le nombre de pas avec Seaborn
    '''
    plt.figure(figsize=(12, 6)) 
    sns.lineplot(x=steps, y=gap_step, color='orange', label='Difference * Step')
    plt.axhline(y=0, color='black', linestyle='--')  
    plt.title('Difference (BS Price - Computed Prices) * Steps vs Steps')
    plt.xlabel('Steps')
    plt.ylabel('Difference * Step')
    plt.legend()
    plt.tight_layout()
    fig = plt.gcf()
    return fig

def plot_greek(df, greek, color = 'blue'):
    '''
    Affichage des grecs selon le spot
    '''
    plt.figure(figsize=(8, 5))
    sns.lineplot(x='Spot', y=greek, data=df, marker='o', color=color)
    plt.title(f'Variation de {greek} en fonction du Spot')
    plt.xlabel('Spot')
    plt.ylabel(greek)
    fig = plt.gcf()
    return fig