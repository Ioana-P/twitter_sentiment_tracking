import pandas as pd
import numpy as np
import os

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import nltk
import string

from nltk.corpus import stopwords
from nltk import FreqDist, text
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer, PorterStemmer
import re
from nltk.collocations import BigramCollocationFinder, TrigramCollocationFinder
bigram_measures = nltk.collocations.BigramAssocMeasures()
trigram_measures = nltk.collocations.TrigramAssocMeasures()
import plotly_express as px

from sklearn.decomposition import LatentDirichletAllocation as LDA
from pyLDAvis import sklearn as sklearn_lda
import pickle 
import pyLDAvis

import html

# tokenizer = RegexpTokenizer(r'\b[A-Za-z0-9\-]{2,}\b')
# tokenizer = RegexpTokenizer(r"\s+", gaps=True)
# gen_stop_words = list(set(stopwords.words("english")))
# gen_stop_words += list(set(stopwords.words('french')))
# gen_stop_words += list(set(stopwords.words('german')))
# gen_stop_words += list(set(stopwords.words('spanish')))
# gen_stop_words += list(set(stopwords.words('russian')))

# gen_stop_words += list(string.punctuation)

from pathlib import Path

tokenizer = RegexpTokenizer(r'\b[A-Za-z0-9\-]{2,}\b')
default_tk = tokenizer

def generate_stop_words_by_language(lst_languages:list)->list:
    """Returns a list with stopwords from different languages, based on 
    nltk.corpus.stopwords. Also adds punctuations to the list of stopwords. 
    Result to be used in data cleaning/omitting terms

    Args:
        lst_languages (list): list of languages to use. If an incorrect language 
        is specified, then it will be omitted but an error will NOT be raised

    Returns:
        list: list of stopwords 
    """    

    gen_stop_words = []
    for lang in lst_languages:
        try:
            gen_stop_words += list(set(stopwords.words(lang)))

        except OSError: 
            print(f'Could not find stop words for {lang}. Omitting from list of stopwords')
            pass

    gen_stop_words += list(string.punctuation)

    return gen_stop_words

lst_languages = ['english', 'french', 'spanish', 'german', 'spanish', 'russian']
gen_stop_words = generate_stop_words_by_language(lst_languages)

gen_stop_words.extend(['amp', '&amp', '’', '&amp;'])

class LemmaTokenizer(object):
    def __init__(self, tokenizer = default_tk, stopwords = gen_stop_words):
        self.wnl = WordNetLemmatizer()
        self.tokenizer = tokenizer
        self.stopwords = stopwords
    def __call__(self, articles):
        return [self.wnl.lemmatize(token, ) for token in self.tokenizer.tokenize(articles) if token not in self.stopwords]
    
    def tokenize(self, articles):
        return [self.wnl.lemmatize(token) for token in self.tokenizer.tokenize(articles) if token not in self.stopwords]
    
default_tk = tokenizer

lemmy = LemmaTokenizer()

def apply_tfidf_and_return_table(tfidf:TfidfVectorizer, df:pd.DataFrame, text_col:str)->pd.DataFrame:
    """Fn takes in dataframe, with specified text column, an instantiated sklearn tfidf-vectorizer 
    and the dataframe with tf-idf data joined onto the original data

    Args:
        tfidf (TfidfVectorizer): sklearn tfidf vectorizer instance
        df (pd.DataFrame): dataframe
        text_col (str): text column we wish to tokenizer and analyse

    Returns:
        pd.DataFrame: dataframe where df is joined onto the tfidf_df
    """    
    tfidf_df = pd.DataFrame(tfidf.fit_transform(df[text_col]).toarray(), index = df.index, columns = tfidf.get_feature_names_out())

    full_df = df.join(tfidf_df)
    
    return full_df

def apply_tfidf_and_return_table_of_results(tfidf:TfidfVectorizer, df:pd.DataFrame, text_col:str)->pd.DataFrame:
    """Fn takes in dataframe, with specified text column, an instantiated sklearn tfidf-vectorizer 
    and outputs a sorted table of all the the terms with their respective tf-idf scores

    Args:
        tfidf (TfidfVectorizer): sklearn tfidf vectorizer instance
        df (pd.DataFrame): dataframe
        text_col (str): text column we wish to tokenizer and analyse

    Returns:
        pd.DataFrame: single-column table containing the terms as an index 
    """    
    tfidf_df = pd.DataFrame(tfidf.fit_transform(df[text_col]).toarray(), index = df.index, columns = tfidf.get_feature_names_out())

    # full_df = df.join(new_df)
    tfidf_sum = pd.DataFrame(tfidf_df.sum(), columns = ['tf_idf_score']).sort_values('tf_idf_score', ascending=False).reset_index().rename({'index':'terms'}, axis=1)
    
    return tfidf_sum

def apply_count_vect_and_return_data(cvt:CountVectorizer, df:pd.DataFrame, text_col:str)->pd.DataFrame:
    """Fn takes in dataframe, with specified text column, an instantiated sklearn count-vectorizer 
    and outputs the entire dataframe 

    Args:
        cvt (CountVectorizer): sklearn count vectorizer instance
        df (pd.DataFrame): dataframe
        text_col (str): text column we wish to tokenizer and analyse

    Returns:
        pd.DataFrame: single-column table containing the terms as an index 
    """    
    cvt_df = pd.DataFrame(cvt.fit_transform(df[text_col]).toarray(), index = df.index, columns = cvt.get_feature_names_out())
    
    return cvt_df

def apply_count_vect_and_return_table_of_results(cvt:CountVectorizer, df:pd.DataFrame, text_col:str)->pd.DataFrame:
    """Fn takes in dataframe, with specified text column, an instantiated sklearn count-vectorizer 
    and outputs a sorted table of all the the terms with their respective count vector scores

    Args:
        cvt (CountVectorizer): sklearn count vectorizer instance
        df (pd.DataFrame): dataframe
        text_col (str): text column we wish to tokenizer and analyse

    Returns:
        pd.DataFrame: single-column table containing the terms as an index 
    """    
    cvt_df = pd.DataFrame(cvt.fit_transform(df[text_col]).toarray(), index = df.index, columns = cvt.get_feature_names_out())

    cvt_sum = pd.DataFrame(cvt_df.sum(), columns = ['cvt_score']).sort_values('cvt_score', ascending=False).reset_index().rename({'index':'terms'}, axis=1)
    
    return cvt_sum

def apply_tfidf_and_return_grouped_table_of_results(tfidf:TfidfVectorizer, df:pd.DataFrame, text_col:str, group_col:str)->pd.DataFrame:
    """Fn takes in dataframe, with specified text column, an instantiated sklearn tfidf-vectorizer 
    and outputs a sorted table of all the the terms with their respective tf-idf scores 
    but aggregated by the level of the group col specified
    Args:
        tfidf (TfidfVectorizer): sklearn tfidf vectorizer instance
        df (pd.DataFrame): dataframe
        text_col (str): text column we wish to tokenizer and analyse
        group_col(str): column(s) specifying at which level we wish to aggregate, typically
        at the user level. 

    Returns:
        pd.DataFrame: single-column table containing the terms as an index 
    """    
    tfidf_df = pd.DataFrame(tfidf.fit_transform(df[text_col]).toarray(), index = df.index, columns = tfidf.get_feature_names_out())

    if isinstance(group_col, str):
        group_col = [group_col]

    full_df = df[group_col].join(tfidf_df)
    agg_df = get_tfidf_grouped_scores(df, text_col, group_col, 
                                     )

    agg_df_melt = agg_df.groupby(group_col).sum().reset_index().melt(id_vars=[group_col], 
                        var_name='term', value_name='tfidf_score').sort_values([ group_col, 'tfidf_score'], ascending=False)

    # tfidf_sum = pd.DataFrame(tfidf_df.sum(), columns = ['tf_idf_score']).sort_values('tf_idf_score', ascending=False).reset_index().rename({'index':'terms'}, axis=1)
    
    return agg_df_melt

def get_tfidf_grouped_scores(df:pd.DataFrame, text_col:str,group_col:str, ngram_range:tuple=(1,2), 
                    tokenizer=tokenizer.tokenize, stopwords:list=gen_stop_words, 
                    min_doc_frequency:float=0.005, max_doc_frequency:float=0.95,
                    smooth_idf:bool=False,
                    )->pd.DataFrame:


    tfidf = TfidfVectorizer(tokenizer=tokenizer, 
                            ngram_range=ngram_range, 
                            min_df=min_doc_frequency, 
                            max_df=max_doc_frequency,
                            smooth_idf=smooth_idf,
                            stop_words=stopwords)

    return apply_tfidf_and_return_grouped_table_of_results(tfidf, df, text_col, group_col)

def get_tfidf_scores(df:pd.DataFrame, text_col:str, ngram_range:tuple=(1,2), 
                    tokenizer=tokenizer.tokenize, stopwords:list=gen_stop_words, 
                    min_doc_frequency:float=0.005, max_doc_frequency:float=0.95,
                    smooth_idf:bool=False,
                    )->pd.DataFrame:


    tfidf = TfidfVectorizer(tokenizer=tokenizer, 
                            ngram_range=ngram_range, 
                            min_df=min_doc_frequency, 
                            max_df=max_doc_frequency,
                            smooth_idf=smooth_idf,
                            stop_words=stopwords)

    return apply_tfidf_and_return_table_of_results(tfidf, df, text_col)

def get_tfidf_df(df:pd.DataFrame, text_col:str, ngram_range:tuple=(1,2), 
                    tokenizer=tokenizer.tokenize, stopwords:list=gen_stop_words, 
                    min_doc_frequency:float=0.005, max_doc_frequency:float=0.95,
                    smooth_idf:bool=False,
                    id_col:str='tweet_id',
                    )->pd.DataFrame:


    tfidf = TfidfVectorizer(tokenizer=tokenizer, 
                            ngram_range=ngram_range, 
                            min_df=min_doc_frequency, 
                            max_df=max_doc_frequency,
                            smooth_idf=smooth_idf,
                            stop_words=stopwords)

    df.dropna(subset=[id_col], inplace=True)
    df.set_index(id_col, inplace=True)

    return apply_tfidf_and_return_table(tfidf, df, text_col)

def get_count_vectorized_df(df:pd.DataFrame, text_col:str, ngram_range:tuple=(1,2), 
                    tokenizer=lemmy, stopwords:list=gen_stop_words, 
                    min_doc_frequency:float=0.005, max_doc_frequency:float=0.95,
                    )->pd.DataFrame:


    count_vect = CountVectorizer(tokenizer=tokenizer, 
                            ngram_range=ngram_range, 
                            min_df=min_doc_frequency, 
                            max_df=max_doc_frequency,
                            stop_words=stopwords)

    return apply_count_vect_and_return_data(count_vect, df, text_col), count_vect


def calculate_and_plot_tfidf(input_dir:Path, output_dir:Path, top_n:int, text_col_raw :str, tokenizer=tokenizer.tokenize, 
                            stopwords:list=gen_stop_words, 
                            ngram_range:tuple=(1,2),
                        min_doc_frequency:float=0.005, max_doc_frequency:float=0.95,
                        smooth_idf:bool=False,):
    """Pulls up the csv file containing the tweet texts, cleans, tokenizes and vectorizes
    the text data and outputs (and returns) a plotly_express graph of the top_n terms by 
    tf-idf score.

    Args:
        input_dir (Path): directory containing tweet_text.csv
        output_dir (Path): directory where we want to output the results (normally the same as input_dir)
        top_n (int): how many terms do we want displayed
        text_col_raw (str): name of raw text column
        tokenizer (optional): Tokenizer for parsing and tokenizing text. Defaults to tokenizer.tokenize.
        stopwords (list, optional): Stopwords to be discarded. Please modify the generate_stop_words() function
        to add more stopwords from different languages. Punctuation is also includedd. Defaults to gen_stop_words.
        ngram_range (tuple, optional): N grams we want to look at. If we want just single tokens, then
        specify (1,1). Just bigrams : (2,2). Uni-grams, bigrams and trigrams : (1,3). Defaults to (1,2).
        min_doc_frequency (float, optional): The minimum fraction of tweets we want a term to appear in for it
        to be included in the final table. Defaults to 0.01 (i.e. 1% of tweets).
        max_doc_frequency (float, optional): The maximum fraction of tweets we want a term to appear in for it 
        to be included in the final table - this is useful in case we want to cut-off terms that appear almost
        everywhere (but remember that the tf-idf score in itself already does some of the work in reducing/eliminating
        those terms). Defaults to 1.0 (i.e. 100%).
        smooth_idf (bool, optional): Whether or not to add 1 to the denominator. This is only useful to have as 
        True when using the tf-idf vectorizer for new, unseen data (e.g. in the case of building a model).
        The canonical form of the tf-idf formula that most researchers expected, however, does *NOT* have a 1
        added to the denominator, so it's recommended for descriptive stats that we keep this set to default.
         Defaults to False.

    Returns:
        plot: plotly_express bar plot
    """    
    df = etl_tweet_text(input_dir)
    text_col_clean = f'clean_{text_col_raw}'
    tfidf_ = get_tfidf_scores(df, text_col_clean, ngram_range, tokenizer, stopwords, min_doc_frequency, max_doc_frequency, smooth_idf)
    return plot_tfidf_dist(tfidf_, output_dir, top_n)

def etl_tweet_text(input_dir:Path, text_col_raw:str='tweet_text')->pd.DataFrame:
    """Get csv file from input_dir tweet_text.csv, extract and clean features such as 
    URLs, mentions and hashtags into separate columns. Returns copy of data with
    raw text col and new clean version (same name as raw column with 'clean_' prefix)

    Args:
        input_dir (Path): directory containing tweet_text.csv
        output_dir (Path): directory where we want to output the results (normally the same as input_dir)
        text_col_raw (str): name of raw text column
        
    Returns:
        pd.DataFrame: clean dataframe
    """    
    fpath = input_dir/ Path('tweet_text.csv')
    df = pd.read_csv(str(fpath))
    files = os.listdir(input_dir)
    if 'tweet_text_addition.csv' in files:
        fpath = input_dir/ Path('tweet_text_addition.csv')
        extra = df = pd.read_csv(str(fpath))
        df = pd.concat([df, extra], axis=0)
        df.drop_duplicates(subset=['tweet_id'], inplace=True)

    df[text_col_raw] = df[text_col_raw].apply(lambda x: convert_html_entities_to_unicode(x))
    df = extract_and_remove_linkable_features(df, text_col_raw)
    return df

def extract_specific_str(x:str)->str:
    spec = {'&amp;':'&',
            '&quot;' : '\"', 
            '&lt;': '>', 
            '&gt;' : '<'
    }
    for sp, repl in spec.items():
        x = x.replace(sp, repl)
    return x

def convert_html_entities_to_unicode(text):
    """Converts HTML entities to unicode.  For example '&amp;' becomes '&'."""
    text = html.unescape(text)
    return text


def plot_tfidf_dist(data :pd.DataFrame, output_dir : Path,  top_n:int=20):

    # top terms, filter out
    df = data.copy()
    df = df.sort_values('tf_idf_score', ascending=False)
    df = df.iloc[:top_n]

    top_n = len(df)

    fig_follower = px.bar(df, x='tf_idf_score',y='terms',
                        # color= '#followers', color_continuous_scale= 'deep',
                labels={
                    "frequency" : "Frequency",
                    # "#followers" : "number of followers"
                    },
                        )
    fig_follower.update_traces(hovertemplate='tf-idf score: %{x}'+'<br>Term: %{y}')
    fig_follower.update_layout(title_text= f"Top {top_n} terms by TF-IDF* scores", title_x= 0.5,
                                # subtitle_text = f"*Term Frequency Inverse Document Frequency - a measure of the importance\nor relevance of the term"
                                )
    fig_follower.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    fig_follower.write_html(output_dir/ f"{top_n}_TF_IDF_frequency_plot.html")
    return fig_follower


def plot_term_freq_dist(data :pd.DataFrame, output_dir : Path, y_term:str='word', top_n:int=20):

    df = data.copy()
    # top terms, filter out
    df = df.sort_values('frequency', ascending=False)
    df = df.iloc[:top_n]

    fig_follower = px.bar(df, x='frequency',y=y_term,
                        # color= '#followers', color_continuous_scale= 'deep',
                labels={
                    "frequency" : "Frequency",
                    # "#followers" : "number of followers"
                    },
                        )
    fig_follower.update_traces(hovertemplate='Frequency: %{x}'+'<br>Term: %{y}')
    fig_follower.update_layout(title_text= f"{top_n} most commonly used {y_term}", title_x= 0.5)
    fig_follower.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    fig_follower.write_html(output_dir/ f"{top_n}_{y_term}_frequency_plot.html")


def tokenize_text(df:pd.DataFrame, text_col:str='clean_tweet_text', stopwords:list=gen_stop_words)->pd.DataFrame:
    df[f'{text_col}_tokens'] = df[text_col].apply(lambda x : [tok for tok in tokenizer.tokenize(x) if tok not in stopwords])

def get_lda_topic_data(input_dir:Path, text_col_raw:str='tweet_text', 
                        lemmatizer=lemmy,  **kwargs):

    
    #etl of data

    df = etl_tweet_text(input_dir)
    text_col_clean = f'clean_{text_col_raw}'

    # lemmatize the text col
    # lemm_col = f'lemmatized_{text_col_raw}'
    # df[lemm_col] = df[text_col_clean].apply(lambda x : lemmatize_text_data(x))

    # count vectorize data

    cvt_df, cvt_vectorizer = get_count_vectorized_df(df, text_col_clean, tokenizer = lemmatizer)

    #get lda object
    lda_model_ = inst_lda_object(**kwargs)
    # return cvt_df
    lda_df, lda_model_ = dt_to_lda(cvt_df, lda_model_)

    cvt_dt_mat = cvt_vectorizer.transform(df[text_col_clean])

    return lda_df, lda_model_, cvt_vectorizer, cvt_dt_mat

def etl_transform_visualize_lda_topics(input_dir:Path, text_col_raw:str='tweet_text', 
                        lemmatizer=lemmy,  **kwargs):
    """Fn extracts, transforms, loads, cleans, lemmatizes and visualises Latent Dirichlet
    Allocation (LDA) topics from a dataset, using a single text series as input. 
    To use, simply specify the directory containing the data, and it will 
    output a pyLDAvis dashboard in the same dir.

    Args:
        input_dir (Path): directory containing 'tweet_text.csv'. Also where the 
        output html file will be stored
        text_col_raw (str, optional): Name of text column in input file. Defaults to 'tweet_text'.
        lemmatizer (Lemmatizer class, optional): Lemmatizer used for processing. Defaults to lemmy.

    Returns:
        pyLDAviz display data
    """    
    lda_df, lda_model_, cvt_vectorizer, cvt_dt_mat = get_lda_topic_data(input_dir,
                                                            text_col_raw, 
                                                            lemmatizer, 
                                                            **kwargs)



    return generate_pyldaviz_dashboard(lda_model_, cvt_dt_mat, cvt_vectorizer, input_dir)


def print_topics(model, vectorizer, n_top_words, topics_to_include = None):
    """Takes in the sklearn decomposition model (LDA), our DocTerm 
    vectorizer (Count/TFiDF), nr of words we'd like to see and num of topics
    to visualise. 
    Prints out the top n topics/latent concepts plus their most 
    strongly associated terms"""
    words = vectorizer.get_feature_names()
    if topics_to_include==None:
        for topic_idx, topic in enumerate(model.components_):
            print(f"\nTopic #{topic_idx+1}:")
            print("; ".join([words[i]
                            for i in topic.argsort()[:-n_top_words - 1:-1]]))
    else:
        for topic_idx, topic in enumerate(model.components_):
            if topic_idx in topics_to_include:
                print(f"\nTopic ##{topic_idx+1}")
                print("; ".join([words[i]
                                for i in topic.argsort()[:-n_top_words - 1:-1]]))
    
def generate_pyldaviz_dashboard(lda_model_, cvt_sparse_dt, cvt_vectorizer, output_dir):
    """Fn generates and saves a pyLDAviz dashboard as an html file. 
    It also returns the display data so this can be used in other functions/
    in a jupyter notebook. To use this in a Jupyter nb, once you have 
    received display_data from this fn, run:

    ```
    import pyLDAvis
    
    pyLDAvis.enable_notebook()

    pyLDAvis.display(display_data)
    ```
    and this will render the dashboard in the notebook.

    Args:
        lda_model_ (sklearn.decomposition object): fitted LDA model
        cvt_sparse_dt (sparse matrix): sparse matrix resulting from applying an sklearn
        count vectorizer to a text series
        cvt_vectorizer (sklearn.feature_extraction.text.CountVectorizer object):
         the fitted count vectorizer object itself
        output_dir (pathlib.Path): directory to output to

    Returns:
        LDA viz display data 
    """
    
    display_data = pyLDAvis.sklearn.prepare(lda_model_, 
                                            cvt_sparse_dt, 
                                            cvt_vectorizer)

    output_path = str(output_dir / Path('LDA_viz_plot.html'))
    pyLDAvis.save_html(display_data, output_path)

    return display_data
    

def lemmatize_text_data(x:str, lemmatizer=lemmy)->pd.DataFrame:
    return ' '.join(lemmy(x))

def inst_lda_object(**kwargs):
    try:
        alpha_ = kwargs['alpha']
        eta_ = kwargs['eta']
        n_topics_ = kwargs['n_topics']

    except KeyError:
        n_topics_ = 10
        alpha_ = 1/n_topics_
        eta_ = 1/n_topics_

    return LDA(n_components=n_topics_,
             doc_topic_prior=alpha_, 
             topic_word_prior=eta_)

def dt_to_lda(data, lda_obj):
    """Takes document term matrix and returns (dataframe with LDirA topic data, 
    LDirA sklearn object). Specify number of non-DocTerm columns, fn will assume 
    all the Doc-Term columns are to the left of that. 
    Params:
    data - (Pandas DataFrame obj) dataframe containing text and other data
    your original dataframe, pre-vectorisation.
    lda_obj - (obj) pre-instantiated sklearn LatentDirichletAllocation object
    
    Returns: 
    new_df , vect_train_df (tuple) - dataframe with/out non-text columns on the left and document term matrix on the right"""
    
    
    lda_df = pd.DataFrame(lda_obj.fit_transform(data), index=data.index, columns=list(range(1,(lda_obj.n_components+1))))
    lda_df = lda_df.add_prefix('topic_')
    
    return lda_df, lda_obj

def preprocess_data(string):
    """Function that takes in any single continous string;
    Returns 1 continuous string
    A precautionary measure to try to remove any emails or websites that BS4 missed"""
    new_str = re.sub(r"\S+@\S+", '', string)
    new_str = re.sub(r"\S+.co\S+", '', new_str)
    new_str = re.sub(r"\S+.ed\S+", '', new_str)
    new_str_tok = tokenizer.tokenize(new_str)
    new_str_lemm = [lemmy.lemmatize(token) for token in new_str_tok]
    new_str_cont = ''
    for tok in new_str_lemm:
        new_str_cont += tok + ' '
    return new_str_cont

def print_top_trig_collocs(pd_series:pd.Series, tokenizer, frac_corpus = 0.1, stopwords = gen_stop_words):
    corpus = [tokenizer.tokenize(x) for x in pd_series.to_list()]
    finder = TrigramCollocationFinder.from_documents(corpus)
    finder.apply_freq_filter(round(frac_corpus*len(pd_series)))
    main_trigrams = finder.nbest(trigram_measures.likelihood_ratio, 100000)
    # for trigram in main_trigrams:
    #     if word in trigram:
    #         print(trigram)
        
    return main_trigrams

def print_top_bigr_collocs(pd_series:pd.Series, tokenizer, frac_corpus = 0.01, stopwords = gen_stop_words):
    corpus = [tokenizer.tokenize(x) for x in pd_series.to_list()]
    finder = BigramCollocationFinder.from_documents(corpus)
    finder.apply_freq_filter(round(frac_corpus*len(pd_series)))
    main_bigrams = finder.nbest(bigram_measures.likelihood_ratio, 100000)
    # for trigram in main_trigrams:
    #     if word in trigram:
    #         print(trigram)
        
    return main_bigrams

def get_term_freq_df(tok_series:pd.Series)->pd.DataFrame:
    """Takes in a pandas series with tokenized cells of text; adds them together
    then returns the frequency distribution dataframe for that corpus. 

    Args:
        tok_series (pd.Series): data series containing tokenized text

    Returns:
        pd.DataFrame: dataframe with corpus frequency distribution values
    """    

    corpus_lst = tok_series.to_list()
    joined_corpus = []
    for doc in corpus_lst:
        for token in doc:
            joined_corpus.append(token)

    fdist = FreqDist(joined_corpus)

    term_freqs = pd.DataFrame(fdist, index=[0]).T.reset_index()
    term_freqs.columns = ['term', 'frequency']
    term_freqs.sort_values('frequency', ascending=False, inplace=True)
        
    return term_freqs

#cleaning extract URLs, extract handles

def extract_linkable_features(df:pd.DataFrame, text_col:str='tweet_text')->pd.DataFrame:


    df['extracted_twitter_handles'] = df[text_col].apply(lambda x: re.findall('@[a-zA-Z0-9_]{1,16}', x) if isinstance(x,str) else x)

    url_regex_patt = '(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'
    df['extracted_URLs'] = df[text_col].apply(lambda x: re.findall(url_regex_patt ,x) if isinstance(x,str) else x)

    df['extracted_hashtags'] = df[text_col].apply(lambda x: re.findall('#[a-zA-Z0-9]{1,140}', x) if isinstance(x,str) else x)

    return df

def remove_linkable_features(df:pd.DataFrame, text_col:str='tweet_text')->pd.DataFrame:

    clean_col = f'clean_{text_col}'
    df[clean_col] = df[text_col].apply(lambda x: re.subn('@[a-zA-Z0-9_]{1,16}','', x)[0] if isinstance(x,str) else x)

    url_regex_patt = '(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'
    df[clean_col] = df[clean_col].apply(lambda x: re.subn(url_regex_patt ,'',x)[0] if isinstance(x,str) else x)

    df[clean_col] = df[clean_col].apply(lambda x: re.subn('#[a-zA-Z0-9]{1,140}','', x)[0] if isinstance(x,str) else x)

    # final bit of text cleaning
    punct_lst = list(string.punctuation)
    punct_lst.append('’')
    df[clean_col] = df[clean_col].apply(lambda x : clean_up_text(x, punct_lst))

    return df

def clean_up_text(x:str, punct_lst:list):
    if x!=x:
        return x
    
    
    x = x.replace('\n', '')
    for punct in punct_lst:
        x = x.replace(punct, '')
    x= x.strip()
    return x


def extract_and_remove_linkable_features(df:pd.DataFrame, text_col:str='tweet_text'):
    
    return remove_linkable_features(extract_linkable_features(df, text_col))


def main(input_dir:str, output_dir:str, 
        text_col_raw:str = 'tweet_text', num_topics:int=10,
        lemmatizer=lemmy, 
        **kwargs
        ):

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if kwargs is None:
        num_topics=10
        kwargs = {}
        

    #get and plot tfidf
    calculate_and_plot_tfidf(input_dir, output_dir, 20, text_col_raw, min_doc_frequency=0.005, max_doc_frequency=0.9)

    #term frequency as well



    # print most common terms from topics
    lda_df, lda_model_, cvt_vectorizer, cvt_dt_mat = get_lda_topic_data(input_dir,
                                                            text_col_raw, 
                                                            lemmatizer, 
                                                            **kwargs)
    print_topics(lda_model_, cvt_vectorizer, 20)


    # plot lda topics
    generate_pyldaviz_dashboard(lda_model_, cvt_dt_mat, cvt_vectorizer, input_dir)
    return

def evaluate_topic_model(lda_model) -> float:
    """Fn uses either the extrinsic coherence score (UCI) of the intrinsice
    UMass coherence measure to return a single value of coherence

    Args:
        lda_model (sklearn LDirA model): fitted LDA model
    Returns:
    (float): coherence score
    """

    pass


def fit_and_evaluate_multiple_topic_models(df:pd.DataFrame, text_col:str='clean_tweet_text', topic_num_start_end:tuple=(3,10),  alpha:float=0.1, eta:float=0.1,
                                        tokenizer = lemmy)->dict:
    """With given alpha and eta parameters, fn fits toic models onto the corpus for range of number of topics,
    evaluates coherence scores, and returns a dict with results, including the best fitted model, and the evaluation results. 

    Args:
        corpus (pd.DataFrame):  documents to be fitted to
        topic_num_start_end (tuple, optional): (Start number of topics, End number of topics). Defaults to (3,10).
        alpha (float, optional): _description_. Defaults to 0.1.
        eta (float, optional): _description_. Defaults to 0.1.

    Returns:
        dict: {'most_coherent_model': lda_model, 
            'coherence_scores': dict_coherence_scores, 
            
                }
    """



    cvt_df, cvt_vectorizer = get_count_vectorized_df(df, text_col,  tokenizer = lemmatizer)

    
    results_dict, model_dict, coherence_scores = {}, {}, {}
    start, end = topic_num_start_end
    for num_topics in range(start, end+1):
        #fit model

        #get lda object
        lda_model_ = inst_lda_object(**{'num_topics':num_topics, 'alpha':alpha, 'eta':eta})
        # return lda_df and lda_model
        _, lda_model_ = dt_to_lda(cvt_df, lda_model_)

        eval_score = evaluate_topic_model(lda_model_)

        coherence_scores[num_topics] = eval_score
        model_dict[num_topics] = lda_model_

    
    values_max = max(list(coherence_scores.values()))
    lst_topic_num = list(range(start,end))
    best_num_t_index = list(coherence_scores.values()).index(values_max)
    best_number_topics = lst_topic_num[best_num_t_index]

    results_dict['most_coherent_model'] = model_dict[best_num_t_index]
    results_dict['coherence_scores'] = coherence_scores

    return results_dict

def fit_pretrained_model_to_data():
    pass

def fit_pretrained_word_vector_model_to_data():
    pass

def fit_predict_pretrained_sentiment_model_to_data():
    pass



if __name__=='__main__':

    # start_user = sys.argv[0]
    # depth = int(sys.argv[1])

    main()