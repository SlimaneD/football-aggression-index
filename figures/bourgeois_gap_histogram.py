"""Standalone blog figure: interactive distribution of the Bourgeois-convention
gap (home minus away forward press rate) across all 80 teams.

Same underlying number as the static matplotlib histogram in
validation_appendix.ipynb ("Distribution of the Bourgeois-convention gap across
all 80 teams"), rebuilt here as an interactive Plotly chart for the blog: hover
on a bar to see the individual teams in it and their exact values, not just the
bin's aggregate count.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gaussian_kde

BAR_COLOR = "#4C72B0"
KDE_COLOR = "#2A3F5F"
N_BINS = 15

paths = {
    "Premier League": "data/aggression_raw_premier_league.csv",
    "La Liga": "data/aggression_raw_la_liga.csv",
    "Ligue 1": "data/aggression_raw_ligue_1.csv",
    "Serie A": "data/aggression_raw_serie_a.csv",
}
europe_df = pd.concat(
    [pd.read_csv(p).assign(league=l) for l, p in paths.items()], ignore_index=True
)

home_away_diff = (
    europe_df[europe_df["venue"] == "Home"].groupby("team")["raw_aggression_index"].mean()
    - europe_df[europe_df["venue"] == "Away"].groupby("team")["raw_aggression_index"].mean()
).rename("home_minus_away").sort_values(ascending=False)

team_league = europe_df.drop_duplicates("team").set_index("team")["league"]

bin_edges = np.histogram_bin_edges(home_away_diff.values, bins=N_BINS)
bin_width = bin_edges[1] - bin_edges[0]
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

bin_of_team = pd.cut(home_away_diff, bins=bin_edges, include_lowest=True, labels=False)

counts = np.zeros(N_BINS, dtype=int)
hover_text = [""] * N_BINS
for bin_idx, group in home_away_diff.groupby(bin_of_team):
    ordered = group.sort_values(ascending=False)
    counts[bin_idx] = len(ordered)
    lines = [f"{team} ({team_league[team]}): {value:+.3f}" for team, value in ordered.items()]
    hover_text[bin_idx] = "<br>".join(lines)

# KDE overlaid on the same count scale as the histogram (density * n * bin width),
# matching what seaborn's histplot(kde=True) shows by default.
kde = gaussian_kde(home_away_diff.values)
grid = np.linspace(bin_edges[0], bin_edges[-1], 300)
kde_scaled = kde(grid) * len(home_away_diff) * bin_width

fig = go.Figure()

fig.add_trace(go.Bar(
    x=bin_centers,
    y=counts,
    width=bin_width * 0.95,
    marker=dict(color=BAR_COLOR, line=dict(color="white", width=0.5)),
    customdata=hover_text,
    hovertemplate="%{customdata}<extra></extra>",
    name="Teams",
))

fig.add_trace(go.Scatter(
    x=grid, y=kde_scaled,
    mode="lines",
    line=dict(color=KDE_COLOR, width=2.5),
    hoverinfo="skip",
    name="Density (smoothed)",
))

fig.add_vline(
    x=0, line=dict(color="#888888", width=1.5, dash="dash"),
)
fig.add_annotation(
    x=0, y=1.04, yref="paper", showarrow=False,
    text="No home/away difference",
    font=dict(size=12, color="#888888"),
)

fig.update_layout(
    title=dict(text="Distribution of the Bourgeois-convention gap across all 80 teams"),
    font=dict(family="Helvetica, Arial, Liberation Sans, DejaVu Sans, sans-serif", size=14, color="black"),
    xaxis=dict(title="Home aggression − away aggression", ticks="outside", showline=True, linecolor="black", gridcolor="#e5e5e5"),
    yaxis=dict(title="Number of teams", ticks="outside", showline=True, linecolor="black", gridcolor="#e5e5e5"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    bargap=0.05,
    showlegend=False,
    width=820,
    height=520,
    margin=dict(t=90, l=70, r=40, b=60),
)

fig.write_html("figures/bourgeois_gap_histogram.html", include_plotlyjs="cdn")
fig.write_image("figures/bourgeois_gap_histogram.png", scale=2)
print("Saved figures/bourgeois_gap_histogram.html and .png")
print()
print(f"n teams: {len(home_away_diff)}, mean gap: {home_away_diff.mean():.3f}")
