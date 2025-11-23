# %% [markdown]
# ## Chart Descriptions
# Text content for dashboard transparency.

# %%
descriptions = {
    "money": """
    **How this is calculated:**
    - **Data Source:** Players self-report their total spending tier (e.g., F2P, $1-$100, $1000++).
    - **Metric:** The box plot shows the distribution of 'Win Rate' for all players within each spending tier.
    - **Interpretation:** The box represents the middle 50% of players (IQR). The line inside is the median win rate. Whiskers show the range of typical performance. Outliers are shown as individual points.
    - **Goal:** To visualize if higher spending correlates with higher win rates, or if F2P players remain competitive.
    """,
    
    "teams": """
    **How this is calculated:**
    - **Team Definition:** A unique combination of 3 Umas used by a single player in a single session (Round + Day).
    - **Filtering:** Only team compositions that appear at least 8 times in the dataset are shown to ensure statistical relevance.
    - **Metric:** The average win rate of all players using that specific trio of Umas.
    - **Goal:** To identify the "Meta" teams that consistently perform well across different trainers.
    """,
    
    "umas": """
    **How this is calculated:**
    - **Scope:** Evaluates each Uma individually, regardless of their teammates.
    - **Metric:** The average win rate of all teams that included this specific Uma.
    - **Filtering:** Umas with fewer than 10 recorded runs are excluded to prevent skewed data (e.g., 1 win / 1 run = 100%).
    - **Goal:** To produce a "Tier List" of individual character strength in the current meta.
    """,
    
    "strategy": """
    **How this is calculated:**
    - **Standardization:** Raw running styles (e.g., "Betweener", "Leader") are mapped to standard English terms (Pace Chaser, Front Runner, etc.).
    - **Metric:** The average win rate for Umas using that specific running style.
    - **Goal:** To see which running strategy is dominant on this specific track.
    """,
    
    "runaway": """
    **How this is calculated:**
    - **Definition:** A team is flagged as "With Runaway" if at least one Uma uses the 'Runaway' (Nigeru) or 'Oonige' strategy. Note: 'Front Runner' (Senkou) is NOT considered a Runaway.
    - **Metric:** Compares the average win rate of teams that include a Runaway vs. teams that do not.
    - **Goal:** To test the hypothesis that having a Runaway is essential for controlling the race pace.
    """,
    
    "cards": """
    **How this is calculated:**
    - **Data Source:** Players report the status (Limit Break level) of specific key Support Cards (e.g., Kitasan Black).
    - **Metric:** The average win rate of players grouped by the Limit Break status of the selected card (e.g., MLB vs 0LB).
    - **Goal:** To measure the impact of "Meta" support cards on actual race performance.
    """,
    
    "leaderboard": """
    **How this is calculated:**
    - **Sorting:** Trainers are ranked by a 'Performance Score' which prioritizes Total Wins first, and Win Rate second.
    - **Formula:** Score = Win Rate * log(Total Races + 1). This ensures a player with 19/20 wins ranks higher than a player with 1/1 wins.
    - **Filtering:** Trainers with fewer than 15 total races are excluded to ensure the leaderboard reflects consistent performance.
    - **Anonymization:** Only the Top 10 trainers are shown by name; all others are anonymized in the dataset.
    """,
    
    "trends": """
    **How this is calculated:**
    - **Grouping:** Data is aggregated by Round (1 or 2) and Day (1 or 2).
    - **Metric:** The average win rate of the entire player base for that specific session.
    - **Goal:** To observe how the competition difficulty evolves over time (e.g., does win rate drop in Round 2 as casual players are eliminated?).
    """
}

footer_html = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #0E1117;
    color: #FAFAFA;
    text-align: center;
    padding: 10px;
    font-size: 14px;
    font-weight: bold;
    border-top: 1px solid #333;
}
</style>
<div class="footer">
    <p>Made by Zuse 🚀 | Virgo Cup Analytics</p>
</div>
"""