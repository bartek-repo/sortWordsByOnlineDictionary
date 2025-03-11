import multiprocessing
import queue
import requests
from bs4 import BeautifulSoup

path = r"B1 Vocabulary List – Part 1.txt"
dictionary_url = "https://www.dictionary.com/browse/"
dictionary = {}
list_sorted_words = list()

class WordDictionary:
    def __init__(self, wrd, type):
        self.word = wrd
        self.type = type


class WordContainer:
    def __init__(self, wrd, type):
        self.list_words = list()
        self.list_words.append(wrd)
        self.type = type


def updatedictionary(word2):
    if not (word2.type in dictionary):
        dictionary.update({word2.type: str(len(dictionary))})
        list_sorted_words.append(WordContainer(word2.word, word2.type))
    else:
        list_sorted_words[int(dictionary[word2.type])].list_words.append(word2.word)


def download_word_attr (word, kolejka, idx):
    # outpout structure [finded word, idx process]
    response2 = requests.get(dictionary_url+word)
    soup2 = BeautifulSoup(response2.content, 'html.parser')
    find_element2 = soup2.find('div', {'class' : 'S3nX0leWTGgcyInfTEbW'})
    if find_element2 is None:
        print(word)
        kolejka.put([WordDictionary(word,'-'), idx])
    else:
        print(word)
        kolejka.put([WordDictionary(word, find_element2.find('h2').text), idx] )


class WordParser:
    __listWords = ['']
    __counter = 0

    def __init__(self, path):
        self.path = path

    def setcounter(self, i):
        self.__counter = i

    def getnextword(self)->str | None:
        self.__counter += 1
        if self.__counter >= len(self.__listWords):
            return None
        return self.__listWords[self.__counter - 1]

    def getbackwardword(self)->str | None:
        if 0 < self.__counter <= len(self.__listWords):
            self.__counter -= 1
            return self.__listWords[self.__counter]
        return None

    def parse(self):
        file = open(self.path, mode='r')
        statemachine = 0

        for l in file.readlines():
            for c in l:
                if (64 < ord(c) < 91) or (96 < ord(c) < 123) or (ord(c) == 45):
                    if statemachine == 0:
                        self.__listWords[-1] += c
                    else:
                        statemachine = 0
                        self.__listWords.append(c)
                else:
                    statemachine = 1
        file.close()

if __name__ == '__main__':
    WP = WordParser(path)
    WP.parse()

    processes = list()
    que = multiprocessing.Queue()

    maxprocesses = 100
    processidx = 0
    wrd = WP.getnextword()
    while not(wrd is None):
        #get next word to analyze from list
        if len(processes) < maxprocesses:
            processidx = len(processes)
            processes.append(None)
        else:
            returnprocess = que.get()
            updatedictionary(returnprocess[0])
            processidx = returnprocess[1]
            processes[processidx].terminate()
        processes[processidx] = multiprocessing.Process(
            target=download_word_attr,
            args=(wrd, que, processidx,)
        )
        processes[processidx].start()
        wrd = WP.getnextword()
    try:
        while True:
            returnprocess = que.get(timeout=8)
            updatedictionary(returnprocess[0])
            processidx = returnprocess[1]
            processes[processidx].terminate()
    except queue.Empty:
        pass

    for typeswords in list_sorted_words:
        f2 = open(typeswords.type + '.txt', mode='x', encoding="UTF-8")
        for www in typeswords.list_words:
            f2.writelines(www +  '\n')
            print(www)
        f2.close()