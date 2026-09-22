# Football Aggression Index

A defensive "pressing aggression" score for football (soccer) teams, built from StatsBomb open event data, grounded in evolutionary game theory (EGT).

## Motivation

Team quality and team *style* are easy to conflate. Leicester City won the 2015/16 Premier League with a deep block and counter-attacks, not high pressing — a metric that can't tell that apart from "how good is this team" isn't measuring style at all. This project builds a composite aggression score from event data and validates it against known pressing identities (Barcelona, Bayern Munich, Dortmund, Atlético, Napoli) and known non-pressing but strong teams (Leicester, PSG) before trusting it for anything else.

The longer-term motivation is framed in EGT terms. The classic Hawk-Dove-Bourgeois-Antibourgeois ownership game gives four strategies, where "ownership" maps naturally onto home/away status in football (home = territory owner):

- **Hawk** — aggressive everywhere
- **Dove** — passive everywhere
- **Bourgeois** — aggressive at home, passive away (conditions on ownership)
- **Antibourgeois** — the reverse

If a team's aggression score at home consistently differs from its score away, that's evidence for a conditional (Bourgeois/Antibourgeois) strategy rather than a fixed (Hawk/Dove) one. The score is kept continuous rather than forced into these four labels — most teams will sit somewhere in the middle of a home-aggression vs. away-aggression plot, not in a corner.

## Data

StatsBomb open data, **"2015/16 Big 5 Leagues"** release: full round-robin coverage of the Premier League, La Liga, Bundesliga, Serie A, and Ligue 1, 2015/16 season only.

## Aggression score — components

Computed per team, per match, from event data:

- PPDA (opponent passes completed before a defensive action, defensive two-thirds)
- Pressures per opponent possession
- Counterpressing rate (regains within ~5 seconds of losing the ball)
- Defensive line proxy (average distance from own goal of tackles/interceptions/pressures)
- Fouls committed in the middle/attacking third

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
