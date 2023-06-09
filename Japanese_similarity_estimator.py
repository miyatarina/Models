# -*- coding: utf-8 -*-
"""和文類似度推定.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ORvbIauCaoOP5LYbemH2WDPcBZhzi5cL
"""

# ライブラリのインストール
! pip install gensim

from google.colab import drive
drive.mount('/content/drive')

jtest = list()
with open("/content/drive/MyDrive/Vdata/Japanese/test.text.txt", "r") as f:
    for data in f:
        jtest.append(data.rstrip('\n'))

# 単語ベクトルのダウンロード
! curl -Lo chive-1.2-mc90_gensim.tar.gz https://sudachi.s3-ap-northeast-1.amazonaws.com/chive/chive-1.2-mc90_gensim.tar.gz
! tar -zxvf chive-1.2-mc90_gensim.tar.gz

# 単語ベクトルの読み込み
import gensim
w2v = gensim.models.KeyedVectors.load("./chive-1.2-mc90_gensim/chive-1.2-mc90.kv")

# sudachiインストール
! pip install sudachipy
! pip install sudachidict_core

# 前処理: 文 -> 単語リスト
from sudachipy import Dictionary
from sudachipy import SplitMode

tokenizer = Dictionary().create()

s1 = list()
s2 = list()
sn1 = list()
sn2 = list()
stopword1 = list()
stopword2 = list()
replaced1 = list()
replaced2 = list()
wordslist1 = list()
wordslist2 = list()

# 文1と文2に分割
def split_s(inlist, outlist1, outlist2):
    textnum = 0
    for sentence in inlist:
        textnum += 1
        s = sentence.split()
        outlist1.append(s[0])
        outlist2.append(s[1])
    return textnum

# 正規化する
def normarize(inlist, outlist):
    for sentence in inlist:
        normarized = list()
        for token in tokenizer.tokenize(sentence, SplitMode.A):
            normarized.append(token.normalized_form())
        outlist.append(normarized)

# 助詞などを抜いてみる
def stopword(inlist, outlist):
    stop_words = ["が", "は", "て", "ます", "を", "の", "。", "に", "へ", "と", "より", "、", "から", "で", "や", "です", "い", "た", "し", "お", "れ", "られ", "いる", "ある"]
    for sentence in inlist:
        stoplist = list()
        for word in sentence:
            if word not in stop_words:
                stoplist.append(word)
        outlist.append(stoplist)

# 数字置き換え
def replace_num(inlist, outlist):
    for sentence in inlist:
        replaced = list()
        for word in sentence:
            if word.isdigit():
                replaced.append("0")
            else:
                replaced.append(word)
        outlist.append(replaced)

textnum = split_s(jtest, s1, s2)

normarize(s1, sn1)
normarize(s2, sn2)

stopword(sn1, stopword1)
stopword(sn2, stopword2)

replace_num(stopword1, wordslist1)
replace_num(stopword2, wordslist2)

# wikiからの単語リストの作成
from collections import defaultdict

def wiki_tokenizer(filename):
    i = 0
    word2freq = defaultdict(int) # 出現回数を格納
    word2docnum = defaultdict(int) # 何文書に登場したかを格納
    with open(filename, "r") as f:
        for sentence in f:
            if i == 1000000:
                break
            s = tokenizer.tokenize(sentence, SplitMode.A)
            for token in s:
                word2freq[token.normalized_form()] += 1
            for token in set(s):
                word2docnum[token.normalized_form()] += 1
            i += 1
    return word2freq, word2docnum

word2freq, word2docnum = wiki_tokenizer("/content/drive/MyDrive/Vdata/Japanese/ja_wiki.sent.10m.txt")

# 確率の計算
def cal_p(word2freq):
    word2prob = defaultdict(float)
    total = sum(word2freq.values())
    for word in word2freq:
        word2prob[word] = word2freq[word] / total
    return word2prob

word2prob = cal_p(word2freq)

import numpy as np

# ベクトルの平均の算出
def avg_embedding(word2vec, word2prob):
    vector = np.zeros(word2vec.vector_size)
    for word in word2vec.vocab:
        if word in word2prob:
            vector += word2prob[word] * word2vec[word]
    return vector
    
avg_w2v = avg_embedding(w2v, word2prob)

# ベクトル化: 単語リスト -> ベクトル
vector1 = list()
vector2 = list()

def vectorize(words, w2v):
    vectors = list()
    for word in words:
        if word in w2v:
            vectors.append(w2v[word])
    return np.array(vectors).mean(axis=0)

for i in range(textnum):
    vector1.append(vectorize(wordslist1[i], w2v))
    vector2.append(vectorize(wordslist2[i], w2v))

# 中心化
# ベクトル化: 単語リスト -> ベクトル
vector1_centor = list()
vector2_centor = list()

def vectorize(words, w2v):
    vectors = list()
    for word in words:
        if word in w2v:
            vectors.append(w2v[word] - avg_w2v)
    return np.array(vectors).mean(axis=0)

for i in range(textnum):
    vector1_centor.append(vectorize(wordslist1[i], w2v))
    vector2_centor.append(vectorize(wordslist2[i], w2v))

# 類似度推定: 2つのベクトル -> コサイン類似度
import math

def cos(v1, v2):
    if math.isnan(np.linalg.norm(vector1[i]) * np.linalg.norm(vector2[i])):
        c = 0
    else:
        c = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return c

f = open("jaresult.txt", "w", encoding="UTF-8")

for i in range(textnum):
    ensamble = (0.2 * cos(vector1[i], vector2[i]) + 0.8 * cos(vector1_centor[i], vector2_centor[i]))
    print("%1.3f\t%s\t%s" % (ensamble, wordslist1[i], wordslist2[i]))
    f.write(str(ensamble)+"\n")

f.close()