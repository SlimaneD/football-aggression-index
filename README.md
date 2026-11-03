# Football Aggression Index

[![Launch Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/SlimaneD/football-aggression-index/master?labpath=territorial_behavior_in_football.ipynb)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SlimaneD/football-aggression-index/blob/master/territorial_behavior_in_football.ipynb)

An investigation of territorial behavior and pressing aggression in football (soccer), grounded in evolutionary game theory (EGT). The project has two parts: Part 1 measures how aggressively teams press in the opponent's half using event data from four European leagues, and tests whether the home/away asymmetry matches what the Hawk-Dove ownership game predicts. Part 2 takes a complementary angle using SkillCorner tracking data from the Australian A-League: instead of asking *how often* teams press, it asks what makes a pressing attempt *succeed* and whether home teams employ more often successful pressing strategies than away teams. This second part involves training ML and deep learning models on the full spatial configuration of all 22 players.

---

# Part 1: The Bourgeois hypothesis (European leagues, event data)

## Motivation

This project builds an aggression score from event data, then stress-tests it on a hard case (Barcelona's 2015/16 side; see Key Findings below).

"Aggression" is used here in the Hawk-Dove sense (willingness to contest a resource), not the colloquial sense of physicality or fouls. Concretely, the score measures how often a team ventures into the opponent's own territory to contest the ball.

One common observation is that home teams tend to be more tactically aggressive, i.e., they contest the ball higher up the pitch, while away teams tend to sit back. This home/away asymmetry is exactly what a classical extension of the Hawk-Dove game predicts, once "ownership" of a contested resource enters the picture: a team playing at home is the *owner* of the territory, a team playing away is the *intruder*, and that asymmetry alone is enough to generate four candidate strategies:

| Strategy | Behavior as owner | Behavior as intruder |
|---|---|---|
| Hawk | Escalate | Escalate |
| Dove | Retreat | Retreat |
| Bourgeois | Escalate | Retreat |
| Anti-bourgeois | Retreat | Escalate |

The Bourgeois strategy is of particular interest here because it matches the home/away asymmetry just described. It is also an evolutionarily stable strategy (ESS): in a population of animals playing this game, if every individual adopted Bourgeois, no individual could gain an advantage by switching to one of the other three strategies, an uninvadable state.

If a team's aggression score at home consistently differs from its score away, that's evidence for a conditional (Bourgeois/Antibourgeois) strategy rather than a fixed (Hawk/Dove) one. The score is kept continuous rather than forced into these four labels; most teams will sit somewhere in the middle of a home-aggression vs. away-aggression plot, not in a corner.

## Key findings

- **The Bourgeois convention dominates.** 75 of 80 teams (93.8%) across four major European leagues press more when playing at home than away, a highly significant effect in every league individually, the pattern predicted by the Hawk-Dove-Bourgeois-Antibourgeois ownership game.
- **Barcelona (2015/16) is a useful stress test.** Reputation predicts a top pressing score; the data places them 22nd of 80 in Europe. That gap traces to two real, checked effects: Barcelona's opponents have the fewest possessions per match in La Liga (a small-denominator effect) and Barcelona's own style leans on retaining the ball rather than repeatedly winning it back. Relative to their league rivals specifically, Barcelona classifies as **Hawk** (aggressive everywhere), not Bourgeois.
- **Event data and tracking data can disagree, informatively.** An independent check using Metrica Sports' open tracking data initially found the *opposite* pattern (the away team looked more territorially committed than home). Investigating why traced the mismatch to scoreline, not baseline style: the trailing team's tracking-based territorial presence is inflated by the leading team choosing to circulate the ball deep, not by the trailing team actively pressing more. Once scoreline is held constant, the tracking data flips back to match the event-data direction. See the tracking notebook below for the full investigation.

## Data

StatsBomb open data, **"2015/16 Big 5 Leagues"** release, 2015/16 season only, restricted to the Premier League, La Liga, Serie A, and Ligue 1. Bundesliga is excluded: the open-data release only covers one team's (Bayer Leverkusen) matches for that competition, not the full round-robin, so it can't support team-vs-team comparisons. Ligue 1 is also missing 3 of its 380 fixtures in the open data; the other three leagues are complete (380/380, 20 teams each).

A companion analysis uses Metrica Sports' openly available player-tracking data (one anonymized match) as an independent, positional cross-check on the event-based score.

Both StatsBomb's and Metrica Sports' data remain subject to their own respective terms of use, not this repository's license. See [StatsBomb's open data terms](https://github.com/statsbomb/open-data) and [Metrica Sports' sample data terms](https://github.com/metrica-sports/sample-data).

## Aggression score: definition

The raw aggression score is a single metric, **forward press rate**: the number of defensive-action *attempts* (pressures, tackles, interceptions, and fouls committed, regardless of outcome) a team makes while the ball is in the opponent's half, per opponent possession.

Computed per team, per match, from event data. Two design choices matter:

- **Attempts, not successes.** Whether a tackle succeeds reflects player skill; whether a team attempts it reflects strategy. Counting only successful regains would conflate style with quality, exactly the confound this project exists to avoid (see the Barcelona case study below).
- **Zone-restricted to the opponent's half.** A team that only engages once the ball reaches its own third scores near zero here, no matter how efficient it is once the ball arrives deep. This is what ties the score to territory in the EGT sense, rather than to generic defensive workrate.

Forward press rate is deliberately a single, directly interpretable rate rather than a composite blending several metrics (PPDA, pressures per possession, counterpressing rate, a defensive-line proxy, fouls in the middle/attacking third) via z-scoring and averaging. A z-scored composite of heterogeneous, correlated metrics gives a number with no direct interpretation, and not every candidate component is zone-restricted to the opponent's half (pressures per possession, for instance, isn't), so folding them in would dilute the territorial signal the score is built to capture.

## Confounds

A raw aggression score can conflate style with context. Two threats are directly tested here; two more are identified but not yet controlled for.

**Tested:**
- **Match state.** Teams press harder when chasing a game late on. A paired first-half-vs-second-half comparison checks whether this shifts the raw score in a way that would bias team-level comparisons.
- **Quality mismatch, qualitatively.** The Barcelona case study directly checks whether a low score is actually a quality/possession-share artifact (opponents having fewer possessions to press) rather than a style difference. See `data/la_liga_diagnostics.csv` and the diagnostics section of the appendix notebook.

**Identified, not yet controlled for:**
- **Manager identity.** A mid-season managerial change (e.g. Liverpool, Klopp, October 2015) can mean two genuinely different tactical identities within one season, currently averaged together.
- **Dead rubbers.** Matches where the title, relegation, or European qualification is already effectively decided at kickoff are not excluded.

## Validation

Before the score is trusted for any downstream analysis:

- **Face validity, stress-tested on a hard case.** Barcelona's 2015/16 side is used as the sternest available test: about as strong a pressing reputation as exists in the dataset. The gap between that reputation and its raw ranking (see Key Findings above) is investigated rather than dismissed, and both explanations found for it are checked directly against the underlying event data rather than assumed.
- **Teams aren't forced into a single label.** The home/away scatter plot shows each team's position with a ±1-standard-error ellipse, not just a point estimate, so imprecisely-estimated teams are visually distinguishable from confidently-estimated ones. The La Liga quadrant classification goes further: teams within a buffer zone around the league median on either axis are labeled Uncategorizable rather than forced into Hawk/Dove/Bourgeois/Antibourgeois; five of La Liga's 20 teams land there.

## Notebooks: where to start

Five notebooks live in this repo. Three are the polished analysis, meant to be read in this order:

1. **[`territorial_behavior_in_football.ipynb`](territorial_behavior_in_football.ipynb) (start here)** ([Binder](https://mybinder.org/v2/gh/SlimaneD/football-aggression-index/master?labpath=territorial_behavior_in_football.ipynb), [Colab](https://colab.research.google.com/github/SlimaneD/football-aggression-index/blob/master/territorial_behavior_in_football.ipynb)). The main narrative: the Hawk-Dove framing, forward press rate, the European ranking, the Barcelona case study, and the Bourgeois-hypothesis tests.
2. **[`validation_appendix.ipynb`](validation_appendix.ipynb)**: supporting technical validation in full detail: the complete pressing-efficiency investigation, per-match pitch visualizations, and further statistical robustness checks referenced from the main narrative.
3. **[`tracking_defensive_line.ipynb`](tracking_defensive_line.ipynb)**: the independent tracking-data cross-check described in Key Findings above.

The remaining notebook, [`explore_statsbomb_2015_16.ipynb`](explore_statsbomb_2015_16.ipynb), is a working/exploratory notebook kept for transparency, not part of the polished narrative.

Separately, [`OwnershipGame.ipynb`](OwnershipGame.ipynb) builds the Hawk-Dove-Bourgeois-Antibourgeois replicator-dynamics phase portraits referenced in the Motivation section above, using the [pynamo-egt](https://pypi.org/project/pynamo-egt/) library. This constitutes pure evolutionary-game-theory background, with no reference to football data.

## Reproducing this analysis

```bash
pip install -r requirements.txt
jupyter lab
```

No API keys or manual downloads needed: `statsbombpy` fetches StatsBomb's open data live, and the tracking notebook downloads Metrica Sports' sample match automatically on first run. Data is cached locally under `data/` after the first run (gitignored, so a fresh clone re-fetches everything).

The Binder and Colab badges above open the main narrative notebook (`territorial_behavior_in_football.ipynb`) without a local install. It only reads small, already-computed CSVs bundled in the repo, so it runs in a few seconds either way.

The notebook(s) in `deep_learning/` require a separate environment; see Part 2 below.

---

# Part 2: Pressing effectiveness (Australian A-League, tracking data)

## Motivation

Part 1 measured one dimension of pressing aggression: how often teams contest the ball in the opponent's half. Part 2 addresses the other dimension: how hard they contest, and whether it pays off. Does pressing more aggressively actually lead to regaining the ball? And does it pay off differently for home and away teams?

Using SkillCorner's open tracking data (A-League 2024/25, 20 matches), this part extracts pressing chains and trains models to predict their outcome (ball regain vs. disruption only) from the spatial snapshot of all 22 players at the last frame of each pressing chain.

## Approach

Two modeling layers, both working from the raw (x, y) coordinates plus velocities of every player on the pitch:

1. **Logistic regression on hand-crafted features.** Closing speed of the nearest pressing player, numerical superiority around the ball, distance to the goal line, and home/away status. Interpretable coefficients and partial dependence plots let us ask which tactical ingredients matter most.
2. **DeepSets.** A permutation-invariant deep learning architecture (phi network per player, sum pooling, rho classifier) that takes the full 22-player configuration as input, with no hand-crafted features. Tests whether the raw spatial geometry carries predictive signal beyond what the logistic regression captures.

## Key findings

- **Both dimensions of pressing aggressiveness increase the probability of regain.** Higher closing speed (contesting harder) and greater numerical superiority near the ball (contesting with more players) both raise the probability of regaining possession, with numerical superiority showing the stronger effect.
- **Home teams gain a pressing advantage that is not explained by pressing style.** Home pressing succeeds more often than away pressing (42.8% vs 37.4%, p=0.046), yet home and away teams show no significant difference in closing speed or numerical commitment. The advantage appears to operate through the opponent's response rather than through the pressing team's behavior.
- **The DeepSets model matches logistic regression performance** (CV AUC 0.66 vs 0.62), suggesting that the hand-crafted features already capture the main spatial signal. A temporal extension (Conv1D over five keyframes) does not improve on the snapshot model, likely because more training data is needed before extra parameters help.
- **The home advantage in pressing connects back to the Bourgeois framework.** Partial dependence analysis shows the home edge is additive: home teams benefit from a flat probability bonus regardless of how they press, consistent with a psychological or crowd-driven effect on the defending team rather than a tactical difference.

## Data

SkillCorner open tracking data, accessed via the [kloppy](https://github.com/kloppy-project/kloppy) library. 20 A-League 2024/25 matches, 10 Hz tracking. Pressing chains are extracted from SkillCorner's annotated pressing events and linked to the frame-level tracking data. See `deep_learning/data/` for cached intermediate files.

SkillCorner's data is subject to its own [terms of use](https://github.com/SkillCorner/opendata).

## Notebook

**[`deep_learning/MLpressing.ipynb`](deep_learning/MLpressing.ipynb)** contains the full analysis: data extraction, feature engineering, logistic regression, DeepSets, temporal modeling, and the interpretation section connecting the results back to Part 1's Bourgeois framework.

## Reproducing this analysis

The deep learning notebook requires PyTorch and kloppy. A conda environment file is provided:

```bash
conda env create -f deep_learning/environment.yml
conda activate football-dl
```

SkillCorner tracking data is downloaded automatically on first run via kloppy.

`render_video.py` generates the pressing animation video (three example pressing chains with team colors and velocity arrows) used for the LinkedIn post accompanying this project.

---

## Roadmap

Open direction: testing both parts' findings on a larger tracking or event-data release if one becomes available, to assess how the Bourgeois pattern and the pressing effectiveness results generalize beyond the current datasets.

## License

Code and analysis in this repository are released under the [MIT License](LICENSE). The underlying StatsBomb, Metrica Sports, and SkillCorner data are not (see the Data sections above).