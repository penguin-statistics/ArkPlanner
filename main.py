import sys, codecs
from MaterialPlanning import MaterialPlanning

if __name__ == '__main__':
    
    mp = MaterialPlanning()
    
    with codecs.open('required.txt', 'r', 'utf-8') as f:
        required_dct = {}
        for line in f.readlines():
            required_dct[line.split(' ')[0]] = int(line.split(' ')[1])
            
    with codecs.open('owned.txt', 'r', 'utf-8') as f:
        owned_dct = {}
        for line in f.readlines():
            owned_dct [line.split(' ')[0]] = int(line.split(' ')[1])
            
    mp.get_plan(required_dct, owned_dct)