import json
from collections import Counter
from typing import List, Set, Tuple, Union

import pandas as pd
import torch

from v1.config import (end_token, unknown_token, min_count_tokens)
from .utils import custom_tokenizer, encode, get_vocab


def get_infrequent_tokens(tokens: Union[List[str], str], min_count: int) -> Set[str]:
    """
    Identify tokens that appear less than a minimum count.
    
    Args:
        tokens (list[str] | str): When it is the raw text in a string,
            frequencies are counted on character level.
            When it is the tokenized corpus as list, frequencies are counted
            on token level.
        min_count (int): Threshold of occurence to flag a token.

    Returns:
        Set[str]:  List of tokens that appear infrequently.
    """
    counts = Counter(tokens)
    infreq_tokens = {k for k, v in counts.items() if v <= min_count}
    return infreq_tokens


def mask_tokens(tokens: List[str], mask: Set[str]) -> List[str]:
    """
    Iterate through all tokens. Any token that is part of the set,
    is replaced by the unknown token.
    
    Args:
        tokens (list[str]): The tokenized corpus.
        mask (set(str)): Set of tokens that shall be masked in the corpus.

    Returns:
        list[str]: List of tokenized corpus after the masking operation.
    """
    return [unknown_token if t in mask else t for t in tokens]


def drop_chars(txt: str, drop: Set[str]) -> str:
    """Drop a list of characters from string"""
    return txt.translate(str.maketrans("", "", "".join(drop)))


def flatten_tuple(txt: List[Tuple[str, str]]) -> str:
    """Convert list of tuples into string separated by the end token"""
    return "".join([x0 + ":" + x1 + end_token for x0, x1 in txt])


def make_train_test() -> None:
    """
    Prepare training and testing datasets from chat messages.
    This function performs multiple tasks:
    
    1. Reads a corpus of WhatsApp chat messages from a text file
    2. Filters out infrequent characters from the corpus
    3. Splits the text based on regular expressions
    4. Tokenizes the text and encodes the tokens into integers
    5. Splits the encoded data into training and validation sets
    6. Saves the training and validation datasets, as well as the vocab and senders, to disk
    """
    # with open("assets/input/chat.txt", "r") as f:
    #     text = f.read()
    
    # remove very rare characters (mostly emojies)
    # infreq_chars = get_infrequent_tokens(text, min_count=min_count_chars)
    # text = drop_chars(text, infreq_chars)

    # split string into list of tuples (date, contact, message)
    # pattern = r'\[(.*?)\] (.*?): (.*)'
    # matches = re.findall(pattern, text)
    # text = [(x1, x2.lower()) for x0, x1, x2 in matches if not x2.startswith("\u200e")]
    
    chat_df = pd.read_csv('chat_analysis/chat_data/chat_history 2024-11-08 v3.csv')
    members_df = pd.read_csv('chat_analysis/chat_data/'
                             'chat_members 2024-11-08 v3.csv')
    text = chat_df[['from_id', 'text']].merge(
        members_df, how='left', left_on='from_id',right_on='user_id')
    text = [(un, tx.lower()) for un, tx in zip(text.username, text.text)]
    
    # print(text[:100], end='\n\n')

    # get list of all contacts, treated as special tokens
    # contacts = list(set([contact + ":" for contact, msg in text]))
    # spec_tokens = contacts + [end_token]
    
    # Save most active users with > 0.25% messages in chat
    message_count = (chat_df.groupby('from_id')[['id']].count()
                     .merge(members_df, left_on='from_id',
                            right_on='user_id')[['username', 'id']]
                     .sort_values('id', ascending=False).reset_index(drop=True))
    contacts = (message_count[message_count.id / message_count.id.sum() > 0.0025]
                .username.to_list())
    
    text = [(un, msg) for un, msg in text if un in contacts]
    contacts = [c + ':' for c in contacts]
    print(contacts)
    
    # convert list of tuples into list of tokens (word or character level)
    # text_flat = flatten_tuple(text)
    # tokens = custom_tokenizer(txt=text_flat, spec_tokens=spec_tokens)
    
    tokens = custom_tokenizer(text)
    
    # print(tokens[:100])
    
    # mask very rare tokens as unknown, to shrink the vocabulary
    infreq_tokens = get_infrequent_tokens(tokens, min_count=min_count_tokens)
    tokens = mask_tokens(tokens, infreq_tokens)

    # get vocabulary of corpus to file
    vocab = get_vocab(tokens)
    print(f"The corpus has {len(vocab)} unique tokens.")

    # encode tokens into a tensor of integers
    data = encode(tokens, vocab)

    # split up the data into train and validation set
    n = int(0.9 * len(data))
    train_data = data[:n]
    valid_data = data[n:]

    # export tensors
    torch.save(train_data, "assets/output/train2.pt")
    torch.save(valid_data, "assets/output/valid2.pt")

    with open("assets/output/vocab2.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(vocab, ensure_ascii=False))

    with open("assets/output/contacts2.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(contacts, ensure_ascii=False))

    print("SUCCESS")
