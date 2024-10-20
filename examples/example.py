from Noema import *

s = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")

def count_letters(word):
    return len(word)

n1 = Noesis("Description of the word",('p1','p2'),[
    Print("Hello {p1} {p2}"),
    IF(lambda: s.p2 < 6, [
        PrintNoema(),
        Return("Hello {p1} {p2} is less than 6.")
    ]),
    PrintNoema(),
    Return("Hello {p1} {p2}")
])

s = Horizon(
    Var(word = "Hello"),
    Var(nb_letters = lambda: count_letters(s.word)),
    CallFunction(res = lambda: count_letters(s.word)),
    Constitute(res = lambda: n1(s, p1=s.word,p2=s.nb_letters)),
    Print("After Noesis: {res}"),
    Print("Nb letters: {nb_letters}, in word: {word}"),   
    Var(test = "{word} has {nb_letters} letters."),
    Print("Test: {test}"),
    Sentence(nb_explanation = "Explain why there is {nb_letters} in the word {word}." ),
    Print("Explanation: {nb_explanation}"),
    Int(nbLettersI = "How many letters are there in the word {word}?"),
    Float(nbLettersF = "How many letters are there in the word {word}?"),
    Bool(nbLettersB = "Are there {nb_letters} letters in the word {word}?"),
    ListOf(Word, words = "Give me a list of 5 words."),
    Print("Nb letters: {nbLettersI}"),
    Print("Nb letters: {nbLettersF}"),
    Print("Bool: {nbLettersB}"),
    Print("Words: {words}"),
    Var(vnb = 6),
    IF(lambda: s.nbLettersI < 6, [
        Word(thought2 = "Résume en un mot '{nbLettersI} est inférieur à 6.'"),
        Print("In True {thought2}")
    ], ELSE=[
        Word(thought2 = "Résume en un mot '{nbLettersI} est sup à 6.'"),
        Print("In False {thought2}")
    ]),
    Repeat(lambda: s.nbLettersI, [
        Word(word = "Choose a word."),
        Print("Word: {word}")
    ]),
    ForEach(["1","2","3"], [
        Bool(value = "Is {idx} equal to {item}?"),
        Print("Is {idx} equal to {item}?"),
        Print("Bool: {value}")
    ]),
    While(lambda: s.vnb >= 6, [
        Word(word = "Choose a new word."),
        Print("Word: {word}"),
        Var(nbLettersI = lambda: count_letters(s.word)),
        Print("Nb letters: {nbLettersI}"),
        Var(vnb = lambda: s.nbLettersI - 2),
        Print("vnb: {vnb}")
    ]),
    PrintNoema(),
).constituteWith(s)

