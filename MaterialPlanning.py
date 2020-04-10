import numpy as np
import urllib.request, json, time, os, copy, sys
from scipy.optimize import linprog
from collections import defaultdict as ddict

global penguin_url, headers
penguin_url = 'https://penguin-stats.io/PenguinStats/api/'
headers = {'User-Agent':'ArkPlanner'}

Price = dict()
with open('price.txt', 'r', encoding='utf8') as f:
    for line in f.readlines():
        name, value = line.split()
        Price[name] = int(value)

class MaterialPlanning(object):
    def __init__(self,
                 filter_freq=200,
                 filter_stages=[],
                 url_stats='result/matrix?show_stage_details=true&show_item_details=true',
                 url_rules='formula',
                 path_stats='data/matrix.json',
                 path_rules='data/formula.json',
                 update=False,
                 banned_stages={},
#                 expValue=30,
                 ConvertionDR=0.18,
                 display_main_only=True):
        """
        Object initialization.
        Args:
            filter_freq: int or None. The lowest frequence that we consider.
                No filter will be applied if None.
            url_stats: string. url to the dropping rate stats data.
            url_rules: string. url to the composing rules data.
            path_stats: string. local path to the dropping rate stats data.
            path_rules: string. local path to the composing rules data.
        """
        try:
            material_probs, self.convertion_rules = load_data(path_stats, path_rules)
        except:
            print('exceptRequesting data from web resources (i.e., penguin-stats.io)...', end=' ')
            material_probs, self.convertion_rules = request_data(penguin_url+url_stats, penguin_url+url_rules, path_stats, path_rules)
            print('done.')
        if update:
            print('Requesting data from web resources (i.e., penguin-stats.io)...', end=' ')
            material_probs, self.convertion_rules = request_data(penguin_url+url_stats, penguin_url+url_rules, path_stats, path_rules)
            print('done.')

        self.exp_factor = 1

        self.material_probs = material_probs
        self.banned_stages = banned_stages
        self.display_main_only = display_main_only
        self.stage_times = ddict(int)

        filtered_probs = []
        needed_stage = []
        for dct in material_probs['matrix']:
            if dct['times'] > self.stage_times[dct['stage']['code']] or self.stage_times[dct['stage']['code']] == 0:
                self.stage_times[dct['stage']['code']] = dct['times']
            if dct['times']>=filter_freq and dct['stage']['code'] not in filter_stages:
                filtered_probs.append(dct)
            elif dct['stage']['code'] not in needed_stage:
                needed_stage.append(dct['stage']['code'])
        material_probs['matrix'] = filtered_probs
        self.ConvertionDR = ConvertionDR
        self._pre_processing(material_probs)
        self._set_lp_parameters()



    def _pre_processing(self, material_probs):
        """
        Compute costs, convertion rules and items probabilities from requested dictionaries.
        Args:
            material_probs: List of dictionaries recording the dropping info per stage per item.
                Keys of instances: ["itemID", "times", "itemName", "quantity", "apCost", "stageCode", "stageID"].
            convertion_rules: List of dictionaries recording the rules of composing.
                Keys of instances: ["id", "name", "level", "source", "madeof"].
        """
        # To count items and stages.
        additional_items = {'30135': u'D32钢', '30125': u'双极纳米片',
                            '30115': u'聚合剂', '00010':'经验', '4001':'龙门币',
                            '31014':'聚合凝胶', '31024':'炽合金块', '31013':'凝胶',
                            '31023':'炽合金', '3303':'技巧概要·卷3', '00030':'家具零件',
                            '3211': '先锋芯片', '3212': '先锋芯片组', '3213': '先锋双芯片',
                            '3221': '近卫芯片', '3222': '近卫芯片组', '3223': '近卫双芯片',
                            '3231': '重装芯片', '3232': '重装芯片组', '3233': '重装双芯片',
                            '3241': '狙击芯片', '3242': '狙击芯片组', '3243': '狙击双芯片',
                            '3251': '术师芯片', '3252': '术师芯片组', '3253': '术师双芯片',
                            '3261': '医疗芯片', '3262': '医疗芯片组', '3263': '医疗双芯片',
                            '3271': '辅助芯片', '3272': '辅助芯片组', '3273': '辅助双芯片',
                            '3281': '特种芯片', '3282': '特种芯片组', '3283': '特种双芯片',
                            '9001': '采购凭证', '32001': '芯片助剂'
                            }
        item_dct = {}
        stage_dct = {}
        self.stage_array = []
        for dct in material_probs['matrix']:
            item_dct[dct['item']['itemId']]=dct['item']['name']
            stage_dct[dct['stage']['code']]=dct['stage']['code']
        item_dct.update(additional_items)
        # To construct mapping from id to item names.
        item_array = []
        item_id_array = []
        for k,v in item_dct.items():
            try:
                float(k)
                item_array.append(v)
                item_id_array.append(k)
            except:
                pass

        self.item_array = np.array(item_array)
        self.item_id_array = np.array(item_id_array)
        self.item_dct_rv = {v:k for k,v in enumerate(item_array)}
        self.item_id_to_name = {self.item_id_array[k]:item for k,item in enumerate(item_array)}
        self.item_name_to_id = {item:self.item_id_array[k] for k,item in enumerate(item_array)}
        # To construct mapping from stage id to stage names and vice versa.
        for k,v in stage_dct.items():
            if v not in self.banned_stages:
                self.stage_array.append(v)

        self.stage_dct_rv = {v:k for k,v in enumerate(self.stage_array)}

        # To format dropping records into sparse probability matrix
        self.cost_lst = np.zeros(len(self.stage_array))

        self.update_stage()
        self.stage_array = np.array(self.stage_array)
        self.probs_matrix = np.zeros([len(self.stage_array), len(item_array)])

        for dct in material_probs['matrix']:
            try:
                self.cost_lst[self.stage_dct_rv[dct['stage']['code']]] = dct['stage']['apCost']
                self.probs_matrix[self.stage_dct_rv[dct['stage']['code']], self.item_dct_rv[dct['item']['name']]] = dct['quantity']/float(dct['times'])
            except:
                pass

        # 添加LS, CE, S4-6, S5-2等的掉落 及 默认龙门币掉落
        for k, stage in enumerate(self.stage_array):
            self.probs_matrix[k, self.item_dct_rv['龙门币']] = self.cost_lst[k]*12
        self.update_droprate()


        # To build equavalence relationship from convert_rule_dct.
        self.update_convertion()
        self.convertions_dct = {}
        convertion_matrix = []
        convertion_outc_matrix = []
        convertion_cost_lst = []
        for rule in self.convertion_rules:
            convertion = np.zeros(len(self.item_array))
            convertion[self.item_dct_rv[rule['name']]] = 1

            comp_dct = {comp['name']:comp['count'] for comp in rule['costs']}
            self.convertions_dct[rule['name']] = comp_dct
            for iname in comp_dct:
                convertion[self.item_dct_rv[iname]] -= comp_dct[iname]
            convertion[self.item_dct_rv['龙门币']] -= rule['goldCost']
            convertion_matrix.append(copy.deepcopy(convertion))

            outc_dct = {outc['name']:outc['count'] for outc in rule['extraOutcome']}
            outc_wgh = {outc['name']:outc['weight'] for outc in rule['extraOutcome']}
            weight_sum = float(rule['totalWeight'])
            for iname in outc_dct:
                convertion[self.item_dct_rv[iname]] += outc_dct[iname]*self.ConvertionDR*outc_wgh[iname]/weight_sum
            convertion_outc_matrix.append(convertion)
            convertion_cost_lst.append(0)

        convertions_group = (np.array(convertion_matrix), np.array(convertion_outc_matrix), convertion_cost_lst)
        self.convertion_matrix, self.convertion_outc_matrix, self.convertion_cost_lst = convertions_group

    def _set_lp_parameters(self):
        """
        Object initialization.
        Args:
            convertion_matrix: matrix of shape [n_rules, n_items].
                Each row represent a rule.
            convertion_cost_lst: list. Cost in equal value to the currency spent in convertion.
            probs_matrix: sparse matrix of shape [n_stages, n_items].
                Items per clear (probabilities) at each stage.
            cost_lst: list. Costs per clear at each stage.
        """
        assert len(self.probs_matrix)==len(self.cost_lst)
        assert len(self.convertion_matrix)==len(self.convertion_cost_lst)
        assert self.probs_matrix.shape[1]==self.convertion_matrix.shape[1]


    def update(self,
               filter_freq=200,
               filter_stages=[],
               url_stats='result/matrix?show_stage_details=true&show_item_details=true',
               url_rules='formula',
               path_stats='data/matrix.json',
               path_rules='data/formula.json'):
        """
        To update parameters when probabilities change or new items added.
        Args:
            url_stats: string. url to the dropping rate stats data.
            url_rules: string. url to the composing rules data.
            path_stats: string. local path to the dropping rate stats data.
            path_rules: string. local path to the composing rules data.
        """
        print('Requesting data from web resources (i.e., penguin-stats.io)...', end=' ')
        material_probs, self.convertion_rules = request_data(penguin_url+url_stats, penguin_url+url_rules, path_stats, path_rules)
        print('done.')

        if filter_freq:
            filtered_probs = []
            for dct in material_probs['matrix']:
                if dct['times']>=filter_freq and dct['stage']['code'] not in filter_stages:
                    filtered_probs.append(dct)
            material_probs['matrix'] = filtered_probs

        self._pre_processing(material_probs)
        self._set_lp_parameters()


    def _get_plan_no_prioties(self, demand_lst, outcome, gold_demand, exp_demand, convertion_dr, probs_matrix, convertion_matrix, convertion_outc_matrix, cost_lst, convertion_cost_lst):
        """
        To solve linear programming problem without prioties.
        Args:
            demand_lst: list of materials demand. Should include all items (zero if not required).
        Returns:
            strategy: list of required clear times for each stage.
            fun: estimated total cost.
        """
        if convertion_dr != 0.18:
            convertion_outc_matrix = (convertion_outc_matrix - convertion_matrix)/0.18*convertion_dr+convertion_matrix
        else:
            convertion_outc_matrix = convertion_outc_matrix
        A_ub = (np.vstack([probs_matrix, convertion_outc_matrix])
                if outcome else np.vstack([probs_matrix, convertion_matrix])).T
        farm_cost = (cost_lst)
        cost = (np.hstack([farm_cost, convertion_cost_lst]))
        assert np.any(farm_cost>=0)

        excp_factor = 1.0
        dual_factor = 1.0

        while excp_factor>1e-7:
            solution = linprog(c=cost,
                               A_ub=-A_ub,
                               b_ub=-np.array(demand_lst)*excp_factor,
                               method='interior-point')
            if solution.status != 4:
                break

            excp_factor /= 10.0

        while dual_factor>1e-7:
            dual_solution = linprog(c=-np.array(demand_lst)*excp_factor*dual_factor,
                                    A_ub=A_ub.T,
                                    b_ub=cost,
                                    method='interior-point')
            if solution.status != 4:
                break

            dual_factor /= 10.0


        return solution, dual_solution, excp_factor


    def get_plan(self, requirement_dct={}, deposited_dct={},
                 print_output=True, outcome=False, gold_demand=True, exp_demand=True, exclude=[], store=False, convertion_dr=0.18):
        """
        User API. Computing the material plan given requirements and owned items.
        Args:
                requirement_dct: dictionary. Contain only required items with their numbers.
                deposit_dct: dictionary. Contain only owned items with their numbers.
        """
        status_dct = {0: 'Optimization terminated successfully. ',
                      1: 'Iteration limit reached. ',
                      2: 'Problem appears to be infeasible. ',
                      3: 'Problem appears to be unbounded. ',
                      4: 'Numerical difficulties encountered.'}

        demand_lst = np.zeros(len(self.item_array))
        for k, v in requirement_dct.items():
            demand_lst[self.item_dct_rv[k]] = v
        if gold_demand:
            demand_lst[self.item_dct_rv['龙门币']] = 1e9
        if exp_demand:
            demand_lst[self.item_dct_rv['经验']] = 1e9
        for k, v in deposited_dct.items():
            demand_lst[self.item_dct_rv[k]] -= v

        if gold_demand == False and exp_demand == True:
            # 如果不需要龙门币 并 需要经验, 就删掉赤金到经验的转化
            convertion_matrix = self.convertion_matrix[:-1]
            convertion_outc_matrix = self.convertion_outc_matrix[:-1]
            convertion_cost_lst = self.convertion_cost_lst[:-1]
        else:
            convertion_matrix = self.convertion_matrix
            convertion_outc_matrix = self.convertion_outc_matrix
            convertion_cost_lst = self.convertion_cost_lst

        is_stage_alive = [False if stage in exclude else True for stage in self.stage_array]
        stage_array = self.stage_array[is_stage_alive]
        cost_lst = self.cost_lst[is_stage_alive]
        probs_matrix = self.probs_matrix[is_stage_alive]
        stage_dct_rv = {v:k for k,v in enumerate(stage_array)}

        solution, dual_solution, excp_factor = self._get_plan_no_prioties(demand_lst, outcome, gold_demand, exp_demand, convertion_dr, probs_matrix, convertion_matrix, convertion_outc_matrix, cost_lst, convertion_cost_lst)
        x, status = solution.x/excp_factor, solution.status
        y, slack = dual_solution.x, dual_solution.slack
        n_looting, n_convertion = x[:len(cost_lst)], x[len(cost_lst):]

        if status != 0:
            raise ValueError(status_dct[status])

        values = [{"level":'1', "items":[]},
                  {"level":'2', "items":[]},
                  {"level":'3', "items":[]},
                  {"level":'4', "items":[]},
                  {"level":'5', "items":[]}]

        item_values = dict()
        for i,item in enumerate(self.item_array):
            item_values[item] = y[i]

        for i,item in enumerate(self.item_array):
            v = item_values[item]
            if y[i]>=0 and '作战记录' not in item and item not in ['龙门币', '赤金', '经验']:
                if v>0.1:
                    item_value = {
                        "name": item,
                        "value": '%.2f'% v
                    }
                else:
                    item_value = {
                        "name": item,
                        "value": '%.5f'% v
                    }
                if not 0 < int(self.item_id_array[i][-1]) < 6:
                    continue
                values[int(self.item_id_array[i][-1])-1]['items'].append(item_value)

        for group in values:
            group["items"] = sorted(group["items"], key=lambda k: float(k['value']), reverse=True)

        cost = np.dot(x[:len(cost_lst)], cost_lst)
        gcost = -np.dot(x[len(cost_lst):], convertion_matrix[:, self.item_dct_rv['龙门币']])
        gold = np.dot(n_looting, probs_matrix[:, self.item_dct_rv['龙门币']])
        exp = np.dot(n_looting, probs_matrix[:, self.item_dct_rv['基础作战记录']])*200 +\
              np.dot(n_looting, probs_matrix[:, self.item_dct_rv['初级作战记录']])*400 +\
              np.dot(n_looting, probs_matrix[:, self.item_dct_rv['中级作战记录']])*1000 +\
              np.dot(n_looting, probs_matrix[:, self.item_dct_rv['经验']])

        stages = []
        for i, t in enumerate(n_looting):
            if t >= 0.1:
                stage_name = stage_array[i]
                if self.is_gold_or_exp(stage_name, cost_lst, item_values, self.item_array, probs_matrix, stage_dct_rv):
                    cost -= t*cost_lst[i]
                    gold -= t*probs_matrix[i, self.item_dct_rv['龙门币']]
                    exp -= t*(probs_matrix[i, self.item_dct_rv['基础作战记录']]*200 + 
                                probs_matrix[i, self.item_dct_rv['初级作战记录']]*400 + 
                                probs_matrix[i, self.item_dct_rv['中级作战记录']]*1000 +
                                probs_matrix[i, self.item_dct_rv['经验']])
                if stage_name[:2] in ['CE', 'LS'] and self.display_main_only:
                    continue
                target_items = np.where(probs_matrix[i]>0.02)[0]
                items = {self.item_array[idx]: float2str(probs_matrix[i, idx]*t)
                            for idx in target_items if self.item_array[idx] not in ['龙门币']}
                stage = {
                    "stage": stage_array[i],
                    "count": float2str(t),
                    "items": items
                }
                stages.append(stage)


        syntheses = []
        for i,t in enumerate(n_convertion):
            if t >= 0.1:
                target_item = self.item_array[np.argmax(convertion_matrix[i])]
                if target_item in ['经验', '龙门币', '家具零件']:
                    # 不显示经验和龙门币的转化
                    continue
                materials = {k: str(v*int(t+0.9)) for k,v in self.convertions_dct[target_item].items()}
                if '芯片' in target_item:
                    materials = {k: str(v*int(t+0.9)) for k,v in self.convertions_dct[target_item].items() if k != '经验'}
                synthesis = {
                    "target": target_item,
                    "count": str(int(t+0.9)),
                    "materials": materials
                }
                syntheses.append(synthesis)
            elif t >= 0.05:
                target_item = self.item_array[np.argmax(convertion_matrix[i])]
                if target_item in ['经验', '龙门币', '家具零件']:
                    # 不显示经验和龙门币的转化
                    continue
                materials = { k: '%.1f'%(v*t) for k,v in self.convertions_dct[target_item].items() }
                synthesis = {
                    "target": target_item,
                    "count": '%.1f'%t,
                    "materials": materials
                }
                syntheses.append(synthesis)

        res = {
            "cost": int(cost),
            "gcost": int(gcost),
            'gold': int(gold),
            'exp': int(exp),
            "stages": stages,
            "syntheses": syntheses,
            "values": list(reversed(values))
        }

        if store:
            green = {item['name']: '%.3f' % (float(item['value'])/Price[item['name']]) for item in values[2]['items']}
            yellow = {item['name']: '%.3f' % (float(item['value'])/Price[item['name']]) for item in values[3]['items']}

            res.update({'green': green,
                             'yellow': yellow})

        if print_output:
            print('Estimated total cost: %d, gold: %d, exp: %d.'%(res['cost'], res['gold'], res['exp']))
            print('Loot at following stages:')
            for stage in stages:
                display_lst = [k + '(%s) '%stage['items'][k] for k in stage['items']]
                print('Stage ' + stage['stage'] + '(%s times) ===> '%stage['count']
                + ', '.join(display_lst))

            print('\nSynthesize following items:')
            for synthesis in syntheses:
                display_lst = [k + '(%s) '%synthesis['materials'][k] for k in synthesis['materials']]
                print(synthesis['target'] + '(%s) <=== '%synthesis['count']
                + ', '.join(display_lst))

            print('\nItems Values:')
            for i, group in reversed(list(enumerate(values))):
                display_lst = ['%s:%s'%(item['name'], item['value']) for item in group['items']]
                print('Level %d items: '%(i+1))
                print(', '.join(display_lst))

        return res

    def is_gold_or_exp(self, stage_name, farm_cost, item_value, item_array, probs_matrix, stage_dct_rv, gate=0.1):
        return stage_name[:2] in ['LS', 'CE']

    def update_stage_processing(self, stage_name: str, cost: int):
        if stage_name not in self.stage_array:
            self.stage_array.append(stage_name)
            self.stage_dct_rv.update({stage_name: len(self.stage_array)-1})
            self.cost_lst = np.append(self.cost_lst, cost)
        else:
            self.cost_lst[self.stage_dct_rv[stage_name]] = cost

    def update_droprate(self):
        self.update_droprate_processing('S4-6', '龙门币', 3228)
        self.update_droprate_processing('S5-2', '龙门币', 2484)
        self.update_droprate_processing('S6-4', '龙门币', 2700, 'update')
        self.update_droprate_processing('SK-1', '家具零件', 1, 'update')
        self.update_droprate_processing('SK-2', '家具零件', 3, 'update')
        self.update_droprate_processing('SK-3', '家具零件', 5, 'update')
        self.update_droprate_processing('SK-4', '家具零件', 7, 'update')
        self.update_droprate_processing('SK-5', '家具零件', 10, 'update')
        self.update_droprate_processing('CE-1', '龙门币', 1700, 'update')
        self.update_droprate_processing('CE-2', '龙门币', 2800, 'update')
        self.update_droprate_processing('CE-3', '龙门币', 4100, 'update')
        self.update_droprate_processing('CE-4', '龙门币', 5700, 'update')
        self.update_droprate_processing('CE-5', '龙门币', 7500, 'update')
        self.update_droprate_processing('LS-1', '经验', 1600, 'update')
        self.update_droprate_processing('LS-2', '经验', 2800, 'update')
        self.update_droprate_processing('LS-3', '经验', 3900, 'update')
        self.update_droprate_processing('LS-4', '经验', 5900, 'update')
        self.update_droprate_processing('LS-5', '经验', 7400, 'update')

        self.update_droprate_processing('AP-1', '采购凭证', 3, 'update')
        self.update_droprate_processing('AP-2', '采购凭证', 6, 'update')
        self.update_droprate_processing('AP-3', '采购凭证', 10, 'update')
        self.update_droprate_processing('AP-4', '采购凭证', 15, 'update')
        self.update_droprate_processing('AP-5', '采购凭证', 21, 'update')

        self.update_droprate_processing('PR-A-1', '重装芯片', 1/2, 'update')
        self.update_droprate_processing('PR-A-1', '医疗芯片', 1/2, 'update')
        self.update_droprate_processing('PR-B-1', '狙击芯片', 1/2, 'update')
        self.update_droprate_processing('PR-B-1', '术师芯片', 1/2, 'update')
        self.update_droprate_processing('PR-C-1', '先锋芯片', 1/2, 'update')
        self.update_droprate_processing('PR-C-1', '辅助芯片', 1/2, 'update')
        self.update_droprate_processing('PR-D-1', '近卫芯片', 1/2, 'update')
        self.update_droprate_processing('PR-D-1', '特种芯片', 1/2, 'update')
        self.update_droprate_processing('PR-A-2', '重装芯片组', 1/2, 'update')
        self.update_droprate_processing('PR-A-2', '医疗芯片组', 1/2, 'update')
        self.update_droprate_processing('PR-B-2', '狙击芯片组', 1/2, 'update')
        self.update_droprate_processing('PR-B-2', '术师芯片组', 1/2, 'update')
        self.update_droprate_processing('PR-C-2', '先锋芯片组', 1/2, 'update')
        self.update_droprate_processing('PR-C-2', '辅助芯片组', 1/2, 'update')
        self.update_droprate_processing('PR-D-2', '近卫芯片组', 1/2, 'update')
        self.update_droprate_processing('PR-D-2', '特种芯片组', 1/2, 'update')

    def update_convertion_processing(self, target_item: tuple, cost: int, source_item: dict, extraOutcome: dict):
        '''
            target_item: (item, itemCount)
            cost: number of 龙门币
            source_item: {item: itemCount}
            extraOutcome: {outcome: {item: weight}, rate, totalWeight}
        '''
        toAppend = dict()
        Outcome, rate, totalWeight = extraOutcome
        toAppend['costs'] = [{'count':x[1]/target_item[1], 'id':self.item_dct_rv[x[0]], 'name':x[0]} for x in source_item.items()]
        toAppend['extraOutcome'] = [{'count': rate, 'id': self.item_dct_rv[x[0]], 'name': x[0], 'weight': x[1]/target_item[1]} for x in Outcome.items()]
        toAppend['goldCost'] = cost/target_item[1]
        toAppend['id'] = self.item_dct_rv[target_item[0]]
        toAppend['name'] = target_item[0]
        toAppend['totalWeight'] = totalWeight
        self.convertion_rules.append(toAppend)

    def update_convertion(self):
        # TODO: 考虑芯片/基建材料的不同副产物掉落
        self.update_convertion_processing(('经验', 200), 0, {'基础作战记录': 1}, ({}, 0, 1))
        self.update_convertion_processing(('经验', 400), 0, {'初级作战记录': 1}, ({}, 0, 1))
        self.update_convertion_processing(('经验', 1000), 0, {'中级作战记录': 1}, ({}, 0, 1))
        self.update_convertion_processing(('技巧概要·卷3', 1), 0, {'技巧概要·卷2': 3}, ({'技巧概要·卷3':1}, 1, 1))
        self.update_convertion_processing(('技巧概要·卷2', 1), 0, {'技巧概要·卷1': 3}, ({'技巧概要·卷2':1}, 1, 1))
#        self.update_convertion_processing(('经验', 2000), 0, {'高级作战记录': 1}, ({}, 0, 1))
        self.update_convertion_processing(('经验', 400), 0, {'赤金': 1}, ({}, 0, 1))
        self.update_convertion_processing(('家具零件', 4), 200, {'碳': 1}, ({'碳': 1}, 0.5, 1))
        self.update_convertion_processing(('家具零件', 8), 200, {'碳素': 1}, ({'碳素': 1}, 0.5, 1))
        self.update_convertion_processing(('家具零件', 12), 200, {'碳素组': 1}, ({'碳素组': 1}, 0.5, 1))
        self.update_convertion_processing(('重装芯片', 2), 0, {'医疗芯片': 3}, ({'重装芯片': 1, '医疗芯片':1,
                '狙击芯片': 1, '术师芯片': 1, '先锋芯片': 1, '辅助芯片': 1, '近卫芯片': 1, '特种芯片': 1}, 1, 8))
        self.update_convertion_processing(('医疗芯片', 2), 0, {'重装芯片': 3}, ({'重装芯片': 1, '医疗芯片':1,
                '狙击芯片': 1, '术师芯片': 1, '先锋芯片': 1, '辅助芯片': 1, '近卫芯片': 1, '特种芯片': 1}, 1, 8))
        self.update_convertion_processing(('狙击芯片', 2), 0, {'术师芯片': 3}, ({'重装芯片': 1, '医疗芯片':1,
                '狙击芯片': 1, '术师芯片': 1, '先锋芯片': 1, '辅助芯片': 1, '近卫芯片': 1, '特种芯片': 1}, 1, 8))
        self.update_convertion_processing(('术师芯片', 2), 0, {'狙击芯片': 3}, ({'重装芯片': 1, '医疗芯片':1,
                '狙击芯片': 1, '术师芯片': 1, '先锋芯片': 1, '辅助芯片': 1, '近卫芯片': 1, '特种芯片': 1}, 1, 8))
        self.update_convertion_processing(('先锋芯片', 2), 0, {'辅助芯片': 3}, ({'重装芯片': 1, '医疗芯片':1,
                '狙击芯片': 1, '术师芯片': 1, '先锋芯片': 1, '辅助芯片': 1, '近卫芯片': 1, '特种芯片': 1}, 1, 8))
        self.update_convertion_processing(('辅助芯片', 2), 0, {'先锋芯片': 3}, ({'重装芯片': 1, '医疗芯片':1,
                '狙击芯片': 1, '术师芯片': 1, '先锋芯片': 1, '辅助芯片': 1, '近卫芯片': 1, '特种芯片': 1}, 1, 8))
        self.update_convertion_processing(('特种芯片', 2), 0, {'近卫芯片': 3}, ({'重装芯片': 1, '医疗芯片':1,
                '狙击芯片': 1, '术师芯片': 1, '先锋芯片': 1, '辅助芯片': 1, '近卫芯片': 1, '特种芯片': 1}, 1, 8))
        self.update_convertion_processing(('近卫芯片', 2), 0, {'特种芯片': 3}, ({'重装芯片': 1, '医疗芯片':1,
                '狙击芯片': 1, '术师芯片': 1, '先锋芯片': 1, '辅助芯片': 1, '近卫芯片': 1, '特种芯片': 1}, 1, 8))
        self.update_convertion_processing(('重装芯片组', 2), 0, {'医疗芯片组': 3}, ({'重装芯片组': 1, '医疗芯片组':1,
                '狙击芯片组': 1, '术师芯片组': 1, '先锋芯片组': 1, '辅助芯片组': 1, '近卫芯片组': 1, '特种芯片组': 1}, 1, 8))
        self.update_convertion_processing(('医疗芯片组', 2), 0, {'重装芯片组': 3}, ({'重装芯片组': 1, '医疗芯片组':1,
                '狙击芯片组': 1, '术师芯片组': 1, '先锋芯片组': 1, '辅助芯片组': 1, '近卫芯片组': 1, '特种芯片组': 1}, 1, 8))
        self.update_convertion_processing(('狙击芯片组', 2), 0, {'术师芯片组': 3}, ({'重装芯片组': 1, '医疗芯片组':1,
                '狙击芯片组': 1, '术师芯片组': 1, '先锋芯片组': 1, '辅助芯片组': 1, '近卫芯片组': 1, '特种芯片组': 1}, 1, 8))
        self.update_convertion_processing(('术师芯片组', 2), 0, {'狙击芯片组': 3}, ({'重装芯片组': 1, '医疗芯片组':1,
                '狙击芯片组': 1, '术师芯片组': 1, '先锋芯片组': 1, '辅助芯片组': 1, '近卫芯片组': 1, '特种芯片组': 1}, 1, 8))
        self.update_convertion_processing(('先锋芯片组', 2), 0, {'辅助芯片组': 3}, ({'重装芯片组': 1, '医疗芯片组':1,
                '狙击芯片组': 1, '术师芯片组': 1, '先锋芯片组': 1, '辅助芯片组': 1, '近卫芯片组': 1, '特种芯片组': 1}, 1, 8))
        self.update_convertion_processing(('辅助芯片组', 2), 0, {'先锋芯片组': 3}, ({'重装芯片组': 1, '医疗芯片组':1,
                '狙击芯片组': 1, '术师芯片组': 1, '先锋芯片组': 1, '辅助芯片组': 1, '近卫芯片组': 1, '特种芯片组': 1}, 1, 8))
        self.update_convertion_processing(('特种芯片组', 2), 0, {'近卫芯片组': 3}, ({'重装芯片组': 1, '医疗芯片组':1,
                '狙击芯片组': 1, '术师芯片组': 1, '先锋芯片组': 1, '辅助芯片组': 1, '近卫芯片组': 1, '特种芯片组': 1}, 1, 8))
        self.update_convertion_processing(('近卫芯片组', 2), 0, {'特种芯片组': 3}, ({'重装芯片组': 1, '医疗芯片组':1,
                '狙击芯片组': 1, '术师芯片组': 1, '先锋芯片组': 1, '辅助芯片组': 1, '近卫芯片组': 1, '特种芯片组': 1}, 1, 8))
        self.update_convertion_processing(('芯片助剂', 1), 0, {'采购凭证': 90}, ({}, 0, 1))
        self.update_convertion_processing(('近卫双芯片', 1), 0, {'近卫芯片组': 2, '经验': 1000/3, '芯片助剂': 1}, ({}, 0, 1))
        self.update_convertion_processing(('重装双芯片', 1), 0, {'重装芯片组': 2, '经验': 1000/3, '芯片助剂': 1}, ({}, 0, 1))
        self.update_convertion_processing(('医疗双芯片', 1), 0, {'医疗芯片组': 2, '经验': 1000/3, '芯片助剂': 1}, ({}, 0, 1))
        self.update_convertion_processing(('特种双芯片', 1), 0, {'特种芯片组': 2, '经验': 1000/3, '芯片助剂': 1}, ({}, 0, 1))
        self.update_convertion_processing(('辅助双芯片', 1), 0, {'辅助芯片组': 2, '经验': 1000/3, '芯片助剂': 1}, ({}, 0, 1))
        self.update_convertion_processing(('术师双芯片', 1), 0, {'术师芯片组': 2, '经验': 1000/3, '芯片助剂': 1}, ({}, 0, 1))
        self.update_convertion_processing(('狙击双芯片', 1), 0, {'狙击芯片组': 2, '经验': 1000/3, '芯片助剂': 1}, ({}, 0, 1))
        self.update_convertion_processing(('先锋双芯片', 1), 0, {'先锋芯片组': 2, '经验': 1000/3, '芯片助剂': 1}, ({}, 0, 1))

        # 这里一定保证这一条在最后!
        self.update_convertion_processing(('经验', 400), 0, {'赤金': 1}, ({}, 0, 1))

    def update_stage(self):
        self.update_stage_processing('CE-1', 10)
        self.update_stage_processing('CE-2', 15)
        self.update_stage_processing('CE-3', 20)
        self.update_stage_processing('CE-4', 25)
        self.update_stage_processing('CE-5', 30)
        self.update_stage_processing('PR-A-1', 18)
        self.update_stage_processing('PR-A-2', 36)
        self.update_stage_processing('PR-B-1', 18)
        self.update_stage_processing('PR-B-2', 36)
        self.update_stage_processing('PR-C-1', 18)
        self.update_stage_processing('PR-C-2', 36)
        self.update_stage_processing('PR-D-1', 18)
        self.update_stage_processing('PR-D-2', 36)
        self.update_stage_processing('CE-1', 10)
        self.update_stage_processing('CE-2', 15)
        self.update_stage_processing('CE-3', 20)
        self.update_stage_processing('CE-4', 25)
        self.update_stage_processing('CE-5', 30)
        self.update_stage_processing('LS-1', 10)
        self.update_stage_processing('LS-2', 15)
        self.update_stage_processing('LS-3', 20)
        self.update_stage_processing('LS-4', 25)
        self.update_stage_processing('LS-5', 30)
        self.update_stage_processing('AP-1', 10)
        self.update_stage_processing('AP-2', 15)
        self.update_stage_processing('AP-3', 20)
        self.update_stage_processing('AP-4', 25)
        self.update_stage_processing('AP-5', 30)

    def update_droprate_processing(self, stage, item, droprate, mode='add'):
        if stage not in self.stage_array:
            return
        if item not in self.item_array:
            return
        stageid = self.stage_dct_rv[stage]
        itemid = self.item_dct_rv[item]
        if mode == 'add':
            self.probs_matrix[stageid][itemid] += droprate
        elif mode == 'update':
            self.probs_matrix[stageid][itemid] = droprate



def Cartesian_sum(arr1, arr2):
    arr_r = []
    for arr in arr1:
        arr_r.append(arr+arr2)
    arr_r = np.vstack(arr_r)
    return arr_r

def float2str(x, offset=0.5):

    if x < 1.0:
        out = '%.1f'%x
    else:
        out = '%d'%(int(x+offset))
    return out

def request_data(url_stats, url_rules, save_path_stats, save_path_rules):
    """
    To request probability and convertion rules from web resources and store at local.
    Args:
        url_stats: string. url to the dropping rate stats data.
        url_rules: string. url to the composing rules data.
        save_path_stats: string. local path for storing the stats data.
        save_path_rules: string. local path for storing the composing rules data.
    Returns:
        material_probs: dictionary. Content of the stats json file.
        convertion_rules: dictionary. Content of the rules json file.
    """
    try:
        os.mkdir(os.path.dirname(save_path_stats))
    except:
        pass
    try:
        os.mkdir(os.path.dirname(save_path_rules))
    except:
        pass

    req = urllib.request.Request(url_stats, None, headers)
    with urllib.request.urlopen(req) as response:
        material_probs = json.loads(response.read().decode())
        with open(save_path_stats, 'w') as outfile:
            json.dump(material_probs, outfile)

    req = urllib.request.Request(url_rules, None, headers)
    with urllib.request.urlopen(req) as response:
        response = urllib.request.urlopen(req)
        convertion_rules = json.loads(response.read().decode())
        with open(save_path_rules, 'w') as outfile:
            json.dump(convertion_rules, outfile)

    return material_probs, convertion_rules

def load_data(path_stats, path_rules):
    """
    To load stats and rules data from local directories.
    Args:
        path_stats: string. local path to the stats data.
        path_rules: string. local path to the composing rules data.
    Returns:
        material_probs: dictionary. Content of the stats json file.
        convertion_rules: dictionary. Content of the rules json file.
    """
    with open(path_stats) as json_file:
        material_probs  = json.load(json_file)
    with open(path_rules) as json_file:
        convertion_rules  = json.load(json_file)

    return material_probs, convertion_rules
