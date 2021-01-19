import os
import json
import logging
from typing import List

logger = logging.getLogger(__name__)


class ConfigError(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)


# TODO: make it a singleton
class ConfigManager:
    """Loads config file and gives access to the data"""

    config_data = None

    def __init__(self, configfile="config.json"):

        # Load config data
        try:
            with open(configfile) as config_file:
                self.config_data = json.load(config_file)
        except:
            logger.error("Error opening config file: {}".format(configfile))
            raise ConfigError("Could not load config data from {}".format(configfile))

    # Return searched json data
    def get(self, group, key):

        try:
            value = self.config_data[group][key]
            logger.debug("Get config data: {} -> {} with {}".format(group, key, value))
        except:
            logger.error("Getting config data {} -> {} without success".format(group, key))
            raise ConfigError("Could not get config data {} -> {}".format(group, key))

        # Return searched config data value
        return value

    # Overwrite config data
    def set(self, group, key, value):

        try:
            self.config_data[group][key] = value
            logger.debug("Overwriting config data {} -> {} with {}".format(group, key, value))
        except:
            logger.error("Overwriting config data {} -> {} without success".format(group, key))
            raise ConfigError("Could not overwrite config data {} -> {}".format(group, key))

    @staticmethod
    def reconstruct_path(base_path, relative_path: List[str]):
        for d in relative_path:
            base_path = os.path.join(base_path, d)
        return base_path