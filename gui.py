import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from new import Simulation
import streamlit.components.v1 as components



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

is_fast_run = st.checkbox("Fast Run", value=True)
st.info('Fast run runs day one time and multiplies by 365 instead of running 365 separate day iterations', icon="ℹ️")

st.write("Cost Parameters")
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
                    results.append({
                        "Number of Breaks": num_breaks,
                        "Total Profit": 0 if total_profit < 0 else total_profit,
                        "Years": 'no' if total_profit < 0 else yrs,
                        "Price per Min": row1["price_per_min"],
                        "Cost per Min": row1["cost_per_min"],
                        "Speaking Time": row2["speaking_time"],
                        "Ads Percent": row2["ads_percent"],
                        "Erlang Mean": row3["erlang_mean"],
                        "Duration Low": row3["duration_low"],
                        "Duration High": row3["duration_high"],
                        "Partial Addition Coefficient": row1["partially_addition_coefficient"],
                        "Late Addition Coefficient": row1["late_addition_coefficient"]
                    })

    results_df = pd.DataFrame(results)
    st.write("### Simulation Output")
    st.dataframe(results_df)

    group_cols = [col for col in results_df.columns if col not in ["Number of Breaks", "Total Profit", "Years"]]

    grouped_results = results_df.groupby(group_cols)

    results_df = results_df.copy()
    results_df["Run"] = 0  # Initialize Run column

    for run_number, (_, group) in enumerate(grouped_results, start=1):
        results_df.loc[group.index, "Run"] = run_number  # Assign run numbers

    # Display small dataframes separately
    for run_number, run_df in results_df.groupby("Run"):
        st.write(f"#### Run {run_number}")
        st.dataframe(run_df)

    # Plot results
    fig, ax = plt.subplots()

    # Loop through each unique "Run" and plot the data
    for name, group in results_df.groupby("Run"):
        ax.plot(
            group["Number of Breaks"],
            group["Total Profit"],
            marker='o',
            linestyle='-',  # Ensures lines are drawn
            label=f"Run {name}"
        )

    # Set labels and title
    ax.set_xlabel("Number of Breaks")
    ax.set_ylabel("Total Profit")
    ax.set_title("Profit vs. Number of Breaks (Grouped by Unique Parameter Sets)")

    # Add legend
    ax.legend(title="Run")

    # Show the plot (for Streamlit)
    st.pyplot(fig)

    # Provide option to download results with all inputs
    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Full Results as CSV",
        data=csv,
        file_name="simulation_results.csv",
        mime="text/csv"
    )
