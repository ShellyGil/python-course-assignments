import periodic_table_quiz

def test_quiz_correct(monkeypatch):
    # Simulate correct answers for the first 5 elements
    answers = [name for _, name in list(periodic_table_quiz.elements.items())[:5]]
    inputs = iter(answers)
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    periodic_table_quiz.random = __import__('random')  # Ensure random is available
    periodic_table_quiz.quiz()
    # No assertion: just check that the function runs without error

def test_quiz_incorrect(monkeypatch):
    # Simulate incorrect answers
    inputs = iter(['Wrong'] * 5)
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    periodic_table_quiz.random = __import__('random')
    periodic_table_quiz.quiz()
    # No assertion: just check that the function runs without error
