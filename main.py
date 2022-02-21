import csv
import os
import signal
import time
from os.path import isfile, join
from pathlib import Path
from os import listdir
import logging

from biodivine_boolean_networks import *
from biodivine_aeon import *

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

MODELS_DIR = 'control_models'
TIMEOUT_SECS = 5


def get_model_files():
    return [Path(join(MODELS_DIR, f)) for f in listdir(MODELS_DIR) if isfile(join(MODELS_DIR, f))]


def attractor_colors(vertex: [bool], perturbation_graph: PerturbationGraph):
    graph = perturbation_graph.as_perturbed()
    colored_vertex = graph.fix_vertex(vertex)
    fwd = graph.post(colored_vertex)
    bwd = graph.pre(colored_vertex)
    scc = fwd.intersect(bwd)
    not_attractor_colors = fwd.minus(scc).colors()
    return scc.minus_colors(not_attractor_colors).colors()


def timeout_handler(_num, _stack):
    logging.warning("Received SIGALRM")
    raise Exception("FUBAR")


def measure(fun):
    logging.info("Starting measuring")
    start = time.time()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECS)
    try:
        fun()
    except Exception as ex:
        if "FUBAR" in str(ex):
            return "N/A"
        else:
            raise ex
    finally:
        signal.alarm(0)
    end = time.time()
    return end - start


def benchmark_model(model_file_path):
    results = []
    logging.info(model_file_path)
    model_string = model_file_path.read_text()
    boolean_network = BooleanNetwork.from_aeon(model_string)
    vars_count = boolean_network.num_vars()
    logging.info(f"vars count: {vars_count}")
    try:
        symbolic_async_graph = SymbolicAsyncGraph(boolean_network)
    except Exception as e:
        print(e)
        return

    logging.info(f"colors count: {symbolic_async_graph.unit_colored_vertices().cardinality() / vars_count}")
    logging.info(f"total cardinality: {symbolic_async_graph.unit_colored_vertices().cardinality()}")

    logging.info(find_attractors(symbolic_async_graph))
    witness = SymbolicAsyncGraph(symbolic_async_graph.pick_witness(symbolic_async_graph.unit_colors()))
    attractor_vertices = [a.pick_vertex().vertices().vertices()[0] for a in find_attractors(witness)]
    logging.info(f"attractor count: {len(attractor_vertices)}")

    for i, target in enumerate(attractor_vertices[:8]):
        perturbation_graph = PerturbationGraph(boolean_network)
        colors = attractor_colors(target, perturbation_graph)
        for j, source in enumerate(attractor_vertices[:8]):
            if i == j:
                continue
            one_step_time = measure(lambda: perturbation_graph.one_step_control(source, target, colors))
            permanent_time = measure(lambda: perturbation_graph.permanent_control(source, target, colors))
            temporary_time = measure(lambda: perturbation_graph.temporary_control(source, target, colors))
            results.append((model_file_path, i, j, one_step_time, permanent_time, temporary_time))
    return results


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    model_files = get_model_files()
    header = [['model', 'target_ix', 'source_ix', 'one_step_time', 'permanent_time', 'temporary_time']]
    all_results = sum([benchmark_model(mf) for mf in model_files], header)
    with open("out.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(all_results)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
