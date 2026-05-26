"""Forge modeling recipes and plan enrichment."""

from app.services.forge_modeling import (
    CAPABILITY_GAP_PREFIX,
    analyze_forge_capability,
    enrich_plan_geometry_recipes,
)


def test_enrich_plan_geometry_recipes_from_assembly_spec():
    plan = enrich_plan_geometry_recipes(
        {
            "task_class": "A",
            "assembly_spec": [
                {"id": "CaseShell", "role": "shell"},
                {"id": "Motor", "role": "internal"},
            ],
        }
    )
    recipes = plan["geometry_recipes"]
    assert len(recipes) == 2
    by_id = {r["part_id"]: r["recipe"] for r in recipes}
    assert by_id["CaseShell"] == "sketch_extrude_shell"
    assert by_id["Motor"] == "primitive_layout"


def test_analyze_forge_capability_detects_recipe_gap():
    source = 'return [{ name: "CaseShell", shape: box(10,10,10) }];'
    report = analyze_forge_capability(
        source,
        [{"part_id": "CaseShell", "recipe": "sketch_extrude_shell"}],
        design_intent={"task_class": "A", "fidelity": "printable"},
    )
    assert report["gaps"]
    assert report["gaps"][0].startswith(CAPABILITY_GAP_PREFIX)


def test_analyze_forge_capability_recognizes_sketch_shell():
    source = """
    const sk = constrainedSketch();
    const body = sk.solve().extrude(5).subtract(box(1,1,1));
    return [{ name: "CaseShell", shape: body }];
    """
    report = analyze_forge_capability(
        source,
        [{"part_id": "CaseShell", "recipe": "sketch_extrude_shell"}],
        design_intent={"task_class": "A"},
    )
    assert report["advanced_modeling"] is True
    assert not report["gaps"]
