#!/usr/bin/env python

import datetime
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

def plot(plotable_data,config):            
    """
    plotable_data is a list of tuples with the following structure:
    (time_bucket, count, eta)
    """
    use_x_var = True
    if "use_x_var" in config:
        use_x_var = bool(config["use_x_var"])
    if "start_time" in config and "stop_time" in config:
        start_tm = datetime.datetime.strptime(config["start_time"],"%Y%m%d%H%M")
        stop_tm = datetime.datetime.strptime(config["stop_time"],"%Y%m%d%H%M")
        data = [(tup[0].start_time,tup[1],tup[2]) for tup in plotable_data if tup[0].start_time > start_tm and tup[0].stop_time < stop_tm ]
    else:
        data = [(tup[0].start_time,tup[1],tup[2]) for tup in plotable_data] 

    tbs = [tup[0] for tup in data]
    cts = [tup[1] for tup in data]
    eta = [tup[2] for tup in data]
    if cts == []:
        return -1
    max_cts = max(cts)
    min_cts = min(cts)
    
    fig = plt.figure()
    plt.title(config["plot_title"])
    
    ax1 = fig.add_subplot(111)
    if use_x_var:
        ax1.plot(tbs,cts,'b.',tbs,cts,'k-') 
    else:
        ax1.plot(cts,'b.',cts,'k-') 
    # fancify
    ax1.set_ylabel("counts",color='b',fontsize=10)
    ax1.set_ylim(min_cts*0.9,max_cts*1.7)
    for tl in ax1.get_yticklabels():
        tl.set_color('b')
        tl.set_fontsize(10)
    plt.locator_params(axis = 'y', nbins = 4)
    ax1.set_xlabel("time ({} bins)".format(config["x_unit"].rstrip('s')))
    formatter = mdates.DateFormatter('%Y-%m-%d')
    ax1.xaxis.set_major_formatter( formatter ) 
    days = mdates.DayLocator()
    ax1.xaxis.set_major_locator(days) 
    fig.autofmt_xdate()

    ax2 = ax1.twinx()
    plotter="plot"
    if config["logscale_eta"]:
        plotter="semilogy"
    if use_x_var:
        getattr(ax2,plotter)(tbs,eta,'r')
    else:
        getattr(ax2,plotter)(eta,'r')
    min_eta = 0
    if min(eta) > 0:
        min_eta = min(eta) * 0.9
    ax2.set_ylim(min_eta, max(eta)*1.1)
    ax2.set_ylabel("eta",color='r',fontsize=10)
    for tl in ax2.get_yticklabels():
        tl.set_color('r')
        tl.set_fontsize(10)
    
    plt.savefig(config["plot_dir"] + "/{}.{}".format(config["plot_title"],config["plot_extension"]),dpi=400) 


if __name__ == "__main__":
    
    import argparse
    import ConfigParser
    import pickle
    import logging
    
    import models
    from analyze import analyze as analyzer

    logr = logging.getLogger("analyzer")
    #logr.setLevel(logging.DEBUG)
    if logr.handlers == []:
        fmtr = logging.Formatter('%(asctime)s %(name)s - %(levelname)s - %(message)s') 
        hndlr = logging.StreamHandler()
        hndlr.setFormatter(fmtr)
        logr.addHandler(hndlr) 

    parser = argparse.ArgumentParser()
    parser.add_argument("-i",dest="input_file_name",default="output.pkl") 
    parser.add_argument("-c",dest="config_file_name",default="config.cfg",help="get configuration from this file")
    parser.add_argument("-t",dest="plot_title",default=None) 
    parser.add_argument("-d",dest="analyzed_data_file",default=None) 
    parser.add_argument("-v",dest="verbose",action="store_true",default=False) 
    args = parser.parse_args()

    plot_config = {}
    
    config = ConfigParser.ConfigParser()
    config.read(args.config_file_name)
    model_name = config.get("analyze","model_name")
    model_config = dict(config.items(model_name + "_model")) 
    if config.has_section("plot"):
        plot_config = dict(config.items("plot"))
    else:
        plot_config["plot_title"] = "output"
        plot_config["plot_dir"] = "."
    rebin_items = config.items("rebin")
    rebin_config = dict(rebin_items)
    rule_name = rebin_config["rule_name"]
    plot_config["x_unit"] = str(rebin_config["n_binning_unit"]) + " " + str(rebin_config["binning_unit"])
    if "logscale_eta" in plot_config:
        plot_config["logscale_eta"] = config.getboolean("plot","logscale_eta")
    else:
        plot_config["logscale_eta"] = False
   
    if args.plot_title is not None:
        plot_config["plot_title"] = args.plot_title
    if args.verbose is True:
        logr.setLevel(logging.DEBUG)

    model = getattr(models,model_name)(config=model_config) 
    if args.analyzed_data_file is not None:
        plotable_data = pickle.load(open(args.analyzed_data_file))[rule_name]
    else:
        generator = pickle.load(open(args.input_file_name))[rule_name]
        plotable_data = analyzer(generator,model,None,None,logr)
    
    plot(plotable_data,plot_config)