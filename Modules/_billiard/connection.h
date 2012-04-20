/*
 * Definition of a `Connection` type.
 * Used by `socket_connection.c` and `pipe_connection.c`.
 *
 * connection.h
 *
 * Copyright (c) 2006-2008, R Oudkerk --- see COPYING.txt
 */

#ifndef CONNECTION_H
#define CONNECTION_H

/*
 * Read/write flags
 */

#define READABLE 1
#define WRITABLE 2

#define CHECK_READABLE(self) \
    if (!(self->flags & READABLE)) { \
    PyErr_SetString(PyExc_IOError, "connection is write-only"); \
    return NULL; \
    }

#define CHECK_WRITABLE(self) \
    if (!(self->flags & WRITABLE)) { \
    PyErr_SetString(PyExc_IOError, "connection is read-only"); \
    return NULL; \
    }

/*
 * Allocation and deallocation
 */

static PyObject *
Billiard_connection_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    BilliardConnectionObject *self;
    HANDLE handle;
    BOOL readable = TRUE, writable = TRUE;

    static char *kwlist[] = {"handle", "readable", "writable", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, F_HANDLE "|ii", kwlist,
                                     &handle, &readable, &writable))
        return NULL;

    if (handle == INVALID_HANDLE_VALUE || (Py_ssize_t)handle < 0) {
        PyErr_Format(PyExc_IOError, "invalid handle %zd",
                     (Py_ssize_t)handle);
        return NULL;
    }

    if (!readable && !writable) {
        PyErr_SetString(PyExc_ValueError,
                        "either readable or writable must be true");
        return NULL;
    }

    self = PyObject_New(BilliardConnectionObject, type);
    if (self == NULL)
        return NULL;

    self->weakreflist = NULL;
    self->handle = handle;
    self->flags = 0;

    if (readable)
        self->flags |= READABLE;
    if (writable)
        self->flags |= WRITABLE;
    assert(self->flags >= 1 && self->flags <= 3);

    return (PyObject*)self;
}

static void
Billiard_connection_dealloc(BilliardConnectionObject* self)
{
    if (self->weakreflist != NULL)
        PyObject_ClearWeakRefs((PyObject*)self);

    if (self->handle != INVALID_HANDLE_VALUE) {
        Py_BEGIN_ALLOW_THREADS
        CLOSE(self->handle);
        Py_END_ALLOW_THREADS
    }
    PyObject_Del(self);
}

/*
 * Functions for transferring buffers
 */

static PyObject *
Billiard_connection_sendbytes(BilliardConnectionObject *self, PyObject *args)
{
    char *buffer;
    Py_ssize_t length, offset=0, size=PY_SSIZE_T_MIN;
    int res;

    if (!PyArg_ParseTuple(args, F_RBUFFER "#|" F_PY_SSIZE_T F_PY_SSIZE_T,
                          &buffer, &length, &offset, &size))
        return NULL;

    CHECK_WRITABLE(self);

    if (offset < 0) {
        PyErr_SetString(PyExc_ValueError, "offset is negative");
        return NULL;
    }
    if (length < offset) {
        PyErr_SetString(PyExc_ValueError, "buffer length < offset");
        return NULL;
    }

    if (size == PY_SSIZE_T_MIN) {
        size = length - offset;
    } else {
        if (size < 0) {
            PyErr_SetString(PyExc_ValueError, "size is negative");
            return NULL;
        }
        if (offset + size > length) {
            PyErr_SetString(PyExc_ValueError,
                            "buffer length < offset + size");
            return NULL;
        }
    }

    res = Billiard_conn_send_string(self, buffer + offset, size);

    if (res < 0) {
        if (PyErr_Occurred())
            return NULL;
        else
            return Billiard_SetError(PyExc_IOError, res);
    }

    Py_RETURN_NONE;
}

static PyObject *
Billiard_connection_recvbytes(BilliardConnectionObject *self, PyObject *args)
{
    char *freeme = NULL;
    Py_ssize_t res, maxlength = PY_SSIZE_T_MAX;
    PyObject *result = NULL;

    if (!PyArg_ParseTuple(args, "|" F_PY_SSIZE_T, &maxlength))
        return NULL;

    CHECK_READABLE(self);

    if (maxlength < 0) {
        PyErr_SetString(PyExc_ValueError, "maxlength < 0");
        return NULL;
    }

    res = Billiard_conn_recv_string(self, self->buffer, CONNECTION_BUFFER_SIZE,
                           &freeme, maxlength);

    if (res < 0) {
        if (res == MP_BAD_MESSAGE_LENGTH) {
            if ((self->flags & WRITABLE) == 0) {
                Py_BEGIN_ALLOW_THREADS
                CLOSE(self->handle);
                Py_END_ALLOW_THREADS
                self->handle = INVALID_HANDLE_VALUE;
            } else {
                self->flags = WRITABLE;
            }
        }
        Billiard_SetError(PyExc_IOError, res);
    } else {
        if (freeme == NULL) {
            result = PyString_FromStringAndSize(self->buffer, res);
        } else {
            result = PyString_FromStringAndSize(freeme, res);
            PyMem_Free(freeme);
        }
    }

    return result;
}

#ifdef HAS_NEW_PY_BUFFER
static PyObject *
Billiard_connection_recvbytes_into(BilliardConnectionObject *self, PyObject *args)
{
    char *freeme = NULL, *buffer = NULL;
    Py_ssize_t res, length, offset = 0;
    PyObject *result = NULL;
    Py_buffer pbuf;

    CHECK_READABLE(self);

    if (!PyArg_ParseTuple(args, "w*|" F_PY_SSIZE_T,
                          &pbuf, &offset))
        return NULL;

    buffer = pbuf.buf;
    length = pbuf.len;

    if (offset < 0) {
        PyErr_SetString(PyExc_ValueError, "negative offset");
        goto _error;
    }

    if (offset > length) {
        PyErr_SetString(PyExc_ValueError, "offset too large");
        goto _error;
    }

    res = Billiard_conn_recv_string(self, buffer+offset, length-offset,
                           &freeme, PY_SSIZE_T_MAX);

    if (res < 0) {
        if (res == MP_BAD_MESSAGE_LENGTH) {
            if ((self->flags & WRITABLE) == 0) {
                Py_BEGIN_ALLOW_THREADS
                CLOSE(self->handle);
                Py_END_ALLOW_THREADS
                self->handle = INVALID_HANDLE_VALUE;
            } else {
                self->flags = WRITABLE;
            }
        }
        Billiard_SetError(PyExc_IOError, res);
    } else {
        if (freeme == NULL) {
            result = PyInt_FromSsize_t(res);
        } else {
            result = PyObject_CallFunction(BufferTooShort,
                                           F_RBUFFER "#",
                                           freeme, res);
            PyMem_Free(freeme);
            if (result) {
                PyErr_SetObject(BufferTooShort, result);
                Py_DECREF(result);
            }
            goto _error;
        }
    }

_cleanup:
    PyBuffer_Release(&pbuf);
    return result;

_error:
    result = NULL;
    goto _cleanup;
}
# else /* old buffer protocol */

static PyObject *
Billiard_connection_recvbytes_into(BilliardConnectionObject *self, PyObject *args)
{
    char *freeme = NULL, *buffer = NULL;
    Py_ssize_t length = 0, res, offset = 0;
    PyObject *result = NULL;

    CHECK_READABLE(self);

    if (!PyArg_ParseTuple(args, "w#|", F_PY_SSIZE_T,
            &buffer, &length, &offset))
        return NULL;

    if (offset < 0) {
        PyErr_SetString(PyExc_ValueError, "negative offset");
        goto _error;
    }

    if (offset > 0) {
        PyErr_SetString(PyExc_ValueError, "offset out of bounds");
        goto _error;
    }

    res = Billiard_conn_recv_string(self, buffer+offset, length-offset,
            &freeme, PY_SSIZE_T_MAX);
    if (res < 0) {
       if (res == MP_BAD_MESSAGE_LENGTH) {
            if ((self->flags & WRITABLE) == 0) {
                Py_BEGIN_ALLOW_THREADS
                CLOSE(self->handle);
                Py_END_ALLOW_THREADS;
                self->handle = INVALID_HANDLE_VALUE;
            } else {
                self->flags = WRITABLE;
            }
       }
       Billiard_SetError(PyExc_IOError, res);
    } else {
        if (freeme == NULL) {
            result = PyInt_FromSsize_t(res);
        } else {
            result = PyObject_CallFunction(BufferTooShort,
                    F_RBUFFER "#",
                    freeme, res);
            PyMem_Free(freeme);
            if (result) {
                PyErr_SetObject(BufferTooShort, result);
                Py_DECREF(result);
            }
            goto _error;
        }
    }

_cleanup:
    return result;

_error:
    result = NULL;
    goto _cleanup;

}
# endif /* buffer */


/*
 * Functions for transferring objects
 */

static PyObject *
Billiard_connection_send_obj(BilliardConnectionObject *self, PyObject *obj)
{
    char *buffer;
    int res;
    Py_ssize_t length;
    PyObject *pickled_string = NULL;

    CHECK_WRITABLE(self);

    pickled_string = PyObject_CallFunctionObjArgs(pickle_dumps, obj,
                                                  pickle_protocol, NULL);
    if (!pickled_string)
        goto failure;

    if (PyString_AsStringAndSize(pickled_string, &buffer, &length) < 0)
        goto failure;

    res = Billiard_conn_send_string(self, buffer, (int)length);

    if (res < 0) {
        Billiard_SetError(PyExc_IOError, res);
        goto failure;
    }

    Py_XDECREF(pickled_string);
    Py_RETURN_NONE;

  failure:
    Py_XDECREF(pickled_string);
    return NULL;
}

static PyObject *
Billiard_connection_recv_obj(BilliardConnectionObject *self)
{
    char *freeme = NULL;
    Py_ssize_t res;
    PyObject *temp = NULL, *result = NULL;

    CHECK_READABLE(self);

    res = Billiard_conn_recv_string(self, self->buffer, CONNECTION_BUFFER_SIZE,
                           &freeme, PY_SSIZE_T_MAX);

    if (res < 0) {
        if (res == MP_BAD_MESSAGE_LENGTH) {
            if ((self->flags & WRITABLE) == 0) {
                Py_BEGIN_ALLOW_THREADS
                CLOSE(self->handle);
                Py_END_ALLOW_THREADS
                self->handle = INVALID_HANDLE_VALUE;
            } else {
                self->flags = WRITABLE;
            }
        }
        Billiard_SetError(PyExc_IOError, res);
    } else {
        if (freeme == NULL) {
            temp = PyString_FromStringAndSize(self->buffer, res);
        } else {
            temp = PyString_FromStringAndSize(freeme, res);
            PyMem_Free(freeme);
        }
    }

    if (temp)
        result = PyObject_CallFunctionObjArgs(pickle_loads,
                                              temp, NULL);
    Py_XDECREF(temp);
    return result;
}

/*
 * Other functions
 */

static PyObject *
Billiard_connection_poll(BilliardConnectionObject *self, PyObject *args)
{
    PyObject *timeout_obj = NULL;
    double timeout = 0.0;
    int res;

    CHECK_READABLE(self);

    if (!PyArg_ParseTuple(args, "|O", &timeout_obj))
        return NULL;

    if (timeout_obj == NULL) {
        timeout = 0.0;
    } else if (timeout_obj == Py_None) {
        timeout = -1.0;                                 /* block forever */
    } else {
        timeout = PyFloat_AsDouble(timeout_obj);
        if (PyErr_Occurred())
            return NULL;
        if (timeout < 0.0)
            timeout = 0.0;
    }

    Py_BEGIN_ALLOW_THREADS
    res = Billiard_conn_poll(self, timeout, _save);
    Py_END_ALLOW_THREADS

    switch (res) {
    case TRUE:
        Py_RETURN_TRUE;
    case FALSE:
        Py_RETURN_FALSE;
    default:
        return Billiard_SetError(PyExc_IOError, res);
    }
}

static PyObject *
Billiard_connection_fileno(BilliardConnectionObject* self)
{
    if (self->handle == INVALID_HANDLE_VALUE) {
        PyErr_SetString(PyExc_IOError, "handle is invalid");
        return NULL;
    }
    return PyInt_FromLong((long)self->handle);
}

static PyObject *
Billiard_connection_close(BilliardConnectionObject *self)
{
    if (self->handle != INVALID_HANDLE_VALUE) {
        Py_BEGIN_ALLOW_THREADS
        CLOSE(self->handle);
        Py_END_ALLOW_THREADS
        self->handle = INVALID_HANDLE_VALUE;
    }

    Py_RETURN_NONE;
}

static PyObject *
Billiard_connection_repr(BilliardConnectionObject *self)
{
    static char *conn_type[] = {"read-only", "write-only", "read-write"};

    assert(self->flags >= 1 && self->flags <= 3);
    return FROM_FORMAT("<%s %s, handle %zd>",
                       conn_type[self->flags - 1],
                       CONNECTION_NAME, (Py_ssize_t)self->handle);
}

/*
 * Getters and setters
 */

static PyObject *
Billiard_connection_closed(BilliardConnectionObject *self, void *closure)
{
    return PyBool_FromLong((long)(self->handle == INVALID_HANDLE_VALUE));
}

static PyObject *
Billiard_connection_readable(BilliardConnectionObject *self, void *closure)
{
    return PyBool_FromLong((long)(self->flags & READABLE));
}

static PyObject *
Billiard_connection_writable(BilliardConnectionObject *self, void *closure)
{
    return PyBool_FromLong((long)(self->flags & WRITABLE));
}

/*
 * Tables
 */

static PyMethodDef Billiard_connection_methods[] = {
    {"send_bytes", (PyCFunction)Billiard_connection_sendbytes, METH_VARARGS,
     "send the byte data from a readable buffer-like object"},
    {"recv_bytes", (PyCFunction)Billiard_connection_recvbytes, METH_VARARGS,
     "receive byte data as a string"},
    {"recv_bytes_into",(PyCFunction)Billiard_connection_recvbytes_into,METH_VARARGS,
     "receive byte data into a writeable buffer-like object\n"
     "returns the number of bytes read"},

    {"send", (PyCFunction)Billiard_connection_send_obj, METH_O,
     "send a (picklable) object"},
    {"recv", (PyCFunction)Billiard_connection_recv_obj, METH_NOARGS,
     "receive a (picklable) object"},

    {"poll", (PyCFunction)Billiard_connection_poll, METH_VARARGS,
     "whether there is any input available to be read"},
    {"fileno", (PyCFunction)Billiard_connection_fileno, METH_NOARGS,
     "file descriptor or handle of the connection"},
    {"close", (PyCFunction)Billiard_connection_close, METH_NOARGS,
     "close the connection"},

    {NULL}  /* Sentinel */
};

static PyGetSetDef Billiard_connection_getset[] = {
    {"closed", (getter)Billiard_connection_closed, NULL,
     "True if the connection is closed", NULL},
    {"readable", (getter)Billiard_connection_readable, NULL,
     "True if the connection is readable", NULL},
    {"writable", (getter)Billiard_connection_writable, NULL,
     "True if the connection is writable", NULL},
    {NULL}
};

/*
 * Connection type
 */

PyDoc_STRVAR(Billiard_connection_doc,
             "Connection type whose constructor signature is\n\n"
             "    Connection(handle, readable=True, writable=True).\n\n"
             "The constructor does *not* duplicate the handle.");

PyTypeObject CONNECTION_TYPE = {
    PyVarObject_HEAD_INIT(NULL, 0)
    /* tp_name           */ "_billiard." CONNECTION_NAME,
    /* tp_basicsize      */ sizeof(BilliardConnectionObject),
    /* tp_itemsize       */ 0,
    /* tp_dealloc        */ (destructor)Billiard_connection_dealloc,
    /* tp_print          */ 0,
    /* tp_getattr        */ 0,
    /* tp_setattr        */ 0,
    /* tp_compare        */ 0,
    /* tp_repr           */ (reprfunc)Billiard_connection_repr,
    /* tp_as_number      */ 0,
    /* tp_as_sequence    */ 0,
    /* tp_as_mapping     */ 0,
    /* tp_hash           */ 0,
    /* tp_call           */ 0,
    /* tp_str            */ 0,
    /* tp_getattro       */ 0,
    /* tp_setattro       */ 0,
    /* tp_as_buffer      */ 0,
    /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE |
                            Py_TPFLAGS_HAVE_WEAKREFS,
    /* tp_doc            */ Billiard_connection_doc,
    /* tp_traverse       */ 0,
    /* tp_clear          */ 0,
    /* tp_richcompare    */ 0,
    /* tp_weaklistoffset */ offsetof(BilliardConnectionObject, weakreflist),
    /* tp_iter           */ 0,
    /* tp_iternext       */ 0,
    /* tp_methods        */ Billiard_connection_methods,
    /* tp_members        */ 0,
    /* tp_getset         */ Billiard_connection_getset,
    /* tp_base           */ 0,
    /* tp_dict           */ 0,
    /* tp_descr_get      */ 0,
    /* tp_descr_set      */ 0,
    /* tp_dictoffset     */ 0,
    /* tp_init           */ 0,
    /* tp_alloc          */ 0,
    /* tp_new            */ Billiard_connection_new,
};

#endif /* CONNECTION_H */
