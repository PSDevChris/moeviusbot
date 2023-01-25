'''This tool contains functions to help loading/saving Python dicts from/to .json-files'''

import json
import logging
import os


def load_file(file_path: str) -> dict:
    '''Opens the file under the specified path and converts it to a dict.

    If the file could not be found or the file path is empty, the function returns None.'''

    if str(file_path) == '':
        logging.warning('Can\'t save file, file_path is empty.')
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            logging.info('File %s opened succesfully.', file_path)
            return json.load(file)
    except OSError as err_msg:
        logging.error(
            'Could not read file %s! Exception: %s', file_path, err_msg
        )
        return None


def save_file(file_path: str, content: dict) -> bool:
    '''Writes the content dict into a file under the specified path.

    If the file could not be found or the file path is empty, the function returns False,
    otherwise it returns True.'''

    if str(file_path) == '':
        logging.warning('Can\'t save file, file_path is empty.')
        return False

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(content, file)
            logging.info('File %s saved succesfully.', file_path)
            return True
    except OSError as err_msg:
        logging.error(
            'Could not write file %s! Exception: %s', file_path, err_msg
        )
        return False


class DictFile(dict):
    '''Extension to the dict type to automatically save the dictionary as a .json-file
    when it is updated. Additionally new dicts can directly by populated with data from
    a file.'''

    def __init__(
        self,
        name: str,
        /,
        suffix: str = '.json',
        path: str = 'json/',
        load_from_file: bool = True
    ) -> None:
        '''Initializes a new dict which is linked to a file.

        By default, it tries to load data from the file when created.
        The usual path for this is ./json/name.json and if the path
        does not exist, the dicts will be created.'''

        logging.debug(
            'Initializing DictFile %s ...', name
        )

        super().__init__()
        self.file_name = path + name + suffix

        if not os.path.exists(path):
            os.makedirs(path)
            logging.debug(
                'Created dirs for path %s', path
            )

        if load_from_file:
            if (data_from_file := load_file(self.file_name)) is None:
                logging.debug(
                    'Can\'t load data from file %s', self.file_name
                )
            else:
                logging.debug(
                    'Loaded data from file %s. %s',
                    self.file_name, str(data_from_file)
                )
                self.update(data_from_file)

        logging.info(
            'DictFile %s initialized succesfully.', self.file_name
        )

    def __setitem__(self, __key, __value) -> None:
        super().__setitem__(__key, __value)

        logging.debug(
            'DictFile %s item set. %s: %s',
            self.file_name, __key, __value
        )

        save_file(self.file_name, self)

    def update(self, __m) -> None:
        super().update(__m)

        logging.debug(
            "DictFile %s updated. %s",
            self.file_name, str(self)
        )

        save_file(self.file_name, self)

    def pop(self, key) -> None:
        item = super().pop(key)

        logging.debug(
            "DictFile %s popped. %s",
            self.file_name, str(item)
        )

        save_file(self.file_name, self)

        return item
