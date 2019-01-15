# Factorio Inserter Test

These scripts generate blueprints containing various configurations of [Bob's
adjustable inserters](https://mods.factorio.com/mods/Bobingabout/bobinserters)
for the game [Factorio](http://factorio.com).

Fully researched, the inserter pickup and dropoff locations can independently
be in any location on a 7x7 grid. In addition, the dropoff location can have an
offset from a 3x3 grid, which is like a 20% nudge in the given direction.
Altogether, that's 7x7x7x7x9 for a grand total of 21,609.

Difficult to test that many configurations by hand. Enter automation!

# Method

I wrote a python script to create a 49x49 grid of inserters with an
accompanying timing circuit. Each inserter has a specific pickup and dropoff
location, according to its position in the grid. All inserters have the same
offset. I then ran this 9 times to get a version for each offset, and tested
those 9 versions separately. It looks like this.

![The grid](inserters.png)

You can test a blueprint yourself by applying power, then connecting a green
with from the constant combinator at the top left to the input of the leftmost
decider combinator. You'll need the Nixie Tubes mod for the timing display,
Bob's Logistics for the chests, and (obviously) Bob's adjustable inserters for
the inserters.

The raw results are in the results/ directory. Each result is a blueprint
containing the timing data for all configurations with a given offset.

# Observations

Much of this was already known, but here are some general observations of the
results.

- Smaller angles are faster.
- Longer arms can achieve smaller angles, and therefore are faster.
- Changing the arm length from pickup to dropoff slows down the cycle time significantly.
- The offset can affect the arm length, and therefore, the cycle time.

# Results

I've included two blueprints with the best inserters.

1. [This blueprint](testOffsetPerPos.bp) has a grid of inserters for every
possible pickup and dropoff configuration, with the fastest offset for that
configuration. (Note than many configurations have multiple offsets that are
equally fast. The blueprint includes only one offset per configuration, chosen
arbitrarily from the best.)

2. [This one](fasterThan300.bp) has only the very fastest inserters
(ones that transfer 2000 items faster than 300 ticks on my machine).

I also attempted to find a correlation between (swing angle, arm length) and
cycle time. That attempt is in the [angleAnalyze](angleAnalyze.py) script. I
couldn't get good results out of it, so I gave up. Maybe someone else can
figure it out.
