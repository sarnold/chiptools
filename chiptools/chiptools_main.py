# Copyright 2015 Peter Bennett
# Copyright 2015 PerkinElmer
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
import sys

from chiptools import __version__
from chiptools.core.cli import CommandLine


def main():
    """
    Launch the Framework application command line interface.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-v', '--version', help='Display version info', action='store_true'
    )

    options = parser.parse_args()

    if options.version:
        print('[chiptools {}]'.format(__version__))
        sys.exit(0)

    main = CommandLine()
    main.cmdloop()
    logging.shutdown()


if __name__ == '__main__':
    main()
