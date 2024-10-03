import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

def get_recommendations(title, df_books):
    # Filling missing descriptions with empty strings
    df_books['description'] = df_books['description'].fillna('')

    # Creating TF-IDF matrix from book descriptions
    tfid = TfidfVectorizer(stop_words='english')
    tfid_matrix = tfid.fit_transform(df_books['description'])

    # Computing the cosine similarity matrix
    cosine_sim = linear_kernel(tfid_matrix, tfid_matrix)

    # Creating a Series to maps book titles to DataFrame indices
    indices = pd.Series(df_books.index, index=df_books['title']).drop_duplicates()

    # Finding the index of the book that matches the title...
    idx = indices[title]

    # Getting the pairwise similarity scores of all books with that book
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort the books based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the indices of the top 5 most similar books
    sim_scores = sim_scores[1:6]

    # Get the book indices
    sim_index = [i[0] for i in sim_scores]

    # Return the titles of the top 5 similar books
    return df_books['title'].iloc[sim_index]