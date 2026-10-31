"""Render a 3-clip pressing video for LinkedIn."""

import json
import pickle
import subprocess
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np

import os as _os
_SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
FONT_DIR = _os.path.join(_SCRIPT_DIR, "fonts")
_bold_path = f"{FONT_DIR}/BarlowCondensed-Bold.ttf"
_semi_path = f"{FONT_DIR}/BarlowCondensed-SemiBold.ttf"
fm.fontManager.addfont(_bold_path)
fm.fontManager.addfont(_semi_path)
FONT_BOLD = fm.FontProperties(fname=_bold_path)
FONT_SEMI = fm.FontProperties(fname=_semi_path)
from matplotlib.animation import FuncAnimation
from mplsoccer import Pitch
from mplsoccer.soccer.markers import football_hexagon_marker, football_pentagon_marker

# ---------- Config ----------
CLIPS = [
    {"chain": 701, "subtitle": "Successful pressing sequence: clean recovery",            "extra_s": 5},
    {"chain": 495, "subtitle": "Successful pressing sequence: throw-in obtained",       "extra_s": 7},
    {"chain": 379, "subtitle": "Failed pressing sequence: holding team keeps the ball", "extra_s": 7},
]

FPS_TRACK = 10
ANIM_INTERVAL = 100   # ms per frame
ANIM_DPI = 150
PITCH_BG = "#3a6b35"
BLACK = "#000000"

N_OPENING_FRAMES = 40     # 4s opening title card
N_BLACK_TITLE_FRAMES = 30 # 3s black screen before each clip

ARROW_SCALE = 1
ARROW_WIDTH = 0.004

BALL_S_MIN = 60
BALL_S_MAX = 180
BALL_Z_CAP = 10.0

TEAM_COLORS = {
    866:  ("#e4002b", "#f2a900"),
    4177: ("#00205b", "#68b8e5"),
    1802: ("#f36c21", "#1a1a1a"),
    870:  ("#f7d417", "#003087"),
    1804: ("#1a1a1a", "#c8a64e"),
    2380: ("#6caddf", "#1c2c5b"),
    868:  ("#0e1e45", "#ffffff"),
    1805: ("#c8102e", "#f1be48"),
    871:  ("#5b2d8e", "#f2a900"),
    869:  ("#6cace4", "#1a3a6b"),
    867:  ("#ffcb05", "#1a1a1a"),
    2902: ("#e4002b", "#1a1a1a"),
    1803: ("#2d8a4e", "#1a1a1a"),
}

import tempfile as _tempfile
OUT_DIR = _tempfile.mkdtemp(prefix="pressing_render_")
FINAL_DIR = _SCRIPT_DIR

# ---------- Load data ----------
DATA_DIR = _SCRIPT_DIR

with open(f"{DATA_DIR}/data/skillcorner/pressing_configs.pkl", "rb") as f:
    configs = pickle.load(f)

REPO_RAW = "https://raw.githubusercontent.com/SkillCorner/opendata/master"
matches = json.loads(urllib.request.urlopen(f"{REPO_RAW}/data/matches.json").read())
home_team_ids = {m["id"]: m["home_team"]["id"] for m in matches}
away_team_ids = {m["id"]: m["away_team"]["id"] for m in matches}
team_names_map = {}
for m in matches:
    team_names_map[m["home_team"]["id"]] = m["home_team"]["short_name"]
    team_names_map[m["away_team"]["id"]] = m["away_team"]["short_name"]

# ---------- Load tracking (cache per match) ----------
from kloppy import skillcorner as kloppy_sc

_trk_cache = {}

def load_tracking(mid):
    if mid in _trk_cache:
        return _trk_cache[mid]
    print(f"  Downloading tracking for match {mid} ...")
    ds = kloppy_sc.load_open_data(match_id=mid, coordinates="skillcorner")
    store = {}
    for fr in ds.frames:
        pl = {}
        for p, pd in fr.players_data.items():
            if pd.coordinates is not None:
                pl[p.player_id] = (
                    p.team.team_id,
                    pd.coordinates.x + 52.5,
                    pd.coordinates.y + 34,
                )
        bc = fr.ball_coordinates
        store[fr.frame_id] = {
            "p": pl,
            "b": (
                (bc.x + 52.5) if bc else np.nan,
                (bc.y + 34) if bc else np.nan,
                (getattr(bc, "z", 0.0) or 0.0) if bc else 0.0,
            ),
        }
    del ds
    _trk_cache[mid] = store
    print(f"    {len(store)} frames cached")
    return store


# ---------- Render a black title card as a static MP4 ----------
def render_black_card(text, n_frames, out_path, figsize=(10, 7)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.set_dpi(ANIM_DPI)
    fig.patch.set_facecolor(BLACK)
    ax.set_facecolor(BLACK)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.5, text, fontsize=36, color="white",
            ha="center", va="center", transform=ax.transAxes,
            fontproperties=FONT_BOLD)

    def _update(i):
        return []

    anim = FuncAnimation(fig, _update, frames=n_frames, interval=ANIM_INTERVAL, blit=False)
    anim.save(out_path, writer="ffmpeg", dpi=ANIM_DPI,
              savefig_kwargs={"facecolor": BLACK})
    plt.close(fig)


# ---------- Render a pitch clip ----------
def render_pitch_clip(clip_cfg):
    chain_idx = clip_cfg["chain"]
    subtitle = clip_cfg["subtitle"]
    extra_s = clip_cfg["extra_s"]

    c = configs[chain_idx - 1]
    mid = c["match_id"]
    fs, fl = c["frame_start"], c["frame_last"]
    fl_ext = fl + int(extra_s * FPS_TRACK)

    match_info = next(m for m in matches if m["id"] == mid)
    home_name = match_info["home_team"]["short_name"]
    away_name = match_info["away_team"]["short_name"]
    press_tid = home_team_ids[mid] if c["is_home_pressing"] else match_info["away_team"]["id"]
    hold_tid = home_team_ids[mid] if not c["is_home_pressing"] else match_info["away_team"]["id"]
    press_name = home_name if c["is_home_pressing"] else away_name
    hold_name = away_name if c["is_home_pressing"] else home_name
    press_color, press_edge = TEAM_COLORS.get(press_tid, ("#e74c3c", "#ffffff"))
    hold_color, hold_edge = TEAM_COLORS.get(hold_tid, ("#3498db", "#ffffff"))

    trk = load_tracking(mid)
    fids = sorted(f for f in trk if fs <= f <= fl_ext)
    N = len(fids)

    anim_frames = []
    for i, fid in enumerate(fids):
        rd = trk[fid]
        press, hold = {}, {}
        for pid, (tid, x, y) in rd["p"].items():
            (press if tid == press_tid else hold)[pid] = (x, y)
        press_vel = {}
        if i > 0:
            prev_press = anim_frames[i - 1]["press"]
            for pid, (x, y) in press.items():
                if pid in prev_press:
                    px0, py0 = prev_press[pid]
                    press_vel[pid] = ((x - px0) * FPS_TRACK, (y - py0) * FPS_TRACK)
        anim_frames.append({"press": press, "hold": hold, "ball": rd["b"], "press_vel": press_vel})

    pitch = Pitch(pitch_type="custom", pitch_length=105, pitch_width=68,
                  pitch_color=PITCH_BG, line_color="white")
    fig, ax = pitch.draw(figsize=(10, 7))
    fig.set_dpi(ANIM_DPI)
    fig.patch.set_facecolor(PITCH_BG)

    hold_scat = ax.scatter([], [], s=140, c=hold_color, edgecolors=hold_edge, zorder=3)
    press_scat = ax.scatter([], [], s=140, c=press_color, edgecolors=press_edge, zorder=3)
    ball_hex = ax.scatter([], [], s=60, c="white", edgecolors="black",
                          linewidths=0.5, marker=football_hexagon_marker, zorder=5)
    ball_pent = ax.scatter([], [], s=60, c="black", edgecolors="black",
                           linewidths=0.5, marker=football_pentagon_marker, zorder=5)

    _arrow_artists = []

    leg = ax.legend(
        [hold_scat, press_scat],
        [hold_name + " (holding)", press_name + " (pressing)"],
        loc="upper right", fontsize=16,
        bbox_to_anchor=(1.1, 1.12),
        facecolor=PITCH_BG, edgecolor=PITCH_BG,
        labelcolor="white",
    )
    for text in leg.get_texts():
        text.set_fontproperties(FONT_SEMI)

    title_line = f"{home_name} vs {away_name}\n{subtitle}"
    ttl = ax.set_title(title_line, color="white", pad=15)
    ttl.set_fontproperties(FONT_BOLD)
    ttl.set_fontsize(20)

    def _update(i):
        f = anim_frames[i]

        if f["hold"]:
            hxy = np.array(list(f["hold"].values()))
            hold_scat.set_offsets(hxy)
        else:
            hold_scat.set_offsets(np.empty((0, 2)))

        if f["press"]:
            pxy = np.array(list(f["press"].values()))
            press_scat.set_offsets(pxy)
        else:
            press_scat.set_offsets(np.empty((0, 2)))

        bx, by, bz = f["ball"]
        ball_hex.set_offsets([[bx, by]])
        ball_pent.set_offsets([[bx, by]])
        z_frac = min(max(bz, 0.0), BALL_Z_CAP) / BALL_Z_CAP
        ball_s = BALL_S_MIN + (BALL_S_MAX - BALL_S_MIN) * z_frac
        ball_hex.set_sizes([ball_s])
        ball_pent.set_sizes([ball_s])

        for a in _arrow_artists:
            a.remove()
        _arrow_artists.clear()

        pv = f["press_vel"]
        if f["press"] and pv:
            pids_with_vel = [pid for pid in f["press"] if pid in pv]
            if pids_with_vel:
                qx = np.array([f["press"][pid][0] for pid in pids_with_vel])
                qy = np.array([f["press"][pid][1] for pid in pids_with_vel])
                qu = np.array([pv[pid][0] for pid in pids_with_vel]) / ARROW_SCALE
                qv = np.array([pv[pid][1] for pid in pids_with_vel]) / ARROW_SCALE
                q = ax.quiver(qx, qy, qu, qv, color=press_color, alpha=0.5,
                              scale=1, scale_units="xy", angles="xy",
                              width=ARROW_WIDTH, headwidth=4, headlength=5, zorder=4)
                _arrow_artists.append(q)

        return hold_scat, press_scat, ball_hex, ball_pent

    return fig, _update, N, title_line


# ---------- Main ----------
print("=== Rendering pressing video ===\n")
clip_paths = []
part = 0

# 1. Opening title card on black
print(f"Rendering opening title card ({N_OPENING_FRAMES} frames) ...")
opening_path = f"{OUT_DIR}/part_{part:02d}.mp4"
render_black_card("Pressing effectiveness analysis\nSkillCorner tracking data",
                  N_OPENING_FRAMES, opening_path)
clip_paths.append(opening_path)
part += 1
print(f"  Saved {opening_path}")

# 2. For each clip: black title card + pitch animation
for i, clip_cfg in enumerate(CLIPS):
    c = configs[clip_cfg["chain"] - 1]
    mid = c["match_id"]
    match_info = next(m for m in matches if m["id"] == mid)
    home_name = match_info["home_team"]["short_name"]
    away_name = match_info["away_team"]["short_name"]
    title_text = f"{home_name} vs {away_name}\n{clip_cfg['subtitle']}"

    # Black title card
    print(f"\nRendering black title for clip {i+1}/3 ({N_BLACK_TITLE_FRAMES} frames) ...")
    black_path = f"{OUT_DIR}/part_{part:02d}.mp4"
    render_black_card(title_text, N_BLACK_TITLE_FRAMES, black_path)
    clip_paths.append(black_path)
    part += 1
    print(f"  Saved {black_path}")

    # Pitch animation
    print(f"Rendering pitch clip {i+1}/3: chain {clip_cfg['chain']} ...")
    fig, update_fn, n_frames, _ = render_pitch_clip(clip_cfg)
    anim = FuncAnimation(fig, update_fn, frames=n_frames, interval=ANIM_INTERVAL, blit=False)
    anim_path = f"{OUT_DIR}/part_{part:02d}.mp4"
    anim.save(anim_path, writer="ffmpeg", dpi=ANIM_DPI,
              savefig_kwargs={"facecolor": PITCH_BG})
    plt.close(fig)
    clip_paths.append(anim_path)
    part += 1
    print(f"  Saved {anim_path} ({n_frames} frames)")

# 3. Concatenate all parts
concat_list = f"{OUT_DIR}/concat.txt"
with open(concat_list, "w") as f:
    for p in clip_paths:
        f.write(f"file '{p}'\n")

final_path = f"{FINAL_DIR}/pressing_linkedin.mp4"
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", concat_list, "-c", "copy", final_path
], check=True)

print(f"\n=== Done! Final video: {final_path} ===")
print(f"Parts: {len(clip_paths)} segments")
