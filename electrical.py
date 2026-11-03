import math


def analyze_dc(voltage_v, resistance_ohm):
    if not math.isfinite(voltage_v):
        raise ValueError("Voltage must be a finite number.")
    if not math.isfinite(resistance_ohm) or resistance_ohm <= 0:
        raise ValueError("Resistance must be greater than zero.")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


def analyze_network(voltage_v, branches):
    if not math.isfinite(voltage_v):
        raise ValueError("Voltage must be a finite number.")
    if not branches or any(not branch for branch in branches):
        raise ValueError("Enter at least one resistor in every branch.")
    if any(
        not math.isfinite(resistance) or resistance <= 0
        for branch in branches
        for resistance in branch
    ):
        raise ValueError("Every resistance must be greater than zero.")

    branch_resistances = [sum(branch) for branch in branches]
    if any(not math.isfinite(resistance) for resistance in branch_resistances):
        raise ValueError("The total resistance in each branch must be finite.")
    equivalent_resistance = 1 / sum(1 / resistance for resistance in branch_resistances)
    total_current = voltage_v / equivalent_resistance
    resistor_results = []

    for branch_index, (branch, branch_resistance) in enumerate(
        zip(branches, branch_resistances), start=1
    ):
        branch_current = voltage_v / branch_resistance
        resistors = []
        for resistance in branch:
            resistor_voltage = branch_current * resistance
            resistors.append(
                {
                    "resistance_ohm": resistance,
                    "voltage_v": resistor_voltage,
                    "current_a": branch_current,
                    "power_w": resistor_voltage * branch_current,
                }
            )
        resistor_results.append(
            {"branch": branch_index, "current_a": branch_current, "resistors": resistors}
        )

    return {
        "equivalent_resistance_ohm": equivalent_resistance,
        "total_current_a": total_current,
        "total_power_w": voltage_v * total_current,
        "branches": resistor_results,
    }


def parse_branches(value):
    try:
        return [
            [float(item.strip()) for item in branch.split(",")]
            for branch in value.split(";")
        ]
    except ValueError as error:
        raise ValueError("Use numbers separated by commas and branches by semicolons.") from error


def main():
    print("DC Circuit Calculator")
    print("Enter series resistors with commas and parallel branches with semicolons.")
    print("Example: 10,20;30")

    try:
        voltage_v = float(input("Supply voltage (V): "))
        branches = parse_branches(input("Resistors (ohm): "))
        result = analyze_network(voltage_v, branches)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    print(f"\nEquivalent resistance: {result['equivalent_resistance_ohm']:.4g} ohm")
    print(f"Total current: {result['total_current_a']:.4g} A")
    print(f"Total power: {result['total_power_w']:.4g} W")
    for branch in result["branches"]:
        print(f"\nBranch {branch['branch']} current: {branch['current_a']:.4g} A")
        for index, resistor in enumerate(branch["resistors"], start=1):
            print(
                f"  R{index}: {resistor['resistance_ohm']:.4g} ohm, "
                f"{resistor['voltage_v']:.4g} V, "
                f"{resistor['current_a']:.4g} A, "
                f"{resistor['power_w']:.4g} W"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())