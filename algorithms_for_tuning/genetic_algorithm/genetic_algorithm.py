import os
import click
import random
import numpy as np
import time
import copy
import operator
import uuid
import gc

from kube_fitness.tasks import make_celery_app, parallel_fitness, IndividualDTO

from mutation import mutation
from crossover import crossover
from selection import selection

NUM_FITNESS_EVALUATIONS = 150


@click.command()
@click.option('--num-individuals', default=10)
@click.option('--mutation-type', default="combined")
@click.option('--crossover-type', default="blend_crossover")
@click.option('--selection-type', default="fitness_prop")
@click.option('--elem-cross-prob', default=None)
@click.option('--cross-alpha', default=None)
@click.option('--best-proc', default=0.4)
def run_algorithm(num_individuals,
                  mutation_type, crossover_type, selection_type,
                  elem_cross_prob, cross_alpha,
                  best_proc):
    g = GA(num_individuals=num_individuals, num_iterations=400, mutation_type=mutation_type,
           crossover_type=crossover_type,
           selection_type=selection_type,
           elem_cross_prob=elem_cross_prob,
           num_fitness_evaluations=NUM_FITNESS_EVALUATIONS,
           best_proc=best_proc,
           alpha=cross_alpha)
    best_value = g.run(verbose=True, logs_path="logs")
    return best_value


class GA:
    def __init__(self, num_individuals, num_iterations,
                 mutation_type='mutation_one_param', crossover_type='blend_crossover',
                 selection_type='fitness_prop', mutation_probability=0.6,
                 elem_mutation_prob=0.1, elem_cross_prob=0.2, num_fitness_evaluations=200,
                 best_proc=0.3, alpha=None):

        if crossover_type == 'blend_crossover':
            self.crossover_children = 1
        else:
            self.crossover_children = 2

        self.num_individuals = num_individuals
        self.num_iterations = num_iterations
        self.mutation = mutation(mutation_type)  # mutation function
        self.crossover = crossover(crossover_type)  # crossover finction
        self.selection = selection(selection_type)  # selection function
        self.mutation_probability = mutation_probability  # ?
        self.elem_mutation_prob = elem_mutation_prob  # ?
        self.elem_cross_prob = elem_cross_prob
        self.alpha = alpha
        self.num_fitness_evaluations = num_fitness_evaluations
        self.best_proc = best_proc

    @staticmethod
    def init_individ(high_decor=1e5,
                     high_n=8, high_spb=1e2,
                     low_spm=-1e2):
        val_decor = np.random.uniform(low=0, high=high_decor, size=1)[0]
        var_n = np.random.randint(low=0, high=high_n, size=5)
        var_sm = np.random.uniform(low=1e-3, high=high_spb, size=2)
        var_sp = np.random.uniform(low=low_spm, high=-1e-3, size=4)
        ext_mutation_prob = np.random.uniform(low=0, high=1, size=1)[0]
        ext_elem_mutation_prob = np.random.uniform(low=0, high=1, size=1)[0]
        ext_mutation_selector = np.random.uniform(low=0, high=1, size=1)[0]
        val_decor_2 = np.random.uniform(low=0, high=high_decor, size=1)[0]
        params = [
            val_decor, var_n[0],
            var_sm[0], var_sm[1], var_n[1],
            var_sp[0], var_sp[1], var_n[2],
            var_sp[2], var_sp[3], var_n[3],
            var_n[4],
            ext_mutation_prob, ext_elem_mutation_prob, ext_mutation_selector,
            val_decor_2
        ]
        params = [float(i) for i in params]
        return params

    def init_population(self):
        list_of_individuals = []
        for i in range(self.num_individuals):
            list_of_individuals.append(IndividualDTO(id=str(uuid.uuid4()),
                                                     params=self.init_individ()))
        population_with_fitness = parallel_fitness(list_of_individuals)
        return population_with_fitness

    def run(self, logs_path, verbose=False):

        evaluations_counter = 0
        ftime = str(int(time.time()))

        print(
            '!=========================================== Starting experiment {} ===========================================!'.format(
                ftime))
        log_file_path = os.path.join(logs_path, 'log_{}_trial_rank_based'.format(ftime))
        with open(log_file_path, 'w') as log_file:
            log_file.write('=======================\n')
            log_file.write(
                'ALGORITHM PARAMS  number of individuals {}; number of fitness evals {}; crossover prob {}: \n'.format(
                    self.num_individuals, self.num_fitness_evaluations, self.elem_cross_prob))
            log_file.write('=======================\n')

            # population initialization
            population = self.init_population()

            evaluations_counter = self.num_individuals

            log_file.write('=======================\n')
            log_file.write('POPULATION IS CREATED \n')
            log_file.write('=======================\n')

            x, y = [], []
            high_fitness = 0
            for ii in range(self.num_iterations):

                new_generation = []

                log_file.write('=======================\n')
                log_file.write('ENTERING GENERATION {} \n'.format(ii))
                log_file.write('=======================\n')

                population.sort(key=operator.attrgetter('fitness_value'), reverse=True)
                pairs_generator = self.selection(population=population,
                                                 best_proc=self.best_proc, children_num=self.crossover_children)

                log_file.write('=======================\n')
                log_file.write('PAIRS ARE CREATED \n')
                log_file.write('=======================\n')

                # Crossover
                for i, j in pairs_generator:

                    parent_1 = copy.deepcopy(i.params)
                    parent_2 = copy.deepcopy(j.params)

                    if self.crossover_children == 2:

                        child_1, child_2 = self.crossover(parent_1=parent_1,
                                                          parent_2=parent_2,
                                                          elem_cross_prob=self.elem_cross_prob,
                                                          alpha=self.alpha)

                        new_generation.append(IndividualDTO(id=str(uuid.uuid4()),
                                                            params=child_1))
                        new_generation.append(IndividualDTO(id=str(uuid.uuid4()),
                                                            params=child_2))
                        evaluations_counter += 2
                    else:
                        child_1 = self.crossover(parent_1=parent_1,
                                                 parent_2=parent_2,
                                                 elem_cross_prob=self.elem_cross_prob,
                                                 alpha=self.alpha
                                                 )
                        new_generation.append(IndividualDTO(id=str(uuid.uuid4()),
                                                            params=child_1))

                        evaluations_counter += 1

                print('CURRENT COUNTER: {}'.format(evaluations_counter))
                new_generation = parallel_fitness(new_generation)

                new_generation.sort(key=operator.attrgetter('fitness_value'), reverse=True)
                population.sort(key=operator.attrgetter('fitness_value'), reverse=True)

                log_file.write('=======================\n')
                log_file.write('CROSSOVER IS OVER \n')
                log_file.write('=======================\n')

                if evaluations_counter >= self.num_fitness_evaluations:
                    log_file.write('=======================\n')
                    log_file.write('TERMINATION IS TRIGGERED \n')
                    log_file.write('=======================\n')
                    log_file.write('THE BEST FITNESS {}\n'.format(population[0].fitness_value))
                    #                     log_file.write('THE BEST SCORES {}\n'.format(population[0].scores))
                    log_file.write('THE BEST PARAMS {}\n'.format(''.join([str(i) for i in population[0].params])))
                    log_file.close()
                    return population[0].fitness_value

                del pairs_generator
                gc.collect()

                population_params = [copy.deepcopy(individ.params) for individ in population]

                the_best_guy_params = copy.deepcopy(population[0].params)
                new_generation = [individ for individ in new_generation if individ.params != the_best_guy_params]

                population = population[0:int(self.num_individuals * self.best_proc)] + new_generation[:(
                        self.num_individuals - int(self.num_individuals * self.best_proc))]

                try:
                    del new_generation
                except:
                    pass

                gc.collect()

                population.sort(key=operator.attrgetter('fitness_value'), reverse=True)

                try:
                    del population[self.num_individuals]
                except:
                    pass

                # mutation params 12, 13
                for i in range(1, len(population)):
                    if random.random() <= population[i].params[12]:
                        for idx in range(3):
                            if random.random() < population[i].params[13]:
                                if idx == 0:
                                    population[i].params[12] = np.random.uniform(low=0, high=1, size=1)[0]
                                elif idx == 2:
                                    population[i].params[13] = np.random.uniform(low=0, high=1, size=1)[0]
                                elif idx == 3:
                                    population[i].params[13] = np.random.uniform(low=0, high=1, size=1)[0]

                    if random.random() <= population[i].params[12]:
                        params = self.mutation(copy.deepcopy(population[i].params),
                                               elem_mutation_prob=copy.deepcopy(population[i].params[13]))
                        population[i] = IndividualDTO(id=str(uuid.uuid4()),
                                                      params=[float(i) for i in params])  # TODO: check mutation
                    evaluations_counter += 1

                population = parallel_fitness(population)

                ###
                log_file.write('=======================\n')
                log_file.write('MUTATION IS OVER \n')
                log_file.write('=======================\n')

                population.sort(key=operator.attrgetter('fitness_value'), reverse=True)

                if evaluations_counter >= self.num_fitness_evaluations:
                    log_file.write('=======================\n')
                    log_file.write('TERMINATION IS TRIGGERED \n')
                    log_file.write('=======================\n')
                    log_file.write('THE BEST FITNESS {}\n'.format(population[0].fitness_value))
                    #                     log_file.write('THE BEST SCORES {}\n'.format(population[0].scores))
                    log_file.write('THE BEST PARAMS {}\n'.format('; '.join([str(i) for i in population[0].params])))
                    log_file.close()
                    return population[0].fitness_value

                current_fitness = population[0].fitness_value
                if (current_fitness > high_fitness) or (ii == 0):
                    high_fitness = current_fitness

                log_file.write('=======================\n')
                log_file.write('GENERATION {} IS OVER \n'.format(ii))
                log_file.write('=======================\n')
                log_file.write('THE BEST FITNESS {}\n'.format(population[0].fitness_value))
                #                 log_file.write('THE BEST SCORES {}\n'.format(population[0].scores))
                log_file.write('THE BEST PARAMS {}\n'.format('; '.join([str(i) for i in population[0].params])))

                x.append(ii)
                y.append(population[0].fitness_value)

                print('Population len {}'.format(len(population)))
                print()
                print('Best params so far: {}, with fitness: {}'.format(population[0].params,
                                                                        population[0].fitness_value))
            log_file.close()
            print()
            print(y)
            # plot_ga(x, y, fig_title='Genetic algorithm convergence', x_title='Iteration', y_title='Best perplexity')
            return population[0].fitness_value


if __name__ == "__main__":
    run_algorithm()