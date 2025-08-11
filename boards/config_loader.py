import yaml
from boards.arguments import args
import os


def load_config(yml_path):
    with open(yml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

if args.config:
    configFile = args.config
else:
    configFile = "config.yml"
config = load_config(configFile)


masterDir = config['masterDir']
if args.config: masterDir = os.path.join(os.dirname(masterDir), os.basename(config))

suffix = ''

if args.upload: suffix = '_upload'
elif args.imageLists: suffix = '_imglist'

outputDir = masterDir + suffix
