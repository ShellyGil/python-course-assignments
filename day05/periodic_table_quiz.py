"""
Periodic Table Quiz Game
"""
import random

elements = {
    'H': 'Hydrogen',
    'He': 'Helium',
    'Li': 'Lithium',
    'Be': 'Beryllium',
    'B': 'Boron',
    'C': 'Carbon',
    'N': 'Nitrogen',
    'O': 'Oxygen',
    'F': 'Fluorine',
    'Ne': 'Neon',
    'Na': 'Sodium',
    'Mg': 'Magnesium',
    'Al': 'Aluminum',
    'Si': 'Silicon',
    'P': 'Phosphorus',
    'S': 'Sulfur',
    'Cl': 'Chlorine',
    'Ar': 'Argon',
    'K': 'Potassium',
    'Ca': 'Calcium',
}

def quiz():
    print("Welcome to the Periodic Table Quiz!")
    print("Type the name of the element for each symbol.")
    score = 0
    questions = random.sample(list(elements.items()), 5)
    for symbol, name in questions:
        answer = input(f"What is the name of the element with symbol '{symbol}'? ").strip()
        if answer.lower() == name.lower():
            print("Correct!")
            score += 1
        else:
            print(f"Incorrect. The correct answer is {name}.")
    print(f"Your score: {score}/5")

if __name__ == "__main__":
    quiz()
