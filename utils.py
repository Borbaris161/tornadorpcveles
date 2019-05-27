#!/usr/bin/env python
# -*- coding: utf-8

import inspect


def getcallargs(func, *positional, **named):
    args, varargs, varkw, defaults\
        , kwonlyargs, kwdefaults, annotations = inspect.getfullargspec(func)

    final_kwargs = {}
    extra_args = []
    has_self = inspect.ismethod(func) and func.__self__ is not None
    if has_self:
        args.pop(0)
    if named:
        for key, value in named.iteritems():
            arg_key = None
            try:
                arg_key = args[args.index(key)]
            except ValueError:
                if not varkw:
                    raise TypeError("Keyword argument '%s' not valid" % key)
            if key in final_kwargs.keys():
                message = "Keyword argument '%s' used more than once" % key
                raise TypeError(message)
            final_kwargs[key] = value
    else:
        for i in range(len(positional)):
            value = positional[i]
            arg_key = None
            try:
                arg_key = args[i]
            except IndexError:
                if not varargs:
                    raise TypeError("Too many positional arguments")
            if arg_key:
                final_kwargs[arg_key] = value
            else:
                extra_args.append(value)
    if defaults:
        for kwarg, default in zip(args[-len(defaults):], defaults):
            final_kwargs.setdefault(kwarg, default)
    for arg in args:
        if arg not in final_kwargs:
            raise TypeError("Not all arguments supplied. (%s)", arg)
    return final_kwargs, extra_args
