#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 23 20:14:28 2023

@author: wangyiran
"""

# https://blog.paperspace.com/working-with-different-genetic-algorithm-representations-python/

import pygad
import numpy as np
import pandas as pd
import json
import sys

class run_pyGAD():
    def __init__(self, run_scheme):
        self.run_scheme = run_scheme

        # For saving results
        self.result_dict = dict()
        self.result_dict["type_of_run"] = "pyGAD"
        self.result_dict['type_of_initial_data'] = run_scheme['initial_data_type']
        self.result_dict['max_index_found'] = []
        self.result_dict['total_combination_explored'] = []

        # For temporary storage for individual run
        self.initial_data_list = []
        self.iteration_list = []

        # Other private field used in individual run
        self.file_with_path = run_scheme['excel_path'] + run_scheme['user_results_file_name']
        self.choice_dict = self.create_choice_dict(self.file_with_path)
        self.result_df = pd.read_excel(self.file_with_path, sheet_name = 'ALL_RESULTS_DATA')
        self.gene_space = self.create_gene_space(self.choice_dict)
        self.initial_population = self.create_initial_population()





    def create_choice_dict(self, excel_file_name, current_data = 'CURRENT_DATA', property_basket = 'PROPERTY_BASKET', target_name = 'Target'):
        choice_dict ={}
        df_current = pd.read_excel(excel_file_name, sheet_name = current_data)

        for col_name in df_current.columns: 
            if col_name != target_name:
                choice_dict[col_name] = []
                
        df_prop = pd.read_excel(excel_file_name, sheet_name = property_basket)
        df_prop = df_prop.dropna(how='all', axis=1) #drop any empty columns in df_prop
        
        ##create choice_dict
        for key in choice_dict:
            name = key+'-CHOICES'
            if name in df_prop.columns:
                curr_list = df_prop[name].dropna().tolist()
                choice_dict[key] = [str(i) for i in curr_list]
                
        return choice_dict
    
    def create_gene_space(self, choice_dict):
        gene_space = []
        for key in choice_dict.keys():
            gene_space.append(range(len(choice_dict[key])))
        return gene_space
            
    def create_initial_population(self):
        df_current = pd.read_excel(self.file_with_path, sheet_name = 'CURRENT_DATA')
        initial_population = []
        for idx in df_current.index:
            index_list = [] # For GA usage
            point_dict = {} # For saving result usage
            for feature in df_current:
                point_dict[feature] = df_current[feature][idx]
                if feature != 'Target':
                    choice = df_current[feature][idx]
                    choice_index = self.choice_dict[feature].index(choice)
                    index_list.append(choice_index)
            initial_population.append(index_list)
            self.initial_data_list.append(point_dict)
        return initial_population
    
    def fitness_function(self, ga_instance, solution, solution_idx):
        # self.counter += 1
        point_dict = {}
        for i, key in enumerate(self.choice_dict):
            point_dict[key] = self.choice_dict[key][int(solution[i])]


        find_string = ''
        for i, key in enumerate(point_dict):
            if type(point_dict[key]) == str:
                added_string = ' {} == "{}" '.format(key, point_dict[key])
            else:
                added_string = ' {} == {} '.format(key, point_dict[key])
            if i < len(point_dict)-1:
                added_string += 'and'
            find_string += added_string
        
        # value = 0
        # #value = -100
        try:
            selected_df = self.result_df.query(find_string)
            value = selected_df['Target'].to_numpy()[0]
            point_dict['Target'] = value
            if (point_dict not in self.initial_data_list) and (point_dict not in self.iteration_list):
                self.iteration_list.append(point_dict)
        except:
            value = float('-inf')
            #print('omited combination: ' + find_string)
            
        return value

        
    
    def run(self):
        max_result = self.max_point()
        for i in range(self.run_scheme['num_repeated_runs']):
            ga_instance = pygad.GA(num_generations=self.run_scheme['num_generations'],
                           num_parents_mating=self.run_scheme['num_parents_mating'],
                           keep_parents=self.run_scheme['keep_parents'],
                           mutation_percent_genes=self.run_scheme['mutation_percent_genes'],
                           keep_elitism=self.run_scheme['keep_elitism'],
                           fitness_func=self.fitness_function,
                           gene_space=self.gene_space,
                           initial_population = self.initial_population,
                           gene_type = int,
                           save_solutions=True)
            ga_instance.run()
            self.result_dict['total_combination_explored'].append(len(self.iteration_list))
            if max_result in self.iteration_list:
                self.result_dict['max_index_found'].append(self.iteration_list.index(max_result))
            else:
                self.result_dict['max_index_found'].append(len(self.result_df))
            self.clear_run()


    def save_result(self):
        self.result_dict['max_index_found_avg'] = np.mean(self.result_dict['max_index_found'])
        self.result_dict['max_index_found_std'] = np.std(self.result_dict['max_index_found'])
        with open(self.run_scheme['user_results_folder'] + "pyGAD_output.json", "w") as outfile:
            json.dump(self.result_dict, outfile)


    def clear_run(self):
        self.iteration_list = []

    def check_unique(self, test_list):
        flag = 0

        # using naive method
        # to check all unique list elements
        for i in range(len(test_list)):
            for i1 in range(len(test_list)):
                if i != i1:
                    if test_list[i] == test_list[i1]:
                        flag = 1
        # printing result
        if (not flag):
            print("List contains all unique elements")
        else:
            print("List contains does not contains all unique elements")

    def max_point(self):
        maxCol = self.result_df.loc[self.result_df["Target"].idxmax()]
        return maxCol.to_dict()


if __name__ == '__main__':
    # pyGAD_run_scheme = {
    #     'user_results_file_name': 'reaction_1.xlsx',
    #     'excel_path': '/home/ywang580/scr16_pclancy3/gigi/PAL-SEARCH/',
    #     'generate_random_sample': False,
    #     'initial_data_type': 'cluster',
    #     'num_repeated_runs': 100,
    #     'user_results_folder': '/home/ywang580/scr16_pclancy3/gigi/PAL-SEARCH/', ## output path
    #     ## below are parameter for GA itself
    #     'num_generations': 5,
    #     'num_parents_mating': 4,
    #     'keep_parents': -1,
    #     'keep_elitism': 1,
    #     'mutation_percent_genes': "default",
    # }


    name_of_json = sys.argv[1]
    with open(name_of_json, 'r') as f:
        pyGAD_run_scheme = json.load(f)


    test = run_pyGAD(pyGAD_run_scheme)
    test.run()
    test.save_result()