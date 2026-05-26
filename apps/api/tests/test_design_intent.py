"""Design intent fidelity inference tests."""

from app.services.design_intent import infer_fidelity_fields


def test_infer_layout_only_from_realism_keywords():
    plan = infer_fidelity_fields(
        {"task_class": "A", "summary": "Zippo 打火机", "strategy": "from_scratch"},
        "设计一个 zippo，要求细节逼真",
    )
    assert plan["fidelity"] == "layout_only"
    assert plan["high_fidelity_requested"] is True


def test_infer_printable_for_plain_assembly():
    plan = infer_fidelity_fields(
        {"task_class": "A", "summary": "90mm 五部件装配", "strategy": "from_scratch"},
        "做一个盒子支架",
    )
    assert plan["fidelity"] == "printable"
    assert plan["high_fidelity_requested"] is False


def test_respects_explicit_fidelity():
    plan = infer_fidelity_fields(
        {
            "task_class": "B",
            "summary": "装饰",
            "strategy": "from_scratch",
            "fidelity": "decorative",
        },
        "要逼真",
    )
    assert plan["fidelity"] == "decorative"
