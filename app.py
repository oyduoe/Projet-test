import streamlit as st
import pandas as pd
from PythonFiles.market import Market
from PythonFiles.options import EuropeanCallOption, EuropeanPutOption, AmericanCallOption, AmericanPutOption, BermudeanCallOption, BermudeanPutOption, DigitalCallOption, DigitalPutOption
from PythonFiles.utils import generate_and_price
from datetime import datetime, timedelta

st.title("Trinomial Tree Pricer")
st.header("Price your option :")

option_exercises_str = ['European', 'American', 'Bermudean', 'Digital']
option_types_str = ["Call", "Put"]
col1, col2 = st.columns(2)
with col1:
    option_exercises = st.selectbox("Option Exercise", option_exercises_str, index=option_exercises_str.index('European'))
with col2:
    option_type = st.selectbox("Option type", option_types_str)

st.subheader("Market parameters :")

col1, col2 = st.columns(2)
with col1:
    spot = st.number_input("Spot", value=100)
    rate = st.number_input("Risk free rate", value=0.05)
with col2:
    vol = st.number_input("Volatility", value=0.20)
    div_date = st.date_input("Dividend date")

st.subheader("Option parameters :")
col1, col2 = st.columns(2)
with col1:
    strike = st.number_input("Strike", value=100)
    div = st.number_input("Dividend", value=0)
with col2:
    default_date = datetime.now() + timedelta(days=365)
    start_date = st.date_input("Start date of the contract")
    end_date = st.date_input("End date of the contract", default_date)

if option_exercises == "Bermudean":
    if 'exercise_dates' not in st.session_state:
        st.session_state.exercise_dates = []

    # Bouton pour ajouter une nouvelle date
    if st.button("Add exercise date"):
        # Ajout d'une nouvelle date par défaut (date du jour) à la liste
        st.session_state.exercise_dates.append(datetime.today())

    # Affichage de toutes les dates ajoutées avec la possibilité de les modifier
    for i, date in enumerate(st.session_state.exercise_dates):
        # L'utilisateur peut modifier chaque date avec un champ date_input
        st.session_state.exercise_dates[i] = st.date_input(f"Exercise date {i + 1}", value=date, key=f"date_{i}")

elif option_exercises == "Digital":
    coupon = st.number_input("Digital coupon", value=1)

st.subheader("Model parameters :")
col1, col2 = st.columns(2)
with col1:
    nb_steps = st.number_input("Number of steps", value=1000)
    is_greeks = st.checkbox("Calculate Greeks ?", value=False)
with col2:
    prunning_value = st.number_input("Prunning treshold (number of decimals)", value=8)
    prunning_value = 10 ** (-prunning_value)
    is_visu = st.checkbox("Visualise ?", value=False)

price_button = st.button("Compute option price")
if price_button:
    with st.spinner("In progress..."):
        if start_date > end_date :
            st.warning("Please select an end date after the strat date !")
        elif div_date > end_date or div_date < start_date:
            st.warning("Please select a div date between start and end dates     !")
        else :
            maturity = (end_date - start_date).days / 365
            st.write(f"Option maturity : {round(maturity,2)} years")
            match option_exercises:
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
                case "Bermudean":
                    if option_type == "Call":
                        option = BermudeanCallOption(time_to_maturity=maturity, strike=strike, start_date=start_date, exercise_dates=st.session_state.exercise_dates)
                    else:
                        option = BermudeanPutOption(time_to_maturity=maturity, strike=strike, start_date=start_date, exercise_dates=st.session_state.exercise_dates)
                case "Digital":
                    if option_type == "Call":
                        option = DigitalCallOption(time_to_maturity=maturity, strike=strike, start_date=start_date, coupon=coupon)
                    else:
                        option = DigitalPutOption(time_to_maturity=maturity, strike=strike, start_date=start_date, coupon=coupon)

            market = Market(spot=spot, rate=rate, volatility=vol,div_date=div_date, dividende=div)
            info_dict, greeks_dict, fig = generate_and_price(market=market, option=option, nb_steps=nb_steps, prunning=prunning_value, visualise=is_visu, greeks=is_greeks)
            st.write("---")

            option_price = round(info_dict["Price"],5)
            if option_exercises == "European" and market.dividende == 0:
                    close_formula_price = round(info_dict["Benchmark Price"],5)
            else:
                close_formula_price = 'N/A'
            tree_time = round(info_dict["Time Generate"],3)
            pricing_time = round(info_dict["Time Price"],3)
            total_time = round(tree_time + pricing_time,3)

            html_code = f'''
            <div class="results-container">
                <h2><b>Results<b></h2>
                <div class="pricing">
                    <h3>Pricing :</h3>
                    <p> <b>Option price :</b> {option_price}</p>
                    <p> <b>VS Close formula price </b>: {close_formula_price}</p>
                </div>
                <div class="performance">
                    <h3><b>Performance :<b></h3>
                    <p> <b>Tree generated in :</b> {tree_time} sec</p>
                    <p> <b>Option priced in :</b> {pricing_time} sec</p>
                    <p> <b>Total time :</b> {total_time} sec</p>
                </div>
            </div>

            <style>
                .results-container {{
                    width: 50%;
                    margin: 0 auto;
                    padding: 20px;
                    border: 2px solid #FF4B4B;
                    border-radius: 10px;
                    text-align: center;
                }}

                .results-container h2, 
                .results-container h3 {{
                    color: #FF4B4B;
                }}

                .results-container p {{
                    font-size: 1.2em;
                }}

                .pricing, .performance {{
                    margin-top: 20px;
                }}
            </style>
            '''
            st.markdown(html_code, unsafe_allow_html=True)

            if greeks_dict is not None :
                st.subheader("Option greeks :")
                df = pd.DataFrame(list(greeks_dict.items()), columns=["Option Greeks", "Value"])
                df.style.hide(axis='index')
                st.table(df)

            if nb_steps >= 25 and is_visu:
                st.warning("Cannot visualize more than 25 steps")
            else :
                if fig is not None :
                    st.pyplot(fig)