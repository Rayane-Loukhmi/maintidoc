from maintidoc.generation import build_prompt, fallback_answer, validate_citations


def test_fallback_has_citation():
    evidence = [{"id": "P05-TEXT", "page": 5, "type": "text", "content": "AL-01 orange"}]
    answer = fallback_answer("Question", evidence)
    assert answer["status"] == "answered"
    assert answer["citations"] == [{"id": "P05-TEXT", "page": 5}]


def test_unknown_citation_is_reported():
    evidence = [{"id": "P05-TEXT", "page": 5, "type": "text", "content": "x"}]
    response = {"status": "answered", "answer": "x", "citations": [{"id": "BAD", "page": 99}]}
    issues = validate_citations(response, evidence)
    assert any("inconnue" in issue for issue in issues)


def test_prompt_contains_image_description():
    evidence = [{"id": "P05-TAB01", "page": 5, "type": "table", "content": "AL-01"}]
    prompt = build_prompt("Que signifie AL-01 ?", evidence, language="en",
                          image_description="Orange LED visible")
    assert "Orange LED visible" in prompt
    assert "P05-TAB01" in prompt
