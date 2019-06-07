import sys
from MaterialPlanning import MaterialPlanning

if __name__ == '__main__':
    
    mp = MaterialPlanning()
    
    with open('required.txt', 'r') as f:
        required_dct = {}
        for line in f.readlines():
            required_dct[line.split(' ')[0]] = int(line.split(' ')[1])
            
    with open('owned.txt', 'r') as f:
        owned_dct = {}
        for line in f.readlines():
            owned_dct [line.split(' ')[0]] = int(line.split(' ')[1])
            
    mp.get_plan(required_dct, owned_dct)