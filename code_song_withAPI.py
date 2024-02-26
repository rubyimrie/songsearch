import re
import time
from nltk.stem import PorterStemmer
import numpy as np
import xml.etree.ElementTree as ET
from string import digits
from flask import Flask, jsonify, request
import csv
import joblib
import cProfile

app = Flask(__name__)

# Constants ------------------------------------------------------------------------------------------------------------
# Note that all query and document files need to be stored in the cw1collection folder.
# Edit the resource folder name below if needed.

use_stemming = False
use_stopping = False
# Allow hyphen in a token or not (split).
use_hyphen = False

#resource_folder = r"data"
# Data file
csv_name = r"data/labeled_lyrics_cleaned.csv"
boolean_file_name = "queries.boolean.txt"
ranked_file_name = "queries.ranked.txt"

# Pre-processing -------------------------------------------------------------------------------------------------------
if use_stopping:
    with open(r"data\englishST.txt", encoding="utf-8") as stop_words_file:
        stop_words = stop_words_file.read().splitlines()


def stemmer(tokens):
    unique_tokens = list(set(tokens))
    unique_stems = {token: PorterStemmer().stem(token) for token in unique_tokens}

    return [unique_stems[token] for token in tokens]


def stopper(tokens):
    return [token for token in tokens if token not in stop_words]


def pre_processor(text):
    if use_hyphen:
        token_pattern = r"(\w+-\w+|\w+)"
    else:
        token_pattern = r"\w+"

    tokens = list()
    for token in re.findall(token_pattern, text):
        token = token.strip().lower()
        tokens.append(token)

    if use_stopping:
        tokens = stopper(tokens)

    if use_stemming:
        tokens = stemmer(tokens)

    return tokens


def inverted_index(text_dict):
    inverted_index_dict = dict()
    for tokens in text_dict.values():
        for token in tokens:
            inverted_index_dict[token] = list()

    for text_index, tokens in text_dict.items():
        for token_index, token in enumerate(tokens):
            inverted_index_dict[token].append((text_index, token_index))

    return inverted_index_dict


def csv_loader(file_name):
    
    with open(file_name) as csv_file:
    
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
    
        return_dict = dict()
        headers_dict = dict()
        others_dict = dict()
        
        for row in csv_reader:
            DocNo = row[0]
            Artist = row[1]
            Lyrics = row[2]
            Title = row[3]

            return_dict[DocNo]=  pre_processor(Title + Lyrics)
            headers_dict[DocNo] = Title
            others_dict[DocNo] = [Artist,Lyrics]

            print(DocNo)

    return return_dict, headers_dict,others_dict


# Boolean, Phrase, and Proximity search ---------------------------------------------------------------------------------------
# Note that the phrase search is implemented by utilising the proximity search function.
# Internally, a phrase search query is treated as a proximity search with the distance = 1 (no gap).
def search_helper(ii, adi, positive_terms, negative_terms):
    """Find the matching document indices"""
    document_indices = list()
    for positive_term in positive_terms:
        if positive_term in ii:
            document_indices.append(set([entry[0] for entry in ii[positive_term]]))

    for negative_term in negative_terms:
        if negative_term in ii:
            document_indices.append(set(adi).difference(set([entry[0] for entry in ii[negative_term]])))

    return document_indices


def check_next_terms(matching_ii, depth, document_index, term_position, max_distance):
    matching_entries = [(entry[0], entry[1]) for entry in matching_ii[depth] if (entry[0] == document_index) and (0 < entry[1] - term_position <= max_distance)]
    if depth + 1 == len(matching_ii):
        if matching_entries:
            return True
        else:
            return False
    else:
        if matching_entries:
            values = list()
            for cdi, ctp in matching_entries:
                values.append(check_next_terms(matching_ii, depth + 1, cdi, ctp, max_distance))
            return any(values)
        else:
            return False


def proximity_search(ii, terms, max_distance=1):
    """Only searches for the phrases where the terms exist in the given order.
    The distance between the terms in the phrases will not exceed the max_distance (1 means no gap)."""
    if max_distance < 1:
        raise ValueError("max_distance has to be bigger or equal to 1")

    matching_ii = [ii[term] for term in terms]
    matching_document_indices = list()

    for document_index, term_position in matching_ii[0]:
        if check_next_terms(matching_ii, 1, document_index, term_position, max_distance):
            matching_document_indices.append((document_index, term_position))

    return set([index[0] for index in matching_document_indices])


def search_parser(query, ii, data_dict):
    adi = data_dict.keys()

    if " AND " in query:
        terms = [term.strip() for term in query.split(" AND ")]
        result_sets = [search_parser(term, ii, data_dict) for term in terms]
        return set.intersection(*result_sets)

    elif " OR " in query:
        terms = [term.strip() for term in query.split(" OR ")]
        result_sets = [search_parser(term, ii, data_dict) for term in terms]
        return set.union(*result_sets)

    # Proximity search
    elif "#" in query:
        number_pattern = r"#\d+"
        match_span = re.match(number_pattern, query).span()
        distance = int(query[1:match_span[1]])
        terms = pre_processor(query[match_span[1] + 1: -1])
        return proximity_search(ii, terms, max_distance=distance)

    # Phrase search (proximity search with max_distance=1)
    elif '"' in query:
        terms = pre_processor(query[1:-1])
        return proximity_search(ii, terms, max_distance=1)

    elif "NOT" in query:
        term = pre_processor(query.strip()[4:])[0]
        result_sets = search_helper(ii, adi, [], [term])
        return result_sets[0]

    else:
        # Removing accidental spaces at the start or end
        # Query without explicit Boolean operator is treated as AND search
        query = query.strip()
        terms = pre_processor(query)
        result_sets = search_helper(ii, adi, terms, [])
        return result_sets[0]


# TFIDF -----------------------------------------------------------------------------------------------------------------------

def term_frequency_document(term, document_id,data_dict):
    
    return data_dict[document_id].count(term)
    #return len([entry for entry in term_entries if entry[0] == document_id])



def document_frequency(term, ii):
    term_entries = ii[term]
    return len(set([entry[0] for entry in term_entries]))

def term_weight(tf, df, idf,number_of_documents,avg_document_length,dl,ranking,k1,b):


    if ranking == "1":
        result = (1 + np.log10(tf)) * np.log10(number_of_documents / df)
        
    elif ranking == "2":
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (dl / avg_document_length))
        result = idf * (numerator / denominator)

    return result
    
def rank_documents(query_terms, ii, data_dict,ranking):
    
    k1 = 1.2
    b = 0.75

    profiler = cProfile.Profile()
    profiler.enable()

    number_of_documents = len(data_dict.keys())

    avg_document_length = sum(len(value) for key,value in data_dict.items()) / number_of_documents

    retrieval_scores = dict()

    df_scores = dict()
    for term in query_terms:
        df_scores[term] = document_frequency(term, ii)

    


    for term in query_terms:
                   
        for document_id in set([entry[0] for entry in ii[term]]):
            
            dl = len(data_dict[document_id])
            df = df_scores[term]
            idf = np.log10((number_of_documents - df + 0.5) / (df + 0.5))
            tf_score = term_frequency_document(term, document_id, data_dict)
            #print(tf_score)
            tw_score = term_weight(tf_score, df,idf, number_of_documents,avg_document_length,dl,ranking,k1,b)
            #print(tw_score)
            if document_id in retrieval_scores:
                #print(tf_score,df,idf,tw_score)
                retrieval_scores[document_id] += tw_score
            else:
                retrieval_scores[document_id] = tw_score

            

    profiler.disable()
    profiler.print_stats(sort='cumulative')

    #print(retrieval_scores.items())

    result = dict(sorted(retrieval_scores.items(), key=lambda item: item[1], reverse=True))

    return result


def rank_parser(query, ii, data_dict,ranking):
    
    query = query.strip()
    terms = [term for term in pre_processor(query)]

    return rank_documents(terms, ii, data_dict,ranking)


# File generation (processing queries) ----------------------------------------------------------------------------------------

start_time = time.time()
trec_dict, trec_headers, others_dict = csv_loader(csv_name)
finish_time = time.time()
print(f"{round(finish_time - start_time, 3)} seconds for data loading")

#joblib.dump(trec_dict,'trec_dict_nsms')
#joblib.dump(trec_headers,'trec_headers_nsms')
#joblib.dump(others_dict,'others_dict_nsns')


start_time = time.time()
trec_ii = inverted_index(trec_dict)
finish_time = time.time()
print(f"{round(finish_time - start_time, 3)} seconds for pre-processing")

"""
#print("Hi")
trec_dict = joblib.load('trec_dict')
trec_headers = joblib.load('trec_headers')
others_dict = joblib.load('others_dict')
"""

def get_ranked_queries(query,filter,page,ranking):

    Docs = rank_parser(query, trec_ii, trec_dict,ranking)

    result_list = list()

    for key,value in list(Docs.items())[((10*int(page))-10):((10*int(page)))]:
        result_list.append({'id':key,'title':trec_headers[key],'artist':others_dict[key][0],'score':value})

    
    return result_list, len(Docs)

def get_song(id):
    return {'id' : id, 'title':trec_headers[id],'artist':others_dict[id][0],'lyrics':others_dict[id][1]}

@app.route('/ranked', methods=['GET'])
def get_ranked():
 query = request.args.get('query')
 page = request.args.get('page')
 filter = request.args.get('filter')
 ranking = request.args.get('ranking') 
#Ranking = 1 for TFIDF , Ranking = 2 for BM25

 ranked = get_ranked_queries(query,filter,page,ranking)
 if ranked is None:
   return jsonify({ 'error': 'Does not exist'}), 404
 return jsonify(ranked)


@app.route('/song_by_id', methods=['GET'])
def song_by_id():
 id = request.args.get('id')
#Ranking = 1 for TFIDF , Ranking = 2 for BM25

 song_details = get_song(id)

 if song_details is None:
   return jsonify({ 'error': 'Does not exist'}), 404
 return song_details

if __name__ == '__main__':
   app.run(port=8000)

   