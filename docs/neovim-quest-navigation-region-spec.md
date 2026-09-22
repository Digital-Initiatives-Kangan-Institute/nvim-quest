# NeoVim Quest Navigation Region Specification

## Purpose

This document defines the Navigation region for the NeoVim Quest minimum viable product.

The region establishes the core learning philosophy for the game:

> The player solves navigation problems, not command exercises.

Each lesson introduces a related set of motions and then requires the learner to navigate through multiple destinations. This encourages the learner to compare available motions and select the most appropriate command for each situation.

Single-target activities should be used sparingly and primarily when introducing a completely new interaction. Most levels should use navigation chains containing several ordered targets.

## Region Goal

The learner will move through text efficiently by selecting an appropriate motion for each navigation requirement.

The region covers:

```text
h j k l
w b e
0 ^ $
gg G
f<char> t<char>
/ n N
```

## Learning Model

Each lesson should follow this general progression:

1. Introduce related commands together.
2. Demonstrate the contrast between those commands.
3. Provide an ordered chain of navigation targets.
4. Remove command prompts as the learner progresses.
5. Finish with an outcome-based challenge requiring command selection.

The intended learning cycle is:

```text
Learn
  ↓
Practise
  ↓
Compare
  ↓
Apply
  ↓
Optimise
```

## General Level Requirements

Each level should define:

- Level identifier
- Title
- Lesson
- Narrative or context
- Starting text
- Starting cursor position
- Ordered navigation targets
- Available commands
- Newly introduced commands
- Completion conditions
- Hint sequence
- Reference or master solution
- Scoring thresholds
- Alternative valid solutions

## Evaluation Principles

Levels should evaluate whether the learner reaches the required destinations in the correct order.

The game should not require one exact command sequence unless the level is explicitly demonstrating a command. Alternative valid solutions should be accepted.

Scoring should recognise:

- Correct completion
- Use of the lesson's target concepts
- Efficient command selection
- Completion without invalid commands
- Completion without hints

Time should provide only a small bonus. Beginners should be encouraged to think about command selection rather than rush.

A suggested ranking model is:

```text
Bronze: Complete the navigation chain
Silver: Complete without invalid commands
Gold: Complete within the target action count
Mastery: Use the intended motion families appropriately
```

---

# Lesson 1: Character Motion

## Lesson Goal

Use individual character motions to move horizontally and vertically through text.

## Concepts

```text
h = move left
j = move down
k = move up
l = move right
```

## Level 1: First Steps

**Level ID:** `navigation_character_01`

**Stage:** Introduction

**Introduces:**

```text
h
l
```

### Objective

Visit the specified characters in order.

### Starting Text

```text
sword shield potion
^
```

The cursor starts on the first character of `sword`.

### Targets

1. The `s` in `shield`
2. The `p` in `potion`
3. The `s` in `sword`

### Learning Outcome

- Move horizontally using `h` and `l`.
- Move in both directions.
- Understand that the cursor is the player's avatar.

### Guidance

The first target may include a direct prompt explaining `l`. Before the learner returns to the left, introduce `h`.

### Completion Condition

All three targets are visited in order.

---

## Level 2: The Narrow Path

**Level ID:** `navigation_character_02`

**Stage:** Introduction and practice

**Introduces:**

```text
j
k
```

### Objective

Visit the specified items in order.

### Starting Text

```text
sword
shield
potion
map
^
```

The cursor starts on the `s` in `sword`.

### Targets

1. The `p` in `potion`
2. The `s` in `shield`
3. The `m` in `map`

### Learning Outcome

- Move vertically with `j` and `k`.
- Compare upward and downward movement.
- Correct an overshoot by reversing direction.

### Completion Condition

All three targets are visited in order.

---

## Level 3: Cursor Trial

**Level ID:** `navigation_character_03`

**Stage:** Mixed challenge

**Uses:**

```text
h
j
k
l
```

### Objective

Retrieve all artifacts in the specified order.

### Starting Text

```text
sword      gem
shield     key
potion     rune
map        scroll
^
```

The cursor starts on the `s` in `sword`.

### Targets

1. The `k` in `key`
2. The `p` in `potion`
3. The `s` in `scroll`
4. The `s` in `sword`
5. The `r` in `rune`

### Learning Outcome

- Combine horizontal and vertical movement.
- Plan movement between two-dimensional targets.
- Use all four character motions without direct prompts.

### Completion Condition

All five targets are visited in order.

### Mastery Condition

Complete the chain without invalid keypresses or overshooting a target.

---

# Lesson 2: Word Motion

## Lesson Goal

Move between word beginnings and endings by selecting the most appropriate word motion.

## Concepts

```text
w = move to the beginning of the next word
b = move to the beginning of the previous word
e = move to the end of the current or next word
```

The three motions should be introduced together so the learner can compare them during the same navigation chains.

## Level 4: Stepping Stones

**Level ID:** `navigation_word_01`

**Stage:** Guided introduction

**Introduces:**

```text
w
b
e
```

### Objective

Visit each target in order.

### Starting Text

```text
map rope lantern compass
^
```

The cursor starts on the `m` in `map`.

### Targets

1. The beginning of `rope`
2. The beginning of `lantern`
3. The end of `lantern`
4. The beginning of `rope`
5. The end of `compass`

### Learning Outcome

- Recognise words as navigation units.
- Compare movement to a word beginning with movement to a word ending.
- Reverse direction using `b`.

### Guidance

The first use of each motion may display a short explanation. Later targets should provide only the destination.

### Completion Condition

All five targets are visited in order.

---

## Level 5: Word Explorer

**Level ID:** `navigation_word_02`

**Stage:** Practice

**Uses:**

```text
w
b
e
```

### Objective

Visit each location in the specified order.

### Starting Text

```text
map rope lantern compass crystal
^
```

### Targets

1. The beginning of `compass`
2. The beginning of `rope`
3. The end of `lantern`
4. The beginning of `map`
5. The end of `crystal`

### Learning Outcome

- Select between forward and backward word motions.
- Move efficiently across several words.
- Use `e` when a target is at the end of a word.

### Completion Condition

All five targets are visited in order.

### Mastery Condition

Use each of `w`, `b`, and `e` at least once and remain within the target action count.

---

## Level 6: Edge Walker

**Level ID:** `navigation_word_03`

**Stage:** Contrast challenge

**Uses:**

```text
w
b
e
```

### Objective

Move between beginnings and endings of words.

### Starting Text

```text
ancient silver lantern hidden compass
^
```

### Targets

1. The end of `silver`
2. The beginning of `lantern`
3. The end of `compass`
4. The beginning of `hidden`
5. The beginning of `ancient`
6. The end of `lantern`

### Learning Outcome

- Distinguish word beginnings from word endings.
- Compare `w`, `b`, and `e` repeatedly in one level.
- Choose motions based on destination type rather than habit.

### Completion Condition

All six targets are visited in order.

---

## Level 7: Word Trial

**Level ID:** `navigation_word_04`

**Stage:** Independent challenge

**Uses:**

```text
w
b
e
```

### Objective

Collect the clues in order without command hints.

### Starting Text

```text
ancient map silver key dragon scroll hidden doorway
^
```

### Targets

1. The beginning of `silver`
2. The end of `key`
3. The beginning of `map`
4. The beginning of `dragon`
5. The end of `scroll`
6. The beginning of `ancient`
7. The end of `doorway`

### Learning Outcome

- Apply word motions independently.
- Plan a mixed forward and backward route.
- Use destination type to select the appropriate motion.

### Completion Condition

All seven clues are visited in order.

### Mastery Condition

Complete within the reference action count while using all three word motions appropriately.

---

# Lesson 3: Line and Document Motion

## Lesson Goal

Move directly to important positions within lines and across an entire document.

## Concepts

```text
0 = move to the absolute beginning of the line
^ = move to the first non-blank character of the line
$ = move to the end of the line
gg = move to the first line of the document
G = move to the final line of the document
```

## Level 8: The Line Gates

**Level ID:** `navigation_line_01`

**Stage:** Guided contrast

**Introduces:**

```text
0
^
$
```

### Objective

Visit important positions on indented lines.

### Starting Text

```text
        open_gate()
                ^
```

The cursor begins within `open_gate()`.

### Targets

1. The first non-blank character
2. The end of the line
3. The absolute beginning of the line
4. The end of the line
5. The first non-blank character

### Learning Outcome

- Understand the difference between `0` and `^`.
- Move directly to the end of a line with `$`.
- Compare all three line motions within the same challenge.

### Completion Condition

All five positions are visited in order.

---

## Level 9: The Ancient Scroll

**Level ID:** `navigation_document_01`

**Stage:** Guided introduction and repetition

**Introduces:**

```text
gg
G
```

### Starting Document

```text
LEVEL HEADER

The expedition entered the northern hall.
A damaged map rested beside the doorway.
The first inscription mentioned a sleeping dragon.

MAGIC NOTES

The blue rune opens the lower chamber.
The silver rune reveals a hidden passage.
The gold rune returns the traveller to the entrance.

DRAGON INDEX

Fire dragon: eastern cavern
Frost dragon: lower vault
Storm dragon: ruined tower

EXIT RUNE
```

The cursor starts on `MAGIC NOTES`.

### Targets

1. `EXIT RUNE`
2. `LEVEL HEADER`
3. `DRAGON INDEX`
4. `LEVEL HEADER`
5. `EXIT RUNE`

### Learning Outcome

- Move directly to the top and bottom of a document.
- Compare document jumps with slower line-by-line navigation.
- Repeat `gg` and `G` enough to establish recall.

### Implementation Note

For targets that are not exactly at the top or bottom, the learner may need to combine document and line movement. This prepares them for the next level.

### Completion Condition

All five targets are visited in order.

---

## Level 10: Archive Expedition

**Level ID:** `navigation_document_02`

**Stage:** Combined challenge

**Uses:**

```text
0
^
$
gg
G
h
j
k
l
```

### Environment

A longer document containing:

- Indented code
- Section headings
- Short narrative paragraphs
- A header at the top
- A footer at the bottom

### Targets

1. The first non-blank character on a specified indented line
2. The end of a specified line
3. The top of the document
4. The bottom of the document
5. The absolute beginning of an indented line
6. The first non-blank character of that same line

### Learning Outcome

- Combine line-scale and document-scale movement.
- Select direct motions rather than repeated character movement.
- Reinforce the distinction between `0` and `^` in realistic text.

### Completion Condition

All six targets are visited in order.

### Mastery Condition

Use `0`, `^`, `$`, `gg`, and `G` at least once during the successful attempt.

---

# Lesson 4: Character Finding

## Lesson Goal

Move efficiently to, or immediately before, a character on the current line.

## Concepts

```text
f<char> = move onto the next occurrence of the character
t<char> = move to the position immediately before the next occurrence
```

The motions should be introduced together because their contrast is the central learning outcome.

## Level 11: Hidden Rune

**Level ID:** `navigation_find_01`

**Stage:** Guided contrast

**Introduces:**

```text
f<char>
t<char>
```

### Starting Text

```text
iron, silver, amber, crystal
^
```

### Targets

1. The first comma
2. The character immediately before the second comma
3. The second comma
4. The character immediately before the third comma
5. The third comma

### Learning Outcome

- Observe that `f,` lands on a comma.
- Observe that `t,` stops immediately before a comma.
- Alternate between the two motions in one navigation chain.

### Guidance

When each command is first used, visually show the resulting cursor position:

```text
f,
    ^
```

```text
t,
   ^
```

### Completion Condition

All five targets are visited in order.

---

## Level 12: Rune Hunter

**Level ID:** `navigation_find_02`

**Stage:** Applied challenge

**Uses:**

```text
f<char>
t<char>
w
b
e
```

### Starting Text

```text
cast_spell(fire, frost, storm, arcane)
^
```

### Targets

1. The opening parenthesis
2. The first comma
3. The beginning of `frost`
4. The character immediately before the comma after `frost`
5. The beginning of `arcane`
6. The closing parenthesis
7. The end of `cast_spell`

### Learning Outcome

- Combine character finding with word motions.
- Choose `f` when the target is the character itself.
- Choose `t` when the target is immediately before a character.
- Navigate realistic code-like text.

### Completion Condition

All seven targets are visited in order.

### Mastery Condition

Use both `f` and `t`, as well as at least one word motion, within the target action count.

---

# Lesson 5: Search

## Lesson Goal

Search through a document and move forwards and backwards between repeated matches.

## Concepts

```text
/search-term = search forwards for text
n = move to the next match
N = move to the previous match
```

The three commands should be introduced together so the learner understands search as a continuing navigation session rather than a one-off command.

## Level 13: Echoes in the Archive

**Level ID:** `navigation_search_01`

**Stage:** Guided introduction and applied practice

**Introduces:**

```text
/
n
N
```

### Starting Document

```text
dragon sword
magic ring
dragon shield
ancient scroll
dragon crown
crystal doorway
dragon key
```

The cursor begins at the top of the document.

### Targets

1. The first occurrence of `dragon`
2. The third occurrence of `dragon`
3. The second occurrence of `dragon`
4. The fourth occurrence of `dragon`
5. The first occurrence of `dragon`

### Learning Outcome

- Start a search with `/`.
- Move forward through matches with `n`.
- Move backward through matches with `N`.
- Maintain and reuse the active search term.

### Guidance

The first target should prompt the learner to search for `dragon`. Later targets should identify only which occurrence is required.

### Completion Condition

All five occurrences are visited in order.

### Mastery Condition

Perform one search and use `n` and `N` to complete the remaining navigation chain without starting another search.

---

# Final Navigation Challenge

## Level 14: Trial of the Navigator

**Level ID:** `navigation_final_01`

**Stage:** Region mastery challenge

### Objective

Recover a sequence of relics and clues distributed throughout a realistic document.

### Available Skills

```text
h j k l
w b e
0 ^ $
gg G
f<char> t<char>
/ n N
```

### Environment Requirements

The document should contain:

- Inventory lists
- Narrative notes
- Code snippets
- Indented lines
- Repeated keywords
- Section headings
- Important content near the top and bottom
- Several lines containing useful punctuation targets

The environment should be large enough that inefficient movement is noticeably slower, but not so large that a beginner becomes disoriented.

### Example Quest Objectives

Visit the following locations in order:

1. The beginning of `Silver Key`
2. The end of `Dragon Scroll`
3. The `:` following `Lost Compass`
4. The first non-blank character of the `exit_rune` code line
5. The final occurrence of `dragon`
6. The document footer
7. The document header

### Rules

- No command hints are displayed initially.
- The learner sees only the current destination and remaining destinations.
- Alternative valid solutions are accepted.
- Hints may be requested, but reduce the final score.

### Learning Outcome

- Select navigation methods based on scale and destination type.
- Combine character, word, line, document, find, and search motions.
- Solve navigation problems without being told which command to use.

### Completion Condition

All required destinations are visited in the correct order.

### Mastery Conditions

A mastery result should require the learner to:

- Complete the entire navigation chain
- Avoid invalid commands
- Remain within the target action count
- Use at least four different motion families
- Complete the level without hints

### Motion Families

```text
Character: h j k l
Word: w b e
Line: 0 ^ $
Document: gg G
Find: f<char> t<char>
Search: / n N
```

---

# Region Completion Criteria

The Navigation region is complete when the learner has:

- Completed all 14 levels
- Demonstrated each navigation command at least once
- Completed the Trial of the Navigator
- Achieved at least Bronze rank on every level

A stronger readiness requirement for unlocking the Editing region may be:

- Bronze or higher on every level
- Silver or higher on each lesson's final challenge
- Bronze or higher on the Trial of the Navigator

# Navigation Region Summary

```text
Lesson 1: Character Motion       3 levels
Lesson 2: Word Motion            4 levels
Efficient Motion (counts)        1 level
Lesson 3: Line and Document      5 levels
Lesson 4: Character Finding      2 levels
Lesson 5: Search                 3 levels
Final Navigation Challenges      2 levels
                                 ─────────
Total                           20 levels
```

# Expansion Addendum (post-MVP-spec)

Six levels were added beyond the original 14 to strengthen Search,
Document navigation, and efficiency with counts. Levels are ordered
pedagogically via the `order` field in each level file (menu follows
loader order, not filename order).

- `navigation_counts_01` (order 8, Long Strides): introduces `N<motion>`
  counts; Gold (3 actions) requires counts.
- `navigation_document_03` (order 12, The Deep Archive): 22-line document,
  `gg`/`G` anchors plus counted `j`/`k`, `^`/`$` edges.
- `navigation_document_04` (order 13, Middle Ground): mid-document targets
  only, no top/bottom anchors.
- `navigation_search_02` (order 17, Shifting Echoes): alternating search
  terms requiring re-search, forward and backward (`n`/`N`).
- `navigation_search_03` (order 18, Pinpoint): search for coarse positioning
  plus word motions for precision.
- `navigation_final_02` (order 20, The Grand Archive): 45-line capstone
  requiring all six motion families for Mastery.

# Future Specification Work

Before implementation, each level should receive:

- Final narrative text
- Exact cursor coordinates
- Machine-readable target definitions
- Reference action count
- Hint wording
- Accepted alternative solutions
- Scoring thresholds
- Test cases for each completion condition

The same multi-target and contrast-based structure should be applied to later regions, particularly:

- Delete versus change operations
- Inner versus around text objects
- Named, unnamed, zero, and black-hole registers
- Sequential versus direct buffer navigation
- Telescope file, buffer, and content search
