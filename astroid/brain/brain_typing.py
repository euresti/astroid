# Copyright (c) 2016 David Euresti <david@dropbox.com>

"""Astroid hooks for typing.py support."""

from textwrap import dedent

from astroid import (
    MANAGER,
    register_module_extender,
    inference_tip,
    UseInferenceDefault
)
from astroid import nodes, extract_node
from astroid.builder import AstroidBuilder

def infer_NamedTuple(node, context=None):
    """Infer a typing.NamedTuple(...) call."""
    # This is essentially a namedtuple with different arguments
    # so we extract the args and infer a named tuple.
    if len(node.args) != 2:
        raise UseInferenceDefault

    typename = node.args[0].as_string()
    names = []
    try:
        for elt in node.args[1].elts:
            if len(elt.elts) != 2:
                raise UseInferenceDefault
            names.append(elt.elts[0].as_string())
    except AttributeError:
        raise UseInferenceDefault

    node = extract_node('namedtuple(%(typename)s, (%(fields)s,)) ' %
        {'typename': typename, 'fields': ",".join(names)})
    return node.infer(context=context)

def typing_transform():
    """Help astroid infer the typing module.

    The typing module has a lot of really complicated metaclasses that are
    difficult to infer.  This makes them inferable and simpifies them for naming
    convention purposes.

    For example:
        MyDict = Dict[str, str]
        MyOptions = Union[int, str]

    The first one returns a class in the real world, yet the 2nd one returns an
    instance of the _Union class.  However they both want to be named as if they
    were classes.  This applies to all of them.

    """
    return AstroidBuilder(MANAGER).string_build(dedent('''
    import six

    class GenericMeta(type):
        def __getitem__(cls, params):
            return cls

    @six.add_metaclass(GenericMeta)
    class Generic(object):
        pass

    @six.add_metaclass(GenericMeta)
    class Callable(object):
        pass

    @six.add_metaclass(GenericMeta)
    class Tuple(tuple):
        pass

    @six.add_metaclass(GenericMeta)
    class Union(object):
        pass

    @six.add_metaclass(GenericMeta)
    class Optional(object):
        pass

    def NewType(name, tp):
        return tp

    '''))

register_module_extender(MANAGER, 'typing', typing_transform)
MANAGER.register_transform(
    nodes.Call,
    inference_tip(infer_NamedTuple),
    lambda node: getattr(node.func, 'name',
                         getattr(node.func, 'attrname', None)) == 'NamedTuple')

