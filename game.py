import os
from datetime import datetime as dt
from itertools import product

import pandas as pd
import numpy as np

import config as cfg

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = RESET = ""

    class Style:
        BRIGHT = RESET_ALL = ""


def c(text, *codes):
    """Wrap text in color codes when colorama is available."""
    if not HAS_COLOR:
        return str(text)
    return f"{''.join(codes)}{text}{Style.RESET_ALL}"


def select_player(df_stats: pd.DataFrame) -> str:
    if df_stats.empty:
        return input("Enter player name: ").strip()

    players = {i: u for i, u in enumerate(df_stats["player"].drop_duplicates().values, 1)}
    print("Select an existing player or type a new name:")
    for i, u in players.items():
        print(f"  {i} : {u}")
    choice = input(" >> ").strip()

    if choice.isnumeric() and int(choice) in players:
        current_player = players[int(choice)]
    else:
        current_player = choice

    print(f"Player: {c(current_player, Fore.CYAN)}")
    return current_player


def select_difficulty():
    levels = {
        "1": ("Easy",   cfg.FIGURES_EASY,    80),
        "2": ("Medium", cfg.FIGURES_MEDIUM, 100),
        "3": ("Hard",   cfg.FIGURES_HARD,   200),
    }
    print("\nDifficulty:  1=Easy (2-12)  2=Medium (2-50)  3=Hard (2-99)  [default: 2]")
    choice = input(" >> ").strip()
    name, figures, max_result = levels.get(choice, levels["2"])
    print(f"Difficulty: {c(name, Fore.CYAN)}")
    return figures, max_result


def select_operations():
    options = {
        "1": (["+"],              "Addition only"),
        "2": (["-"],              "Subtraction only"),
        "3": (["*"],              "Multiplication only"),
        "4": (["/"],              "Division only"),
        "":  (["+", "-", "*", "/"], "All operations"),
    }
    print("Operations:  1=+  2=-  3=*  4=/  Enter=All  [default: All]")
    choice = input(" >> ").strip()
    ops, label = options.get(choice, options[""])
    print(f"Operations: {c(label, Fore.CYAN)}")
    return ops


def generate_valid_questions(figures, operation, max_result=100):
    questions = []
    for a, b in product(figures, figures):
        q = f"{a:2} {operation} {b:2}"
        res = eval(q)
        if res > max_result or res < 0:
            continue
        if operation == "/" and (np.floor(res) != res or res == 1):
            continue
        questions.append((q, int(res)))
    return questions


def play_round(player, figures, max_result, operations):
    test_start = dt.now().strftime("%Y-%m-%d %T")
    per_op = cfg.TOTAL_QUESTIONS // len(operations)

    round_questions = []
    for op in operations:
        pool = generate_valid_questions(figures, op, max_result)
        n = min(per_op, len(pool))
        indices = np.random.choice(len(pool), n, replace=False)
        round_questions += [pool[i] for i in indices]

    np.random.shuffle(round_questions)

    answers, times, scores = [], [], []
    streak = 0
    max_streak = 0
    total = len(round_questions)

    for i, (q, expected) in enumerate(round_questions):
        t0 = dt.now()

        while True:
            raw = input(f"{i+1}/{total}: What is {q} = ").strip()
            try:
                given = int(raw)
                break
            except ValueError:
                print(c("Please enter a whole number.", Fore.YELLOW))

        elapsed = (dt.now() - t0).total_seconds()
        correct = given == expected

        if correct:
            streak += 1
            max_streak = max(max_streak, streak)
            msg = c("Correct! Good job!", Fore.GREEN)
            if streak >= 3:
                msg += c(f"  {streak} in a row!", Fore.MAGENTA, Style.BRIGHT)
            print(msg)
        else:
            streak = 0
            print(c(f"Nope... the correct answer is {expected}", Fore.RED))

        # Score: 100 base + speed bonus (up to 50) + streak bonus (up to 100)
        q_score = (100 + max(0, 50 - int(elapsed) * 5) + min(streak, 10) * 10) if correct else 0
        answers.append(int(correct))
        times.append(elapsed)
        scores.append(q_score)

    print(c(f"\nBest streak this round: {max_streak}", Fore.CYAN))

    return pd.DataFrame({
        "player":        player,
        "question":      [q for q, _ in round_questions],
        "expected":      [e for _, e in round_questions],
        "answer":        answers,
        "question_time": times,
        "score":         scores,
        "test_time":     test_start,
    })


def print_test_report(stats, player, df_stats):
    print("=" * 80)
    accuracy = stats["answer"].mean() * 100
    total_time = stats["question_time"].sum()
    avg_time = stats["question_time"].mean()
    total_score = stats["score"].sum()

    if accuracy == 100:
        print(c("AMAZING! Not a single mistake!", Fore.GREEN, Style.BRIGHT))
    elif accuracy >= 80:
        print(c("Great job!", Fore.GREEN))
    elif accuracy >= 60:
        print(c("Good effort! Keep practicing.", Fore.YELLOW))
    else:
        print(c("Keep trying, you'll get there!", Fore.RED))

    print(f"Accuracy:   {c(f'{accuracy:.1f}%', Fore.CYAN)}")
    print(f"Total time: {total_time:.1f}s   Avg per question: {avg_time:.1f}s")
    print(f"Score:      {c(str(int(total_score)), Fore.MAGENTA, Style.BRIGHT)} points")

    # Personal best
    if not df_stats.empty and "answer" in df_stats.columns and player in df_stats["player"].values:
        prev = df_stats[df_stats["player"] == player]
        prev_best = prev.groupby("test_time")["answer"].mean().max() * 100
        if accuracy > prev_best:
            print(c("New personal best!", Fore.GREEN, Style.BRIGHT))

    print("-" * 80)


def print_wrong_answers(stats):
    wrong = stats[stats["answer"] == 0]
    if wrong.empty:
        return
    print(c(f"\nReview - {len(wrong)} missed question(s):", Fore.YELLOW))
    for _, row in wrong.iterrows():
        print(f"  {row['question']} = {c(str(row['expected']), Fore.GREEN)}")


def print_leaderboard(df_stats):
    print("=" * 80)
    print("Leaderboard (top 5):")
    print("-" * 80)
    board = (
        df_stats.groupby("player")[["answer", "question_time"]]
        .mean()
        .sort_values("answer", ascending=False)
        .head(5)
    )
    board["accuracy"] = board["answer"].map(lambda x: f"{x*100:.1f}%")
    board["avg_time"] = board["question_time"].map(lambda x: f"{x:.1f}s")
    print(board[["accuracy", "avg_time"]])
    print("-" * 80)


def main():
    df_stats = pd.read_csv(cfg.STATS_FILE) if os.path.exists(cfg.STATS_FILE) else pd.DataFrame()

    current_player = select_player(df_stats)
    figures, max_result = select_difficulty()
    operations = select_operations()

    stats = play_round(current_player, figures, max_result, operations)

    print_test_report(stats, current_player, df_stats)
    print_wrong_answers(stats)

    df_stats = pd.concat([df_stats, stats], ignore_index=True)
    df_stats.to_csv(cfg.STATS_FILE, index=False)

    print_leaderboard(df_stats)


if __name__ == "__main__":
    main()
