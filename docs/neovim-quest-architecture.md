# NeoVim Quest Architecture

**Vision**

NeoVim Quest is a console-based learning game that teaches real-world NeoVim workflows through interactive challenges.

Instead of memorising commands, players learn how to think like a NeoVim user by solving practical editing, navigation, search, and refactoring scenarios.

The game focuses on:

- Navigation
- Editing
- Text objects
- Registers
- Buffers
- Telescope
- Macros
- Real-world coding workflows

The player progresses through a series of themed regions, unlocking increasingly advanced editor skills.

**High-Level Architecture**

```text
┌───────────────────────┐
│      Game Loop        │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│     Quest Engine      │
└──────────┬────────────┘
           │
 ┌─────────┼─────────┐
 ▼         ▼         ▼

Level   Evaluation   Progress

System    System      System
```

**Core Components**

**Quest Engine**

Responsible for:

- Loading quests
- Initialising levels
- Tracking objectives
- Determining completion conditions

A quest defines:

- Title
- Description
- Starting text
- Cursor position
- Expected outcome
- Allowed concepts
- Difficulty

Example:

```yaml
id: registers_01
title: The Amber Vault

objective:
  Store "amber key" in register a

start_text:
  - healing potion
  - amber key
  - broken compass

success:
  register_a: amber key
```

**Level System**

Levels are grouped into regions.

```text
Region
 ├─ Lesson
 │   ├─ Level
 │   ├─ Level
 │   └─ Level
```

Example:

```text
Navigation Plains
 ├─ Word Motions
 ├─ Line Motions
 └─ Search Motions

Register Ruins
 ├─ Named Registers
 ├─ Register Reuse
 └─ Black Hole Register
```

**Simulation Engine**

Responsible for:

- Cursor movement
- Text manipulation
- Virtual buffers
- Registers
- Marks
- Searches

The player interacts with this environment using real NeoVim-style commands.

Example:

```text
dw
ciw
yi"
"ap
```

The simulation updates the virtual editor state.

**Evaluation Engine**

Determines whether objectives are completed.

Checks:

- Text state
- Cursor location
- Register contents
- Buffer contents
- Buffer order
- Quest-specific conditions

Example:

```text
Objective:
Store "amber key" in register a

Success:
register[a] == "amber key"
```

**Scoring Engine**

Tracks:

- Time
- Commands entered
- Mistakes
- Efficiency

Produces:

```text
Quest Complete

Time: 00:19
Actions: 8

Efficiency: 92%

Rank: Gold
```

**Progress System**

Tracks:

- Completed levels
- Best scores
- Regions unlocked
- Skill mastery

Example:

```text
Navigation .......... 100%
Operators ........... 80%
Registers ........... 45%
Buffers ............. 20%
Telescope ........... 0%
```

Progress is stored locally.

**User Interface**

**Main Menu**

```text
NeoVim Quest

1. Continue Adventure
2. Lessons
3. Practice Arena
4. Progress
5. Settings
6. Exit
```

**Quest Screen**

```text
Quest: The Amber Vault

Objective:
Store "amber key" in register a

────────────────────────

healing potion
amber key
broken compass

────────────────────────

Cursor: Line 2

>
```

**Results Screen**

```text
Quest Complete

Gold Rank

Time: 00:21
Commands: 7
Mistakes: 0

You used:
"ayy

Master Solution:
"ayy
```

**Content Structure**

```text
World
 ├─ Region
 │   ├─ Lesson
 │   ├─ Lesson
 │   └─ Lesson
 │
 └─ Region
```

Example:

```text
Cursor Plains
Operator Forest
Register Ruins
Buffer Archipelago
Telescope Observatory
Macro Mountains
```

**Save Data**

Stores:

- Completed quests
- Best ranks
- Mastery percentages
- Unlocked regions

Example:

```json
{
  "player_level": 8,
  "completed": [
    "motions_01",
    "motions_02",
    "registers_01"
  ]
}
```
