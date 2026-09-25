START PROGRAM

FUNCTION load_mission_file(filename)
    Open CSV file
    Read all records into data structure
    Determine grid dimensions from max x and y values
    Return mission_data, num_rows, num_columns
END FUNCTION


FUNCTION calculate_movement(destination_record, previous_depth)

    Dnew = destination_record.depth_m
    d = destination_record.distance_m
    t = destination_record.time_min

    hull_loss = ABS(Dnew - previous_depth) * 0.8 * t

    energy_loss = (ABS(Dnew - previous_depth) * 0.5)
                  + ((d / t) * 1.2)

    Return hull_loss, energy_loss

END FUNCTION


FUNCTION check_failure(energy, hull)

    IF energy <= 10 OR hull <= 10 THEN
        Return TRUE
    ELSE
        Return FALSE
    END IF

END FUNCTION


FUNCTION update_plot(time_history,
                     energy_history,
                     hull_history)

    Create matplotlib plot

    X axis = mission time

    Plot energy on first Y axis
    Plot hull integrity on second Y axis

    Add title
    Add labels
    Add legend

    Refresh display

END FUNCTION


FUNCTION process_search(current_record)

    IF current location already searched THEN
        Display "Location already searched."
        Return CONTINUE
    END IF

    Add current coordinate to searched_locations

    Display category
    Display description

    IF category == "Treasure" THEN
        Return TREASURE_FOUND
    END IF

    Apply dictionary effects:

        Low Hazard:
            hull -= 5
            energy -= 5

        Medium Hazard:
            hull -= 10
            energy -= 5

        High Hazard:
            hull -= 15
            energy -= 10

        Low Value Clue:
            hull -= 5
            energy -= 5
            clues += 1

        Strong Clue:
            hull -= 2
            energy -= 5
            clues += 2

        High Value Clue:
            hull -= 2
            energy -= 2
            clues += 3

        None:
            hull -= 2
            energy -= 5

    Update latest history values

    Return CONTINUE

END FUNCTION


----------------------------------------------------
MAIN PROGRAM
----------------------------------------------------

Load mission file

Initialize search_effect_dictionary

Initialize rover state:

    current_x = 0
    current_y = 0
    current_depth = 2.0

    energy = 100
    hull = 100

    clues = 0
    total_time = 0

    searched_locations = empty list

Initialize history lists:

    time_history = [0]
    energy_history = [100]
    hull_history = [100]

Display mission information
Display starting position
Display clue target

mission_active = TRUE

WHILE mission_active

    ------------------------------------------------
    GET MOVEMENT COMMAND
    ------------------------------------------------

    Prompt user for direction

    Validate direction input

    IF direction = Forward THEN
        new_x = current_x
        new_y = current_y + 1

    ELSE IF direction = Backward THEN
        new_x = current_x
        new_y = current_y - 1

    ELSE IF direction = Right THEN
        new_x = current_x + 1
        new_y = current_y

    ELSE IF direction = Left THEN
        new_x = current_x - 1
        new_y = current_y

    ELSE
        Display invalid input message
        Continue loop
    END IF


    ------------------------------------------------
    BOUNDARY CHECK
    ------------------------------------------------

    IF new_x < 0 OR
       new_x >= num_columns OR
       new_y < 0 OR
       new_y >= num_rows THEN

        Display boundary error
        Continue loop

    END IF


    ------------------------------------------------
    APPLY MOVEMENT
    ------------------------------------------------

    destination_record =
        record located at (new_x, new_y)

    Calculate hull_loss and energy_loss

    energy = energy - energy_loss
    hull = hull - hull_loss

    total_time =
        total_time + destination_record.time_min

    current_x = new_x
    current_y = new_y

    current_depth =
        destination_record.depth_m

    Append total_time to time_history
    Append energy to energy_history
    Append hull to hull_history

    Update plot

    Display:
        new coordinate
        depth
        energy loss
        hull loss
        total time
        energy remaining
        hull integrity
        clue score


    ------------------------------------------------
    FAILURE CHECK AFTER MOVE
    ------------------------------------------------

    IF energy <= 10 OR hull <= 10 THEN

        Display mission failure

        mission_active = FALSE

        BREAK

    END IF


    ------------------------------------------------
    SEARCH PROMPT
    ------------------------------------------------

    Ask user:
        "Search this location? (yes/no)"

    Validate yes/no input

    IF answer == "no" THEN
        Continue navigation loop
    END IF


    ------------------------------------------------
    PROCESS SEARCH
    ------------------------------------------------

    search_result =
        process_search(current_record)

    Update plot

    IF search_result == TREASURE_FOUND THEN

        Display mission success

        mission_active = FALSE

        BREAK

    END IF


    ------------------------------------------------
    FAILURE CHECK AFTER SEARCH
    ------------------------------------------------

    IF energy <= 10 OR hull <= 10 THEN

        Display mission failure

        mission_active = FALSE

        BREAK

    END IF


    ------------------------------------------------
    CLUE SUCCESS CHECK
    ------------------------------------------------

    IF clues >= 6 AND
       energy > 10 AND
       hull > 10 THEN

        Display clue-based success

        mission_active = FALSE

        BREAK

    END IF

END WHILE


----------------------------------------------------
FINAL SUMMARY
----------------------------------------------------

Display:

    Mission outcome
    Final coordinate
    Total mission time
    Remaining energy
    Remaining hull integrity
    Clue score
    Number of searched locations

Save final plot

END PROGRAM