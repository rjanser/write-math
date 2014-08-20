#!/usr/bin/env python

import os
import logging
import sys
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)
import yaml
import time
# my modules
import utils
import preprocess_dataset
import create_pfiles


def update_model_description_file(model_description_file, raw_data):
    from collections import OrderedDict

    def ordered_load(stream, Loader=yaml.Loader,
                     object_pairs_hook=OrderedDict):
        class OrderedLoader(Loader):
            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return object_pairs_hook(loader.construct_pairs(node))
        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_mapping)
        return yaml.load(stream, OrderedLoader)

    def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
        class OrderedDumper(Dumper):
            pass

        def _dict_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                data.items())
        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        return yaml.dump(data, stream, OrderedDumper, **kwds)

    # Read the model description file
    with open(args.model_description_file, 'r') as ymlfile:
        md = ordered_load(ymlfile, yaml.SafeLoader)

    # Set new raw data
    md['data-source'] = "archive/" + \
                        "archive/".join(raw_data.split("archive/")[1:])
    # Get time string
    time_prefix = time.strftime("%Y-%m-%d-%H-%M")
    # Update 'preprocessed'
    md['preprocessed'] = ("archive/datasets/%s-"
                          "handwriting_datasets-preprocessed"
                          ".pickle") % time_prefix
    # Update data
    md['data']['training'] = "archive/pfiles/%s-traindata.pfile" % time_prefix
    md['data']['validating'] = "archive/pfiles/%s-validdata.pfile" % \
        time_prefix
    md['data']['testing'] = "archive/pfiles/%s-testdata.pfile" % time_prefix
    # Write the file
    with open(model_description_file, 'w') as ymlfile:
        ymlfile.write(ordered_dump(md,
                                   Dumper=yaml.SafeDumper,
                                   default_flow_style=False,
                                   indent=4).replace('-   ', '  - '))


def main(model_description_file, latest_data):
    # Read the model description file
    with open(model_description_file, 'r') as ymlfile:
        model_description = yaml.load(ymlfile)

    if model_description['model']['type'] != 'mlp':
        logging.info("The type of your model is '%s'.",
                     model_description['model']['type'])
        return 0

    # Make sure the user really wants to do this
    logging.info("The model uses the raw dataset '%s'. "
                 "The latest raw dataset is '%s'. ",
                 model_description['data-source'],
                 latest_data)
    refresh_it = utils.query_yes_no("Do you want to refresh the model file?",
                                    "no")
    if refresh_it:
        # Refresh the model
        update_model_description_file(model_description_file, latest_data)

    # Check if the data source is the latest one
    if latest_data == model_description['data-source']:
        logging.info("The latest raw dataset is '%s'. "
                     "That was already used for the model '%s'",
                     latest_data,
                     model_description_file)
        return 0

    # Preprocessing
    refresh_it = utils.query_yes_no("Do you want to refresh the "
                                    "preprocessing file?",
                                    "no")
    if refresh_it:
        preprocess_dataset.main(model_description_file)

    # Create pfiles
    refresh_it = utils.query_yes_no("Do you want to refresh the pfiles?",
                                    "no")
    if refresh_it:
        create_pfiles.main(model_description_file)


if __name__ == '__main__':
    PROJECT_ROOT = utils.get_project_root()

    # Get latest model description file
    models_folder = os.path.join(PROJECT_ROOT, "archive/models")
    latest_model = utils.get_latest_in_folder(models_folder, ".yml")

    # Get latest raw data file
    models_folder = os.path.join(PROJECT_ROOT, "archive/datasets")
    latest_data = utils.get_latest_in_folder(models_folder, "raw.pickle")

    # Get command line arguments
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model_description_file",
                        dest="model_description_file",
                        help="where is the model description YAML file?",
                        metavar="FILE",
                        type=lambda x: utils.is_valid_file(parser, x),
                        default=latest_model)
    parser.add_argument("-d", "--dataset",
                        dest="dataset",
                        help="which new dataset should be used?",
                        metavar="FILE",
                        type=lambda x: utils.is_valid_file(parser, x),
                        default=latest_data)
    args = parser.parse_args()
    main(args.model_description_file, args.dataset)
