from ftl.rules import Rule, structure, unstructure
from ftl.tasks import EncodeMp4, parameterize


def test_list_of_rules_serialization():
    rule1 = Rule(
        name="Encode File",
        file_type="FileSequence",
        file_patterns=["*.mov"],
        tasks=[
            parameterize(
                EncodeMp4,
                input_colorspace="linear",
                max_size=1920,
                fps=24,
                vcodec="h264",
            )
        ],
    )
    rule2 = Rule(
        name="Encode File Sequences",
        file_type="FileSequence",
        file_patterns=["*"],
        tasks=[
            parameterize(
                EncodeMp4,
                input_colorspace="rgb",
                max_size=512,
                fps=24,
                vcodec="h264",
            )
        ],
    )
    rules = [rule1, rule2]

    rules_data = unstructure(rules)
    rules_round_tripped = structure(rules_data, list[Rule])
    assert rules == rules_round_tripped


def test_rule_serialization():
    rule = Rule(
        name="Encode File",
        file_type="FileSequence",
        file_patterns=["*.mov"],
        tasks=[
            parameterize(
                EncodeMp4,
                input_colorspace="linear",
                max_size=1920,
                fps=24,
                vcodec="h264",
            )
        ],
    )

    rule_data = unstructure(rule)
    rule_round_tripped = structure(rule_data, Rule)
    assert rule == rule_round_tripped
