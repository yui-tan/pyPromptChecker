# -*- coding: utf-8 -*-

import sys
import os

package_root = os.path.dirname(os.path.abspath(__file__))

if package_root not in sys.path:
    sys.path.insert(0, package_root)
