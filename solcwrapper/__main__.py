#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
SOLCWrapper

"""
import logging
from . import solcwrapper


if __name__ == "__main__":
    logging.basicConfig(format='[%(filename)s - %(funcName)20s() ][%(levelname)8s] %(message)s',
                        level=logging.INFO)
    solcwrapper.main()
