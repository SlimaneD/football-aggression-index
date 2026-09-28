"""Standalone blog figure: average player positions, Barcelona vs Real Madrid.

La Liga, 2016-04-02, Spotify Camp Nou (Barcelona 1-2 Real Madrid). StatsBomb open
data, match_id 267533. Not part of the polished analysis notebooks -- a one-off
intro visual for the blog post.

Starting-XI players only. A player's average position is the mean (x, y) of every
StatsBomb event they're attached to that carries a location (passes, carries,
receipts, dribbles, shots, pressures, duels, interceptions, clearances, etc.) --
StatsBomb has no separate "touch" event type, so this is the broadest, most
standard "average position" signal, matching classic broadcast-style maps.

StatsBomb gives each team's own coordinates as "own goal = x0" regardless of which
team it is, so both teams' raw locations start out overlapping on the same side.
Real Madrid's coordinates are mirrored (120-x, 80-y) so both teams land correctly
on their own half of one shared pitch.

Pitch dimension constants come from mplsoccer.Pitch (statsbomb pitch type) -- only
the numbers, not mplsoccer's own matplotlib rendering. All lines are drawn as
Plotly shapes directly.
"""
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from mplsoccer import Pitch
from statsbombpy import sb
from statsbombpy.api_client import NoAuthWarning

warnings.filterwarnings("ignore", category=NoAuthWarning)

MATCH_ID = 267533
# Accent color per team: used for the convex hull tint and the marker outline.
TEAM_ACCENT = {"Barcelona": "#A50044", "Real Madrid": "#1A2A5E"}
# Marker fill per team: Real Madrid plays in white, so their dots are white-filled
# (with the navy accent as an outline instead, so they still read against the pitch).
MARKER_FILL = {"Barcelona": "#A50044", "Real Madrid": "white"}
# Barcelona's own blue (blaugrana), distinct from Real Madrid's navy accent;
# Real Madrid's outline uses its own accent, since white-on-white would be invisible.
MARKER_OUTLINE = {"Barcelona": "#004D98", "Real Madrid": TEAM_ACCENT["Real Madrid"]}
# mplsoccer's own 'grass' colormap endpoints (mplsoccer.cm.grass_cmap), reused here
# as alternating mowed-stripe bands rather than mplsoccer's own rendering.
GRASS_DARK = "#40701F"
GRASS_LIGHT = "#62C55F"
N_STRIPES = 10

# Same "defensive action attempt" definition used for forward press rate in the
# main analysis notebooks (validation_appendix.ipynb), reused here for consistency.
DEFENSIVE_ACTION_TYPES = ["Pressure", "Interception", "Foul Committed"]
# StatsBomb's 120-unit pitch length has no native metric scale; 105m is the
# standard approximate real-world pitch length used to convert StatsBomb units
# to meters throughout this project (same assumption as the tracking notebook).
PITCH_LENGTH_M = 105


def get_starting_xi(events):
    """{team_name: {player_id: position_name}} from the Starting XI events."""
    lineup_by_team = {}
    starting_xi_events = events[events["type"] == "Starting XI"]
    for _, row in starting_xi_events.iterrows():
        lineup_by_team[row["team"]] = {
            p["player"]["id"]: p["position"]["name"] for p in row["tactics"]["lineup"]
        }
    return lineup_by_team


def _first_valid_string(*candidates):
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c
    return None


def resolve_names(match_id, lineup_by_team):
    """{player_id: display_name}, nickname > full name > player_id string."""
    lineups = sb.lineups(match_id=match_id)
    names = {}
    for team, df in lineups.items():
        for _, row in df.iterrows():
            pid = row["player_id"]
            names[pid] = _first_valid_string(row["player_nickname"], row["player_name"]) or str(pid)
    return names


def average_positions(events, lineup_by_team, names):
    located = events[events["location"].notna() & events["player_id"].notna()].copy()
    located["x"] = located["location"].apply(lambda loc: loc[0])
    located["y"] = located["location"].apply(lambda loc: loc[1])

    rows = []
    for team, roster in lineup_by_team.items():
        team_events = located[located["team"] == team]
        for pid, position in roster.items():
            player_events = team_events[team_events["player_id"] == pid]
            if player_events.empty:
                # No located events at all for this player (rare, e.g. an
                # immediate red card) -- skip rather than plot a meaningless point.
                continue
            rows.append(
                {
                    "team": team,
                    "player_id": pid,
                    "name": names.get(pid, str(pid)),
                    "position": position,
                    "x": player_events["x"].mean(),
                    "y": player_events["y"].mean(),
                    "n_events": len(player_events),
                }
            )
    return pd.DataFrame(rows)


def mirror_team(df, team_to_mirror, pitch_length, pitch_width):
    df = df.copy()
    mask = df["team"] == team_to_mirror
    df.loc[mask, "x"] = pitch_length - df.loc[mask, "x"]
    df.loc[mask, "y"] = pitch_width - df.loc[mask, "y"]
    return df


def average_defensive_line(events, lineup_by_team, pitch_length):
    """Per team: mean x (= distance from own goal, in StatsBomb units and meters)
    of defensive-action attempts by starting-XI players. Same definition as
    forward press rate elsewhere in this project: Pressure, Interception, Foul
    Committed, or a Duel with duel_type == Tackle."""
    located = events[events["location"].notna() & events["player_id"].notna()].copy()
    located["x"] = located["location"].apply(lambda loc: loc[0])
    is_tackle = (located["type"] == "Duel") & (located["duel_type"] == "Tackle")
    is_defensive_action = located["type"].isin(DEFENSIVE_ACTION_TYPES) | is_tackle

    rows = []
    for team, roster in lineup_by_team.items():
        team_actions = located[
            (located["team"] == team) & is_defensive_action & located["player_id"].isin(roster.keys())
        ]
        mean_x = team_actions["x"].mean()
        rows.append(
            {
                "team": team,
                "x": mean_x,
                "x_m": mean_x * pitch_length / 120,
                "n_actions": len(team_actions),
            }
        )
    return pd.DataFrame(rows)


def add_grass_stripes(fig, pitch_dim):
    L, W = pitch_dim.length, pitch_dim.width
    stripe_width = L / N_STRIPES
    for i in range(N_STRIPES):
        fig.add_shape(
            type="rect",
            x0=i * stripe_width, x1=(i + 1) * stripe_width, y0=0, y1=W,
            fillcolor=GRASS_DARK if i % 2 == 0 else GRASS_LIGHT,
            line=dict(width=0),
            layer="below",
        )


def add_pitch_shapes(fig, pitch_dim):
    L, W = pitch_dim.length, pitch_dim.width
    pa_len, pa_w = pitch_dim.penalty_area_length, pitch_dim.penalty_area_width
    six_len, six_w = pitch_dim.six_yard_length, pitch_dim.six_yard_width
    circle_r = pitch_dim.circle_diameter / 2
    line_kwargs = dict(line=dict(color="white", width=1.6), layer="below")

    # Outer boundary
    fig.add_shape(type="rect", x0=0, y0=0, x1=L, y1=W, **line_kwargs)
    # Halfway line
    fig.add_shape(type="line", x0=L / 2, y0=0, x1=L / 2, y1=W, **line_kwargs)
    # Center circle + spot
    fig.add_shape(
        type="circle",
        x0=L / 2 - circle_r, y0=W / 2 - circle_r, x1=L / 2 + circle_r, y1=W / 2 + circle_r,
        **line_kwargs,
    )
    fig.add_shape(
        type="circle", x0=L / 2 - 0.4, y0=W / 2 - 0.4, x1=L / 2 + 0.4, y1=W / 2 + 0.4,
        fillcolor="white", line=dict(width=0), layer="below",
    )
    # Penalty areas + six-yard boxes, both ends
    for x0, x1 in [(0, pa_len), (L - pa_len, L)]:
        fig.add_shape(type="rect", x0=x0, y0=W / 2 - pa_w / 2, x1=x1, y1=W / 2 + pa_w / 2, **line_kwargs)
    for x0, x1 in [(0, six_len), (L - six_len, L)]:
        fig.add_shape(type="rect", x0=x0, y0=W / 2 - six_w / 2, x1=x1, y1=W / 2 + six_w / 2, **line_kwargs)
    # Penalty spots
    for spot_x in [pitch_dim.penalty_spot_distance, L - pitch_dim.penalty_spot_distance]:
        fig.add_shape(
            type="circle", x0=spot_x - 0.4, y0=W / 2 - 0.4, x1=spot_x + 0.4, y1=W / 2 + 0.4,
            fillcolor="white", line=dict(width=0), layer="below",
        )


def add_defensive_line(fig, x_display, x_m, team_name, color, pitch_width):
    # Densely sampled rather than a 2-point line: Plotly's hover triggers on
    # proximity to actual data points, not to the line itself, so only 2 points
    # (at each end) meant hover only worked right at the very top or bottom.
    n_points = 100
    x = [x_display] * n_points
    y = np.linspace(0, pitch_width, n_points)

    # All traces below share a legendgroup (see groupclick="togglegroup" in
    # build_figure) so that clicking the legend entry toggles the glow and the
    # dots together, instead of only the trace that happens to own the legend
    # entry.
    legendgroup = f"{team_name}_defline"

    # Soft glow: a few wider, near-transparent lines drawn first (so they sit
    # behind), shading both sides of the crisp line drawn on top of them.
    for glow_width, glow_opacity in [(60, 0.12), (40, 0.20), (22, 0.30)]:
        fig.add_trace(
            go.Scatter(
                x=x, y=y, mode="lines",
                line=dict(color=color, width=glow_width),
                opacity=glow_opacity,
                hoverinfo="skip",
                showlegend=False,
                legendgroup=legendgroup,
            )
        )

    # Built from round markers rather than a "dot"-dash line: Plotly's dash
    # styles use flat (SVG "butt") line caps, so a dashed "dot" style actually
    # renders as tiny squares, not circles. This is also the trace that owns
    # the legend entry, so its legend icon (one circle) exactly matches the
    # real dots on the pitch, rather than approximating them with a dash
    # pattern -- the same convention already used for the player-dot legend
    # entries (one circle standing in for eleven players).
    n_dots = 34
    fig.add_trace(
        go.Scatter(
            x=[x_display] * n_dots, y=np.linspace(0, pitch_width, n_dots),
            mode="markers",
            marker=dict(color=color, size=6, symbol="circle"),
            hovertemplate=f"Average distance between goal line and defensive actions = {x_m:.1f} m<extra></extra>",
            name=f"{team_name} — avg. defensive line",
            legendgroup=legendgroup,
        )
    )


def add_team_scatter(fig, team_df, team_name, fill_color, outline_color):
    fig.add_trace(
        go.Scatter(
            x=team_df["x"], y=team_df["y"],
            mode="markers",
            marker=dict(
                size=team_df["n_events"],
                sizemode="area",
                sizeref=2.0 * team_df["n_events"].max() / (34 ** 2),
                sizemin=10,
                symbol="circle",
                color=fill_color,
                line=dict(color=outline_color, width=1.8),
            ),
            text=team_df["name"],
            customdata=team_df[["x", "y", "n_events"]].to_numpy(),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Avg. position: (%{customdata[0]:.1f}, %{customdata[1]:.1f})<br>"
                "Involvements: %{customdata[2]}<extra></extra>"
            ),
            name=team_name,
        )
    )


def build_figure(positions, def_lines, pitch_dim):
    fig = go.Figure()
    add_grass_stripes(fig, pitch_dim)
    add_pitch_shapes(fig, pitch_dim)
    for team in TEAM_ACCENT:
        team_df = positions[positions["team"] == team]
        add_team_scatter(fig, team_df, team, MARKER_FILL[team], MARKER_OUTLINE[team])
    for _, row in def_lines.iterrows():
        add_defensive_line(fig, row["x_display"], row["x_m"], row["team"], TEAM_ACCENT[row["team"]], pitch_dim.width)

    fig.update_layout(
        title="Barcelona vs. Real Madrid — average player positions<br><sub>La Liga, 2 April 2016 (Barcelona 1-2 Real Madrid)</sub>",
        font=dict(family="Helvetica, Arial, Liberation Sans, DejaVu Sans, sans-serif", size=14),
        plot_bgcolor="white",
        paper_bgcolor="white",
        width=900,
        height=640,
        legend=dict(orientation="h", yanchor="bottom", y=1.16, xanchor="center", x=0.5, groupclick="togglegroup"),
        margin=dict(l=20, r=20, t=130, b=20),
    )
    fig.update_xaxes(visible=False, range=[-2, pitch_dim.length + 2])
    # StatsBomb defines y=0 as the top touchline, y=80 as the bottom (confirmed via
    # mplsoccer's own dim.top/dim.bottom); Plotly's default y-axis increases upward,
    # the opposite way, so the range is reversed here to match the real orientation.
    fig.update_yaxes(visible=False, range=[pitch_dim.width + 2, -2], scaleanchor="x", scaleratio=1)
    return fig


def main():
    events = sb.events(match_id=MATCH_ID)
    lineup_by_team = get_starting_xi(events)
    names = resolve_names(MATCH_ID, lineup_by_team)
    positions = average_positions(events, lineup_by_team, names)
    positions = mirror_team(positions, "Real Madrid", pitch_length=120, pitch_width=80)

    def_lines = average_defensive_line(events, lineup_by_team, pitch_length=PITCH_LENGTH_M)
    def_lines["x_display"] = def_lines["x"]
    real_madrid_mask = def_lines["team"] == "Real Madrid"
    def_lines.loc[real_madrid_mask, "x_display"] = 120 - def_lines.loc[real_madrid_mask, "x"]

    pitch = Pitch(pitch_type="statsbomb")
    fig = build_figure(positions, def_lines, pitch.dim)

    fig.write_html("figures/barca_real_average_positions.html", include_plotlyjs="cdn")
    fig.write_image("figures/barca_real_average_positions.png", scale=2)
    print("Saved figures/barca_real_average_positions.html and .png")
    print()
    print(positions[["team", "name", "position", "x", "y", "n_events"]].sort_values(["team", "x"]).to_string(index=False))
    print()
    print(def_lines[["team", "x", "x_m", "n_actions"]].to_string(index=False))


if __name__ == "__main__":
    main()
