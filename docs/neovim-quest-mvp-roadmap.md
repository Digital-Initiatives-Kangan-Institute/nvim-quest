# NeoVim Quest MVP Scope and Lesson Roadmap

**MVP Scope**

Included:

- Cursor motions
- Word motions
- Operators
- Text objects
- Registers
- Buffers
- Telescope
- Progress tracking
- Scoring

Excluded:

- Story mode
- Visual effects
- Multiplayer
- Online leaderboard
- LSP lessons
- Macro lessons
- Plugin manager integrations
- Cloud saves

---

# MVP Lessons Discussion

A key design principle for NeoVim Quest is that the game should teach practical productivity rather than individual commands in isolation.

Many Vim tutorials begin with h, j, k and l because they are easy to explain. However, many users become significantly more productive because of:

- w
- b
- e
- f
- t
- /
- ciw
- Buffers
- Telescope

The lesson structure should focus on practical milestones rather than command categories.

---

# Region 1: Navigation

**Goal:** Stop using arrow keys.

## Lessons

### Character Motion

- h
- j
- k
- l

### Word Motion

- w
- b
- e

### Line Motion

- 0
- ^
- $

### Document Motion

- gg
- G

### Find Characters

- f
- t

### Search

- /
- n
- N

---

# Region 2: Editing

**Goal:** Modify text efficiently.

## Lessons

### Delete

- x
- dw
- dd

### Change

- cw
- ciw

### Copy and Paste

- yy
- p

### Repeating

- .
- Counts

---

# Region 3: Text Objects

**Goal:** Think in structures rather than characters.

## Lessons

### Words

- iw
- aw

### Quotes

- i"
- a"

### Parentheses

- i(
- a(

### Brackets

- i[
- a[

This is typically where users begin feeling truly powerful with modal editing.

---

# Region 4: Registers

**Goal:** Store and reuse information.

## Lessons

### Named Registers

```text
"a
"b
```

### Register Pasting

```text
"ap
```

### Multiple Registers

Store and retrieve information from multiple locations.

### Black Hole Register

```text
"_d
```

### Register 0

Recover previously yanked content.

This region offers some of the most unique educational value compared to existing Vim trainers.

---

# Region 5: Buffers

**Goal:** Work across multiple files.

## Lessons

### What Is a Buffer?

Understanding the difference between files and buffers.

### Next Buffer

Navigate to the next active buffer.

### Previous Buffer

Navigate back through open buffers.

### Direct Buffer Selection

Jump directly to a specific buffer.

### Multi-Buffer Tasks

Example:

```text
Find the API key in config.lua
Insert it into main.lua
```

---

# Region 6: Telescope

**Goal:** Navigate projects efficiently.

## Lessons

### Find Files

Locate files quickly within a project.

### Buffer Search

Switch between active buffers.

### Live Grep

Search across the project.

### Project Navigation

Combine multiple searches to complete objectives.

### Large Project Challenge

Example:

```text
Locate the file containing:
calculate_tax()
```

This region differentiates NeoVim Quest from traditional Vim training applications.

---

# Recommended MVP Size

A practical first release would contain approximately 30 to 40 levels.

## Suggested Breakdown

- Navigation: 8 levels
- Editing: 8 levels
- Text Objects: 6 levels
- Registers: 6 levels
- Buffers: 6 levels
- Telescope: 6 levels

Total: approximately 40 levels.

This provides enough depth to be genuinely useful without creating an overwhelming development burden.

## Learning Progression

```text
Navigation
    ↓
Editing
    ↓
Text Objects
    ↓
Registers
    ↓
Buffers
    ↓
Telescope
```

This progression mirrors the journey many users take from experimenting with Vim motions to becoming productive NeoVim users in day-to-day development.
