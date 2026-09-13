# Reusable Musical Randomizer Algorithms

This file preserves the musical randomization logic developed for the UNO Synth Pro editor as reusable reference material for future projects. It is intentionally kept outside the runtime project structure.

## Provenance

Recovered from the UNO Synth Pro Editor codebase (`app.py`) and project notes. The SYNTH randomizer was accepted/frozen in the project around v1.46 and remained in later builds. The sequencer randomizer appears alongside it in the same codebase.

These implementations were developed for this project; they are not copied from a third-party algorithm. External links below document the underlying general techniques used: weighted choice, triangular distribution, Gaussian distribution, and random walk.

## 1. Synth randomizer

### Core idea

Do not uniformly randomize every parameter across its full range. Generate musically plausible patches by combining:

- weighted/discrete choices for musically meaningful values;
- triangular distributions biased toward useful centers;
- correlated oscillator level ranges;
- conservative envelope ranges;
- low-probability toggles for aggressive/special features;
- bounded FX ranges;
- preservation of the existing sequencer.

### Triangular helper

```python
def rand_tri(low, high, mode=None):
    return int(round(random.triangular(
        low,
        high,
        (low + high) / 2 if mode is None else mode
    )))
```

The important feature is `mode`: values cluster around a useful musical region instead of being uniformly distributed.

### Oscillators

Use one strong source and make secondary layers less likely to dominate.

```python
OSC1_TUNE = random.choice([-12, 0, 0, 0, 7, 12])
OSC2_TUNE = random.choice([-12, -7, 0, 0, 7, 12])
OSC3_TUNE = random.choice([-12, 0, 0, 12])

OSC1_FINE  = rand_tri(-12, 12, 0)
OSC2_FINE  = rand_tri(-18, 18, 0)
OSC3_FINE  = rand_tri(-18, 18, 0)

OSC1_LEVEL = rand_tri(85, 127, 118)
OSC2_LEVEL = rand_tri(0, 112, 55)
OSC3_LEVEL = rand_tri(0, 100, 35)
NOISE      = rand_tri(0, 45, 5)
```

This produces tonal hierarchy instead of three equally loud random oscillators.

### Filters

Bias cutoff toward useful open/mid positions and resonance toward restrained values.

```python
F1_CUTOFF = rand_tri(28, 127, 82)
F1_RES    = rand_tri(0, 95, 22)
F1_ENV    = rand_tri(-48, 64, 22)
F1_TRACK  = rand_tri(-80, 200, 70)

F2_CUTOFF = rand_tri(35, 127, 90)
F2_RES    = rand_tri(0, 85, 18)
F2_ENV    = rand_tri(-42, 64, 18)
F2_TRACK  = rand_tri(-60, 200, 60)

FILTER_SPACING = rand_tri(-40, 40, 0)
```

Filter modes are weighted instead of equally likely:

```python
F1_MODE = random.choices(range(5), weights=[5, 3, 2, 1, 0.3])[0]
F2_MODE = random.choices(range(6), weights=[4, 3, 2, 2, 0.3, 0.3])[0]
```

### Envelopes

Bias toward playable attack/decay/release values and reasonably strong sustain.

```python
FENV_A = rand_tri(0, 70, 8)
FENV_D = rand_tri(5, 100, 35)
FENV_S = rand_tri(45, 127, 95)
FENV_R = rand_tri(3, 105, 28)

AENV_A = rand_tri(0, 60, 5)
AENV_D = rand_tri(5, 100, 28)
AENV_S = rand_tri(55, 127, 105)
AENV_R = rand_tri(3, 100, 25)
```

### LFO / glide / FX

```python
LFO1_RATE = rand_tri(5, 110, 42)
LFO2_RATE = rand_tri(5, 110, 48)
LFO1_FADE = rand_tri(0, 90, 12)
LFO2_FADE = rand_tri(0, 90, 12)
GLIDE     = rand_tri(0, 75, 8)

DRIVE        = rand_tri(0, 80, 12)
MOD_AMOUNT   = rand_tri(0, 90, 25)
DELAY_AMOUNT = rand_tri(0, 75, 18)
REV_AMOUNT   = rand_tri(0, 80, 24)
```

Rare/special switches use probabilities rather than 50/50 randomization:

```python
SYNC2      = random.random() < 0.18
SYNC3      = random.random() < 0.12
RING       = random.random() < 0.10
DELAY_SYNC = random.random() < 0.35
```

### General reusable rule

For musical controls, define:

```text
minimum + maximum + preferred center + probability
```

instead of simply choosing any legal value.

---

## 2. Sequencer randomizer

### Core idea

Use a scale-constrained random walk instead of independently random notes. Combine it with rhythmic density, Gaussian velocity variation, bounded gate/length values, occasional accent/tie, and smooth automation.

### Root and scale

```python
root = random.choice([36, 48, 48, 60])
scale = random.choice([
    [0, 2, 3, 5, 7, 8, 10],      # minor-like
    [0, 2, 4, 5, 7, 9, 11],      # major-like
    [0, 3, 5, 7, 10],             # pentatonic-like
])
```

The repeated `48` biases the register toward the middle octave.

Create a bounded pitch pool across several octaves:

```python
pool = sorted({
    root + 12 * octave + degree
    for octave in range(-1, 3)
    for degree in scale
    if 24 <= root + 12 * octave + degree <= 84
})
```

### Random walk

Instead of selecting every pitch independently, move around the scale pool:

```python
step = random.choices(
    [-2, -1, 0, 1, 2],
    weights=[1, 4, 6, 4, 1]
)[0]

index = clamp(index + step, 0, len(pool) - 1)
note = pool[index]
```

This strongly favors repetition and neighboring scale tones, while still allowing occasional larger movement.

### Density / rests

```python
density = random.uniform(0.52, 0.82)
```

Each step is active only if it passes the density test. This prevents the generated pattern from becoming a wall of notes.

### Humanized notes

```python
velocity = clamp(int(random.gauss(98, 13)), 1, 127)
gate = random.randint(5, 10)
length = random.choice([0.5, 0.75, 1.0, 1.0, 1.25])
accent = random.randint(82, 127) if random.random() < 0.18 else 0
tie = random.random() < 0.08
probability = random.randint(72, 100)
```

The duplicate `1.0` weights normal note length more heavily without needing a separate weighted-choice table.

### Empty steps

For rests, keep sane defaults instead of random garbage:

```python
notes = []
velocity = random.randint(70, 100)
gate = random.randint(4, 8)
length = random.choice([0.5, 0.75, 1.0])
accent = 0
tie = False
probability = random.randint(80, 100)
```

### Smooth automation random walk

Automation lanes should also move gradually:

```python
value = random.randint(38, 90)
for step in range(sequence_length):
    value = clamp(value + random.randint(-14, 14), 8, 119)
    automation[step] = value
```

This creates evolving modulation instead of unrelated jumps on every step.

---

## 3. Why these algorithms work well

The common principle is **constrained randomness**:

1. Use the full legal range only where arbitrary variation is musically harmless.
2. Bias important controls toward useful regions.
3. Use weighted choices for discrete musical decisions.
4. Correlate related parameters instead of randomizing them independently.
5. Use random walks for time/pitch evolution so adjacent events have continuity.
6. Use Gaussian/triangular distributions for human-like concentration around a center.
7. Make unusual behavior intentionally rare.
8. Preserve unrelated state when randomizing one subsystem.

These ideas are reusable for synthesizers, drum machines, MIDI generators, generative effects, and procedural music tools.

## External references for the underlying techniques

- Python `random` module (`choice`, `choices`, `triangular`, `gauss`, `uniform`):
  https://docs.python.org/3/library/random.html
- Random walk concept, Wolfram MathWorld:
  https://mathworld.wolfram.com/RandomWalk.html

## Project-source reference

The recovered implementation is in the UNO Pro Advanced / UNO Synth Pro Editor code history around the v1.46-v1.52 period, in `app.py`, functions:

```text
randomize_synth()
seq_randomize()
_rand_tri()
```

Keep this file as reusable reference material even if future application code changes.