#My dad specializes in python so he helped me so it might not be what we learned in class

import csv
import os
import sys

import matplotlib.pyplot as plt


START_X = 0
START_Y = 0
START_DEPTH_M = 2.0
START_ENERGY = 100.0
START_HULL = 100.0
START_CLUES = 0
CLUE_TARGET = 6
FAILURE_THRESHOLD = 10.0

# Paths are built from the folder that holds hunt.py, so the program works
# no matter which folder it is launched from (terminal, IDE, double-click).
PROGRAM_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MISSION_NAME = "mission_recovery.csv"
PLOT_FILE = os.path.join(PROGRAM_DIR, "plots", "mission_plot.png")

# SRCH-07: search effects as (hull change, energy change, clue change).
# Treasure is handled separately because it ends the mission with no penalty.
SEARCH_EFFECTS = {
    "Low Hazard":       (-5, -5, 0),
    "Medium Hazard":    (-10, -5, 0),
    "High Hazard":      (-15, -10, 0),
    "Low Value Clue":   (-5, -5, 1),
    "Strong Clue":      (-2, -5, 2),
    "High Value Clue":  (-2, -2, 3),
    "None":             (-2, -5, 0),
}
TREASURE = "Treasure"
VALID_CATEGORIES = list(SEARCH_EFFECTS.keys()) + [TREASURE]


def find_mission_file(name=DEFAULT_MISSION_NAME):
    """Return the first existing path for the mission file.

    Looks (1) at the name exactly as given, (2) beside hunt.py, (3) in
    hunt.py's data/ folder, (4) in the current folder's data/ folder.
    If nothing exists, the name is returned so the loader reports it.
    """
    candidates = [name,
                  os.path.join(PROGRAM_DIR, name),
                  os.path.join(PROGRAM_DIR, "data", name),
                  os.path.join("data", name)]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return name


def load_mission_file(filename):
    """SYS-12: load the mission CSV into a 2D list mission[y][x].

    Columns (no header row): x, y, at_location, description, depth_m,
    distance_m, time_min. Grid size is taken from the largest x and y found
    (SYS-03). Raises ValueError with a clear message if the file is unusable.
    """
    records = {}
    with open(filename, newline="") as csv_file:
        for line_number, row in enumerate(csv.reader(csv_file), start=1):
            if not row or all(cell.strip() == "" for cell in row):
                continue
            # Tolerate a header row even though the official files have none.
            if line_number == 1 and not row[0].strip().lstrip("-").isdigit():
                continue
            if len(row) < 7:
                raise ValueError(f"Line {line_number}: expected 7 columns, "
                                 f"found {len(row)}.")
            try:
                x, y = int(row[0]), int(row[1])
                depth, distance, time = (float(row[4]), float(row[5]),
                                         float(row[6]))
            except ValueError:
                raise ValueError(f"Line {line_number}: a number could not "
                                 f"be read.")
            category = row[2].strip()          # DATA-12: case-sensitive token
            if category not in VALID_CATEGORIES:
                raise ValueError(f"Line {line_number}: unknown category "
                                 f"'{category}'.")
            # Data rules from the CSV schema table and DATA-08.
            if depth < 0 or distance < 0:
                raise ValueError(f"Line {line_number}: depth_m and "
                                 f"distance_m must be nonnegative.")
            if (x, y) != (START_X, START_Y) and time <= 0:
                raise ValueError(f"Line {line_number}: time_min must be "
                                 f"greater than 0 (DATA-08).")
            if time < 0:
                raise ValueError(f"Line {line_number}: time_min must not "
                                 f"be negative.")
            if (x, y) in records:
                raise ValueError(f"Line {line_number}: coordinate ({x}, {y}) "
                                 f"appears more than once (DATA-06).")
            records[(x, y)] = {"at_location": category,
                               "description": row[3].strip(),
                               "depth_m": depth, "distance_m": distance,
                               "time_min": time}

    if not records:
        raise ValueError("The mission file contains no records.")

    num_columns = max(x for x, y in records) + 1
    num_rows = max(y for x, y in records) + 1
    check_start_and_treasure(records)
    mission = []
    for y in range(num_rows):
        row_of_records = []
        for x in range(num_columns):
            if (x, y) not in records:
                raise ValueError(f"Missing record for coordinate ({x}, {y}).")
            row_of_records.append(records[(x, y)])
        mission.append(row_of_records)
    return mission, num_rows, num_columns


def check_start_and_treasure(records):
    """Validate the start record and treasure count (DATA-07, DATA-10).

    A bad start record stops the mission. Deviations that do not break the
    program (a different start distance/time, treasure count) only warn, so
    the pilot sees the issue but a usable file is not rejected.
    """
    start = records.get((START_X, START_Y))
    if start is None:
        raise ValueError("The start record (0, 0) is missing.")
    if start["at_location"] != "None":
        raise ValueError("The start record (0, 0) must have category None.")
    if start["depth_m"] != START_DEPTH_M:
        print(f"Warning: start depth in file is {start['depth_m']} m, "
              f"expected {START_DEPTH_M} m (DATA-07).")
    if start["distance_m"] != 0.0 or start["time_min"] != 0.0:
        print("Warning: start record distance/time are not 0.0 (DATA-07); "
              "using the file values for any revisit of (0, 0).")
    treasure_count = sum(1 for rec in records.values()
                         if rec["at_location"] == TREASURE)
    if treasure_count != 1:
        print(f"Warning: file has {treasure_count} Treasure records, "
              f"expected exactly 1 (DATA-10).")


def get_direction():
    """NAV-01 / NAV-02: prompt until one of the four full words is entered."""
    while True:
        choice = input("\nEnter direction (Forward, Backward, Left, Right): ")
        choice = choice.strip().lower()
        if choice in ("forward", "backward", "left", "right"):
            return choice
        print("Invalid input. Please type Forward, Backward, Left, or Right.")


def propose_move(current_x, current_y, direction):
    """NAV-03: compute the proposed coordinate WITHOUT changing the rover."""
    if direction == "forward":
        return current_x, current_y + 1
    elif direction == "backward":
        return current_x, current_y - 1
    elif direction == "right":
        return current_x + 1, current_y
    else:                                   # "left"
        return current_x - 1, current_y


def in_bounds(new_x, new_y, num_rows, num_columns):
    """NAV-04: valid only if 0 <= x < columns and 0 <= y < rows."""
    return 0 <= new_x < num_columns and 0 <= new_y < num_rows


def ask_yes_no(question):
    """SRCH-02: return True/False; re-prompt on unsupported input."""
    while True:
        answer = input(question).strip().lower()
        if answer == "yes":
            return True
        if answer == "no":
            return False
        print("Invalid input. Please type yes or no.")


def calculate_movement(destination, previous_depth):
    """STAT-01: movement losses for entering the destination record.

    hull loss   = |Dnew - Dprev| * 0.8 * t
    energy loss = |Dnew - Dprev| * 0.5 + (d / t) * 1.2
    """
    depth_change = abs(destination["depth_m"] - previous_depth)
    time = destination["time_min"]
    hull_loss = depth_change * 0.8 * time
    # DESIGN DECISION: the start record (0, 0) has time_min = 0 (DATA-07), so
    # d / t would divide by zero when the rover revisits it (SRCH-11). Every
    # other record has t > 0 (DATA-08). The start record also has d = 0, so
    # the speed term is treated as 0 there instead of crashing.
    speed_term = (destination["distance_m"] / time) * 1.2 if time > 0 else 0.0
    energy_loss = depth_change * 0.5 + speed_term
    return hull_loss, energy_loss


def apply_move(rover, destination, new_x, new_y):
    """STAT-02 to STAT-04: apply a VALID move and record the history."""
    hull_loss, energy_loss = calculate_movement(destination, rover["depth"])
    rover["energy"] -= energy_loss
    rover["hull"] -= hull_loss
    rover["time"] += destination["time_min"]
    rover["x"], rover["y"] = new_x, new_y
    rover["depth"] = destination["depth_m"]
    rover["time_history"].append(rover["time"])
    rover["energy_history"].append(rover["energy"])
    rover["hull_history"].append(rover["hull"])
    return hull_loss, energy_loss


def process_search(rover, record):
    """Handle a search at the current location (SRCH-04 to SRCH-09).

    Returns "treasure", "repeat" or "searched". Repeat searches apply
    nothing and are tracked separately from the path (STATE-04).
    """
    location = (rover["x"], rover["y"])
    if location in rover["searched"]:
        print("Location already searched. No effects applied.")
        return "repeat"

    rover["searched"].append(location)
    print(f"\nSearch result: {record['at_location']}")
    print(record["description"])

    if record["at_location"] == TREASURE:
        return "treasure"               # SRCH-08: no penalty

    hull_change, energy_change, clue_change = SEARCH_EFFECTS[record["at_location"]]
    rover["hull"] += hull_change
    rover["energy"] += energy_change
    rover["clues"] += clue_change
    # SRCH-09: overwrite the latest history values so the plot shows the
    # post-search condition at the same mission time.
    rover["energy_history"][-1] = rover["energy"]
    rover["hull_history"][-1] = rover["hull"]
    print(f"Search effects: hull {hull_change:+d}, energy {energy_change:+d}, "
          f"clues {clue_change:+d}")
    return "searched"



def check_failure(energy, hull):
    """SYS-07: failure at or below the 10.0 threshold (<=, not <)."""
    return energy <= FAILURE_THRESHOLD or hull <= FAILURE_THRESHOLD


def check_clue_success(clue_points, energy, hull):
    """SYS-05: 6+ clues AND energy and hull strictly above 10."""
    return (clue_points >= CLUE_TARGET
            and energy > FAILURE_THRESHOLD
            and hull > FAILURE_THRESHOLD)


def create_plot():
    """OUT-05/06: one figure, energy on the left axis, hull on the right.

    Interactive mode is NOT turned on, so the figure is built and redrawn
    quietly during the mission and only appears when main() calls plt.show()
    after the mission ends.
    """
    fig, energy_axis = plt.subplots(figsize=(9, 5))
    hull_axis = energy_axis.twinx()
    return fig, energy_axis, hull_axis


def update_plot(fig, energy_axis, hull_axis, rover):
    """OUT-07 / OUT-08: redraw with title, labelled axes and a legend.

    Called after every valid move and every state-changing search, so the
    figure always holds the full multi-step history as one continuous line.
    The window itself is not shown until the mission ends."""
    energy_axis.clear()
    hull_axis.clear()
    # clear() resets the twin axis to the left side, so move it back right.
    hull_axis.yaxis.tick_right()
    hull_axis.yaxis.set_label_position("right")
    energy_line, = energy_axis.plot(rover["time_history"],
                                    rover["energy_history"],
                                    color="tab:blue", marker="o",
                                    label="Energy remaining (%)")
    hull_line, = hull_axis.plot(rover["time_history"],
                                rover["hull_history"],
                                color="tab:red", marker="s",
                                label="Hull integrity (%)")
    energy_axis.set_title("Captain Flint Recovery Mission - Rover Status")
    energy_axis.set_xlabel("Total mission time (min)")
    energy_axis.set_ylabel("Energy remaining (%)", color="tab:blue")
    hull_axis.set_ylabel("Hull integrity (%)", color="tab:red")
    energy_axis.set_ylim(0, 105)
    hull_axis.set_ylim(0, 105)
    energy_axis.grid(True, alpha=0.3)
    energy_axis.legend(handles=[energy_line, hull_line], loc="lower left")
    fig.tight_layout()


def save_final_plot(fig):
    """Save the final plot into the required plots/ folder."""
    os.makedirs(os.path.dirname(PLOT_FILE), exist_ok=True)
    fig.savefig(PLOT_FILE, dpi=150)
    print(f"Final plot saved to {PLOT_FILE}")


def display_start(filename, rover, num_rows, num_columns):
    """OUT-01: mission file, start position, status and clue target."""
    print("=== Captain Flint Recovery Mission ===")
    print(f"Mission file:   {filename}")
    print(f"Grid size:      {num_columns} columns x {num_rows} rows")
    print(f"Start position: ({rover['x']}, {rover['y']})")
    print(f"Energy:         {rover['energy']:.2f}")
    print(f"Hull integrity: {rover['hull']:.2f}")
    print(f"Clue score:     {rover['clues']} (target {CLUE_TARGET})")


def display_move(rover, hull_loss, energy_loss):
    """OUT-02. Rounded for display only (STATE-03)."""
    print(f"\nMoved to ({rover['x']}, {rover['y']})")
    print(f"  Depth:          {rover['depth']:.1f} m")
    print(f"  Energy loss:    {energy_loss:.2f}")
    print(f"  Hull loss:      {hull_loss:.2f}")
    print(f"  Total time:     {rover['time']:.1f} min")
    print(f"  Energy:         {rover['energy']:.2f}")
    print(f"  Hull integrity: {rover['hull']:.2f}")
    print(f"  Clue score:     {rover['clues']}")


def display_state(rover):
    """Compact status shown after a search."""
    print(f"  Energy: {rover['energy']:.2f}   Hull: {rover['hull']:.2f}   "
          f"Clues: {rover['clues']}/{CLUE_TARGET}")


def display_final_summary(rover, outcome):
    """OUT-04: final mission summary."""
    print("\n========== MISSION SUMMARY ==========")
    print(f"Outcome:           {outcome}")
    print(f"Final coordinate:  ({rover['x']}, {rover['y']})")
    print(f"Total time:        {rover['time']:.1f} min")
    print(f"Remaining energy:  {rover['energy']:.2f}")
    print(f"Remaining hull:    {rover['hull']:.2f}")
    print(f"Clue score:        {rover['clues']}")
    print(f"Locations searched: {len(rover['searched'])}")


def new_rover():
    """Starting state and history lists (Rover State Model)."""
    return {"x": START_X, "y": START_Y, "depth": START_DEPTH_M,
            "energy": START_ENERGY, "hull": START_HULL,
            "clues": START_CLUES, "time": 0.0, "searched": [],
            "time_history": [0.0], "energy_history": [START_ENERGY],
            "hull_history": [START_HULL]}


def run_mission(mission, num_rows, num_columns, filename):
    """Run the navigation loop in the Required Execution Order.
    Returns (rover, outcome, figure, energy_axis, hull_axis)."""
    rover = new_rover()
    fig, energy_axis, hull_axis = create_plot()
    display_start(filename, rover, num_rows, num_columns)

    outcome = None
    while outcome is None:
        # Steps 2-3: direction, proposed coordinate, boundary check.
        direction = get_direction()
        new_x, new_y = propose_move(rover["x"], rover["y"], direction)
        if not in_bounds(new_x, new_y, num_rows, num_columns):
            print("Boundary error: that move leaves the search grid. "
                  "No cost applied. Choose another direction.")
            continue                                       # NAV-05

        # Steps 4-5: movement, history, plot.
        record = mission[new_y][new_x]
        hull_loss, energy_loss = apply_move(rover, record, new_x, new_y)
        display_move(rover, hull_loss, energy_loss)
        update_plot(fig, energy_axis, hull_axis, rover)

        # Step 6: failure BEFORE any search is offered (STAT-06/07).
        if check_failure(rover["energy"], rover["hull"]):
            outcome = "FAILURE - energy or hull at or below 10"
            print("\nMission failure: the rover can no longer continue.")
            continue

        # Steps 7-8: search prompt and search.
        if not ask_yes_no("Search this location? (yes/no): "):
            continue                                       # SRCH-03
        result = process_search(rover, record)
        if result == "repeat":
            continue                                       # SRCH-05

        # Step 9: refresh the plot so it shows the latest state.
        update_plot(fig, energy_axis, hull_axis, rover)

        if result == "treasure":
            outcome = "SUCCESS - treasure found"
            print("\nMission success: Captain Flint's treasure recovered!")
            continue
        display_state(rover)

        # Step 10: failure first, then clue success (SYS-08).
        if check_failure(rover["energy"], rover["hull"]):
            outcome = "FAILURE - energy or hull at or below 10"
            print("\nMission failure: the search left the rover too damaged.")
        elif check_clue_success(rover["clues"], rover["energy"],
                                rover["hull"]):
            outcome = "SUCCESS - clue target reached"
            print("\nMission success: enough clues collected to locate "
                  "the treasure!")

    return rover, outcome, fig, energy_axis, hull_axis


def main(mission_file=None):
    if mission_file is None:
        if len(sys.argv) > 1:
            requested = sys.argv[1]         # python hunt.py other_mission.csv
        else:
            requested = DEFAULT_MISSION_NAME
        mission_file = find_mission_file(requested)

    try:
        mission, num_rows, num_columns = load_mission_file(mission_file)
    except (OSError, ValueError) as error:
        print(f"Could not load mission file: {error}")
        return

    rover, outcome, fig, energy_axis, hull_axis = run_mission(
        mission, num_rows, num_columns, mission_file)
    display_final_summary(rover, outcome)
    update_plot(fig, energy_axis, hull_axis, rover)   # final state
    save_final_plot(fig)                      # SRCH-10 / SYS-09
    plt.show()                                # plot appears only now


if __name__ == "__main__":
    main()
