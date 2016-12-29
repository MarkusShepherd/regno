# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from importlib import import_module

def class_from_path(path):
    parts = path.split('.')

    try:
        if len(parts) == 1:
            return globals().get(path) or import_module(path)

        else:
            obj = import_module(parts[0])
            for part in parts[1:]:
                if not obj:
                    break
                obj = getattr(obj, part, None)
            return obj

    except ImportError:
        return None
