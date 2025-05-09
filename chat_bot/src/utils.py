import random
import re
import time
from datetime import datetime
from typing import List, Union

import torch
from nltk.tokenize import TweetTokenizer

from v1.config import (batch_size, block_size, eval_iters, unknown_token, end_token)


@torch.no_grad()
def estimate_loss(model, data):
    """
    Set evaluation mode and evaluate the loss on multiple batches.
    
    Args:
        model:  Pytorch model
        data (torch.tensor): Evaluation dataset.

    Returns:
        float: The average of collected losses.
    """
    model.eval()
    loss_list = torch.zeros(eval_iters).to('cuda')
    for i in range(eval_iters):
        X, Y = get_batch(data)
        logits, loss = model(X.to('cuda'), Y.to('cuda'))
        loss_list[i] = loss.item()

    loss_avg = loss_list.mean()    
    model.train() 
    return loss_avg


def get_batch(data):
    """Generate a small batch of data of inputs x and targets y"""
    ix = torch.randint(len(data) - block_size, (batch_size,),
                       device='cuda')
    x = torch.stack([data[i:i + block_size] for i in ix])
    y = torch.stack([data[i + 1:i + block_size + 1] for i in ix])
    return x, y


def encode(s: list, vocab: list) -> torch.tensor:
    """
    Encode a list of tokens into a tensor of integers, given a fixed vocabulary.
    When a token is not found in the vocabulary, the special unknown token is assigned.
    When the training set did not use that special token, a random token is assigned.
    
    Args:
        s (list[str]): List of tokens (strings).
        vocab (list[str]): Tokenizer vocabulary.

    Returns:
        torch.tensor: Encoded tokens sequence by vocab indices.
    """
    # rand_token = random.randint(0, len(vocab))
    map = {t: i for i, t in enumerate(vocab)}
    enc = [map.get(c, map.get(unknown_token, random.randint(0, len(vocab))))
           for c in s]
    # enc = [map.get(c, '') for c in s]
    enc = torch.tensor(enc, dtype=torch.long)
    return enc


def decode(tensor: torch.tensor, vocab: list) -> str:
    """Decode a tensor of integers, back into a string."""
    map_dec = {i: s for i, s in enumerate(vocab)}
    # map_dec = {i: s for s, i in map_enc.items()}
    dec = [map_dec[i.item()] for i in tensor]
    dec = " ".join(dec)
    return dec


# def custom_tokenizer(txt: str, spec_tokens: List[str], pattern: str="|\\d|\\w+|[^\\s]") -> List[str]:
#     """
#     pattern: str="|\d|\\w+|[^\\s]"
#     Tokenize text into words or characters using NLTK's RegexpTokenizer, considerung
#     given special combinations as single tokens.
#
#     :param txt: The corpus as a single string element.
#     :param spec_tokens: A list of special tokens (e.g. ending, out-of-vocab).
#     :param pattern: By default the corpus is tokenized on a word level (split by spaces).
#                     Numbers are considered single tokens.
#
#     >> note: The pattern for character level tokenization is '|.'
#     """
#     pattern = "|".join(spec_tokens) + pattern
#     tokenizer = RegexpTokenizer(pattern)
#     tokens = tokenizer.tokenize(txt)
#     return tokens


def custom_tokenizer(txt: list[tuple[str, str]] | str, spec_tokens=None):
    """
    Text tokenizer for format: "user: message_text", if token "user:" exists.
    If messages contains files, they are added without other text.
    
    Args:
        txt (list[tuple[str, str]] | str): The corpus as a single string element.
        spec_tokens (list[str] | None): A list of special tokens
            (e.g. ending, out-of-vocab).

    Returns:
        list[str]: List of word tokens.
    """
    tokenizer = TweetTokenizer()
    tokens = []
    if isinstance(txt, str):
        if any(txt.startswith(st) for st in spec_tokens):
            un, txt = txt.split(':', 1)
            tokens.append(un + ':')
        
        if re.search('file: <[\w\s()/.-]+>', txt):
            tokens.extend(re.findall('file: <[\w\s()/.-]+>', txt))
        else:
            tokens.extend(tokenizer.tokenize(txt))
            
        tokens.append(end_token)
    elif isinstance(txt, list):
        tokens = []
        for u, msg in txt:
            tokens.append(u + ':')
            if msg.startswith('file: <') and msg.endswith('>'):
                # print(msg)
                tokens.extend([msg, end_token])
                continue
            
            tokens.extend(tokenizer.tokenize(msg))
            tokens.append(end_token)
    
    return tokens


def get_vocab(text: Union[List[str], str]) -> List[str]:
    """Returns a sorted list of all unique tokens in the corpus."""
    return sorted(list(set(text)))


def current_time():
    return datetime.now().strftime("%H:%M:%S")


def print_delayed(s: str, delay: float = 0.05) -> None:
    """
    Prints each character of a string one by one on the same line with a delay.
    
    Args:
        s (str): The input string.
        delay (float): The time delay between each character in seconds.
    """
    for char in s:
        print(char, end="", flush=True)
        time.sleep(delay)

    print(end='\n\n')
