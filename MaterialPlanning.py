import numpy as np
import urllib.request, json, time, os
from scipy.optimize import linprog

class MaterialPlanning(object):
    
    def __init__(self, 
                 filter_freq=20,
                 url_stats='https://penguin-stats.io/PenguinStats/api/result/matrix', 
                 url_rules='https://ak.graueneko.xyz/akmaterial.json', 
                 path_stats='data/matrix', 
                 path_rules='data/akmaterial.json'):
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
            material_probs, convertion_rules = load_data(path_stats, path_rules)
        except:
            print('Requesting data from web resources (i.e., penguin-stats.io and ak.graueneko.xyz)...', end=' ')
            material_probs, convertion_rules = request_data(url_stats, url_rules, path_stats, path_rules)
            print('done.')

        if filter_freq:
            for dct in material_probs['matrix']:
                if dct['times']<filter_freq:
                    dct['quantity'] = 0

        self._set_lp_parameters(*self._pre_processing(material_probs, convertion_rules))
            
                
    def _pre_processing(self, material_probs, convertion_rules):
        """
        Compute costs, convertion rules and items probabilities from requested dictionaries.
        Args:
            material_probs: List of dictionaries recording the dropping info per stage per item.
                Keys of instances: ["itemID", "times", "itemName", "quantity", "apCost", "stageCode", "stageID"].
            convertion_rules: List of dictionaries recording the rules of composing.
                Keys of instances: ["id", "name", "level", "source", "madeof"].
        """
        # To count items and stages.
        item_dct = {}
        stage_dct = {}
        for dct in material_probs['matrix']:
            item_dct[dct['itemID']]=dct['itemName']
            stage_dct[dct['stageID']]=dct['stageCode']
        self.item_dct_rv = {v:k for k,v in item_dct.items()}
        
        # To unify the item identities from the two sources.
        for dct in convertion_rules:
            try:
                dct['id'] = self.item_dct_rv[dct['name']]
            except:
                self.item_dct_rv[dct['name']] = len(self.item_dct_rv)-1
                item_dct[len(item_dct)-1] = dct['name']
                dct['id'] = self.item_dct_rv[dct['name']]
            
        # To construct mapping from id to item names.
        self.item_array = np.empty(len(item_dct)-1, dtype='U25')
        for k,v in item_dct.items():
            if k>= 0:
                self.item_array[k] = v
                
        # To construct mapping from stage id to stage names and vice versa.
        stage_array = []
        for k,v in stage_dct.items():
            stage_array.append(v)
        self.stage_array = np.array(stage_array)
        self.stage_dct_rv = {v:k for k,v in enumerate(self.stage_array)}
        
        # To format dropping records into sparse probability matrix
        probs_matrix = np.zeros([len(self.stage_array), len(self.item_array)])
        cost_lst = np.zeros(len(self.stage_array))
        for dct in material_probs['matrix']:
            if dct['itemID'] >= 0:
                probs_matrix[self.stage_dct_rv[dct['stageCode']], dct['itemID']] = dct['quantity']/float(dct['times'])
                cost_lst[self.stage_dct_rv[dct['stageCode']]] = dct['apCost']
                
        # To build equavalence relationship from convert_rule_dct.
        self.convertions_dct = {}
        convertion_matrix = []
        convertion_cost_lst = []
        convertion_lv_cost = {2:100, 3:200, 4:300, 5:400}
        for rule in convertion_rules:
            if len(rule['madeof'])>0:
                self.convertions_dct[rule['name']] = rule['madeof']
                convertion = np.zeros(len(self.item_array))
                convertion[rule['id']] = 1
                for iname in rule['madeof']:
                    convertion[self.item_dct_rv[iname]] -= rule['madeof'][iname]
                convertion_matrix.append(convertion)
                convertion_cost_lst.append(convertion_lv_cost[rule['level']]*0.004)
        convertion_matrix = np.array(convertion_matrix)
        convertion_cost_lst = np.array(convertion_cost_lst)
                
        return convertion_matrix, convertion_cost_lst, probs_matrix, cost_lst
    
        
    def _set_lp_parameters(self, convertion_matrix, convertion_cost_lst, probs_matrix, cost_lst):
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
        self.convertion_matrix = convertion_matrix
        self.convertion_cost_lst = convertion_cost_lst
        self.probs_matrix = probs_matrix
        self.cost_lst = cost_lst
        
        assert len(self.probs_matrix)==len(self.cost_lst)
        assert len(self.convertion_matrix)==len(self.convertion_cost_lst)
        assert self.probs_matrix.shape[1]==self.convertion_matrix.shape[1]
        
        self.equav_cost_lst = np.hstack([cost_lst, convertion_cost_lst])
        self.equav_matrix = np.vstack([probs_matrix, convertion_matrix])
        
        
    def update(self, url_stats='https://penguin-stats.io/PenguinStats/api/result/matrix', 
                 url_rules='https://ak.graueneko.xyz/akmaterial.json', 
                 path_stats='data/matrix', 
                 path_rules='data/akmaterial.json'):
        """
        To update parameters when probabilities change or new items added.
        Args:
            url_stats: string. url to the dropping rate stats data.
            url_rules: string. url to the composing rules data.
            path_stats: string. local path to the dropping rate stats data.
            path_rules: string. local path to the composing rules data.
        """
        try:
            material_probs, convertion_rules = load_data(path_stats, path_rules)
        except:
            material_probs, convertion_rules = request_data(url_stats, url_rules)
        self.__init__(convert_rules_dct, cost_lst, looting_lst)


    def _get_plan_no_prioties(self, demand_lst):
        """
        To solve linear programming problem without prioties.
        Args:
            demand_lst: list of materials demand. Should include all items (zero if not required).
        Returns:
            strategy: list of required clear times for each stage.
            fun: estimated total cost.
        """
        status_dct = {0: 'Optimization terminated successfully, ',
                                    1: 'Iteration limit reached, ',
                                    2: 'Problem appears to be infeasible, ',
                                    3: 'Problem appears to be unbounded, '}
        
        solution = linprog(c=np.array(self.equav_cost_lst),
                                          A_ub=-self.equav_matrix.T,
                                          b_ub=-np.array(demand_lst))
        x, fun, status = solution.x, solution.fun, solution.status
        
        n_looting = x[:len(self.cost_lst)]
        n_convertion = x[len(self.cost_lst):]
        strategy = (n_looting, n_convertion)
        
        return strategy, fun, status_dct[status]
    
    
    def get_plan(self, requirement_dct, deposited_dct={}, prioty_dct=None):
        """
        User API. Computing the material plan given requirements and owned items.
        Args:
                requirement_dct: dictionary. Contain only required items with their numbers.
                deposit_dct: dictionary. Contain only owned items with their numbers.
        """
        demand_lst = np.zeros(len(self.item_array))+1e-5
        for k, v in requirement_dct.items():
            demand_lst[self.item_dct_rv[k]] = v
        for k, v in deposited_dct.items():
            demand_lst[self.item_dct_rv[k]] -= v
            
        stt = time.time()
        (n_looting, n_convertion), cost, status = self._get_plan_no_prioties(demand_lst)
        print(status+('Computed in %.4f seconds,' %(time.time()-stt)))
        
        print('Estimated total cost', int(cost))
        print('Looting at stages:')
        for i,t in enumerate(n_looting):
            if t > 1.0:
                target_items = np.where(self.probs_matrix[i]*t>=1)[0]
                display_lst = [self.item_array[idx]+' (%d)'%int(self.probs_matrix[i, idx]*t) for idx in target_items]
                print(self.stage_array[i] + ' (%d times) ===> ' %int(t) + ', '.join(display_lst))
        print('Synthesize items:')
        for i,t in enumerate(n_convertion):
            if t > 1.0:
                target_item = self.item_array[np.argmax(self.convertion_matrix[i])]
                display_lst = [k+' (%d) '%(v*int(t)) for k,v in self.convertions_dct[target_item].items()]
                print(target_item + ' (%d) <=== ' %int(t) +  ', '.join(display_lst))

def Cartesian_sum(arr1, arr2):
    arr_r = []
    for arr in arr1:
        arr_r.append(arr+arr2)
    arr_r = np.vstack(arr_r)
    return arr_r

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
    
    with urllib.request.urlopen(url_stats) as url:
        material_probs = json.loads(url.read().decode())
        with open(save_path_stats, 'w') as outfile:
            json.dump(material_probs, outfile)

    with urllib.request.urlopen(url_rules) as url:
        convertion_rules = json.loads(url.read().decode())
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