import os
import sys
import json
import shutil
import auxilliary_functions as aux


def create_script(job_name, json_file_location, specification_dict, src_path = './', output_path = './', queue_system = 'slurm', additional_line = "", start_run = False):
    
    additional_line = "ml anaconda\nconda activate pal-search\n"
    number_of_cores = specification_dict['number_of_cores']
    partition = specification_dict['partition']
    walltime = specification_dict['walltime']
    allocation = specification_dict['allocation']
    if queue_system == 'slurm':
        file_name = output_path + job_name+".slurm" 
        
        with open(file_name, 'w') as file:
            file.write("#!/bin/sh\n")
            file.write("#SBATCH -J {}\n".format(job_name))
            file.write("#SBATCH -o {}.o%j\n".format(output_path + job_name))
            file.write("#SBATCH -N 1\n")
            file.write("#SBATCH -n {}\n".format(number_of_cores))
            file.write("#SBATCH -p {}\n".format(partition))
            file.write("#SBATCH -t {}\n".format(walltime))
            file.write("#SBATCH -A {}\n".format(allocation))
            if specification_dict['extra_time']:
                file.write("#SBATCH --qos=extended\n")
        
            file.write("\n")
            file.write(additional_line)
            for type_of_run in specification_dict['type_of_run_list']:
                json_filename = json_file_location + type_of_run + '_run_scheme.json'
                if type_of_run == 'smac':
                    file.write("python {}run_SMAC.py {} > {} \n".format(src_path, json_filename, output_path + job_name+'.out'))
                elif type_of_run == 'pyGAD':
                    file.write("python {}run_GA.py {} > {} \n".format(src_path, json_filename, output_path + job_name+'.out'))
                elif type_of_run == 'hyperopt':
                    file.write("python {}run_hyperopt.py {} > {} \n".format(src_path, json_filename, output_path + job_name+'.out'))
                else:
                    file.write("python {}run_belief.py {} > {} \n".format(src_path, json_filename, output_path + job_name+'.out'))
        if start_run:
            os.system('sbatch ' + file_name)

def write_json(run_scheme_list, target_path, excel_path):
    for run_scheme in run_scheme_list:
        run_scheme['user_results_folder'] = target_path
        run_scheme['excel_path'] = excel_path
        if 'pal' in run_scheme['type_of_run']:
            json_filename = 'pal_run_scheme.json'
        elif 'smac' in run_scheme['type_of_run']:
            json_filename = 'smac_run_scheme.json'
        elif 'pyGAD' in run_scheme['type_of_run']:
            json_filename = 'pyGAD_run_scheme.json'
        elif 'hyperopt' in run_scheme['type_of_run']:
            json_filename = 'hyperopt_run_scheme.json'
        else:
            json_filename = 'other_run_scheme.json'
        with open(target_path + json_filename, "w") as outfile:
            json.dump(run_scheme, outfile)

def create_exp_folder(exp_index, output_path_allFolders, pal_src_folder, original_user_results_file, initial_data_type, number_of_initial_data, other_run_schemes, other_slurm_specification, ps_run_scheme, pal_slurm_specification, start_run):
    trial_name = 'exp_' + str(exp_index)
    os.makedirs(os.path.join(output_path_allFolders, trial_name))
    target_path = output_path_allFolders + trial_name + '/'
    original_location = pal_src_folder + original_user_results_file
    target_location = target_path + original_user_results_file
    shutil.copyfile(original_location, target_location)
    aux.generate_initial_data_for_bo(target_location, sample_style = initial_data_type, number_of_initial_data= number_of_initial_data, closed_loop=True, avoid_max=True)
    write_json(other_run_schemes, target_path, target_path)
    create_script('run_other', target_path, other_slurm_specification, src_path = pal_src_folder, output_path = target_path, start_run = start_run)
    # Create ps_scheme folders
    for key in ps_run_scheme:
        os.makedirs(os.path.join(target_path, key))
        ps_path = target_path + key + '/'
        write_json([ps_run_scheme[key]], ps_path, target_path)
        create_script('run_pal', ps_path, pal_slurm_specification, src_path = pal_src_folder, output_path = ps_path, start_run = start_run)

if __name__ == "__main__":
    start_run = False
    ## parameters to defined for a run
    pal_src_folder = '/home/ywang580/scr16_pclancy3/gigi/PAL-SEARCH/'
    output_dir_name = 'test_other' 
    original_user_results_file = 'test_henry.xlsx' 
    initial_data_type = 'random' ## 'clustered', 'dispersed'
    initial_data_fraction = 0.05
    total_number_of_data_point = 71
    number_of_initial_data = int(initial_data_fraction * total_number_of_data_point)
    number_of_experiment = 2
    
    pal_slurm_specification = {
        'number_of_cores' : 1, 
        'allocation' : 'pclancy3', 
        'partition' : 'defq', 
        'walltime' : '140:00:00',
        'type_of_run_list' : ['pal'],
        'extra_time' : True ## Set this to true only if the wall-time exceed 72 hours
    }

    other_slurm_specification = {
        'number_of_cores' : 1, 
        'allocation' : 'pclancy3', 
        'partition' : 'defq', 
        'walltime' : '01:00:00',
        'type_of_run_list': ['other', 'smac', 'pyGAD', 'hyperopt'],
        # 'type_of_run_list': ['other'],
        'extra_time' : False ## Set this to true only if the wall-time exceed 72 hours
    }

    pal_run_scheme = {
        'user_results_file_name': original_user_results_file,
        'excel_path': './',
        'tops': '5%',
        'pseudo_pal_storage_name': 'test2',
        'initial_data': [False, initial_data_type, number_of_initial_data],
        'restart': True,
        'descriptor_kernels': ['Matern5'],
        'simple_operations': False,
        'mean_types': ['linear', 'constant', '0'],
        'target_name': ['Target'],
        'user_results_folder': './',
        'type_of_run': ['pal'],
        'voting_scheme': ['aristocracy'],
        'acquisition_function': "probability",
        'optimization': 'max',  ## max/min
        'simple_method': False,
        'BO-iterations': int(total_number_of_data_point - number_of_initial_data),
        'use_pca': False,
        'include_sigma': False,
        'include_ohe': False,
        'training_iterations': 200,
        'OPEN_LOOP': False
    }

    # param_to_vary = {'score_weighting': [{'criteria_1': [1.0, 'linear'], 'criteria_2': [1.0, 'linear'], 'criteria_3': [1.0, 'linear']}, {'criteria_1': [1.0, 'relu'], 'criteria_2': [1.0, 'relu'], 'criteria_3': [1.0, 'relu']}]}
    # param_to_vary = {'tops': ['1','2','5%']}
    param_to_vary = {}

    other_run_scheme = {
        'user_results_file_name': original_user_results_file,
        'restart': True,
        'initial_data': [False, initial_data_type, number_of_initial_data],
        'excel_path': './',
        'acquisition_function': 'contextual-varied',
        'optimization': 'max',  ## max/min
        'BO-iterations': int(total_number_of_data_point - number_of_initial_data),
        'target_name': ['Target'],
        'user_results_folder': './',
        'training_iterations': 200,
        'OPEN_LOOP': False,
        'type_of_run': ['naive', 'random'],
        'custom': 'henry_model.json'
    }


    smac_run_scheme = {
        "user_results_file_name": original_user_results_file,
        'excel_path': './',
        'generate_random_sample': False,
        "walltime_limit" : 360, # in second
        "initial_data_type" : initial_data_type,
        'n_trials': total_number_of_data_point,
        'number_of_initial_data': 36, ## needed if generate_random_sample is True
        'number_of_experiments': 1,
        'facade': ['blackbox', 'hyper'], ## hyper, blackbox, algo
        'user_results_folder': "./test_SMAC/", ## output path
        'type_of_run': ['smac']
    }

    pyGAD_run_scheme = {
        'user_results_file_name': original_user_results_file,
        'excel_path': './',
        'generate_random_sample': False,
        'initial_data_type': initial_data_type,
        'num_repeated_runs': 100,
        'user_results_folder': './', ## output path
        ## below are parameter for GA itself
        'num_generations': 100,
        'num_parents_mating': 4,
        'keep_parents': -1,
        'keep_elitism': 1,
        'mutation_percent_genes': "default",
        'type_of_run':['pyGAD']
    }

    hyperopt_run_scheme = {
    'user_results_file_name': original_user_results_file,
    'excel_path': './',
    'user_results_folder': './', ## output path
    'type_of_run':['hyperopt']
    }
    
    if 'custom' in other_run_scheme['type_of_run']:
        new_custom_filename = pal_src_folder + other_run_scheme['custom']
        with open(new_custom_filename, 'r') as f:
            print("Working belief file exit")
        other_run_scheme['custom'] = new_custom_filename

    # Creating multiple ps_run_scheme
    if len(param_to_vary) == 0: # run base case if param_to_vary is empty
        ps_run_scheme = {'ps_scheme1': pal_run_scheme}
    else:
        count = 1
        ps_run_scheme = {}
        for k, v in param_to_vary.items():
            for param in v:
                new_run_scheme = dict(pal_run_scheme)
                new_run_scheme[k] = param
                scheme_name = 'ps_scheme' + str(count)
                ps_run_scheme[scheme_name] = new_run_scheme
                count+=1

    other_run_schemes = [other_run_scheme, smac_run_scheme, pyGAD_run_scheme, hyperopt_run_scheme]
    
    try: 
        # Create output directory:
        os.makedirs(os.path.join(pal_src_folder, output_dir_name))
        output_path_allFolders = pal_src_folder + output_dir_name + '/'

        # Saving ps_run_scheme:
        with open(output_path_allFolders + 'ps_run_scheme.json', "w") as outfile:
                json.dump(ps_run_scheme, outfile)
                
        # Create exp folders
        for i in range(1, number_of_experiment + 1):
            create_exp_folder(i, output_path_allFolders, pal_src_folder, original_user_results_file, initial_data_type, number_of_initial_data, other_run_schemes, other_slurm_specification, ps_run_scheme, pal_slurm_specification, start_run)
    except FileExistsError:
        previous_num_exp = 0
        cur_exp=[]
        for dir_name in os.listdir(pal_src_folder + output_dir_name):
            if 'exp_' in dir_name:
                cur_exp_temp = int(dir_name.split('_')[1])
                cur_exp.append(cur_exp_temp)
        if previous_num_exp < max(cur_exp):
            previous_num_exp = max(cur_exp)

        if previous_num_exp >= number_of_experiment:
            raise Exception(f"{output_dir_name} already existed, number_of_experiment must be greater than {previous_num_exp}")
        print("start creating new exp folder")
        
        # reconstruct run_schemes from exp_1 folder
        other_run_schemes = []
        ps_run_scheme = {}
        exp_1_path = pal_src_folder + output_dir_name + '/exp_1'
        for dir_name in os.listdir(exp_1_path):
            if "_run_scheme.json" in dir_name:
                with open(exp_1_path + '/' + dir_name, 'r') as f:
                    other_run_schemes.append(json.load(f))
            elif "ps_scheme" in dir_name:
                with open(f"{exp_1_path}/{dir_name}/pal_run_scheme.json", 'r') as f:
                    ps_run_scheme[dir_name] = json.load(f)
        
        # start creating exp folder
        for i in range(previous_num_exp + 1, number_of_experiment + 1):
            output_path_allFolders = pal_src_folder + output_dir_name + '/'
            ps_sample_dict = ps_run_scheme['ps_scheme1']
            #data_type = ps_sample_dict['initial_data']
            print("**********************")
            data_type = ps_run_scheme['ps_scheme1']['initial_data'][1]
            num_initial_data = ps_run_scheme['ps_scheme1']['initial_data'][2]
            print(data_type)
            print(num_initial_data)
            create_exp_folder(i, output_path_allFolders, pal_src_folder, original_user_results_file, data_type, num_initial_data, other_run_schemes, other_slurm_specification, ps_run_scheme, pal_slurm_specification, start_run)
