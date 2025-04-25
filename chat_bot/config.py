# model hyperparameters
block_size = 128  # 32 / context length
embed_size = 256  # 256
dropout = 0.08  # 0.2
n_heads = 6  # 6
n_layer = 8  # 6
eval_iters = 42
batch_size = 32  # 32

# learning hyperparameters
learn_rate = 0.002  # 3e-4
# max_iters = 4000 # 5000
eval_interval = 500  # 500
epochs = 12

# preprocess
min_count_chars = 1
min_count_tokens = 1

# encoding
end_token = "<END>"
unknown_token = "<UNK>"
n_chats = 5
