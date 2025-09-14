"""Public Goods game agent utilities and OpenAI integration.

This module provides:
- Static prompt text builders
- Message construction for the LLM
- History and transcript helpers
- A simple `Agent` class with no GUI dependencies
"""

import os
import pickle
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key from environment (if available)
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}")
    client = None

# Default OpenAI chat model
model = 'gpt-5-mini'

# TODO: Ensure this text mirrors info for game participants. It's close but does not
# perfectly match what subjects see.
def text_content():
    """Return the static text used in prompts.

    Returns:
        dict: Mapping of sections to prompt strings.
    """
    preamble = """You are a participant in a game."""
    rules1 = """- Matchings: The experiment consists of a series of rounds. In each round, you will be matched with the same group consisting of all 16 participants, i.e. you and 3 other people. The decisions that you and the other people make will determine the amounts earned by each of you.

- Investments: You begin each round with a number of "tokens," which may either be kept or invested. The 3 people you are matched with will decide how many of their tokens to keep, and how many to invest. You will be not be able to see the others' decisions until after your decision is submitted.

- Earnings: The payoff to you will equal:
    $0.20 for each token you keep,
    $0.10 for each token you invest, and
    $0.10 for each token invested by the 3 other people who you are matched with.

- Subsequent Matchings: You will be in the same group of 4 participants in all subsequent rounds, so the 3 other people you are matched with in one round are the same people that you are matched with in the next round."""
    rules2 = """Example: Suppose you have only two tokens for the round, and the earnings from tokens kept, invested, and invested by the others are $0.20, $0.10, and $0.10 respectively.

    If you keep both tokens, then your earnings will be: $0.20 x 2 = $0.40 from the tokens kept, plus $.1 times the number of tokens invested by the other people in your group.

    If you invest both tokens, then your earnings will be: $0.10 x 2 = $0.20 from the tokens invested, plus $.1 times the number of tokens invested by the other people in your group.

    If you keep one and invest one, then your earnings will be:
    $0.20 x 1 = $0.20 from the token kept, plus
    $0.10 x 1 = $0.10 for the token invested, plus
    $.1 times the number of tokens invested by the other people in your group. 

Note: In each of the 3 above cases, what you earn from the others' investments is: $0.00 if the others invest 0 tokens, $0.10 if the other people invest 1 token (in total) and keep the rest, $0.20 if the other people invest 2 tokens (in total), etc."""
    rules_summary = """Here are the rules for the game:
    
- There will be 15 rounds, and in all rounds you will begin with a new endowment of 5 tokens, each of which can either be kept or invested. The 3 other people in your group will also have 5 tokens.

- Everybody earns money in the same manner: $0.20 for each token kept, $0.10 for each token invested, and $0.10 for each token invested by the 3 other people.

- At the start of a new round, you will be given a new endowment of 5 tokens. You are free to change the numbers of tokens kept and invested from round to round.

- Note: You will be matched with the same people in all rounds."""
    rules_test1 = """In the following examples, please select the best answer.

Earnings reminder: $0.20 for each token you keep, $0.10 for each token you invest, and $0.10 for each token invested by others.

Define X = number of tokens invested, and Y=tokens invested by the other people in your group.
    
Suppose you invest X of your 5 tokens and the total number invested by the 3 other people is Y tokens.
a) Then you earn (5 - X)*$0.20 + X*$0.10.
b) Then your earnings will be at least as high as (5 - X)*$0.20 + X*$0.10. 

Please choose either a) or b)."""
    rules_test2 = """In the following example, please select the best answer.

Earnings reminder: $0.20 for each token you keep, $0.10 for each token you invest, and $0.10 for each token invested by others.    
    
Which is true?
a) You may divide your 5 tokens any way you wish in each round, keeping some and investing some, or you may keep or invest them all.
b) The more you invest in one round the less there is to invest in later rounds. 

Please choose either (a) or (b)."""
    rules_test_results1_correct = """Your answer, (b) is Correct, and how much more you earn depends on the others' investments."""
    rules_test_results1_incorrect = """Your answer, (a) is Incorrect; the calculations are OK, but you might also earn money from the others' investments."""    
    rules_test_results2_correct = """Your answer, (a) is Correct; the only requirement is that the number kept and the number invested sum to 5 in each round."""
    rules_test_results2_incorrect = """Your answer, (b) is Incorrect, you receive a new endowment of 5 tokens in each round; the only requirement is that the number kept and the number invested sum to 5."""
    rules_summary = """Rules for our game:

- You will be matched with the same group of 3 other people in each round. There will be a total of 15 rounds in this part of the experiment.

- All people will begin with 5 tokens which they may keep (and earn $0.20 each) or invest (and earn $0.10 each), knowing that they will also earn $0.10 for each token invested by other people in the group.

- You will begin each round with a new endowment of 5 tokens, irrespective of how many tokens you may have kept or invested in previous rounds.

- There will be a total of 15 rounds in this part of the experiment. Your earnings for each round will be calculated for you and added to previous earnings, as will be shown in the total earnings column of the record form that you will see next."""
    choice = """Choose a number of tokens to invest (between and including 0 and 5). Your earnings: $0.20 for each token you keep, $0.10 for each token you invest, and $0.10 for each token invested by the 3 other people. The groups of people will remain the same for all rounds in this part. Respond ONLY with a JSON object of the form: {\"tokens\": <integer between 0 and 5>}."""    
    return {"preamble" : preamble,
            "rules" : {"rules1": rules1, "rules2": rules2},
            "rules_summary": rules_summary,
            "rules_test": {1: rules_test1, 2: rules_test2},
            "rules_q_message": {1: {'a': rules_test_results1_incorrect,
                                    'b': rules_test_results1_correct},
                                2: {'a': rules_test_results2_correct,
                                    'b': rules_test_results2_incorrect}},
            "choice": choice}

def message_builder(mtype, game_round, history, question=None):
    """Construct a message for the LLM.

    Args:
        mtype (str): One of "rules_test", "rules_test_gui", or "invest".
        game_round (int): Zero-based round index.
        history (pd.DataFrame): History table; latest round should be first row.
        question (int | None): Rules test question number when applicable.

    Returns:
        str: The constructed message text.
    """
    
    text = text_content()

    if mtype == "rules_test":
        message = text['rules_summary'] + text['rules_test'][question]

    elif mtype == "rules_test_gui":
        message = text['rules_test'][question]
        
    elif mtype == "invest":
        if game_round == 0:
            round_report=''
        else:
            # Transform the history DataFrame to the expected format for round_report_maker
            if not history.empty and 'round' in history.columns:
                # Convert the game engine format to the expected format
                # For the latest round (most recent entry)
                latest_round = history.iloc[-1]  # Get the most recent round
                
                # Assume we're player 0 for simplicity - in a real game this would be passed as a parameter
                player_investment = latest_round['investments'][0] if len(latest_round['investments']) > 0 else 0
                tokens_kept = 5 - player_investment  # Assuming 5 total tokens
                total_invested = latest_round['total_invested']
                others_invested = total_invested - player_investment
                player_earnings = latest_round['payoffs'][0] if len(latest_round['payoffs']) > 0 else 0
                
                # Create a DataFrame in the expected format for round_report_maker
                transformed_df = pd.DataFrame({
                    'Round': [latest_round['round']],
                    'Number You Kept': [tokens_kept],
                    '$ from Tokens You Kept': [tokens_kept * 0.20],
                    'Number You Invested': [player_investment],
                    '$ from Tokens You Invested': [player_investment * 0.10],
                    'Invested by Others': [others_invested],
                    '$ from Others\' Inv.': [others_invested * 0.10],
                    'Your Earnings (Round)': [player_earnings],
                    'Your Total Earnings': [player_earnings]  # For simplicity, just use current round earnings
                })
                round_report = round_report_maker(transformed_df)
            else:
                round_report = ""
        
        # Use the actual history structure for markdown display
        if not history.empty:
            # Create a simplified view for display
            display_data = []
            for idx, row in history.iterrows():
                round_num = row['round']
                investments = row['investments']
                total_invested = row['total_invested']
                payoffs = row['payoffs']
                
                # Add a summary row for this round
                display_data.append({
                    'Round': round_num,
                    'Total_Invested': total_invested,
                    'Average_Investment': round(sum(investments) / len(investments), 2) if investments else 0
                })
            
            display_history = pd.DataFrame(display_data)
            history_md = display_history.to_markdown(index=False)
        else:
            history_md = "No previous rounds"
            
        message = text['rules_summary'] + round_report + "\n\nWe are starting round " + str(game_round + 1) +"\n" +\
            "\nResults so far: \n" +"```markdown\n" +  history_md +'```\n'+\
            text['choice']
    return message

def round_report_maker(history_df):
    """Build a natural language report for the previous round.

    The DataFrame should contain at least:
    ["Round", "Number You Kept", "$ from Tokens You Kept", "Number You Invested",
     "$ from Tokens You Invested", "Invested by Others", "$ from Others' Inv.",
     "Your Earnings (Round)", "Your Total Earnings"], with the latest round first.

    Args:
        history_df (pd.DataFrame): Round-by-round results; latest round first.

    Returns:
        str: Human-readable summary for the latest round.
    """
    # Check if history DataFrame is empty
    if len(history_df) == 0:
        return ""
    
    round_ = history_df.iloc[0]['Round']
    chat_keep = history_df.iloc[0]['Number You Kept'].astype(int)
    chat_invest = history_df.iloc[0]['Number You Invested'].astype(int)
    tot_other_grp_invest = history_df.iloc[0]['Invested by Others'].astype(int)
    cumulative_earnings = history_df.iloc[0]['Your Total Earnings']
    
    keep_income = '{:4.2f}'.format(round(chat_keep*.20, 2))
    inv_income = '{:4.2f}'.format(round(chat_invest*.10, 2))
    other_income = '{:4.2f}'.format(round(tot_other_grp_invest*.10, 2))
    total_income = '{:4.2f}'.format(round(chat_keep * .2 + chat_invest * .1 +\
                                         tot_other_grp_invest *.1, 2))
    
    round_report = "\n\nYour Results for Round " +str(round_)+"\n\n" +\
                   "Your Decision: "+ '{:d}'.format(chat_keep) + " kept, " + '{:d}'.format(chat_invest) + " invested\n\n" +\
                   '{:d}'.format(tot_other_grp_invest) + " tokens invested by the 3 other people in your group,\n" +\
                   "which yields earnings of:\n"+\
                   " " + '{:d}'.format(chat_keep) +" x $0.20 = $" +keep_income+"\n"+\
                   " " + '{:d}'.format(chat_invest) +" x $0.10 = $" +inv_income+"\n"+\
                   " " + '{:d}'.format(tot_other_grp_invest) +" x $0.10 = $" +other_income+"\n"+\
                   "for a total earnings of: \n"+\
                   "$"+keep_income + " + $" + inv_income + " + $" + other_income +\
                   "= $" + total_income +"\n\n" +\
                   "To summarize, your round " + str(round_) + " earnings= $" +\
                   total_income +"\n" +\
                   "Your Cumulative Earnings = $" + '{:.2f}'.format(round(cumulative_earnings, 2))
    return round_report 

def transcript_builder(message, transcript):
    """Append a message/response pair to a transcript.

    Args:
        message (str): Prompt sent to the LLM.
        transcript (list): Existing transcript list; pass empty list initially.

    Returns:
        str: The LLM's response.
    """
    response = gpt_discourse(message)
    transcript.extend([["Researcher: ", message]])
    transcript.extend([["ChatGPT: ", response]])
    return response

def build_history(history, game_id, user_id, game_round, invest_response, round_response):
    """Append a row to the game history DataFrame.

    Args:
        history (pd.DataFrame): Existing history (empty on first round).
        game_id (str): Game identifier.
        user_id (str | int): User identifier.
        game_round (int): Zero-based round index.
        invest_response (dict): Contains 'invested' key with tokens invested.
        round_response (dict): Contains 'earnings' key for the round.

    Returns:
        pd.DataFrame: Updated history DataFrame with the new row prepended.
    """
    invested = float(invest_response['invested'])
    kept = 5 - invested
    earnings = float(round_response['earnings'])

    # this is my earnings from other's investment
    earnings_other = round(earnings - .2 * kept - .1 * invested, 1) 
    others_invest = round(10 * (earnings - .2 * kept - .1 * invested), 1) 
    earnings_kept = .2 * kept
    earnings_invested = .1 * invested
    earnings_round = earnings_kept + earnings_invested + earnings_other
    if game_round > 0: 
        earnings_total = history['Your Earnings (Round)'].sum() + earnings_round
    else:
        earnings_total = earnings_round
        
    this_df = pd.DataFrame([[game_round+1, kept, earnings_kept, invested, earnings_invested, others_invest, earnings_other,
                             earnings_round, earnings_total]],
                           columns = ["Round", "Number You Kept", "$ from Tokens You Kept", "Number You Invested",
                                      "$ from Tokens You Invested", "Invested by Others", "$ from Others' Inv.",
                                      "Your Earnings (Round)", "Your Total Earnings"])   
    history = pd.concat([this_df, history], axis='rows')
    return history

def save_session(transcript, history, game_rounds, game_id, user_id):
    """Save transcript/history as pickle and Excel files.

    Note: Assumes results directory exists one level up from the project directory.

    Args:
        transcript (list): Conversation transcript.
        history (pd.DataFrame): Transactions history.
        game_rounds (int): Total number of rounds in the game.
        game_id (str): Assigned game identifier.
        user_id (str | int): Assigned user identifier.
    """

    fname_dict = '../results/dict_' + str(game_id) + '_' + str(game_rounds) + '_' + str(user_id) +'.pkl'
    fname_transcript = '../results/transcript_' + str(game_id) + '_' + str(game_rounds) + '_' + str(user_id) + '.xlsx'
    fname_history = '../results/history_' + str(game_id) + '_' + str(game_rounds) + '_' + str(user_id) + '.xlsx'
    
    #
    # prepare and save dictionary
    #
    results = {'transcript': transcript, 'history_df': history}
    f = open(fname_dict, "wb")
    # write the python object (dict) to pickle file
    pickle.dump(results, f)
    # close file
    f.close()

    #
    # Prepare and save dataframes as excel
    #

    # convert transcript to dataframe and save as excel
    transcript_df = pd.DataFrame(transcript, columns = ['role', 'message'])
    transcript_df['message'] = transcript_df['message'].str.replace("\n1", "\n").str.replace("\n2", "\n").\
        str.replace("\n3","\n").str.replace("\n4","\n")#.str.replace("\n","")
    
    with pd.ExcelWriter(fname_transcript, engine='xlsxwriter') as writer:
        workbook  = writer.book
        #writer.sheets={'Sheet1':workbook.add_worksheet()}
        #worksheet = writer.sheets['Sheet1']
        writer.book.formats[0].set_text_wrap()
        cell_format = workbook.add_format({'text_wrap': True})
        #worksheet.set_column('A:Z', cell_format=cell_format)
        transcript_df.to_excel(writer, index=False)
    
    # save history as a excel file
    history.to_excel(fname_history, index=False)
    return
 
def gpt_discourse(message, ai_model = model):
    """Call the OpenAI ChatCompletion API and return the text content.

    Args:
        message (str): Prompt to send to the LLM.
        ai_model (str): Model name.

    Returns:
        str: Aggregated response content from the API.
    """
    if client is None:
        # Return a mock response if client is not available
        return '{"tokens": 2}'
    
    response = client.chat.completions.create(
        model=ai_model,
        messages=[
                {"role": "system", "content": "Act like you are a player in a game. Respond ONLY with a JSON object of the form: {\"tokens\": <integer between 0 and 5>}"},
                {"role": "user", "content": message},
                ]
        )

    result = ''
    for choice in response.choices:
        result += choice.message.content

    return result

class Agent:
    """A minimal agent for the Public Goods game (no GUI).

    Responsibilities:
    - Build messages for the model (rules, investment prompt, round summaries)
    - Call the OpenAI API (or a drop-in provider if you swap gpt_discourse)
    - Track transcript and history
    - Save session artifacts
    """

    def __init__(self, model: str = 'gpt-4o-2024-08-06', game_id: str | None = None, user_id: int | None = None):
        self.model = model
        self.game_id = game_id
        self.user_id = user_id
        self.transcript: list[list[str]] = []
        self.history = pd.DataFrame(columns=[
            "Round", "Number You Kept", "$ from Tokens You Kept", "Number You Invested",
            "$ from Tokens You Invested", "Invested by Others", "$ from Others' Inv.",
            "Your Earnings (Round)", "Your Total Earnings"
        ])

    def ask(self, message: str) -> str:
        """Send a prompt to the LLM and record the exchange in the transcript.

        Args:
            message (str): Prompt to send.

        Returns:
            str: The LLM response text.
        """
        response = gpt_discourse(message, ai_model=self.model)
        self.transcript.extend([["Researcher: ", message]])
        self.transcript.extend([["ChatGPT: ", response]])
        return response

    def build_investment_prompt(self, game_round: int) -> str:
        """Return the investment decision prompt for the given round."""
        return message_builder("invest", game_round, self.history)

    def append_history(self, game_round: int, invested: float, earnings: float) -> None:
        """Append a round to the internal history.

        Mirrors :func:`build_history`, but operates on this agent's state.

        Args:
            game_round (int): Zero-based round index.
            invested (float): Number of tokens invested.
            earnings (float): Total earnings realized this round.
        """
        invested_f = float(invested)
        kept = 5 - invested_f
        earnings_f = float(earnings)

        earnings_other = round(earnings_f - .2 * kept - .1 * invested_f, 1)
        others_invest = round(10 * (earnings_f - .2 * kept - .1 * invested_f), 1)
        earnings_kept = .2 * kept
        earnings_invested = .1 * invested_f
        earnings_round = earnings_kept + earnings_invested + earnings_other
        if game_round > 0:
            earnings_total = self.history['Your Earnings (Round)'].sum() + earnings_round
        else:
            earnings_total = earnings_round

        this_df = pd.DataFrame([[game_round + 1, kept, earnings_kept, invested_f, earnings_invested,
                                  others_invest, earnings_other, earnings_round, earnings_total]],
                                columns=["Round", "Number You Kept", "$ from Tokens You Kept", "Number You Invested",
                                         "$ from Tokens You Invested", "Invested by Others", "$ from Others' Inv.",
                                         "Your Earnings (Round)", "Your Total Earnings"])
        self.history = pd.concat([this_df, self.history], axis='rows')

    def save(self, game_rounds: int, results_dir: str = '../results') -> None:
        """Persist transcript and history to disk.

        Args:
            game_rounds (int): Total number of rounds played.
            results_dir (str): Directory to write artifacts.
        Raises:
            ValueError: If `game_id` or `user_id` are not set.
        """
        if self.game_id is None or self.user_id is None:
            raise ValueError("game_id and user_id must be set to save the session.")

        os.makedirs(results_dir, exist_ok=True)
        fname_dict = os.path.join(results_dir, f'dict_{self.game_id}_{game_rounds}_{self.user_id}.pkl')
        fname_transcript = os.path.join(results_dir, f'transcript_{self.game_id}_{game_rounds}_{self.user_id}.xlsx')
        fname_history = os.path.join(results_dir, f'history_{self.game_id}_{game_rounds}_{self.user_id}.xlsx')

        results = {'transcript': self.transcript, 'history_df': self.history}
        with open(fname_dict, 'wb') as f:
            pickle.dump(results, f)

        transcript_df = pd.DataFrame(self.transcript, columns=['role', 'message'])
        transcript_df['message'] = transcript_df['message'].str.replace("\n1", "\n").str.replace("\n2", "\n").\
            str.replace("\n3", "\n").str.replace("\n4", "\n")

        with pd.ExcelWriter(fname_transcript, engine='xlsxwriter') as writer:
            workbook = writer.book
            writer.book.formats[0].set_text_wrap()
            _ = workbook.add_format({'text_wrap': True})
            transcript_df.to_excel(writer, index=False)

        self.history.to_excel(fname_history, index=False)

if __name__ == "__main__":
    # Test OpenAI API call
    test_message = "You are a participant in a game. You have 5 tokens. You may keep some and invest some. You earn $0.20 for each token you keep, $0.10 for each token you invest, and $0.10 for each token invested by the 3 other people in your group. Respond ONLY with a JSON object of the form: {\"tokens\": <integer between 0 and 5>}. You decide to invest 3 tokens. How many tokens do you keep?"
    print("Test message to LLM:")
    print(test_message)
    print("\nLLM response:")
    print(gpt_discourse(test_message))
