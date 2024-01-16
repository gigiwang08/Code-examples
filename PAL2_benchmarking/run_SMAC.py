import logging
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

from ConfigSpace import Configuration, ConfigurationSpace, ForbiddenEqualsClause, ForbiddenAndConjunction
#from ConfigSpace.hyperparameters import Categorical
from ConfigSpace import Categorical
from smac import BlackBoxFacade, Scenario
from smac import HyperparameterOptimizationFacade
from smac import AlgorithmConfigurationFacade

from smac.initial_design import RandomInitialDesign


import sys
import random
import pickle
import json

import auxilliary_functions as aux 


class PalSMAC:
    def __init__(self, user_results_file_name):
        self.excel_file = user_results_file_name
        self.feature_dict = aux.create_choice_dict(user_results_file_name)
        self.result_df = pd.read_excel(user_results_file_name, sheet_name='ALL_RESULTS_DATA')
        self.current_df = pd.read_excel(user_results_file_name, sheet_name='CURRENT_DATA')
    
        
    def configspace(self) -> ConfigurationSpace: 
        cs = ConfigurationSpace()
        feature_list = []
        key_list = []
        for key in self.feature_dict:
            if len(self.current_df) > 0:
                feature_list.append(Categorical(key, self.feature_dict[key], default = self.current_df[key][0]))
            else:
                feature_list.append(Categorical(key, self.feature_dict[key]))
            
            key_list.append(key)
            
        cs.add_hyperparameters(feature_list)
        ## Take care of combination to omit:
        omit_df = pd.read_excel(self.excel_file, sheet_name='COMBINATIONS_TO_OMIT')
        if len(omit_df) != 0:
            forbidden_clauses_list = []
            for i in omit_df.index: 
                print("*****omitting configs*****")
                forbidden_conf = ForbiddenAndConjunction(
                    ## TODO: Change this according to how many features in your domain
                    ForbiddenEqualsClause(feature_list[0], omit_df[key_list[0]][i]),
                    ForbiddenEqualsClause(feature_list[1], omit_df[key_list[1]][i]),
                    ForbiddenEqualsClause(feature_list[2], omit_df[key_list[2]][i]),
                    ForbiddenEqualsClause(feature_list[3], omit_df[key_list[3]][i]),
                    ForbiddenEqualsClause(feature_list[4], omit_df[key_list[4]][i])
                    )
                forbidden_clauses_list.append(forbidden_conf)
            cs.add_forbidden_clauses(forbidden_clauses_list)

        return cs
    
    def cost_function(self, cfg, seed = 0):
        point_dict = {}
        for key in self.feature_dict:
            point_dict[key] = cfg[key]
        
        find_string = ''
        for i, key in enumerate(point_dict):
            if type(point_dict[key]) == str:
                added_string = ' {} == "{}" '.format(key, point_dict[key])
            else:
                added_string = ' {} == {} '.format(key, point_dict[key])
            if i < len(point_dict)-1:
                added_string += 'and'
            find_string += added_string

        selected_df = self.result_df.query(find_string)
        return -selected_df['Target'].to_numpy()[0]
    
    def max_value(self):
        maxCol = self.result_df.loc[self.result_df["Target"].idxmax()]
        return maxCol['Target']

def read_initial_data(pal): 
    df = pd.read_excel(pal.excel_file, sheet_name='CURRENT_DATA')
    cs = pal.configspace()

    conf_list = []
    value_pair = {}
    for i in df.index:
        for key in pal.feature_dict:
            value_pair[key] = df[key][i]
        conf = Configuration(cs, values = value_pair)
        conf_list.append(conf)

    return conf_list

def target_value_list(smac):
    y_list = []
    for i, config in enumerate(smac.runhistory.get_configs()):
        target = -pal.cost_function(config)
        y_list.append(target)
        
    return y_list
    

def incumbent_value_list(smac):
    max_num = 0
    x_list = []
    y_list = []
    for i, config in enumerate(smac.runhistory.get_configs()):
        target = -pal.cost_function(config)
        if max_num < target:
            x_list.append(i+1)
            y_list.append(target)
    return x_list, y_list


def plot(x_target_list, y_target_list, x_incumbent_list, y_incumbent_list, maxValue = 0):
    plt.scatter(x_target_list, y_target_list)
    plt.step(x_incumbent_list, y_incumbent_list, 'r*', where='post')
    if maxValue != 0:
        plt.axhline(y=maxValue, color='r', linestyle='-')
    plt.show()

def create_json_file(type_of_facade, target_value_list, all_configs, pal, output_path, type_of_inital_data):
    number_of_initial_data = len(pal.current_df)
    feature_list = list(pal.feature_dict.keys())
    dictionary = {}
    dictionary["type_of_run"] = "smac"
    dictionary["type_of_initial_data"] = type_of_inital_data
    dictionary["facade"] = type_of_facade
    dictionary["Configs"] = {}
    dictionary["Configs"]["initial_data"] = {}
    dictionary["Configs"]["Bo_iterations"] = {}
    
    BO_count = 1
    for i, conf in enumerate(all_configs):
        # Convert a conf into a value dictionary:
        value_dict = {}
        value_dict['Target'] = target_value_list[i]
        for feature in feature_list:
            value_dict[feature] = conf[feature]
        if (i+1 <= number_of_initial_data) :
            dictionary["Configs"]["initial_data"][i+1] = value_dict
        else:
            dictionary["Configs"]["Bo_iterations"][BO_count] = value_dict
            BO_count += 1
    
    print(dictionary)
    with open(output_path + "smac_" + type_of_facade + "_output.json", "w") as f:
        json.dump(dictionary, f)


    
if __name__ == "__main__":
    
    run_scheme1 = {
        "user_results_file_name": "test_r2.xlsx",
        'generate_random_sample': False,
        "walltime_limit" : 360, # in second
        "initial_data_type" : "cluster",
        'n_trials': 140,
        'number_of_initial_data': 36, ## needed if generate_random_sample is True
        'number_of_experiments': 1,
        'facade': ['hyper'], ## hyper, blackbox, algo
        'user_results_folder': "./test_SMAC/", ## output path
        'type_of_run': ['smac']
    }
    
    try:
        name_of_json = sys.argv[1]
        with open(name_of_json, 'r') as f:
            run_scheme = json.load(f)
    except:
        run_scheme = run_scheme1

    print(run_scheme['user_results_file_name'])
    pal = PalSMAC(run_scheme['user_results_folder'] + run_scheme['user_results_file_name'])
    cs = pal.configspace()
    number_of_experiment = run_scheme['number_of_experiments']
    seed_list = [random.randint(0, 2**32) for i in range(number_of_experiment)]


    # HyperparameterOptimizationFacade
    if 'hyper' in run_scheme['facade']:
        total_target = []
        for i in range(number_of_experiment):
            scenario = Scenario(cs, n_trials=run_scheme['n_trials'], name = "HyperFacade", output_directory = run_scheme['user_results_folder'], deterministic=True, seed = seed_list[i], walltime_limit=run_scheme["walltime_limit"])
            if run_scheme['generate_random_sample']:
                initial_design = RandomInitialDesign(scenario, max_ratio=0.8, n_configs = run_scheme['number_of_initial_data'])
            else:
                initial_design = RandomInitialDesign(scenario, max_ratio=0.8, n_configs = 0, additional_configs = read_initial_data(pal))
            smac = HyperparameterOptimizationFacade(
                    scenario,
                    pal.cost_function,
                    initial_design=initial_design,
                    overwrite=True
                )
            incumbent = smac.optimize()
            y_target_list = target_value_list(smac)
            total_target.append(y_target_list)
            file_name = run_scheme['user_results_folder'] + 'hyper' + '_configuration_' + str(i) + '_trial' + '.pkl'
            create_json_file('hyper', y_target_list, smac.runhistory.get_configs(), pal, run_scheme['user_results_folder'], run_scheme['initial_data_type'])
            
    # BlackBoxFacade
    if 'blackbox' in run_scheme['facade']:
        total_target = []
        total_config_list = []
        for i in range(number_of_experiment):
            scenario = Scenario(cs, n_trials=run_scheme['n_trials'], name = "BlackBoxFacade", output_directory = run_scheme['user_results_folder'], deterministic=True, seed = seed_list[i], walltime_limit=run_scheme["walltime_limit"])
            if run_scheme['generate_random_sample']:
                initial_design = RandomInitialDesign(scenario, max_ratio=0.8, n_configs = run_scheme['number_of_initial_data'])
            else:
                initial_design = RandomInitialDesign(scenario, max_ratio=0.8, n_configs = 0, additional_configs = read_initial_data(pal))
            smac = BlackBoxFacade(
                    scenario,
                    pal.cost_function,
                    initial_design=initial_design,
                    overwrite=True
                )
            incumbent = smac.optimize()
            y_target_list = target_value_list(smac)
            total_target.append(y_target_list)
            # Save config for each experiment:
            file_name = run_scheme['user_results_folder'] + 'blackbox' + '_configuration_' + str(i) + '_trial' + '.pkl'
            create_json_file('blackbox', y_target_list, smac.runhistory.get_configs(), pal, run_scheme['user_results_folder'], run_scheme['initial_data_type'])
            
    # Algorithm configuration
    if 'algo' in run_scheme['facade']:
        total_target = []
        for i in range(number_of_experiment):
            scenario = Scenario(cs, n_trials=run_scheme['n_trials'], name = "AlgoFacade", output_directory = run_scheme['user_results_folder'], deterministic=True, seed = seed_list[i], walltime_limit=run_scheme["walltime_limit"])
            if run_scheme['generate_random_sample']:
                initial_design = RandomInitialDesign(scenario, max_ratio=0.8, n_configs = run_scheme['number_of_initial_data'])
            else:
                initial_design = RandomInitialDesign(scenario, max_ratio=0.8, n_configs = 0, additional_configs = read_initial_data(pal))
            smac = AlgorithmConfigurationFacade(
                    scenario,
                    pal.cost_function,
                    initial_design=initial_design,
                    overwrite=True
                )
            incumbent = smac.optimize()
            y_target_list = target_value_list(smac)
            total_target.append(y_target_list)
            file_name = run_scheme['user_results_folder'] + 'hyper' + '_configuration_' + str(i) + '_trial' + '.pkl'
            create_json_file('algo', y_target_list, smac.runhistory.get_configs(), pal, run_scheme['user_results_folder'], run_scheme['initial_data_type'])


        
    
