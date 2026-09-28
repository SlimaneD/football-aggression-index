"""Standalone blog figure: the full European ranking (80 teams, four leagues,
2015/16) by forward press rate, as a sober, classy standalone table matching
the styling of the other blog figures.
"""
import pandas as pd
import plotly.graph_objects as go

HEADER_COLOR = "#3D4C5E"
ROW_COLORS = ["white", "#F2F4F6"]

paths = {
    "Premier League": "data/aggression_raw_premier_league.csv",
    "La Liga": "data/aggression_raw_la_liga.csv",
    "Ligue 1": "data/aggression_raw_ligue_1.csv",
    "Serie A": "data/aggression_raw_serie_a.csv",
}
europe_df = pd.concat(
    [pd.read_csv(p).assign(league=l) for l, p in paths.items()], ignore_index=True
)

overall_ranking = europe_df.groupby("team")["raw_aggression_index"].mean().sort_values(ascending=False)
team_league = europe_df.drop_duplicates("team").set_index("team")["league"]

table = overall_ranking.rename("score").reset_index().rename(columns={"team": "Team"})
table.insert(0, "Rank", range(1, len(table) + 1))
table["League"] = table["Team"].map(team_league)
table["Mean aggression score"] = table["score"].map(lambda v: f"{v:.3f}")
table = table[["Rank", "Team", "League", "Mean aggression score"]]

row_colors = [ROW_COLORS[i % 2] for i in range(len(table))]

fig = go.Figure(data=[go.Table(
    columnwidth=[50, 220, 150, 150],
    header=dict(
        values=[f"<b>{c}</b>" for c in table.columns],
        fill_color=HEADER_COLOR,
        font=dict(color="white", family="Helvetica, Arial, Liberation Sans, DejaVu Sans, sans-serif", size=14),
        align=["center", "left", "left", "center"],
        height=36,
    ),
    cells=dict(
        values=[table[c] for c in table.columns],
        fill_color=[row_colors],
        font=dict(color="#222222", family="Helvetica, Arial, Liberation Sans, DejaVu Sans, sans-serif", size=13),
        align=["center", "left", "left", "center"],
        height=28,
    ),
)])

fig.update_layout(
    title=dict(text="European ranking — forward press rate (2015/16, four leagues)"),
    font=dict(family="Helvetica, Arial, Liberation Sans, DejaVu Sans, sans-serif", size=14, color="black"),
    paper_bgcolor="white",
    width=650,
    height=760,
    margin=dict(t=70, l=20, r=20, b=20),
)

fig.write_html("figures/european_ranking_table.html", include_plotlyjs="cdn")
fig.write_image("figures/european_ranking_table.png", scale=2)
print("Saved figures/european_ranking_table.html and .png")
print(f"n teams: {len(table)}")
