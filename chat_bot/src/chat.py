import json

import torch
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from v1.src.utils import custom_tokenizer, decode, encode, print_delayed
from v1.config import end_token, n_chats


def conversation() -> None:
    """
    Emulates chat conversations by sampling from a pre-trained GPTLanguageModel.

    This function loads a trained GPTLanguageModel along with vocabulary and 
    the list of special tokens. It then enters into a loop where the user specifies 
    a contact. Given this input, the model generates a sample response. The conversation 
    continues until the user inputs the end token.

    :example:

    >>> conversation()
    message >> Alice
    Model's Response: How are you?
    response >> end
    """
    with open("assets/output/vocab.txt", "r", encoding="utf-8") as f:
        vocab = json.loads(f.read())

    with open("assets/output/contacts.txt", "r", encoding="utf-8") as f:
        contacts = json.loads(f.read())   

    spec_tokens = contacts + [end_token]
    model = torch.load("assets/models/model05.pt").cuda()
    print(model)
    completer = WordCompleter(spec_tokens, ignore_case=True)
    
    uinput = prompt("message >> ", completer=completer, default="")  # completer=completer,
    output = torch.tensor([], dtype=torch.long, device='cuda')
    print()
    
    print_delayed(decode(encode(custom_tokenizer(uinput, spec_tokens),
                                vocab),
                         vocab).replace(' ' + end_token, ''))
    # uinput = random.choice(contacts)
    # enc_uin = decode(encode(custom_tokenizer(uinput, spec_tokens), vocab), vocab)

    while uinput != end_token:
        for _ in range(n_chats):
            add_tokens = custom_tokenizer(uinput, spec_tokens)
            add_context = encode(add_tokens, vocab).to('cuda')
            context = torch.cat((output, add_context)).unsqueeze(1).T
            
            n0 = len(output)
            output = model.generate(context, vocab).to('cuda')
            n1 = len(output)
            
            # print('{' + enc_uin + '} ' + str(len(enc_uin)))
            # print(decode(output[n0-n1:], vocab))
            print_delayed(decode(output[n0-n1:], vocab).split(end_token + ' ')[1])
            # uinput = random.choice(contacts)

        uinput = prompt("\nresponse >> ", completer=completer, default="")
        print()
        
        enc_uin = decode(encode(custom_tokenizer(uinput, spec_tokens),
                                vocab), vocab)
        print_delayed(enc_uin.replace(' ' + end_token, ''))
        # uinput = random.choice(contacts)
