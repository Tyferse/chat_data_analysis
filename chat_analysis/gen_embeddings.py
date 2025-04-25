# import gc
import pandas as pd
import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel


device = torch.device('cuda')

def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

def get_detailed_instruct(task_description: str, query: str) -> str:
    return f'Instruct: {task_description}\nQuery: {query}'

# Each query must come with a one-sentence instruction that describes the task
task = 'Identify the main category of Telegram message from group chat'
queries = [
    get_detailed_instruct(task, 'What is the category or theme of message?')
]

documents = pd.read_csv('chat_analysis/chat_data/chat_history 2024-11-08 v3.csv')
documents = documents[~documents.text.str.startswith('File: <') | ~documents.text.str.endswith('>')].text.to_list()
input_texts = queries + documents

print(*documents[-1000:-990], sep='\n')
print(len(documents))
print()
input()

tokenizer = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-large-instruct')
model = AutoModel.from_pretrained('intfloat/multilingual-e5-large-instruct')
model.to(device)
# model.half()

# print([repr(m) for i, m in enumerate(input_texts[1:]) if not isinstance(m, str)])
# Tokenize the input texts
# batch_dict = (tokenizer(input_texts[:51], max_length=512, padding=True,
#                        truncation=True, return_tensors='pt')
#               .to(device))
#
# outputs = model(**batch_dict)
# embeds = average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
# embeds = F.normalize(embeds, p=2, dim=1)

step = 50
for i in range(1, len(input_texts), step):
    if i + step >= len(input_texts):
        blob = input_texts[i:]
    else:
        blob = input_texts[i: i + step]

    batch_dict = (tokenizer(queries + blob, max_length=512, padding=True,
                            truncation=True, return_tensors='pt')
                  .to(device))
    
    with torch.no_grad():
        outputs = model(**batch_dict)
        embeddings = average_pool(outputs.last_hidden_state, 
                                  batch_dict['attention_mask'])
    
    embeddings = F.normalize(embeddings[1:], p=2, dim=1)
    torch.save(embeddings, f'embeds/embeddings{i - 1:0>6}.pt')
    # embeds = torch.cat((embeds, embeddings), dim=0)
    
    del batch_dict
    del outputs
    del embeddings
    # gc.collect()
    torch.cuda.empty_cache()
    

# torch.save(embeds[1:], 'embeddings.pt')
# scores = (embeds[1:] @ embeds[1:].T) * 100
# print(scores.tolist())
# => [[91.92852783203125, 67.580322265625], [70.3814468383789, 92.1330795288086]]
