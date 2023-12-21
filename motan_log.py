#!/usr/bin/env python
# Script to perform motion analysis and return data table
#
# Copyright (C) 2019-2021  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import sys, optparse, ast
import pandas as pd
import readlog, analyzers
try:
    import urlparse
except:
    import urllib.parse as urlparse

######################################################################
# Data Table Generation
######################################################################

def generate_motion_csv(amanager, graph_descs):
    data = {}
    for graph_row in graph_descs:
        for graph_desc in graph_row:
            dataset, _ = parse_graph_description(graph_desc)
            amanager.setup_dataset(dataset)
    amanager.generate_datasets()
    datasets = amanager.get_datasets()
    times = amanager.get_dataset_times()

    for dataset in datasets:
        data[dataset] = datasets[dataset]

    data['Time'] = times
    df = pd.DataFrame(data)
    return df

######################################################################
# Startup
######################################################################

def setup_matplotlib(output_to_file):
    global matplotlib
    if output_to_file:
        matplotlib.use('Agg')
    import matplotlib.pyplot, matplotlib.dates, matplotlib.font_manager
    import matplotlib.ticker

def parse_graph_description(desc):
    if '?' not in desc:
        return (desc, {})
    dataset, params = desc.split('?', 1)
    params = {k: v for k, v in urlparse.parse_qsl(params)}
    for fkey in ['alpha']:
        if fkey in params:
            params[fkey] = float(params[fkey])
    return (dataset, params)

def list_datasets():
    datasets = readlog.list_datasets() + analyzers.list_datasets()
    out = ["\nAvailable datasets:\n"]
    for dataset, desc in datasets:
        out.append("%-24s: %s\n" % (dataset, desc))
    out.append("\n")
    sys.stdout.write("".join(out))
    sys.exit(0)

def main():
    # Parse command-line arguments
    usage = "%prog [options] <logname>"
    opts = optparse.OptionParser(usage)
    opts.add_option("-o", "--output", type="string", dest="output",
                    default=None, help="filename of output CSV")
    opts.add_option("-s", "--skip", type="float", default=0.,
                    help="Set the start time to graph")
    opts.add_option("-d", "--duration", type="float", default=5.,
                    help="Number of seconds to graph")
    opts.add_option("--segment-time", type="float", default=0.000100,
                    help="Analysis segment time (default 0.000100 seconds)")
    opts.add_option("-g", "--graph", help="Graph to generate (python literal)")
    opts.add_option("-l", "--list-datasets", action="store_true",
                    help="List available datasets")
    options, args = opts.parse_args()
    if options.list_datasets:
        list_datasets()
    if len(args) != 1:
        opts.error("Incorrect number of arguments")
    log_prefix = args[0]

    # Open data files
    lmanager = readlog.LogManager(log_prefix)
    lmanager.setup_index()
    lmanager.seek_time(options.skip)
    amanager = analyzers.AnalyzerManager(lmanager, options.segment_time)
    amanager.set_duration(options.duration)

    # Default graphs to draw
    graph_descs = [
        "status(hall_filament_width_sensor.Diameter)?color=green",
    ]
    if options.graph is not None:
        graph_descs = ast.literal_eval(options.graph)

    # Generate motion data table
    motion_data = generate_motion_csv(amanager, [graph_descs])

    # Print or save the data table
    if options.output is None:
        print(motion_data)
    else:
        motion_data.to_csv(options.output, index=False)

if __name__ == '__main__':
    main()
