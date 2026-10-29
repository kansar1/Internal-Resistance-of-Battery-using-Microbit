### MAKE SURE YOU ADD THE DATALOGGER EXTENSION TO YOUR PROJECT BEFORE RUNNING THIS CODE, ELSE YOU WILL GET ERRORS.
# ============================================================
# MICRO:BIT V2 BATTERY INTERNAL RESISTANCE LOGGER
# MAKECODE PYTHON
#
# BUTTON A: START / RESUME
# BUTTON B: PAUSE
#
# LOCAL DATALOGGER ONLY
# EACH SETTING IS RECORDED ON ITS OWN ROW
# NO VOLTAGE CUTOFF
# ============================================================

# -------------------- CONFIGURATION --------------------

LOG_NAME = "LADDA_AAA_Trial_05_Battery_03" ### Change trial name here
BATTERY_TYPE = "AAA_NiMH" ### Change the battery type here
STARTING_VOLTAGE_MV = 1364  ### Change starting voltage here, use a multimeter to test
SESSION_DATE_TIME = "2026-10-23_14-15" ### Trial start date and time

TEST_DURATION_MINUTES = 60 ### Trial duration. Set to 0.2 for testing if the circuit works, else set to 60 for a full test.
LOAD_RESISTANCE_OHM = 2.5 ### Change to the load resistor value you are using

SAMPLE_INTERVAL_MS = 1000 ### Change to the sample interval (Time between samples) you want. 1000 = 1 second, 5000 = 5 seconds, etc.
ADC_REFERENCE_MV = 3300 ### Change to the ADC reference voltage of your micro:bit. 3300 = 3.3V, 3000 = 3.0V, etc.
MEASUREMENT_SETTLE_MS = 1000 ### Change to the time you want to wait for the voltage to settle after switching the load on or off. A greater settle time will give more accurate readings, but will also increase the time between samples.
AVERAGE_READINGS = 3 ### Averages the number of readings to take for each voltage measurement. A greater number of readings will give more accurate readings, but will also increase the time between samples.

# -------------------- STATE --------------------

running = False
started = False
finished = False

start_time = 0
paused_time = 0
pause_started = 0
reading_count = 0

# -------------------- HARDWARE --------------------

pins.digital_write_pin(DigitalPin.P1, 0)

# -------------------- ROUNDING --------------------

def round_to_integer(value):
    adjusted = value + 0.5
    return adjusted - (adjusted % 1)

def round_resistance(value):
    scaled = value * 100
    if scaled >= 0:
        adjusted = scaled + 0.5
    else:
        adjusted = scaled - 0.5
    rounded = adjusted - (adjusted % 1)
    return rounded / 100

# -------------------- LED INDICATORS --------------------

def show_ready():
    basic.show_icon(IconNames.DIAMOND)

def show_running():
    basic.show_icon(IconNames.HEART)

def show_paused():
    basic.show_icon(IconNames.NO)

def show_finished():
    pins.digital_write_pin(DigitalPin.P1, 0)
    basic.show_icon(IconNames.YES)
    basic.pause(500)
    basic.show_string("DONE")

# -------------------- COMMON LOG ROW --------------------
# Keep the same column names and types in every call.
#
# Text columns:
# record_type, setting_name, setting_value
#
# Numeric columns:
# elapsed_s, unloaded_mV, loaded_mV, collector_mV,
# load_voltage_mV, load_current_mA, internal_resistance_ohm

def log_row(record_type, setting_name, setting_value,
            elapsed_s, unloaded_mv, loaded_mv, collector_mv,
            load_voltage_mv, load_current_ma, resistance_ohm):

    datalogger.log(
        datalogger.create_cv("record_type", record_type),
        datalogger.create_cv("setting_name", setting_name),
        datalogger.create_cv("setting_value", setting_value),
        datalogger.create_cv("elapsed_s", elapsed_s),
        datalogger.create_cv("unloaded_mV", unloaded_mv),
        datalogger.create_cv("loaded_mV", loaded_mv),
        datalogger.create_cv("collector_mV", collector_mv),
        datalogger.create_cv("load_voltage_mV", load_voltage_mv),
        datalogger.create_cv("load_current_mA", load_current_ma),
        datalogger.create_cv("internal_resistance_ohm", resistance_ohm)
    )

# -------------------- SAVE SETTINGS --------------------

def record_settings():
    log_row("SETUP", "log_name", LOG_NAME, 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "battery_type", BATTERY_TYPE, 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "starting_voltage_mV", str(STARTING_VOLTAGE_MV), 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "session_datetime", SESSION_DATE_TIME, 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "duration_minutes", str(TEST_DURATION_MINUTES), 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "load_resistance_ohm", str(LOAD_RESISTANCE_OHM), 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "sample_interval_ms", str(SAMPLE_INTERVAL_MS), 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "ADC_reference_mV", str(ADC_REFERENCE_MV), 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "settle_time_ms", str(MEASUREMENT_SETTLE_MS), 0, 0, 0, 0, 0, 0, 0)
    log_row("SETUP", "average_readings", str(AVERAGE_READINGS), 0, 0, 0, 0, 0, 0, 0)

# -------------------- ELAPSED TIME --------------------

def get_elapsed_ms():
    if running:
        return input.running_time() - start_time - paused_time

    if started and pause_started > 0:
        return pause_started - start_time - paused_time

    return 0

# -------------------- VOLTAGE MEASUREMENT --------------------

def read_voltage_mv(pin):
    total = 0

    for i in range(AVERAGE_READINGS):
        total = total + pins.analog_read_pin(pin)
        basic.pause(2)

    average = total / AVERAGE_READINGS
    voltage = average * ADC_REFERENCE_MV / 1023

    return round_to_integer(voltage)

# -------------------- FINISH TEST --------------------

def finish_test():
    global running
    global finished

    if finished:
        return

    elapsed_s = round_to_integer(get_elapsed_ms() / 1000)

    running = False
    finished = True

    pins.digital_write_pin(DigitalPin.P1, 0)

    log_row("TEST_FINISHED", "", "", elapsed_s, 0, 0, 0, 0, 0, 0)

    show_finished()

# -------------------- START / RESUME --------------------

def start_or_resume():
    global running
    global started
    global start_time
    global paused_time
    global pause_started

    if finished:
        return

    if not started:
        started = True
        running = True

        start_time = input.running_time()
        paused_time = 0
        pause_started = 0

        log_row("SECTION_START", "", "", 0, 0, 0, 0, 0, 0, 0)

        show_running()

    elif not running:
        if pause_started > 0:
            paused_time = (
                paused_time
                + input.running_time()
                - pause_started
            )

        pause_started = 0
        running = True

        log_row(
            "RESUMED", "", "",
            round_to_integer(get_elapsed_ms() / 1000),
            0, 0, 0, 0, 0, 0
        )

        show_running()

# -------------------- PAUSE --------------------

def pause_test():
    global running
    global pause_started

    if running and not finished:
        elapsed_s = round_to_integer(get_elapsed_ms() / 1000)

        running = False
        pause_started = input.running_time()

        pins.digital_write_pin(DigitalPin.P1, 0)

        log_row("PAUSED", "", "", elapsed_s, 0, 0, 0, 0, 0, 0)

        show_paused()

# -------------------- BUTTONS --------------------

input.on_button_pressed(Button.A, start_or_resume)
input.on_button_pressed(Button.B, pause_test)

# -------------------- STARTUP --------------------

show_ready()
record_settings()
show_ready()

# -------------------- MAIN LOOP --------------------

while not finished:

    if running:

        elapsed_ms = get_elapsed_ms()

        if elapsed_ms >= TEST_DURATION_MINUTES * 60000:
            finish_test()

        if running and not finished:

            # Load OFF: measure unloaded voltage.
            pins.digital_write_pin(DigitalPin.P1, 0)
            basic.pause(MEASUREMENT_SETTLE_MS)

            unloaded_mv = read_voltage_mv(AnalogPin.P0)

            # Load ON: measure loaded voltage.
            pins.digital_write_pin(DigitalPin.P1, 1)
            basic.pause(MEASUREMENT_SETTLE_MS)

            loaded_mv = read_voltage_mv(AnalogPin.P0)
            collector_mv = read_voltage_mv(AnalogPin.P2)

            # Estimate current through the load.
            load_voltage_mv = loaded_mv - collector_mv

            if load_voltage_mv > 0:
                load_current_ma = load_voltage_mv / LOAD_RESISTANCE_OHM
            else:
                load_current_ma = 0

            # Estimate internal resistance.
            if load_current_ma > 1:
                resistance_ohm = round_resistance(
                    (unloaded_mv - loaded_mv) / load_current_ma
                )
            else:
                resistance_ohm = -1

            elapsed_s = round_to_integer(get_elapsed_ms() / 1000)

            log_row(
                "DATA", "", "",
                elapsed_s,
                unloaded_mv,
                loaded_mv,
                collector_mv,
                load_voltage_mv,
                load_current_ma,
                resistance_ohm
            )

            reading_count = reading_count + 1
            basic.show_number(reading_count)

            pins.digital_write_pin(DigitalPin.P1, 1)
            basic.pause(SAMPLE_INTERVAL_MS)

    else:
        basic.pause(100)

# -------------------- END --------------------

pins.digital_write_pin(DigitalPin.P1, 0)
