"""List primitive ops."""

from typing import List

from mypyc.ir.ops import ERR_MAGIC, ERR_NEVER, ERR_FALSE, EmitterInterface
from mypyc.ir.rtypes import (
    int_rprimitive, short_int_rprimitive, list_rprimitive, object_rprimitive, bool_rprimitive
)
from mypyc.primitives.registry import (
    name_ref_op, binary_op, func_op, method_op, custom_op, name_emit,
    call_emit, call_negative_bool_emit,
)


name_ref_op('builtins.list',
            result_type=object_rprimitive,
            error_kind=ERR_NEVER,
            emit=name_emit('(PyObject *)&PyList_Type'),
            is_borrowed=True)

to_list = func_op(
    name='builtins.list',
    arg_types=[object_rprimitive],
    result_type=list_rprimitive,
    error_kind=ERR_MAGIC,
    emit=call_emit('PySequence_List'))


def emit_new(emitter: EmitterInterface, args: List[str], dest: str) -> None:
    # TODO: This would be better split into multiple smaller ops.
    emitter.emit_line('%s = PyList_New(%d); ' % (dest, len(args)))
    emitter.emit_line('if (likely(%s != NULL)) {' % dest)
    for i, arg in enumerate(args):
        emitter.emit_line('PyList_SET_ITEM(%s, %s, %s);' % (dest, i, arg))
    emitter.emit_line('}')


new_list_op = custom_op(arg_types=[object_rprimitive],
                        result_type=list_rprimitive,
                        is_var_arg=True,
                        error_kind=ERR_MAGIC,
                        steals=True,
                        format_str='{dest} = [{comma_args}]',
                        emit=emit_new)


list_get_item_op = method_op(
    name='__getitem__',
    arg_types=[list_rprimitive, int_rprimitive],
    result_type=object_rprimitive,
    error_kind=ERR_MAGIC,
    emit=call_emit('CPyList_GetItem'))


# Version with no int bounds check for when it is known to be short
method_op(
    name='__getitem__',
    arg_types=[list_rprimitive, short_int_rprimitive],
    result_type=object_rprimitive,
    error_kind=ERR_MAGIC,
    emit=call_emit('CPyList_GetItemShort'),
    priority=2)

# This is unsafe because it assumes that the index is a non-negative short integer
# that is in-bounds for the list.
list_get_item_unsafe_op = custom_op(
    name='__getitem__',
    arg_types=[list_rprimitive, short_int_rprimitive],
    result_type=object_rprimitive,
    error_kind=ERR_NEVER,
    format_str='{dest} = {args[0]}[{args[1]}] :: unsafe list',
    emit=call_emit('CPyList_GetItemUnsafe'))


list_set_item_op = method_op(
    name='__setitem__',
    arg_types=[list_rprimitive, int_rprimitive, object_rprimitive],
    steals=[False, False, True],
    result_type=bool_rprimitive,
    error_kind=ERR_FALSE,
    emit=call_emit('CPyList_SetItem'))


list_append_op = method_op(
    name='append',
    arg_types=[list_rprimitive, object_rprimitive],
    result_type=bool_rprimitive,
    error_kind=ERR_FALSE,
    emit=call_negative_bool_emit('PyList_Append'))

list_extend_op = method_op(
    name='extend',
    arg_types=[list_rprimitive, object_rprimitive],
    result_type=object_rprimitive,
    error_kind=ERR_MAGIC,
    emit=call_emit('CPyList_Extend'))

list_pop_last = method_op(
    name='pop',
    arg_types=[list_rprimitive],
    result_type=object_rprimitive,
    error_kind=ERR_MAGIC,
    emit=call_emit('CPyList_PopLast'))

list_pop = method_op(
    name='pop',
    arg_types=[list_rprimitive, int_rprimitive],
    result_type=object_rprimitive,
    error_kind=ERR_MAGIC,
    emit=call_emit('CPyList_Pop'))

method_op(
    name='count',
    arg_types=[list_rprimitive, object_rprimitive],
    result_type=short_int_rprimitive,
    error_kind=ERR_MAGIC,
    emit=call_emit('CPyList_Count'))

binary_op(op='*',
          arg_types=[list_rprimitive, int_rprimitive],
          result_type=list_rprimitive,
          error_kind=ERR_MAGIC,
          format_str='{dest} = {args[0]} * {args[1]} :: list',
          emit=call_emit("CPySequence_Multiply"))

binary_op(op='*',
          arg_types=[int_rprimitive, list_rprimitive],
          result_type=list_rprimitive,
          error_kind=ERR_MAGIC,
          format_str='{dest} = {args[0]} * {args[1]} :: list',
          emit=call_emit("CPySequence_RMultiply"))


def emit_len(emitter: EmitterInterface, args: List[str], dest: str) -> None:
    temp = emitter.temp_name()
    emitter.emit_declaration('Py_ssize_t %s;' % temp)
    emitter.emit_line('%s = PyList_GET_SIZE(%s);' % (temp, args[0]))
    emitter.emit_line('%s = CPyTagged_ShortFromSsize_t(%s);' % (dest, temp))


list_len_op = func_op(name='builtins.len',
                      arg_types=[list_rprimitive],
                      result_type=short_int_rprimitive,
                      error_kind=ERR_NEVER,
                      emit=emit_len)
