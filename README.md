# chat_data_analysis

Some statistics of messages from the telegram chat, and bot with transformer, trained on this data.

Model was copied from https://github.com/bernhard-pfann/lad-gpt

**chat_analysis** folder contains templates for telegram chat history statistics. It is devided on messages and words statistics with frequancies of various indicators and visualizations. And also:

 * Script for telegram chat history converter from json to csv, but it doesn't save messages with all media types, except stickers, or without text and answers on these messages.  

 * If there are few chat histories for different periods, they can be united to one csv file.

 * Text embeddings generation with transformers model for futher clustering.

 * Applying different clustering algorithms and selecting the most valid. Hyperparameters tuning, printing messages and words, visualizing wordclouds for each cluster and scatterplot of embeddings's 2D projections with 4 variant of algorithms for dimensionality reduction (PCA, tSNE, PCA + tSNE and UMAP). Applying cuml for faster algorithms сonvergence (on GPU).

**chat_bot**

 * Transformer model with hyperparameters in config and training on random generated butches with learning rate schedule..
 
 * Asynchonous telegram chat bot for chatting with contacts (members) from chat. There is simple sqlalchemy database, user roles in dialogue, context saves and optional number of answers from bot (default is 5).
