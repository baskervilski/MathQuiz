#%%

import os
import pandas as pd
import numpy as np
from datetime import datetime as dt

import config as cfg

#%%



#%%

def select_player(df_stats):

    if df_stats.empty:
        current_player = input("Enter player name: ")
    else:
        players = {i: u for i, u in enumerate(df_stats['player'].drop_duplicates().values, 1)}

        print("Select an existing player or type a new name: ")
        {print(i, ":", u) for i, u in players.items()}
        current_player = input(" >> ")

        if current_player.isnumeric():
            if int(current_player) in players:
                current_player = players[int(current_player)]
            else:
                print('User index invalid!')

    print("Player selected:", current_player)

    return current_player


def print_user_overall_stats(df_stats):
    
    print('='*80)
    print('Stats per user:')
    print('-'*80)

    print(
        df_stats\
            .groupby(['player'])[['answer', 'question_time']]\
            .mean()\
            .sort_values(by='answer', ascending=False)
    )

    print('-'*80)


def print_test_report(test_stats): 

    print('='*80)

    print(f"{test_stats.answer.mean()*100:.1f} % of correct answers")
    print(f"{test_stats.question_time.sum():.1f} seconds in total")
    print(f"{test_stats.question_time.mean():.1f} seconds per question, on average")

    if test_stats.answer.mean() == 1:
        print('AMAING! Not a single mistake!') 

    print('-'*80)


#%% 

def main():

    if os.path.exists(cfg.stats_file):
        df_stats = pd.read_csv(cfg.stats_file)
    else:
        df_stats = pd.DataFrame()

    current_player = select_player(df_stats)

    test_start = dt.now().strftime('%Y-%m-%d %T')

    questions = []
    answers = []
    times_per_question = []

    figures = cfg.figures

    for i in range(cfg.n_questions):

        t0 = dt.now()

        while 1:
            a = np.random.choice(figures)
            b = np.random.choice(figures)

            # If question already asked, generate another one
            if sorted([a, b]) not in questions:
                break

        questions.append([a, b])
        odgovor = input(f'{i+1}/{cfg.n_questions}: What is {a} * {b} = ')

        odgovor_tacan = (int(odgovor) == a * b)

        if odgovor_tacan:
            print('Correct! Good job!')
        else:
            print(f'Nope... :-( the correct answer is = {a*b}')

        answers.append(odgovor_tacan)
        times_per_question.append((dt.now() - t0).total_seconds())

    print('End of the test!')

    this_test_stats = pd.DataFrame({
        'player': current_player,
        'question': questions,
        'answer': answers,
        'question_time': times_per_question,
        'test_time': test_start
    })

    print_test_report(this_test_stats)

    df_stats = df_stats.append(this_test_stats)

    df_stats.to_csv(cfg.stats_file, index=False)

    print_user_overall_stats(df_stats)

# %%

if __name__ == "__main__":
    main()