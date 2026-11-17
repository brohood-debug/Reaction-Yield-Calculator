"""
Reaction Yield Lab

A Drafter website that helps chemistry students find the limiting reactant,
theoretical yield, percent yield, and heat released for a reaction, and saves
each experiment to a history so runs can be compared.

Advanced techniques: none beyond course material. Two small formatting tools
are worth noting: f-string format specs such as {value:.2f} (round to 2
decimals) and ", ".join(list) (glue a list of strings into one string).
"""
from dataclasses import dataclass
from bakery import assert_equal
from drafter import *

# Global CONSTANTS (allowed): molar masses in g/mol for supported compounds.
MOLAR_MASSES = {
    "H2": 2.016, "O2": 31.998, "N2": 28.014, "H2O": 18.015,
    "CO2": 44.009, "CH4": 16.043, "NH3": 17.031, "HCl": 36.458,
    "NaCl": 58.44, "NaOH": 39.997, "Na2CO3": 105.988,
    "NaHCO3": 84.006, "Mg": 24.305, "MgO": 40.304, "Fe": 55.845,
    "Fe2O3": 159.687, "Al": 26.982, "Al2O3": 101.961, "Cu": 63.546,
    "CuO": 79.545, "CaO": 56.077, "CaCO3": 100.086, "H2SO4": 98.072,
    "C6H12O6": 180.156,
}
COEFFICIENT_CHOICES = ["1", "2", "3", "4", "5", "6"]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Species:
    """One chemical in the reaction (a reactant or the product)."""
    formula: str
    molar_mass: float
    coefficient: int
    grams: float  # starting mass for a reactant, actual yield for the product


@dataclass
class Experiment:
    """A finished calculation saved to the history."""
    name: str
    limiting_formula: str
    theoretical_grams: float
    actual_grams: float
    yield_percent: float
    heat_kj: float
    heat_type: str
    notes: str


@dataclass
class State:
    """Everything the website remembers between pages."""
    experiment_name: str
    reactants: list[Species]
    product: Species
    status_message: str
    saved_experiments: list[Experiment]


def make_empty_state() -> State:
    """Create a brand new State with nothing entered yet."""
    return State("", [], Species("", 0.0, 1, 0.0), "", [])


# ---------------------------------------------------------------------------
# Helper functions (pure, so they are easy to unit test)
# ---------------------------------------------------------------------------
set_website_style("98")
def is_number(text: str) -> bool:
    """Return True if text looks like a number such as 4, 2.5, or -90.4."""
    cleaned = text.strip()
    if cleaned.startswith("-"):
        cleaned = cleaned[1:]
    return cleaned.replace(".", "", 1).isdigit()


def is_positive_number(text: str) -> bool:
    """Return True if text is a number greater than zero."""
    return is_number(text) and float(text) > 0


def lookup_molar_mass(formula: str) -> float:
    """Return the molar mass of a supported formula, or 0.0 if unknown."""
    cleaned = formula.strip()
    if cleaned in MOLAR_MASSES:
        return MOLAR_MASSES[cleaned]
    return 0.0


def supported_formulas_text() -> str:
    """Return all supported formulas as one comma-separated string."""
    return ", ".join(MOLAR_MASSES.keys())


def moles_of(grams: float, molar_mass: float) -> float:
    """Convert grams to moles."""
    return grams / molar_mass


def find_limiting(reactants: list[Species]) -> Species:
    """Return the limiting reactant (smallest moles / coefficient).

    Assumes the list has at least one reactant.
    """
    limiting = reactants[0]
    smallest_ratio = moles_of(limiting.grams, limiting.molar_mass) / limiting.coefficient
    for reactant in reactants:
        ratio = moles_of(reactant.grams, reactant.molar_mass) / reactant.coefficient
        if ratio < smallest_ratio:
            smallest_ratio = ratio
            limiting = reactant
    return limiting


def theoretical_yield_grams(limiting: Species, product: Species) -> float:
    """Grams of product made if the limiting reactant is used up completely."""
    limiting_moles = moles_of(limiting.grams, limiting.molar_mass)
    reaction_units = limiting_moles / limiting.coefficient
    product_moles = reaction_units * product.coefficient
    return product_moles * product.molar_mass


def percent_yield(actual_grams: float, theoretical_grams: float) -> float:
    """Return actual / theoretical * 100 (0.0 if theoretical is zero)."""
    if theoretical_grams == 0:
        return 0.0
    return actual_grams / theoretical_grams * 100


def heat_released(delta_h_per_mole: float, product_moles: float) -> float:
    """Total heat flow in kJ: delta H per mole of product times moles made."""
    return delta_h_per_mole * product_moles


def classify_heat(delta_h: float) -> str:
    """Label a reaction by the sign of its delta H."""
    if delta_h < 0:
        return "exothermic"
    if delta_h > 0:
        return "endothermic"
    return "thermoneutral"


def heat_summary(heat_type: str, heat_kj: float) -> str:
    """Describe the heat flow in a sentence for the results page."""
    if heat_type == "exothermic":
        return f"Exothermic: about {abs(heat_kj):.2f} kJ released at full theoretical yield."
    if heat_type == "endothermic":
        return f"Endothermic: about {abs(heat_kj):.2f} kJ absorbed at full theoretical yield."
    return "Thermoneutral: no net heat flow."


def yield_comment(yield_percent: float) -> str:
    """Give a short interpretation of a percent yield."""
    if yield_percent > 100:
        return "Warning: over 100%. The product may be wet or impure, or a number was entered wrong."
    if yield_percent < 50:
        return "Low yield: product may have been lost in transfers or side reactions."
    return "This is a reasonable yield."


def build_experiment(name: str, reactants: list[Species], product: Species,
                     delta_h: float, notes: str) -> Experiment:
    """Run all calculations and package them as an Experiment."""
    limiting = find_limiting(reactants)
    theoretical = theoretical_yield_grams(limiting, product)
    product_moles = moles_of(theoretical, product.molar_mass)
    return Experiment(
        name, limiting.formula, theoretical, product.grams,
        percent_yield(product.grams, theoretical),
        heat_released(delta_h, product_moles), classify_heat(delta_h), notes)


def validate_calculation_inputs(reactants: list[Species], product_formula: str,
                                actual_yield: str, delta_h: str) -> str:
    """Return an error message for bad calculate-page input, or "" if all is fine."""
    if len(reactants) == 0:
        return "Add at least one reactant first."
    if lookup_molar_mass(product_formula) == 0.0:
        return "Product formula not supported. Try: " + supported_formulas_text()
    if not is_positive_number(actual_yield):
        return "Actual yield must be a number greater than 0."
    if not is_number(delta_h):
        return "Delta H must be a number (negative if heat is released)."
    return ""


# --- helpers that loop over the lists in State -----------------------------
def entered_reactant_rows(reactants: list[Species]) -> list[list[str]]:
    """Table rows for the reactants entered so far."""
    rows = [["Formula", "Coefficient", "Mass (g)"]]
    for reactant in reactants:
        rows.append([reactant.formula, str(reactant.coefficient), f"{reactant.grams:.2f}"])
    return rows


def reactant_formulas(reactants: list[Species]) -> list[str]:
    """Return just the formulas, used to fill the 'remove' SelectBox."""
    formulas = []
    for reactant in reactants:
        formulas.append(reactant.formula)
    return formulas


def reactant_equation_text(reactants: list[Species]) -> str:
    """Left half of the equation as text, e.g. '2 Mg + O2' (a coefficient of 1 is hidden)."""
    if len(reactants) == 0:
        return "(no reactants entered yet)"
    parts = []
    for reactant in reactants:
        if reactant.coefficient == 1:
            parts.append(reactant.formula)
        else:
            parts.append(f"{reactant.coefficient} {reactant.formula}")
    return " + ".join(parts)


def leftover_grams(reactant: Species, limiting: Species) -> float:
    """Grams of a reactant left over once the limiting reactant is used up."""
    reaction_units = moles_of(limiting.grams, limiting.molar_mass) / limiting.coefficient
    moles_used = reaction_units * reactant.coefficient
    moles_left = moles_of(reactant.grams, reactant.molar_mass) - moles_used
    if moles_left < 0:  # guards against tiny floating-point error
        return 0.0
    return moles_left * reactant.molar_mass


def moles_table_rows(reactants: list[Species], limiting: Species) -> list[list[str]]:
    """Table rows of moles, moles / coefficient, and leftover grams per reactant."""
    rows = [["Reactant", "Moles", "Moles / coefficient", "Leftover (g)", "Limiting?"]]
    for reactant in reactants:
        moles = moles_of(reactant.grams, reactant.molar_mass)
        ratio = moles / reactant.coefficient
        marker = ""
        if reactant.formula == limiting.formula:
            marker = "<-- limiting"
        rows.append([reactant.formula, f"{moles:.4f}", f"{ratio:.4f}",
                     f"{leftover_grams(reactant, limiting):.2f}", marker])
    return rows


def history_rows(experiments: list[Experiment]) -> list[list[str]]:
    """Table rows summarizing every saved experiment."""
    rows = [["Name", "Limiting", "Theoretical (g)", "Actual (g)", "Percent yield", "Heat"]]
    for experiment in experiments:
        rows.append([experiment.name, experiment.limiting_formula,
                     f"{experiment.theoretical_grams:.2f}",
                     f"{experiment.actual_grams:.2f}",
                     f"{experiment.yield_percent:.1f}%", experiment.heat_type])
    return rows


def experiment_names(experiments: list[Experiment]) -> list[str]:
    """Return just the names, used to fill the 'delete' SelectBox."""
    names = []
    for experiment in experiments:
        names.append(experiment.name)
    return names


def average_yield(experiments: list[Experiment]) -> float:
    """Average percent yield over all saved experiments (0.0 if none)."""
    if len(experiments) == 0:
        return 0.0
    total = 0.0
    for experiment in experiments:
        total += experiment.yield_percent
    return total / len(experiments)


def without_reactant(reactants: list[Species], formula: str) -> list[Species]:
    """Copy of the list with the FIRST reactant matching formula left out."""
    kept = []
    removed_one = False
    for reactant in reactants:
        if reactant.formula == formula and not removed_one:
            removed_one = True
        else:
            kept.append(reactant)
    return kept


def without_experiment(experiments: list[Experiment], name: str) -> list[Experiment]:
    """Copy of the list with the FIRST experiment matching name left out."""
    kept = []
    removed_one = False
    for experiment in experiments:
        if experiment.name == name and not removed_one:
            removed_one = True
        else:
            kept.append(experiment)
    return kept


# ---------------------------------------------------------------------------
# Routes (pages: index, reactants_page, product_page, results_page, history_page)
# ---------------------------------------------------------------------------
@route
def index(state: State) -> Page:
    """Home page: explains the tool and starts a new experiment."""
    return Page(state, [
        Header("Reaction Yield Lab", 1),
        "Find the limiting reactant, theoretical yield, percent yield, and heat "
        "released for a reaction without hand calculations.",
        LineBreak(),
        # Input 1 (one line for the prompt, one for the box)
        "Experiment name (any label you like, e.g. Magnesium combustion - Trial 1):",
        TextBox("experiment_name", state.experiment_name),
        LineBreak(),
        Button("Start experiment", save_name),
        Button("View history", history_page),
        LineBreak(),
        state.status_message,
    ])


@route
def save_name(state: State, experiment_name: str) -> Page:
    """Save the experiment name and clear any old reactants."""
    if experiment_name.strip() == "":
        state.status_message = "Please give your experiment a name."
        return index(state)
    state.experiment_name = experiment_name.strip()
    state.reactants = []
    state.status_message = ""
    return reactants_page(state)


@route
def reactants_page(state: State) -> Page:
    """Page for entering and removing reactants."""
    content = [
        Header("Reactants for " + state.experiment_name, 2),
        # Reactants entered so far (the left half of the equation)
        "Equation so far: " + reactant_equation_text(state.reactants) + " -> ?",
        Table(entered_reactant_rows(state.reactants)),
        LineBreak(),
        # Input 1: formula
        "1. Reactant formula (exactly as in the supported list below, e.g. Mg or O2):",
        TextBox("formula", ""),
        LineBreak(),
        # Input 2: coefficient
        "2. Coefficient (the number in front of it in your balanced equation):",
        SelectBox("coefficient", COEFFICIENT_CHOICES, "1"),
        LineBreak(),
        # Input 3: starting mass
        "3. Starting mass in grams (a number greater than 0, e.g. 12.0):",
        TextBox("grams", ""),
        LineBreak(),
        Button("Add reactant", add_reactant),
    ]
    if len(state.reactants) > 0:
        content.append(LineBreak())
        content.append("Made a mistake? Choose a reactant to remove:")
        content.append(SelectBox("formula_to_remove", reactant_formulas(state.reactants)))
        content.append(LineBreak())
        content.append(Button("Remove selected", remove_reactant))
    content.append(LineBreak())
    content.append(state.status_message)
    content.append(Button("Next: product and yield", product_page))
    content.append(LineBreak())
    content.append("Supported formulas: " + supported_formulas_text())
    return Page(state, content)


@route
def add_reactant(state: State, formula: str, coefficient: str, grams: str) -> Page:
    """Validate the form and add a reactant to the state."""
    molar_mass = lookup_molar_mass(formula)
    if molar_mass == 0.0:
        state.status_message = "Formula not supported. Check the list below."
    elif not is_positive_number(grams):
        state.status_message = "Mass must be a number greater than 0."
    else:
        state.reactants.append(
            Species(formula.strip(), molar_mass, int(coefficient), float(grams)))
        state.status_message = "Added " + formula.strip() + "."
    return reactants_page(state)


@route
def remove_reactant(state: State, formula_to_remove: str) -> Page:
    """Remove the chosen reactant from the state."""
    state.reactants = without_reactant(state.reactants, formula_to_remove)
    state.status_message = "Removed " + formula_to_remove + "."
    return reactants_page(state)


@route
def product_page(state: State) -> Page:
    """Page for the product, actual yield, delta H, and notes."""
    return Page(state, [
        Header("Product and yield for " + state.experiment_name, 2),
        # Top of page: the left half of the equation (the reactants)
        "Your reactants (left side of the equation):",
        reactant_equation_text(state.reactants) + " -> ?",
        Table(entered_reactant_rows(state.reactants)),
        LineBreak(),
        # Input 1: product formula
        "1. Product formula (exactly as in the supported list, e.g. MgO):",
        TextBox("product_formula", state.product.formula),
        LineBreak(),
        # Input 2: product coefficient
        "2. Product coefficient (the number in front of it in your balanced equation):",
        SelectBox("product_coefficient", COEFFICIENT_CHOICES, "1"),
        LineBreak(),
        # Input 3: actual yield
        "3. Actual yield you collected in grams (a number greater than 0):",
        TextBox("actual_yield", ""),
        LineBreak(),
        # Input 4: delta H
        "4. Delta H in kJ per mole of product (negative if heat is released, e.g. -601.6):",
        TextBox("delta_h", ""),
        LineBreak(),
        # Input 5: notes
        "5. Lab notes (optional):",
        TextArea("notes", ""),
        LineBreak(),
        Button("Calculate", calculate),
        Button("Back to reactants", reactants_page),
        LineBreak(),
        state.status_message,
    ])


@route
def calculate(state: State, product_formula: str, product_coefficient: str,
              actual_yield: str, delta_h: str, notes: str) -> Page:
    """Validate input, run the calculations, and save the experiment."""
    error = validate_calculation_inputs(
        state.reactants, product_formula, actual_yield, delta_h)
    if error != "":
        state.status_message = error
        return product_page(state)
    state.product = Species(
        product_formula.strip(), lookup_molar_mass(product_formula),
        int(product_coefficient), float(actual_yield))
    state.saved_experiments.append(build_experiment(
        state.experiment_name, state.reactants, state.product,
        float(delta_h), notes))
    state.status_message = ""
    return results_page(state)


@route
def results_page(state: State) -> Page:
    """Show the most recent experiment's results."""
    if len(state.saved_experiments) == 0:
        return Page(state, ["No results yet.", Button("Home", index)])
    latest = state.saved_experiments[-1]
    # Each result: a plain label line, then the value as a larger header so it stands out.
    return Page(state, [
        Header("Results: " + latest.name, 1),
        LineBreak(),
        "Limiting reactant:",
        Header(latest.limiting_formula, 2),
        LineBreak(),
        "Theoretical yield:",
        Header(f"{latest.theoretical_grams:.2f} g", 2),
        LineBreak(),
        "Actual yield:",
        Header(f"{latest.actual_grams:.2f} g", 2),
        LineBreak(),
        "Percent yield:",
        Header(f"{latest.yield_percent:.1f}%", 2),
        f"({latest.actual_grams:.2f} / {latest.theoretical_grams:.2f} x 100)",
        yield_comment(latest.yield_percent),
        LineBreak(),
        "Heat flow at full theoretical yield:",
        Header(f"{latest.heat_kj:.2f} kJ ({latest.heat_type})", 2),
        heat_summary(latest.heat_type, latest.heat_kj),
        LineBreak(),
        # Details last, since they are secondary to the answers above
        "Moles breakdown:",
        Table(moles_table_rows(state.reactants, find_limiting(state.reactants))),
        LineBreak(),
        Button("New experiment", index),
        Button("View history", history_page),
    ])


@route
def history_page(state: State) -> Page:
    """List every saved experiment, with options to delete or clear."""
    if len(state.saved_experiments) == 0:
        return Page(state, [
            Header("History", 2), "No saved experiments yet.", Button("Home", index)])
    return Page(state, [
        Header("History", 2),
        Table(history_rows(state.saved_experiments)),
        f"Average percent yield: {average_yield(state.saved_experiments):.1f}%",
        SelectBox("experiment_to_delete", experiment_names(state.saved_experiments)),
        Button("Delete selected", delete_experiment),
        Button("Clear everything", reset),
        Button("Home", index),
        state.status_message,
    ])


@route
def delete_experiment(state: State, experiment_to_delete: str) -> Page:
    """Delete the chosen experiment from the history."""
    state.saved_experiments = without_experiment(
        state.saved_experiments, experiment_to_delete)
    state.status_message = "Deleted " + experiment_to_delete + "."
    return history_page(state)


@route
def reset(state: State) -> Page:
    """Clear all data and return to the home page."""
    state.experiment_name = ""
    state.reactants = []
    state.product = Species("", 0.0, 1, 0.0)
    state.saved_experiments = []
    state.status_message = "Everything was cleared."
    return index(state)


# ---------------------------------------------------------------------------
# Unit tests (module-level assert_equal calls, as in the course)
# ---------------------------------------------------------------------------
SAMPLE_A = Species("A", 10.0, 1, 20.0)   # 2.0 mol, ratio 2.0
SAMPLE_B = Species("B", 20.0, 2, 20.0)   # 1.0 mol, ratio 0.5 -> limiting
SAMPLE_PRODUCT = Species("P", 50.0, 1, 20.0)

# is_number / is_positive_number
assert_equal(is_number("4"), True)
assert_equal(is_number("-90.4"), True)
assert_equal(is_number("abc"), False)
assert_equal(is_number(""), False)
assert_equal(is_number("1.2.3"), False)
assert_equal(is_positive_number("5"), True)
assert_equal(is_positive_number("-5"), False)
assert_equal(is_positive_number("0"), False)

# lookups and conversions
assert_equal(lookup_molar_mass("H2O"), 18.015)
assert_equal(lookup_molar_mass(" H2O "), 18.015)
assert_equal(lookup_molar_mass("XYZ"), 0.0)
assert_equal(moles_of(20.0, 10.0), 2.0)

# core chemistry
assert_equal(find_limiting([SAMPLE_A, SAMPLE_B]), SAMPLE_B)
assert_equal(find_limiting([SAMPLE_A]), SAMPLE_A)
assert_equal(theoretical_yield_grams(SAMPLE_B, SAMPLE_PRODUCT), 25.0)
assert_equal(percent_yield(20.0, 25.0), 80.0)
assert_equal(percent_yield(20.0, 0.0), 0.0)
assert_equal(heat_released(-100.0, 0.5), -50.0)
assert_equal(classify_heat(-5.0), "exothermic")
assert_equal(classify_heat(5.0), "endothermic")
assert_equal(classify_heat(0.0), "thermoneutral")
assert_equal(yield_comment(120.0)[:8], "Warning:")
assert_equal(yield_comment(30.0)[:9], "Low yield")
assert_equal(yield_comment(80.0), "This is a reasonable yield.")
assert_equal(heat_summary("thermoneutral", 0.0), "Thermoneutral: no net heat flow.")

# validation
assert_equal(validate_calculation_inputs([], "P", "5", "-1"),
             "Add at least one reactant first.")
assert_equal(validate_calculation_inputs([SAMPLE_A], "H2O", "5", "-1"), "")
assert_equal(validate_calculation_inputs([SAMPLE_A], "H2O", "x", "-1"),
             "Actual yield must be a number greater than 0.")
assert_equal(validate_calculation_inputs([SAMPLE_A], "H2O", "5", "x"),
             "Delta H must be a number (negative if heat is released).")

# loops over the lists
assert_equal(leftover_grams(SAMPLE_A, SAMPLE_B), 15.0)
assert_equal(leftover_grams(SAMPLE_B, SAMPLE_B), 0.0)
assert_equal(moles_table_rows([SAMPLE_A, SAMPLE_B], SAMPLE_B),
             [["Reactant", "Moles", "Moles / coefficient", "Leftover (g)", "Limiting?"],
              ["A", "2.0000", "2.0000", "15.00", ""],
              ["B", "1.0000", "0.5000", "0.00", "<-- limiting"]])
assert_equal(reactant_equation_text([SAMPLE_A, SAMPLE_B]), "A + 2 B")
assert_equal(reactant_equation_text([]), "(no reactants entered yet)")
assert_equal(reactant_formulas([SAMPLE_A, SAMPLE_B]), ["A", "B"])
assert_equal(entered_reactant_rows([SAMPLE_A]),
             [["Formula", "Coefficient", "Mass (g)"], ["A", "1", "20.00"]])
SAMPLE_EXPERIMENT = Experiment("Lab 1", "B", 25.0, 20.0, 80.0, -50.0, "exothermic", "")
assert_equal(history_rows([SAMPLE_EXPERIMENT]),
             [["Name", "Limiting", "Theoretical (g)", "Actual (g)", "Percent yield", "Heat"],
              ["Lab 1", "B", "25.00", "20.00", "80.0%", "exothermic"]])
assert_equal(experiment_names([SAMPLE_EXPERIMENT]), ["Lab 1"])
assert_equal(average_yield([SAMPLE_EXPERIMENT]), 80.0)
assert_equal(average_yield([]), 0.0)
assert_equal(without_reactant([SAMPLE_A, SAMPLE_B], "A"), [SAMPLE_B])
assert_equal(without_experiment([SAMPLE_EXPERIMENT], "Lab 1"), [])
assert_equal(build_experiment("Lab 1", [SAMPLE_A, SAMPLE_B], SAMPLE_PRODUCT,
                              -100.0, ""), SAMPLE_EXPERIMENT)

# routes: each test checks the state of the Page the route returns
route_state = make_empty_state()
assert_equal(save_name(route_state, "Lab 1").state.experiment_name, "Lab 1")
assert_equal(save_name(make_empty_state(), "  ").state.status_message,
             "Please give your experiment a name.")
route_state = make_empty_state()
assert_equal(len(add_reactant(route_state, "H2O", "2", "9.0").state.reactants), 1)
assert_equal(len(add_reactant(route_state, "XYZ", "1", "9.0").state.reactants), 1)
assert_equal(len(add_reactant(route_state, "H2", "1", "-3").state.reactants), 1)
assert_equal(len(remove_reactant(route_state, "H2O").state.reactants), 0)
route_state = make_empty_state()
route_state.experiment_name = "Lab 1"
add_reactant(route_state, "Mg", "2", "12.0")
add_reactant(route_state, "O2", "1", "4.0")
calculate(route_state, "MgO", "2", "9.0", "-601.6", "test")
assert_equal(len(route_state.saved_experiments), 1)
assert_equal(route_state.product.formula, "MgO")
assert_equal(route_state.saved_experiments[0].limiting_formula, "O2")
assert_equal(len(delete_experiment(route_state, "Lab 1").state.saved_experiments), 0)
assert_equal(reset(route_state).state.experiment_name, "")
# index, product_page, results_page, and history_page only display data, so
# their tests just confirm the state is passed through unchanged.
assert_equal(index(make_empty_state()).state, make_empty_state())
assert_equal(product_page(make_empty_state()).state, make_empty_state())
assert_equal(results_page(make_empty_state()).state, make_empty_state())
assert_equal(history_page(make_empty_state()).state, make_empty_state())
assert_equal(reactants_page(make_empty_state()).state, make_empty_state())

# ---------------------------------------------------------------------------
# Site setup
# ---------------------------------------------------------------------------
set_website_title("Reaction Yield Lab")
set_site_information(
    author="Brody Hood",
    description="Calculates limiting reactant, theoretical and percent yield, "
                "and heat flow for chemical reactions.",
    sources=["Chemistry 2e (OpenStax), Chapter 4"],
    planning=["planning.md"],
    links=[],
)
hide_debug_information()
start_server(make_empty_state())
