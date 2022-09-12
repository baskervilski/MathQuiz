import os
from datetime import datetime as dt
from itertools import product

import pandas as pd
import numpy as np

import config as cfg


def select_player(df_stats: pd.DataFrame) -> str:

    if df_stats.empty:
        current_player = input("Enter player name: ")
    else:
        players = {
            i: u for i, u in enumerate(df_stats["player"].drop_duplicates().values, 1)
        }

        print("Select an existing player or type a new name: ")
        for i, u in players.items():
            print(i, ":", u)
        current_player = input(" >> ")

        if current_player.isnumeric():
            if int(current_player) in players:
                current_player = players[int(current_player)]
            else:
                print("User index invalid!")

    print("Player selected:", current_player)

    return current_player


def print_user_overall_stats(df_stats):

    print("=" * 80)
    print("Stats per user:")
    print("-" * 80)

    print(
        df_stats.groupby(["player"])[["answer", "question_time"]]
        .mean()
        .sort_values(by="answer", ascending=False)
    )

    print("-" * 80)


def print_test_report(test_stats):

    print("=" * 80)

    print(f"{test_stats.answer.mean()*100:.1f} % of correct answers")
    print(f"{test_stats.question_time.sum():.1f} seconds in total")
    print(f"{test_stats.question_time.mean():.1f} seconds per question, on average")

    if test_stats.answer.mean() == 1:
        print("AMAZING! Not a single mistake!")

    print("-" * 80)


def generate_all_valid_questions(
    figures, operations=("*", "+", "-", "/"), max_result=100
):

    all_valid_questions = []
    for a, op, b in product(figures, operations, figures):
        q_string = f"{a:2} {op} {b:2}"
        res = eval(q_string)

        if res > max_result:
            continue

        if op == "/" and (np.floor(res) != float(res) or res == 1):
            continue
        all_valid_questions.append([q_string, res])

    return all_valid_questions


def play_round(player):

    test_start = dt.now().strftime("%Y-%m-%d %T")

    round_questions = []
    for op in ["/", "-", "+", "*"]:
        valid_op_questions = generate_all_valid_questions(cfg.FIGURES, operations=[op])
        # results = [abs(res) for _, res in valid_op_questions]
        # sum_res = sum(results)
        # probas = [r/sum_res for r in results]
        # assert sum(probas) == 1, sum(probas)
        choice_indices = np.random.choice(
            len(valid_op_questions),
            cfg.N_QUESTIONS,
            replace=False,
            # p=probas,
        )
        round_questions += [valid_op_questions[i] for i in choice_indices]

    answers = []
    times_per_question = []

    for i, (q, answer_expected) in enumerate(round_questions):

        t0 = dt.now()
        # answer_expected = eval(q)
        answer_given = input(f"{i+1}/{cfg.N_QUESTIONS}: What is {q} = ")

        if answer_correct := int(answer_given) == answer_expected:
            print("Correct! Good job!")
        else:
            print(f"Nope... :-( the correct answer is = {answer_expected}")

        answers.append(answer_correct)
        times_per_question.append((dt.now() - t0).total_seconds())

    print("End of the test!")

    this_test_stats = pd.DataFrame(
        {
            "player": player,
            "question": round_questions,
            "answer": answers,
            "question_time": times_per_question,
            "test_time": test_start,
        }
    )

    return this_test_stats


def main():

    if os.path.exists(cfg.STATS_FILE):
        df_stats = pd.read_csv(cfg.STATS_FILE)
    else:
        df_stats = pd.DataFrame()

    current_player = select_player(df_stats)

    this_test_stats = play_round(player=current_player)

    print_test_report(this_test_stats)

    df_stats = df_stats.append(this_test_stats)

    df_stats.to_csv(cfg.STATS_FILE, index=False)

    print_user_overall_stats(df_stats)


if __name__ == "__main__":
    main()
