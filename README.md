# Football Aggression Index

A defensive "pressing aggression" score for football (soccer) teams, built from StatsBomb open event data, grounded in evolutionary game theory (EGT).

## Motivation

This project builds an aggression score from event data and validates it against known pressing identities (Barcelona, Atlético, Napoli) and known non-pressing but strong teams (Leicester, PSG) before trusting it for anything else.

"Aggression" is used here in the EGT/Hawk-Dove sense — willingness to contest a resource — not the colloquial sense of physicality or fouls. Concretely, the score measures how often a team ventures into the opponent's own territory to contest the ball, not how hard it tackles or how many fouls it commits.

The longer-term motivation is framed in EGT terms. The classic Hawk-Dove-Bourgeois-Antibourgeois ownership game gives four strategies, where "ownership" maps naturally onto home/away status in football (home = territory owner):

- **Hawk** — aggressive everywhere
- **Dove** — passive everywhere
- **Bourgeois** — aggressive at home, passive away (conditions on ownership)
- **Antibourgeois** — the reverse

If a team's aggression score at home consistently differs from its score away, that's evidence for a conditional (Bourgeois/Antibourgeois) strategy rather than a fixed (Hawk/Dove) one. The score is kept continuous rather than forced into these four labels — most teams will sit somewhere in the middle of a home-aggression vs. away-aggression plot, not in a corner.

## Data

StatsBomb open data, **"2015/16 Big 5 Leagues"** release, 2015/16 season only — restricted to the Premier League, La Liga, Serie A, and Ligue 1. Bundesliga is excluded: the open-data release only covers one team's (Bayer Leverkusen) matches for that competition, not the full round-robin, so it can't support team-vs-team comparisons. Ligue 1 is also missing 3 of its 380 fixtures in the open data; the other three leagues are complete (380/380, 20 teams each).

## Aggression score — definition

The raw aggression score is a single metric, **forward press rate**: the number of defensive-action *attempts* — pressures, tackles, interceptions, and fouls committed, regardless of outcome — a team makes while the ball is in the opponent's own half, per opponent possession.

Computed per team, per match, from event data. Two design choices matter:

- **Attempts, not successes.** Whether a tackle succeeds reflects player skill; whether a team attempts it reflects strategy. Counting only successful regains would conflate style with quality — exactly the confound this project exists to avoid (see the Leicester City validation case below).
- **Zone-restricted to the opponent's half.** A team that only engages once the ball reaches its own third scores near zero here, no matter how efficient it is once the ball arrives deep. This is what ties the score to territory in the EGT sense, rather than to generic defensive workrate.

This replaced an earlier design that combined five separate components (PPDA, pressures per possession, counterpressing rate, a defensive-line proxy, and fouls in the middle/attacking third) via z-scoring and averaging. That approach was dropped: combining heterogeneous, correlated metrics into a z-scored composite gave a number with no direct interpretation, and some of those components (e.g. pressures per possession) weren't zone-restricted at all, so they didn't actually capture territorial behavior. Forward press rate is a single, directly interpretable rate that subsumes what those components were reaching for.

## Confounds to control for

A raw aggression score conflates style with context. Before attributing a score to team identity, the following are controlled for:

- **Match state** — teams press harder when chasing a game late on. First halves only is one mitigation, since tactical adjustments cluster around half-time.
- **Manager identity** — a mid-season managerial change (e.g. Liverpool, Klopp, October 2015) can mean two genuinely different tactical identities within one season.
- **Dead rubbers** — matches where the title is already won or relegation (or non-relegation) already confirmed at kickoff.
- **Quality mismatch** — weaker teams often sit deeper regardless of usual style; pre-match betting odds asymmetry is used as a proxy for the quality gap.

## Validation

Before the score is trusted for any downstream analysis:

- **Face validity**: known high-pressing teams score high; Leicester City (2015/16 champions, not a pressing side) scores low despite being the best team in the league that season — this is the key test that the score isn't just quality in disguise.
- **High-variance teams** are not forced into a single label. The score stays continuous; if categorization is reported at all, it's probabilistic (e.g. % of matches above league median), and high variance is checked against the manager-spell and dead-rubber flags before being called "real" style inconsistency.

## Roadmap

This first pass uses event data only. A planned second phase incorporates tracking data to complement the event-based measures.

## About

Part of a portfolio project transitioning from evolutionary game theory research to sports data science.
