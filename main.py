import sys, codecs
from MaterialPlanning import *


if __name__ == '__main__':
    if '-fe' in sys.argv:
        filter_stages = ['GT-{}'.format(i) for i in range(1,7)]
    else:
        filter_stages = []
    mp = MaterialPlanning(filter_stages=filter_stages)

    with codecs.open('required.txt', 'r', 'utf-8') as f:
        required_dct = {}
        for line in f.readlines():
            required_dct[line.split(' ')[0]] = int(line.split(' ')[1])

    with codecs.open('owned.txt', 'r', 'utf-8') as f:
        owned_dct = {}
        for line in f.readlines():
            owned_dct[line.split(' ')[0]] = int(line.split(' ')[1])

    mp.get_plan(required_dct, owned_dct, print_output='zh', outcome=True,
                gold_demand=True, exp_demand=True, store=True, output_lang='ja', server='CN')
