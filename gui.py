import streamlit as st
import pandas as pd
import streamlit.components.v1 as components


class Simulation:
    def __init__(self, num_breaks, price_per_min, cost_per_min, speaking_time, ads_percent,
                 erlang_mean, duration_low, duration_high,
                 partially_addition_coefficient, late_addition_coefficient, is_fast_run):
        self.num_breaks = num_breaks
        self.price_per_min = price_per_min
        self.cost_per_min = cost_per_min
        self.speaking_time = speaking_time
        self.ads_percent = ads_percent
        self.erlang_mean = erlang_mean
        self.duration_low = duration_low
        self.duration_high = duration_high
        self.partially_addition_coefficient = partially_addition_coefficient
        self.late_addition_coefficient = late_addition_coefficient
        self.is_fast_run = is_fast_run

    def run(self):
        # Placeholder logic for simulation
        total_profit = (self.price_per_min - self.cost_per_min) * self.speaking_time * self.num_breaks
        total_profit += self.ads_percent * 100
        yrs = 10 if self.is_fast_run else 15
        return total_profit, yrs


st.title("A20")

num_breaks_min, num_breaks_max = st.slider("Number of Breaks Range", min_value=1, max_value=10, value=(1, 3))

if "table_data_1" not in st.session_state:
    st.session_state.table_data_1 = pd.DataFrame({
        "price_per_min": [300],
        "cost_per_min": [20],
        "partially_addition_coefficient": [0.9],
        "late_addition_coefficient": [0.7]
    })

if "table_data_2" not in st.session_state:
    st.session_state.table_data_2 = pd.DataFrame({
        "speaking_time": [16],
        "ads_percent": [0.10]
    })

if "table_data_3" not in st.session_state:
    st.session_state.table_data_3 = pd.DataFrame({
        "erlang_mean": [20],
        "duration_low": [2.5],
        "duration_high": [3.5]
    })

# Checkbox for is_fast_run
is_fast_run = st.checkbox("Fast Run", value=True)
st.info('Fast run runs day one time and multiplies by 365 instead of running 365 separate day iterations', icon="ℹ️")

# Editable tables
st.write("### Cost Parameters")
edited_df_1 = st.data_editor(st.session_state.table_data_1, num_rows="dynamic")

st.write("Speaking & Ads parameters")
edited_df_2 = st.data_editor(st.session_state.table_data_2, num_rows="dynamic")

st.write("Time parameters")
edited_df_3 = st.data_editor(st.session_state.table_data_3, num_rows="dynamic")

if st.button("Run Simulation"):
    results = []
    for num_breaks in range(num_breaks_min, num_breaks_max + 1):
        for _, row1 in edited_df_1.iterrows():
            for _, row2 in edited_df_2.iterrows():
                for _, row3 in edited_df_3.iterrows():
                    simulation = Simulation(
                        num_breaks=num_breaks,
                        price_per_min=row1["price_per_min"],
                        cost_per_min=row1["cost_per_min"],
                        speaking_time=row2["speaking_time"],
                        ads_percent=row2["ads_percent"],
                        erlang_mean=row3["erlang_mean"],
                        duration_low=row3["duration_low"],
                        duration_high=row3["duration_high"],
                        partially_addition_coefficient=row1["partially_addition_coefficient"],
                        late_addition_coefficient=row1["late_addition_coefficient"],
                        is_fast_run=is_fast_run
                    )
                    total_profit, yrs = simulation.run()
                    results.append({"Number of Breaks": num_breaks, "Total Profit": total_profit, "Years": yrs})

    # Convert results to DataFrame and display
    results_df = pd.DataFrame(results)
    st.write("### Simulation Output")
    st.dataframe(results_df)
